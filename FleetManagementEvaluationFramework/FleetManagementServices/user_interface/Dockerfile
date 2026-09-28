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
EXPOSE 3010
CMD ["python","-m","streamlit", "run", "app.py", "--server.port=3010", "--server.address=0.0.0.0"]