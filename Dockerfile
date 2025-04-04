# Dockerfile (place this in the ROOT of your project)

# 1. Base Image: Start with an official Python image
FROM python:3.11-slim

# 2. Set Working Directory: Create a directory inside the container for the app
WORKDIR /app

# 3. Set Environment Variables: For better Python logging in Docker
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


# 4. Install Dependencies:
#    - Copy *only* the requirements file first to leverage Docker cache
#    - Install the dependencies
COPY backend/requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy Application Code: Copy the entire backend directory content
#    The first '.' refers to the backend dir on your host (relative to COPY instruction)
#    The second '.' refers to the WORKDIR (/app) inside the container
COPY backend/ .

# 6. Expose Port: Tell Docker the container listens on port 8000
EXPOSE 8000

# 7. Run Command: The command to start the FastAPI app using uvicorn
#    Use 0.0.0.0 to make it accessible outside the container within Fly.io's network
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]