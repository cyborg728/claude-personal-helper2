FROM python:3.12-alpine AS builder

RUN apk add --no-cache gcc musl-dev libffi-dev
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-alpine

RUN apk add --no-cache ffmpeg
WORKDIR /app
COPY --from=builder /install /usr/local
COPY bot/ bot/

RUN mkdir -p /app/data

EXPOSE 8443
CMD ["python", "-m", "bot.app"]
