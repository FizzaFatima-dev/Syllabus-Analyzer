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
    safe_text = syllabus_text[:4000] 
    
    prompt = f"""
    You are an expert NEP 2020 Consultant. Analyze the syllabus text provided.
    
    EVALUATION CRITERIA:
    1. SDG (Sustainable Development): Look for environmental science, ethics, equality, or social health.
    2. IKS (Indian Knowledge Systems): Look for traditional logic, ancient history, Indian contributions to science/math, or local languages.
    3. STARTUP: Look for critical thinking, project-based learning, problem-solving, or innovation.

    SCORING GUIDELINE:
    - If a topic is mentioned but not detailed, give 30-50%.
    - Only give 0% if the topic is completely absent.
    - Be encouraging but honest.

    CRITICAL: For 'evidence', you MUST extract 3-5 words found EXACTLY in the text for the highlighter to work.

    Text: {safe_text}
    """
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            # 0.2 is the "Sweet Spot" between strict and creative
            temperature=0.2, 
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"Error: {e}")
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