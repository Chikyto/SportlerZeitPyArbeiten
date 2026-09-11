# Requisitos de API para Integración

**Versión**: 1.0
**Fecha**: 2026-03-03

---

## 📋 Resumen

Este documento especifica los endpoints y formatos de datos que debe implementar la **Plataforma de Registro** para integrarse con el **Sistema de Timing RFID**.

### Principio de Independencia

```
┌─────────────────────────────────────────────────────────────┐
│  La integración es OPCIONAL                                  │
│  Ambos sistemas deben funcionar de forma independiente      │
│                                                              │
│  ✅ Sistema de Timing sin Plataforma → Funciona (CSV manual)│
│  ✅ Plataforma sin Sistema de Timing → Funciona (sin chips) │
│  ✅ Ambos integrados → Funciona (mejor experiencia)         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Autenticación

### API Key

Todos los requests deben incluir autenticación vía header:

```http
Authorization: Bearer {API_KEY}
```

### Generación de API Key

La plataforma debe proporcionar:
1. **API Key** única por evento u organización
2. **Documentación** de cómo obtenerla
3. **Revocación** y regeneración de keys

---

## 📥 Endpoints de Importación (Sistema de Timing → Plataforma)

### 1. GET /api/events/{event_id}/categories

**Propósito**: Obtener lista de distancias/categorías del evento

**Request**:
```http
GET /api/events/ultra-2026/categories HTTP/1.1
Host: api.example.com
Authorization: Bearer your-api-key
```

**Response exitosa** (200 OK):
```json
{
  "success": true,
  "event_id": "ultra-2026",
  "event_name": "Ultra Trail 2026",
  "event_date": "2026-03-15",
  "categories": [
    {
      "category_id": "5k",
      "name": "5 Kilómetros",
      "distance_km": 5.0,
      "expected_checkpoints": 0,
      "mode": "linear",
      "scheduled_start": "2026-03-15T09:00:00Z",
      "description": "Carrera de 5K por la ciudad"
    },
    {
      "category_id": "10k",
      "name": "10 Kilómetros",
      "distance_km": 10.0,
      "expected_checkpoints": 1,
      "mode": "linear",
      "scheduled_start": "2026-03-15T09:30:00Z",
      "description": "Carrera de 10K con 1 checkpoint"
    },
    {
      "category_id": "100k",
      "name": "Ultra 100K",
      "distance_km": 100.0,
      "expected_checkpoints": 6,
      "mode": "linear",
      "scheduled_start": "2026-03-15T06:00:00Z",
      "description": "Ultra trail de 100km con 6 checkpoints"
    }
  ]
}
```

**Campos requeridos**:
- `category_id` (string): Identificador único de la categoría
- `name` (string): Nombre descriptivo
- `distance_km` (number): Distancia en kilómetros

**Campos opcionales**:
- `expected_checkpoints` (int): Cantidad de checkpoints (default: 0)
- `mode` (string): "linear", "laps", "time_based" (default: "linear")
- `scheduled_start` (ISO 8601): Hora programada de largada
- `max_laps` (int): Para modo "laps"
- `max_time_hours` (int): Para modo "time_based"

**Response de error** (404 Not Found):
```json
{
  "success": false,
  "error": "Event not found",
  "error_code": "EVENT_NOT_FOUND"
}
```

---

### 2. GET /api/events/{event_id}/athletes

**Propósito**: Obtener lista completa de participantes inscritos

**Request**:
```http
GET /api/events/ultra-2026/athletes HTTP/1.1
Host: api.example.com
Authorization: Bearer your-api-key
```

**Query parameters opcionales**:
- `category_id`: Filtrar por categoría (ej: `?category_id=5k`)
- `status`: Filtrar por estado (ej: `?status=confirmed`)
- `limit`: Limitar resultados (ej: `?limit=100`)
- `offset`: Paginación (ej: `?offset=100`)

**Response exitosa** (200 OK):
```json
{
  "success": true,
  "event_id": "ultra-2026",
  "total_athletes": 350,
  "returned": 350,
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
      "dietary_restrictions": "Vegetariano",
      "registration_date": "2026-01-15T10:30:00Z",
      "registration_number": "REG-2026-0101"
    },
    ...
  ]
}
```

**Campos requeridos del atleta**:
- `athlete_id` (string): ID único en la plataforma
- `bib_number` (int): Número de dorsal
- `full_name` (string): Nombre completo (o first_name + last_name)
- `category_id` (string): Categoría inscrita

**Campos opcionales pero recomendados**:
- `first_name`, `last_name` (string): Nombre y apellido separados
- `email` (string): Email de contacto
- `phone` (string): Teléfono (formato internacional recomendado)
- `birth_date` (YYYY-MM-DD): Fecha de nacimiento (para categorías por edad)
- `gender` (string): "M", "F", "Other"
- `team_name` (string): Equipo o club
- `emergency_contact_name` (string): Contacto de emergencia
- `emergency_contact_phone` (string): Teléfono de emergencia
- `payment_status` (string): "confirmed", "pending", "failed"
- `medical_notes` (string): Notas médicas importantes
- `registration_date` (ISO 8601): Fecha de inscripción

**Mapeo en Sistema de Timing**:
```python
Athlete(
    athlete_id=data['athlete_id'],
    bib_number=data['bib_number'],
    name=data.get('full_name') or f"{data['first_name']} {data['last_name']}",
    distance_id=data['category_id'],
    gender=data.get('gender'),
    birth_date=parse_date(data.get('birth_date')),
    team=data.get('team_name'),
    notes=build_notes(data)  # Combina email, teléfono, emergencia, etc.
)
```

---

### 3. GET /api/events/{event_id}/athletes/{athlete_id}

**Propósito**: Obtener detalles de un atleta específico (opcional, para verificaciones)

**Request**:
```http
GET /api/events/ultra-2026/athletes/uuid-abc-123 HTTP/1.1
Host: api.example.com
Authorization: Bearer your-api-key
```

**Response exitosa** (200 OK):
```json
{
  "success": true,
  "athlete": {
    // Mismo formato que en el listado
    "athlete_id": "uuid-abc-123",
    "bib_number": 101,
    ...
  }
}
```

---

## 📤 Endpoints de Exportación (Plataforma → Sistema de Timing)

### 4. POST /api/events/{event_id}/detection

**Propósito**: Registrar detección de chip RFID en tiempo real

**Request**:
```http
POST /api/events/ultra-2026/detection HTTP/1.1
Host: api.example.com
Authorization: Bearer your-api-key
Content-Type: application/json

{
  "tag_id": "7662",
  "athlete_id": "uuid-abc-123",
  "bib_number": 101,
  "timestamp": "2026-03-15T14:30:25.123Z",
  "antenna_port": 2,
  "event_type": "start",
  "category_id": "5k",
  "checkpoint_number": null,
  "athlete_name": "Juan Pérez"
}
```

**Campos**:
- `tag_id` (string): ID del chip RFID detectado
- `athlete_id` (string): ID del atleta (si se identificó)
- `bib_number` (int): Dorsal (si se identificó)
- `timestamp` (ISO 8601): Momento exacto de detección
- `antenna_port` (int): Puerto de antena (1-8)
- `event_type` (string): "start", "checkpoint", "finish", "lap"
- `category_id` (string): Categoría del atleta
- `checkpoint_number` (int|null): Número de checkpoint (si aplica)
- `athlete_name` (string): Nombre del atleta (para display)

**Response exitosa** (200 OK):
```json
{
  "success": true,
  "detection_id": "det-xyz-789",
  "timestamp_received": "2026-03-15T14:30:25.456Z"
}
```

**Response de error** (400 Bad Request):
```json
{
  "success": false,
  "error": "Invalid athlete_id",
  "error_code": "ATHLETE_NOT_FOUND"
}
```

**Frecuencia**: Hasta 100 detecciones/minuto en evento grande

---

### 5. POST /api/events/{event_id}/result

**Propósito**: Actualizar resultado completo de un atleta

**Request**:
```http
POST /api/events/ultra-2026/result HTTP/1.1
Host: api.example.com
Authorization: Bearer your-api-key
Content-Type: application/json

{
  "athlete_id": "uuid-abc-123",
  "bib_number": 101,
  "category_id": "5k",
  "status": "finished",
  "start_time": "2026-03-15T09:00:05.123Z",
  "finish_time": "2026-03-15T09:25:20.456Z",
  "total_seconds": 1515.333,
  "position_overall": 1,
  "position_gender": 1,
  "position_category": 1,
  "checkpoint_times": {
    "1": "2026-03-15T09:12:30.789Z"
  },
  "splits_seconds": {
    "1": 745.666,
    "2": 769.667
  },
  "laps_completed": 0
}
```

**Campos**:
- `athlete_id` (string): ID del atleta
- `bib_number` (int): Dorsal
- `category_id` (string): Categoría
- `status` (string): "not_started", "running", "finished", "dnf", "dns", "dsq"
- `start_time` (ISO 8601|null): Momento de largada
- `finish_time` (ISO 8601|null): Momento de llegada
- `total_seconds` (number|null): Tiempo total en segundos
- `position_overall` (int|null): Posición general
- `position_gender` (int|null): Posición en su género
- `position_category` (int|null): Posición en categoría de edad
- `checkpoint_times` (object): `{checkpoint_num: timestamp}`
- `splits_seconds` (object): `{checkpoint_num: seconds}`
- `laps_completed` (int): Número de vueltas (para carreras por vueltas)

**Response exitosa** (200 OK):
```json
{
  "success": true,
  "result_id": "res-xyz-789",
  "public_url": "https://results.example.com/ultra-2026/athlete/uuid-abc-123"
}
```

**Frecuencia**: 1-2 actualizaciones por atleta por checkpoint

---

### 6. POST /api/events/{event_id}/results/final

**Propósito**: Subir resultados completos al finalizar el evento

**Request**:
```http
POST /api/events/ultra-2026/results/final HTTP/1.1
Host: api.example.com
Authorization: Bearer your-api-key
Content-Type: application/json

{
  "event_id": "ultra-2026",
  "category_id": "5k",
  "event_status": "finished",
  "finish_timestamp": "2026-03-15T10:30:00Z",
  "total_participants": 150,
  "results": [
    {
      "position": 1,
      "athlete_id": "uuid-abc-123",
      "bib_number": 101,
      "name": "Juan Pérez",
      "gender": "M",
      "category_age": "M20-34",
      "team": "Club Runners",
      "status": "finished",
      "start_time": "2026-03-15T09:00:05.123Z",
      "finish_time": "2026-03-15T09:25:20.456Z",
      "total_time": "00:25:15.333",
      "total_seconds": 1515.333,
      "pace_per_km": "00:05:03",
      "position_gender": 1,
      "position_category": 1,
      "checkpoint_times": {...},
      "splits": {...}
    },
    ...
  ]
}
```

**Response exitosa** (200 OK):
```json
{
  "success": true,
  "results_imported": 150,
  "results_url": "https://results.example.com/ultra-2026/5k",
  "diplomas_generated": true,
  "emails_sent": 150
}
```

**Nota**: Este endpoint se llama típicamente una sola vez al finalizar el evento

---

### 7. GET /api/events/{event_id}/results

**Propósito**: Obtener resultados actuales (para verificación desde sistema de timing)

**Request**:
```http
GET /api/events/ultra-2026/results?category_id=5k HTTP/1.1
Host: api.example.com
Authorization: Bearer your-api-key
```

**Query parameters**:
- `category_id`: Filtrar por categoría
- `status`: Filtrar por estado ("finished", "running", "all")
- `limit`: Limitar resultados

**Response exitosa** (200 OK):
```json
{
  "success": true,
  "event_id": "ultra-2026",
  "category_id": "5k",
  "total_results": 150,
  "last_updated": "2026-03-15T09:25:30Z",
  "results": [
    // Mismo formato que results/final
  ]
}
```

---

### 8. GET /api/events/{event_id}/sync-status

**Propósito**: Verificar estado de sincronización (opcional)

**Request**:
```http
GET /api/events/ultra-2026/sync-status HTTP/1.1
Host: api.example.com
Authorization: Bearer your-api-key
```

**Response exitosa** (200 OK):
```json
{
  "success": true,
  "event_id": "ultra-2026",
  "last_detection_received": "2026-03-15T09:25:30.123Z",
  "total_detections": 456,
  "total_results": 150,
  "categories_status": {
    "5k": {
      "participants": 150,
      "detections": 300,
      "finished": 145,
      "running": 5
    }
  }
}
```

---

## 🔄 Alternativa: Exportación CSV

Si la implementación de API es compleja, se puede usar CSV como alternativa:

### Export desde Plataforma

**Archivo**: `participants.csv`
```csv
athlete_id,bib_number,full_name,email,phone,birth_date,gender,category_id,team_name,emergency_contact,payment_status
uuid-abc-123,101,Juan Pérez,juan@example.com,+5491112345678,1990-05-15,M,5k,Club Runners,"María Pérez +5491187654321",confirmed
```

### Import a Plataforma

**Archivo**: `results_5k.csv`
```csv
position,athlete_id,bib_number,name,gender,category,team,status,start_time,finish_time,total_time,total_seconds,pace_per_km,checkpoints
1,uuid-abc-123,101,Juan Pérez,M,M20-34,Club Runners,finished,2026-03-15T09:00:05,2026-03-15T09:25:20,00:25:15,1515.333,00:05:03,2
```

---

## 🧪 Testing de Integración

### 1. Herramienta de Testing

```bash
# Script incluido en sistema de timing
python scripts/test_integration.py
```

**Verifica**:
- ✅ Conectividad a API
- ✅ Autenticación válida
- ✅ Endpoints disponibles
- ✅ Formato de respuestas
- ✅ Mapeo de campos

### 2. Datos de Prueba

La plataforma debe proporcionar:
- **Event ID de testing**: Ej: `test-event-2026`
- **API Key de testing**: Con permisos completos
- **Datos de muestra**: 10-20 atletas ficticios

### 3. Postman Collection

Proveer colección de Postman con:
- Todos los endpoints
- Ejemplos de requests
- Ejemplos de responses
- Variables de entorno

---

## 📊 Consideraciones de Performance

### Latencia Aceptable
- **Importación inicial**: < 5 segundos para 500 atletas
- **Detección individual**: < 500ms
- **Resultado individual**: < 1 segundo

### Rate Limiting
- **Recomendado**: 100 requests/minuto mínimo
- **Burst**: Hasta 500 detecciones en 1 minuto (largadas masivas)

### Manejo de Errores
- **Sistema de timing**: Continúa funcionando si API falla
- **Reintento**: Exponential backoff (2s, 4s, 8s)
- **Queue local**: Almacena mensajes fallidos para reenvío

---

## 🔒 Seguridad

### HTTPS Obligatorio
- Todos los endpoints deben usar HTTPS
- Certificado válido requerido

### API Key
- Longitud mínima: 32 caracteres
- Rotación: Permitir regenerar sin afectar evento en curso

### CORS
- Habilitar CORS si hay frontend web
- Whitelist de dominios recomendado

---

## 📝 Documentación Requerida

La plataforma debe proporcionar:

1. **Swagger / OpenAPI**:
   - Especificación completa de API
   - Ejemplos interactivos

2. **Guía de Inicio Rápido**:
   - Cómo obtener API Key
   - Primer request de prueba
   - Troubleshooting común

3. **Changelog de API**:
   - Versionado semántico
   - Cambios backward-compatible
   - Deprecations con aviso previo

4. **Soporte**:
   - Email de contacto técnico
   - Tiempo de respuesta esperado
   - Horario de soporte el día del evento

---

## ✅ Checklist de Implementación

### Mínimo Viable (MVP)
- [ ] GET `/api/events/{event_id}/categories`
- [ ] GET `/api/events/{event_id}/athletes`
- [ ] POST `/api/events/{event_id}/detection`
- [ ] POST `/api/events/{event_id}/result`
- [ ] Autenticación con API Key
- [ ] HTTPS

### Recomendado
- [ ] POST `/api/events/{event_id}/results/final`
- [ ] GET `/api/events/{event_id}/results`
- [ ] GET `/api/events/{event_id}/sync-status`
- [ ] Rate limiting adecuado
- [ ] Documentación Swagger

### Opcional
- [ ] WebSocket para updates en tiempo real
- [ ] Webhook para eventos importantes
- [ ] Dashboard de monitoreo

---

## 🤝 Coordinación entre Equipos

### Reunión Inicial
- Revisar este documento
- Aclarar dudas técnicas
- Definir timelines

### Testing Conjunto
- Ambiente de staging
- Evento de prueba
- Validación end-to-end

### Día del Evento
- Contacto técnico disponible
- Monitoreo de ambos sistemas
- Plan de contingencia definido

---

**Documento de Requisitos de API v1.0**
*Para consultas: Incluir contacto técnico*
