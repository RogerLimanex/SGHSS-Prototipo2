# ============================================================
# Paciente Schemas
# ============================================================
from .paciente import (
    PacienteCreate,
    PacienteUpdate,
    PacienteResponse
)

# ============================================================
# Médico Schemas
# ============================================================
from .medico import (
    MedicoCreate,
    MedicoUpdate,
    MedicoResponse
)

# ============================================================
# Consulta Schemas
# ============================================================
from .consulta import (
    ConsultaCreate,
    ConsultaResponse
)

# ============================================================
# Teleconsulta Schemas
# ============================================================
from .teleconsulta import (
    TeleconsultaCreate,
    TeleconsultaResponse
)

# ============================================================
# Prescrição Schemas
# ============================================================
from .prescricao import (
    PrescricaoCreate,
    PrescricaoResponse
)

# ============================================================
# Prontuário Schemas
# ============================================================
from .prontuario import (
    ProntuarioMedicoCreate as ProntuarioCreate,
    ProntuarioMedicoResponse as ProntuarioResponse
)

# ============================================================
# Leito Schemas
# ============================================================
from .leito import (
    LeitoBase,
    LeitoResponse
)
