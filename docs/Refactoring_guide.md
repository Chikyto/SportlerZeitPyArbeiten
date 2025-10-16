# Guía de Refactorización - RFID Athletics Timer

## 🎯 Objetivo

Convertir el código monolítico `tabbed_gui.py` en una arquitectura modular, escalable y mantenible con wizard de configuración automático.

## ✅ Estado del Proyecto

**Completado:**
- ✅ Arquitectura modular con separación de responsabilidades
- ✅ Sistema de señales centralizado (AppSignals)
- ✅ Tabs modulares (ConnectionTab, DetectionTab)
- ✅ MainWindow refactorizado como orquestador
- ✅ Wizard automático con auto-detección
- ✅ Integración wizard → MainWindow
- ✅ Configuración pre-cargada desde wizard
- ✅ Modo edición opcional para ajustes
- ✅ **AdvancedScanner refactorizado con YR8900Protocol**
- ✅ **Sistema de multi-antena funcional**
- ✅ **Detección física de antenas con return loss**

**En Progreso:**
- 🔄 Integración de configuración wizard → scanner
- 🔄 Sistema de detección de chips por antena específica

**Pendiente:**
- ⏳ Gestión de eventos y categorías
- ⏳ Tracking de carreras en tiempo real
- ⏳ Exportación de datos
- ⏳ Integración con Firebase

---

## 📁 Estructura Actual

```
src/
├── core/                           # Lógica de negocio
│   ├── advanced_scanner.py         # ✨ REFACTORIZADO: Scanner multi-antena
│   ├── tag_parser.py               # Parser de tags RFID
│   ├── event_manager.py            # Gestión de eventos
│   ├── integrated_race_tracker.py  # Tracking de carreras
│   └── race_config.py              # Configuración
│
├── hardware/                       # Interfaz con hardware
│   ├── yr8900_protocol.py          # Protocolo de comunicación
│   ├── antenna_detection.py        # Detección física de antenas
│   ├── reader_manager.py           # Gestor de alto nivel
│   └── config.py                   # Configuración de hardware
│
├── gui/
│   ├── main_window.py              # MainWindow refactorizado
│   │
│   ├── wizard/                     # Wizard de configuración
│   │   ├── configuration_wizard.py
│   │   ├── antenna_config_page.py
│   │   ├── antenna_detection_page.py
│   │   └── connection_page.py
│   │
│   ├── tabs/                       # Tabs modulares
│   │   ├── __init__.py
│   │   ├── base_tab.py
│   │   ├── connection_tab.py
│   │   ├── detection_tab.py
│   │   ├── antenna_config_tab.py
│   │   ├── event_config_tab.py
│   │   ├── competition_tab.py
│   │   └── database_tab.py
│   │
│   └── widgets/                    # Widgets especializados
│       ├── antenna_config_widget.py
│       ├── event_config_widget.py
│       └── race_monitoring_widget.py
│
├── utils/                          # Utilidades
│   ├── __init__.py
│   ├── signals.py                  # Sistema de señales
│   └── logger.py                   # Sistema de logging
│
├── tests/                          # Tests
│   ├── test_multiantena.py         # ✨ NUEVO: Test multi-antena
│   └── ...
│
└── main.py                         # Entry point único
```

---

## 🔄 Cambios Recientes (Octubre 2025)

### AdvancedScanner Refactorizado

**Problema Anterior:**
- Scanner creaba conexiones socket directas
- Comandos sin checksum correcto
- `set_work_antenna()` causaba timeouts
- No integraba con el sistema de detección de antenas

**Solución Implementada:**
```python
# Antes (❌ No funcionaba)
def set_work_antenna(self, antenna_id):
    cmd = bytes([0xA0, 0x04, 0xF3, 0x74, antenna_id])  # Sin checksum
    response = self.send_command(cmd)

# Ahora (✅ Funciona)
def set_work_antenna(self, antenna_id):
    result = self.protocol.send_command(
        CommandCodes.SET_WORK_ANTENNA,
        [port - 1]  # Base 0 para protocolo
    )
    # Checksum automático + manejo robusto
```

**Beneficios:**
- ✅ Reutiliza `YR8900Protocol` probado
- ✅ Checksum automático en todos los comandos
- ✅ Integración con `AntennaDetector`
- ✅ Manejo consistente de errores
- ✅ Multi-antena funcional

### Sistema Multi-Antena

**Características:**
- Detección automática de antenas físicas (1-8 puertos)
- Medición de return loss para validar conexiones
- Rotación automática entre antenas activas
- Tracking de qué tag fue visto en qué antena

**Test Exitoso:**
```
Antenas conectadas: 4
Puertos: [2, 3, 4, 6]
Tags únicos detectados: 7

Tag 8600: detectado en puerto(s) 2, 3, 4, 6
Tag 8575: detectado en puerto(s) 3, 6
Tag 7662: detectado en puerto(s) 2
```

---

## 🎨 Arquitectura Actualizada

### Flujo de Comunicación con Hardware

```
GUI/MainWindow
      ↓
AdvancedScanner
      ↓
YR8900Protocol ←→ Socket ←→ Hardware YR8900
      ↓
AntennaDetector
```

### Jerarquía de Clases

```
YR8900Protocol (Base)
├── Manejo de comandos
├── Cálculo de checksums
├── Parsing de respuestas
└── Gestión de conexiones

AntennaDetector (usa Protocol)
├── Detección física (return loss)
├── Scan de todos los puertos
└── Validación de conexiones

ReaderManager (usa Protocol + Detector)
├── API de alto nivel
├── Gestión de estado
└── Operaciones complejas

AdvancedScanner (usa Protocol + Detector)
├── Scanning de tags
├── Multi-antena
├── Parsing de EPC
└── Compatibilidad con GUI
```

---

## 🔧 Integración con Wizard (Próximo Paso)

### Estado Actual del Wizard

El wizard ya detecta y configura:
1. ✅ Conexión al lector (IP/Puerto)
2. ✅ Antenas físicamente conectadas (return loss)
3. ✅ Roles de antenas (Largada/Meta/Checkpoint)
4. ✅ Potencia y parámetros

**Configuración Guardada:**
```json
{
  "connection": {
    "host": "192.168.0.178",
    "port": 4001
  },
  "antennas": {
    "2": {
      "enabled": true,
      "name": "Largada",
      "start": true,
      "finish": false,
      "checkpoint": false
    },
    "3": {
      "enabled": true,
      "name": "Checkpoint 1",
      "start": false,
      "finish": false,
      "checkpoint": true
    }
  }
}
```

### Integración Necesaria

**Archivo: `src/gui/main_window.py`**

```python
class MainWindow:
    def __init__(self, wizard_config=None):
        self.wizard_config = wizard_config
        self.scanner = None
        self.setup_scanner()
    
    def setup_scanner(self):
        """Configura scanner con datos del wizard"""
        if self.wizard_config:
            # Usar configuración del wizard
            host = self.wizard_config['connection']['host']
            port = self.wizard_config['connection']['port']
            
            self.scanner = AdvancedScanner(host, port)
            
            # Configurar antenas habilitadas
            enabled_antennas = [
                int(port) for port, config in 
                self.wizard_config['antennas'].items()
                if config['enabled']
            ]
            self.scanner.available_antennas = enabled_antennas
```

**Archivo: `src/gui/tabs/detection_tab.py`**

```python
class DetectionTab(BaseTab):
    def start_scanning(self):
        """Inicia scan solo en antenas configuradas"""
        if not self.scanner.available_antennas:
            # Si no hay config, detectar todas
            self.scanner.detect_connected_antennas()
        
        # Scan multi-antena con rotación
        tags = self.scanner.continuous_scan_multi_antenna(
            duration=self.scan_duration
        )
        
        # Filtrar por roles si es necesario
        self.filter_tags_by_antenna_role(tags)
```

---

## 📝 Tareas Pendientes

### Próxima Fase: Integración Wizard → Scanner

- [ ] Cargar configuración del wizard en MainWindow
- [ ] Pasar antenas habilitadas a AdvancedScanner
- [ ] Filtrar tags por rol de antena (largada/meta)
- [ ] Implementar lógica de detección por posición
- [ ] Testing integración completa

### Fase Futura: Sistema de Carreras

- [ ] EventManager con categorías
- [ ] RaceTracker por antena
- [ ] Cálculo automático de splits
- [ ] Detección de vueltas
- [ ] Exportación de resultados

---

## 🐛 Debugging

### Verificar Multi-Antena

```bash
python test_multiantena.py
```

### Verificar Configuración del Wizard

```python
# En Python
import json
with open('timing_system_config.json', 'r') as f:
    config = json.load(f)
    print(f"Antenas habilitadas: {config['antennas']}")
```

### Logs del Scanner

```python
# Habilitar logs detallados
import logging
logging.basicConfig(level=logging.DEBUG)

scanner = AdvancedScanner()
scanner.connect()
```

---

## 📚 Referencias

- [YR8900 Protocol Spec](docs/yr8900_protocol.pdf)
- [PyQt6 Documentation](https://doc.qt.io/qtforpython-6/)
- [Test Multi-Antena](tests/test_multiantena.py)
- [Advanced Scanner](src/core/advanced_scanner.py)

---

**Última Actualización:** Octubre 2025
**Estado:** 🟢 Multi-antena funcional - Listo para integración