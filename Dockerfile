# Cloud Run image. The repo's Markdown files (voice, playbooks) ship with the code,
# so updating them in GitHub and redeploying updates the bot's writing.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN pip install --no-cache-dir --no-deps .
ENV REPO_ROOT=/app STORAGE=firestore PORT=8080
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 120 "founder_engine.app:create_wsgi()"
