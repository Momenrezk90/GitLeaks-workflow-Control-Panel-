FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY api-server.py .
COPY gitleaks-control-panel.html .

# Expose ports
EXPOSE 5000 8000

# Create startup script
RUN echo '#!/bin/bash\n\
python3 api-server.py &\n\
python3 -m http.server 8000\n\
' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]
