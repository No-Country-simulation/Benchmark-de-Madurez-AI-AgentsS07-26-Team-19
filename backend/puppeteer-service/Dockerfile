# Imagen oficial de Puppeteer — incluye Node + Chrome, sin apt-get de chromium
FROM ghcr.io/puppeteer/puppeteer:24.2.0

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install --omit=dev

COPY server.js .

ENV PORT=3001
EXPOSE 3001

CMD ["node", "server.js"]
