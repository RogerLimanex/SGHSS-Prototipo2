# D:\ProjectSGHSS\app\models\__init__.py

# Importa AuditLog
from .audit import AuditLog

# Importa todos os modelos principais do medical.py
from .medical import (
    Usuario,
    Paciente,
    Medico,
    Consulta,
    Prontuario,
    Receita,
    Teleconsulta,
    StatusConsulta,
    PapelUsuario,
)
