FROM python:3.11-slim

# Install SQL Server dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl cron bash \
 && curl -sSL -O https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
 && dpkg -i packages-microsoft-prod.deb \
 && rm packages-microsoft-prod.deb \
 && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
 && rm -rf /var/lib/apt/lists/*


WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENV STREAMLIT_PORT=8484 \
    STREAMLIT_ADDRESS=0.0.0.0 \
    JOB_SCRIPT=/app/etl/production-stock-etl.py \
    TZ=Etc/Warsaw

EXPOSE 8484

HEALTHCHECK --interval=30s --timeout=5s --retries=5 \
  CMD curl --fail http://localhost:8484/_stcore/health || exit 1

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]