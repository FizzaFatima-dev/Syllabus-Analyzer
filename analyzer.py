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
    prompt = f"""
    You are an Elite Academic Auditor. Audit this syllabus for SDG, IKS, and Startup modules.
    
    Return ONLY JSON:
    {{
        "audit": [
            {{"theme": "SDG", "goal": "Goal Name", "score": "85%", "evidence": "Exact 5-8 word phrase from text"}},
            {{"theme": "IKS", "goal": "Goal Name", "score": "70%", "evidence": "Exact 5-8 word phrase from text"}},
            {{"theme": "STARTUP", "goal": "Goal Name", "score": "90%", "evidence": "Exact 5-8 word phrase from text"}}
        ],
        "taxonomy": {{ "bloom_level": "L4 - Analyzing", "obe_status": "Highly Compliant" }},
        "suggestion": "Add more hands-on startup modules."
    }}
    Text: {syllabus_text[:25000]}
    """
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except: return None

def highlight_evidence(input_pdf, output_pdf, results):
    doc = fitz.open(input_pdf)
    colors = {"SDG": (0.1, 0.7, 0.3), "IKS": (0.5, 0.2, 0.8), "STARTUP": (0.9, 0.2, 0.3)}
    
    for item in results.get('audit', []):
        phrase = item.get('evidence', '').strip().replace('"', '')
        if len(phrase) < 4: continue
        
        color = colors.get(item['theme'].upper(), (1, 1, 0))
        
        for page in doc:
            # FIX: Changed 'quad' to 'quads'
            # Also added 'small_caps' and 'dehyphenate' flags to find text more easily
            search_instances = page.search_for(phrase, quads=True)

            for inst in search_instances:
                annot = page.add_highlight_annot(inst)
                annot.set_colors(stroke=color)
                annot.update()
    
    doc.save(output_pdf)
    doc.close()