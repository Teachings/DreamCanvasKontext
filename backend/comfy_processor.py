import requests
import websocket
import uuid
import json
import os
from urllib.parse import urlencode
from PIL import Image
import io
import time

# --- Configuration ---
# We will get this from an environment variable in main.py
COMFYUI_SERVER_ADDRESS = os.getenv("COMFYUI_SERVER_ADDRESS", "127.0.0.1:8188")
WORKFLOW_API_JSON_FILE = "backend/kontext_workflow_api.json"

# --- Helper Functions ---

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
            # Set a timeout for receiving data to avoid infinite loops
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


# --- Main Orchestration Function ---

def generate_image(prompt_text: str, input_image_bytes: bytes, input_filename: str):
    """The main function to process an image and return the output image bytes."""
    
    if not os.path.exists(WORKFLOW_API_JSON_FILE):
        raise FileNotFoundError(f"Workflow file not found at '{WORKFLOW_API_JSON_FILE}'")

    client_id = str(uuid.uuid4())

    # 1. Upload the input image to ComfyUI
    upload_info = upload_image_to_comfyui(input_image_bytes, input_filename)
    if not upload_info:
        raise Exception("Failed to upload image to ComfyUI.")

    # 2. Load and modify the workflow
    with open(WORKFLOW_API_JSON_FILE, "r") as f:
        workflow = json.load(f)

    # --- Modify workflow nodes ---
    image_loader_node_id = "142"
    workflow[image_loader_node_id]["inputs"]["image"] = upload_info['name']

    prompt_node_id = "6"
    workflow[prompt_node_id]["inputs"]["text"] = prompt_text

    sampler_node_id = "31"
    workflow[sampler_node_id]["inputs"]["seed"] = uuid.uuid4().int & (1<<32)-1
    
    print("Workflow modified with new image and prompt.")
    
    # 3. Queue the prompt
    queued_prompt = queue_prompt(client_id, workflow)
    if not queued_prompt:
        raise Exception("Failed to queue prompt.")
    prompt_id = queued_prompt['prompt_id']
    print(f"Prompt queued with ID: {prompt_id}")
    
    # 4. Wait for completion
    if not wait_for_prompt_completion(client_id, prompt_id):
         raise Exception("Image generation timed out or failed.")
    
    # 5. Get history and retrieve the output image
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

    # We'll take the first image
    image_info = output_images_info[0]
    image_data = get_image(image_info['filename'], image_info['subfolder'], image_info['type'])

    if not image_data:
        raise Exception("Failed to download the final image.")

    print(f"Successfully generated image: {image_info['filename']}")
    return image_data