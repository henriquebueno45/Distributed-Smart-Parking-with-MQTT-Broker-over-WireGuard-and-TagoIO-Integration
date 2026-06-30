FROM python:3.11-slim
WORKDIR /app
COPY main.py .
RUN pip install paho-mqtt
CMD ["python", "main.py"]
