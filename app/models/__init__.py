# D:\ProjectSGHSS\app\models\__init__.py

# ----------------------------
# Audit Logs
# ----------------------------
from .audit import AuditLog

# ----------------------------
# Modelos principais (médico, paciente, consultas, etc.)
# ----------------------------
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

# ----------------------------
# Financeiro
# ----------------------------
from .financeiro import Financeiro

# ----------------------------
# Suprimentos
# ----------------------------
from .suprimento import Suprimento

# ----------------------------
# Leitos
# ----------------------------
from .leito import Leito
