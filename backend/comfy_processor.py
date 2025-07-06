import requests
import websocket
import uuid
import json
import os
from urllib.parse import urlencode
from PIL import Image
import io
import time
from pathlib import Path

# --- Configuration ---
COMFYUI_SERVER_ADDRESS = os.getenv("COMFYUI_SERVER_ADDRESS", "127.0.0.1:8188")
# Make the path robust by referencing this file's location
WORKFLOW_API_JSON_FILE = Path(__file__).parent / "kontext_workflow_api.json"

# --- Style Presets ---
# This dictionary maps the style keys from the frontend to prompt prefixes.
STYLE_PRESETS = {
    "ghibli": "A beautiful masterpiece in the style of Studio Ghibli, anime film, cel shading, high quality, detailed",
    "minecraft": "A detailed scene in the blocky, pixelated art style of Minecraft, sandbox game aesthetic",
    "family_guy": "In the distinct, bold-lined, satirical cartoon art style of Family Guy",
    "anime": "Vibrant modern anime style, high-contrast, cinematic lighting, detailed character design",
    "simpsons": "In the iconic cartoon style of The Simpsons, yellow characters, overbite, simple backgrounds",
    "colorify": "Colorize this black and white image, add realistic and vibrant colors, natural lighting",
    "cartoonify": "Convert this into a charming cartoon, with bold outlines, simplified shapes, and vibrant flat colors",
    "sticker": "A die-cut vinyl sticker with a thick white border, glossy, isolated on a white background, high detail",
    "pixel_art": "8-bit pixel art, retro video game style, limited color palette, nostalgic",
    "claymation": "A charming stop-motion claymation scene, textured, handcrafted look, like Aardman Animations",
    "cinematic": "A cinematic film still, dramatic lighting, anamorphic lens flare, 4K, high detail, epic mood",
    "3d_render": "A hyper-realistic 3D render, trending on ArtStation, octane render, detailed textures, Unreal Engine 5"
}

# --- Helper Functions (Unchanged) ---

def upload_image_to_comfyui(image_bytes: bytes, filename: str):
    """Uploads an image from bytes to the ComfyUI server."""
    print(f"Uploading {filename} to ComfyUI server...")
    url = f"http://{COMFYUI_SERVER_ADDRESS}/upload/image"
    files = {'image': (filename, image_bytes, 'image/png')}
    data = {'overwrite': 'true'}
    try:
        response = requests.post(url, files=files, data=data, timeout=30)
        response.raise_for_status()
        print("Upload successful.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error uploading image: {e}")
        return None

def queue_prompt(client_id, prompt_workflow):
    """Queues a prompt on the ComfyUI server."""
    url = f"http://{COMFYUI_SERVER_ADDRESS}/prompt"
    payload = {"prompt": prompt_workflow, "client_id": client_id}
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error queueing prompt: {e}")
        return None

def get_image(filename, subfolder, folder_type):
    """Retrieves an image from the ComfyUI server."""
    url = f"http://{COMFYUI_SERVER_ADDRESS}/view?{urlencode({'filename': filename, 'subfolder': subfolder, 'type': folder_type})}"
    try:
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error getting image: {e}")
        return None

def get_history(prompt_id):
    """Gets the history for a given prompt ID."""
    try:
        with requests.get(f"http://{COMFYUI_SERVER_ADDRESS}/history/{prompt_id}", timeout=30) as response:
            response.raise_for_status()
            return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error getting history: {e}")
        return None

def wait_for_prompt_completion(client_id, prompt_id):
    """Waits for a prompt to finish executing using WebSockets."""
    ws_url = f"ws://{COMFYUI_SERVER_ADDRESS}/ws?clientId={client_id}"
    print(f"Waiting for prompt {prompt_id} to complete...")
    try:
        ws = websocket.create_connection(ws_url, timeout=30)
        start_time = time.time()
        while True:
            if time.time() - start_time > 300: # 5 minute timeout
                print("Error: WebSocket wait timed out.")
                ws.close()
                return False
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data.get('node') is None and data.get('prompt_id') == prompt_id:
                        print("Execution complete.")
                        ws.close()
                        return True
    except (websocket.WebSocketException, ConnectionRefusedError, TimeoutError) as e:
        print(f"WebSocket connection error: {e}")
        return False

# --- Main Orchestration Function (Updated) ---

def generate_image(prompt_text: str, input_image_bytes: bytes, input_filename: str, styles: list[str] = None):
    """The main function to process an image and return the output image bytes."""
    
    if not os.path.exists(WORKFLOW_API_JSON_FILE):
        raise FileNotFoundError(f"Workflow file not found at '{WORKFLOW_API_JSON_FILE}'")

    client_id = str(uuid.uuid4())

    # 1. Upload the input image to ComfyUI
    upload_info = upload_image_to_comfyui(input_image_bytes, input_filename)
    if not upload_info:
        raise Exception("Failed to upload image to ComfyUI.")

    # 2. Load the workflow
    with open(WORKFLOW_API_JSON_FILE, "r") as f:
        workflow = json.load(f)

    # 3. Build the final prompt
    final_prompt_parts = []
    if styles:
        for style_key in styles:
            if style_key in STYLE_PRESETS:
                final_prompt_parts.append(STYLE_PRESETS[style_key])
    
    # Add the user's custom prompt
    if prompt_text:
        final_prompt_parts.append(prompt_text)

    # Join everything into a single string
    final_prompt = ", ".join(final_prompt_parts)
    print(f"Final constructed prompt: {final_prompt}")
    
    # 4. Modify workflow nodes
    image_loader_node_id = "142"
    workflow[image_loader_node_id]["inputs"]["image"] = upload_info['name']

    prompt_node_id = "6"
    workflow[prompt_node_id]["inputs"]["text"] = final_prompt

    sampler_node_id = "31"
    workflow[sampler_node_id]["inputs"]["seed"] = uuid.uuid4().int & (1<<32)-1
    
    print("Workflow modified with new image and prompt.")
    
    # 5. Queue the prompt
    queued_prompt = queue_prompt(client_id, workflow)
    if not queued_prompt:
        raise Exception("Failed to queue prompt.")
    prompt_id = queued_prompt['prompt_id']
    print(f"Prompt queued with ID: {prompt_id}")
    
    # 6. Wait for completion
    if not wait_for_prompt_completion(client_id, prompt_id):
         raise Exception("Image generation timed out or failed.")
    
    # 7. Get history and retrieve the output image
    history = get_history(prompt_id)
    if not history or prompt_id not in history:
        raise Exception("Failed to retrieve generation history.")
        
    history_data = history[prompt_id]
    
    save_image_node_id = "136"
    if save_image_node_id not in history_data['outputs']:
         raise Exception("Could not find SaveImage node in the output history.")

    output_images_info = history_data['outputs'][save_image_node_id]['images']

    if not output_images_info:
        raise Exception("No images found in the output.")

    image_info = output_images_info[0]
    image_data = get_image(image_info['filename'], image_info['subfolder'], image_info['type'])

    if not image_data:
        raise Exception("Failed to download the final image.")

    print(f"Successfully generated image: {image_info['filename']}")
    return image_data