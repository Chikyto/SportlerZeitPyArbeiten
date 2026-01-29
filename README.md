# RFID Athletics Timer

Sistema profesional de cronometraje deportivo con tecnología RFID para carreras de atletismo, usando el lector YR8900.

## 🎯 Características Principales

- ✅ **AutoWizard Inteligente**: Conexión y detección de antenas automática en <5 segundos
- ✅ **Multi-Antena Funcional**: Soporte para hasta 8 antenas con rotación automática
- ✅ **Detección por Roles**: Antenas configurables como Largada/Meta/Checkpoint
- ✅ **Roles Múltiples por Antena**: Una antena puede ser Largada+Meta simultáneamente
- ✅ **Tracking en Tiempo Real**: Monitoreo de participantes con splits y tiempos
- ✅ **Persistencia de Configuración**: Guarda y carga configuración automáticamente
- ✅ **Arquitectura Modular Refactorizada**: Código limpio, mantenible y escalable
- ✅ **Sistema de Detección Física**: Validación de antenas con return loss
- ✅ **Separación de Responsabilidades**: Managers, Components, Core bien organizados
- ⏳ **Exportación de Datos**: Reportes y análisis (próximamente)
- ⏳ **Integración Cloud**: Firebase para datos en tiempo real (próximamente)

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.10+
- Lector RFID YR8900
- 1-8 Antenas RFID
- Sistema operativo: Windows / Linux / macOS

### Instalación

**Opción 1: Setup Automático (Recomendado)**

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/rfid-athletics-timer.git
cd rfid-athletics-timer

# Ejecutar script de setup (Linux/macOS)
./setup.sh
```

**Opción 2: Instalación Manual**

```bash
# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Ejecutar Aplicación

```bash
python main.py
```

### Primera Ejecución (AutoWizard)

El AutoWizard se ejecuta automáticamente y configura todo en <5 segundos:

```
┌─────────────────────────────────────┐
│  🔌 Auto-Conexión (0.5s)            │
│  ✓ Conectando a 192.168.0.178:4001 │
│  ✓ Firmware v2.1 detectado          │
│  → Avanza automáticamente           │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  📡 Auto-Detección (2s)             │
│  ✓ Puerto 2: Conectada (15 dB)     │
│  ✓ Puerto 3: Conectada (18 dB)     │
│  ✓ Puerto 6: Conectada (20 dB)     │
│  → Avanza automáticamente           │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  ⚙️ Configuración de Roles          │
│  Usuario asigna roles a antenas     │
│  Puerto 2: [✓] Largada              │
│  Puerto 3: [✓] Checkpoint           │
│  Puerto 6: [✓] Meta                 │
└─────────────────────────────────────┘
         ↓
    🎉 ¡Listo en ~5 segundos!
```

Solo se detiene si hay problemas (sin conexión o sin antenas).

## 📖 Documentación

### Arquitectura del Proyecto (v1.1 - Refactorizada)

```
rfid-athletics-timer/
├── main.py                    # Entry point + carga de configuración
├── timing_system_config.json  # Configuración guardada (auto-generado)
├── src/
│   ├── gui/                   # Interfaz gráfica
│   │   ├── main_window.py                (150 líneas) - Coordinación principal
│   │   │
│   │   ├── managers/          # 🆕 Gestores especializados
│   │   │   ├── __init__.py
│   │   │   ├── antenna_manager.py        (80 líneas)  - Gestión de antenas
│   │   │   └── tab_manager.py            (100 líneas) - Gestión de tabs
│   │   │
│   │   ├── components/        # 🆕 Componentes UI reutilizables
│   │   │   ├── __init__.py
│   │   │   └── scan_thread.py            (80 líneas)  - Thread de scanning
│   │   │
│   │   ├── tabs/              # Tabs de la interfaz
│   │   │   ├── __init__.py
│   │   │   ├── base_tab.py               # Clase base
│   │   │   ├── detection_tab.py          (200 líneas) - Tab de detección ✅
│   │   │   └── configuration_tab.py      # Tab de configuración
│   │   │
│   │   ├── widgets/           # Widgets especializados
│   │   │   ├── event_config_widget.py
│   │   │   └── race_monitoring_widget.py
│   │   │
│   │   └── wizard/            # Wizard de configuración
│   │       ├── auto_wizard.py            # AutoWizard automático ✅
│   │       ├── configuration_wizard.py   # Wizard completo
│   │       ├── connection_page.py
│   │       ├── antenna_detection_page.py
│   │       ├── antenna_config_page.py
│   │       └── summary_page.py
│   │
│   ├── core/                  # 🆕 Lógica de negocio pura
│   │   ├── __init__.py
│   │   ├── advanced_scanner.py           # Scanner RFID
│   │   ├── tag_parser.py                 # Parser de tags
│   │   ├── tag_processor.py              (150 líneas) - Procesamiento ✅
│   │   ├── event_manager.py              # Gestión de eventos
│   │   ├── race_config.py                # Configuración
│   │   └── integrated_race_tracker.py    # Tracking de carreras
│   │
│   ├── hardware/              # Interfaz con hardware
│   │   ├── __init__.py
│   │   ├── yr8900_protocol.py            # Protocolo YR8900
│   │   ├── antenna_detection.py          # Detección física
│   │   └── reader_manager.py             # Gestor de alto nivel
│   │
│   ├── utils/                 # Utilidades compartidas
│   │   ├── __init__.py
│   │   └── signals.py                    # Sistema de señales
│   │
│   └── config/                # Configuración del sistema
│       ├── __init__.py
│       └── system_config.py              # Clases de configuración
│
├── docs/                      # Documentación adicional
├── tests/                     # Tests unitarios
│   └── test_multiantena.py
├── requirements.txt           # Dependencias
└── README.md                  # Este archivo
```

### 🏗️ Arquitectura de Capas (v1.1)

```
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                     │
│  gui/                                                        │
│  ├── main_window.py        (Coordinación)                   │
│  ├── tabs/                 (Pestañas de UI)                 │
│  ├── widgets/              (Componentes visuales)           │
│  └── wizard/               (Configuración inicial)          │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                   CAPA DE GESTIÓN                           │
│  gui/managers/                                               │
│  ├── antenna_manager.py    (Lógica de antenas)             │
│  └── tab_manager.py        (Gestión de tabs)               │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                  CAPA DE NEGOCIO                            │
│  core/                                                       │
│  ├── tag_processor.py      (Procesamiento de tags)         │
│  ├── advanced_scanner.py   (Lógica de scanning)            │
│  ├── event_manager.py      (Gestión de eventos)            │
│  └── race_tracker.py       (Tracking de carreras)          │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                   CAPA DE HARDWARE                          │
│  hardware/                                                   │
│  ├── yr8900_protocol.py    (Protocolo bajo nivel)          │
│  ├── antenna_detection.py  (Detección física)              │
│  └── reader_manager.py     (Gestor de lector)              │
└─────────────────────────────────────────────────────────────┘
```

### 📊 Flujo de Datos: Wizard → MainWindow → Tabs

```
┌─────────────────────────────────────────────────────────┐
│ 1. Usuario ejecuta: python main.py                     │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│ 2. main.py                                              │
│    - load_config() desde timing_system_config.json     │
│    - Normaliza keys: "2" → 2 (string → int)            │
│    - Si no existe config → AutoWizard                   │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│ 3. AutoWizard (solo si no hay config)                  │
│    - Auto-conecta al lector (0.5s)                     │
│    - Auto-detecta antenas físicas (2s)                 │
│    - Usuario asigna roles                              │
│    - Genera config con keys INT: {2: {...}, 3...}     │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│ 4. MainWindow.__init__(wizard_config)                  │
│    - _normalize_config(): keys como int               │
│    - AntennaManager(config)                            │
│    - setup_ui() → TabManager                           │
│    - setup_scanner(): conecta al lector                │
│    - apply_config() → TabManager.apply_config()        │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│ 5. TabManager.apply_config_to_all_tabs()               │
│    - detection_tab.update_antenna_roles_from_config()  │
│    - config_tab.load_configuration()                   │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│ 6. DetectionTab                                         │
│    - Recibe: {2: {start:true}, 6: {finish:true}}      │
│    - Actualiza antenna_roles internamente              │
│    - Muestra UI: "Puerto 2: Largada (🟢)"            │
│    - Crea TagProcessor(antenna_roles)                  │
│    - Al detectar tag → TagProcessor.process_tag()      │
└─────────────────────────────────────────────────────────┘
```

### 🔄 Separación de Responsabilidades (v1.1)

#### **main_window.py** (150 líneas)
- ✅ Coordinación de alto nivel
- ✅ Setup UI básica (tabs, status bar)
- ✅ Configuración de scanner
- ❌ NO gestiona antenas directamente → AntennaManager
- ❌ NO crea tabs directamente → TabManager

#### **AntennaManager** (80 líneas)
- ✅ `get_antenna_config(port)` - Config completa
- ✅ `get_antenna_roles(port)` - Lista de roles
- ✅ `get_antenna_name(port)` - Nombre personalizado
- ✅ `get_enabled_antennas()` - Puertos activos
- ✅ Validación y normalización de config

#### **TabManager** (100 líneas)
- ✅ `create_all_tabs()` - Crear todos los tabs
- ✅ `apply_config_to_all_tabs()` - Propagar config
- ✅ `get_tab(name)` - Acceso a tabs específicos
- ✅ Coordina: DetectionTab, ConfigTab, EventTab, RaceTab

#### **TagProcessor** (150 líneas)
- ✅ `process_tag(tag_info)` - Procesar detección
- ✅ `format_role_text(roles)` - Formateo para UI
- ✅ `get_color_code_for_roles()` - Colores
- ✅ Emite señales según roles
- ✅ **Sin dependencias de PyQt** - Lógica pura

#### **ScanThread** (80 líneas)
- ✅ Scanning en background
- ✅ Rota entre antenas disponibles
- ✅ Emite señales de tags detectados
- ✅ Manejo de errores

#### **DetectionTab** (200 líneas)
- ✅ UI de detección
- ✅ Tabla de detecciones
- ✅ Coordina ScanThread y TagProcessor
- ❌ NO procesa tags directamente → TagProcessor
- ❌ NO hace scanning directamente → ScanThread

### Guías Disponibles

- [📘 Guía de Refactorización](docs/Refactoring_guide.md) - Arquitectura v1.1
- [🔗 Guía de Integración](docs/Integration_guide.md) - Wizard → Scanner → MainWindow
- [🧪 Testing Multi-Antena](tests/test_multiantena.py) - Test de múltiples antenas

## 💡 Uso Básico

### 1. Configuración Inicial (AutoWizard)

El AutoWizard automáticamente:
- ✅ Conecta al lector RFID (sin intervención)
- ✅ Detecta antenas físicas (sin intervención)
- 👤 Usuario asigna roles a cada antena
- ✅ Guarda configuración para futuras sesiones

**Tiempo total: ~5 segundos** (3s automático + 2s usuario)

### 2. Detección de Chips

Una vez configurado, el sistema detecta automáticamente:

```
[12:34:56.789] Tag 8599 → Puerto 2 (🟢 Largada)
[12:35:01.234] Tag 8599 → Puerto 3 (🔵 Checkpoint)
[12:35:15.678] Tag 8599 → Puerto 6 (🏁 Meta)
```

Cada detección incluye:
- **Timestamp preciso** (milisegundos)
- **Número de tag** (EPC parseado)
- **Puerto/Antena** donde fue detectado
- **Rol(es)** (Largada/Meta/Checkpoint - puede ser múltiple)

### 3. Sistema Multi-Antena

El scanner rota automáticamente entre todas las antenas configuradas:

```python
# Configuración desde wizard
antennas = [2, 3, 4, 6]  # Puertos detectados
roles = {
    2: ['start'],              # Solo Largada
    3: ['checkpoint'],         # Solo Checkpoint 1
    4: ['checkpoint'],         # Solo Checkpoint 2
    6: ['start', 'finish']     # Largada Y Meta (circuito cerrado)
}

# El sistema escanea en bucle:
# Puerto 2 → Puerto 3 → Puerto 4 → Puerto 6 → Puerto 2...
```

**Ventajas:**
- ✅ Detección simultánea en múltiples puntos
- ✅ No se pierden tags entre rotaciones (scan < 300ms/antena)
- ✅ Identificación automática del punto de paso
- ✅ Tracking completo del recorrido del participante
- ✅ Soporte para roles múltiples por antena

### 4. Roles Múltiples por Antena

Una antena puede tener múltiples roles simultáneamente:

```python
# Ejemplo: Circuito cerrado (largada = meta)
antena_6 = {
    'name': 'Arco Principal',
    'start': True,      # ✅ Es largada
    'finish': True,     # ✅ Es meta
    'checkpoint': False
}

# Al detectar un tag en este puerto:
# - Se emite señal start_detected
# - Se emite señal finish_detected
# - Se muestra: "🟢 Largada + 🏁 Meta"
```

## 🛠️ Configuración Avanzada

### Configuración de Antenas

El sistema soporta múltiples setups:

**Setup Simple (2 antenas):**
```
Puerto 2: Largada
Puerto 6: Meta
```

**Circuito con Checkpoints:**
```
Puerto 2: Largada
Puerto 3: Checkpoint 1
Puerto 4: Checkpoint 2  
Puerto 6: Meta
```

**Arco de Meta (múltiples antenas):**
```
Puertos 3,4,5,6: Todas como Meta
(aumenta área de cobertura)
```

**Circuito Cerrado (largada = meta):**
```
Puerto 2: Largada + Meta
Puertos 3,4,5: Checkpoints (vueltas)
```

### Archivo de Configuración

La configuración se guarda automáticamente en `timing_system_config.json`:

```json
{
  "connection": {
    "host": "192.168.0.178",
    "port": 4001,
    "verified": true
  },
  "power_dbm": 30,
  "antennas": {
    "2": {
      "enabled": true,
      "name": "Largada",
      "start": true,
      "finish": false,
      "checkpoint": false,
      "functions": ["largada"]
    },
    "3": {
      "enabled": true,
      "name": "Checkpoint 1",
      "start": false,
      "finish": false,
      "checkpoint": true,
      "functions": ["checkpoint"]
    },
    "6": {
      "enabled": true,
      "name": "Meta",
      "start": false,
      "finish": true,
      "checkpoint": false,
      "functions": ["llegada"]
    }
  }
}
```

**⚠️ Nota Importante:** El sistema normaliza automáticamente las keys al cargar:
- Keys en JSON pueden ser strings: `"2"`, `"3"`, `"6"`
- Se convierten a int internamente: `2`, `3`, `6`
- Esto asegura compatibilidad y evita bugs de comparación

## 🧪 Testing

### Test de Múltiples Antenas

```bash
python tests/test_multiantena.py
```

### Tests Unitarios

```bash
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=src tests/

# Test específico
pytest tests/test_scanner.py -v
```

## 🐛 Debugging

### Modo Verbose

```bash
python main.py --verbose
```

### Verificar Logs

```bash
# Ver logs en tiempo real
tail -f logs/app.log

# Seguir flujo de configuración
tail -f logs/app.log | grep -E "📡|✅|🔄|🔥"
```

### Problemas Comunes

**Roles no se muestran:**
```bash
# Verificar normalización de tipos
python -c "import json; config = json.load(open('timing_system_config.json')); 
           print('Keys:', list(config['antennas'].keys()));
           print('Tipos:', [type(k) for k in config['antennas'].keys()])"
```

## 🤝 Contribuir

### Convenciones de Código

- Python 3.10+ con type hints
- PEP 8 para estilo
- Docstrings en español
- Separación de responsabilidades
- Tests para nuevas funcionalidades

### Estructura para Nuevas Funcionalidades

```
¿Dónde agregar código nuevo?

Lógica de negocio pura    → src/core/
Componentes UI reutiliz.  → src/gui/components/
Gestores especializados   → src/gui/managers/
Nuevo tab de interfaz     → src/gui/tabs/
Widget complejo           → src/gui/widgets/
```

## 📋 Roadmap

### v1.1 (Completado) ✅
- ✅ AutoWizard con auto-conexión y detección
- ✅ Refactorización completa de arquitectura
- ✅ AntennaManager para gestión centralizada
- ✅ TabManager para gestión de tabs
- ✅ TagProcessor como lógica pura
- ✅ ScanThread como componente reutilizable
- ✅ Separación clara: managers/components/core
- ✅ detection_tab.py reducido 430 → 200 líneas
- ✅ main_window.py reducido 330 → 150 líneas

### v1.2 (Próximo)
- [ ] Race tracking completo por categoría
- [ ] Gestión de múltiples categorías simultáneas
- [ ] Cálculo automático de splits
- [ ] Detección de vueltas en circuitos
- [ ] Exportación de datos (CSV, Excel, PDF)
- [ ] Reportes automáticos con estadísticas

### v1.3 (Futuro)
- [ ] Panel de resultados en vivo
- [ ] Modo kiosko para pantallas públicas
- [ ] Impresión de diplomas
- [ ] Backup automático de datos

### v2.0 (Visión)
- [ ] Integración Firebase
- [ ] App móvil para resultados en vivo
- [ ] Panel web para organizadores
- [ ] API REST para integraciones
- [ ] Análisis estadístico avanzado

## 🔧 Mantenimiento

### Métricas de Calidad del Código

| Métrica | v1.0 | v1.1 | Mejora |
|---------|------|------|--------|
| Archivo más grande | 430 líneas | 200 líneas | **-53%** |
| Líneas en main_window | 330 líneas | 150 líneas | **-55%** |
| Módulos especializados | 0 | 5 | **+5** |
| Separación responsabilidades | ⚠️ Media | ✅ Alta | **✅** |
| Testeable | ⚠️ Difícil | ✅ Fácil | **✅** |

### Principios de Diseño (v1.1)

1. **Single Responsibility Principle** ✅
   - Cada clase/módulo tiene una responsabilidad
   
2. **Separation of Concerns** ✅
   - UI separada de lógica de negocio
   - Lógica de negocio sin dependencias de PyQt

3. **Dependency Injection** ✅
   - Managers reciben dependencias por constructor
   - Fácil testear con mocks

4. **Composition over Inheritance** ✅
   - MainWindow usa managers, no hereda todo

## 📄 Licencia

Este proyecto está bajo la licencia MIT - ver [LICENSE](LICENSE) para detalles.

## 👥 Equipo

- **Desarrollo Principal**: [Tu Nombre]
- **Arquitectura y Refactorización**: Claude (Anthropic)
- **Testing**: [Colaboradores]

## 🙏 Agradecimientos

- Comunidad PyQt6
- Fabricantes del lector YR8900
- Todos los contribuidores
- Organizadores de eventos deportivos que probaron el sistema

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/rfid-athletics-timer/issues)
- **Discusiones**: [GitHub Discussions](https://github.com/tu-usuario/rfid-athletics-timer/discussions)
- **Email**: soporte@example.com
- **Documentación**: [Wiki](https://github.com/tu-usuario/rfid-athletics-timer/wiki)

## 🔗 Enlaces Útiles

- [Manual YR8900](docs/yr8900_manual.pdf)
- [Protocolo RFID](docs/rfid_protocol.md)
- [Guía de Instalación Antenas](docs/antenna_setup.md)
- [FAQ](docs/FAQ.md)
- [Changelog](CHANGELOG.md)

---

## 📊 Estado del Proyecto

**Estado**: 🟢 En Desarrollo Activo

**Última Actualización**: Octubre 2025

**Versión**: 1.1.0

**Tested con**:
- ✅ YR8900 Firmware v6.9
- ✅ 4-8 antenas simultáneas
- ✅ Hasta 50 tags detectados
- ✅ Windows 10/11, Ubuntu 22.04, macOS 14+
- ✅ Roles múltiples por antena
- ✅ Configuración persistente
- ✅ Normalización automática de datos
- ✅ Arquitectura refactorizada

**Últimos Cambios (v1.1.0)**:
- 🎉 **Refactorización completa de arquitectura**
- ✅ AutoWizard con conexión y detección automática
- ✅ AntennaManager para gestión centralizada
- ✅ TabManager para creación de tabs
- ✅ TagProcessor como lógica pura (sin PyQt)
- ✅ ScanThread como componente reutilizable
- ✅ detection_tab.py: 430 → 200 líneas (-53%)
- ✅ main_window.py: 330 → 150 líneas (-55%)
- ✅ Nueva estructura: managers/, components/, core/
- 📚 README completamente actualizado

---

**¿Necesitas ayuda?** Abre un issue o consulta la [documentación](docs/).

**¿Encontraste un bug?** Repórtalo en [GitHub Issues](https://github.com/tu-usuario/rfid-athletics-timer/issues).

**¿Quieres contribuir?** Lee [CONTRIBUTING.md](CONTRIBUTING.md) (próximamente).