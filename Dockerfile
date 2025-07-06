# --- Build Stage ---
# Use a Python base image
FROM python:3.10-slim AS builder

# Set the working directory
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Final Stage ---
# Use the same Python base image for the final image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the backend and frontend code into the container
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Expose the port the app runs on
EXPOSE 8000

# Set the command to run the application using uvicorn
# We run it from the /app directory
# host 0.0.0.0 makes it accessible from outside the container
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]