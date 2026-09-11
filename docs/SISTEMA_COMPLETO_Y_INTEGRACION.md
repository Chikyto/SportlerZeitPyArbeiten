# Sistema de Cronometraje RFID - Documentación Completa e Integración

**Versión**: 2.0
**Fecha**: 2026-03-03
**Estado**: Sistema de Timing Funcional + Plan de Integración con Plataforma de Registro

---

## 📋 Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Sistema Actual - Estado y Capacidades](#sistema-actual---estado-y-capacidades)
3. [Arquitectura Técnica](#arquitectura-técnica)
4. [Funcionalidades Existentes](#funcionalidades-existentes)
5. [Integración con Plataforma de Registro](#integración-con-plataforma-de-registro)
6. [Arquitectura de Integración](#arquitectura-de-integración)
7. [Plan de Implementación](#plan-de-implementación)
8. [Casos de Uso y Escenarios](#casos-de-uso-y-escenarios)
9. [Apéndices Técnicos](#apéndices-técnicos)

---

## 1. Resumen Ejecutivo

### 1.1 ¿Qué es el Sistema?

**RFID Athletics Timer** es un sistema profesional de cronometraje deportivo con tecnología RFID para carreras de atletismo. Permite el registro automático de tiempos mediante chips RFID y lectores YR8900/YR9011.

### 1.2 Componentes Principales

```
┌─────────────────────────────────────────────────────────────┐
│                  SISTEMA DE TIMING RFID                      │
│                                                              │
│  ┌────────────────┐         ┌──────────────────┐           │
│  │  Hardware RFID │────────▶│  Aplicación      │           │
│  │  - YR8900/9011 │         │  Desktop         │           │
│  │  - Antenas     │         │  (Python/PyQt6)  │           │
│  └────────────────┘         └──────────────────┘           │
│                                     │                        │
│                                     ▼                        │
│                         ┌────────────────────┐              │
│                         │  SQLite Local      │              │
│                         │  - Detecciones     │              │
│                         │  - Resultados      │              │
│                         │  - Configuración   │              │
│                         └────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Estado Actual

| Aspecto | Estado | Detalles |
|---------|--------|----------|
| **Hardware** | ✅ Funcionando | Soporte YR8900 (TCP/IP) y YR9011 (USB) |
| **Detección RFID** | ✅ Funcionando | Multi-antena con rotación automática |
| **Interfaz Gráfica** | ✅ Funcionando | PyQt6 con múltiples tabs |
| **Gestión de Carreras** | ✅ Funcionando | Múltiples distancias/categorías |
| **Asignación de Chips** | ✅ Funcionando | Widget dedicado para asignar chips |
| **Resultados** | ✅ Funcionando | Tiempo real, clasificaciones |
| **Exportación** | ✅ Funcionando | PDF, CSV con resultados |
| **Persistencia Local** | ✅ Funcionando | SQLite para datos locales |
| **Integración Web** | ⚠️ Parcial | API client implementado, requiere backend |
| **Pre-registro Web** | ❌ Pendiente | Requiere integración con plataforma |

---

## 2. Sistema Actual - Estado y Capacidades

### 2.1 Capacidades Operacionales

#### ✅ Configuración Automática (AutoWizard)
- **Auto-detección**: Conexión automática al lector RFID en <0.5s
- **Detección física de antenas**: Escaneo automático de antenas conectadas (2s)
- **Configuración de roles**: Asignación de roles (Largada/Meta/Checkpoint) por antena
- **Persistencia**: Guarda configuración para futuras sesiones

#### ✅ Detección RFID Multi-Antena
- **Hardware soportado**:
  - YR8900: Lector TCP/IP (hasta 8 antenas)
  - YR9011: Lector USB (hasta 4 antenas)
- **Rotación automática**: Escaneo continuo entre todas las antenas activas
- **Roles múltiples**: Una antena puede ser Largada+Meta simultáneamente
- **Anti-duplicados**: Sistema de latencia configurable para evitar lecturas duplicadas
- **Detección robusta**: Return loss para validar antenas físicamente conectadas

#### ✅ Gestión de Carreras
- **Múltiples distancias**: 5K, 10K, 21K, 42K, Ultra (50K, 100K, etc.)
- **Categorías de premiación**: IAAF estándar por género y edad
  - Sub-20 (15-19)
  - Elite (20-34)
  - Master A-E (35+)
- **Estados de carrera**: Pending, Ready, Running, Finished
- **Modos de carrera**:
  - Linear: Largada → Checkpoints → Meta
  - Laps: Vueltas (misma antena múltiples veces)
  - Time-based: Máximo de vueltas en X horas

#### ✅ Gestión de Participantes
- **Importación**:
  - CSV manual
  - API REST (implementado pero requiere backend)
- **Asignación de chips**:
  - Manual: Seleccionar atleta y escanear chip
  - Masiva: Importar CSV con asignaciones
  - Por scanner: Modo escucha para asignar chips en tiempo real
- **Datos de atleta**:
  - Datos básicos: Nombre, dorsal, categoría
  - Datos extendidos: Edad, género, equipo, contacto de emergencia
  - Notas personalizables

#### ✅ Tracking en Tiempo Real
- **Detecciones**: Registro de todas las lecturas RFID con timestamp preciso
- **Resultados**: Cálculo automático de tiempos
- **Clasificaciones**: Rankings actualizados en tiempo real
- **Splits**: Tiempos parciales en checkpoints
- **Vueltas**: Contador automático para carreras por vueltas

#### ✅ Exportación y Reportes
- **Formatos**:
  - PDF: Resultados profesionales con logo
  - CSV: Para análisis en Excel
  - JSON: Para integraciones
- **Contenido**:
  - Clasificación general
  - Clasificación por categorías de premiación
  - Tiempos parciales (splits)
  - Estadísticas generales

### 2.2 Limitaciones Actuales

| Limitación | Impacto | Solución Propuesta |
|------------|---------|-------------------|
| **Sin pre-registro web** | Organización manual el día del evento | Integración con plataforma de registro |
| **Resultados solo locales** | Espectadores no pueden ver resultados online | Sincronización con backend web |
| **Configuración manual de categorías** | Trabajo previo duplicado | Importación desde plataforma |
| **Sin backup en cloud** | Riesgo de pérdida de datos | Sincronización automática |

### 2.3 Tecnologías Utilizadas

```python
# Stack Tecnológico Actual
{
    "Lenguaje": "Python 3.10+",
    "GUI Framework": "PyQt6 6.6.1",
    "Comunicación": {
        "TCP/IP": "socket (built-in)",
        "Serial USB": "pyserial 3.5",
        "HTTP": "requests 2.31.0"
    },
    "Base de Datos": "SQLite (local)",
    "Exportación": "reportlab 4.0.9",
    "Async": "asyncio + aiohttp",
    "Modelos": "dataclasses + dataclasses-json"
}
```

---

## 3. Arquitectura Técnica

### 3.1 Arquitectura de Capas

```
┌──────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                      │
│  src/gui/                                                     │
│  ├─ main_window.py        (Ventana principal)                │
│  ├─ tabs/                 (Pestañas de UI)                   │
│  │  ├─ detection_tab.py   (Detección en vivo)               │
│  │  ├─ event_config_tab.py (Configuración de evento)        │
│  │  ├─ competition_tab.py  (Asignación de chips)            │
│  │  └─ configuration_tab.py (Config de hardware)            │
│  ├─ widgets/              (Componentes visuales)             │
│  │  ├─ chip_assignment_widget.py                            │
│  │  ├─ race_monitoring_widget.py                            │
│  │  └─ event_config_widget.py                               │
│  └─ wizard/               (Configuración inicial)            │
│     └─ auto_wizard.py     (AutoWizard)                       │
└──────────────────────────────────────────────────────────────┘
                              ↕
┌──────────────────────────────────────────────────────────────┐
│                   CAPA DE GESTIÓN                            │
│  src/gui/managers/                                            │
│  ├─ antenna_manager.py    (Gestión de antenas)              │
│  └─ tab_manager.py        (Gestión de tabs)                 │
└──────────────────────────────────────────────────────────────┘
                              ↕
┌──────────────────────────────────────────────────────────────┐
│                  CAPA DE NEGOCIO                             │
│  src/core/                                                    │
│  ├─ race_tracking/                                           │
│  │  ├─ race_manager.py    (Gestor principal de carreras)    │
│  │  ├─ models.py          (Modelos de datos)                │
│  │  └─ results_exporter.py (Exportación de resultados)      │
│  ├─ advanced_scanner.py   (Lógica de scanning)              │
│  ├─ tag_processor.py      (Procesamiento de tags)           │
│  ├─ athlete_importer.py   (Importación de atletas)          │
│  └─ csv_importer.py       (Importación CSV)                 │
└──────────────────────────────────────────────────────────────┘
                              ↕
┌──────────────────────────────────────────────────────────────┐
│                   CAPA DE HARDWARE                           │
│  hardware/                                                    │
│  ├─ yr8900_protocol.py    (Protocolo YR8900 TCP/IP)         │
│  ├─ reader_manager.py     (Gestor de alto nivel)            │
│  └─ antenna_detection.py  (Detección física)                │
│  src/core/                                                    │
│  └─ yr9011_usb_scanner.py (Protocolo YR9011 USB)            │
└──────────────────────────────────────────────────────────────┘
                              ↕
┌──────────────────────────────────────────────────────────────┐
│                   CAPA DE DATOS                              │
│  src/data/                                                    │
│  ├─ database.py           (SQLite manager)                   │
│  ├─ models.py             (ORM models)                       │
│  └─ export.py             (Exportación de datos)             │
└──────────────────────────────────────────────────────────────┘
                              ↕
┌──────────────────────────────────────────────────────────────┐
│                   CAPA DE INTEGRACIÓN                        │
│  src/api/                                                     │
│  └─ client.py             (Cliente API REST)                 │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Flujo de Datos Principal

```
┌─────────────┐
│   Antena    │ Detecta chip RFID
│   RFID      │
└──────┬──────┘
       │ EPC: 7662
       ▼
┌─────────────────────┐
│  ReaderManager      │ Lee del hardware
│  (Hardware Layer)   │
└──────┬──────────────┘
       │ tag_data
       ▼
┌─────────────────────┐
│  AdvancedScanner    │ Rota antenas, emite señales
│  (Core Layer)       │
└──────┬──────────────┘
       │ tag_detected signal
       ▼
┌─────────────────────┐
│  TagProcessor       │ Parsea EPC, identifica roles
│  (Core Layer)       │
└──────┬──────────────┘
       │ tag_info
       ▼
┌─────────────────────┐
│  RaceManager        │ Procesa detección, actualiza resultados
│  (Core Layer)       │
└──────┬──────────────┘
       │
       ├──────────────┐ DetectionEvent
       │              ▼
       │         ┌─────────────────┐
       │         │  Database       │ Guarda en SQLite
       │         │  (Data Layer)   │
       │         └─────────────────┘
       │
       ├──────────────┐ AthleteResult
       │              ▼
       │         ┌─────────────────┐
       │         │  API Client     │ Envía a backend web (opcional)
       │         │  (API Layer)    │
       │         └─────────────────┘
       │
       └──────────────┐ UI Update
                      ▼
                 ┌─────────────────┐
                 │  GUI Tabs       │ Actualiza interfaz
                 │  (GUI Layer)    │
                 └─────────────────┘
```

### 3.3 Modelos de Datos Principales

```python
# ===== ATLETA =====
@dataclass
class Athlete:
    """Participante en una carrera"""
    athlete_id: str          # UUID único
    tag_id: str              # Chip RFID (puede estar vacío)
    bib_number: int          # Número de dorsal
    name: str                # Nombre completo
    distance_id: str         # Distancia inscrita (5k, 10k, etc.)
    gender: Optional[str]    # M, F, Otro
    birth_date: Optional[datetime]  # Para calcular edad
    team: Optional[str]      # Equipo o club
    notes: Optional[str]     # Notas adicionales

# ===== DISTANCIA DE CARRERA =====
@dataclass
class RaceDistance:
    """Distancia de carrera (5K, 10K, etc.)"""
    distance_id: str         # Identificador (5k, 10k, 21k, etc.)
    name: str                # Nombre descriptivo
    distance: float          # Distancia en km
    expected_checkpoints: int  # Cantidad de checkpoints
    mode: RaceMode           # LINEAR, LAPS, TIME_BASED
    max_laps: Optional[int]  # Para modo LAPS
    max_time: Optional[timedelta]  # Para TIME_BASED
    participants: List[Athlete]  # Lista de atletas
    status: RaceStatus       # PENDING, READY, RUNNING, FINISHED
    scheduled_start: Optional[datetime]  # Hora programada
    actual_start: Optional[datetime]     # Hora real de largada

# ===== EVENTO DE DETECCIÓN =====
@dataclass
class DetectionEvent:
    """Evento de detección de chip RFID"""
    tag_id: str              # Chip detectado
    timestamp: datetime      # Momento de detección
    antenna_port: int        # Puerto de antena (1-8)
    event_type: EventType    # START, CHECKPOINT, FINISH, LAP
    distance_id: str         # Distancia asociada
    athlete: Optional[Athlete]  # Atleta (si se encontró)
    checkpoint_number: Optional[int]  # Número de checkpoint
    lap_number: Optional[int]  # Número de vuelta

# ===== RESULTADO DE ATLETA =====
@dataclass
class AthleteResult:
    """Resultado de un atleta en la carrera"""
    athlete: Athlete         # Referencia al atleta
    distance_id: str         # Distancia
    status: AthleteStatus    # NOT_STARTED, RUNNING, FINISHED, DNF, etc.
    start_time: Optional[datetime]  # Tiempo de largada
    finish_time: Optional[datetime]  # Tiempo de llegada
    total_time: Optional[timedelta]  # Tiempo total
    checkpoint_times: Dict[int, datetime]  # {checkpoint_num: timestamp}
    splits: Dict[int, timedelta]  # {checkpoint_num: tiempo_parcial}
    position: Optional[int]  # Posición en clasificación
    award_category_position: Optional[int]  # Posición en su categoría
    laps_completed: int      # Para carreras por vueltas

# ===== CATEGORÍA DE PREMIACIÓN =====
@dataclass
class AwardCategory:
    """Categoría de premiación por género y edad"""
    award_category_id: str   # Ej: "M20-34", "F35-39"
    name: str                # Nombre descriptivo
    gender: str              # M, F
    min_age: int             # Edad mínima
    max_age: Optional[int]   # Edad máxima (None = sin límite)
```

---

## 4. Funcionalidades Existentes

### 4.1 Wizard de Configuración Inicial

**Ubicación**: `src/gui/wizard/auto_wizard.py`

#### Proceso Automático
1. **Auto-conexión** (0.5s):
   - Busca lector RFID en red/USB
   - Valida firmware
   - Establece conexión

2. **Auto-detección de antenas** (2s):
   - Escanea puertos 1-8 (YR8900) o 1-4 (YR9011)
   - Mide return loss para validar conexión física
   - Identifica antenas conectadas

3. **Configuración de roles** (usuario):
   - Asigna roles a cada antena:
     - ✅ Largada
     - ✅ Checkpoint
     - ✅ Meta
     - ✅ Combinaciones (Largada+Meta)
   - Asigna nombres personalizados

4. **Guardado de configuración**:
   - Persiste en `timing_system_config.json`
   - Carga automática en futuros inicios

**Tiempo total**: ~5 segundos (3s automático + 2s usuario)

### 4.2 Detección y Tracking RFID

**Ubicación**: `src/core/advanced_scanner.py`, `src/core/tag_processor.py`

#### Características
- **Multi-antena**: Rotación automática entre todas las antenas activas
- **Scan rápido**: <300ms por antena
- **Anti-duplicados**: Sistema de latencia configurable
  - Mínimo 3s entre lecturas en misma antena
  - Grace period de 45s después de largada
- **Parsing inteligente**: Detecta formato GEN2 EPC
- **Identificación de roles**: Determina automáticamente si es largada/checkpoint/meta

#### Flujo de Detección
```python
# Ejemplo de procesamiento
tag_detected = "E28011700000000000007662"  # EPC completo
parsed_tag = "7662"  # Tag ID parseado
antenna_port = 2
roles = ["start"]  # Según configuración de antena

# RaceManager procesa
event = race_manager.process_detection(
    tag_id="7662",
    timestamp=datetime.now(),
    antenna_port=2,
    roles=["start"]
)

# Resultado
# → Athlete "Juan Pérez" started at 14:30:25.123
# → Status: RUNNING
# → Start time recorded
```

### 4.3 Gestión de Carreras

**Ubicación**: `src/core/race_tracking/race_manager.py`

#### Operaciones Principales

```python
# 1. Crear distancia
distance_5k = RaceDistance(
    distance_id="5k",
    name="5 Kilómetros",
    distance=5.0,
    expected_checkpoints=0,
    mode=RaceMode.LINEAR
)
race_manager.add_distance(distance_5k)

# 2. Agregar atletas
athlete = Athlete(
    tag_id="7662",
    bib_number=101,
    name="Juan Pérez",
    distance_id="5k",
    gender="M",
    birth_date=datetime(1990, 5, 15)
)
distance_5k.add_participant(athlete)

# 3. Iniciar carrera
race_manager.start_distance("5k")

# 4. Procesar detecciones
# (Automático cuando scanner detecta chips)

# 5. Obtener resultados
results = race_manager.get_classification("5k")
# Returns: List[AthleteResult] ordenados por tiempo

# 6. Exportar
from src.core.race_tracking.results_exporter import ResultsExporter
exporter = ResultsExporter()
exporter.export_to_pdf("5k", results, "resultados_5k.pdf")
```

#### Clasificaciones
- **General**: Todos los participantes
- **Por género**: Masculino / Femenino
- **Por categoría de edad**: IAAF estándar
- **Por equipo**: Ranking por equipos

### 4.4 Asignación de Chips

**Ubicación**: `src/gui/widgets/chip_assignment_widget.py`

#### Métodos de Asignación

**1. Manual (UI)**
```
┌──────────────────────────────────────────────┐
│  Atleta: [Dropdown]  Juan Pérez (#101)      │
│  Chip:   [Input]     7662                    │
│  [Asignar]                                   │
└──────────────────────────────────────────────┘
```

**2. Por Scanner (Modo Escucha)**
```
1. Seleccionar atleta en lista
2. Activar "Modo Scanner"
3. Pasar chip por antena
4. Asignación automática
```

**3. Importación Masiva (CSV)**
```csv
bib_number,chip_id
101,7662
102,7663
103,7664
```

### 4.5 Exportación de Resultados

**Ubicación**: `src/core/race_tracking/results_exporter.py`, `src/utils/pdf_exporter.py`

#### Formatos Disponibles

**PDF Profesional**
- Logo del evento
- Información de la carrera
- Tabla de resultados con:
  - Posición
  - Dorsal
  - Nombre
  - Categoría
  - Tiempo final
  - Tiempo por km
- Clasificaciones por categoría de premiación

**CSV para Análisis**
```csv
position,bib,name,category,finish_time,total_seconds,pace_per_km,checkpoints
1,101,Juan Pérez,M20-34,00:25:15,1515,00:05:03,2
2,102,María González,F20-34,00:26:45,1605,00:05:21,2
```

**JSON para Integraciones**
```json
{
  "event": "5K Race",
  "distance": "5k",
  "date": "2026-03-03",
  "results": [
    {
      "position": 1,
      "athlete_id": "uuid-123",
      "bib_number": 101,
      "name": "Juan Pérez",
      "total_time": "00:25:15",
      "splits": {...}
    }
  ]
}
```

---

## 5. Integración con Plataforma de Registro

### 5.1 Principios de Integración

#### 🎯 Objetivo: Sistemas Independientes pero Interoperables

```
┌────────────────────────────────────────────────────────────┐
│                    PRINCIPIO CLAVE                          │
│                                                             │
│  Cada sistema debe poder funcionar de forma INDEPENDIENTE  │
│  Una organización puede contratar:                         │
│  • Solo la plataforma de registro                          │
│  • Solo el sistema de timing                               │
│  • Ambos servicios (con integración)                       │
└────────────────────────────────────────────────────────────┘
```

#### Características de Independencia

| Sistema | Funcionamiento Standalone |
|---------|--------------------------|
| **Sistema de Timing** | ✅ Importación CSV manual<br>✅ Configuración local<br>✅ Exportación local<br>✅ No requiere internet |
| **Plataforma de Registro** | ✅ Gestión de inscripciones<br>✅ Pagos online<br>✅ Comunicaciones<br>✅ Reportes administrativos |

### 5.2 Puntos de Integración

```
ANTES DEL EVENTO                 DÍA DEL EVENTO                DESPUÉS DEL EVENTO

┌─────────────────┐             ┌─────────────────┐           ┌─────────────────┐
│  Plataforma     │             │  Sistema        │           │  Plataforma     │
│  Registro       │             │  Timing         │           │  Registro       │
└────────┬────────┘             └────────┬────────┘           └────────┬────────┘
         │                               │                             │
         │ 1. Exportar                   │                             │
         │    Inscripciones              │                             │
         │                               │                             │
         ▼                               │                             │
    ┌─────────┐                          │                             │
    │   CSV   │──────────────────────────▶ 2. Importar                │
    │   API   │                          │    Participantes            │
    └─────────┘                          │                             │
                                         │                             │
                                         │ 3. Asignar Chips            │
                                         │                             │
                                         │ 4. Detectar Tiempos         │
                                         │                             │
                                         │ 5. (Opcional)               │
                                         │    Enviar en vivo           │
                                         │    ───────────────────────▶ Resultados
                                         │                             │  en vivo
                                         ▼                             │
                                    ┌─────────┐                        │
                                    │   CSV   │────────────────────────▶ 6. Importar
                                    │   PDF   │                        │    Resultados
                                    └─────────┘                        │    Finales
                                                                       ▼
                                                                  ┌──────────┐
                                                                  │ Diplomas │
                                                                  │ Emails   │
                                                                  │ Stats    │
                                                                  └──────────┘
```

### 5.3 Modos de Operación

#### Modo 1: Sistema de Timing Standalone (Sin Plataforma)
```
Organización pequeña, sin pre-registro web

Día del evento:
1. Organización recibe inscripciones manualmente
2. Crea CSV con participantes
3. Importa a sistema de timing
4. Asigna chips
5. Corre carrera
6. Exporta resultados PDF/CSV
7. Publica resultados manualmente
```

#### Modo 2: Plataforma de Registro Standalone (Sin Timing)
```
Evento sin cronometraje electrónico

Antes del evento:
1. Participantes se registran en plataforma
2. Pagan online
3. Reciben confirmación

Día del evento:
4. Check-in manual
5. Cronometraje manual o sin cronometraje
```

#### Modo 3: Integración Completa (Ambos Sistemas)
```
Evento profesional con integración

Antes del evento:
1. Participantes se registran en plataforma
2. Sistema de timing importa datos vía API/CSV
3. Organizador asigna chips (día previo o día del evento)

Día del evento:
4. Sistema de timing detecta automáticamente
5. (Opcional) Envía resultados en tiempo real a plataforma
6. Espectadores ven resultados en vivo en web

Después del evento:
7. Sistema de timing exporta resultados finales
8. Plataforma importa y genera diplomas/emails
```

---

## 6. Arquitectura de Integración

### 6.1 Arquitectura General

```
┌──────────────────────────────────────────────────────────────────────┐
│                        PLATAFORMA DE REGISTRO                         │
│                      (Cloud Run + Vercel + DB)                        │
│                                                                       │
│  ┌────────────────┐    ┌─────────────┐    ┌──────────────────────┐ │
│  │   Frontend     │────│   Backend   │────│   Base de Datos      │ │
│  │   (Vercel)     │    │ (Cloud Run) │    │ (PostgreSQL/MySQL)   │ │
│  └────────────────┘    └─────────────┘    └──────────────────────┘ │
│                              ▲  ▼                                     │
└──────────────────────────────┼──┼────────────────────────────────────┘
                               │  │
                         API REST / CSV
                               │  │
┌──────────────────────────────┼──┼────────────────────────────────────┐
│                               ▼  ▲                                     │
│                        CAPA DE INTEGRACIÓN                            │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  src/api/client.py - RaceAPIClient                          │    │
│  │  • Cola asíncrona de mensajes                               │    │
│  │  • Retry automático con exponential backoff                 │    │
│  │  • No bloquea sistema de timing                             │    │
│  │  • Modo offline (continúa si falla conexión)                │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  src/core/athlete_importer.py - AthleteImporter            │    │
│  │  • Importación desde API REST                               │    │
│  │  • Importación desde CSV                                    │    │
│  │  • Mapeo de campos configurable                             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                               ▲  ▼                                    │
└───────────────────────────────┼──┼───────────────────────────────────┘
                                │  │
┌───────────────────────────────┼──┼───────────────────────────────────┐
│                                ▼  ▲                                   │
│                      SISTEMA DE TIMING LOCAL                          │
│                      (Python + PyQt6 + SQLite)                        │
│                                                                       │
│  ┌────────────────┐    ┌─────────────┐    ┌──────────────────────┐ │
│  │   GUI          │────│ RaceManager │────│   SQLite Local       │ │
│  │   (PyQt6)      │    │   (Core)    │    │   (Datos primarios)  │ │
│  └────────────────┘    └─────────────┘    └──────────────────────┘ │
│          ▲                                                            │
│          │                                                            │
│  ┌───────┴────────┐                                                  │
│  │ RFID Hardware  │                                                  │
│  │ (YR8900/9011)  │                                                  │
│  └────────────────┘                                                  │
└──────────────────────────────────────────────────────────────────────┘
```

### 6.2 Flujo de Datos: Importación de Participantes

```python
# PASO 1: Organización configura integración
# config/api_config.json
{
    "api_url": "https://your-backend-xyz123.run.app",
    "api_key": "your-api-key-here",
    "event_id": "ultra-trail-2026",
    "sync_enabled": true,
    "sync_interval_seconds": 10,
    "import_enabled": true
}

# PASO 2: Sistema de timing importa participantes
from src.core.athlete_importer import AthleteImporter

importer = AthleteImporter(
    api_url="https://your-backend.run.app",
    api_key="your-api-key"
)

# Opción A: Desde API REST
categories = importer.import_categories(event_id="ultra-trail-2026")
athletes_by_cat = importer.import_athletes(event_id="ultra-trail-2026")

# Opción B: Desde CSV exportado
athletes_by_cat = importer.import_from_csv("participantes.csv")

# PASO 3: Cargar en RaceManager
for category in categories:
    race_manager.add_distance(category)
    for athlete in athletes_by_cat[category.distance_id]:
        category.add_participant(athlete)

# PASO 4: Asignar chips (día del evento)
# Via GUI en ChipAssignmentWidget

# PASO 5: Durante la carrera
# Detecciones automáticas → RaceManager

# PASO 6: (Opcional) Enviar resultados en vivo
if api_client:
    await api_client.send_detection(event)
    await api_client.send_result(result)
```

### 6.3 Formato de Datos de Integración

#### Estructura de Participante (Export desde Plataforma)

**API REST**
```json
GET /api/events/{event_id}/athletes

Response:
{
  "success": true,
  "event_id": "ultra-trail-2026",
  "total_athletes": 250,
  "athletes": [
    {
      "athlete_id": "uuid-abc-123",
      "bib_number": 101,
      "first_name": "Juan",
      "last_name": "Pérez",
      "full_name": "Juan Pérez",
      "email": "juan@example.com",
      "phone": "+5491112345678",
      "birth_date": "1990-05-15",
      "gender": "M",
      "category_id": "5k",
      "team_name": "Club Runners",
      "emergency_contact_name": "María Pérez",
      "emergency_contact_phone": "+5491187654321",
      "payment_status": "confirmed",
      "shirt_size": "L",
      "medical_notes": "Asmático - tiene inhalador",
      "registration_date": "2026-01-15T10:30:00Z"
    },
    ...
  ]
}
```

**CSV Export**
```csv
athlete_id,bib_number,full_name,email,phone,birth_date,gender,category_id,team_name,emergency_contact,payment_status
uuid-abc-123,101,Juan Pérez,juan@example.com,+5491112345678,1990-05-15,M,5k,Club Runners,"María Pérez +5491187654321",confirmed
```

#### Estructura de Detección (Import a Plataforma)

**API REST**
```json
POST /api/events/{event_id}/detection

Request:
{
  "tag_id": "7662",
  "athlete_id": "uuid-abc-123",
  "bib_number": 101,
  "timestamp": "2026-03-03T14:30:25.123Z",
  "antenna_port": 2,
  "event_type": "start",
  "category_id": "5k",
  "checkpoint_number": null,
  "athlete_name": "Juan Pérez"
}

Response:
{
  "success": true,
  "detection_id": "det-xyz-789"
}
```

#### Estructura de Resultado (Import a Plataforma)

**API REST**
```json
POST /api/events/{event_id}/result

Request:
{
  "athlete_id": "uuid-abc-123",
  "bib_number": 101,
  "category_id": "5k",
  "status": "finished",
  "start_time": "2026-03-03T14:30:00.000Z",
  "finish_time": "2026-03-03T14:55:15.234Z",
  "total_seconds": 1515.234,
  "position_overall": 1,
  "position_gender": 1,
  "position_category": 1,
  "checkpoint_times": {
    "1": "2026-03-03T14:42:30.123Z"
  },
  "splits_seconds": {
    "1": 750.123
  }
}

Response:
{
  "success": true,
  "result_id": "res-xyz-789",
  "public_url": "https://results.example.com/ultra-2026/athlete/uuid-abc-123"
}
```

### 6.4 Implementación de Cliente API

**Ubicación**: `src/api/client.py`

#### Características Clave

```python
class RaceAPIClient:
    """
    Cliente asíncrono para enviar datos a servidor web

    Características:
    - ✅ Cola de mensajes con procesamiento asíncrono
    - ✅ Retry automático con exponential backoff (2s, 4s, 8s)
    - ✅ No bloquea el sistema de timing local
    - ✅ Continúa funcionando si el servidor está caído
    - ✅ Estadísticas de envío (sent/failed/queued)
    - ✅ Modo offline (enabled=False)
    """

    def __init__(
        self,
        api_url: str,
        event_id: str,
        api_key: Optional[str] = None,
        enabled: bool = True
    ):
        self.api_url = api_url
        self.event_id = event_id
        self.enabled = enabled  # ← Modo offline
        self.queue = asyncio.Queue()  # ← Cola asíncrona
        self.stats = {'sent': 0, 'failed': 0, 'queued': 0}

    async def send_detection(self, detection_event):
        """Agregar a cola (no bloquea)"""
        await self.queue.put({
            'type': 'detection',
            'data': {...}
        })

    async def _worker(self):
        """Worker que procesa cola con retry"""
        while True:
            item = await self.queue.get()

            # Intentar 3 veces con exponential backoff
            for attempt in range(3):
                try:
                    async with self.session.post(url, json=data) as response:
                        if response.status == 200:
                            self.stats['sent'] += 1
                            break
                except Exception as e:
                    if attempt < 2:
                        await asyncio.sleep(2 ** (attempt + 1))
```

#### Uso en MainWindow

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Inicializar API client (opcional)
        self.api_client = None
        self.setup_api_client()

    def setup_api_client(self):
        """Configurar cliente para enviar resultados"""
        try:
            with open('config/api_config.json') as f:
                config = json.load(f)

            if config.get('sync_enabled'):
                self.api_client = RaceAPIClient(
                    api_url=config['api_url'],
                    event_id=config['event_id'],
                    api_key=config.get('api_key'),
                    enabled=True
                )

                # Iniciar en background
                asyncio.create_task(self.api_client.start())

                logger.info("✅ API Client habilitado")
        except FileNotFoundError:
            # Sin config → modo offline
            logger.info("⚠️  Modo offline - sin integración web")
        except Exception as e:
            logger.error(f"❌ Error: {e}")

    def on_tag_detected(self, tag_data):
        """Procesar detección"""
        # 1. Procesar localmente (SIEMPRE)
        event = self.race_manager.process_detection(...)

        # 2. Enviar a web (OPCIONAL, no bloquea)
        if event and self.api_client:
            asyncio.create_task(self.api_client.send_detection(event))
```

---

## 7. Plan de Implementación

### 7.1 Fases de Implementación

#### FASE 0: Preparación (ACTUAL)
**Objetivo**: Documentar y validar arquitectura

- [x] Documentar sistema actual
- [x] Diseñar arquitectura de integración
- [x] Definir contratos API
- [ ] Revisar y aprobar plan

**Duración**: 1 semana
**Entregable**: Este documento

#### FASE 1: Configuración de Integración
**Objetivo**: Permitir conexión entre sistemas

**Tareas**:
1. Crear `config/api_config.json` template
2. Documentar endpoints requeridos de la plataforma
3. Implementar validación de conectividad
4. Crear script de prueba de integración

**Archivos a crear/modificar**:
- `config/api_config_template.json`
- `scripts/test_integration.py`
- `docs/API_REQUIREMENTS.md`

**Duración**: 3 días
**Entregable**: Sistema puede conectarse a backend (sin enviar datos aún)

#### FASE 2: Importación de Participantes
**Objetivo**: Importar atletas desde plataforma

**Tareas**:
1. Adaptar `AthleteImporter` a estructura de API real
2. Mapear campos de la plataforma a modelo Athlete
3. Agregar botón "Importar desde Web" en EventConfigTab
4. Implementar manejo de errores y validaciones
5. Testing con datos reales

**Archivos a modificar**:
- `src/core/athlete_importer.py` (ajustar parsing)
- `src/gui/tabs/event_config_tab.py` (agregar botón)
- `src/gui/widgets/event_config_widget.py` (agregar UI)

**Duración**: 1 semana
**Entregable**: Sistema puede importar atletas desde plataforma

#### FASE 3: Sincronización de Resultados
**Objetivo**: Enviar detecciones y resultados en tiempo real

**Tareas**:
1. Integrar `RaceAPIClient` en `MainWindow`
2. Conectar señales de `RaceManager` con API client
3. Implementar manejo de errores y fallbacks
4. Agregar indicador visual de estado de sincronización
5. Testing con backend real

**Archivos a modificar**:
- `src/gui/main_window.py` (integrar API client)
- `src/core/race_tracking/race_manager.py` (emitir eventos)
- `src/gui/widgets/status_widget.py` (nuevo - mostrar estado)

**Duración**: 1 semana
**Entregable**: Sistema envía detecciones en tiempo real

#### FASE 4: Exportación de Resultados Finales
**Objetivo**: Exportar resultados para importar en plataforma

**Tareas**:
1. Agregar formato JSON completo en `ResultsExporter`
2. Crear endpoint/método para subir resultados finales
3. Agregar botón "Publicar Resultados" en UI
4. Implementar confirmación y validación

**Archivos a modificar**:
- `src/core/race_tracking/results_exporter.py`
- `src/api/client.py` (método `upload_final_results`)
- `src/gui/widgets/race_monitoring_widget.py` (botón)

**Duración**: 3 días
**Entregable**: Resultados finales exportables a plataforma

#### FASE 5: Testing y Documentación
**Objetivo**: Validar integración completa

**Tareas**:
1. Testing end-to-end con datos reales
2. Documentar proceso para organizadores
3. Crear guías de troubleshooting
4. Video tutorial de configuración

**Entregables**:
- Manual de integración para usuarios
- Guía de troubleshooting
- Video tutorial
- Tests automatizados

**Duración**: 1 semana

### 7.2 Cronograma Estimado

```
Semana 1: Fase 0 - Documentación y aprobación
Semana 2: Fase 1 - Configuración de integración
Semanas 3-4: Fase 2 - Importación de participantes
Semanas 5-6: Fase 3 - Sincronización en tiempo real
Semana 7: Fase 4 - Exportación de resultados
Semana 8: Fase 5 - Testing y documentación

TOTAL: 8 semanas
```

### 7.3 Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| Estructura de API de plataforma diferente | Alta | Alto | Diseño adaptable, mapeo configurable |
| Problemas de conectividad en eventos | Media | Alto | Modo offline, cola con retry |
| Pérdida de datos por fallo de red | Baja | Alto | Persistencia local primero, sync después |
| Cambios en backend durante desarrollo | Media | Medio | Versionado de API, contratos claros |

---

## 8. Casos de Uso y Escenarios

### 8.1 Escenario 1: Evento con Integración Completa

**Contexto**: Ultra Trail de 100K con 300 participantes

**Timeline**:

**2 semanas antes:**
- Participantes se registran en plataforma web
- Pagan inscripción online
- Reciben confirmación por email

**1 semana antes:**
- Organizador configura integración:
  ```json
  // config/api_config.json
  {
    "api_url": "https://backend.ultratrail.com",
    "event_id": "ultra-100k-2026",
    "sync_enabled": true
  }
  ```
- Prueba conexión con `python scripts/test_integration.py`
- Importa participantes: Click en "Importar desde Web"
- Sistema carga 300 atletas con toda su información

**Día del evento:**
1. **6:00 AM** - Setup del hardware:
   - Conectar lectores RFID
   - AutoWizard detecta 8 antenas
   - Configurar roles: 2 largada, 4 checkpoints, 2 meta

2. **7:00 AM** - Asignación de chips:
   - Abrir tab "Asignación de Chips"
   - Participantes llegan, muestran dorsal
   - Organizador escanea chip y lo asigna
   - 300 chips asignados en 2 horas

3. **9:00 AM** - Largada:
   - Click "Iniciar Carrera"
   - Antenas 1-2 detectan 300 largadas
   - RaceManager registra tiempos
   - API Client envía a plataforma
   - Familiares ven "Juan Pérez - LARGÓ 09:00:05" en web

4. **Durante la carrera:**
   - Checkpoints 1-4 detectan automáticamente
   - Resultados actualizan en tiempo real
   - Familiares siguen progreso en web
   - Sistema local guarda todo en SQLite (backup)

5. **18:00 PM** - Finalización:
   - Últimos participantes cruzan meta
   - Click "Finalizar Carrera"
   - Exportar PDF con resultados
   - Click "Publicar Resultados Finales"
   - Plataforma genera diplomas automáticamente
   - Emails enviados a todos los participantes

**Resultado**: ✅ Evento exitoso con resultados en tiempo real

### 8.2 Escenario 2: Evento Sin Integración (Standalone)

**Contexto**: Carrera local de 5K con 50 participantes

**Timeline**:

**1 día antes:**
- Organización recibe inscripciones por WhatsApp/Email
- Crea CSV manualmente:
  ```csv
  bib_number,name,gender,birth_date,category_id
  1,Juan Pérez,M,1990-05-15,5k
  2,María González,F,1985-03-20,5k
  ...
  ```
- Importa CSV al sistema de timing

**Día del evento:**
1. Setup hardware (igual que con integración)
2. Asignación de chips (manual)
3. Largada y tracking (automático)
4. Exportar PDF al final
5. Publicar manualmente en redes sociales

**Resultado**: ✅ Sistema funciona perfectamente sin integración

### 8.3 Escenario 3: Fallo de Conectividad

**Contexto**: Ultra Trail en zona rural, internet intermitente

**Comportamiento del Sistema**:

```
09:00 - Largada
        ✅ Detecciones guardadas en SQLite
        ⏳ Intento enviar a plataforma... timeout
        ✅ Sistema continúa funcionando
        📝 Detecciones quedan en cola

09:15 - Internet vuelve
        ✅ API Client reintenta envíos fallidos
        ✅ Sincroniza las 50 detecciones pendientes
        ✅ Todo actualizado

11:30 - Internet cae nuevamente
        ✅ Sistema sigue funcionando localmente
        ⏳ Mensajes en cola

17:00 - Evento termina, internet sigue caído
        ✅ Todos los datos en SQLite
        ✅ Exportar PDF local
        ✅ Entregar resultados físicos

20:00 - Organizador vuelve a zona con internet
        ✅ Abre sistema
        ✅ API Client sincroniza automáticamente
        ✅ Plataforma recibe resultados completos
        ✅ Diplomas generados

**Resultado**: ✅ Sistema resiliente, no se pierden datos

---

## 9. Apéndices Técnicos

### A. Endpoints Requeridos del Backend

**La plataforma de registro debe implementar estos endpoints:**

```
# CATEGORÍAS
GET  /api/events/{event_id}/categories
→ Lista de distancias/categorías del evento

# ATLETAS
GET  /api/events/{event_id}/athletes
→ Lista completa de participantes inscritos

GET  /api/events/{event_id}/athletes/{athlete_id}
→ Detalle de un atleta específico

# DETECCIONES (Tiempo Real)
POST /api/events/{event_id}/detection
→ Registrar detección de chip (largada/checkpoint/meta)

# RESULTADOS (Tiempo Real)
POST /api/events/{event_id}/result
→ Actualizar resultado de un atleta

# RESULTADOS FINALES
POST /api/events/{event_id}/results/final
→ Subir resultados completos al finalizar evento

GET  /api/events/{event_id}/results
→ Obtener resultados (para verificación)

# SINCRONIZACIÓN
GET  /api/events/{event_id}/sync-status
→ Estado de sincronización
```

### B. Estructura de Directorios Completa

```
SportlerZeitPyArbeiten/
├── main.py                      # Entry point
├── requirements.txt             # Dependencias
├── timing_system_config.json    # Config persistente
│
├── config/                      # Configuración
│   ├── __init__.py
│   ├── api_config.json          # Config de integración ← NUEVO
│   ├── api_config_template.json # Template ← NUEVO
│   ├── system_config.py
│   └── exceptions.py
│
├── src/
│   ├── api/                     # Integración Web
│   │   ├── __init__.py
│   │   └── client.py            # RaceAPIClient
│   │
│   ├── core/                    # Lógica de negocio
│   │   ├── __init__.py
│   │   ├── advanced_scanner.py
│   │   ├── tag_parser.py
│   │   ├── tag_processor.py
│   │   ├── athlete_importer.py  # Importador desde web
│   │   ├── csv_importer.py
│   │   └── race_tracking/
│   │       ├── __init__.py
│   │       ├── models.py
│   │       ├── race_manager.py
│   │       └── results_exporter.py
│   │
│   ├── data/                    # Persistencia
│   │   ├── __init__.py
│   │   ├── database.py          # SQLite manager
│   │   ├── models.py            # ORM
│   │   └── export.py
│   │
│   ├── gui/                     # Interfaz gráfica
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── managers/
│   │   │   ├── __init__.py
│   │   │   ├── antenna_manager.py
│   │   │   └── tab_manager.py
│   │   ├── components/
│   │   │   ├── __init__.py
│   │   │   └── scan_thread.py
│   │   ├── tabs/
│   │   │   ├── __init__.py
│   │   │   ├── base_tab.py
│   │   │   ├── detection_tab.py
│   │   │   ├── event_config_tab.py
│   │   │   ├── competition_tab.py
│   │   │   └── configuration_tab.py
│   │   ├── widgets/
│   │   │   ├── __init__.py
│   │   │   ├── chip_assignment_widget.py
│   │   │   ├── race_monitoring_widget.py
│   │   │   └── event_config_widget.py
│   │   └── wizard/
│   │       ├── __init__.py
│   │       └── auto_wizard.py
│   │
│   ├── hardware/                # Interfaz con RFID
│   │   ├── __init__.py
│   │   ├── yr8900_protocol.py
│   │   ├── yr9011_usb_scanner.py
│   │   ├── reader_manager.py
│   │   └── antenna_detection.py
│   │
│   └── utils/                   # Utilidades
│       ├── __init__.py
│       ├── constants.py
│       ├── helpers.py
│       ├── logger.py
│       ├── pdf_exporter.py
│       └── signals.py
│
├── docs/                        # Documentación
│   ├── SISTEMA_COMPLETO_Y_INTEGRACION.md  # Este documento ← NUEVO
│   ├── API_REQUIREMENTS.md      # ← NUEVO (Fase 1)
│   ├── INTEGRATION_GUIDE.md
│   ├── WEB_INTEGRATION_ARCHITECTURE.md
│   ├── Refactoring_guide.md
│   └── ...
│
├── scripts/                     # Scripts utilitarios
│   ├── __init__.py
│   ├── test_integration.py      # ← NUEVO (Fase 1)
│   ├── sync_with_web.py
│   ├── import_csv.py
│   └── setup.py
│
└── test/                        # Tests
    ├── test_multiantena.py
    ├── test_race_manager.py
    └── test_api_client.py       # ← NUEVO (Fase 3)
```

### C. Checklist de Integración para Organizadores

```markdown
# Checklist de Integración - Sistema de Timing con Plataforma

## Antes del Evento (1-2 semanas)

### Configuración Técnica
- [ ] Obtener credenciales de API de la plataforma
  - [ ] URL del backend
  - [ ] API Key
  - [ ] Event ID
- [ ] Crear `config/api_config.json`
- [ ] Ejecutar `python scripts/test_integration.py`
- [ ] Verificar que la conexión es exitosa

### Importación de Datos
- [ ] Importar categorías desde plataforma
- [ ] Importar atletas inscritos
- [ ] Verificar que todos los datos están correctos
- [ ] Revisar campos mapeados (email, teléfono, etc.)

## Día del Evento

### Setup Hardware (6:00 - 8:00 AM)
- [ ] Conectar lectores RFID
- [ ] Ejecutar AutoWizard
- [ ] Verificar que todas las antenas están detectadas
- [ ] Asignar roles a antenas
- [ ] Probar detección de chips de prueba

### Asignación de Chips (7:00 - 9:00 AM)
- [ ] Abrir tab "Asignación de Chips"
- [ ] Asignar chips a cada participante
- [ ] Verificar que no hay chips duplicados
- [ ] Confirmar que todos tienen chip asignado

### Largada (9:00 AM)
- [ ] Verificar internet funcional (opcional, no crítico)
- [ ] Click "Iniciar Carrera"
- [ ] Verificar que detecciones se registran
- [ ] (Si web) Verificar que aparecen en plataforma

### Durante la Carrera
- [ ] Monitorear detecciones en tiempo real
- [ ] Verificar que splits se registran
- [ ] Revisar estado de sincronización (si aplica)
- [ ] Backup manual cada 1 hora (opcional)

### Finalización
- [ ] Click "Finalizar Carrera"
- [ ] Exportar PDF con resultados
- [ ] Verificar clasificaciones
- [ ] (Si web) Click "Publicar Resultados Finales"
- [ ] Verificar que diplomas se generaron (si aplica)

## Después del Evento

- [ ] Backup de SQLite local
- [ ] Verificar que todos los resultados están en plataforma
- [ ] Entregar PDFs a organización
- [ ] Archivar datos del evento
```

### D. Glosario de Términos

| Término | Definición |
|---------|------------|
| **Chip / Tag** | Chip RFID pasivo que lleva el atleta |
| **EPC** | Electronic Product Code - Identificador único del chip |
| **Dorsal / Bib** | Número visible que lleva el atleta |
| **Largada / Start** | Punto de inicio de la carrera |
| **Meta / Finish** | Punto final de la carrera |
| **Checkpoint** | Punto intermedio de control |
| **Split** | Tiempo parcial entre dos puntos |
| **Vuelta / Lap** | Una vuelta completa en carrera circular |
| **DNF** | Did Not Finish - No completó la carrera |
| **DNS** | Did Not Start - No largó |
| **DSQ** | Disqualified - Descalificado |
| **Return Loss** | Medida de calidad de conexión de antena |
| **Grace Period** | Período de gracia para evitar re-detecciones |
| **Award Category** | Categoría de premiación (género/edad) |

---

## 📞 Contacto y Soporte

Para consultas sobre integración:
- **Documentación técnica**: Ver `docs/` en repositorio
- **Estructura de API**: `docs/API_REQUIREMENTS.md` (próximamente)
- **Issues y bugs**: GitHub Issues

---

**Fin del Documento**

*Versión 2.0 - 2026-03-03*
