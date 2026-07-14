from fastapi import FastAPI, UploadFile, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import List
import time, json

from database import engine, get_db, Base
from models import Invoice, InvoiceResponse, InvoiceData
from extractor import extract_text_from_pdf, get_structured_data

# Tables create karo — agar pehle se hain toh ignore karega
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Invoice Extractor API",
    description="PDF invoices se structured data extract karo using LLM",
    version="1.0.0"
)


# ── Middleware — har request log karo ───────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    print(
        f"[{request.method}] {request.url.path} → "
        f"{response.status_code} ({duration:.3f}s)"
    )
    return response


# ── POST /extract-invoice ────────────────────────────────────────
@app.post(
    "/extract-invoice",
    response_model=InvoiceResponse,
    status_code=201
)
async def extract_invoice(
    file: UploadFile,
    db: Session = Depends(get_db)
):
    """PDF upload karo — LLM se data extract karo — DB mein save karo."""

    # Validation 1 — sirf PDF accept karo
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Sirf PDF files accept ki jaati hain"
        )

    # Step 1 — PDF se text nikalo
    text = extract_text_from_pdf(file.file)

    # Validation 2 — PDF empty toh nahi?
    if not text:
        raise HTTPException(
            status_code=400,
            detail="PDF se koi text nahi nikla — file corrupt ya empty hai"
        )

    # Step 2 — LLM se structured data nikalo
    try:
        raw_data = get_structured_data(text)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="LLM ne valid JSON nahi diya — dobara try karo"
        )

    # Step 3 — Pydantic se validate karo LLM ka output
    try:
        validated = InvoiceData(**raw_data)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"LLM data incomplete hai: {str(e)}"
        )

    # Step 4 — DB mein save karo
    try:
        invoice = Invoice(
            order_id=validated.order_id,
            customer=validated.customer,
            amount=validated.amount,
            date=validated.date
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        return invoice

    except Exception as e:
        db.rollback()     # koi bhi error → changes wapas
        raise HTTPException(
            status_code=500,
            detail=f"DB mein save nahi hua: {str(e)}"
        )


# ── GET /invoices ────────────────────────────────────────────────
@app.get("/invoices", response_model=List[InvoiceResponse])
def get_invoices(db: Session = Depends(get_db)):
    """Sari saved invoices return karo."""
    return db.query(Invoice).all()


# ── GET /invoices/{id} ───────────────────────────────────────────
@app.get("/invoices/{id}", response_model=InvoiceResponse)
def get_invoice(id: int, db: Session = Depends(get_db)):
    """Ek specific invoice by ID."""
    invoice = db.query(Invoice).filter(Invoice.id == id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice nahi mili")
    return invoice


# ── DELETE /invoices/{id} ────────────────────────────────────────
@app.delete("/invoices/{id}")
def delete_invoice(id: int, db: Session = Depends(get_db)):
    """Invoice delete karo."""
    invoice = db.query(Invoice).filter(Invoice.id == id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice nahi mili")
    db.delete(invoice)
    db.commit()
    return {"message": f"Invoice {id} delete ho gayi"}