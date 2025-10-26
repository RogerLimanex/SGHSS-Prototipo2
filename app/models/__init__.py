# D:\ProjectSGHSS\app\models\__init__.py
# Inicializa os modelos da aplicação, permitindo importações unificadas

# ----------------------------
# Audit Logs
# ----------------------------
from .audit import AuditLog  # Modelo de log de auditoria do sistema

# ----------------------------
# Modelos principais (médico, paciente, consultas, prontuário, receitas, teleconsultas)
# ----------------------------
from .medical import (
    Usuario,  # Usuário do sistema (admin, médico)
    Paciente,  # Paciente cadastrado
    Medico,  # Médico cadastrado
    Consulta,  # Consultas agendadas
    Prontuario,  # Prontuários médicos
    Receita,  # Prescrições médicas
    Teleconsulta,  # Teleconsultas
    StatusConsulta,  # Enum de status da consulta
    PapelUsuario,  # Enum de papéis de usuário (ADMIN, MEDICO, etc.)
)

# ----------------------------
# Financeiro
# ----------------------------
from .financeiro import Financeiro  # Modelo de movimentações financeiras

# ----------------------------
# Suprimentos
# ----------------------------
from .suprimento import Suprimento  # Modelo de suprimentos do sistema

# ----------------------------
# Leitos
# ----------------------------
from .leito import Leito  # Modelo de leitos hospitalares
