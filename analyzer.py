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
        text += page.get_text("text") # Preserve text flow
    doc.close()
    return text

def analyze_syllabus(syllabus_text):
    # Prompt is strictly tuned to ignore titles and find deep module content
    prompt = f"""
    You are an Elite Academic Auditor for NEP 2020. 
    Analyze the syllabus text and find specific technical modules/topics.

    STRICT RULES:
    1. DO NOT pick course titles, university names, or headers as 'evidence'.
    2. Pick a UNIQUE 6-10 word phrase from the ACTUAL syllabus content (Units/Modules).
    3. For IKS: Look for Indian IT Acts, Cyber Laws, Professional Ethics, or local case studies.
    4. For STARTUP: Look for Agile, SDLC, Project Management, or Innovation modules.

    Return ONLY JSON:
    {{
        "audit": [
            {{"theme": "SDG", "goal": "Goal Name", "score": "85%", "evidence": "exact long phrase from a module"}},
            {{"theme": "IKS", "goal": "IKS Topic", "score": "75%", "evidence": "exact long phrase from a module"}},
            {{"theme": "STARTUP", "goal": "Innovation Topic", "score": "90%", "evidence": "exact long phrase from a module"}}
        ],
        "taxonomy": {{ "bloom_level": "L4 - Analyzing", "obe_status": "Highly Compliant (NEP 2020)" }},
        "suggestion": "Detailed academic recommendation."
    }}
    Text: {syllabus_text[:28000]}
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
    # COLORS: SDG: Emerald, IKS: Purple, STARTUP: Rose
    colors = {
        "SDG": (0.06, 0.72, 0.51),      # emerald-500
        "IKS": (0.66, 0.33, 0.97),      # purple-500
        "STARTUP": (0.96, 0.25, 0.25)   # rose-500
    }
    
    for item in results.get('audit', []):
        phrase = item.get('evidence', '').strip().replace('"', '').replace("'", "")
        if len(phrase) < 5 or "bachelor" in phrase.lower(): # Guard against titles
            continue
            
        color = colors.get(item.get('theme', '').upper(), (1, 1, 0))
        
        for page in doc:
            # Pass 1: Exact search with quads
            search_instances = page.search_for(phrase, quads=True)
            
            # Pass 2: Fuzzy search (handles line breaks in PDFs)
            if not search_instances and len(phrase.split()) > 3:
                # Try the first half of the phrase
                fuzzy_phrase = " ".join(phrase.split()[:4])
                search_instances = page.search_for(fuzzy_phrase, quads=True)

            for inst in search_instances:
                annot = page.add_highlight_annot(inst)
                annot.set_colors(stroke=color)
                annot.update()
    
    doc.save(output_pdf)
    doc.close()