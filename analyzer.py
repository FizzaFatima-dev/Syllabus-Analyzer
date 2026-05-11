import os, fitz, json, re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyze_syllabus(syllabus_text):
    safe_text = syllabus_text[:30000] 
    
    prompt = f"""
    You are an Elite Academic Auditor specialized in NEP 2020, OBE, and Bloom's Taxonomy.
    
    AUDIT REQUIREMENTS:
    1. SDG: Identify which of the 17 SDGs are covered (e.g., SDG 4, SDG 9, SDG 12).
    2. IKS: Detect Indian Knowledge Systems, history, or traditional logic.
    3. STARTUP: Innovation and Entrepreneurship modules.
    4. OBE & BLOOM: Identify 'Course Outcomes' and categorize by Bloom's Level (e.g., L3-Apply, L4-Analyze).

    STRICT JSON OUTPUT:
    {{
        "audit": [
            {{"theme": "SDG", "goal": "SDG 12: Sustainable Consumption", "score": "85%", "evidence": "exact text"}},
            {{"theme": "IKS", "goal": "Indian Mathematics", "score": "0%", "evidence": "None"}},
            {{"theme": "STARTUP", "goal": "Venture Development", "score": "90%", "evidence": "exact text"}}
        ],
        "taxonomy": {{
            "bloom_level": "L4 - Analyzing",
            "obe_status": "Highly Compliant"
        }},
        "heatmap": [
            {{"dept": "Computer Science", "sdg": "9"}},
            {{"dept": "General Science", "sdg": "4"}}
        ],
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
    except: return None

def highlight_evidence(input_pdf, output_pdf, results):
    doc = fitz.open(input_pdf)
    colors = {"SDG": (0.1, 0.8, 0.1), "IKS": (0.6, 0.4, 0.9), "STARTUP": (1, 0.4, 0)}
    for item in results.get('audit', []):
        text = item.get('evidence', '')
        if not text or text.lower() == "none": continue
        for page in doc:
            for inst in page.search_for(text):
                page.add_highlight_annot(inst).set_colors(stroke=colors.get(item['theme'], (1,1,0))).update()
    doc.save(output_pdf); doc.close()