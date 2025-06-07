document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('generatorForm');
    const progressContainer = document.getElementById('progressContainer');
    const resultContainer = document.getElementById('resultContainer');
    const resultVideo = document.getElementById('resultVideo');
    const errorContainer = document.getElementById('errorContainer');
    const errorMessage = document.getElementById('errorMessage');
    const submitButton = form.querySelector('button[type="submit"]');
    const connectionStatus = document.getElementById('connection-status');
    const connectionDot = document.getElementById('connection-dot');

    // 进度相关元素
    const progressBar = document.getElementById('progressBar');
    const progressText = document.getElementById('progressText');
    const progressStatus = document.getElementById('progressStatus');
    const progressMessage = document.getElementById('progressMessage');
    
    // 步骤图标
    const step1Icon = document.getElementById('step1Icon');
    const step2Icon = document.getElementById('step2Icon');
    const step3Icon = document.getElementById('step3Icon');

    let eventSource = null;

    // 添加调试功能
    function debugLog(message, data) {
        console.log(`[DEBUG] ${message}`, data || '');
        // 如果页面上有调试元素，也可以显示在页面上
        if (window.debugElement) {
            const debugItem = document.createElement('div');
            debugItem.textContent = `${new Date().toISOString()} - ${message}`;
            window.debugElement.appendChild(debugItem);
        }
    }

    function getBaseUrl() {
        // 获取当前URL的路径部分
        const pathParts = window.location.pathname.split('/');
        // 在JupyterHub环境中，URL格式为 /user/{username}/proxy/{port}/
        const proxyIndex = pathParts.indexOf('proxy');
        if (proxyIndex !== -1) {
            // 返回到proxy端口的完整路径
            return pathParts.slice(0, proxyIndex + 2).join('/');
        }
        return '';
    }

    function setupEventSource() {
        if (eventSource) {
            eventSource.close();
        }

        const baseUrl = getBaseUrl();
        const progressUrl = `${baseUrl}/progress`;
        debugLog('设置SSE连接URL:', progressUrl);

        eventSource = new EventSource(progressUrl);
        
        eventSource.onopen = () => {
            debugLog('SSE连接已建立');
            connectionStatus.textContent = '服务器连接正常';
            connectionStatus.classList.remove('bg-yellow-100', 'text-yellow-800');
            connectionStatus.classList.add('bg-green-100', 'text-green-800');
            connectionDot.classList.remove('bg-yellow-500');
            connectionDot.classList.add('bg-green-500');
        };

        eventSource.onerror = () => {
            debugLog('SSE连接错误');
            connectionStatus.textContent = '服务器连接断开';
            connectionStatus.classList.remove('bg-green-100', 'text-green-800');
            connectionStatus.classList.add('bg-red-100', 'text-red-800');
            connectionDot.classList.remove('bg-green-500');
            connectionDot.classList.add('bg-red-500');
        };

        eventSource.onmessage = (event) => {
            debugLog('收到进度更新', event.data);
            const data = JSON.parse(event.data);
            updateProgress(data);

            // 如果进度完成，显示视频
            if (data.progress === 100) {
                // 检查是否有视频URL
                if (data.video_url) {
                    debugLog('收到视频URL:', data.video_url);
                    // 确保视频URL包含正确的基础路径
                    const baseUrl = getBaseUrl();
                    const fullVideoUrl = data.video_url.startsWith('http') ? 
                        data.video_url : 
                        `${baseUrl}${data.video_url.startsWith('/') ? '' : '/'}${data.video_url}`;
                    
                    resultVideo.src = fullVideoUrl;
                    
                    resultVideo.onloadeddata = () => {
                        debugLog('视频加载完成');
                    };
                    
                    resultVideo.onerror = (err) => {
                        debugLog('视频加载失败:', err);
                        errorMessage.textContent = '视频加载失败，请检查网络连接或重试';
                        errorContainer.classList.remove('hidden');
                    };
                }
                
                // 等待一小段时间确保视频文件已经准备好
                setTimeout(() => {
                    resultContainer.classList.remove('hidden');
                    resultContainer.classList.add('fade-in');
                    resultContainer.scrollIntoView({ behavior: 'smooth' });
                    
                    // 关闭事件源
                    eventSource.close();
                    eventSource = null;
                    
                    // 重置按钮状态
                    submitButton.disabled = false;
                }, 1000);
            }
        };
    }

    function updateProgress(data) {
        // 更新进度条
        progressBar.style.width = `${data.progress}%`;
        progressText.textContent = `${data.progress}%`;
        progressMessage.textContent = data.message;

        // 更新步骤状态
        const steps = {
            'emotion_analysis': { element: step1Icon, threshold: 10 },
            'generating': { element: step2Icon, threshold: 30 },
            'copying': { element: step3Icon, threshold: 80 }
        };

        // 更新步骤图标
        Object.entries(steps).forEach(([key, info]) => {
            if (data.progress >= info.threshold) {
                info.element.classList.remove('bg-gray-200');
                info.element.classList.add('bg-green-500');
            }
        });

        // 处理完成状态
        if (data.progress === 100) {
            progressStatus.textContent = '完成！';
            progressStatus.classList.add('text-green-500');
        } else {
            progressStatus.textContent = data.message;
        }
    }

    // 初始化SSE连接
    setupEventSource();

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 禁用提交按钮
        submitButton.disabled = true;
        
        // 重置容器状态
        errorContainer.classList.add('hidden');
        resultContainer.classList.add('hidden');
        progressContainer.classList.remove('hidden');
        
        // 重置进度条和图标
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
        [step1Icon, step2Icon, step3Icon].forEach(icon => {
            icon.classList.remove('bg-green-500');
            icon.classList.add('bg-gray-200');
        });

        try {
            // 设置事件源以接收进度更新
            setupEventSource();
            
            const formData = new FormData(form);
            const inputText = formData.get('text');
            debugLog(`开始处理文本: "${inputText}"`);
            
            // 获取完整的生成请求URL
            const baseUrl = getBaseUrl();
            const generateUrl = `${baseUrl}/generate`;
            debugLog('发送生成请求:', generateUrl);
            
            const response = await fetch(generateUrl, {
                method: 'POST',
                body: formData
            });

            debugLog('收到响应:', response.status);
            
            const data = await response.json();
            debugLog('响应数据:', data);

            if (!response.ok) {
                throw new Error(data.error || '生成视频时出错');
            }

            debugLog('生成任务已启动:', data);

        } catch (error) {
            debugLog("处理出错:", error);
            errorMessage.textContent = error.message;
            errorContainer.classList.remove('hidden');
            errorContainer.classList.add('fade-in');
            progressContainer.classList.add('hidden');
            submitButton.disabled = false;
            
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
        }
    });

    // 添加一个调试元素到页面（可选）
    function addDebugElement() {
        const debugDiv = document.createElement('div');
        debugDiv.id = 'debug-log';
        debugDiv.style.cssText = 'position: fixed; bottom: 0; right: 0; width: 400px; max-height: 300px; overflow-y: auto; background: rgba(0,0,0,0.8); color: #0f0; padding: 10px; font-family: monospace; font-size: 12px; z-index: 9999; display: none;';
        document.body.appendChild(debugDiv);
        
        const debugToggle = document.createElement('button');
        debugToggle.textContent = 'Debug';
        debugToggle.style.cssText = 'position: fixed; bottom: 0; right: 0; z-index: 10000; padding: 5px; background: #333; color: #fff; border: none;';
        debugToggle.onclick = () => {
            debugDiv.style.display = debugDiv.style.display === 'none' ? 'block' : 'none';
        };
        document.body.appendChild(debugToggle);
        
        window.debugElement = debugDiv;
        
        debugLog('调试日志已初始化');
    }
    
    // 重置表单处理
    window.resetForm = () => {
        form.reset();
        errorContainer.classList.add('hidden');
        resultContainer.classList.add('hidden');
        progressContainer.classList.add('hidden');
        submitButton.disabled = false;
        
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }

        // 重置进度相关元素
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
        progressStatus.textContent = '准备中...';
        progressMessage.textContent = '';
        [step1Icon, step2Icon, step3Icon].forEach(icon => {
            icon.classList.remove('bg-green-500');
            icon.classList.add('bg-gray-200');
        });
    };
    
    // 添加调试元素
    addDebugElement();
}); 