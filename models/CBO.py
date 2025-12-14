from sqlalchemy.orm import Mapped, mapped_column

from helpers.database import db

from flask_restful import fields

cbo_fields = {
    'cod_cbo': fields.Integer,
    'titulo': fields.String
}

class CBO(db.Model):
    __tablename__ = "tb_cbo"

    cod_cbo: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    titulo: Mapped[str] = mapped_column()

def __init__(self, cod_cbo: int, titulo: str):
    self.cod_cbo = cod_cbo
    self.titulo = titulo

def __repr__(self):
    return f"<CBO(cod_cbo={self.cod_cbo}, titulo='{self.titulo}')>"

def __str__(self):
    return f"{self.titulo}"