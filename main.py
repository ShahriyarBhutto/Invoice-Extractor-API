from fastapi import FastAPI, UploadFile, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import List
import time, json

from database import engine, get_db, Base
from models import Invoice, InvoiceResponse, InvoiceData
from extractor import extract_text_from_pdf, get_structured_data


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Invoice Extractor API",
    description="PDF invoices se structured data extract karo using LLM",
    version="1.0.0"
)



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



@app.post(
    "/extract-invoice",
    response_model=InvoiceResponse,
    status_code=201
)
async def extract_invoice(
    file: UploadFile,
    db: Session = Depends(get_db)
):


    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF file is allowed"
        )


    text = extract_text_from_pdf(file.file)


    if not text:
        raise HTTPException(
            status_code=400,
            detail="PDF is empty!"
        )

    try:
        raw_data = get_structured_data(text)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=500,
            detail="LLM is not giving valid JSON"
        )


    try:
        validated = InvoiceData(**raw_data)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"LLM data incomplete : {str(e)}"
        )


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
        db.rollback()     
        raise HTTPException(
            status_code=500,
            detail=f"DB mein save nahi hua: {str(e)}"
        )



@app.get("/invoices", response_model=List[InvoiceResponse])
def get_invoices(db: Session = Depends(get_db)):
    return db.query(Invoice).all()



@app.get("/invoices/{id}", response_model=InvoiceResponse)
def get_invoice(id: int, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice nahi mili")
    return invoice



@app.delete("/invoices/{id}")
def delete_invoice(id: int, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice nahi mili")
    db.delete(invoice)
    db.commit()
    return {"message": f"Invoice {id} delete ho gayi"}