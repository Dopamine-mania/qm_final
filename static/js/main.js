document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('generatorForm');
    const progressContainer = document.getElementById('progressContainer');
    const resultContainer = document.getElementById('resultContainer');
    const resultVideo = document.getElementById('resultVideo');
    const errorContainer = document.getElementById('errorContainer');
    const errorMessage = document.getElementById('errorMessage');
    const submitButton = form.querySelector('button[type="submit"]');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 重置UI状态
        errorContainer.classList.add('hidden');
        resultContainer.classList.add('hidden');
        submitButton.disabled = true;
        progressContainer.classList.remove('hidden');

        try {
            const formData = new FormData(form);
            
            const response = await fetch('/generate', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || '生成视频时出错');
            }

            // 更新视频源并显示结果
            console.log("收到视频路径:", data.video_path);
            resultVideo.src = data.video_path;
            
            // 确保视频加载完毕后显示
            resultVideo.onloadeddata = () => {
                console.log("视频加载完成");
                resultContainer.classList.remove('hidden');
                resultContainer.classList.add('fade-in');
                
                // 滚动到结果区域
                resultContainer.scrollIntoView({ behavior: 'smooth' });
            };
            
            // 处理视频加载错误
            resultVideo.onerror = (err) => {
                console.error("视频加载失败:", err);
                throw new Error(`视频加载失败: ${data.video_path}`);
            };
            
            // 如果5秒后视频仍未加载，也显示容器
            setTimeout(() => {
                if (resultContainer.classList.contains('hidden')) {
                    resultContainer.classList.remove('hidden');
                    resultContainer.classList.add('fade-in');
                }
            }, 5000);

        } catch (error) {
            console.error("处理出错:", error);
            errorMessage.textContent = error.message;
            errorContainer.classList.remove('hidden');
            errorContainer.classList.add('fade-in');
        } finally {
            progressContainer.classList.add('hidden');
            submitButton.disabled = false;
        }
    });

    // 重置表单处理
    window.resetForm = () => {
        form.reset();
        errorContainer.classList.add('hidden');
        resultContainer.classList.add('hidden');
        progressContainer.classList.add('hidden');
        submitButton.disabled = false;
    };
}); 