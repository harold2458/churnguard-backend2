import csv
import io

from fastapi import APIRouter, Depends, Query, Response
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database import get_database
from app.utils.dependencies import require_roles


router = APIRouter(prefix="/reports", tags=["Rapports"], dependencies=[Depends(require_roles("admin", "manager"))])


@router.get("/summary")
async def reports_summary(db: AsyncIOMotorDatabase = Depends(get_database)):
    by_contract = await db.clients.aggregate(
        [{"$group": {"_id": "$Contract", "avg_score": {"$avg": "$score_churn"}, "count": {"$sum": 1}}}]
    ).to_list(20)
    by_tenure = await db.clients.aggregate(
        [
            {
                "$bucket": {
                    "groupBy": "$tenure",
                    "boundaries": [0, 6, 12, 24, 1000],
                    "default": "unknown",
                    "output": {"count": {"$sum": 1}, "avg_score": {"$avg": "$score_churn"}},
                }
            }
        ]
    ).to_list(20)
    by_payment = await db.clients.aggregate(
        [{"$group": {"_id": "$PaymentMethod", "avg_score": {"$avg": "$score_churn"}, "count": {"$sum": 1}}}]
    ).to_list(20)
    return {"par_contrat": by_contract, "par_anciennete": by_tenure, "par_paiement": by_payment}


@router.get("/export")
async def export_report(
    format: str = Query("csv", pattern="^(csv|pdf)$"),
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    clients = await db.clients.find({}).sort("score_churn", -1).to_list(5000)
    if format == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["id", "nom", "prenom", "email", "score_churn", "niveau_risque", "contract", "monthly_charges"])
        for client in clients:
            writer.writerow(
                [
                    str(client.get("_id")),
                    client.get("nom"),
                    client.get("prenom"),
                    client.get("email"),
                    client.get("score_churn"),
                    client.get("niveau_risque"),
                    client.get("Contract"),
                    client.get("MonthlyCharges"),
                ]
            )
        return Response(
            content=buffer.getvalue(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=churnguard_clients.csv"},
        )

    lines = ["ChurnGuard - Rapport clients a risque", ""]
    for client in clients[:100]:
        lines.append(
            f"{client.get('prenom', '')} {client.get('nom', '')} - "
            f"{round((client.get('score_churn') or 0) * 100, 2)}% - {client.get('niveau_risque')}"
        )
    pdf_bytes = _simple_pdf("\n".join(lines[:40]))
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=churnguard_report.pdf"},
    )


def _simple_pdf(text: str) -> bytes:
    safe_lines = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")[:100] for line in text.splitlines()]
    content_lines = ["BT", "/F1 11 Tf", "50 790 Td"]
    for index, line in enumerate(safe_lines):
        if index:
            content_lines.append("0 -16 Td")
        content_lines.append(f"({line}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="ignore")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode())
        pdf.extend(obj)
        pdf.extend(b"\nendobj\n")
    xref = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return bytes(pdf)
