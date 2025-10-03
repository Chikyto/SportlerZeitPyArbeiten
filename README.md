# RFID Athletics Timer

Sistema profesional de cronometraje deportivo con tecnología RFID para carreras de atletismo, usando el lector YR8900.

## 🎯 Características Principales

- ✅ **Wizard de Configuración Automático**: Auto-detección de hardware y conexión en <1 minuto
- ✅ **Multi-Antena**: Soporte para hasta 8 antenas con roles configurables
- ✅ **Gestión de Eventos**: Múltiples categorías y carreras simultáneas
- ✅ **Tracking en Tiempo Real**: Monitoreo de participantes con splits y tiempos
- ✅ **Arquitectura Modular**: Código limpio, mantenible y escalable
- ⏳ **Exportación de Datos**: Reportes y análisis (próximamente)
- ⏳ **Integración Cloud**: Firebase para datos en tiempo real (próximamente)

## 🚀 Inicio Rápido

### Requisitos Previos

- Python 3.10+
- Lector RFID YR8900
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

Al iniciar, el wizard automático:
1. Se conecta al lector RFID (2 segundos)
2. Detecta antenas conectadas (5 segundos)
3. Te pide configurar roles de antenas (30 segundos)
4. Abre la aplicación lista para usar

## 📖 Documentación

### Estructura del Proyecto

```
rfid-athletics-timer/
├── src/
│   ├── core/              # Lógica de negocio
│   ├── gui/               # Interfaz gráfica
│   │   ├── wizard/        # Wizard de configuración
│   │   ├── tabs/          # Tabs modulares
│   │   └── widgets/       # Widgets especializados
│   ├── utils/             # Utilidades compartidas
│   ├── config/            # Configuración
│   └── hardware/          # Interfaz con hardware
├── docs/                  # Documentación adicional
├── tests/                 # Tests unitarios
├── main.py               # Entry point
├── requirements.txt      # Dependencias
└── README.md             # Este archivo
```

### Guías Disponibles

- [Guía de Refactorización](REFACTORING_GUIDE.md) - Arquitectura y diseño
- [Pasos de Implementación](IMPLEMENTATION_STEPS.md) - Guía paso a paso

## 💡 Uso Básico

### 1. Configuración Inicial (Wizard)

El wizard se ejecuta automáticamente la primera vez:

```
┌─────────────────────────────────┐
│  Auto-Conexión                  │
│  ✓ Conectando a lector...       │
│  ✓ Firmware v2.1 detectado      │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│  Auto-Detección de Antenas      │
│  ✓ Puerto 3: Conectada          │
│  ✓ Puerto 7: Conectada          │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│  Configuración de Roles         │
│  □ Puerto 3: [✓] Largada        │
│  □ Puerto 7: [✓] Meta           │
└─────────────────────────────────┘
```

### 2. Gestión de Eventos

```python
# Crear categoría
event_manager.create_category(
    category_id="100m_varones",
    name="100m Varones",
    distance=100
)

# Registrar participante
event_manager.register_participant(
    chip_number="E2001234567890123456",
    category_id="100m_varones",
    name="Juan Pérez",
    bib_number="101"
)

# Iniciar categoría
event_manager.start_category("100m_varones")
```

### 3. Detección de Chips

La aplicación detecta automáticamente cuando un chip cruza una antena configurada:

```python
# Detección automática
tag = {
    'number': 'E2001234567890123456',
    'antenna': 2,  # Puerto 3 (índice 2)
    'timestamp': datetime.now()
}

# El sistema procesa automáticamente:
# - Identifica participante
# - Registra tiempo
# - Actualiza estado (En Curso / Finalizado)
# - Muestra en monitor de carrera
```

## 🛠️ Configuración Avanzada

### Configuración de Antenas

El sistema soporta múltiples setups:

**Setup Simple (2 antenas):**
- Antena 1: Largada
- Antena 2: Meta

**Circuito Cerrado:**
- Antena 1: Largada + Meta
- Antenas 2-4: Checkpoints

**Arco de Meta (4 antenas):**
- Antenas 1-4: Todas como Meta

### Archivo de Configuración

La configuración se guarda automáticamente en `timing_system_config.json`:

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
    "6": {
      "enabled": true,
      "name": "Meta",
      "start": false,
      "finish": true,
      "checkpoint": false
    }
  }
}
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con coverage
pytest --cov=src tests/

# Test específico
pytest tests/test_scanner.py
```

## 🐛 Debugging

### Modo Verbose

```bash
python main.py --verbose
```

### Logs

Los logs se guardan en `logs/app.log`:

```bash
tail -f logs/app.log
```

### Test sin Hardware

```bash
python quick_test_main.py
```

## 🤝 Contribuir

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

### Convenciones de Código

- Python 3.10+ con type hints
- PEP 8 para estilo
- Docstrings en español
- Tests para nuevas funcionalidades

## 📋 Roadmap

### v1.0 (Actual)
- ✅ Wizard automático
- ✅ Detección multi-antena
- ✅ Configuración modular
- ⏳ Sistema de detección integrado

### v1.1 (Próximo)
- Race tracking completo
- Gestión de múltiples categorías
- Exportación de datos (CSV, Excel)
- Reportes automáticos

### v2.0 (Futuro)
- Integración Firebase
- App móvil para resultados en vivo
- Panel web para organizadores
- Análisis estadístico avanzado

## 📄 Licencia

Este proyecto está bajo la licencia MIT - ver [LICENSE](LICENSE) para detalles.

## 👥 Equipo

- **Desarrollo Principal**: [Tu Nombre]
- **Arquitectura**: Claude (Anthropic)
- **Testing**: [Colaboradores]

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/rfid-athletics-timer/issues)
- **Email**: soporte@example.com
- **Documentación**: [Wiki](https://github.com/tu-usuario/rfid-athletics-timer/wiki)

## 🙏 Agradecimientos

- Comunidad PyQt6
- Fabricantes del lector YR8900
- Todos los contribuidores

---

**Estado del Proyecto**: 🟢 En Desarrollo Activo

**Última Actualización**: Octubre 2025