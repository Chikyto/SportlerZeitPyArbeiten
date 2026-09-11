# Arquitectura de Integración Web - Sistema RFID Athletics Timer

## 📋 Tabla de Contenidos
1. [Visión General](#visión-general)
2. [Componentes del Sistema](#componentes-del-sistema)
3. [Flujo de Datos](#flujo-de-datos)
4. [Opciones de Arquitectura](#opciones-de-arquitectura)
5. [API REST para Resultados en Vivo](#api-rest-para-resultados-en-vivo)
6. [Pre-Registro Web](#pre-registro-web)
7. [Visualización en Vivo](#visualización-en-vivo)
8. [Implementación por Fases](#implementación-por-fases)

---

## 🎯 Visión General

### Objetivos
- **Pre-registro online**: Permitir que corredores se registren antes del evento desde una web
- **Sincronización**: Importar registros al sistema de timing local
- **Resultados en vivo**: Publicar tiempos en tiempo real durante la carrera
- **Clasificaciones online**: Mostrar rankings actualizados automáticamente

### Casos de Uso
```
Usuario Web → Pre-registro → Base de Datos → Importación → Sistema Local
Sistema Local → Detecciones → Procesamiento → API → Web en Vivo → Espectadores
```

---

## 🏗️ Componentes del Sistema

### 1. Sistema Actual (Desktop - PyQt6)
```
[RFID Scanner] → [Python App] → [RaceManager]
                      ↓
                 [SQLite Local]
```

### 2. Componentes Nuevos a Agregar

#### A. Base de Datos Central (Cloud/Local Server)
- **PostgreSQL** o **MySQL**: Para producción robusta
- **SQLite Compartido**: Para eventos pequeños
- **Firebase/Supabase**: Para cloud managed

#### B. API Backend (REST/WebSocket)
- **FastAPI** (Python): Se integra fácilmente con tu código actual
- **Flask** (Python): Más simple, menos features
- **Node.js + Express**: Si prefieres JavaScript

#### C. Frontend Web (Público)
- **React/Vue/Svelte**: Para página de pre-registro
- **WebSockets**: Para actualizaciones en tiempo real
- **Tailwind CSS**: Para diseño responsive

---

## 🔄 Flujo de Datos Completo

### Fase 1: Pre-Registro (Antes del Evento)

```
┌─────────────────────────────────────────────────────────┐
│                    INTERNET                              │
│  ┌──────────────┐         ┌─────────────────────┐      │
│  │  Corredor    │────────>│  Sitio Web          │      │
│  │              │         │  (Pre-registro)     │      │
│  └──────────────┘         └──────────┬──────────┘      │
│                                       │                  │
│                            ┌──────────▼──────────┐      │
│                            │  Base de Datos      │      │
│                            │  Central (Cloud)    │      │
│                            └──────────┬──────────┘      │
└────────────────────────────────────────┼────────────────┘
                                         │
                           ┌─────────────▼─────────────┐
                           │  IMPORTACIÓN              │
                           │  (CSV / API / Sync)       │
                           └─────────────┬─────────────┘
                                         │
                        ┌────────────────▼────────────────┐
                        │   Sistema Local (Desktop App)   │
                        │   EventConfigWidget             │
                        │   ↓                              │
                        │   RaceManager                    │
                        └─────────────────────────────────┘
```

**Datos a Sincronizar:**
```python
{
    "chip_id": "7662",
    "bib_number": 125,
    "name": "Juan Pérez",
    "category": "100k",
    "email": "juan@example.com",
    "phone": "+54911234567",
    "emergency_contact": "María Pérez - +5491177777",
    "team": "Club Runners",
    "payment_status": "confirmed",
    "registration_date": "2025-01-15T10:30:00Z"
}
```

### Fase 2: Durante la Carrera (Tiempo Real)

```
┌─────────────────────────────────────────────────────────┐
│                  SISTEMA LOCAL                           │
│  ┌──────────┐    ┌──────────────┐   ┌──────────────┐  │
│  │  Scanner │───>│ RaceManager  │──>│ SQLite Local │  │
│  └──────────┘    └──────┬───────┘   └──────────────┘  │
│                          │                              │
│                          │ Cada detección               │
│                          ▼                              │
│                  ┌───────────────┐                      │
│                  │  API Client   │                      │
│                  │  (Async POST) │                      │
│                  └───────┬───────┘                      │
└──────────────────────────┼──────────────────────────────┘
                           │ HTTP/WebSocket
┌──────────────────────────▼──────────────────────────────┐
│                    SERVIDOR WEB                          │
│  ┌─────────────────────────────────────────────┐        │
│  │  API Backend (FastAPI/Flask)                │        │
│  │  POST /api/events/detection                 │        │
│  │  GET  /api/events/{id}/results              │        │
│  │  WS   /api/events/{id}/live                 │        │
│  └──────────────────┬──────────────────────────┘        │
│                     │                                    │
│  ┌──────────────────▼──────────────────────────┐        │
│  │  Base de Datos (PostgreSQL/MySQL)           │        │
│  │  - events, categories, athletes             │        │
│  │  - detections, results, rankings            │        │
│  └──────────────────┬──────────────────────────┘        │
└─────────────────────┼───────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────┐
│                  CLIENTE WEB (Público)                   │
│  ┌────────────────────────────────────────────┐         │
│  │  React/Vue App                             │         │
│  │  - Tabla de resultados en vivo             │         │
│  │  - Filtros por categoría                   │         │
│  │  - Búsqueda por nombre/dorsal              │         │
│  │  - Notificaciones de llegadas              │         │
│  │  - Gráficos de progreso                    │         │
│  └────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

---

## 🏛️ Opciones de Arquitectura

### Opción 1: **Cloud-First** (Recomendado para eventos grandes)

**Stack Tecnológico:**
- **Backend**: FastAPI (Python) en Railway/Render/Heroku
- **Base de Datos**: PostgreSQL (Supabase/Railway)
- **Frontend**: React + Vercel/Netlify
- **Real-time**: WebSockets (FastAPI native)
- **Costo**: ~$20-50/mes

**Ventajas:**
✅ Escalable a miles de espectadores
✅ No requiere configuración de red local
✅ Accesible desde cualquier lugar
✅ Backups automáticos
✅ SSL/HTTPS incluido

**Desventajas:**
❌ Requiere internet estable en el sitio de la carrera
❌ Latencia de red (300-800ms)
❌ Costo mensual

---

### Opción 2: **Local-First con Sincronización** (Recomendado para confiabilidad)

**Stack Tecnológico:**
- **Backend Local**: FastAPI corriendo en la misma PC del timing
- **Base de Datos**: SQLite local + PostgreSQL cloud (replica)
- **Frontend**: React servido localmente + copia en cloud
- **Sincronización**: Script Python que pushea a cloud cada 5-10 segundos

**Ventajas:**
✅ Funciona sin internet (modo offline)
✅ Latencia mínima (< 50ms)
✅ No depende de proveedores externos
✅ Gratis o muy barato

**Desventajas:**
❌ Requiere configuración de red local (WiFi/Router)
❌ Espectadores deben estar en la misma red o VPN
❌ Más complejo de configurar

---

### Opción 3: **Híbrido** (Lo mejor de ambos mundos)

**Flujo:**
```
Sistema Local → SQLite Local (timing primario)
     ↓
Async Worker → Pushea a Cloud cada X segundos
     ↓
Cloud DB → Sirve resultados a internet
     ↓
Espectadores → Ven resultados con pequeño delay (5-15s)
```

**Ventajas:**
✅ Timing local confiable (no depende de internet)
✅ Resultados online para espectadores
✅ Fallback: si internet falla, timing sigue funcionando
✅ Sincronización post-evento si hay problemas

**Desventajas:**
❌ Más complejo de implementar
❌ Requiere manejo de conflictos de sincronización

---

## 🚀 API REST para Resultados en Vivo

### Diseño de API (FastAPI)

```python
# src/api/main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List, Optional
import asyncio

app = FastAPI(title="RFID Athletics Timer API")

# CORS para permitir acceso desde navegadores
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================================================
# MODELOS
# ========================================================================

class DetectionEvent(BaseModel):
    tag_id: str
    timestamp: datetime
    antenna_port: int
    event_type: str  # "start", "checkpoint", "finish"
    checkpoint_number: Optional[int]
    category_id: str

class AthleteResult(BaseModel):
    athlete_id: str
    tag_id: str
    bib_number: int
    name: str
    category_id: str
    status: str  # "not_started", "running", "finished"
    start_time: Optional[datetime]
    finish_time: Optional[datetime]
    total_time: Optional[float]  # en segundos
    position: Optional[int]
    checkpoint_times: dict

# ========================================================================
# ENDPOINTS - PRE-REGISTRO
# ========================================================================

@app.post("/api/athletes/register")
async def register_athlete(athlete: dict):
    """
    Pre-registrar un atleta desde la web
    """
    # Guardar en base de datos
    # Retornar confirmación con QR code para imprimir
    return {
        "success": True,
        "athlete_id": "...",
        "qr_code_url": "https://..."
    }

@app.get("/api/athletes/export")
async def export_athletes(category_id: Optional[str] = None):
    """
    Exportar atletas registrados para importar al sistema local
    Formato: CSV o JSON
    """
    # Consultar DB y retornar lista
    return {
        "athletes": [...]
    }

# ========================================================================
# ENDPOINTS - RESULTADOS EN VIVO
# ========================================================================

@app.post("/api/events/{event_id}/detection")
async def record_detection(event_id: str, detection: DetectionEvent):
    """
    Recibir detección desde el sistema local
    """
    # Guardar en DB
    # Actualizar cache de resultados
    # Notificar a WebSocket clients
    await broadcast_detection(event_id, detection)

    return {"success": True}

@app.get("/api/events/{event_id}/results")
async def get_results(
    event_id: str,
    category_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
) -> List[AthleteResult]:
    """
    Obtener resultados actuales

    Parámetros:
    - category_id: Filtrar por categoría
    - status: "running", "finished", "all"
    - limit: Máximo de resultados
    """
    # Consultar DB y retornar
    return [...]

@app.get("/api/events/{event_id}/leaderboard/{category_id}")
async def get_leaderboard(event_id: str, category_id: str):
    """
    Obtener tabla de posiciones ordenada
    """
    # Top 50 o todos, ordenados por tiempo
    return {
        "category": {...},
        "updated_at": datetime.now(),
        "results": [
            {
                "position": 1,
                "bib_number": 125,
                "name": "Juan Pérez",
                "total_time": "2:45:32",
                "status": "finished"
            },
            ...
        ]
    }

# ========================================================================
# WEBSOCKETS - TIEMPO REAL
# ========================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Cliente desconectado
                pass

manager = ConnectionManager()

@app.websocket("/ws/events/{event_id}/live")
async def websocket_live_results(websocket: WebSocket, event_id: str):
    """
    WebSocket para recibir actualizaciones en tiempo real

    Cliente recibe mensajes tipo:
    {
        "type": "detection",
        "data": {...}
    }
    {
        "type": "finish",
        "data": {...}
    }
    """
    await manager.connect(websocket)
    try:
        while True:
            # Mantener conexión abierta
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def broadcast_detection(event_id: str, detection: DetectionEvent):
    """Enviar detección a todos los clientes conectados"""
    await manager.broadcast({
        "type": "detection",
        "event_id": event_id,
        "data": detection.dict()
    })

# ========================================================================
# ESTADÍSTICAS
# ========================================================================

@app.get("/api/events/{event_id}/stats")
async def get_event_stats(event_id: str):
    """
    Estadísticas generales del evento
    """
    return {
        "total_participants": 250,
        "currently_running": 180,
        "finished": 45,
        "not_started": 25,
        "categories": [
            {
                "id": "100k",
                "name": "Ultra 100K",
                "running": 50,
                "finished": 10
            },
            ...
        ],
        "latest_finishers": [
            # Últimos 10 que terminaron
        ]
    }
```

---

## 🌐 Pre-Registro Web

### Formulario de Registro (React)

```jsx
// src/components/RegistrationForm.jsx
import React, { useState } from 'react';
import axios from 'axios';

function RegistrationForm() {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    category: '100k',
    team: '',
    emergencyContact: '',
    emergencyPhone: ''
  });

  const [chipId, setChipId] = useState('');
  const [qrCode, setQrCode] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post('/api/athletes/register', formData);

      // Mostrar confirmación con QR
      setChipId(response.data.chip_id);
      setQrCode(response.data.qr_code_url);

      // Enviar email de confirmación
      alert('¡Registro exitoso! Revisa tu email para más detalles.');
    } catch (error) {
      alert('Error en el registro. Por favor intenta nuevamente.');
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <h2 className="text-3xl font-bold mb-6">Registro - Ultra Trail 2025</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="Nombre"
            value={formData.firstName}
            onChange={(e) => setFormData({...formData, firstName: e.target.value})}
            className="px-4 py-2 border rounded"
            required
          />

          <input
            type="text"
            placeholder="Apellido"
            value={formData.lastName}
            onChange={(e) => setFormData({...formData, lastName: e.target.value})}
            className="px-4 py-2 border rounded"
            required
          />
        </div>

        <input
          type="email"
          placeholder="Email"
          value={formData.email}
          onChange={(e) => setFormData({...formData, email: e.target.value})}
          className="w-full px-4 py-2 border rounded"
          required
        />

        <select
          value={formData.category}
          onChange={(e) => setFormData({...formData, category: e.target.value})}
          className="w-full px-4 py-2 border rounded"
        >
          <option value="100k">Ultra 100K - $150</option>
          <option value="50k">Trail 50K - $100</option>
          <option value="30k">Mountain 30K - $75</option>
          <option value="21k">Half Marathon - $50</option>
        </select>

        {/* Más campos... */}

        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-3 rounded-lg font-bold hover:bg-blue-700"
        >
          Registrarse y Pagar
        </button>
      </form>

      {/* Mostrar QR después del registro */}
      {qrCode && (
        <div className="mt-6 p-4 bg-green-50 rounded">
          <h3 className="font-bold mb-2">¡Registro Exitoso!</h3>
          <p>Tu Chip ID: <strong>{chipId}</strong></p>
          <img src={qrCode} alt="QR Code" className="mt-4 w-48 h-48" />
          <p className="text-sm text-gray-600 mt-2">
            Imprime este QR o guárdalo en tu teléfono para el día del evento
          </p>
        </div>
      )}
    </div>
  );
}
```

---

## 📊 Visualización en Vivo

### Página de Resultados en Tiempo Real (React)

```jsx
// src/components/LiveResults.jsx
import React, { useState, useEffect } from 'react';

function LiveResults({ eventId }) {
  const [results, setResults] = useState([]);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // WebSocket para actualizaciones en tiempo real
  useEffect(() => {
    const ws = new WebSocket(`wss://api.example.com/ws/events/${eventId}/live`);

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (message.type === 'detection') {
        // Actualizar resultados con nueva detección
        updateResults(message.data);
      } else if (message.type === 'finish') {
        // Mostrar notificación de llegada
        showFinishNotification(message.data);
      }
    };

    // Cargar resultados iniciales
    fetchResults();

    return () => ws.close();
  }, [eventId]);

  const fetchResults = async () => {
    const response = await fetch(`/api/events/${eventId}/results`);
    const data = await response.json();
    setResults(data);
  };

  const updateResults = (detection) => {
    // Actualizar estado local sin recargar toda la página
    setResults(prevResults => {
      // Lógica de actualización incremental
    });
  };

  const filteredResults = results.filter(r => {
    // Filtrar por categoría y búsqueda
    if (filter !== 'all' && r.category_id !== filter) return false;
    if (searchTerm && !r.name.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-4xl font-bold mb-8">Resultados en Vivo</h1>

      {/* Filtros */}
      <div className="flex gap-4 mb-6">
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="px-4 py-2 border rounded"
        >
          <option value="all">Todas las categorías</option>
          <option value="100k">Ultra 100K</option>
          <option value="50k">Trail 50K</option>
          <option value="30k">Mountain 30K</option>
          <option value="21k">Half Marathon</option>
        </select>

        <input
          type="text"
          placeholder="Buscar por nombre..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-4 py-2 border rounded"
        />
      </div>

      {/* Tabla de Resultados */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-4 py-3 text-left">Pos</th>
              <th className="px-4 py-3 text-left">Dorsal</th>
              <th className="px-4 py-3 text-left">Nombre</th>
              <th className="px-4 py-3 text-left">Categoría</th>
              <th className="px-4 py-3 text-left">Estado</th>
              <th className="px-4 py-3 text-left">Tiempo</th>
              <th className="px-4 py-3 text-left">Checkpoints</th>
            </tr>
          </thead>
          <tbody>
            {filteredResults.map((result, idx) => (
              <tr
                key={result.athlete_id}
                className={`border-b ${
                  result.status === 'running' ? 'bg-yellow-50' :
                  result.status === 'finished' ? 'bg-green-50' : ''
                }`}
              >
                <td className="px-4 py-3 font-bold">{result.position || '-'}</td>
                <td className="px-4 py-3">{result.bib_number}</td>
                <td className="px-4 py-3 font-semibold">{result.name}</td>
                <td className="px-4 py-3">{result.category_id.toUpperCase()}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded text-sm ${
                    result.status === 'running' ? 'bg-yellow-200' :
                    result.status === 'finished' ? 'bg-green-200' :
                    'bg-gray-200'
                  }`}>
                    {result.status === 'running' ? '🏃 En Carrera' :
                     result.status === 'finished' ? '🏁 Finalizado' :
                     '⏳ No Iniciado'}
                  </span>
                </td>
                <td className="px-4 py-3 font-mono">
                  {result.total_time ? formatTime(result.total_time) : '-'}
                </td>
                <td className="px-4 py-3">
                  {Object.keys(result.checkpoint_times || {}).length}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Actualizaciones en vivo */}
      <div className="mt-4 text-sm text-gray-600">
        🔴 EN VIVO - Actualización automática cada 2 segundos
      </div>
    </div>
  );
}

function formatTime(seconds) {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}
```

---

## 🔌 Integración con Sistema Local

### Cliente API en Python (src/api/client.py)

```python
import asyncio
import aiohttp
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class RaceAPIClient:
    """Cliente para enviar resultados al servidor web"""

    def __init__(self, api_url: str, event_id: str, api_key: Optional[str] = None):
        self.api_url = api_url.rstrip('/')
        self.event_id = event_id
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.queue = asyncio.Queue()
        self.worker_task = None

    async def start(self):
        """Iniciar cliente y worker"""
        self.session = aiohttp.ClientSession(
            headers={'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}
        )
        self.worker_task = asyncio.create_task(self._worker())
        logger.info(f"🌐 API Client iniciado: {self.api_url}")

    async def stop(self):
        """Detener cliente"""
        if self.worker_task:
            self.worker_task.cancel()
        if self.session:
            await self.session.close()

    async def send_detection(self, detection_event):
        """Enviar detección al servidor (async)"""
        await self.queue.put({
            'type': 'detection',
            'data': {
                'tag_id': detection_event.tag_id,
                'timestamp': detection_event.timestamp.isoformat(),
                'antenna_port': detection_event.antenna_port,
                'event_type': detection_event.event_type.value,
                'checkpoint_number': detection_event.checkpoint_number,
                'category_id': detection_event.category_id
            }
        })

    async def send_result(self, athlete_result):
        """Enviar resultado actualizado"""
        await self.queue.put({
            'type': 'result',
            'data': {
                'athlete_id': athlete_result.athlete.athlete_id,
                'tag_id': athlete_result.athlete.tag_id,
                'bib_number': athlete_result.athlete.bib_number,
                'name': athlete_result.athlete.name,
                'category_id': athlete_result.category_id,
                'status': athlete_result.status.value,
                'start_time': athlete_result.start_time.isoformat() if athlete_result.start_time else None,
                'finish_time': athlete_result.finish_time.isoformat() if athlete_result.finish_time else None,
                'total_time': athlete_result.total_time.total_seconds() if athlete_result.total_time else None,
                'position': athlete_result.position,
                'checkpoint_times': {
                    k: v.isoformat() for k, v in athlete_result.checkpoint_times.items()
                }
            }
        })

    async def _worker(self):
        """Worker que procesa la cola de envíos"""
        while True:
            try:
                item = await self.queue.get()

                if item['type'] == 'detection':
                    url = f"{self.api_url}/api/events/{self.event_id}/detection"
                elif item['type'] == 'result':
                    url = f"{self.api_url}/api/events/{self.event_id}/result"
                else:
                    continue

                # Enviar con retry
                for attempt in range(3):
                    try:
                        async with self.session.post(url, json=item['data']) as response:
                            if response.status == 200:
                                logger.debug(f"✓ Enviado a API: {item['type']}")
                                break
                            else:
                                logger.warning(f"API retornó {response.status}")
                    except Exception as e:
                        logger.error(f"Error enviando a API (intento {attempt+1}): {e}")
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error en worker de API: {e}")
```

### Modificar RaceManager para enviar a API

```python
# src/core/race_tracking/race_manager.py
class RaceManager:
    def __init__(self, api_client: Optional[RaceAPIClient] = None):
        self.categories: Dict[str, RaceCategory] = {}
        self.results: Dict[str, Dict[str, AthleteResult]] = {}
        self.detection_history: List[DetectionEvent] = []
        self.api_client = api_client  # ← NUEVO

        logger.info("🏁 RaceManager inicializado")

    def process_detection(self, tag_id, timestamp, antenna_port, roles):
        # ... código existente ...

        if success:
            self.detection_history.append(event)
            self._update_classification(category.category_id)

            # ← NUEVO: Enviar a API si está configurado
            if self.api_client:
                asyncio.create_task(self.api_client.send_detection(event))
                asyncio.create_task(self.api_client.send_result(result))

            logger.info(f"✅ {event}")
            return event
```

---

## 📝 Implementación por Fases

### Fase 1: Base de Datos y Exportación (1-2 semanas)
- [ ] Agregar SQLite como storage persistente
- [ ] Crear función de exportación CSV/JSON
- [ ] Permitir importación de CSV con registros

### Fase 2: API Backend Básico (2-3 semanas)
- [ ] Setup FastAPI con endpoints básicos
- [ ] Implementar POST /detection y GET /results
- [ ] Desplegar en Railway/Render/Heroku
- [ ] Testing con Postman

### Fase 3: Frontend Web Básico (2 semanas)
- [ ] Página de pre-registro con formulario
- [ ] Página de resultados con tabla simple
- [ ] Polling cada 5 segundos para actualizar

### Fase 4: Tiempo Real con WebSockets (1-2 semanas)
- [ ] Implementar WebSocket endpoint
- [ ] Conectar frontend con WebSocket
- [ ] Actualizaciones instantáneas

### Fase 5: Features Avanzados (según necesidad)
- [ ] Búsqueda y filtros avanzados
- [ ] Gráficos de progreso
- [ ] Comparación entre corredores
- [ ] Notificaciones push
- [ ] App móvil (React Native/Flutter)

---

## 🎯 Próximos Pasos Inmediatos

1. **Agregar persistencia SQLite**
   - Crear esquema de base de datos
   - Guardar detecciones y resultados

2. **Crear exportador simple**
   - Botón "Exportar Resultados" → CSV
   - Estructura: dorsal, nombre, categoría, tiempo

3. **Prototipo de API**
   - FastAPI básico con 3 endpoints
   - Desplegar en un servicio gratuito

4. **Página web estática simple**
   - HTML + JavaScript vanilla
   - Fetch API cada 5 segundos
   - Sin necesidad de framework complejo inicialmente

---

¿Te interesa que empecemos por alguna fase específica? Puedo implementar:
- La persistencia SQLite primero
- Un exportador CSV simple
- O un prototipo de API REST básico
