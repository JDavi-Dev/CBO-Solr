# CBO-Solr (API Flask + Postgres + Solr)

Projeto Flask que popula um banco Postgres a partir do CSV `data/cbo2002-ocupacao.csv`, indexa documentos no Solr e expõe uma API REST para consulta/CRUD das CBOs.

Visão geral rápida
- API REST construída com Flask + Flask-RESTful: [`helpers.application.app`](helpers/application/__init__.py) e [`helpers.application.api`](helpers/application/__init__.py).
- Modelo principal: [`models.CBO.CBO`](models/CBO.py) com serialização em [`models.CBO.cbo_fields`](models/CBO.py).
- Recursos REST: [`resources.CBOResouce.CbosResouce`](resources/CBOResouce.py) e [`resources.CBOResouce.CboResouce`](resources/CBOResouce.py).
- Inicialização/Indexação: scripts [`setup_solr.py`](setup_solr.py) (configura schema do Solr) e [`init_db.py`](init_db.py) (popula DB e indexa Solr).
- Banco: SQLAlchemy via [`helpers.database.db`](helpers/database/__init__.py).
- Contêinerização e orquestração: [`docker-compose.yml`](docker-compose.yml), [`Flask.Dockerfile`](Flask.Dockerfile) e [`docker-entrypoint.sh`](docker-entrypoint.sh).

Como executar (com Docker - recomendado)
1. Ajuste variáveis em `.env`/`Postgres.env` (conforme seus segredos).
2. Build e run:
   docker-compose up --build
   - O entrypoint do contêiner da app executa migrações, configura o Solr e popula o DB/Solr via:
     - [`migrations`](migrations/) (Alembic) — `flask db upgrade` é chamado em [`docker-entrypoint.sh`](docker-entrypoint.sh).
     - [`setup_solr.py`](setup_solr.py) — usa [`setup_solr.wait_for_solr`](setup_solr.py) e [`setup_solr.configure_solr_schema`](setup_solr.py).
     - [`init_db.py`](init_db.py) — lê `data/cbo2002-ocupacao.csv` e popula o DB/indexa o Solr.

Como executar localmente (sem Docker)
1. Criar virtualenv e instalar dependências:
   pip install -r requirements.txt
2. Exportar variáveis de ambiente necessárias (ex.: DATABASE_URL, SOLR_HOST, SOLR_QUERY_URL, SOLR_UPDATE_URL).
3. Aplicar migrações:
   flask db upgrade
4. Configurar Solr e popular DB:
   python setup_solr.py
   python init_db.py
5. Rodar app (desenvolvimento):
   export FLASK_APP=app.py
   flask run

Principais endpoints da API
- GET /cbos?q=<texto>&page=&per_page= — pesquisa (usa Solr se `q` fornecido)  
  Implementado em [`resources.CBOResouce.CbosResouce.get`](resources/CBOResouce.py).
- POST /cbos — cria nova CBO (adiciona também ao Solr)  
  Implementado em [`resources.CBOResouce.CbosResouce.post`](resources/CBOResouce.py).
- GET /cbo/<cod_cbo> — retorna CBO por código  
  Implementado em [`resources.CBOResouce.CboResouce.get`](resources/CBOResouce.py).
- PUT /cbo/<cod_cbo> — atualiza (lembrete: sincronizar também com Solr)  
  Implementado em [`resources.CBOResouce.CboResouce.put`](resources/CBOResouce.py).
- DELETE /cbo/<cod_cbo> — remove (lembrete: sincronizar também com Solr)  
  Implementado em [`resources.CBOResouce.CboResouce.delete`](resources/CBOResouce.py).

Arquivos e locais importantes
- [app.py](app.py)
- [docker-compose.yml](docker-compose.yml)
- [docker-entrypoint.sh](docker-entrypoint.sh)
- [Flask.Dockerfile](Flask.Dockerfile)
- [init_db.py](init_db.py)
- [requirements.txt](requirements.txt)
- [setup_solr.py](setup_solr.py)
- [uwsgi.ini](uwsgi.ini)
- [data/cbo2002-ocupacao.csv](data/cbo2002-ocupacao.csv)
- [helpers/application/__init__.py](helpers/application/__init__.py)
- [helpers/CORS/__init__.py](helpers/CORS/__init__.py)
- [helpers/database/__init__.py](helpers/database/__init__.py)
- [migrations/alembic.ini](migrations/alembic.ini)
- [migrations/env.py](migrations/env.py)
- [migrations/README](migrations/README)
- [migrations/script.py.mako](migrations/script.py.mako)
- [migrations/versions/19f132fe4f61_esquema_inicial_de_tabela.py](migrations/versions/19f132fe4f61_esquema_inicial_de_tabela.py)
- [models/CBO.py](models/CBO.py)
- [resources/CBOResouce.py](resources/CBOResouce.py)

Observações e dicas
- CSV: o arquivo fonte está em [data/cbo2002-ocupacao.csv](data/cbo2002-ocupacao.csv) (codificação ISO-8859-1 usada no `init_db.py`).
- Solr: o projeto espera um core `cbo_core` e os scripts de setup tentam criar/configurar o campo `titulo`. Verifique `SOLR_HOST`, `SOLR_QUERY_URL`, `SOLR_UPDATE_URL` nas variáveis de ambiente.
- Migrações: Alembic está configurado em [migrations/](migrations/) — revisão inicial em [migrations/versions/19f132fe4f61_esquema_inicial_de_tabela.py](migrations/versions/19f132fe4f61_esquema_inicial_de_tabela.py).
- Model: chave primária `cod_cbo` definido em [`models.CBO.CBO`](models/CBO.py).
- Tratamento de erros: end points usam `SQLAlchemyError` e `abort` para retornar códigos HTTP apropriados (confira [resources/CBOResouce.py](resources/CBOResouce.py)).

