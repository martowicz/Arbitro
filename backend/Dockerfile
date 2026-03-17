FROM python:3.12-slim

WORKDIR /app

# Instalacja podstawowych narzędzi systemowych
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Instalacja zależności Pythona
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --verbose

# INSTALACJA PLAYWRIGHTA I JEGO ZALEŻNOŚCI SYSTEMOWYCH
# Ta komenda sama doinstaluje wszystkie libnss3, libatk itd.
RUN playwright install chromium
RUN playwright install-deps chromium

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]