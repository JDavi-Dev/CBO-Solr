import csv
import requests
import os

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text

from helpers.application import app
from helpers.database import db
from helpers.logging import log_exception

from models import CBO
from models.CBO import CBO

SOLR_UPDATE_URL = os.getenv("SOLR_UPDATE_URL")

print("Iniciando a criação e população do banco de dados...")

with app.app_context():
    # --- Inserção de dados ---

    # 1. Inserir CBOs
    print("Populando tabela tb_cbo...")
    cbos_to_add = []

    try:
        with open("data/cbo2002-ocupacao.csv", "r", encoding="iso-8859-1") as f:
            csv_reader = csv.DictReader(f, delimiter=';')
            for row in csv_reader:
                cbo_obj = CBO(
                    cod_cbo=int(row['CODIGO']),
                    titulo=row['TITULO']
                )
                cbos_to_add.append(cbo_obj)
        db.session.bulk_save_objects(cbos_to_add)

        # Sincroniza a sequência com o valor máximo do cod_cbo
        db.session.execute(text("SELECT setval('public.tb_cbo_cod_cbo_seq', (SELECT MAX(cod_cbo) FROM tb_cbo))"))

        db.session.commit()
        print(f"Inseridos {len(cbos_to_add)} registros do CBO.")
    except SQLAlchemyError:
        db.session.rollback()
        log_exception("Erro SQLAlchemy ao popular tb_cbo")
    except Exception:
        db.session.rollback()
        log_exception("Erro ao processar CSV")

    # 2. Indexar CBOs no Solr
    print("Indexando documentos no Solr...")
    solr_documents = []
    
    try:
        cbos_db = db.session.execute(db.select(CBO)).scalars().all() 

        for cbo in cbos_db:
            solr_documents.append({
                "id": str(cbo.cod_cbo),
                "cod_cbo": cbo.cod_cbo,
                "titulo": cbo.titulo
            })

        # Envia os documentos para o Solr via API JSON
        response = requests.post(
            SOLR_UPDATE_URL,
            json=solr_documents,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print(f"Sucesso ao indexar {len(solr_documents)} documentos no Solr.")
        else:
            print(f"ERRO ao indexar no Solr: Status {response.status_code}, Resposta: {response.text}")
    except SQLAlchemyError:
        db.session.rollback()
        log_exception("Erro SQLAlchemy ao popular tb_cbo")        
    except requests.exceptions.ConnectionError:
        log_exception("ERRO: Não foi possível conectar ao Solr. Verifique se o container 'solr' está rodando e acessível.")
    except Exception:
        log_exception("Erro inesperado durante a indexação Solr")     

print("Banco e Solr inicializados com sucesso.")