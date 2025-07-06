document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('generation-form');
    const imageUpload = document.getElementById('image-upload');
    const imagePreview = document.getElementById('image-preview');
    const generateBtn = document.getElementById('generate-btn');
    const spinner = document.getElementById('spinner');
    const outputImage = document.getElementById('output-image');
    const outputPlaceholder = document.getElementById('output-placeholder');
    const downloadBtn = document.getElementById('download-btn');
    const errorToastEl = document.getElementById('error-toast');
    const errorMessageEl = document.getElementById('error-message');
    const errorToast = new bootstrap.Toast(errorToastEl);

    // Show image preview when a file is selected
    imageUpload.addEventListener('change', () => {
        const file = imageUpload.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                imagePreview.src = e.target.result;
                imagePreview.classList.remove('d-none');
            };
            reader.readAsDataURL(file);
        }
    });

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const promptText = document.getElementById('prompt-text').value;
        const imageFile = imageUpload.files[0];

        if (!imageFile) {
            showError("Please select an image file.");
            return;
        }

        setLoading(true);

        // --- Collect selected styles ---
        const selectedStyles = [];
        const styleCheckboxes = document.querySelectorAll('input[name="style-modifier"]:checked');
        styleCheckboxes.forEach(checkbox => {
            selectedStyles.push(checkbox.value);
        });
        
        // --- Create form data to send ---
        const formData = new FormData();
        formData.append('prompt', promptText);
        formData.append('image', imageFile);
        
        // Append each style to the form data
        selectedStyles.forEach(style => {
            formData.append('styles', style);
        });

        try {
            const response = await fetch('/api/generate', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
            }

            const imageBlob = await response.blob();
            const imageUrl = URL.createObjectURL(imageBlob);

            outputImage.src = imageUrl;
            outputImage.classList.remove('d-none');
            outputPlaceholder.classList.add('d-none');

            downloadBtn.href = imageUrl;
            downloadBtn.classList.remove('d-none');

        } catch (error) {
            console.error('Generation failed:', error);
            showError(error.message);
            resetOutput();
        } finally {
            setLoading(false);
        }
    });

    function setLoading(isLoading) {
        if (isLoading) {
            generateBtn.disabled = true;
            generateBtn.classList.add('loading');
        } else {
            generateBtn.disabled = false;
            generateBtn.classList.remove('loading');
        }
    }
    
    function resetOutput() {
        outputImage.classList.add('d-none');
        outputPlaceholder.classList.remove('d-none');
        downloadBtn.classList.add('d-none');
    }

    function showError(message) {
        errorMessageEl.textContent = message;
        errorToast.show();
    }
});