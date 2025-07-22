# 1. Base image
FROM python:3.10-slim

# 2. Working directory
WORKDIR /app

# 3. Install dependencies via requirements.txt
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy application code
COPY . /app

# 5. Expose port
EXPOSE 8000

# 6. Start server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8009"]
