FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt

COPY pyproject.toml README.md ./
COPY astrace ./astrace
RUN pip install .

ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=8788
ENV SEARCH_MAX_RESULTS=8
ENV REQUEST_TIMEOUT=15
ENV MAX_TEXT_CHARS=12000
ENV ASTRACE_TASK_WORKERS=2

EXPOSE 8788

CMD ["python", "-m", "astrace.server"]
