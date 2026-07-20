FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY mcp_server/requirements.txt /app/mcp_server/requirements.txt
RUN pip install --no-cache-dir -r /app/mcp_server/requirements.txt

COPY mcp_server /app/mcp_server
COPY scripts /app/scripts
COPY datasets /app/datasets
COPY outputs /app/outputs

WORKDIR /app

CMD ["python", "mcp_server/server.py"]
