FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ bot/
RUN mkdir -p /app/data

EXPOSE 8443
CMD ["python", "-m", "bot.app"]
