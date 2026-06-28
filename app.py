import os
import tempfile 
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from analyzer import extract_text_from_file, analyze_syllabus

app = Flask(__name__)

UPLOAD_FOLDER = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        text = extract_text_from_file(filepath)
        if not text.strip():
            return jsonify({"error": "Could not read text from document"}), 400

        results = analyze_syllabus(text)
        if not results:
            return jsonify({"error": "AI analysis failed."}), 500

        return jsonify(results)

    except Exception as e:
        print(f"Server Error: {str(e)}")
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)