from dotenv import load_dotenv
from openai import OpenAI
import json, os
import pdfplumber


load_dotenv()


client = OpenAI(
    base_url="",
    api_key= os.environ[""]
)


def extratct_text_from_pdf(file):
    with pdfplumber.open(file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    return text

def get_structured_data(text):
    prompt = f"{text}"
    response = client.chat.completions.create(
        model="",
        messages=[{"role":"user","content":prompt}]
    )
    clean_text = response.choices[0].message.content.strip().replace("```json","").replace("```","")
    return json.loads(clean_text)