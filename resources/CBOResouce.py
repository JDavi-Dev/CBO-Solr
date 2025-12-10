from flask import request, abort
from flask_restful import Resource, marshal

from sqlalchemy.exc import SQLAlchemyError

import requests
import os

from helpers.database import db

from models.CBO import cbo_fields, CBO

SOLR_QUERY_URL = os.getenv("SOLR_QUERY_URL")

class CbosResouce(Resource):
    def get(self):
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 100))
        search_query = request.args.get('q', "").strip()

        if search_query:
            try:
                # 2. Monta e executa a requisição GET para o Solr
                solr_params = {
                    'q': f'titulo:{search_query}',  # Busca no campo 'titulo'
                    'fl': 'cod_cbo, titulo',        # Retorna apenas estes campos
                    'wt': 'json'                    # Formato de resposta JSON
                }
                
                response = requests.get(SOLR_QUERY_URL, params=solr_params)
                response.raise_for_status() # Lança exceção para status 4xx/5xx
                
                solr_data = response.json()
                solr_results = solr_data.get('response', {}).get('docs', [])
                
                # 3. Transforma o resultado do Solr para o formato da API
                cbos_results = []
                for doc in solr_results:
                    cod_cbo_value = doc['cod_cbo']
                    if isinstance(cod_cbo_value, list):
                        cod_cbo_value = cod_cbo_value[0]
                    cbos_results.append({
                        'cod_cbo': cod_cbo_value,
                        'titulo': doc['titulo']
                    })
                
                return marshal(cbos_results, cbo_fields), 200

            except requests.exceptions.RequestException as e:
                # Em caso de falha do Solr, você pode optar por fallback para o DB ou abortar
                abort(503, description="Serviço de busca (Solr) indisponível.")
            except Exception:
                abort(500, description="Ocorreu um erro inesperado na busca.")
        else:
            try:
                cbo = db.session.execute(db.select(CBO).offset((page - 1) * per_page).limit(per_page)).scalars().all()

                # logger.info(f"CBOs retornadas com sucesso")
                return marshal(cbo, cbo_fields), 200

            except SQLAlchemyError:
                db.session.rollback()
                abort(500, description="Problema com o banco de dados.")
            except Exception:
                abort(500, description="Ocorreu um erro inesperado.")

    def post(self):
        cbo_data = request.get_json()

        try:
            nova_cbo = CBO(**cbo_data)

            db.session.add(nova_cbo)
            db.session.commit()
            
            # EXEMPLO DE ADIÇÃO PÓS-POST:
            if nova_cbo:
                doc_to_solr = [{
                    "id": nova_cbo.cod_cbo,
                    "cod_cbo": nova_cbo.cod_cbo,
                    "titulo": nova_cbo.titulo
                }]
                requests.post(SOLR_QUERY_URL.replace("/select", "/update?commit=true"), json=doc_to_solr)

            return marshal(nova_cbo, cbo_fields), 201
        
        except SQLAlchemyError:
            db.session.rollback()
            abort(500, description="Problema com o banco de dados.")
        except Exception:
            abort(500, description="Ocorreu um erro inesperado.")

class CboResouce(Resource):
    def get(self, cod_cbo):
        try:
            cbo = db.session.execute(
                db.select(CBO)
                .filter_by(cod_cbo=cod_cbo)
            ).scalar_one_or_none()

            if cbo is None:
                return {"mensagem": "CBO não encontrada."}, 404

            return marshal(cbo, cbo_fields), 200

        except SQLAlchemyError:
            db.session.rollback()
            abort(500, description="Problema com o banco de dados.")
        except Exception:
            abort(500, description="Ocorreu um erro inesperado.")

    # IMPORTANTE: PUT e DELETE no DB DEVEM ser seguidos por PUT/DELETE no Solr
    def put(self, cod_cbo):
        cbo_data = request.get_json()

        try:
            cbo = db.session.execute(
                db.select(CBO)
                .filter_by(cod_cbo=cod_cbo)
            ).scalar_one_or_none()

            if cbo is None:
                return {"mensagem": "CBO não encontrada."}, 404

            for key, value in cbo_data.items():
                setattr(cbo, key, value)

            db.session.commit()

            return {"mensagem": "CBO atualizada com sucesso."}, 200
        
        except SQLAlchemyError:
            db.session.rollback()
            abort(500, description="Problema com o banco de dados.")
        except Exception:
            abort(500, description="Ocorreu um erro inesperado.")

    def delete(self, cod_cbo):

        try:
            cbo = db.session.execute(
                db.select(CBO)
                .filter_by(cod_cbo=cod_cbo)
            ).scalar_one_or_none()

            if cbo is None:
                return {"mensagem": "CBO não encontrada."}, 404
            
            db.session.delete(cbo)
            db.session.commit()

            return {"mensagem": "CBO removida com sucesso."}, 200
        
        except SQLAlchemyError:
            db.session.rollback()
            abort(500, description="Problema com o banco de dados.")
        except Exception:
            abort(500, description="Ocorreu um erro inesperado.")