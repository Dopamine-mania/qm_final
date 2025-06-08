import os

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