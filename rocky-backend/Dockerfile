FROM python:3.12-alpine

WORKDIR /app/rocky-backend

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install only runtime dependencies.
COPY rocky-backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy only backend runtime files required in production.
COPY rocky-backend/main.py ./main.py
COPY rocky-backend/templates ./templates

# Keep local-api payload files needed by backend pass-through endpoints.
COPY rocky-interface/static/local-api/analytics /app/rocky-interface/static/local-api/analytics
COPY rocky-interface/static/local-api/widgets /app/rocky-interface/static/local-api/widgets

EXPOSE 5001

# Mongita starts empty by default in the container; no seed step is run.
CMD ["flask", "--app", "main", "run", "--host", "0.0.0.0", "--port", "5001"]
