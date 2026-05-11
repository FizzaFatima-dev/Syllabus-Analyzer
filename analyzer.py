import os
import fitz
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return " ".join([page.get_text() for page in doc])

def analyze_syllabus(syllabus_text):
    safe_text = syllabus_text[:3000] 
    prompt = f"""
    Analyze this syllabus. Return ONLY a JSON object with:
    1. 'audit': List of 3 objects (SDG, IKS, Startup). Keys: 'theme', 'goal', 'score' (%), 'evidence' (2-3 words).
    2. 'suggestion': A specific recommendation.
    Text: {safe_text}
    """
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")
        return None

def highlight_evidence(input_pdf, output_pdf, results):
    doc = fitz.open(input_pdf)
    colors = {"SDG": (1, 0.9, 0.2), "IKS": (0.7, 0.5, 1), "STARTUP": (1, 0.4, 0.4)}
    for item in results.get('audit', []):
        color = colors.get(item['theme'].upper(), (1, 1, 0))
        for page in doc:
            for inst in page.search_for(item['evidence']):
                annot = page.add_highlight_annot(inst)
                annot.set_colors(stroke=color)
                annot.update()
    doc.save(output_pdf)