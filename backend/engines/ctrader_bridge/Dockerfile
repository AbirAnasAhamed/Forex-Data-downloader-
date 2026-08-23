FROM python:3.10-slim

WORKDIR /app

# Install dependencies
RUN pip install pyzmq

# Copy script
COPY ctrader_streamer.py .

# Run script
CMD ["python", "ctrader_streamer.py"]
