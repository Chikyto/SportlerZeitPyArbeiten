# Guía de Refactorización - RFID Athletics Timer

## 🎯 Objetivo

Convertir el código monolítico `tabbed_gui.py` en una arquitectura modular, escalable y mantenible.

## 📁 Nueva Estructura

```
src/
├── core/                           # Lógica de negocio (EXISTENTE)
│   ├── advanced_scanner.py         # Scanner RFID
│   ├── event_manager.py            # Gestión de eventos
│   ├── integrated_race_tracker.py  # Tracking de carreras
│   └── race_config.py              # Configuración
│
├── gui/
│   ├── main_window.py             # ✨ NUEVO: MainWindow refactorizado
│   │
│   ├── wizard/                     # Wizard existente (sin cambios)
│   │   ├── configuration_wizard.py
│   │   ├── antenna_config_page.py
│   │   ├── antenna_detection_page.py
│   │   └── connection_page.py
│   │
│   ├── tabs/                       # ✨ NUEVO: Tabs modulares
│   │   ├── __init__.py
│   │   ├── base_tab.py            # Clase base
│   │   ├── connection_tab.py      # Tab conexión RFID
│   │   ├── detection_tab.py       # Tab detección chips
│   │   ├── antenna_config_tab.py  # Tab config antenas
│   │   ├── event_config_tab.py    # Tab gestión eventos
│   │   ├── competition_tab.py     # Tab competencia
│   │   └── database_tab.py        # Tab base de datos
│   │
│   └── widgets/                    # Widgets existentes (sin cambios)
│       ├── antenna_config_widget.py
│       ├── event_config_widget.py
│       └── race_monitoring_widget.py
│
├── utils/                          # ✨ NUEVO: Utilidades
│   ├── __init__.py
│   ├── signals.py                 # Sistema de señales centralizado
│   └── logger.py                  # Sistema de logging
│
└── main.py                        # ✨ NUEVO: Entry point único
```

## 🔄 Plan de Migración

### Fase 1: Crear Infraestructura Base ✅
- [x] `utils/signals.py` - Sistema de señales
- [x] `gui/tabs/base_tab.py` - Clase base para tabs
- [x] `gui/tabs/__init__.py` - Módulo de tabs

### Fase 2: Migrar Tabs Individuales ✅
- [x] `gui/tabs/connection_tab.py` - Extraído de `tabbed_gui.py`
- [x] `gui/tabs/detection_tab.py` - Extraído de `tabbed_gui.py`
- [ ] Los demás tabs usan widgets existentes directamente

### Fase 3: Crear MainWindow Modular ✅
- [x] `gui/main_window.py` - Orquestador principal
- [x] Integración con sistema de señales
- [x] Gestión del ciclo de vida

### Fase 4: Integrar con Wizard ✅
- [x] `main.py` - Entry point que conecta wizard → app
- [x] Pasar configuración del wizard a MainWindow
- [x] Auto-conexión si wizard verificó hardware

### Fase 5: Testing y Limpieza
- [ ] Probar flujo completo: wizard → app
- [ ] Verificar todas las funcionalidades
- [ ] Eliminar `tabbed_gui.py` (obsoleto)

## 🎨 Arquitectura

### Principios de Diseño

1. **Separación de Responsabilidades**
   - `MainWindow`: Orquestación y layout
   - `Tabs`: UI y lógica específica de cada sección
   - `Core`: Lógica de negocio pura
   - `Utils`: Funcionalidad compartida

2. **Comunicación vía Señales**
   - Singleton `AppSignals` para comunicación desacoplada
   - No hay referencias directas entre tabs
   - Fácil extensión y testing

3. **Modularidad**
   - Cada tab es independiente
   - Widgets reutilizables
   - Fácil agregar nuevas funcionalidades

### Flujo de Datos

```
Wizard → main.py → MainWindow
                      ↓
            ┌─────────┴─────────┐
            ↓                   ↓
         Tabs                Widgets
            ↓                   ↓
        AppSignals ←→ Core Components
```

## 🚀 Cómo Usar

### Ejecutar la Aplicación

```bash
# Desde la raíz del proyecto
python -m src.main

# O si tienes un script de entrada
python main.py
```

### Desarrollo de Nuevos Tabs

```python
# gui/tabs/my_new_tab.py
from .base_tab import BaseTab
from PyQt6.QtWidgets import QLabel

class MyNewTab(BaseTab):
    def setup_ui(self):
        self.layout.addWidget(QLabel("Mi nuevo tab!"))
    
    def connect_signals(self):
        self.signals.some_signal.connect(self.on_some_event)
    
    def on_some_event(self):
        self.log("Evento recibido!")
```

Agregar al `MainWindow`:
```python
def create_tabs(self):
    # ... otros tabs
    self.my_tab = MyNewTab()
    self.tab_widget.addTab(self.my_tab, "Mi Tab")
```

## 🔧 Próximos Pasos

1. **Implementar tabs restantes** usando widgets existentes
2. **Sistema de logging mejorado** (`utils/logger.py`)
3. **Persistencia de configuración** (guardar/cargar settings)
4. **Testing unitario** para cada componente
5. **Integración Firebase** (tab de base de datos)

## 📝 Notas de Implementación

### Cambios Respecto al Código Original

- **Eliminado código duplicado** (setup_competition_tab aparecía 2 veces)
- **Desacoplamiento**: tabs no conocen otros tabs
- **Señales centralizadas**: toda comunicación vía `AppSignals`
- **Inicialización consistente**: race_tracker se crea cuando se inicia categoría
- **Mejor manejo de estado**: cada componente gestiona su propio estado

### Compatibilidad

- ✅ Mantiene compatibilidad con widgets existentes
- ✅ El wizard sigue funcionando igual
- ✅ Core components sin cambios
- ✅ Mismas funcionalidades, mejor arquitectura

## 🐛 Debugging

Para verificar conexiones del sistema:
```python
# En MainWindow
state = main_window.get_current_state()
print(state)
```

## 📚 Referencias

- PyQt6 Signals: https://doc.qt.io/qtforpython-6/tutorials/basictutorial/signals_and_slots.html
- Architecture Patterns: Clean Architecture, MVC