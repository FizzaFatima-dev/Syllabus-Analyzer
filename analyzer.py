import os
import json
import re
import fitz  # PyMuPDF for handling PDFs
import docx2txt  # For Word documents (.docx)
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    if ext == ".pdf":
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
    elif ext in [".docx", ".doc"]:
        text = docx2txt.process(file_path)
    else:
        raise ValueError("Unsupported file format!")
    return text

def analyze_syllabus(syllabus_text):
    prompt = f"""
    You are an Expert Curriculum Architect specializing in the Indian National Education Policy (NEP) framework.
    Your task is to take the raw syllabus text provided and restructure it entirely into a standardized, tabular university curriculum matrix.

    =========================================
    CRITICAL CLASSIFICATION MANDATE (STRICT):
    =========================================
    You must look at the topics with an implicit regional/national lens. 
    - ANY mention of data visualization, socio-economic analysis, public healthcare metrics, regional governance, or national development datasets MUST be treated as implicitly relevant to the Indian development context.
    - You MUST wrap these phrases inside the IKS badge: <span class="badge-iks">...</span>
    - Consequently, ensure the global "IKS" percentage score heavily reflects this coverage (do not leave it low if these data/governance topics are present).

    Organize the syllabus content into clear Units. For each structural row, determine:
    1. unit: Unit Number
    2. contents: Detailed Breakdown of topics. 
       Wrap nearly ALL applicable key items inside granular HTML span tags corresponding to the matching pillar badges phrase-by-phrase:
       - Wrap AI, Machine Learning, Data Analytics, Python, tools, or algorithms inside: <span class="badge-ai">...</span>
       - Wrap fundamental practical skills, general definitions, architecture, or standard procedures inside: <span class="badge-skill">...</span>
       - Wrap socio-economic data, public healthcare, governance, or development datasets/visualization inside: <span class="badge-iks">...</span>
       - Wrap business framework, tradeoffs, industry metrics, management, or strategy context inside: <span class="badge-startup">...</span>

    3. co: Course Outcomes Mapped (e.g., CO1, CO2)
    4. cognitive_level: Cognitive Levels (e.g., Acquire, Analyze, Implement, Understand, Apply)
    5. relevance: Relevance (L/R/N/G - Local, Regional, National, Global)
    6. pillars: High-level primary pillar classification list (Make sure to include "IKS" if governance/data visualization is present).
    7. sdg_mapped: Provide specific SDG mappings based on topics (e.g., "SDG 3, SDG 4, SDG 9").

    Return ONLY a JSON object structured exactly like this:
    {{
        "scores": {{
            "SDG": "percentage",
            "IKS": "percentage",
            "STARTUP": "percentage",
            "AI": "percentage"
        }},
        "course_outcomes_summary": "High-level compliance summary.",
        "taxonomy": {{ "bloom_level": "L4 - Analyzing", "obe_status": "Highly Compliant" }},
        "suggestion": "Recommendations for enhancement.",
        "table_rows": [
            {{
                "unit": "I",
                "contents": "Example formatted text using the requested span tags.",
                "co": "CO1",
                "cognitive_level": "Apply",
                "relevance": "N",
                "pillars": "IKS, AI / Tech Integration",
                "sdg_mapped": "SDG 8"
            }}
        ]
    }}

    Syllabus Text: {syllabus_text[:20000]}
    """
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e: 
        print(f"Error calling LLM: {e}")
        return None