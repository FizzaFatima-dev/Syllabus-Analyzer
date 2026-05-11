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
    safe_text = syllabus_text[:30000] # Deep vision for full document
    
    prompt = f"""
    You are an Expert NEP 2020 Academic Auditor. 
    Perform a semantic taxonomy mapping. Do not just look for keywords.

    TAXONOMY RULES:
    1. SDG: Map topics related to sustainability, environment, social health, or ethics.
    2. IKS: Look for Logic, Linguistics, Ancient History, or Indian contributions to science. If no Indian-specific context is found, score 0%.
    3. STARTUP: Map technical innovation, problem-solving, and project-based learning.

    SCORING:
    - High Score: Requires explicit evidence in the text.
    - 0% Score: Use this if the theme is conceptually absent.

    EVIDENCE: Extract a 3-5 word phrase EXACTLY as it appears in the text. 
    If you cannot find an exact phrase to justify a score, you MUST set score to 0% and evidence to "None".

    Return ONLY a JSON object:
    {{
        "audit": [
            {{"theme": "SDG", "goal": "Goal Name", "score": "percentage", "evidence": "exact words"}},
            {{"theme": "IKS", "goal": "Goal Name", "score": "percentage", "evidence": "exact words"}},
            {{"theme": "STARTUP", "goal": "Goal Name", "score": "percentage", "evidence": "exact words"}}
        ],
        "suggestion": "One specific improvement based on Bloom's Taxonomy"
    }}

    Text: {safe_text}
    """
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1, # Low temperature for high accuracy
            response_format={"type": "json_object"}
        )
        raw_content = completion.choices[0].message.content
        json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else None
    except Exception as e:
        print(f"Error: {e}")
        return None

def highlight_evidence(input_pdf, output_pdf, results):
    doc = fitz.open(input_pdf)
    # Colors: SDG (Gold), IKS (Purple), STARTUP (Coral)
    colors = {"SDG": (0.9, 0.7, 0), "IKS": (0.6, 0.4, 0.9), "STARTUP": (1, 0.4, 0.4)}
    
    for item in results.get('audit', []):
        evidence = item.get('evidence', '')
        if not evidence or evidence.lower() == "none": continue
        
        color = colors.get(item.get('theme', '').upper(), (1, 1, 0))
        for page in doc:
            # Quad-based highlighting is more compatible with mobile viewers
            text_instances = page.search_for(evidence)
            for inst in text_instances:
                annot = page.add_highlight_annot(inst)
                annot.set_colors(stroke=color)
                annot.update()
    doc.save(output_pdf)
    doc.close()