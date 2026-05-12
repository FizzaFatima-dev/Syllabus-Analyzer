import os
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from analyzer import extract_text_from_pdf, analyze_syllabus, highlight_evidence

app = Flask(__name__)

# Use /tmp for Render's ephemeral filesystem
UPLOAD_FOLDER = '/tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            text = extract_text_from_pdf(filepath)
            results = analyze_syllabus(text)
            
            if not results:
                return jsonify({"error": "AI analysis failed"}), 500
            
            output_filename = "audited_" + filename
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
            highlight_evidence(filepath, output_path, results)
            
            return jsonify({
                **results,
                "pdf_url": f"/download/{output_filename}"
            })

        elif 'text_input' in request.form:
            text = request.form['text_input']
            results = analyze_syllabus(text)
            return jsonify(results)

        return jsonify({"error": "No input provided"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)