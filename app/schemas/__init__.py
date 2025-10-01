# Pacientes
from .patient import PatientCreate, PatientUpdate, PatientResponse

# Médicos
from .doctor import DoctorCreate, DoctorUpdate, DoctorResponse

# Consultas (atendimentos presenciais)
from .appointment import AppointmentCreate, AppointmentResponse

# Teleconsultas
from .teleconsultation import TeleconsultationCreate, TeleconsultationResponse

# Prescrições
from .prescription import PrescriptionCreate, PrescriptionResponse

# Prontuários
from .medical_record import MedicalRecordCreate, MedicalRecordResponse
