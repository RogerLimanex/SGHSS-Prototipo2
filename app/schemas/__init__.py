"""
📦 Módulo: app.schemas
Centraliza a importação de todos os Schemas Pydantic do sistema SGHSS.
Facilita o acesso e mantém consistência entre os módulos.
"""

# ============================================================
# Paciente Schemas
# ============================================================
from .paciente import (
    PacienteCreate,  # Schema para criação de paciente
    PacienteUpdate,  # Schema para atualização de paciente
    PacienteResponse,  # Schema de retorno (response) de paciente
)

# ============================================================
# Médico Schemas
# ============================================================
from .medico import (
    MedicoCreate,  # Schema para criação de médico
    MedicoUpdate,  # Schema para atualização de médico
    MedicoResponse,  # Schema de retorno de médico
)

# ============================================================
# Consulta Schemas
# ============================================================
from .consulta import (
    ConsultaCreate,  # Schema para criar uma consulta
    ConsultaResponse,  # Schema de retorno de consulta
)

# ============================================================
# Teleconsulta Schemas
# ============================================================
from .teleconsulta import (
    TeleconsultaCreate,  # Schema para criar teleconsulta
    TeleconsultaResponse,  # Schema de retorno de teleconsulta
)

# ============================================================
# Prescrição Schemas
# ============================================================
from .prescricao import (
    PrescricaoCreate,  # Schema para criar prescrição médica
    PrescricaoResponse,  # Schema de retorno de prescrição
)

# ============================================================
# Prontuário Schemas
# ============================================================
from .prontuario import (
    ProntuarioMedicoCreate as ProntuarioCreate,  # Schema para criar prontuário (apelidado)
    ProntuarioMedicoResponse as ProntuarioResponse,  # Schema de retorno de prontuário (apelidado)
)

# ============================================================
# Leito Schemas
# ============================================================
from .leito import (
    LeitoBase,  # Schema base de leito (validação de entrada)
    LeitoResponse,  # Schema de retorno de leito
)

# ============================================================
# Financeiro Schemas
# ============================================================
from .financeiro import (
    FinanceiroBase,  # Schema base de movimentação financeira
    FinanceiroResponse,  # Schema de retorno financeiro
    ResumoFinanceiroResponse,  # Schema resumido de financeiro
)
