FROM node:20-alpine

WORKDIR /app

# Instalacja zależności
COPY package*.json ./
RUN npm install

# Kopiowanie reszty plików
COPY . .

# Vite deweloperski używa portu 5173
EXPOSE 5173

# Kluczowe: --host pozwala na dostęp do Vite spoza kontenera (z Windowsa)
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]