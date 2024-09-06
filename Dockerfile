FROM python:3.10-alpine3.16

RUN apk add --no-cache \
    gcc \
    g++ \
    make \
    libjpeg-turbo-dev \
    zlib-dev \
    musl-dev \
    freetype-dev \
    openblas-dev

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 4000 7860

CMD uvicorn test_service3:app --host 0.0.0.0 --port 4000
