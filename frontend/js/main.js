document.addEventListener('DOMContentLoaded', function () {
    // --- DOM Elements ---
    const form = document.getElementById('generation-form');
    const imageUpload = document.getElementById('image-upload');
    const imagePreview = document.getElementById('image-preview');
    const generateBtn = document.getElementById('generate-btn');
    const generateBtnText = document.getElementById('generate-btn-text');
    const outputImage = document.getElementById('output-image');
    const outputPlaceholder = document.getElementById('output-placeholder');
    const downloadBtn = document.getElementById('download-btn');
    const errorToastEl = document.getElementById('error-toast');
    const errorMessageEl = document.getElementById('error-message');
    const errorToast = new bootstrap.Toast(errorToastEl);

    // --- NEW: Timer and Overlay Elements ---
    const loadingOverlay = document.getElementById('loading-overlay');
    const timerDisplay = document.getElementById('timer-display');
    const generationTimeBadge = document.getElementById('generation-time-badge');

    // --- State Variables ---
    let timerInterval = null;
    let startTime = 0;

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

        // --- Start Loading and Timer ---
        setLoading(true);

        const selectedStyles = [];
        const styleCheckboxes = document.querySelectorAll('input[name="style-modifier"]:checked');
        styleCheckboxes.forEach(checkbox => {
            selectedStyles.push(checkbox.value);
        });
        
        const formData = new FormData();
        formData.append('prompt', promptText);
        formData.append('image', imageFile);
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
            // --- Stop Loading and Timer ---
            setLoading(false);
        }
    });

    function setLoading(isLoading) {
        if (isLoading) {
            // Start loading state
            generateBtn.disabled = true;
            generateBtnText.textContent = "Generating...";
            loadingOverlay.classList.remove('d-none');
            generationTimeBadge.classList.add('d-none'); // Hide previous time
            resetOutput(); // Clear previous image

            // Start timer
            startTime = Date.now();
            timerDisplay.textContent = '0s';
            timerInterval = setInterval(() => {
                const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
                timerDisplay.textContent = `${elapsedSeconds}s`;
            }, 1000);

        } else {
            // Stop loading state
            generateBtn.disabled = false;
            generateBtnText.textContent = "Generate Image";
            loadingOverlay.classList.add('d-none');

            // Stop and clear timer
            clearInterval(timerInterval);
            timerInterval = null;
            
            // Display final time
            if (startTime > 0) {
                const totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
                generationTimeBadge.textContent = `Done in ${totalTime}s`;
                generationTimeBadge.classList.remove('d-none');
                startTime = 0; // Reset start time
            }
        }
    }
    
    function resetOutput() {
        outputImage.src = "#";
        outputImage.classList.add('d-none');
        outputPlaceholder.classList.remove('d-none');
        downloadBtn.classList.add('d-none');
    }

    function showError(message) {
        errorMessageEl.textContent = message;
        errorToast.show();
    }
});