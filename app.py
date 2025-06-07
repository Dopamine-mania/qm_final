from flask import Flask, render_template, request, jsonify, send_file, url_for
import os
from Emo_LLM.full_pipeline import process_text_to_video
import logging
import shutil

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/output')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler(), 
                             logging.FileHandler("flask_app.log", mode='w')])

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_video():
    try:
        input_text = request.form.get('text')
        if not input_text:
            return jsonify({'error': '请输入文本'}), 400

        logger.info(f"收到生成请求，输入文本: {input_text}")
        
        # 处理输入并生成视频
        output_dir = app.config['UPLOAD_FOLDER']
        output_path = process_text_to_video(input_text, output_dir)
        
        # 处理路径，确保可从前端访问
        # 如果是绝对路径，复制到static/output目录
        if os.path.isabs(output_path):
            filename = os.path.basename(output_path)
            destination = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # 如果不在static目录中，复制过来
            if output_path != destination:
                shutil.copy2(output_path, destination)
                output_path = destination
        
        # 获取相对于static目录的路径
        static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
        if output_path.startswith(static_dir):
            relative_path = os.path.relpath(output_path, start=static_dir)
            video_url = url_for('static', filename=relative_path)
        else:
            # 如果不在static目录，取文件名并假设它在output目录
            filename = os.path.basename(output_path)
            video_url = url_for('static', filename=f'output/{filename}')
        
        logger.info(f"视频生成成功，URL: {video_url}")
        
        return jsonify({
            'success': True,
            'video_path': video_url
        })

    except Exception as e:
        logger.error(f"视频生成失败: {str(e)}", exc_info=True)
        return jsonify({'error': f'生成视频时出错: {str(e)}'}), 500

if __name__ == '__main__':
    logger.info(f"Flask应用启动，静态文件目录: {app.config['UPLOAD_FOLDER']}")
    app.run(debug=True, port=5000) 