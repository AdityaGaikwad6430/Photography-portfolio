FROM python:3.11-slim

WORKDIR /app

# Install MySQL dependencies
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev gcc pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Run Flask app with Gunicorn (4 workers, port 8000)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "photo_portfolio_app:app"]
