from flask import Flask, render_template, request, jsonify, send_file, url_for, Response
import os
from Emo_LLM.full_pipeline import process_text_to_video
import logging
import shutil
import socket
import json
import time
from urllib.request import urlopen
from queue import Queue
from threading import Thread

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/output')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# 全局进度跟踪器
progress_tracker = {
    'current_task': '',
    'progress': 0,
    'status': 'idle',
    'message': '',
    'error': None
}

# 用于存储SSE客户端连接的队列
clients = []

def update_progress(task, progress, message=''):
    """更新进度信息"""
    progress_tracker['current_task'] = task
    progress_tracker['progress'] = progress
    progress_tracker['message'] = message
    notify_clients()

def notify_clients():
    """通知所有SSE客户端"""
    msg = json.dumps({
        'task': progress_tracker['current_task'],
        'progress': progress_tracker['progress'],
        'message': progress_tracker['message'],
        'error': progress_tracker['error']
    })
    for client in clients[:]:
        try:
            client.put(msg)
        except:
            clients.remove(client)

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler(), 
                             logging.FileHandler("flask_app.log", mode='w')])

logger = logging.getLogger(__name__)

# 获取公网访问链接函数
def get_external_url(port=5000, base_url=None):
    """尝试获取可公网访问的URL"""
    # 如果在JupyterHub环境中运行
    try:
        # 尝试获取JupyterHub服务URL
        if 'JUPYTERHUB_SERVICE_PREFIX' in os.environ:
            service_prefix = os.environ['JUPYTERHUB_SERVICE_PREFIX']
            logger.info(f"检测到JupyterHub环境，服务前缀: {service_prefix}")
            # 构建代理URL
            proxy_url = f"{service_prefix}proxy/{port}/"
            return proxy_url
    except Exception as e:
        logger.warning(f"获取JupyterHub服务URL失败: {e}")
    
    # 尝试使用base_url
    if base_url:
        return f"{base_url}:{port}"
    
    # 尝试其他方法获取公网IP
    try:
        # 使用外部服务获取公网IP
        external_ip = json.loads(urlopen('https://api.ipify.org/?format=json').read())['ip']
        return f"http://{external_ip}:{port}"
    except Exception as e:
        logger.warning(f"获取公网IP失败: {e}")
    
    # 最后尝试获取本地IP
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return f"http://{local_ip}:{port}"
    except Exception as e:
        logger.warning(f"获取本地IP失败: {e}")
    
    # 如果所有方法都失败，返回localhost
    return f"http://localhost:{port}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/progress')
def progress():
    """SSE端点，用于发送实时进度更新"""
    def generate():
        q = Queue()
        clients.append(q)
        try:
            while True:
                result = q.get()
                yield f"data: {result}\n\n"
        except GeneratorExit:
            clients.remove(q)

    return Response(generate(), mimetype='text/event-stream')

@app.route('/generate', methods=['POST'])
def generate_video():
    try:
        input_text = request.form.get('text')
        if not input_text:
            return jsonify({'error': '请输入文本'}), 400

        logger.info(f"收到生成请求，输入文本: {input_text}")
        
        # 重置进度跟踪器
        progress_tracker['status'] = 'processing'
        progress_tracker['error'] = None
        progress_tracker['progress'] = 0
        
        def process_with_progress():
            try:
                # 更新进度：情感分析
                update_progress('emotion_analysis', 10, '正在进行情感分析...')
                time.sleep(1)  # 给前端一些时间显示进度
                
                # 处理输入并生成视频
                output_dir = app.config['UPLOAD_FOLDER']
                
                # 更新进度：生成视频
                update_progress('generating', 30, '正在生成视频内容...')
                output_path = process_text_to_video(input_text, output_dir)
                
                # 处理路径，确保可从前端访问
                if os.path.isabs(output_path):
                    filename = os.path.basename(output_path)
                    destination = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    # 更新进度：复制文件
                    update_progress('copying', 80, '正在处理生成的视频...')
                    if output_path != destination:
                        shutil.copy2(output_path, destination)
                        output_path = destination
                
                # 获取相对于static目录的路径
                static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
                if output_path.startswith(static_dir):
                    relative_path = os.path.relpath(output_path, start=static_dir)
                    video_url = url_for('static', filename=relative_path)
                else:
                    filename = os.path.basename(output_path)
                    video_url = url_for('static', filename=f'output/{filename}')
                
                logger.info(f"视频生成成功，URL: {video_url}")
                
                # 更新进度：完成
                update_progress('completed', 100, '视频生成完成！')
                
                # 通知客户端视频URL
                notify_clients()
                return video_url
                
            except Exception as e:
                logger.error(f"视频生成失败: {str(e)}", exc_info=True)
                progress_tracker['error'] = str(e)
                progress_tracker['status'] = 'error'
                notify_clients()
                raise
        
        # 在后台线程中处理
        thread = Thread(target=process_with_progress)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '视频生成已开始，请等待进度更新'
        })

    except Exception as e:
        logger.error(f"视频生成失败: {str(e)}", exc_info=True)
        return jsonify({'error': f'生成视频时出错: {str(e)}'}), 500

# 创建一个路由显示当前可用的访问链接
@app.route('/access_info')
def access_info():
    port = 5000  # 默认端口
    
    # 获取可能的访问URL
    local_url = f"http://localhost:{port}"
    
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        network_url = f"http://{local_ip}:{port}"
    except:
        network_url = "无法获取本地网络URL"
    
    try:
        external_ip = json.loads(urlopen('https://api.ipify.org/?format=json').read())['ip']
        public_url = f"http://{external_ip}:{port}"
    except:
        public_url = "无法获取公网URL"
    
    # 获取JupyterHub代理URL
    jupyter_url = ""
    if 'JUPYTERHUB_SERVICE_PREFIX' in os.environ:
        service_prefix = os.environ['JUPYTERHUB_SERVICE_PREFIX']
        jupyter_url = f"{service_prefix}proxy/{port}/"
    
    # 返回HTML页面显示信息
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>访问信息</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .url-box {{ 
                margin: 10px 0; 
                padding: 10px; 
                border: 1px solid #ddd; 
                border-radius: 5px;
            }}
            h2 {{ color: #333; }}
            a {{ color: #0066cc; }}
        </style>
    </head>
    <body>
        <h1>情感视频生成系统 - 访问链接</h1>
        
        <div class="url-box">
            <h2>本地访问</h2>
            <p><a href="{local_url}" target="_blank">{local_url}</a></p>
            <p>仅在运行服务器的机器上可用</p>
        </div>
        
        <div class="url-box">
            <h2>本地网络访问</h2>
            <p><a href="{network_url}" target="_blank">{network_url}</a></p>
            <p>在同一网络内的设备可用（可能需要防火墙设置）</p>
        </div>
        
        <div class="url-box">
            <h2>公网访问</h2>
            <p><a href="{public_url}" target="_blank">{public_url}</a></p>
            <p>如果服务器有公网IP且端口已开放，则任何人都可以访问</p>
        </div>
    """
    
    if jupyter_url:
        html += f"""
        <div class="url-box">
            <h2>JupyterHub代理访问 (推荐)</h2>
            <p><a href="{jupyter_url}" target="_blank">{jupyter_url}</a></p>
            <p>通过JupyterHub代理访问，最可靠的方式</p>
        </div>
        """
    
    html += """
    <div class="url-box">
        <h2>注意</h2>
        <p>如果您使用的是JupyterHub，请尝试JupyterHub代理链接。</p>
        <p>如果需要公网访问，您可能需要使用ngrok等工具进行端口转发。</p>
    </div>
    
    <p><a href="/" style="margin-top: 20px; display: inline-block;">返回主页</a></p>
    </body>
    </html>
    """
    
    return html

if __name__ == '__main__':
    # 获取可能的外部URL
    external_url = get_external_url()
    logger.info(f"Flask应用启动，静态文件目录: {app.config['UPLOAD_FOLDER']}")
    logger.info(f"尝试获取的外部访问URL: {external_url}")
    logger.info(f"您也可以访问 /access_info 路由查看所有可能的访问方式")
    
    # 使用0.0.0.0绑定所有接口，允许外部访问
    app.run(debug=True, host='0.0.0.0', port=5000) 