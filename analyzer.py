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
    # INCREASED VISION: 30,000 characters covers about 15-20 pages
    # Llama-3-70b can handle this easily
    safe_text = syllabus_text[:30000] 
    
    prompt = f"""
    You are an Expert Academic Consultant. Audit this syllabus for NEP 2020.
    
    STRICT RULES FOR EVIDENCE:
    1. DO NOT use the University name, Author names, or Dates as evidence.
    2. 'evidence' MUST be a 3-5 word phrase representing ACTUAL COURSE TOPICS or MODULES.
    3. If you find a topic like 'Yoga', 'Ancient Indian Science', or 'Local Ethics', give high IKS scores.
    4. If you find 'Project', 'Case Study', or 'Java/Python', give high Startup scores.

    SCORING: 
    - Be a supportive consultant. 
    - Map themes to goals even if keywords are slightly different.

    Return ONLY a JSON object:
    {{
        "audit": [
            {{"theme": "SDG", "goal": "Goal Name", "score": "75%", "evidence": "exact course topic"}},
            {{"theme": "IKS", "goal": "Goal Name", "score": "50%", "evidence": "exact course topic"}},
            {{"theme": "STARTUP", "goal": "Goal Name", "score": "85%", "evidence": "exact course topic"}}
        ],
        "suggestion": "Helpful advice for the lecturer"
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
        # (Keep the same JSON cleaning logic from the previous reply)
        import re
        json_match = re.search(r'\{.*\}', completion.choices[0].message.content, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else None
    except Exception as e:
        print(f"Error: {e}")
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