#!/bin/sh

set -e

echo "==> Criando arquivo de log com permissões apropriadas..."
touch /app/app.log
chown www-data:www-data /app/app.log

echo "==> Aplicando migrações do Flask..."
flask db upgrade
echo "==> Migrações aplicadas com sucesso!"

echo "==> Iniciando a configuração do Solr (schema)..."
python setup_solr.py # Configura o schema do Solr
echo "==> Solr configurado com sucesso!"

echo "==> Inicializando e populando o Banco e Solr..."
python init_db.py # Popula o DB e indexa o Solr
echo "==> Banco e Solr inicializados com sucesso!"

exec "$@"