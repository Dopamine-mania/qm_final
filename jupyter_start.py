#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
JupyterHub环境下启动Flask应用的辅助脚本
该脚本帮助用户在JupyterHub环境中获取可用的公网访问链接
"""

import os
import sys
import time
import threading
import webbrowser
import subprocess
import socket
import json
from urllib.request import urlopen
from IPython.display import display, HTML

PORT = 5000  # Flask应用端口

def get_app_path():
    """获取Flask应用的路径"""
    # 尝试找到app.py文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, 'app.py')
    
    if not os.path.exists(app_path):
        # 如果当前目录下没有，尝试搜索
        for root, dirs, files in os.walk(current_dir):
            if 'app.py' in files:
                app_path = os.path.join(root, 'app.py')
                break
    
    return app_path

def get_access_urls(port=PORT):
    """获取所有可能的访问URL"""
    urls = {}
    
    # 本地访问URL
    urls['local'] = f"http://localhost:{port}"
    
    # 本地网络URL
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        urls['network'] = f"http://{local_ip}:{port}"
    except:
        urls['network'] = None
    
    # 公网URL
    try:
        external_ip = json.loads(urlopen('https://api.ipify.org/?format=json').read())['ip']
        urls['public'] = f"http://{external_ip}:{port}"
    except:
        urls['public'] = None
    
    # JupyterHub代理URL
    if 'JUPYTERHUB_SERVICE_PREFIX' in os.environ:
        service_prefix = os.environ['JUPYTERHUB_SERVICE_PREFIX']
        urls['jupyterhub'] = f"{service_prefix}proxy/{port}/"
    else:
        urls['jupyterhub'] = None
    
    return urls

def start_flask_app():
    """启动Flask应用"""
    app_path = get_app_path()
    
    if not os.path.exists(app_path):
        print("错误: 找不到app.py文件")
        return False
    
    print(f"正在启动Flask应用: {app_path}")
    
    # 使用subprocess启动Flask应用
    try:
        # 转到app.py所在目录
        os.chdir(os.path.dirname(app_path))
        
        # 构建命令
        cmd = [sys.executable, app_path]
        
        # 在后台运行Flask应用
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待应用启动
        time.sleep(3)
        
        # 检查进程是否仍在运行
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print("启动失败!")
            print(f"输出: {stdout}")
            print(f"错误: {stderr}")
            return False
            
        print("Flask应用已在后台启动")
        return True
    
    except Exception as e:
        print(f"启动应用出错: {e}")
        return False

def display_access_info():
    """显示访问信息"""
    urls = get_access_urls()
    
    html = """
    <div style="font-family: Arial, sans-serif; margin: 20px; padding: 20px; border: 1px solid #ddd; border-radius: 5px;">
        <h2 style="color: #333;">情感视频生成系统 - 访问链接</h2>
    """
    
    if urls['jupyterhub']:
        html += f"""
        <div style="margin: 15px 0; padding: 15px; border: 1px solid #5cb85c; border-radius: 5px; background-color: #f9fff9;">
            <h3 style="color: #5cb85c;">✅ JupyterHub代理访问 (推荐)</h3>
            <p><a href="{urls['jupyterhub']}" target="_blank" style="color: #5cb85c;">{urls['jupyterhub']}</a></p>
            <p><strong>这是公网可访问的链接，可以分享给他人！</strong></p>
            <button onclick="window.open('{urls['jupyterhub']}', '_blank')" 
                    style="background-color: #5cb85c; color: white; border: none; padding: 10px 15px; border-radius: 4px; cursor: pointer;">
                打开应用
            </button>
        </div>
        """
    
    html += f"""
    <div style="margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
        <h3>本地访问</h3>
        <p><a href="{urls['local']}" target="_blank">{urls['local']}</a></p>
        <p>仅在运行服务器的机器上可用</p>
    </div>
    """
    
    if urls['network']:
        html += f"""
        <div style="margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
            <h3>本地网络访问</h3>
            <p><a href="{urls['network']}" target="_blank">{urls['network']}</a></p>
            <p>在同一网络内的设备可用（可能需要防火墙设置）</p>
        </div>
        """
    
    if urls['public']:
        html += f"""
        <div style="margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
            <h3>公网访问</h3>
            <p><a href="{urls['public']}" target="_blank">{urls['public']}</a></p>
            <p>如果服务器有公网IP且端口已开放，则任何人都可以访问</p>
        </div>
        """
    
    html += """
    <div style="margin: 15px 0; padding: 15px; border: 1px solid #f0ad4e; border-radius: 5px; background-color: #fffcf5;">
        <h3 style="color: #f0ad4e;">⚠️ 注意</h3>
        <p>请使用上面提供的JupyterHub代理链接分享给他人，这是最可靠的公网访问方式。</p>
        <p>您也可以在应用启动后访问 /access_info 路径查看更多访问选项。</p>
    </div>
    
    <p style="margin-top: 20px; color: #666;">应用正在后台运行，关闭此输出不会停止应用。</p>
    </div>
    """
    
    return HTML(html)

def main():
    """主函数"""
    print("正在启动情感视频生成系统...")
    
    # 启动Flask应用
    if start_flask_app():
        # 显示访问信息
        display(display_access_info())
        
        # 如果是在JupyterHub环境中，自动打开应用
        urls = get_access_urls()
        if urls['jupyterhub']:
            print(f"\n✅ 公网访问链接: {urls['jupyterhub']}")
            print("您可以将此链接分享给他人，他们可以通过该链接访问应用。")
            
            # 尝试自动打开浏览器
            try:
                webbrowser.open(urls['jupyterhub'])
            except:
                pass
        else:
            print("\n应用已启动，请使用上面的链接访问。")
    else:
        print("\n❌ 应用启动失败，请检查错误信息。")

if __name__ == "__main__":
    main() 