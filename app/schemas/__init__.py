# D:\ProjectSGHSS\app\schemas\__init__.py
"""
📦 Módulo: app.schemas
Centraliza a importação de todos os Schemas Pydantic do sistema SGHSS.
Facilita o acesso e mantém consistência entre os módulos.
"""

# ============================================================
# Paciente Schemas
# ============================================================
from .paciente import (
    PacienteCreate,
    PacienteUpdate,
    PacienteResponse,
)

# ============================================================
# Médico Schemas
# ============================================================
from .medico import (
    MedicoCreate,
    MedicoUpdate,
    MedicoResponse,
)

# ============================================================
# Consulta Schemas
# ============================================================
from .consulta import (
    ConsultaCreate,
    ConsultaResponse,
)

# ============================================================
# Teleconsulta Schemas
# ============================================================
from .teleconsulta import (
    TeleconsultaCreate,
    TeleconsultaResponse,
)

# ============================================================
# Prescrição Schemas
# ============================================================
from .prescricao import (
    PrescricaoCreate,
    PrescricaoResponse,
)

# ============================================================
# Prontuário Schemas
# ============================================================
from .prontuario import (
    ProntuarioMedicoCreate as ProntuarioCreate,
    ProntuarioMedicoResponse as ProntuarioResponse,
)

# ============================================================
# Leito Schemas
# ============================================================
from .leito import (
    LeitoBase,
    LeitoResponse,
)

# ============================================================
# Financeiro Schemas
# ============================================================
from .financeiro import (
    FinanceiroBase,
    FinanceiroResponse,
    ResumoFinanceiroResponse,
)
