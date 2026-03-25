FROM oven/bun:1-alpine AS build

ARG APP_ENV=production
WORKDIR /app

COPY rocky-interface/package*.json ./rocky-interface/
WORKDIR /app/rocky-interface
RUN bun install

WORKDIR /app
COPY rocky-interface ./rocky-interface
WORKDIR /app/rocky-interface

# Strip dev-only/public-test assets from production builds.
RUN if [ "$APP_ENV" = "production" ]; then \
  rm -rf src/routes/DBtest static/local-api local-api; \
fi

RUN bun run build

FROM oven/bun:1-alpine AS runtime
WORKDIR /app/rocky-interface

COPY --from=build /app/rocky-interface ./

ENV HOST=0.0.0.0
ENV PORT=4173

EXPOSE 4173
CMD ["bun", "run", "preview", "--", "--host", "0.0.0.0", "--port", "4173"]
