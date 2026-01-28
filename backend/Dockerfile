FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install requests schedule sqlalchemy psycopg2-binary

COPY . .

# Install postgresql-client for psql command in start.sh
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Grant execution permissions
RUN chmod +x start.sh

CMD ["./start.sh"]
