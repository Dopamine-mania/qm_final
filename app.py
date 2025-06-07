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
        'error': progress_tracker['error'],
        'video_url': progress_tracker.get('video_url', None)
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

def get_external_url():
    """尝试获取可以从外部访问的URL"""
    # 检查是否在JupyterHub环境中
    if 'JUPYTERHUB_SERVICE_PREFIX' in os.environ:
        # 在JupyterHub中，使用代理URL
        service_prefix = os.environ['JUPYTERHUB_SERVICE_PREFIX']
        logger.info(f"检测到JupyterHub环境，服务前缀: {service_prefix}")
        # 使用8080端口而不是5000
        return f"{service_prefix}proxy/8080/"
    
    # 尝试获取本机IP
    try:
        # 获取主机名
        hostname = socket.gethostname()
        # 获取IP
        ip = socket.gethostbyname(hostname)
        return f"http://{ip}:8080"
    except:
        # 如果无法获取外部IP，则使用localhost
        return "http://localhost:8080"

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
                
                # 确保输出目录存在
                output_dir = app.config['UPLOAD_FOLDER']
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"确保输出目录存在: {output_dir}")
                
                # 更新进度：生成视频
                update_progress('generating', 30, '正在生成视频内容...')
                
                try:
                    # 记录详细的调试信息
                    logger.info(f"调用process_text_to_video函数，参数: text={input_text}, output_dir={output_dir}")
                    output_path = process_text_to_video(input_text, output_dir)
                    logger.info(f"process_text_to_video返回的输出路径: {output_path}")
                except Exception as e:
                    logger.error(f"处理视频时出错: {str(e)}", exc_info=True)
                    progress_tracker['error'] = f"视频处理错误: {str(e)}"
                    progress_tracker['status'] = 'error'
                    notify_clients()
                    raise
                
                # 确保输出路径存在
                if not output_path or not os.path.exists(output_path):
                    error_msg = f"视频文件未生成或路径不存在: {output_path}"
                    logger.error(error_msg)
                    progress_tracker['error'] = error_msg
                    progress_tracker['status'] = 'error'
                    notify_clients()
                    raise Exception(error_msg)
                
                # 处理路径，确保可从前端访问
                if os.path.isabs(output_path):
                    filename = os.path.basename(output_path)
                    destination = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
                    # 更新进度：复制文件
                    update_progress('copying', 80, '正在处理生成的视频...')
                    logger.info(f"复制视频文件从 {output_path} 到 {destination}")
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
                logger.info(f"检查视频文件是否存在: {os.path.exists(output_path)}")
                
                # 更新进度：完成
                update_progress('completed', 100, '视频生成完成！')
                
                # 设置视频URL
                progress_tracker['video_url'] = video_url
                
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
        thread.daemon = True  # 设置为守护线程，确保主线程退出时会自动终止
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '视频生成已开始，请等待进度更新'
        })

    except Exception as e:
        logger.error(f"视频生成失败: {str(e)}", exc_info=True)
        return jsonify({'error': f'生成视频时出错: {str(e)}'}), 500

@app.route('/access_info')
def access_info():
    """返回所有可能的访问方式"""
    access_methods = []
    
    # JupyterHub代理URL (如果在JupyterHub环境中)
    if 'JUPYTERHUB_SERVICE_PREFIX' in os.environ:
        service_prefix = os.environ['JUPYTERHUB_SERVICE_PREFIX']
        # 使用8080端口
        proxy_url = f"{service_prefix}proxy/8080/"
        access_methods.append({
            "name": "JupyterHub代理访问",
            "url": proxy_url,
            "description": "通过JupyterHub代理访问（推荐）"
        })
    
    # 本地URL
    access_methods.append({
        "name": "本地访问",
        "url": "http://localhost:8080",
        "description": "本地直接访问（仅限本机）"
    })
    
    # 尝试获取本机IP
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        access_methods.append({
            "name": "局域网访问",
            "url": f"http://{ip}:8080",
            "description": "通过局域网IP访问（同一网络内的其他设备）"
        })
    except:
        pass
    
    # 尝试获取公网IP
    try:
        public_ip = urlopen('https://api.ipify.org').read().decode('utf8')
        access_methods.append({
            "name": "公网访问（需要端口转发）",
            "url": f"http://{public_ip}:8080",
            "description": "通过公网IP访问（需要配置路由器端口转发）"
        })
    except:
        pass
    
    return render_template('access_info.html', access_methods=access_methods)

if __name__ == '__main__':
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 获取可能的外部URL
    external_url = get_external_url()
    logger.info(f"Flask应用启动，静态文件目录: {app.config['UPLOAD_FOLDER']}")
    logger.info(f"尝试获取的外部访问URL: {external_url}")
    logger.info(f"您也可以访问 /access_info 路由查看所有可能的访问方式")
    
    # 使用0.0.0.0绑定所有接口，允许外部访问，使用不同端口8080
    app.run(debug=True, host='0.0.0.0', port=8080) 