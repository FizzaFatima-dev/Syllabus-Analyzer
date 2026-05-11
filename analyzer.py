import os
import fitz
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    return " ".join([page.get_text() for page in doc])

def analyze_syllabus(syllabus_text):
    # Keep text length manageable for the model
    safe_text = syllabus_text[:4000] 
    
    prompt = f"""
    Analyze this syllabus for NEP 2020 compliance. Return ONLY a JSON object.
    
    For each theme (SDG, IKS, STARTUP):
    1. 'score': Provide a percentage (0-100). Be strict and consistent.
    2. 'evidence': Extract a 3-5 word phrase EXACTLY as it appears in the text. 
       Do not paraphrase. This is for a PDF highlighter.
    
    Structure:
    {{
        "audit": [
            {{"theme": "SDG", "goal": "Goal Name", "score": "80%", "evidence": "exact text"}},
            {{"theme": "IKS", "goal": "Goal Name", "score": "40%", "evidence": "exact text"}},
            {{"theme": "STARTUP", "goal": "Goal Name", "score": "90%", "evidence": "exact text"}}
        ],
        "suggestion": "One specific recommendation"
    }}

    Text: {safe_text}
    """
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0, # Makes scores consistent
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"AI Error: {e}")
        return None

def highlight_evidence(input_pdf, output_pdf, results):
    doc = fitz.open(input_pdf)
    colors = {
        "SDG": (1, 0.9, 0.2),      # Yellow
        "IKS": (0.7, 0.5, 1),      # Purple
        "STARTUP": (1, 0.4, 0.4)   # Red
    }
    
    for item in results.get('audit', []):
        theme = item.get('theme', '').upper()
        evidence = item.get('evidence', '')
        
        if not evidence or len(evidence) < 3:
            continue
            
        color = colors.get(theme, (1, 1, 0))
        
        for page in doc:
            # Case-insensitive search to catch variations
            text_instances = page.search_for(evidence)
            for inst in text_instances:
                annot = page.add_highlight_annot(inst)
                annot.set_colors(stroke=color)
                annot.update()
                
    doc.save(output_pdf)
    doc.close()