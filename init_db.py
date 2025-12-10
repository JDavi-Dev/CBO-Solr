import csv
import requests
import os

from helpers.application import app
from helpers.database import db

from models import CBO
from models.CBO import CBO

SOLR_UPDATE_URL = os.getenv("SOLR_UPDATE_URL")

print("Iniciando a criação e população do banco de dados...")

with app.app_context():
    # --- Inserção de dados (Mantém o load via CSV para popular o DB) ---

    # 2. Inserir CBOs
    print("Populando tabela tb_cbo...")
    cbos_to_add = []

    try:
        # Lê o CSV para popular o banco de dados relacional
        with open("data/cbo2002-ocupacao.csv", "r", encoding="iso-8859-1") as f:
            csv_reader = csv.DictReader(f, delimiter=';')
            for row in csv_reader:
                # O DictReader usa o cabeçalho 'CODIGO' e 'TITULO' como chaves
                cbo_obj = CBO(
                    cod_cbo=int(row['CODIGO']),
                    titulo=row['TITULO']
                )
                cbos_to_add.append(cbo_obj)
        db.session.bulk_save_objects(cbos_to_add)
        db.session.commit()
        print(f"Inseridos {len(cbos_to_add)} registros do CBO no DB.")
    except Exception as e:
        db.session.rollback()
        # Se houver erro (ex: chave primária duplicada em um restart), continua para o Solr
        print(f"Erro ao popular DB com CSV (pode ser chave duplicada): {e}")

    # 3. Indexar CBOs no Solr (LENDO DO BANCO DE DADOS)
    print("Indexando documentos no Solr (lendo do DB)...")
    solr_documents = []
    
    try:
        # Consulta todos os objetos CBO do banco de dados
        # Usa db.select(CBO) do SQLAlchemy para obter todos os registros.
        cbos_from_db = db.session.execute(db.select(CBO)).scalars().all() 

        for cbo in cbos_from_db:
            solr_documents.append({
                "id": str(cbo.cod_cbo),  # Solr usa 'id' como chave primária (String)
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
            
    except requests.exceptions.ConnectionError as e:
        print(f"ERRO: Não foi possível conectar ao Solr. Verifique se o container 'solr' está rodando e acessível. {e}")
    except Exception as e:
        print(f"Erro inesperado durante a indexação Solr: {e}")     

print("Banco e Solr inicializados com sucesso.")