FROM node:22-bookworm-slim

WORKDIR /app

# Install Python, pip, FFmpeg and Git
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .

RUN python3 -m pip install --break-system-packages \
    --no-cache-dir -r requirements.txt

# Download and build bgutil PO Token server
RUN git clone --depth 1 --branch 2.0.0 \
    https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git \
    /opt/bgutil

RUN cd /opt/bgutil/server && \
    npm ci && \
    npx tsc

# Copy FastAPI application
COPY app.py .

# Render provides PORT automatically
EXPOSE 10000

# Start PO Token server and FastAPI
CMD ["sh", "-c", "node /opt/bgutil/server/build/main.js & exec uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000}"]