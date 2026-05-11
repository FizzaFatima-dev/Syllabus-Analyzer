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
    text = "".join([page.get_text() for page in doc])
    doc.close()
    return text

def analyze_syllabus(syllabus_text):
    safe_text = syllabus_text[:30000] 
    
    prompt = f"""
    You are an Elite Academic Auditor specialized in NEP 2020, OBE, and Bloom's Taxonomy.
    
    Return ONLY a JSON object with this EXACT structure:
    {{
        "audit": [
            {{"theme": "SDG", "goal": "Goal Name", "score": "percentage", "evidence": "exact words"}},
            {{"theme": "IKS", "goal": "Goal Name", "score": "percentage", "evidence": "exact words"}},
            {{"theme": "STARTUP", "goal": "Goal Name", "score": "percentage", "evidence": "exact words"}}
        ],
        "taxonomy": {{
            "bloom_level": "L4 - Analyzing",
            "obe_status": "Highly Compliant (Meets NEP 2020 Standards)"
        }},
        "suggestion": "Add a module on X to align with SDG Y."
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
    doc = fitz.open(input_pdf)
    # Colors: SDG (Green), IKS (Purple), STARTUP (Coral)
    colors = {"SDG": (0.1, 0.8, 0.1), "IKS": (0.6, 0.4, 0.9), "STARTUP": (1, 0.4, 0.4)}
    
    for item in results.get('audit', []):
        text = item.get('evidence', '')
        if not text or text.lower() == "none" or len(text) < 3: 
            continue
            
        color = colors.get(item.get('theme', '').upper(), (1, 1, 0))
        for page in doc:
            # We use search_for to find the exact text in the PDF
            text_instances = page.search_for(text)
            for inst in text_instances:
                annot = page.add_highlight_annot(inst)
                annot.set_colors(stroke=color)
                annot.update()
    
    doc.save(output_pdf)
    doc.close()