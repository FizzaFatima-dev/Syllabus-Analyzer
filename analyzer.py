import os
import fitz
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text")
    doc.close()
    return text

def analyze_syllabus(syllabus_text):
    prompt = f"""
    You are an Elite NEP 2020 Auditor. 
    Find specific technical modules for SDG, IKS, and Startup.
    
    STRICT RULES:
    1. PICK EXACT phrases (5-8 words) from the Unit content.
    2. IGNORE the university name or degree headers.
    
    Return ONLY JSON:
    {{
        "audit": [
            {{"theme": "SDG", "goal": "Environment", "score": "85%", "evidence": "exact phrase from text"}},
            {{"theme": "IKS", "goal": "Indigenous Knowledge", "score": "75%", "evidence": "exact phrase from text"}},
            {{"theme": "STARTUP", "goal": "Entrepreneurship", "score": "95%", "evidence": "exact phrase from text"}}
        ],
        "taxonomy": {{ "bloom_level": "L4 - Analyzing", "obe_status": "Highly Compliant" }},
        "suggestion": "Recommendation here."
    }}
    Text: {syllabus_text[:15000]}
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
    # Emerald, Purple, Rose
    colors = {
        "SDG": (0.06, 0.72, 0.51),
        "IKS": (0.66, 0.33, 0.97),
        "STARTUP": (0.96, 0.25, 0.25)
    }
    
    for item in results.get('audit', []):
        phrase = item.get('evidence', '').strip().replace('"', '').replace("'", "")
        if len(phrase) < 5: continue
            
        color = colors.get(item.get('theme', '').upper(), (1, 1, 0))
        
        for page in doc:
            # Multi-Pass Search
            search_results = page.search_for(phrase)
            
            # If full phrase fails, search first 4 words (Handles line breaks)
            if not search_results and len(phrase.split()) > 4:
                search_results = page.search_for(" ".join(phrase.split()[:4]))

            for rect in search_results:
                # Add highlight
                annot = page.add_highlight_annot(rect)
                annot.set_colors(stroke=color)
                # Ensure the highlight is "Multiplied" (shows up better on some PDF readers)
                annot.set_opacity(0.5) 
                annot.update()
    
    # Save with garbage collection to ensure the highlights are "baked in"
    doc.save(output_pdf, garbage=4, deflate=True, clean=True)
    doc.close()