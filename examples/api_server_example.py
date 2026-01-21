#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ejemplo de Servidor API REST para Resultados en Vivo
examples/api_server_example.py

Este es un servidor de ejemplo que muestra cómo recibir
detecciones desde el sistema de timing y servir resultados
a una página web pública.

Instalación:
    pip install fastapi uvicorn python-multipart

Ejecutar:
    uvicorn api_server_example:app --reload --host 0.0.0.0 --port 8000

Acceder:
    http://localhost:8000/docs  (Documentación automática)
    http://localhost:8000/      (Página de resultados)
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Dict
import asyncio
import json

# ============================================================================
# MODELOS DE DATOS
# ============================================================================

class DetectionEvent(BaseModel):
    """Evento de detección RFID"""
    tag_id: str
    timestamp: str  # ISO format
    antenna_port: int
    event_type: str  # "start", "checkpoint", "finish"
    checkpoint_number: Optional[int] = None
    category_id: str
    athlete_name: Optional[str] = None
    bib_number: Optional[int] = None


class AthleteResult(BaseModel):
    """Resultado de un atleta"""
    athlete_id: str
    tag_id: str
    bib_number: int
    name: str
    category_id: str
    status: str
    start_time: Optional[str] = None
    finish_time: Optional[str] = None
    total_time: Optional[float] = None
    position: Optional[int] = None
    checkpoint_times: Dict[str, str] = {}
    splits: Dict[str, float] = {}


class Category(BaseModel):
    """Categoría de carrera"""
    category_id: str
    name: str
    distance: float
    expected_checkpoints: int
    status: str


# ============================================================================
# APLICACIÓN
# ============================================================================

app = FastAPI(
    title="RFID Athletics Timer API",
    description="API para resultados en vivo de carreras con timing RFID",
    version="1.0.0"
)

# Configurar CORS para permitir acceso desde navegadores
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# ALMACENAMIENTO EN MEMORIA (En producción: PostgreSQL/MySQL)
# ============================================================================

# Base de datos simulada
db = {
    'categories': {},
    'athletes': {},
    'results': {},
    'detections': []
}


# ============================================================================
# WEBSOCKET CONNECTION MANAGER
# ============================================================================

class ConnectionManager:
    """Gestor de conexiones WebSocket para actualizaciones en tiempo real"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ Cliente conectado. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"❌ Cliente desconectado. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Enviar mensaje a todos los clientes conectados"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        # Limpiar conexiones muertas
        for conn in disconnected:
            self.active_connections.remove(conn)


manager = ConnectionManager()


# ============================================================================
# ENDPOINTS - CONFIGURACIÓN DEL EVENTO
# ============================================================================

@app.post("/api/events/{event_id}/categories")
async def sync_categories(event_id: str, data: dict):
    """
    Sincronizar categorías desde el sistema local

    Body:
        {
            "event_id": "event-2025-01",
            "categories": [...]
        }
    """
    categories = data.get('categories', [])

    for cat_data in categories:
        cat_id = cat_data['category_id']
        db['categories'][cat_id] = cat_data

    print(f"✅ {len(categories)} categorías sincronizadas para evento {event_id}")

    return {"success": True, "count": len(categories)}


@app.post("/api/events/{event_id}/athletes")
async def sync_athletes(event_id: str, data: dict):
    """
    Sincronizar atletas desde el sistema local

    Body:
        {
            "category_id": "100k",
            "athletes": [...]
        }
    """
    category_id = data.get('category_id')
    athletes = data.get('athletes', [])

    for athlete in athletes:
        athlete_id = athlete['athlete_id']
        db['athletes'][athlete_id] = athlete

        # Inicializar resultado
        db['results'][athlete_id] = {
            **athlete,
            'category_id': category_id,
            'status': 'not_started',
            'start_time': None,
            'finish_time': None,
            'total_time': None,
            'position': None,
            'checkpoint_times': {},
            'splits': {}
        }

    print(f"✅ {len(athletes)} atletas sincronizados en categoría {category_id}")

    return {"success": True, "count": len(athletes)}


# ============================================================================
# ENDPOINTS - DETECCIONES EN TIEMPO REAL
# ============================================================================

@app.post("/api/events/{event_id}/detection")
async def record_detection(event_id: str, detection: DetectionEvent):
    """
    Recibir detección desde el sistema de timing local

    El sistema local envía cada detección RFID a este endpoint
    """
    # Guardar en historial
    db['detections'].append(detection.dict())

    # Actualizar resultado del atleta
    athlete_id = None
    for aid, athlete in db['athletes'].items():
        if athlete['tag_id'] == detection.tag_id:
            athlete_id = aid
            break

    if athlete_id and athlete_id in db['results']:
        result = db['results'][athlete_id]

        # Actualizar según tipo de evento
        if detection.event_type == 'start':
            result['status'] = 'running'
            result['start_time'] = detection.timestamp

        elif detection.event_type == 'checkpoint':
            cp_num = str(detection.checkpoint_number)
            result['checkpoint_times'][cp_num] = detection.timestamp

        elif detection.event_type == 'finish':
            result['status'] = 'finished'
            result['finish_time'] = detection.timestamp

    # Broadcast a clientes WebSocket
    await manager.broadcast({
        'type': 'detection',
        'event_id': event_id,
        'data': detection.dict()
    })

    print(f"📡 Detección recibida: {detection.tag_id} - {detection.event_type}")

    return {"success": True}


@app.post("/api/events/{event_id}/result")
async def update_result(event_id: str, result: AthleteResult):
    """
    Actualizar resultado completo de un atleta

    El sistema local puede enviar el resultado completo
    después de calcular tiempos y posiciones
    """
    athlete_id = result.athlete_id
    db['results'][athlete_id] = result.dict()

    # Broadcast a clientes WebSocket
    await manager.broadcast({
        'type': 'result',
        'event_id': event_id,
        'data': result.dict()
    })

    print(f"📊 Resultado actualizado: {result.name} - {result.status}")

    return {"success": True}


# ============================================================================
# ENDPOINTS - CONSULTA DE RESULTADOS
# ============================================================================

@app.get("/api/events/{event_id}/results")
async def get_results(
    event_id: str,
    category_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
) -> List[dict]:
    """
    Obtener resultados actuales

    Query params:
    - category_id: Filtrar por categoría
    - status: Filtrar por estado ("running", "finished", etc.)
    - limit: Máximo de resultados (default: 100)
    """
    results = list(db['results'].values())

    # Filtrar por categoría
    if category_id:
        results = [r for r in results if r['category_id'] == category_id]

    # Filtrar por estado
    if status:
        results = [r for r in results if r['status'] == status]

    # Ordenar por posición (si existe) o por tiempo
    results.sort(key=lambda r: (
        r['position'] if r['position'] else 9999,
        r['total_time'] if r['total_time'] else 999999
    ))

    # Limitar resultados
    results = results[:limit]

    return results


@app.get("/api/events/{event_id}/leaderboard/{category_id}")
async def get_leaderboard(event_id: str, category_id: str):
    """
    Obtener tabla de posiciones de una categoría

    Retorna resultados ordenados por tiempo
    """
    results = [
        r for r in db['results'].values()
        if r['category_id'] == category_id
    ]

    # Ordenar por tiempo total (finalizados primero)
    finished = [r for r in results if r['status'] == 'finished']
    running = [r for r in results if r['status'] == 'running']
    not_started = [r for r in results if r['status'] == 'not_started']

    finished.sort(key=lambda r: r['total_time'] if r['total_time'] else 999999)
    running.sort(key=lambda r: r['bib_number'])
    not_started.sort(key=lambda r: r['bib_number'])

    # Asignar posiciones a finalizados
    for idx, result in enumerate(finished, 1):
        result['position'] = idx

    ordered_results = finished + running + not_started

    category_info = db['categories'].get(category_id, {'name': category_id})

    return {
        'category': category_info,
        'updated_at': datetime.now().isoformat(),
        'total_participants': len(ordered_results),
        'finished': len(finished),
        'running': len(running),
        'not_started': len(not_started),
        'results': ordered_results
    }


@app.get("/api/events/{event_id}/stats")
async def get_event_stats(event_id: str):
    """
    Estadísticas generales del evento
    """
    results = list(db['results'].values())

    stats_by_category = {}
    for cat_id, cat_data in db['categories'].items():
        cat_results = [r for r in results if r['category_id'] == cat_id]
        stats_by_category[cat_id] = {
            'name': cat_data['name'],
            'total': len(cat_results),
            'running': len([r for r in cat_results if r['status'] == 'running']),
            'finished': len([r for r in cat_results if r['status'] == 'finished']),
            'not_started': len([r for r in cat_results if r['status'] == 'not_started'])
        }

    return {
        'event_id': event_id,
        'total_participants': len(results),
        'total_detections': len(db['detections']),
        'categories': stats_by_category,
        'updated_at': datetime.now().isoformat()
    }


# ============================================================================
# WEBSOCKET - ACTUALIZACIONES EN TIEMPO REAL
# ============================================================================

@app.websocket("/ws/events/{event_id}/live")
async def websocket_live_results(websocket: WebSocket, event_id: str):
    """
    WebSocket para recibir actualizaciones en tiempo real

    Los clientes se conectan y reciben:
    - Detecciones nuevas
    - Resultados actualizados
    - Cambios en clasificaciones

    Ejemplo de uso en JavaScript:
        const ws = new WebSocket('ws://localhost:8000/ws/events/event-2025-01/live');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Nueva actualización:', data);
        };
    """
    await manager.connect(websocket)

    try:
        # Mantener conexión abierta y escuchar mensajes del cliente
        while True:
            data = await websocket.receive_text()
            # El cliente puede enviar "ping" para mantener conexión viva
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        manager.disconnect(websocket)


# ============================================================================
# PÁGINA WEB SIMPLE (HTML)
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Página web simple para ver resultados en vivo
    """
    html_content = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Resultados en Vivo - RFID Athletics Timer</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                background: #f5f5f5;
                padding: 20px;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            h1 {
                font-size: 2rem;
                margin-bottom: 10px;
                color: #333;
            }
            .status {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.9rem;
                font-weight: bold;
            }
            .status.live {
                background: #10b981;
                color: white;
            }
            .controls {
                margin: 20px 0;
                display: flex;
                gap: 10px;
            }
            select, button {
                padding: 10px 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 1rem;
            }
            button {
                background: #3b82f6;
                color: white;
                cursor: pointer;
            }
            button:hover { background: #2563eb; }
            table {
                width: 100%;
                background: white;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            th {
                background: #1f2937;
                color: white;
                padding: 15px;
                text-align: left;
            }
            td {
                padding: 12px 15px;
                border-bottom: 1px solid #f3f4f6;
            }
            tr:hover { background: #f9fafb; }
            .running { background: #fef3c7; }
            .finished { background: #d1fae5; }
            .pos-1 { font-weight: bold; color: #d97706; }
            .pos-2 { font-weight: bold; color: #6b7280; }
            .pos-3 { font-weight: bold; color: #92400e; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏃 Resultados en Vivo</h1>
            <span class="status live" id="status">🔴 EN VIVO</span>

            <div class="controls">
                <select id="categoryFilter">
                    <option value="">Todas las categorías</option>
                </select>
                <button onclick="refreshResults()">🔄 Actualizar</button>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Pos</th>
                        <th>Dorsal</th>
                        <th>Nombre</th>
                        <th>Categoría</th>
                        <th>Estado</th>
                        <th>Tiempo</th>
                        <th>Checkpoints</th>
                    </tr>
                </thead>
                <tbody id="resultsTable">
                    <tr><td colspan="7" style="text-align:center">Cargando resultados...</td></tr>
                </tbody>
            </table>
        </div>

        <script>
            let ws;
            const API_URL = window.location.origin;
            const EVENT_ID = 'event-2025-01';

            // Conectar WebSocket
            function connectWebSocket() {
                const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/events/${EVENT_ID}/live`);

                ws.onopen = () => {
                    console.log('✅ WebSocket conectado');
                    document.getElementById('status').textContent = '🔴 EN VIVO';
                };

                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    console.log('Nueva actualización:', data);
                    refreshResults();
                };

                ws.onclose = () => {
                    console.log('❌ WebSocket desconectado');
                    document.getElementById('status').textContent = '⚪ DESCONECTADO';
                    setTimeout(connectWebSocket, 3000);
                };

                // Ping cada 30 segundos
                setInterval(() => {
                    if (ws.readyState === WebSocket.OPEN) {
                        ws.send('ping');
                    }
                }, 30000);
            }

            // Cargar resultados
            async function refreshResults() {
                try {
                    const category = document.getElementById('categoryFilter').value;
                    const url = `${API_URL}/api/events/${EVENT_ID}/results${category ? '?category_id=' + category : ''}`;
                    const response = await fetch(url);
                    const results = await response.json();

                    const tbody = document.getElementById('resultsTable');
                    tbody.innerHTML = '';

                    if (results.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center">No hay resultados aún</td></tr>';
                        return;
                    }

                    results.forEach((result, idx) => {
                        const row = tbody.insertRow();
                        row.className = result.status === 'running' ? 'running' : result.status === 'finished' ? 'finished' : '';

                        const posClass = result.position === 1 ? 'pos-1' : result.position === 2 ? 'pos-2' : result.position === 3 ? 'pos-3' : '';

                        row.innerHTML = `
                            <td class="${posClass}">${result.position || '-'}</td>
                            <td><strong>${result.bib_number}</strong></td>
                            <td>${result.name}</td>
                            <td>${result.category_id.toUpperCase()}</td>
                            <td>${getStatusBadge(result.status)}</td>
                            <td>${formatTime(result.total_time)}</td>
                            <td>${Object.keys(result.checkpoint_times || {}).length}</td>
                        `;
                    });
                } catch (error) {
                    console.error('Error cargando resultados:', error);
                }
            }

            function getStatusBadge(status) {
                const badges = {
                    'running': '🏃 En Carrera',
                    'finished': '🏁 Finalizado',
                    'not_started': '⏳ No Iniciado'
                };
                return badges[status] || status;
            }

            function formatTime(seconds) {
                if (!seconds) return '-';
                const h = Math.floor(seconds / 3600);
                const m = Math.floor((seconds % 3600) / 60);
                const s = Math.floor(seconds % 60);
                return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
            }

            // Inicializar
            connectWebSocket();
            refreshResults();
            setInterval(refreshResults, 5000); // Refresh cada 5 segundos como fallback
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ============================================================================
# EJECUTAR SERVIDOR
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando servidor API...")
    print("📖 Documentación: http://localhost:8000/docs")
    print("🌐 Página web: http://localhost:8000/")
    uvicorn.run(app, host="0.0.0.0", port=8000)
