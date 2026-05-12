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
        # We extract with 'blocks' to maintain the structure of tables better
        blocks = page.get_text("blocks")
        for b in blocks:
            text += b[4] + " "
    doc.close()
    return text

def analyze_syllabus(syllabus_text):
    # Prompt is now laser-focused on Unit Content, not titles
    prompt = f"""
    You are an Elite Academic Auditor. Your job is to find technical Unit topics.
    
    STRICT RULES:
    1. IGNORE the university name, degree (BBA, BCA), and course titles.
    2. TARGET the Units/Modules (e.g., "Identification of business opportunities", "Woman entrepreneurship").
    3. EVIDENCE must be 6-10 words exactly as they appear in the PDF.
    
    Return ONLY JSON:
    {{
        "audit": [
            {{"theme": "SDG", "goal": "Goal 8: Economic Growth", "score": "90%", "evidence": "exact unit phrase here"}},
            {{"theme": "IKS", "goal": "Professional Ethics", "score": "75%", "evidence": "exact unit phrase here"}},
            {{"theme": "STARTUP", "goal": "Project Management", "score": "95%", "evidence": "exact unit phrase here"}}
        ],
        "taxonomy": {{ "bloom_level": "L4 - Analyzing", "obe_status": "Highly Compliant" }},
        "suggestion": "Strengthen the IKS component by linking Indian Business Acts to the Ethics module."
    }}
    Text Content: {syllabus_text[:28000]}
    """
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except:
        return None

def highlight_evidence(input_pdf, output_pdf, results):
    doc = fitz.open(input_pdf)
    # Elite UI Colors: Emerald (SDG), Purple (IKS), Rose (Startup)
    colors = {
        "SDG": (0.06, 0.72, 0.51),
        "IKS": (0.66, 0.33, 0.97),
        "STARTUP": (0.96, 0.25, 0.25)
    }
    
    for item in results.get('audit', []):
        phrase = item.get('evidence', '').strip().replace('"', '').replace("'", "")
        # Prevent highlighting generic headers
        if len(phrase) < 6 or any(x in phrase.lower() for x in ["bachelor", "semester", "syllabus"]):
            continue
            
        color = colors.get(item.get('theme', '').upper(), (1, 1, 0))
        
        for page in doc:
            # Pass 1: Try the full phrase
            rects = page.search_for(phrase, quads=True)
            
            # Pass 2: Fuzzy Logic - if full phrase fails, try first 5 words
            # This is crucial for text that breaks across lines in the PDF
            if not rects and len(phrase.split()) > 5:
                fuzzy_phrase = " ".join(phrase.split()[:5])
                rects = page.search_for(fuzzy_phrase, quads=True)
            
            # Pass 3: Ultra-Fuzzy - try first 3 words
            if not rects and len(phrase.split()) > 3:
                ultra_fuzzy = " ".join(phrase.split()[:3])
                rects = page.search_for(ultra_fuzzy, quads=True)

            for rect in rects:
                annot = page.add_highlight_annot(rect)
                annot.set_colors(stroke=color)
                annot.update()
    
    doc.save(output_pdf)
    doc.close()