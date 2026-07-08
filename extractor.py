from dotenv import load_dotenv
from openai import OpenAI
import json, os
import pdfplumber


load_dotenv()


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"]
)


def extratct_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text

def get_structured_data(text):
    prompt = f"""
    Extract order_id, customer, amount, date from this invoice.
    Return ONLY valid JSON, no markdown.
    Text: {text}
    """
    response = client.chat.completions.create(
        model="poolside/laguna-xs-2.1:free",
        messages=[{"role":"user","content":prompt}]
    )
    clean_text = response.choices[0].message.content.strip().replace("```json","").replace("```","")
    return json.loads(clean_text)