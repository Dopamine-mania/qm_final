from flask import Flask, render_template, request, jsonify, send_file
import os
from Emo_LLM.full_pipeline import process_text_to_video
import logging

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/output'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_video():
    try:
        input_text = request.form.get('text')
        if not input_text:
            return jsonify({'error': 'No text provided'}), 400

        # Process the text and generate video
        output_path = process_text_to_video(input_text)
        
        # Get the relative path for the video
        relative_path = os.path.relpath(output_path, start=os.path.dirname(__file__))
        
        return jsonify({
            'success': True,
            'video_path': relative_path
        })

    except Exception as e:
        logging.error(f"Error generating video: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000) 