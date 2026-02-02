# db/Dockerfile — pgvector with init scripts baked in so no mount permission issues (e.g. Coolify).
FROM pgvector/pgvector:pg16
COPY init/ /docker-entrypoint-initdb.d/
RUN chmod -R 755 /docker-entrypoint-initdb.d && chown -R 999:999 /docker-entrypoint-initdb.d
