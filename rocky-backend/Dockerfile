FROM ghcr.io/astral-sh/uv:alpine

WORKDIR /app

# Copy requirements first for better caching
COPY rocky-backend/requirements.txt ./
RUN uv init
RUN uv venv
RUN uv pip install -r requirements.txt

# Copy application code
COPY . ./

WORKDIR /app/rocky-backend

# Run the service
CMD ["uv", "run", "flask" ""]
