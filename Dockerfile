FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
COPY bot/ bot/
RUN pip install --no-cache-dir .
RUN mkdir -p /app/data

EXPOSE 8443
CMD ["python", "-m", "bot.app"]
