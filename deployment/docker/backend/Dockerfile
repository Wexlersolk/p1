FROM python:3.12-alpine

WORKDIR /app

RUN apk add --no-cache \
    gcc \
    g++ \
    cmake \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    make

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

CMD ["python", "run_server.py"]