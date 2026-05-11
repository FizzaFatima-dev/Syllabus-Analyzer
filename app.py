from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import os
import uuid
from analyzer import extract_text_from_pdf, analyze_syllabus, highlight_evidence

app = Flask(__name__)
CORS(app)

# Use absolute path for Render stability
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def run_analysis():
    syllabus_text = request.form.get('text_input')
    file = request.files.get('file')
    
    if not file and not syllabus_text:
        return jsonify({"error": "No content provided"}), 400

    pdf_url = None
    if file:
        # Secure filename with UUID
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{unique_id}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        text = extract_text_from_pdf(filepath)
        
        # AI Analysis
        results_object = analyze_syllabus(text)
        if not results_object:
            return jsonify({"error": "AI Analysis failed"}), 500

        # Highlight PDF
        output_filename = "audited_" + filename
        output_pdf_path = os.path.join(UPLOAD_FOLDER, output_filename)
        highlight_evidence(filepath, output_pdf_path, results_object)
        pdf_url = f"/download/{output_filename}"
    else:
        # Text-only path
        text = syllabus_text
        results_object = analyze_syllabus(text)
        if not results_object:
            return jsonify({"error": "AI Analysis failed"}), 500

    return jsonify({
        "audit": results_object['audit'],
        "suggestion": results_object.get('suggestion', ''),
        "pdf_url": pdf_url
    })

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)