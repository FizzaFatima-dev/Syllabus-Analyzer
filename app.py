import os
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from analyzer import extract_text_from_pdf, analyze_syllabus, highlight_evidence

app = Flask(__name__)

# Render ke liye /tmp folder sabse best hai (writable hota hai)
UPLOAD_FOLDER = '/tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # 1. Check if file exists in request
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # 2. Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # 3. Extract Text
        text = extract_text_from_pdf(filepath)
        if not text.strip():
            return jsonify({"error": "Could not read text from PDF"}), 400

        # 4. AI Analysis
        results = analyze_syllabus(text)
        if not results:
            return jsonify({"error": "AI analysis failed. Model might be busy."}), 500

        # 5. Generate Highlighted PDF
        output_filename = "audited_" + filename
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        # Ismein humne 'quads' wala fix backend (analyzer.py) mein kar diya hai
        highlight_evidence(filepath, output_path, results)

        # 6. Return Data + PDF Link
        return jsonify({
            **results,
            "pdf_url": f"/download/{output_filename}"
        })

    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Local testing ke liye
    app.run(host='0.0.0.0', port=5000, debug=True)