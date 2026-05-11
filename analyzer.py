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
    safe_text = syllabus_text[:4500] 
    
    prompt = f"""
    You are an Expert Academic Consultant specializing in NEP 2020. 
    Analyze the syllabus provided to map it against SDG, IKS, and Entrepreneurship.

    PERSONA & TONE:
    - Be a supportive peer to the lecturer. 
    - Use "Semantic Mapping": If a topic implies a goal (e.g., 'Water Management' implies SDG 6), give credit.
    - Be honest but encouraging. A score of 0% should only be used if there is absolutely no relation.

    SCORING RUBRIC:
    - 70-100%: Topic is explicitly mentioned and detailed.
    - 40-65%: Topic is implied or related modules exist.
    - 10-35%: Very brief mention or indirect connection.

    CRITICAL: For 'evidence', you MUST extract 3-5 words EXACTLY as they appear in the text for the highlighter.

    Text: {safe_text}
    """
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            # 0.3 provides "Professional Intuition" while remaining reliable
            temperature=0.3, 
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