from flask import Flask, render_template, request, jsonify, send_file, url_for, Response, send_from_directory
import os
from Emo_LLM.full_pipeline import process_text_to_video
import logging
import shutil
import socket
import json
import time
import psutil
import sys
from urllib.request import urlopen
from queue import Queue
from threading import Thread
from werkzeug.middleware.proxy_fix import ProxyFix
from urllib.parse import urljoin

# 配置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler(), 
                             logging.FileHandler("flask_app.log", mode='w')])

logger = logging.getLogger(__name__)

# 使用代理前缀创建Flask应用
proxy_prefix = os.environ.get('JUPYTERHUB_SERVICE_PREFIX', '')
app = Flask(__name__)

# 配置Flask应用
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'output')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# 配置JupyterHub相关设置
if proxy_prefix:
    app.config['APPLICATION_ROOT'] = proxy_prefix.rstrip('/')
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    app.config['SERVER_NAME'] = 'hub.comp-teach.qmul.ac.uk'  # JupyterHub的主机名

if proxy_prefix:
    logger.info(f"检测到JupyterHub环境，配置代理前缀: {proxy_prefix}")

# 全局进度跟踪器
progress_tracker = {
    'current_task': None,
    'progress': 0,
    'status': 'idle',
    'message': '',
    'error': None,
    'video_url': None
}

# 用于存储SSE客户端连接的队列
clients = []

def update_progress(task: str, progress: int, message: str):
    """更新进度并通知所有客户端"""
    logger.info(f"更新进度: task={task}, progress={progress}, message={message}")
    progress_tracker['current_task'] = task
    progress_tracker['progress'] = progress
    progress_tracker['message'] = message
    notify_clients()

def notify_clients():
    """向所有连接的客户端发送更新"""
    data = json.dumps({
        'task': progress_tracker['current_task'],
        'progress': progress_tracker['progress'],
        'message': progress_tracker['message'],
        'error': progress_tracker['error'],
        'video_url': progress_tracker.get('video_url', None)
    })
    for client in clients[:]:  # 使用切片创建副本以避免并发修改问题
        try:
            client.put(data)
        except:
            if client in clients:
                clients.remove(client)

def get_jupyterhub_prefix():
    """获取JupyterHub代理前缀"""
    return os.environ.get('JUPYTERHUB_SERVICE_PREFIX', '')

def get_file_url(filepath: str) -> str:
    """生成文件的URL，处理JupyterHub代理路径"""
    # 获取相对于static目录的路径
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    if filepath.startswith(static_dir):
        relative_path = os.path.relpath(filepath, start=static_dir)
    else:
        relative_path = os.path.basename(filepath)
        if not relative_path.startswith('output/'):
            relative_path = f'output/{relative_path}'

    # 构建基础URL
    jupyterhub_prefix = os.environ.get('JUPYTERHUB_SERVICE_PREFIX', '')
    if jupyterhub_prefix:
        # JupyterHub环境
        base_url = f"{jupyterhub_prefix.rstrip('/')}/proxy/8080/static/"
        return f"{base_url}{relative_path}"
    else:
        # 本地环境
        return f"/static/{relative_path}"

    # 记录生成的URL
    logger.info(f"生成的文件URL: {url}")
    return url

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
    """主页"""
    logger.info("访问主页")
    return render_template('index.html')

@app.route('/progress')
def progress():
    """SSE端点，用于发送实时进度更新"""
    logger.info("新的SSE连接建立")
    
    def generate():
        q = Queue()
        clients.append(q)
        try:
            # 立即发送当前状态
            current_state = json.dumps({
                'task': progress_tracker['current_task'],
                'progress': progress_tracker['progress'],
                'message': progress_tracker['message'],
                'error': progress_tracker['error'],
                'video_url': progress_tracker.get('video_url', None)
            })
            yield f"data: {current_state}\n\n"
            
            while True:
                result = q.get()
                yield f"data: {result}\n\n"
        except GeneratorExit:
            logger.info("SSE连接关闭")
            if q in clients:
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
        progress_tracker['video_url'] = None
        
        def process_with_progress():
            try:
                # 更新进度：情感分析
                update_progress('emotion_analysis', 10, '正在进行情感分析...')
                time.sleep(1)
                
                # 确保输出目录存在
                output_dir = app.config['UPLOAD_FOLDER']
                os.makedirs(output_dir, exist_ok=True)
                logger.info(f"确保输出目录存在: {output_dir}")
                
                # 更新进度：生成视频
                update_progress('generating', 30, '正在生成视频内容...')
                
                try:
                    logger.info(f"调用process_text_to_video函数，参数: text={input_text}, output_dir={output_dir}")
                    output_path = process_text_to_video(input_text, output_dir)
                    logger.info(f"process_text_to_video返回的输出路径: {output_path}")
                except Exception as e:
                    logger.error(f"处理视频时出错: {str(e)}", exc_info=True)
                    progress_tracker['error'] = f"视频处理错误: {str(e)}"
                    progress_tracker['status'] = 'error'
                    notify_clients()
                    raise
                
                if not output_path or not os.path.exists(output_path):
                    error_msg = f"视频文件未生成或路径不存在: {output_path}"
                    logger.error(error_msg)
                    progress_tracker['error'] = error_msg
                    progress_tracker['status'] = 'error'
                    notify_clients()
                    raise Exception(error_msg)
                
                # 处理路径，确保可从前端访问
                filename = os.path.basename(output_path)
                destination = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # 更新进度：复制文件
                update_progress('copying', 80, '正在处理生成的视频...')
                logger.info(f"复制视频文件从 {output_path} 到 {destination}")
                if output_path != destination:
                    shutil.copy2(output_path, destination)
                    output_path = destination
                
                # 生成视频URL
                video_url = create_file_url(output_path)
                logger.info(f"视频生成成功，URL: {video_url}")
                
                # 更新进度：完成
                update_progress('completed', 100, '视频生成完成！')
                
                # 设置视频URL
                progress_tracker['video_url'] = video_url
                progress_tracker['status'] = 'completed'
                
                # 通知客户端
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

# 健康检查端点
@app.route('/health')
def health_check():
    """健康检查端点，用于确认服务器运行状态"""
    logger.info("健康检查请求")
    return jsonify({
        'status': 'ok',
        'timestamp': time.time(),
        'jupyterhub_prefix': os.environ.get('JUPYTERHUB_SERVICE_PREFIX', None),
        'current_progress': progress_tracker['progress'],
        'active_clients': len(clients)
    })

def create_file_url(filepath: str) -> str:
    """为文件创建可访问的URL"""
    # 获取文件名
    filename = os.path.basename(filepath)
    
    # 确保文件在static/output目录中
    if not filename.startswith('output/'):
        filename = f'output/{filename}'
    
    # 获取JupyterHub前缀
    jupyterhub_prefix = os.environ.get('JUPYTERHUB_SERVICE_PREFIX', '')
    
    if jupyterhub_prefix:
        # JupyterHub环境
        # 使用相对路径，让浏览器基于当前URL构建完整路径
        url = f"./static/{filename}"
    else:
        # 本地环境
        url = f"/static/{filename}"
    
    logger.info(f"为文件 {filepath} 创建URL: {url}")
    return url

def find_and_kill_process_on_port(port):
    """查找并关闭占用指定端口的进程"""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                connections = proc.net_connections()  # 使用net_connections()替代connections()
                for conn in connections:
                    if hasattr(conn, 'laddr') and conn.laddr.port == port:
                        # 检查是否是Python进程且运行的是当前脚本
                        if proc.name() == 'python.exe' or proc.name() == 'python':
                            cmdline = proc.cmdline()
                            if len(cmdline) > 1 and os.path.basename(__file__) in cmdline[1]:
                                logger.info(f"找到旧的应用进程 (PID: {proc.pid})，正在终止...")
                                proc.terminate()
                                proc.wait(timeout=3)
                                logger.info(f"成功终止旧进程")
                                return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        logger.error(f"检查端口占用时出错: {str(e)}")
    return False

def get_all_access_urls(port):
    """获取所有可能的访问URL"""
    access_urls = []
    
    # 获取本地访问URL
    local_url = f"http://localhost:{port}"
    access_urls.append(("本地访问", local_url, "仅限本机访问"))
    
    # 获取局域网访问URL
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        lan_url = f"http://{ip}:{port}"
        access_urls.append(("局域网访问", lan_url, "同一网络下的其他设备可访问"))
    except:
        pass
    
    # 获取JupyterHub访问URL
    if 'JUPYTERHUB_SERVICE_PREFIX' in os.environ:
        service_prefix = os.environ['JUPYTERHUB_SERVICE_PREFIX']
        # 使用完整的域名
        jupyter_url = f"https://hub.comp-teach.qmul.ac.uk{service_prefix}proxy/{port}/"
        access_urls.append(("JupyterHub访问", jupyter_url, "通过JupyterHub代理访问（推荐）"))
    
    # 尝试获取公网IP
    try:
        public_ip = urlopen('https://api.ipify.org').read().decode('utf8')
        public_url = f"http://{public_ip}:{port}"
        access_urls.append(("公网访问", public_url, "需要配置端口转发后可从外网访问"))
    except:
        pass
    
    return access_urls

if __name__ == '__main__':
    # 确保上传目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 获取端口号
    port = int(os.environ.get('PORT', 8080))
    original_port = port
    
    # 尝试启动服务器，如果端口被占用则尝试其他端口
    max_port_attempts = 10
    for attempt in range(max_port_attempts):
        try:
            # 检查是否有旧进程占用端口
            if find_and_kill_process_on_port(port):
                logger.info(f"已清理端口 {port} 的旧进程")
                time.sleep(1)  # 等待端口完全释放
            
            logger.info(f"尝试在端口 {port} 启动服务器...")
            
            # 在启动前打印访问链接
            print("\n" + "="*50)
            print("应用启动中，您可以通过以下链接访问：")
            print("="*50)
            
            access_urls = get_all_access_urls(port)
            for name, url, desc in access_urls:
                print(f"\n{name}:")
                print(f"URL: {url}")
                print(f"说明: {desc}")
            
            print("\n" + "="*50)
            print("\n特别说明：")
            print("1. JupyterHub访问链接可以直接分享给其他人使用")
            print("2. 其他链接仅在对应网络环境下可用")
            print("3. 服务器正在运行中，请勿关闭此终端")
            print("="*50 + "\n")
            
            # 配置Flask应用
            if 'JUPYTERHUB_SERVICE_PREFIX' in os.environ:
                # 在JupyterHub环境中禁用调试模式，避免自动重启
                debug_mode = False
                # 确保正确设置代理
                app.config['PREFERRED_URL_SCHEME'] = 'https'
                app.config['SERVER_NAME'] = 'hub.comp-teach.qmul.ac.uk'
            else:
                debug_mode = True
            
            # 启动服务器
            app.run(
                host='0.0.0.0', 
                port=port, 
                debug=debug_mode,  # 在JupyterHub环境中禁用调试模式
                threaded=True,
                use_reloader=False  # 禁用重载器，避免进程重启
            )
            break  # 如果成功启动，跳出循环
            
        except OSError as e:
            if "Address already in use" in str(e) and attempt < max_port_attempts - 1:
                logger.warning(f"端口 {port} 已被占用，尝试端口 {port + 1}")
                port += 1
            else:
                logger.error(f"无法启动服务器: {str(e)}")
                raise 