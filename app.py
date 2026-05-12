from flask import Flask, request, jsonify, send_from_directory
import os
from analyzer import extract_text_from_pdf, analyze_syllabus, highlight_evidence
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Render has a small disk, so we use /tmp for temporary files
UPLOAD_FOLDER = '/tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Increase limit to 16MB just in case
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # 1. Handle File Upload
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Extract and Analyze
            text = extract_text_from_pdf(filepath)
            results = analyze_syllabus(text)
            
            if not results:
                return jsonify({"error": "AI failed to analyze the document"}), 500
            
            # Create Highlighted PDF
            output_filename = "audited_" + filename
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            highlight_evidence(filepath, output_path, results)
            
            # Return JSON (This is what the frontend needs!)
            return jsonify({
                **results,
                "pdf_url": f"/download/{output_filename}"
            })

        # 2. Handle Text Input
        elif 'text_input' in request.form:
            text = request.form['text_input']
            results = analyze_syllabus(text)
            return jsonify(results)

        return jsonify({"error": "No input provided"}), 400

    except Exception as e:
        # This prevents the "Unexpected token <" error by returning JSON instead of a crash page
        print(f"Server Crash: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)