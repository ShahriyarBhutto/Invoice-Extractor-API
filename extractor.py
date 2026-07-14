from dotenv import load_dotenv
from openai import OpenAI
import json, os
import pdfplumber


load_dotenv()


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)


def extratct_text_from_pdf(file) -> str:
    with pdfplumber.open(file) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n" 
    return text.strip()

def get_structured_data(text:str)-> dict:
    prompt = f"""You are an invoice data extraction assistant.
Extract the following fields from the invoice text below.
Return ONLY a valid JSON object — no explanation, no markdown, no extra text.

Required fields:
- order_id: invoice number or order ID (string)
- customer: customer name (string)  
- amount: total amount as number only, no currency symbol (float)
- date: invoice date in YYYY-MM-DD format (string)

If a field is not found, use null.

Invoice text:
{text}"""
    response = client.chat.completions.create(
        model="poolside/laguna-xs-2.1:free",
        messages=[{"role":"user","content":prompt}],
        temperature= 0.1
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    return json.loads(raw)