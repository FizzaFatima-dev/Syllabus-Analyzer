import os
import fitz  # PyMuPDF
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# MISSING FUNCTION FIXED BELOW
def extract_text_from_pdf(pdf_path):
    """Extracts all text from the uploaded PDF file."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def analyze_syllabus(syllabus_text):
    """Performs deep semantic mapping of the syllabus text."""
    safe_text = syllabus_text[:30000] 
    
    prompt = f"""
    You are an Elite Academic Auditor specialized in NEP 2020, OBE, and Bloom's Taxonomy.
    
    AUDIT REQUIREMENTS:
    1. SDG: Identify which of the 17 SDGs are covered (e.g., SDG 4, SDG 9, SDG 12).
    2. IKS: Detect Indian Knowledge Systems, history, or traditional logic.
    3. STARTUP: Innovation and Entrepreneurship modules.
    4. OBE & BLOOM: Identify 'Course Outcomes' and categorize by Bloom's Level (e.g., L3-Apply, L4-Analyze).

    STRICT JSON OUTPUT:
    {{
        "audit": [
            {{"theme": "SDG", "goal": "SDG Name", "score": "percentage", "evidence": "exact text"}},
            {{"theme": "IKS", "goal": "IKS Name", "score": "percentage", "evidence": "exact text"}},
            {{"theme": "STARTUP", "goal": "Startup Name", "score": "percentage", "evidence": "exact text"}}
        ],
        "taxonomy": {{
            "bloom_level": "L1-L6 Level",
            "obe_status": "Compliance Level"
        }},
        "heatmap": [
            {{"dept": "Subject Area", "sdg": "Number"}}
        ],
        "suggestion": "Detailed academic recommendation"
    }}

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
        print(f"AI Error: {e}")
        return None

def highlight_evidence(input_pdf, output_pdf, results):
    """Highlights the evidence phrases found by the AI in the PDF."""
    doc = fitz.open(input_pdf)
    # SDG: Green, IKS: Purple, STARTUP: Red/Coral
    colors = {"SDG": (0.1, 0.8, 0.1), "IKS": (0.6, 0.4, 0.9), "STARTUP": (1, 0.4, 0.4)}
    
    for item in results.get('audit', []):
        evidence_text = item.get('evidence', '')
        if not evidence_text or evidence_text.lower() == "none":
            continue
            
        color = colors.get(item.get('theme', '').upper(), (1, 1, 0))
        for page in doc:
            text_instances = page.search_for(evidence_text)
            for inst in text_instances:
                annot = page.add_highlight_annot(inst)
                annot.set_colors(stroke=color)
                annot.update()
    
    doc.save(output_pdf)
    doc.close()