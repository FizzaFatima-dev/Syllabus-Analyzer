import os
import fitz
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_text_from_pdf(pdf_path):
    """Extracts text from PDF while closing the file properly."""
    doc = fitz.open(pdf_path)
    text = "".join([page.get_text() for page in doc])
    doc.close()
    return text

def analyze_syllabus(syllabus_text):
    """Deep AI Audit with a focus on unique highlightable phrases."""
    prompt = f"""
    You are an Elite Academic Auditor specialized in NEP 2020.
    
    AUDIT TASK:
    Find modules related to SDG, IKS, and Startup/Entrepreneurship.
    
    IMPORTANT: For 'evidence', you MUST pick a UNIQUE 5-8 word phrase exactly as written 
    in the text. Do not summarize. Do not use generic phrases like "Introduction to".
    
    Return ONLY a JSON object:
    {{
        "audit": [
            {{"theme": "SDG", "goal": "Goal Name", "score": "85%", "evidence": "Exact long phrase from text"}},
            {{"theme": "IKS", "goal": "Goal Name", "score": "70%", "evidence": "Exact long phrase from text"}},
            {{"theme": "STARTUP", "goal": "Goal Name", "score": "90%", "evidence": "Exact long phrase from text"}}
        ],
        "taxonomy": {{
            "bloom_level": "L4 - Analyzing",
            "obe_status": "Highly Compliant (NEP 2020 Standards)"
        }},
        "suggestion": "Specific recommendation based on syllabus gaps."
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
    except Exception as e:
        print(f"AI Audit Error: {e}")
        return None

def highlight_evidence(input_pdf, output_pdf, results):
    """Draws highlights on the PDF using a bulletproof search logic."""
    doc = fitz.open(input_pdf)
    # SDG: Emerald, IKS: Purple, Startup: Rose
    colors = {"SDG": (0.1, 0.7, 0.3), "IKS": (0.5, 0.2, 0.8), "STARTUP": (0.9, 0.2, 0.3)}
    
    for item in results.get('audit', []):
        phrase = item.get('evidence', '').strip().replace('"', '').replace("'", "")
        if len(phrase) < 5: 
            continue
            
        color = colors.get(item.get('theme', '').upper(), (1, 1, 0))
        
        for page in doc:
            # 1. Try exact match
            search_instances = page.search_for(phrase)
            
            # 2. If exact fails, try quad search (handles multi-line text)
            if not search_instances:
                search_instances = page.search_for(phrase, quad=True)

            for inst in search_instances:
                annot = page.add_highlight_annot(inst)
                annot.set_colors(stroke=color)
                annot.set_info(content=f"{item['theme']}: {item['goal']}")
                annot.update()
    
    doc.save(output_pdf)
    doc.close()