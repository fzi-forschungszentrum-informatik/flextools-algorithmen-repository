FROM python:3.11.9-slim

COPY . .

RUN apt-get update && apt-get upgrade -y --no-install-recommends \
    gcc \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*
RUN pip install -r requirements.txt
EXPOSE 3000
CMD ["python", "./main.py"]
