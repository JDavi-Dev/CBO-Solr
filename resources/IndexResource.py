from flask_restful import Resource

class IndexResource(Resource):
    def get(self):
        versao = {"versao": "1.0.0"}
        return versao, 200