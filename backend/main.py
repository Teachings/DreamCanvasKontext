from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from backend import comfy_processor
import io
import os
from typing import List

app = FastAPI(
    title="Kontext Image Generator API",
    description="A modern UI and API for a ComfyUI image generation workflow.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoint (Updated) ---
@app.post("/api/generate")
async def generate(
    prompt: str = Form(...),
    image: UploadFile = File(...),
    styles: List[str] = Form([]) # <-- Accept a list of styles, defaults to empty list
):
    """
    Receives a prompt, styles, and an image, processes them using ComfyUI,
    and streams the resulting image back.
    """
    print(f"Received request with prompt: '{prompt}', styles: {styles}, and image: '{image.filename}'")

    if not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File provided is not an image."
        )

    image_bytes = await image.read()

    try:
        output_image_bytes = comfy_processor.generate_image(
            prompt_text=prompt,
            input_image_bytes=image_bytes,
            input_filename=image.filename,
            styles=styles # Pass the styles to the processor
        )
        return StreamingResponse(io.BytesIO(output_image_bytes), media_type="image/png")
    
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"An error occurred during image generation: {e}")

# --- Static Files Mount ---
if os.path.isdir('frontend'):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="static")