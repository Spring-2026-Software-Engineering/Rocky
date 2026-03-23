FROM oven/bun:latest

WORKDIR /app

COPY rocky-interface/ ./


RUN bun install
COPY . ./


WORKDIR /app/rocky-frontend

RUN bun run build




EXPOSE 4173

CMD ["bun", "preview"]