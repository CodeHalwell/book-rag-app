FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    curl

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
    
COPY . .

RUN uv sync

EXPOSE 5000

CMD ["uv", "run", "flask", "--app", "app", "run", "--host", "0.0.0.0", "--port", "5000"]
