FROM mcr.microsoft.com/playwright/python:v1.52.0-jammy

WORKDIR /app

# Install OS dependencies for MySQL client (Playwright dependencies are pre-installed)
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["bash", "entrypoint.sh"]
CMD ["python", "main.py"]
