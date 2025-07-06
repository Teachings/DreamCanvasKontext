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

        // Prepare UI for loading state
        setLoading(true);

        // Create form data to send
        const formData = new FormData();
        formData.append('prompt', promptText);
        formData.append('image', imageFile);

        try {
            // Make API call
            const response = await fetch('/api/generate', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                // Try to get error message from backend
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
            }

            // Get the image data as a blob
            const imageBlob = await response.blob();
            const imageUrl = URL.createObjectURL(imageBlob);

            // Display the output image
            outputImage.src = imageUrl;
            outputImage.classList.remove('d-none');
            outputPlaceholder.classList.add('d-none');

            // Make download button work
            downloadBtn.href = imageUrl;
            downloadBtn.classList.remove('d-none');

        } catch (error) {
            console.error('Generation failed:', error);
            showError(error.message);
            resetOutput();
        } finally {
            // Revert UI from loading state
            setLoading(false);
        }
    });

    function setLoading(isLoading) {
        if (isLoading) {
            generateBtn.disabled = true;
            generateBtn.classList.add('loading');
            spinner.classList.remove('d-none');
        } else {
            generateBtn.disabled = false;
            generateBtn.classList.remove('loading');
            spinner.classList.add('d-none');
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