FROM python:3.11-slim

# Evitar cache e manter imagem enxuta
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Instalar dependências do sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório da app
WORKDIR /app

# Copiar arquivos para dentro da imagem
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expor porta
EXPOSE 5000

# Dar permissão de execução ao script de entrada
RUN chmod +x ./docker-entrypoint.sh

# Definir o script como o ponto de entrada
ENTRYPOINT ["./docker-entrypoint.sh"]

# Comando de inicialização
CMD ["uwsgi", "--ini", "uwsgi.ini"]