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
    safe_text = syllabus_text[:4000] 
    
    # We add a strict instruction to the system to avoid chatter
    prompt = f"""
    You are an Expert Academic Consultant. Map this syllabus to NEP 2020 goals.
    
    RULES:
    1. SDG: Map to environmental/social goals.
    2. IKS: Map to Indian history, science, or local context.
    3. STARTUP: Map to innovation, logic, or project skills.
    
    SCORING: Be a supportive consultant. Give credit for implied themes.
    EVIDENCE: Extract 3-5 words EXACTLY as they appear in the text.

    Return ONLY a JSON object with this exact structure:
    {{
        "audit": [
            {{"theme": "SDG", "goal": "Goal Name", "score": "75%", "evidence": "exact words"}},
            {{"theme": "IKS", "goal": "Goal Name", "score": "50%", "evidence": "exact words"}},
            {{"theme": "STARTUP", "goal": "Goal Name", "score": "85%", "evidence": "exact words"}}
        ],
        "suggestion": "Your helpful recommendation here"
    }}

    Text: {safe_text}
    """
    
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        raw_content = completion.choices[0].message.content
        
        # CLEANING LOGIC: In case the AI adds extra text
        json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        
        return json.loads(raw_content)

    except Exception as e:
        print(f"Detailed Error: {e}")
        return None

def highlight_evidence(input_pdf, output_pdf, results):
    # (Keep your existing highlight_evidence function here)
    doc = fitz.open(input_pdf)
    colors = {"SDG": (1, 0.9, 0.2), "IKS": (0.7, 0.5, 1), "STARTUP": (1, 0.4, 0.4)}
    
    for item in results.get('audit', []):
        evidence = item.get('evidence', '')
        if not evidence or len(evidence) < 3: continue
        
        color = colors.get(item.get('theme', '').upper(), (1, 1, 0))
        for page in doc:
            text_instances = page.search_for(evidence)
            for inst in text_instances:
                annot = page.add_highlight_annot(inst)
                annot.set_colors(stroke=color)
                annot.update()
    doc.save(output_pdf)
    doc.close()