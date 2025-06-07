document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('generatorForm');
    const progressContainer = document.getElementById('progressContainer');
    const resultContainer = document.getElementById('resultContainer');
    const resultVideo = document.getElementById('resultVideo');
    const errorContainer = document.getElementById('errorContainer');
    const errorMessage = document.getElementById('errorMessage');
    const submitButton = form.querySelector('button[type="submit"]');

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

        // 处理错误状态
        if (data.error) {
            errorMessage.textContent = data.error;
            errorContainer.classList.remove('hidden');
            progressContainer.classList.add('hidden');
            submitButton.disabled = false;
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
        }
    }

    function setupEventSource() {
        if (eventSource) {
            eventSource.close();
        }

        eventSource = new EventSource('/progress');
        
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Progress update:', data);
            
            updateProgress(data);

            // 如果进度完成，显示视频
            if (data.progress === 100) {
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

        eventSource.onerror = (error) => {
            console.error('EventSource failed:', error);
            eventSource.close();
            eventSource = null;
            errorMessage.textContent = '与服务器的连接中断';
            errorContainer.classList.remove('hidden');
            progressContainer.classList.add('hidden');
            submitButton.disabled = false;
        };
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 重置UI状态
        errorContainer.classList.add('hidden');
        resultContainer.classList.add('hidden');
        submitButton.disabled = true;
        progressContainer.classList.remove('hidden');

        // 重置进度条和图标状态
        progressBar.style.width = '0%';
        progressText.textContent = '0%';
        progressStatus.textContent = '准备中...';
        progressMessage.textContent = '';
        [step1Icon, step2Icon, step3Icon].forEach(icon => {
            icon.classList.remove('bg-green-500');
            icon.classList.add('bg-gray-200');
        });

        try {
            // 设置事件源以接收进度更新
            setupEventSource();
            
            const formData = new FormData(form);
            
            const response = await fetch('/generate', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '生成视频时出错');
            }

            console.log('Generation started:', data);

        } catch (error) {
            console.error("处理出错:", error);
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
}); 