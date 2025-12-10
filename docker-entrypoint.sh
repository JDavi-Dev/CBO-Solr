#!/bin/sh

set -e

# --- 1. Rodar Migrações do Banco de Dados (Já Existente) ---
echo "==> Aplicando migrações do Flask..."
echo "==> Executando flask db upgrade"
flask db upgrade
echo "==> Migrações aplicadas com sucesso!"

# --- 2. Configurar e Popular o Solr e o Banco de Dados ---
# NOTA: O Flask.Dockerfile já copiou os arquivos setup_solr.py e init_db.py para /app

echo "==> Iniciando a configuração do Solr (schema)..."
python setup_solr.py # Configura o schema do Solr
echo "==> Solr configurado com sucesso!"

echo "==> Inicializando e populando o Banco e Solr..."
python init_db.py # Popula o DB e indexa o Solr
echo "==> Banco e Solr inicializados com sucesso!"

# --- 3. Iniciar a Aplicação (Já Existente) ---
# Executa o comando principal do contêiner (o CMD que é o uwsgi)
exec "$@"