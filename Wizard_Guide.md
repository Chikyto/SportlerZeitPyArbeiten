# Guía de Integración: Wizard → Scanner → MainWindow

## 🎯 Objetivo

Conectar la configuración del wizard con el sistema de scanning multi-antena para que:
1. Las antenas detectadas se usen automáticamente
2. Los roles (largada/meta) filtren detecciones correctamente
3. La configuración persista entre sesiones

---

## 📊 Flujo de Datos

```
1. Wizard
   └─> Detecta antenas físicas (return loss)
   └─> Usuario configura roles
   └─> Guarda timing_system_config.json

2. MainWindow
   └─> Lee timing_system_config.json
   └─> Crea AdvancedScanner con config
   └─> Pasa antenas habilitadas al scanner

3. AdvancedScanner
   └─> Escanea solo antenas configuradas
   └─> Rotación automática multi-antena
   └─> Tags etiquetados con puerto/antena

4. DetectionTab
   └─> Filtra tags por rol (largada/meta)
   └─> Muestra en UI con contexto
```

---

## 🔧 Implementación

### Paso 1: Actualizar `main.py`

```python
#!/usr/bin/env python3
"""
Entry point de la aplicación RFID Athletics Timer
"""

import sys
import json
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication

from src.gui.wizard.configuration_wizard import ConfigurationWizard
from src.gui.main_window import MainWindow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CONFIG_FILE = Path("timing_system_config.json")

def load_config():
    """Carga configuración guardada"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando config: {e}")
    return None

def save_config(config):
    """Guarda configuración"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        logger.error(f"Error guardando config: {e}")

def run_wizard():
    """Ejecuta el wizard de configuración"""
    wizard = ConfigurationWizard()
    
    if wizard.exec():
        # Wizard completado exitosamente
        config = wizard.get_configuration()
        save_config(config)
        return config
    else:
        # Usuario canceló
        return None

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RFID Athletics Timer")
    
    # Cargar o crear configuración
    config = load_config()
    
    if not config:
        logger.info("No hay configuración. Ejecutando wizard...")
        config = run_wizard()
        
        if not config:
            logger.info("Wizard cancelado. Saliendo...")
            return 0
    
    # Iniciar aplicación principal con configuración
    logger.info("Iniciando aplicación con configuración cargada")
    main_window = MainWindow(wizard_config=config)
    main_window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
```

---

### Paso 2: Actualizar `MainWindow`

**Archivo: `src/gui/main_window.py`**

```python
class MainWindow(QMainWindow):
    def __init__(self, wizard_config=None):
        super().__init__()
        
        self.wizard_config = wizard_config
        self.signals = AppSignals()
        self.scanner = None
        
        self.setWindowTitle("RFID Athletics Timer")
        self.setMinimumSize(1200, 800)
        
        self.setup_ui()
        self.setup_scanner()
        self.connect_signals()
    
    def setup_scanner(self):
        """Configura scanner con datos del wizard"""
        if not self.wizard_config:
            logger.warning("No hay configuración del wizard")
            return
        
        try:
            # Obtener parámetros de conexión
            conn = self.wizard_config.get('connection', {})
            host = conn.get('host', '192.168.0.178')
            port = conn.get('port', 4001)
            
            logger.info(f"Creando scanner: {host}:{port}")
            
            # Crear scanner
            self.scanner = AdvancedYR8900Scanner(host, port)
            
            # Conectar
            if not self.scanner.connect():
                logger.error("No se pudo conectar al scanner")
                return
            
            # Configurar antenas habilitadas del wizard
            antennas_config = self.wizard_config.get('antennas', {})
            enabled_ports = [
                int(port) for port, config in antennas_config.items()
                if config.get('enabled', False)
            ]
            
            logger.info(f"Antenas habilitadas: {enabled_ports}")
            self.scanner.available_antennas = enabled_ports
            
            # Configurar potencia si está en config
            power = self.wizard_config.get('power_dbm')
            if power:
                self.scanner.set_output_power(power)
            
            # Emitir señal de scanner listo
            self.signals.scanner_ready.emit(self.scanner)
            
        except Exception as e:
            logger.error(f"Error configurando scanner: {e}")
    
    def get_antenna_config(self, port: int) -> dict:
        """Obtiene configuración de una antena específica"""
        if not self.wizard_config:
            return {}
        
        antennas = self.wizard_config.get('antennas', {})
        return antennas.get(str(port), {})
    
    def get_antenna_role(self, port: int) -> str:
        """Obtiene el rol de una antena (start/finish/checkpoint)"""
        config = self.get_antenna_config(port)
        
        if config.get('start'):
            return 'start'
        elif config.get('finish'):
            return 'finish'
        elif config.get('checkpoint'):
            return 'checkpoint'
        
        return 'unknown'
```

---

### Paso 3: Actualizar `DetectionTab`

**Archivo: `src/gui/tabs/detection_tab.py`**

```python
class DetectionTab(BaseTab):
    def __init__(self):
        super().__init__()
        self.scanner = None
        self.scan_thread = None
        self.is_scanning = False
        self.antenna_roles = {}  # {port: role}
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Detección de Chips RFID")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # Información de antenas
        self.antenna_info = QGroupBox("Antenas Configuradas")
        self.antenna_info_layout = QVBoxLayout()
        self.antenna_info.setLayout(self.antenna_info_layout)
        layout.addWidget(self.antenna_info)
        
        # Controles de scan
        controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Iniciar Detección")
        self.start_btn.clicked.connect(self.start_scanning)
        controls_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Detener")
        self.stop_btn.clicked.connect(self.stop_scanning)
        self.stop_btn.setEnabled(False)
        controls_layout.addWidget(self.stop_btn)
        
        layout.addLayout(controls_layout)
        
        # Tabla de detecciones
        self.detections_table = QTableWidget()
        self.detections_table.setColumnCount(5)
        self.detections_table.setHorizontalHeaderLabels([
            "Hora", "Tag", "Puerto", "Rol", "EPC"
        ])
        layout.addWidget(self.detections_table)
        
        # Estadísticas
        self.stats_label = QLabel("Tags detectados: 0")
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)
    
    def connect_signals(self):
        """Conecta señales del sistema"""
        # Cuando el scanner esté listo
        self.signals.scanner_ready.connect(self.on_scanner_ready)
        
        # Tags detectados
        self.signals.tag_detected.connect(self.on_tag_detected)
    
    def on_scanner_ready(self, scanner):
        """Callback cuando el scanner está listo"""
        self.scanner = scanner
        self.update_antenna_info()
        self.start_btn.setEnabled(True)
        self.log("Scanner listo para detección")
    
    def update_antenna_info(self):
        """Actualiza información de antenas configuradas"""
        if not self.scanner:
            return
        
        # Limpiar layout anterior
        while self.antenna_info_layout.count():
            child = self.antenna_info_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Obtener config de MainWindow
        main_window = self.parent()
        while main_window and not isinstance(main_window, MainWindow):
            main_window = main_window.parent()
        
        if not main_window:
            return
        
        # Mostrar cada antena configurada
        for port in self.scanner.available_antennas:
            role = main_window.get_antenna_role(port)
            config = main_window.get_antenna_config(port)
            name = config.get('name', f'Antena {port}')
            
            # Guardar rol para filtrado posterior
            self.antenna_roles[port] = role
            
            # Crear label con info
            role_emoji = {
                'start': '🟢',
                'finish': '🏁',
                'checkpoint': '🔵'
            }.get(role, '⚪')
            
            info = QLabel(f"{role_emoji} Puerto {port}: {name} ({role})")
            self.antenna_info_layout.addWidget(info)
    
    def start_scanning(self):
        """Inicia detección continua"""
        if not self.scanner:
            self.log("ERROR: Scanner no disponible")
            return
        
        if self.is_scanning:
            return
        
        self.is_scanning = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Crear thread de scanning
        self.scan_thread = ScanThread(self.scanner)
        self.scan_thread.tag_detected.connect(self.on_tag_detected)
        self.scan_thread.start()
        
        self.log("Iniciando detección multi-antena...")
    
    def stop_scanning(self):
        """Detiene detección"""
        if self.scan_thread:
            self.scan_thread.stop()
            self.scan_thread.wait()
            self.scan_thread = None
        
        self.is_scanning = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        self.log("Detección detenida")
    
    def on_tag_detected(self, tag_info):
        """Procesa tag detectado"""
        # Obtener información del tag
        tag_number = tag_info['number']
        port = tag_info.get('antenna', 0)
        timestamp = tag_info['timestamp'].strftime('%H:%M:%S.%f')[:-3]
        epc = tag_info.get('epc_hex', '')
        
        # Determinar rol de la antena
        role = self.antenna_roles.get(port, 'unknown')
        
        # Agregar a la tabla
        row = self.detections_table.rowCount()
        self.detections_table.insertRow(row)
        
        self.detections_table.setItem(row, 0, QTableWidgetItem(timestamp))
        self.detections_table.setItem(row, 1, QTableWidgetItem(tag_number))
        self.detections_table.setItem(row, 2, QTableWidgetItem(str(port)))
        self.detections_table.setItem(row, 3, QTableWidgetItem(role))
        self.detections_table.setItem(row, 4, QTableWidgetItem(epc[:20]))
        
        # Color según rol
        role_colors = {
            'start': QColor(144, 238, 144),  # Verde claro
            'finish': QColor(255, 215, 0),    # Dorado
            'checkpoint': QColor(173, 216, 230)  # Azul claro
        }
        
        color = role_colors.get(role)
        if color:
            for col in range(5):
                self.detections_table.item(row, col).setBackground(color)
        
        # Scroll a la última fila
        self.detections_table.scrollToBottom()
        
        # Actualizar estadísticas
        count = self.detections_table.rowCount()
        self.stats_label.setText(f"Detecciones: {count}")
        
        # Emitir señal según rol
        if role == 'start':
            self.signals.start_detected.emit(tag_number, timestamp)
        elif role == 'finish':
            self.signals.finish_detected.emit(tag_number, timestamp)
        elif role == 'checkpoint':
            self.signals.checkpoint_detected.emit(tag_number, port, timestamp)


class ScanThread(QThread):
    """Thread para scanning continuo sin bloquear UI"""
    tag_detected = pyqtSignal(dict)
    
    def __init__(self, scanner):
        super().__init__()
        self.scanner = scanner
        self.running = False
    
    def run(self):
        """Loop de scanning"""
        self.running = True
        scan_count = 0
        
        while self.running:
            # Rotar entre antenas disponibles
            if not self.scanner.available_antennas:
                time.sleep(1)
                continue
            
            antenna_id = self.scanner.available_antennas[
                scan_count % len(self.scanner.available_antennas)
            ]
            
            # Escanear antena actual
            tags = self.scanner.scan_single_antenna(antenna_id)
            
            # Emitir cada tag detectado
            for tag in tags:
                self.tag_detected.emit(tag)
            
            scan_count += 1
            time.sleep(0.3)  # Pausa entre scans
    
    def stop(self):
        """Detiene el thread"""
        self.running = False
```

---

### Paso 4: Actualizar Señales

**Archivo: `src/utils/signals.py`**

```python
class AppSignals(QObject):
    # Existentes
    connection_status_changed = pyqtSignal(bool, str)
    tag_detected = pyqtSignal(dict)
    category_started = pyqtSignal(str)
    
    # Nuevas para multi-antena
    scanner_ready = pyqtSignal(object)  # Scanner configurado
    start_detected = pyqtSignal(str, str)  # tag_number, timestamp
    finish_detected = pyqtSignal(str, str)
    checkpoint_detected = pyqtSignal(str, int, str)  # tag, port, timestamp
```

---

## ✅ Checklist de Implementación

- [ ] Actualizar `main.py` con carga de config
- [ ] Agregar `setup_scanner()` en `MainWindow`
- [ ] Implementar `get_antenna_role()` en `MainWindow`
- [ ] Refactorizar `DetectionTab` con roles
- [ ] Crear `ScanThread` para scanning continuo
- [ ] Agregar nuevas señales en `AppSignals`
- [ ] Probar flujo completo: wizard → main → detection

---

## 🧪 Testing

### Test Manual

```python
# 1. Ejecutar wizard
python main.py

# 2. Configurar:
#    - 4 antenas detectadas
#    - Puerto 2: Largada
#    - Puerto 6: Meta
#    - Puertos 3,4: Checkpoints

# 3. Verificar en DetectionTab:
#    - Tags en puerto 2 marcados como "start" (verde)
#    - Tags en puerto 6 marcados como "finish" (dorado)
#    - Tags en puertos 3,4 como "checkpoint" (azul)
```

### Test Automatizado

```bash
pytest tests/test_wizard_integration.py -v
```

---

## 📚 Próximos Pasos

1. **Implementar la integración** según esta guía
2. **Probar con antenas reales** en diferentes puertos
3. **Agregar lógica de carreras** (splits, tiempos)
4. **Exportación de datos** por antena/rol

¿Listo para implementar?