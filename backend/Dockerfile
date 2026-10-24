FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_LINK_MODE=copy
RUN apt-get update && apt-get install -y --no-install-recommends libgdal32 libgeos-c1v5 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv==0.12.22
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend ./backend
COPY contracts ./contracts
RUN useradd --uid 10001 --create-home rescue && chown -R rescue:rescue /app
USER rescue
EXPOSE 8000
CMD ["uv", "run", "--no-sync", "gunicorn", "--chdir", "backend", "rescue.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "1", "--timeout", "30", "--access-logfile", "-"]
