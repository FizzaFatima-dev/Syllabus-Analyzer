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
    You are an Elite Academic Auditor specialized in NEP 2020.
    
    Return ONLY a JSON object:
    {{
        "audit": [
            {{"theme": "SDG", "goal": "Goal Name", "score": "80%", "evidence": "3-5 word phrase from text"}},
            {{"theme": "IKS", "goal": "Goal Name", "score": "70%", "evidence": "3-5 word phrase from text"}},
            {{"theme": "STARTUP", "goal": "Goal Name", "score": "60%", "evidence": "3-5 word phrase from text"}}
        ],
        "taxonomy": {{
            "bloom_level": "L4 - Analyzing",
            "obe_status": "Highly Compliant"
        }},
        "suggestion": "Recommendation here"
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
    except: return None

def highlight_evidence(input_pdf, output_pdf, results):
    doc = fitz.open(input_pdf)
    # Colors: Green (SDG), Purple (IKS), Rose (Startup)
    colors = {"SDG": (0.1, 0.8, 0.1), "IKS": (0.6, 0.4, 0.9), "STARTUP": (1, 0.4, 0.4)}
    
    for item in results.get('audit', []):
        evidence = item.get('evidence', '').strip()
        # Clean the evidence text of any quotes the AI might have added
        evidence = evidence.replace('"', '').replace("'", "")
        
        if not evidence or evidence.lower() == "none" or len(evidence) < 4:
            continue
            
        color = colors.get(item.get('theme', '').upper(), (1, 1, 0))
        
        for page in doc:
            # SEARCH FIX: Use hit_max=10 and ignore case/white-space issues
            text_instances = page.search_for(evidence)
            for inst in text_instances:
                annot = page.add_highlight_annot(inst)
                annot.set_colors(stroke=color)
                annot.update()
    
    doc.save(output_pdf)
    doc.close()