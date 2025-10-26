# 🏥 SGHSS - Sistema de Gestão Hospitalar e de Serviços de Saúde

**Protótipo Back-end desenvolvido com FastAPI**, voltado à administração de pacientes, profissionais de saúde, consultas, prontuários, prescrições, telemedicina, leitos, suprimentos e finanças.  
Inclui autenticação JWT, controle de acesso por perfil, auditoria LGPD e módulos administrativos.

---

## 🚀 Tecnologias Utilizadas

- **Python 3.11+**
- **FastAPI**
- **SQLAlchemy**
- **Pydantic**
- **JWT (Autenticação e Controle de Acesso)**
- **SQLite (banco padrão com WAL)**
- **Uvicorn** (servidor)
- **bcrypt** (hash de senhas)
- **Logs e Auditoria com LGPD**

---

## ⚙️ Estrutura de Pastas

```
app/
├── api/v1/
│ ├── autenticacao.py
│ ├── pacientes.py
│ ├── medicos.py
│ ├── consultas.py
│ ├── prescricoes.py
│ ├── teleconsultas.py
│ ├── prontuario.py
│ ├── auditoria.py
│ ├── financeiro.py
│ ├── relatorios.py
│ └── backup.py
│
├── core/
│ ├── init.py
│ ├── security.py
│ └── audit.py
│
├── db/
│ ├── init.py
│ ├── session.py
│ └── migrations.py
│
├── models/
│ ├── init.py
│ ├── medical.py
│ ├── audit.py
│ ├── financeiro.py
│ ├── leito.py
│ └── suprimento.py
│
├── schemas/
│ ├── init.py
│ ├── paciente.py
│ ├── medico.py
│ ├── consulta.py
│ ├── teleconsulta.py
│ ├── prescricao.py
│ ├── prontuario.py
│ ├── leito.py
│ ├── financeiro.py
│ └── suprimento.py
│
├── utils/
│ ├── init.py
│ └── logs.py
│
├── uploads/
└── main.py
```

---

## 🧩 Perfis de Usuário

| Perfil | Permissões principais |
|--------|------------------------|
| **ADMIN** | Acesso total a todos os módulos, relatórios e auditoria |
| **MEDICO** | CRUD de pacientes, consultas, prontuários, prescrições e teleconsultas |
| **PACIENTE** | Agendar consultas, visualizar histórico e prescrições próprias |

---

## 🔐 Autenticação

Autenticação baseada em **JWT**.  
Para acessar os endpoints protegidos, obtenha um token via `/api/v1/autenticacao/login` e envie nos headers:

```http
Authorization: Bearer <seu_token_aqui>

```

---

## 🧾 Principais Endpoints

### 🔹 Autenticação (`/api/v1/autenticacao`)
| Método | Rota | Descrição |
|--------|------|------------|
| `POST` | `/login` | Realiza login e retorna token JWT |
| `POST` | `/registrar` | Cadastra novo usuário |
| `GET` | `/me` | Retorna dados do usuário autenticado |

---

### 🔹 Pacientes (`/api/v1/pacientes`)
| Método | Rota | Descrição |
|--------|------|------------|
| `GET` | `/` | Lista todos os pacientes |
| `POST` | `/` | Cadastra paciente |
| `PUT` | `/{id}` | Atualiza dados do paciente |
| `DELETE` | `/{id}` | Exclui paciente |

---

### 🔹 Médicos (`/api/v1/medicos`)
| Método | Rota | Descrição |
|--------|------|------------|
| `GET` | `/` | Lista médicos |
| `POST` | `/` | Cadastra médico |
| `PUT` | `/{id}` | Atualiza médico |
| `DELETE` | `/{id}` | Exclui médico |

---

### 🔹 Consultas (`/api/v1/consultas`)
| Método | Rota | Descrição |
|--------|------|------------|
| `GET` | `/` | Lista consultas |
| `POST` | `/` | Agenda nova consulta |
| `PUT` | `/{id}` | Atualiza dados da consulta |
| `DELETE` | `/{id}` | Cancela consulta |

---

### 🔹 Prontuários (`/api/v1/prontuario`)
| Método | Rota | Descrição |
|--------|------|------------|
| `POST` | `/prontuarios` | Cria prontuário com upload opcional |
| `GET` | `/prontuarios` | Lista todos os prontuários |
| `POST` | `/prontuarios/{id}/cancelar` | Cancela prontuário |

---

### 🔹 Prescrições (`/api/v1/prescricoes`)
| Método | Rota | Descrição |
|--------|------|------------|
| `GET` | `/` | Lista prescrições |
| `POST` | `/` | Cria nova prescrição |
| `PUT` | `/{id}` | Atualiza prescrição |
| `DELETE` | `/{id}` | Cancela prescrição |

---

### 🔹 Teleconsultas (`/api/v1/teleconsultas`)
| Método | Rota | Descrição |
|--------|------|------------|
| `GET` | `/` | Lista teleconsultas |
| `POST` | `/` | Cria teleconsulta (com URL de vídeo) |
| `PUT` | `/{id}` | Atualiza teleconsulta |
| `DELETE` | `/{id}` | Cancela teleconsulta |

---

### 🔹 Financeiro (`/api/v1/financeiro`)
| Método | Rota | Descrição |
|--------|------|------------|
| `GET` | `/` | Lista registros financeiros |
| `POST` | `/` | Adiciona lançamento |
| `PUT` | `/{id}` | Atualiza lançamento |
| `DELETE` | `/{id}` | Remove lançamento |

---

### 🔹 Relatórios (`/api/v1/relatorios`)
| Método | Rota | Descrição |
|--------|------|------------|
| `GET` | `/pacientes` | Relatório de pacientes cadastrados |
| `GET` | `/consultas` | Relatório de consultas realizadas |
| `GET` | `/financeiro` | Relatório financeiro consolidado |
| `GET` | `/geral` | Resumo geral (pacientes, médicos, consultas) |

---

### 🔹 Backup (`/api/v1/backup`)
| Método | Rota | Descrição |
|--------|------|------------|
| `GET` | `/exportar` | Gera backup do banco SQLite |
| `POST` | `/restaurar` | Restaura backup enviado |
| `GET` | `/listar` | Lista backups disponíveis |

---

### 🔹 Auditoria (`/api/v1/auditoria`)
| Método | Rota | Descrição |
|--------|------|------------|
| `GET` | `/` | Lista registros de log/auditoria |
| `GET` | `/{id}` | Detalha log específico |

---

## 🧠 LGPD e Auditoria

- Todos os CRUDs registram logs automáticos (tabela: **Auditoria**).
- Campos sensíveis são protegidos e/ou criptografados.
- Controle de acesso por **perfil de usuário**.
- Histórico de ações acessível apenas a administradores.

---

## 🧰 Execução do Projeto

### ▶️ Rodar localmente
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 🌐 Acessar documentação
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

🧾 Dados Iniciais

- Usuário admin:
  - Email: admin@teste.com
  - Senha: 123456


- Médicos de teste: Dr. João Silva, Dra. Maria Souza

- Pacientes de teste: Carlos Alberto, Ana Paula

Dados populados automaticamente via db/migrations.py.

---

## 🧾 Licença
Projeto acadêmico desenvolvido para fins de estudo e demonstração.  
© 2025 — **Roger de Oliveira Lima**
