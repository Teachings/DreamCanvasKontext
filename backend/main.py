from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend import comfy_processor
import io
import os

app = FastAPI(
    title="Kontext Image Generator API",
    description="A modern UI and API for a ComfyUI image generation workflow.",
    version="1.0.0"
)

# --- CORS Middleware ---
# This allows our frontend (even if served from a different origin) to talk to the backend.
# In a production Docker setup where both are served from the same origin, this is less critical
# but good practice for development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

# --- API Endpoint ---
@app.post("/api/generate")
async def generate(
    prompt: str = Form(...),
    image: UploadFile = File(...)
):
    """
    Receives a prompt and an image, processes them using ComfyUI,
    and streams the resulting image back.
    """
    print(f"Received request with prompt: '{prompt}' and image: '{image.filename}'")

    # Ensure the uploaded file is an image
    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File provided is not an image."
        )

    # Read image bytes
    image_bytes = await image.read()

    try:
        # Call the processing logic
        output_image_bytes = comfy_processor.generate_image(
            prompt_text=prompt,
            input_image_bytes=image_bytes,
            input_filename=image.filename
        )
        # Stream the image back as the response
        return StreamingResponse(io.BytesIO(output_image_bytes), media_type="image/png")
    
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"An error occurred during image generation: {e}")


# --- Static Files Mount ---
# This serves the 'frontend' directory at the root URL.
# The `Directory` check prevents errors if the folder doesn't exist during certain build steps.
if os.path.isdir('frontend'):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="static")