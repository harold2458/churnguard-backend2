from bson import ObjectId
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler: GetCoreSchemaHandler):
        return core_schema.no_info_plain_validator_function(
            cls.validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def validate(cls, value):
        if isinstance(value, ObjectId):
            return value
        if isinstance(value, str) and ObjectId.is_valid(value):
            return ObjectId(value)
        raise ValueError("Invalid ObjectId")


def oid(value: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise ValueError("Invalid ObjectId")
    return ObjectId(value)


def serialize_doc(doc: dict | None) -> dict | None:
    if not doc:
        return None
    doc["id"] = str(doc.pop("_id"))
    for key, value in list(doc.items()):
        if isinstance(value, ObjectId):
            doc[key] = str(value)
    return doc


def serialize_docs(docs: list[dict]) -> list[dict]:
    return [serialize_doc(doc) for doc in docs]
