import os, fitz, json, re
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
    # Prompt updated to be more sensitive to subtle IKS/Ethics mentions
    prompt = f"""
    You are an Elite Academic Auditor.
    
    TASK: Find modules for SDG, IKS, and Startup.
    For IKS: Be sensitive. Look for Indian IT laws, Ethics, local community context, or Indian history. 
    If you find even a subtle match, extract the exact phrase.
    
    IMPORTANT: 'evidence' MUST be a 5-8 word phrase exactly as written in the text.
    
    Return ONLY JSON:
    {{
        "audit": [
            {{"theme": "SDG", "goal": "Goal Name", "score": "80%", "evidence": "exact phrase"}},
            {{"theme": "IKS", "goal": "Goal Name", "score": "60%", "evidence": "exact phrase"}},
            {{"theme": "STARTUP", "goal": "Goal Name", "score": "90%", "evidence": "exact phrase"}}
        ],
        "taxonomy": {{ "bloom_level": "L4 - Analyzing", "obe_status": "Highly Compliant" }},
        "suggestion": "Detailed recommendation here."
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
    except: return None

def highlight_evidence(input_pdf, output_pdf, results):
    doc = fitz.open(input_pdf)
    colors = {"SDG": (0.1, 0.7, 0.3), "IKS": (0.5, 0.2, 0.8), "STARTUP": (0.9, 0.2, 0.3)}
    
    for item in results.get('audit', []):
        phrase = item.get('evidence', '').strip().replace('"', '')
        if len(phrase) < 5 or "no specific" in phrase.lower(): continue
            
        color = colors.get(item['theme'].upper(), (1, 1, 0))
        for page in doc:
            # First attempt: Exact phrase search
            search_instances = page.search_for(phrase, quads=True)
            
            # Second attempt: Fuzzy search (if exact fails, try first half of phrase)
            if not search_instances and len(phrase.split()) > 3:
                short_phrase = " ".join(phrase.split()[:4])
                search_instances = page.search_for(short_phrase, quads=True)

            for inst in search_instances:
                annot = page.add_highlight_annot(inst)
                annot.set_colors(stroke=color)
                annot.update()
    
    doc.save(output_pdf)
    doc.close()