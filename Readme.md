# Kontext Image Generator

A beautiful, modern, and responsive web interface for a powerful ComfyUI image-to-image workflow. This application allows users to upload an image, apply creative style modifiers, and generate a new version of their image using the magic of generative AI.

The entire application is packaged in a Docker container for simple, one-command setup and deployment.

## ✨ Features

*   **Modern & Responsive UI:** Built with Bootstrap 5, the interface is elegant and works flawlessly on both desktop and mobile devices.
*   **Easy Image Upload:** Select an image from your device and see an instant preview.
*   **Creative Style Modifiers:** Apply fun, one-tap styles like **Ghibli, Anime, Minecraft, Cartoonify, Cinematic,** and more.
*   **Custom Prompts:** Combine style modifiers with your own text prompts to fine-tune the output.
*   **Real-time Feedback:** A live timer shows the generation progress, so you're never left guessing.
*   **Easy Deployment:** Dockerized with `docker-compose` for a simple and reproducible setup.
*   **Robust Backend:** Powered by FastAPI, providing a fast and reliable API.

## 🛠️ Tech Stack

*   **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5
*   **Backend:** Python 3.10, FastAPI
*   **AI Integration:** Communicates with a running [ComfyUI](https://github.com/comfyanonymous/ComfyUI) instance via its API.
*   **Containerization:** Docker & Docker Compose

## 🚀 Getting Started

Follow these steps to get the Kontext Image Generator running on your local machine.

### Prerequisites

1.  **Docker & Docker Compose:** You must have Docker and Docker Compose installed.
    *   [Install Docker Engine](https://docs.docker.com/engine/install/)
    *   [Install Docker Compose](https://docs.docker.com/compose/install/)

2.  **A Running ComfyUI Instance:** This application requires a separate, running ComfyUI server. The server must be accessible from the machine where you run the Docker container.
    *   Ensure your ComfyUI is updated and has the necessary custom nodes and models required by `kontext_workflow_api.json`.

### Installation & Setup

1.  **Clone the Repository**

    ```bash
    git clone https://github.com/Teachings/DreamCanvasKontext.git
    cd DreamCanvasKontext
    ```

2.  **Configure the ComfyUI Address**

    Open the `docker-compose.yml` file in your favorite text editor. You need to tell the application how to connect to your ComfyUI server.

    Find this section:
    ```yaml
    environment:
      # IMPORTANT: Change this to your ComfyUI server's network address
      - COMFYUI_SERVER_ADDRESS=192.168.1.100:8188
    ```
    
    Replace `192.168.1.100:8188` with the actual network IP address and port of your ComfyUI server.
    
    > **Important:** Do **not** use `localhost` or `127.0.0.1` unless your ComfyUI server is also running inside the same Docker network. Use the IP address of the machine running ComfyUI on your local network (e.g., `192.168.1.100:8188`, `jarvis.mtcl.lan:8188`).

3.  **Build and Run the Docker Container**

    From the root directory of the project, run the following command:

    ```bash
    docker-compose up --build
    ```

    *   `--build` tells Docker Compose to build the image from the `Dockerfile` for the first time or when you've made code changes.
    *   `up` starts the services defined in the `docker-compose.yml` file.

    Docker will now download the base images, install dependencies, and start the application server.

4.  **Access the Application**

    Once the container is running, open your web browser and navigate to:

    **http://localhost:8000**

    You should see the Kontext Image Generator interface, ready for you to use!

## Usage

1.  **Upload an Image:** Click the "Input Image" button and select an image file from your device. A preview will appear.
2.  **Select Styles (Optional):** Tap on any of the style modifier tags (e.g., "Ghibli", "Pixel Art"). You can select multiple.
3.  **Add a Prompt:** In the "Describe Your Changes" text area, add any specific instructions (e.g., "add a futuristic helmet", "change background to a neon city").
4.  **Generate:** Click the "Generate Image" button.
5.  **View & Download:** Watch the timer on the output panel. Once complete, your new image will appear. Click the "Download Image" button to save it.

## 📁 Project Structure

```
kontext-ui/
├── backend/
│   ├── main.py                     # FastAPI application
│   ├── comfy_processor.py          # Logic for interacting with ComfyUI
│   ├── kontext_workflow_api.json   # The ComfyUI workflow definition
│   └── requirements.txt            # Python dependencies
│
├── frontend/
│   ├── index.html                  # Main UI page
│   ├── css/
│   │   └── style.css               # Custom styles
│   └── js/
│       └── main.js                 # Frontend JavaScript logic
│
├── Dockerfile                      # Instructions to build the Docker image
├── docker-compose.yml              # Easy way to run the container
└── README.md                       # This file
```

## Troubleshooting

*   **`ModuleNotFoundError`:** Ensure you have applied the code fixes related to Python's import system (`from backend import ...`). If you pull new changes, always re-run `docker-compose up --build`.
*   **Connection Errors / 503 Service Unavailable:** This almost always means the application cannot reach your ComfyUI server. Double-check the `COMFYUI_SERVER_ADDRESS` in `docker-compose.yml`. Make sure there are no firewalls blocking the connection.
*   **Image Generation Fails:** This could be due to an issue on the ComfyUI server side. Check the ComfyUI console for errors related to missing models, custom nodes, or workflow issues.
