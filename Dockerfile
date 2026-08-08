FROM python:3.12-slim

WORKDIR /app

# Instala as dependências primeiro (aproveita cache de camada do Docker:
# só reinstala se o requirements.txt mudar, não a cada alteração de código)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do projeto
COPY . .

RUN chmod +x start.sh

ENV PYTHONUNBUFFERED=1

# Railway injeta $PORT em tempo de execução — o próprio start.sh já lê essa variável
CMD ["bash", "start.sh"]
