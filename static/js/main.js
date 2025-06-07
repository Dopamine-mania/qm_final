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
        
        // Reset UI state
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
                throw new Error(data.error || 'An error occurred while generating the video');
            }

            // Update video source and show result
            resultVideo.src = data.video_path;
            resultContainer.classList.remove('hidden');
            resultContainer.classList.add('fade-in');
            
            // Scroll to result
            resultContainer.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            errorMessage.textContent = error.message;
            errorContainer.classList.remove('hidden');
            errorContainer.classList.add('fade-in');
        } finally {
            progressContainer.classList.add('hidden');
            submitButton.disabled = false;
        }
    });

    // Reset form handler
    window.resetForm = () => {
        form.reset();
        errorContainer.classList.add('hidden');
        resultContainer.classList.add('hidden');
        progressContainer.classList.add('hidden');
        submitButton.disabled = false;
    };
}); 