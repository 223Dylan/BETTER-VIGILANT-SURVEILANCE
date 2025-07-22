# Use official Python image
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libqt5gui5 \
    libqt5core5a \
    libqt5dbus5 \
    libxcb-xinerama0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-sync1 \
    libxcb-xfixes0 \
    libxcb-xkb1 \
    qtbase5-dev \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV QT_QPA_PLATFORM=xcb
ENV QT_DEBUG_PLUGINS=0
ENV DISPLAY=:99
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose API port
EXPOSE 8000

# Start Xvfb and run the application
CMD Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 & python main.py
