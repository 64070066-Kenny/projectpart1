FROM python:3.8-slim

# Install dependencies required for building some Python packages
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    gfortran \
    libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python", "app.py"]
