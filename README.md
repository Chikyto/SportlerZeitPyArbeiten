# RFID Athletics Timer

Sistema profesional de cronometraje deportivo con tecnología RFID para carreras de atletismo, usando el lector YR8900.

## 🎯 Características Principales

- ✅ **Wizard de Configuración Automático**: Auto-detección de hardware y conexión en <1 minuto
- ✅ **Multi-Antena Funcional**: Soporte para hasta 8 antenas con rotación automática
- ✅ **Detección por Roles**: Antenas configurables como Largada/Meta/Checkpoint
- ✅ **Roles Múltiples por Antena**: Una antena puede ser Largada+Meta simultáneamente
- ✅ **Tracking en Tiempo Real**: Monitoreo de participantes con splits y tiempos
- ✅ **Persistencia de Configuración**: Guarda y carga configuración automáticamente
- ✅ **Arquitectura Modular**: Código limpio, mantenible y escalable
- ✅ **Sistema de Detección Física**: Validación de antenas con return loss
- ✅ **Normalización Automática**: Manejo correcto de tipos de datos en configuración
- ⏳ **Exportación de Datos**: Reportes y análisis (próximamente)
- ⏳ **Integración Cloud**: Firebase para datos en tiempo real (próximamente)

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.10+
- Lector RFID YR8900
- 1-8 Antenas RFID
- Sistema operativo: Windows / Linux / macOS

### Instalación

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/rfid-athletics-timer.git
cd rfid-athletics-timer

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### Ejecutar Aplicación

```bash
python main.py
```

### Primera Ejecución (Con Wizard)

Al iniciar por primera vez, el wizard automático te guiará:

```
┌─────────────────────────────────────┐
│  🔌 Paso 1: Conexión                │
│  ✓ Conectando a 192.168.0.178:4001 │
│  ✓ Firmware v2.1 detectado          │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  📡 Paso 2: Detección de Antenas    │
│  ✓ Puerto 2: Conectada (15 dB)     │
│  ✓ Puerto 3: Conectada (18 dB)     │
│  ✓ Puerto 4: Conectada (16 dB)     │
│  ✓ Puerto 6: Conectada (20 dB)     │
│  Total: 4/8 antenas detectadas      │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│  ⚙️ Paso 3: Configuración de Roles  │
│  ☐ Puerto 2: [✓] Largada            │
│  ☐ Puerto 3: [✓] Checkpoint         │
│  ☐ Puerto 4: [✓] Checkpoint         │
│  ☐ Puerto 6: [✓] Meta               │
└─────────────────────────────────────┘
         ↓
    🎉 ¡Listo para usar!
```

### Ejecuciones Posteriores (Con Configuración Guardada)

```
┌────────────────────────────────────────┐
│ Se encontró una configuración          │
│ existente:                             │
│                                        │
│ 🔌 Conexión: 192.168.0.178:4001       │
│ 📡 Antenas configuradas: 4             │
│   • Puerto 2: Largada (🟢 Largada)    │
│   • Puerto 3: Checkpoint 1 (🔵 CP)    │
│   • Puerto 4: Checkpoint 2 (🔵 CP)    │
│   • Puerto 6: Meta (🏁 Meta)          │
│                                        │
│ ¿Desea usar esta configuración?       │
│   [Sí]  [No]  [Cancelar]              │
└────────────────────────────────────────┘
```

## 📖 Documentación

### Estructura del Proyecto

```
rfid-athletics-timer/
├── main.py                    # Entry point + carga de configuración
├── timing_system_config.json  # Configuración guardada (auto-generado)
├── src/
│   ├── core/                  # Lógica de negocio
│   │   ├── advanced_scanner.py           # Scanner multi-antena
│   │   ├── tag_parser.py                 # Parser de tags
│   │   ├── event_manager.py              # Gestión de eventos
│   │   ├── race_config.py                # Configuración
│   │   └── integrated_race_tracker.py    # Tracking de carreras
│   ├── hardware/              # Interfaz con hardware
│   │   ├── yr8900_protocol.py            # Protocolo YR8900
│   │   ├── antenna_detection.py          # Detección física
│   │   └── reader_manager.py             # Gestor de alto nivel
│   ├── gui/                   # Interfaz gráfica
│   │   ├── main_window.py                # Ventana principal
│   │   ├── wizard/            # Wizard de configuración
│   │   │   ├── configuration_wizard.py   # Wizard completo
│   │   │   ├── auto_wizard.py            # Wizard automático
│   │   │   ├── connection_page.py        # Página de conexión
│   │   │   ├── antenna_detection_page.py # Detección de antenas
│   │   │   ├── antenna_config_page.py    # Configuración de antenas
│   │   │   └── summary_page.py           # Resumen final
│   │   ├── tabs/              # Tabs modulares
│   │   │   ├── base_tab.py               # Clase base para tabs
│   │   │   ├── detection_tab.py          # Tab de detección
│   │   │   └── configuration_tab.py      # Tab de configuración
│   │   └── widgets/           # Widgets especializados
│   │       ├── event_config_widget.py    # Configuración de eventos
│   │       └── race_monitoring_widget.py # Monitoreo de carreras
│   ├── utils/                 # Utilidades compartidas
│   │   └── signals.py                    # Sistema de señales
│   └── config/                # Configuración del sistema
│       └── system_config.py              # Clases de configuración
├── docs/                      # Documentación adicional
├── tests/                     # Tests unitarios
│   └── test_multiantena.py
├── requirements.txt           # Dependencias
└── README.md                  # Este archivo
```

### Flujo de Datos: Wizard → MainWindow → Tabs

```
┌─────────────────────────────────────────────────────┐
│ 1. Usuario ejecuta: python main.py                 │
└────────────────┬────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│ 2. main.py                                          │
│    - load_config() desde timing_system_config.json │
│    - Normaliza keys: "2" → 2 (string → int)        │
│    - Si no existe config, ejecuta wizard           │
└────────────────┬────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│ 3. ConfigurationWizard / AutoWizard                 │
│    - Detecta antenas físicamente conectadas         │
│    - Usuario asigna roles a cada antena             │
│    - Genera config con keys INT: {2: {...}, 3...}  │
│    - Emite señal: configuration_completed.emit()    │
└────────────────┬────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│ 4. MainWindow.__init__(wizard_config)              │
│    - _normalize_config(): asegura keys como int    │
│    - setup_ui(): crea todos los tabs               │
│    - setup_scanner(): conecta al lector            │
│    - apply_config_to_tabs(): 🔥 CRÍTICO            │
│      ├─ detection_tab.update_antenna_roles...()    │
│      └─ config_tab.load_configuration()            │
└────────────────┬────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────┐
│ 5. DetectionTab                                     │
│    - Recibe: {2: {start:true}, 6: {finish:true}}   │
│    - Actualiza antenna_roles internamente           │
│    - Muestra UI: "Puerto 2: Largada (🟢)"         │
│    - Al detectar tag, usa antenna_roles[port]      │
└─────────────────────────────────────────────────────┘
```

### Guías Disponibles

- [📘 Guía de Refactorización](docs/Refactoring_guide.md) - Arquitectura y diseño
- [🔗 Guía de Integración](docs/Integration_guide.md) - Wizard → Scanner → MainWindow
- [🧪 Testing Multi-Antena](tests/test_multiantena.py) - Test de múltiples antenas

## 💡 Uso Básico

### 1. Configuración Inicial (Wizard)

El wizard se ejecuta automáticamente la primera vez y te permite:
- ✅ Conectar al lector RFID
- ✅ Detectar antenas físicamente conectadas
- ✅ Asignar roles a cada antena (Largada/Meta/Checkpoint)
- ✅ Asignar múltiples roles a una antena (ej: Largada + Meta)
- ✅ Configurar potencia de transmisión
- ✅ Guardar configuración para futuras sesiones

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
    3: ['checkpoint'],          # Solo Checkpoint 1
    4: ['checkpoint'],          # Solo Checkpoint 2
    6: ['start', 'finish']      # Largada Y Meta (circuito cerrado)
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

### 5. Ejemplo de Resultado

```
============================================================
   DETECCIONES EN CARRERA 100M VARONES
============================================================

Tag 8599 - Juan Pérez (#101)
  🟢 12:34:56.789 - Largada (Puerto 2)
  🏁 12:35:06.123 - Meta (Puerto 6)
  ⏱️  Tiempo final: 9.334s

Tag 8575 - María López (#102)
  🟢 12:34:57.012 - Largada (Puerto 2)
  🔵 12:35:02.456 - Checkpoint 1 (Puerto 3)
  🔵 12:35:05.234 - Checkpoint 2 (Puerto 4)
  🏁 12:35:07.890 - Meta (Puerto 6)
  ⏱️  Tiempo final: 10.878s

Total participantes: 15
Finalizados: 15
Promedio: 10.245s
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
      "name": "Meta Principal",
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

### Editar Configuración

Para reconfigurar:

```bash
# Opción 1: Borrar archivo y reiniciar
rm timing_system_config.json
python main.py

# Opción 2: Editar manualmente (cuidado con tipos de datos)
nano timing_system_config.json

# Opción 3: Botón "No" cuando pregunta si usar config existente
python main.py
# → Seleccionar "No" → Ejecuta wizard nuevamente
```

## 🧪 Testing

### Test de Múltiples Antenas

```bash
# Test completo multi-antena
python tests/test_multiantena.py
```

Salida esperada:
```
============================================================
   TEST MULTI-ANTENA YR8900
============================================================

[Paso 1] Test de conexión...
✓ Lector respondiendo correctamente

[Paso 2] Detectando antenas conectadas...
✓ Puerto 2: Conectada (15 dB)
✓ Puerto 3: Conectada (18 dB)
✓ Puerto 4: Conectada (16 dB)
✓ Puerto 6: Conectada (20 dB)

Antenas detectadas: [2, 3, 4, 6]

[Paso 3] Probando cada antena individualmente...
[Acerca tags a cada puerto...]

[Paso 4] Scan continuo multi-antena...
[01] Tag 8599 → Puerto 2 (🟢 Largada)
[02] Tag 8575 → Puerto 3 (🔵 Checkpoint)
[03] Tag 7662 → Puerto 6 (🏁 Meta)

============================================================
   RESUMEN
============================================================
Antenas conectadas: 4
Puertos: [2, 3, 4, 6]
Tags únicos detectados: 7
Total de scans: 22

✓ Test completado exitosamente!
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

### Test sin Hardware

Para desarrollo sin hardware físico:

```bash
python tests/test_mock_scanner.py
```

## 🐛 Debugging

### Modo Verbose

```bash
# Logs detallados
python main.py --verbose

# Solo logs de scanner
python main.py --log-scanner

# Nivel de log específico
python main.py --log-level DEBUG
```

### Verificar Logs

```bash
# Ver logs en tiempo real
tail -f logs/app.log

# Filtrar errores
grep ERROR logs/app.log

# Ver últimas 100 líneas
tail -n 100 logs/app.log

# Seguir flujo de configuración
tail -f logs/app.log | grep -E "📡|✅|🔄|🔥"
```

### Verificar Configuración

```python
import json

# Leer config actual
with open('timing_system_config.json') as f:
    config = json.load(f)
    
print(f"Host: {config['connection']['host']}")
print(f"Antenas: {list(config['antennas'].keys())}")
print(f"Tipos de keys: {[type(k).__name__ for k in config['antennas'].keys()]}")
```

### Problemas Comunes

**No detecta antenas:**
```bash
# 1. Verificar conexiones físicas
# 2. Verificar return loss
python -c "from src.hardware.antenna_detection import *; 
           detector = AntennaDetector(...); 
           detector.scan_all_ports()"

# 3. Reducir umbral de return loss
# En config: "return_loss_threshold": 5  # default: 8
```

**Tags no se leen:**
```bash
# 1. Verificar potencia
python -c "from src.core.advanced_scanner import *;
           s = AdvancedYR8900Scanner();
           s.connect();
           print(s.get_output_power())"

# 2. Aumentar potencia (0-33 dBm)
# En wizard o config: "power_dbm": 30

# 3. Acercar más el tag (< 3 metros)
```

**Lecturas duplicadas:**
```bash
# Ajustar tiempo entre scans
# En detection_tab.py: time.sleep(0.5)  # Aumentar de 0.3
```

**Roles no se muestran:**
```bash
# 1. Verificar que config tiene roles
cat timing_system_config.json | grep -A 5 "antennas"

# 2. Verificar normalización de tipos
python -c "import json; config = json.load(open('timing_system_config.json')); 
           print('Keys:', list(config['antennas'].keys()));
           print('Tipos:', [type(k) for k in config['antennas'].keys()])"

# 3. Ver logs de aplicación de config
tail -f logs/app.log | grep "APLICANDO CONFIGURACIÓN"
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add: nueva característica'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Convenciones de Código

- Python 3.10+ con type hints
- PEP 8 para estilo
- Docstrings en español
- Tests para nuevas funcionalidades
- Commits descriptivos en español

### Estilo de Commits

```
Add: nueva funcionalidad
Fix: corrección de bug
Refactor: refactorización de código
Docs: documentación
Test: nuevos tests
Style: formato de código
```

## 📋 Roadmap

### v1.0 (Completado) ✅
- ✅ Wizard automático
- ✅ Detección multi-antena
- ✅ Configuración modular
- ✅ Sistema multi-antena funcional
- ✅ Detección por roles (largada/meta/checkpoint)
- ✅ Roles múltiples por antena
- ✅ Persistencia de configuración
- ✅ Normalización automática de tipos
- ✅ Integración wizard → scanner → tabs

### v1.1 (En Desarrollo) 🚧
- [ ] Race tracking completo por categoría
- [ ] Gestión de múltiples categorías simultáneas
- [ ] Cálculo automático de splits
- [ ] Detección de vueltas en circuitos
- [ ] Exportación de datos (CSV, Excel, PDF)
- [ ] Reportes automáticos con estadísticas
- [ ] Refactorización de archivos grandes (>300 líneas)

### v1.2 (Planificado)
- [ ] Panel de resultados en vivo
- [ ] Modo kiosko para pantallas públicas
- [ ] Impresión de diplomas
- [ ] Backup automático de datos
- [ ] Sistema de alertas y notificaciones

### v2.0 (Futuro)
- [ ] Integración Firebase
- [ ] App móvil para resultados en vivo
- [ ] Panel web para organizadores
- [ ] API REST para integraciones
- [ ] Análisis estadístico avanzado
- [ ] Machine learning para detección de anomalías

## 🔧 Mantenimiento y Refactorización

### Archivos Candidatos a Refactorizar

Según análisis de código, estos archivos superan las 300 líneas:

| Archivo | Líneas | Prioridad | Plan |
|---------|--------|-----------|------|
| `detection_tab.py` | ~430 | 🔴 Alta | Dividir en: UI, ScanThread, TagProcessor |
| `main_window.py` | ~330 | 🟡 Media | Dividir en: Core, ConfigManager, TabCoordinator |

**Nota:** La refactorización se realizará en v1.1 sin afectar funcionalidad.

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

**Última Actualización**: Octubre 2024

**Versión**: 1.0.1

**Tested con**:
- ✅ YR8900 Firmware v2.1
- ✅ 4-8 antenas simultáneas
- ✅ Hasta 50 tags detectados
- ✅ Windows 10/11, Ubuntu 22.04, macOS 14+
- ✅ Roles múltiples por antena
- ✅ Configuración persistente
- ✅ Normalización automática de datos

**Últimos Cambios (v1.0.1)**:
- 🔥 Fix crítico: Roles ahora se cargan correctamente desde JSON
- ✅ Normalización automática de tipos de datos (string → int)
- ✅ Método `apply_config_to_tabs()` para propagación correcta
- ✅ Soporte para roles múltiples por antena
- ✅ Mejor manejo de configuración guardada
- 📝 README actualizado con nueva arquitectura

---

**¿Necesitas ayuda?** Abre un issue o consulta la [documentación](docs/).

**¿Encontraste un bug?** Repórtalo en [GitHub Issues](https://github.com/tu-usuario/rfid-athletics-timer/issues).

**¿Quieres contribuir?** Lee [CONTRIBUTING.md](CONTRIBUTING.md) (próximamente).