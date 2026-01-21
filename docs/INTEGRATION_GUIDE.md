# Guía de Integración con Sistema Web Existente

## 🎯 Objetivo

Conectar el sistema de timing local (Python/PyQt6) con tu sistema web existente:
- **Backend**: Cloud Run (Google Cloud)
- **Frontend**: Vercel
- **Pre-registro**: Atletas ya registrados con datos completos

---

## 📋 Flujo de Integración

```
┌─────────────────────────────────────────────────────────────┐
│              ANTES DEL EVENTO                                │
│                                                              │
│  Vercel (Frontend)                                          │
│       ↓                                                      │
│  Corredores se registran                                    │
│       ↓                                                      │
│  Cloud Run (Backend)                                        │
│       ↓                                                      │
│  Base de Datos (Firebase/PostgreSQL/MySQL)                 │
│       ↓                                                      │
│  [Datos almacenados: nombre, edad, categoría, email, etc.] │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              DÍA DEL EVENTO                                  │
│                                                              │
│  Sistema Local (Python)                                     │
│       ↓                                                      │
│  1. Importar atletas desde Cloud Run                        │
│       GET /api/events/{event_id}/athletes                   │
│       GET /api/events/{event_id}/categories                 │
│       ↓                                                      │
│  2. Asignar Chips Físicos (ChipAssignmentWidget)           │
│       - Seleccionar atleta                                  │
│       - Escanear chip RFID                                  │
│       - Asignar chip → atleta                               │
│       ↓                                                      │
│  3. Iniciar Carrera                                         │
│       - Start category                                      │
│       - Scanner detecta chips                               │
│       - RaceManager procesa                                 │
│       ↓                                                      │
│  4. Enviar Resultados en Vivo a Cloud Run                  │
│       POST /api/events/{event_id}/detection                 │
│       POST /api/events/{event_id}/result                    │
│       ↓                                                      │
│  Cloud Run → Base de Datos → Vercel (Frontend)            │
│       ↓                                                      │
│  Espectadores ven resultados en vivo                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Configuración

### 1. **Configurar Credenciales de API**

Crear archivo `config/api_config.json`:

```json
{
  "api_url": "https://your-backend-xyz123.run.app",
  "api_key": "tu-api-key-aqui",
  "event_id": "ultra-2025",
  "sync_enabled": true,
  "sync_interval_seconds": 10
}
```

### 2. **Adaptar AthleteImporter a tu API**

Editar `src/core/athlete_importer.py` línea 82-140:

```python
def _parse_athletes(self, data: Any) -> Dict[str, List[Athlete]]:
    """
    AJUSTAR ESTA FUNCIÓN según la estructura de tu API
    """
    athletes_by_category = {}

    # ===== AJUSTAR AQUÍ =====
    # Ejemplo: Si tu API retorna
    # {
    #   "success": true,
    #   "data": {
    #     "athletes": [...]
    #   }
    # }

    if 'data' in data and 'athletes' in data['data']:
        athletes_data = data['data']['athletes']
    elif 'athletes' in data:
        athletes_data = data['athletes']
    else:
        athletes_data = data  # Si es directamente un array

    for athlete_data in athletes_data:
        try:
            # MAPEAR CAMPOS DE TU API
            athlete = Athlete(
                athlete_id=athlete_data.get('id'),              # ← tu campo
                tag_id='',  # Vacío al importar, se asigna después
                bib_number=athlete_data.get('bib_number'),      # ← tu campo
                name=athlete_data.get('full_name'),             # ← tu campo
                category_id=athlete_data.get('category_id'),    # ← tu campo
                team=athlete_data.get('team_name'),             # ← tu campo
                notes=self._build_notes(athlete_data)
            )

            # Agrupar por categoría
            category_id = athlete.category_id
            if category_id not in athletes_by_category:
                athletes_by_category[category_id] = []

            athletes_by_category[category_id].append(athlete)

        except Exception as e:
            logger.error(f"Error parseando atleta: {e}")
            continue

    return athletes_by_category
```

### 3. **Mapear Campos Adicionales**

Ajustar `_build_notes()` para incluir todos los datos que necesites:

```python
def _build_notes(self, athlete_data: dict) -> str:
    """Incluir datos extras en las notas"""
    notes = []

    # Edad
    if 'age' in athlete_data:
        notes.append(f"Edad: {athlete_data['age']}")

    # Género
    if 'gender' in athlete_data:
        notes.append(f"Género: {athlete_data['gender']}")

    # Elevación ganada (para trail running)
    if 'elevation_gain' in athlete_data:
        notes.append(f"D+: {athlete_data['elevation_gain']}m")

    # Email
    if 'email' in athlete_data:
        notes.append(f"Email: {athlete_data['email']}")

    # Teléfono
    if 'phone' in athlete_data:
        notes.append(f"Tel: {athlete_data['phone']}")

    # Contacto de emergencia
    if 'emergency_contact' in athlete_data:
        notes.append(f"Emergencia: {athlete_data['emergency_contact']}")

    # Estado de pago
    if 'payment_status' in athlete_data:
        notes.append(f"Pago: {athlete_data['payment_status']}")

    # Camiseta
    if 'shirt_size' in athlete_data:
        notes.append(f"Talla: {athlete_data['shirt_size']}")

    return " | ".join(notes)
```

---

## 📥 Proceso de Importación

### Opción 1: Importación Manual (Recomendada inicialmente)

```python
# test_import.py
from src.core.athlete_importer import AthleteImporter
from src.core.race_tracking.race_manager import RaceManager
import json

# Cargar configuración
with open('config/api_config.json') as f:
    config = json.load(f)

# Crear importador
importer = AthleteImporter(
    api_url=config['api_url'],
    api_key=config['api_key']
)

# Probar conexión
if importer.test_connection():
    print("✅ Conexión exitosa")

    # Importar categorías
    categories = importer.import_categories(event_id=config['event_id'])
    print(f"📋 Categorías: {len(categories)}")

    # Importar atletas
    athletes_by_cat = importer.import_athletes(event_id=config['event_id'])

    # Crear race manager y cargar datos
    race_manager = RaceManager()

    for category in categories:
        race_manager.add_category(category)

        # Agregar atletas a categoría
        if category.category_id in athletes_by_cat:
            for athlete in athletes_by_cat[category.category_id]:
                category.add_participant(athlete)

    print(f"✅ {len(race_manager.get_all_categories())} categorías cargadas")
```

### Opción 2: Importación desde GUI

Agregar botón en `EventConfigWidget`:

```python
# En EventConfigWidget.setup_ui()

self.import_web_button = QPushButton("📥 Importar desde Sistema Web")
self.import_web_button.clicked.connect(self.import_from_web_system)

def import_from_web_system(self):
    """Importar atletas desde Cloud Run"""
    from src.core.athlete_importer import AthleteImporter
    import json

    try:
        # Cargar configuración
        with open('config/api_config.json') as f:
            config = json.load(f)

        # Crear importador
        importer = AthleteImporter(
            api_url=config['api_url'],
            api_key=config['api_key']
        )

        # Probar conexión
        if not importer.test_connection():
            QMessageBox.critical(self, "Error", "No se pudo conectar al servidor")
            return

        # Importar categorías
        categories = importer.import_categories(event_id=config['event_id'])

        # Importar atletas
        athletes_by_cat = importer.import_athletes(event_id=config['event_id'])

        # Agregar a race_manager
        for category in categories:
            self.race_manager.add_category(category)

            if category.category_id in athletes_by_cat:
                for athlete in athletes_by_cat[category.category_id]:
                    category.add_participant(athlete)

        # Actualizar UI
        self.refresh_categories_table()

        total_athletes = sum(len(a) for a in athletes_by_cat.values())

        QMessageBox.information(
            self,
            "Importación Exitosa",
            f"✅ Importados:\n"
            f"• {len(categories)} categorías\n"
            f"• {total_athletes} atletas\n\n"
            f"Ahora ve al tab 'Asignación de Chips' para asignar chips RFID"
        )

    except Exception as e:
        QMessageBox.critical(self, "Error", f"Error importando: {e}")
        logger.error(f"Error importando: {e}")
```

---

## 🏷️ Asignación de Chips

### 1. **Agregar Tab de Asignación**

En `TabManager.create_all_tabs()`:

```python
def create_chip_assignment_tab(self):
    """Crear tab de asignación de chips"""
    logger.info("🏷️ Creando ChipAssignmentWidget...")

    from ..widgets.chip_assignment_widget import ChipAssignmentWidget

    chip_widget = ChipAssignmentWidget(
        race_manager=self.race_manager,
        scanner=self.scanner
    )
    self.tab_widget.addTab(chip_widget, "🏷️ Asignación de Chips")
    self.tabs['chip_assignment'] = chip_widget

    logger.info("✅ ChipAssignmentWidget creado")
```

Y llamarlo:

```python
def create_all_tabs(self):
    """Crear todos los tabs"""
    self.create_detection_tab()
    self.create_event_config_tab()
    self.create_chip_assignment_tab()  # ← NUEVO
    self.create_race_monitoring_tab()
    self.create_configuration_tab()
```

### 2. **Conectar Scanner con Widget**

En `ChipAssignmentWidget`, conectar señal del scanner:

```python
def set_scanner(self, scanner):
    """Conectar con scanner para modo de escaneo"""
    self.scanner = scanner

    # Conectar señal de detección
    if scanner and hasattr(scanner, 'tag_detected'):
        scanner.tag_detected.connect(self.on_chip_scanned)

    logger.info("✅ Scanner conectado a ChipAssignmentWidget")
```

---

## 📤 Envío de Resultados en Vivo

### 1. **Integrar RaceAPIClient en MainWindow**

```python
# src/gui/main_window.py

from src.api.client import RaceAPIClient
import json
import asyncio

class MainWindow(QMainWindow):
    def __init__(self, wizard_config=None):
        super().__init__()

        # ... código existente ...

        # Inicializar API client
        self.api_client = None
        self.setup_api_client()

    def setup_api_client(self):
        """Configurar cliente para enviar resultados a Cloud Run"""
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

                # Iniciar cliente (async)
                asyncio.create_task(self.api_client.start())

                logger.info("✅ API Client configurado para envío de resultados")

        except FileNotFoundError:
            logger.warning("⚠️ No se encontró config/api_config.json - modo offline")
        except Exception as e:
            logger.error(f"❌ Error configurando API client: {e}")

    def on_tag_detected_for_race(self, tag_data):
        """Procesar detección + enviar a Cloud Run"""
        # ... procesamiento local existente ...

        event = self.race_manager.process_detection(...)

        if event and self.api_client:
            # Enviar a Cloud Run (async, no bloquea)
            asyncio.create_task(self.api_client.send_detection(event))
```

### 2. **Endpoints Necesarios en tu Cloud Run**

Tu backend debe implementar estos endpoints:

```
GET  /api/events/{event_id}/categories
GET  /api/events/{event_id}/athletes
POST /api/events/{event_id}/detection
POST /api/events/{event_id}/result
GET  /api/events/{event_id}/results
```

Ejemplo de estructura esperada:

**GET /api/events/{event_id}/athletes**
```json
{
  "success": true,
  "data": {
    "athletes": [
      {
        "id": "athlete-uuid-123",
        "bib_number": 125,
        "first_name": "Juan",
        "last_name": "Pérez",
        "full_name": "Juan Pérez",
        "email": "juan@example.com",
        "phone": "+5491112345678",
        "age": 35,
        "gender": "M",
        "category_id": "100k",
        "team_name": "Club Runners",
        "emergency_contact": "María Pérez - +5491187654321",
        "payment_status": "confirmed",
        "shirt_size": "L"
      },
      ...
    ]
  }
}
```

**POST /api/events/{event_id}/detection**
```json
{
  "tag_id": "7662",
  "timestamp": "2025-01-21T14:30:25.123Z",
  "antenna_port": 1,
  "event_type": "start",
  "checkpoint_number": null,
  "category_id": "100k",
  "athlete_name": "Juan Pérez",
  "bib_number": 125
}
```

---

## 🔄 Sincronización Completa

### Script de Sincronización Inicial

```python
# scripts/sync_with_web.py
"""
Script para sincronización inicial completa
"""

import asyncio
import json
from src.core.athlete_importer import AthleteImporter
from src.core.race_tracking.race_manager import RaceManager
from src.api.client import RaceAPIClient

async def main():
    # Cargar config
    with open('config/api_config.json') as f:
        config = json.load(f)

    # 1. Importar desde Cloud Run
    print("📥 Importando atletas...")
    importer = AthleteImporter(
        api_url=config['api_url'],
        api_key=config['api_key']
    )

    categories = importer.import_categories(event_id=config['event_id'])
    athletes_by_cat = importer.import_athletes(event_id=config['event_id'])

    # 2. Cargar en RaceManager
    print("💾 Cargando en sistema local...")
    race_manager = RaceManager()

    for category in categories:
        race_manager.add_category(category)
        if category.category_id in athletes_by_cat:
            for athlete in athletes_by_cat[category.category_id]:
                category.add_participant(athlete)

    # 3. Configurar API client para envío
    print("🔄 Configurando sincronización...")
    api_client = RaceAPIClient(
        api_url=config['api_url'],
        event_id=config['event_id'],
        api_key=config['api_key']
    )

    await api_client.start()

    # 4. Sincronizar categorías
    await api_client.sync_categories(categories)

    # 5. Sincronizar atletas
    for category in categories:
        await api_client.sync_athletes(category.category_id, category.participants)

    await api_client.stop()

    print("✅ Sincronización completa")
    print(f"  • {len(categories)} categorías")
    total_athletes = sum(len(athletes_by_cat[c.category_id]) for c in categories if c.category_id in athletes_by_cat)
    print(f"  • {total_athletes} atletas")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## ✅ Checklist de Integración

### Antes del Evento:

- [ ] Crear `config/api_config.json` con URL de Cloud Run
- [ ] Probar conexión: `python test_import.py`
- [ ] Verificar estructura de datos de tu API
- [ ] Ajustar `_parse_athletes()` según tus campos
- [ ] Ajustar `_build_notes()` para incluir todos los datos
- [ ] Probar importación de categorías
- [ ] Probar importación de atletas

### Día del Evento:

- [ ] Importar atletas desde Cloud Run
- [ ] Abrir tab "Asignación de Chips"
- [ ] Para cada atleta:
  - [ ] Seleccionar en lista
  - [ ] Escanear chip RFID
  - [ ] Verificar asignación
- [ ] Verificar que todos tienen chip asignado
- [ ] Iniciar categorías
- [ ] Verificar que detecciones se envían a Cloud Run
- [ ] Verificar que Vercel muestra resultados en vivo

---

## 🐛 Troubleshooting

### Error: "No se pudo conectar al servidor"

1. Verificar que Cloud Run está online
2. Verificar API key
3. Verificar que no hay firewall bloqueando

### Error: "Formato de respuesta no esperado"

1. Hacer request manual con curl:
   ```bash
   curl https://your-backend.run.app/api/events/ultra-2025/athletes \
     -H "Authorization: Bearer your-api-key"
   ```
2. Ver estructura de respuesta
3. Ajustar `_parse_athletes()` según estructura real

### Chips no se están enviando a Cloud Run

1. Verificar `config/api_config.json` → `sync_enabled: true`
2. Ver logs del sistema
3. Verificar que API client se inició correctamente

---

## 📞 Soporte

Para configurar correctamente la integración con tu sistema específico:

1. Compartir un ejemplo de la respuesta de tu API
2. Compartir estructura de datos de atletas
3. Ajustaremos el importador específicamente para tu caso

¿Tienes el Swagger/OpenAPI de tu Cloud Run? Eso ayudaría mucho.
