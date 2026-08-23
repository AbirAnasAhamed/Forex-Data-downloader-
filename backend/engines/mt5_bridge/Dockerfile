# Use Ubuntu as the base image
FROM ubuntu:22.04

# Avoid timezone prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Add architecture for Wine (32-bit is often needed for some windows dependencies, though MT5 has 64-bit)
RUN dpkg --add-architecture i386

# Install necessary packages for Xvfb, Wine, and downloading tools
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    software-properties-common \
    xvfb \
    winbind \
    cabextract \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Wine HQ repository and Wine
RUN wget -nc https://dl.winehq.org/wine-builds/winehq.key \
    && apt-key add winehq.key \
    && add-apt-repository 'deb https://dl.winehq.org/wine-builds/ubuntu/ jammy main' \
    && apt-get update \
    && apt-get install -y --install-recommends winehq-stable \
    && rm -rf /var/lib/apt/lists/*

# Set up Wine environment
ENV WINEPREFIX=/root/.wine
ENV WINEARCH=win64
RUN winecfg && sleep 5

# ---------------------------------------------------------
# RELIABLE PYTHON INSTALLATION FOR WINE (Embeddable Zip)
# ---------------------------------------------------------
# Download and extract Windows Python Embeddable (bypasses UI installer crashes)
RUN mkdir -p /root/.wine/drive_c/Python39 && \
    wget https://www.python.org/ftp/python/3.9.13/python-3.9.13-embed-amd64.zip -O /tmp/python.zip && \
    unzip /tmp/python.zip -d /root/.wine/drive_c/Python39 && \
    rm /tmp/python.zip

# Enable 'site' packages by uncommenting 'import site' in python39._pth
RUN sed -i 's/#import site/import site/' /root/.wine/drive_c/Python39/python39._pth

# Install pip inside Wine
RUN wget https://bootstrap.pypa.io/pip/3.9/get-pip.py -O /tmp/get-pip.py && \
    xvfb-run -a wine C:/Python39/python.exe /tmp/get-pip.py && \
    rm /tmp/get-pip.py

# Install Python dependencies (MetaTrader5, pyzmq, pandas) using Windows pip
RUN xvfb-run -a wine C:/Python39/python.exe -m pip install --no-cache-dir MetaTrader5 pyzmq pandas

# ---------------------------------------------------------

# Copy the MetaTrader 5 setup file
RUN wget https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe -O /tmp/mt5setup.exe

# Copy our dynamic bridge scripts
WORKDIR /app
COPY dynamic_publisher.py .
COPY historical_worker.py .

# Set display for Xvfb
ENV DISPLAY=:99

# The entrypoint starts Xvfb and then our Python scripts via Wine
CMD Xvfb :99 -screen 0 1024x768x16 & \
    echo "Starting MT5 Historical Worker..." && \
    wine C:/Python39/python.exe historical_worker.py & \
    echo "Starting MT5 Bridge Engine..." && \
    wine C:/Python39/python.exe dynamic_publisher.py
