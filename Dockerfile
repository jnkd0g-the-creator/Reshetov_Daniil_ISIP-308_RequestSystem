FROM python:3.10-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN groupadd --gid 10001 coffee && useradd --uid 10001 --gid coffee --no-create-home coffee \
    && install -d -o coffee -g coffee /app/data
COPY src ./src
COPY docs/database/schema.sql docs/database/seed.sql ./docs/database/
ENV COFFEE_DB_PATH=/app/data/coffeedesk.db PORT=8000 COFFEE_MODE=development
EXPOSE 8000
USER 10001:10001
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import json,os,urllib.request; r=urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','8000')+'/health',timeout=3); assert json.load(r)['database']=='ok'"
CMD ["python", "-m", "coffeedesk", "serve"]
