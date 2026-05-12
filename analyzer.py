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
    text = ""
    for page in doc:
        # Use blocks to preserve table structures better
        blocks = page.get_text("blocks")
        for b in blocks:
            text += b[4] + " "
    doc.close()
    return text

def analyze_syllabus(syllabus_text):
    # TRUNCATE text to ~15,000 characters to prevent Groq context errors
    truncated_text = syllabus_text[:15000]
    
    prompt = f"""
    You are an Elite Academic Auditor. Return ONLY a valid JSON object.
    
    TASK: Find modules for SDG, IKS, and Startup.
    - Ignore headers/titles.
    - Find exact 6-10 word phrases from Units/Modules.
    
    JSON format:
    {{
        "audit": [
            {{"theme": "SDG", "goal": "Goal Name", "score": "80%", "evidence": "exact phrase from text"}},
            {{"theme": "IKS", "goal": "IKS Topic", "score": "70%", "evidence": "exact phrase from text"}},
            {{"theme": "STARTUP", "goal": "Startup Topic", "score": "90%", "evidence": "exact phrase from text"}}
        ],
        "taxonomy": {{ "bloom_level": "L4 - Analyzing", "obe_status": "Compliant" }},
        "suggestion": "Detailed recommendation."
    }}

    Text: {truncated_text}
    """
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            # This forces Groq to output JSON
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Groq API Error: {e}")
        return None

def highlight_evidence(input_pdf, output_pdf, results):
    doc = fitz.open(input_pdf)
    colors = {"SDG": (0.06, 0.72, 0.51), "IKS": (0.66, 0.33, 0.97), "STARTUP": (0.96, 0.25, 0.25)}
    
    for item in results.get('audit', []):
        phrase = item.get('evidence', '').strip()
        if len(phrase) < 5 or any(x in phrase.lower() for x in ["bachelor", "semester", "syllabus"]):
            continue
            
        color = colors.get(item.get('theme', '').upper(), (1, 1, 0))
        for page in doc:
            # Triple-pass search for maximum reliability
            rects = page.search_for(phrase, quads=True)
            if not rects and len(phrase.split()) > 4:
                rects = page.search_for(" ".join(phrase.split()[:4]), quads=True)
            
            for rect in rects:
                annot = page.add_highlight_annot(rect)
                annot.set_colors(stroke=color)
                annot.update()
    
    doc.save(output_pdf)
    doc.close()