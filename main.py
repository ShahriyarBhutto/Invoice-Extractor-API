from extractor import extratct_text_from_pdf,get_structured_data
from fastapi import FastAPI, HTTPException, UploadFile
import json


app = FastAPI()


@app.post("/invoice-extrator")
async def extract_invoice(file:UploadFile):
    if not file.filename.startswith(".pdf"):
        raise HTTPException(status_code=400,detail="Not a valid file formate, Please upload .pdf files only")
    text =  extratct_text_from_pdf(file.file)
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text found inside PDF")
    try:
        data = get_structured_data(text)
        return data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500,detail="Not getting valid data from LLM")