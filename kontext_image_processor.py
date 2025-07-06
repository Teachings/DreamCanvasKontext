# File: kontext_image_processor.py

import requests
import websocket
import uuid
import json
import os
from urllib.parse import urlencode
from PIL import Image
import io

# --- Configuration ---
COMFYUI_SERVER_ADDRESS = "jarvis.mtcl.lan:8188"
INPUT_IMAGE_PATH = "/Users/mukul/Downloads/mukul.jpg"  # <--- CHANGE THIS TO YOUR INPUT IMAGE
POSITIVE_PROMPT = "Make this a perfect Ghibli Style photo, remove all watermarks, enhance details." # <--- YOUR PROMPT
WORKFLOW_API_JSON_FILE = "kontext_workflow_api.json"
OUTPUT_DIR = "outputs"

# --- Helper Functions ---

def upload_image_to_comfyui(server_address, image_path):
    """Uploads an image to the ComfyUI server's input directory."""
    print(f"Uploading {image_path} to ComfyUI server...")
    url = f"http://{server_address}/upload/image"
    
    with open(image_path, 'rb') as f:
        files = {'image': (os.path.basename(image_path), f, 'image/png')}
        response = requests.post(url, files=files, data={'overwrite': 'true'})

    if response.status_code == 200:
        print("Upload successful.")
        return response.json()
    else:
        print(f"Error uploading image: {response.text}")
        return None

def queue_prompt(server_address, client_id, prompt_workflow):
    """Queues a prompt on the ComfyUI server."""
    url = f"http://{server_address}/prompt"
    payload = {"prompt": prompt_workflow, "client_id": client_id}
    response = requests.post(url, json=payload)
    return response.json()

def get_image(server_address, filename, subfolder, folder_type):
    """Retrieves an image from the ComfyUI server."""
    url = f"http://{server_address}/view?{urlencode({'filename': filename, 'subfolder': subfolder, 'type': folder_type})}"
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        return response.content

def get_history(server_address, prompt_id):
    """Gets the history for a given prompt ID."""
    with requests.get(f"http://{server_address}/history/{prompt_id}") as response:
        response.raise_for_status()
        return response.json()

def wait_for_prompt_completion(server_address, client_id, prompt_id):
    """Waits for a prompt to finish executing using WebSockets."""
    ws_url = f"ws://{server_address}/ws?clientId={client_id}"
    ws = websocket.create_connection(ws_url)
    
    print(f"Waiting for prompt {prompt_id} to complete...")
    try:
        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                if message['type'] == 'executing':
                    data = message['data']
                    if data['node'] is None and data['prompt_id'] == prompt_id:
                        print("Execution complete.")
                        return
    finally:
        ws.close()

# --- Main Execution ---

if __name__ == "__main__":
    if not os.path.exists(INPUT_IMAGE_PATH):
        print(f"Error: Input image not found at '{INPUT_IMAGE_PATH}'")
    elif not os.path.exists(WORKFLOW_API_JSON_FILE):
        print(f"Error: Workflow file not found at '{WORKFLOW_API_JSON_FILE}'")
    else:
        # 1. Create client ID and output directory
        client_id = str(uuid.uuid4())
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # 2. Upload the input image to ComfyUI
        upload_info = upload_image_to_comfyui(COMFYUI_SERVER_ADDRESS, INPUT_IMAGE_PATH)
        
        if upload_info:
            # 3. Load and modify the workflow
            with open(WORKFLOW_API_JSON_FILE, "r") as f:
                workflow = json.load(f)

            # --- KEY MODIFICATIONS FOR IMAGE-TO-IMAGE ---
            # Find the LoadImage node and set its `image` input
            # In your workflow, this is node "142" which is of class_type "LoadImageOutput"
            # NOTE: Your provided workflow uses "LoadImageOutput", we will change this on the fly
            # to be a standard LoadImage which is more robust for programmatic use.
            # We'll assume the node to modify is "142".
            
            # Find the input image node
            image_loader_node_id = "142" # As per your JSON
            workflow[image_loader_node_id]["class_type"] = "LoadImage" # Change class type for robustness
            workflow[image_loader_node_id]["inputs"]["image"] = upload_info['name']
            
            # Find the prompt node and set the text
            prompt_node_id = "6" # As per your JSON
            workflow[prompt_node_id]["inputs"]["text"] = POSITIVE_PROMPT

            # Set a random seed
            sampler_node_id = "31" # As per your JSON
            seed = uuid.uuid4().int & (1<<32)-1
            workflow[sampler_node_id]["inputs"]["seed"] = seed
            
            print("Workflow modified with new image and prompt.")
            
            # 4. Queue the prompt
            queued_prompt = queue_prompt(COMFYUI_SERVER_ADDRESS, client_id, workflow)
            prompt_id = queued_prompt['prompt_id']
            print(f"Prompt queued with ID: {prompt_id}")
            
            # 5. Wait for completion
            wait_for_prompt_completion(COMFYUI_SERVER_ADDRESS, client_id, prompt_id)
            
            # 6. Get history and retrieve the output image
            history = get_history(COMFYUI_SERVER_ADDRESS, prompt_id)
            history_data = history[prompt_id]
            
            # Find the SaveImage node's output
            save_image_node_id = "136" # As per your JSON
            output_images_info = history_data['outputs'][save_image_node_id]['images']

            for image_info in output_images_info:
                image_data = get_image(COMFYUI_SERVER_ADDRESS, image_info['filename'], image_info['subfolder'], image_info['type'])
                
                # 7. Save the final image
                output_filename = os.path.join(OUTPUT_DIR, image_info['filename'])
                image = Image.open(io.BytesIO(image_data))
                image.save(output_filename)
                print(f"Successfully generated and saved image to {output_filename}")