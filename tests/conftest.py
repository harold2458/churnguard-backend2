import re
from copy import deepcopy

import pytest
import pytest_asyncio
from bson import ObjectId
from httpx import ASGITransport, AsyncClient

from app.database import get_database
from app.main import app


class InsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class DeleteResult:
    def __init__(self, deleted_count):
        self.deleted_count = deleted_count


class UpdateResult:
    def __init__(self, matched_count):
        self.matched_count = matched_count


class InMemoryCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, key, direction):
        reverse = direction == -1
        self.docs.sort(key=lambda doc: (doc.get(key) is None, doc.get(key)), reverse=reverse)
        return self

    def skip(self, count):
        self.docs = self.docs[count:]
        return self

    def limit(self, count):
        self.docs = self.docs[:count]
        return self

    async def to_list(self, length):
        return deepcopy(self.docs[:length])


class InMemoryCollection:
    def __init__(self, name):
        self.name = name
        self.docs = []

    async def insert_one(self, doc):
        stored = deepcopy(doc)
        stored.setdefault("_id", ObjectId())
        self.docs.append(stored)
        return InsertOneResult(stored["_id"])

    async def find_one(self, query, sort=None):
        matches = [doc for doc in self.docs if _matches(doc, query)]
        if sort:
            key, direction = sort[0]
            matches.sort(key=lambda doc: doc.get(key), reverse=direction == -1)
        return deepcopy(matches[0]) if matches else None

    def find(self, query):
        return InMemoryCursor([deepcopy(doc) for doc in self.docs if _matches(doc, query)])

    async def update_one(self, query, update, upsert=False):
        for doc in self.docs:
            if _matches(doc, query):
                if "$set" in update:
                    doc.update(deepcopy(update["$set"]))
                return UpdateResult(1)
        if upsert:
            new_doc = deepcopy(query)
            if "$set" in update:
                new_doc.update(deepcopy(update["$set"]))
            new_doc.setdefault("_id", ObjectId())
            self.docs.append(new_doc)
            return UpdateResult(1)
        return UpdateResult(0)

    async def update_many(self, query, update):
        matched = 0
        for doc in self.docs:
            if _matches(doc, query):
                matched += 1
                if "$set" in update:
                    doc.update(deepcopy(update["$set"]))
        return UpdateResult(matched)

    async def delete_one(self, query):
        for index, doc in enumerate(self.docs):
            if _matches(doc, query):
                del self.docs[index]
                return DeleteResult(1)
        return DeleteResult(0)

    async def count_documents(self, query):
        return len([doc for doc in self.docs if _matches(doc, query)])

    def aggregate(self, pipeline):
        if self.name == "clients":
            return InMemoryCursor(_aggregate_clients(self.docs, pipeline))
        if self.name == "historique_scores":
            return InMemoryCursor(_aggregate_history(self.docs, pipeline))
        return InMemoryCursor([])


class InMemoryDatabase:
    def __init__(self):
        self.users = InMemoryCollection("users")
        self.clients = InMemoryCollection("clients")
        self.behaviors = InMemoryCollection("behaviors")
        self.historique_scores = InMemoryCollection("historique_scores")
        self.alertes = InMemoryCollection("alertes")
        self.actions = InMemoryCollection("actions")
        self.settings = InMemoryCollection("settings")
        self.notifications = InMemoryCollection("notifications")

    async def command(self, name):
        return {"ok": 1}


def _matches(doc, query):
    for key, expected in query.items():
        if key == "$or":
            if not any(_matches(doc, subquery) for subquery in expected):
                return False
            continue

        value = doc.get(key)
        if isinstance(expected, dict):
            if "$regex" in expected:
                flags = re.IGNORECASE if expected.get("$options") == "i" else 0
                if not re.search(expected["$regex"], str(value or ""), flags):
                    return False
            if "$gte" in expected and value < expected["$gte"]:
                return False
            if "$lte" in expected and value > expected["$lte"]:
                return False
            if "$in" in expected and value not in expected["$in"]:
                return False
        elif isinstance(value, ObjectId) and isinstance(expected, str) and ObjectId.is_valid(expected):
            if value != ObjectId(expected):
                return False
        elif value != expected:
            return False
    return True


def _aggregate_clients(docs, pipeline):
    group = pipeline[0].get("$group", {}) if pipeline else {}
    bucket = pipeline[0].get("$bucket", {}) if pipeline else {}
    if bucket:
        boundaries = bucket.get("boundaries", [])
        rows = []
        for start, end in zip(boundaries, boundaries[1:]):
            bucket_docs = [doc for doc in docs if start <= (doc.get("tenure") or 0) < end]
            scores = [doc.get("score_churn") for doc in bucket_docs if doc.get("score_churn") is not None]
            rows.append({"_id": start, "count": len(bucket_docs), "avg_score": sum(scores) / len(scores) if scores else None})
        return rows
    if "avg_score" in group:
        if group.get("_id"):
            field = str(group["_id"]).lstrip("$")
            grouped = {}
            for doc in docs:
                grouped.setdefault(doc.get(field), []).append(doc)
            rows = []
            for key, items in grouped.items():
                scores = [doc.get("score_churn") for doc in items if doc.get("score_churn") is not None]
                rows.append({"_id": key, "count": len(items), "avg_score": sum(scores) / len(scores) if scores else None})
            return rows
        scores = [doc.get("score_churn") for doc in docs if doc.get("score_churn") is not None]
        return [{"_id": None, "avg_score": sum(scores) / len(scores) if scores else None}]
    if "count" in group:
        counts = {}
        for doc in docs:
            key = doc.get("niveau_risque")
            counts[key] = counts.get(key, 0) + 1
        return [{"_id": key, "count": count} for key, count in counts.items()]
    return []


def _aggregate_history(docs, pipeline):
    impacts = {}
    for doc in docs:
        for reason in doc.get("top_raisons_shap", []):
            feature = reason.get("feature")
            impacts.setdefault(feature, []).append(abs(reason.get("impact", 0)))
    rows = [
        {"_id": feature, "impact_moyen": sum(values) / len(values), "count": len(values)}
        for feature, values in impacts.items()
    ]
    rows.sort(key=lambda row: row["impact_moyen"], reverse=True)
    return rows[:10]


@pytest.fixture
def fake_db():
    return InMemoryDatabase()


@pytest_asyncio.fixture
async def api_client(fake_db):
    app.dependency_overrides[get_database] = lambda: fake_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
