"""
Versión simplificada para prueba rápida
Usa tus widgets existentes directamente sin refactorización completa
"""
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QTabWidget, QLabel, QMessageBox, QGroupBox,
                            QHBoxLayout, QLineEdit, QSpinBox, QPushButton,
                            QTextEdit)
from PyQt6.QtCore import pyqtSlot

# Ajusta estos imports según tu estructura
from src.core.advanced_scanner import AdvancedYR8900Scanner
from src.core.integrated_race_tracker import IntegratedRaceTracker
from src.gui.widgets.antenna_config_widget import AntennaConfigWidget
from src.gui.widgets.event_config_widget import EventConfigWidget
from src.gui.widgets.race_monitoring_widget import RaceMonitoringWidget


class QuickTestMainWindow(QMainWindow):
    """MainWindow simplificado para pruebas rápidas"""
    
    def __init__(self):
        super().__init__()
        self.scanner = AdvancedYR8900Scanner()
        self.race_tracker = None
        self.setup_ui()
        
    def setup_ui(self):
        """Configurar interfaz"""
        self.setWindowTitle("RFID Athletics Timer - Prueba Rápida")
        self.setGeometry(100, 100, 1000, 750)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Sistema de pestañas
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Crear tabs con tus widgets existentes
        self.create_simple_tabs()
        
        # Barra de estado
        self.status_label = QLabel("✓ Aplicación iniciada - Prueba rápida")
        self.status_label.setStyleSheet("padding: 5px; background: #e8f5e9;")
        layout.addWidget(self.status_label)
    
    def create_simple_tabs(self):
        """Crear tabs usando widgets existentes"""
        
        # Tab 1: Gestión de Eventos (tu widget existente)
        self.event_config_widget = EventConfigWidget()
        self.event_config_widget.category_started.connect(self.on_category_started)
        self.event_config_widget.category_finished.connect(self.on_category_finished)
        self.tab_widget.addTab(self.event_config_widget, "⚙️ Gestión de Eventos")
        
        # Tab 2: Competencia (tu widget existente)
        self.race_monitoring_widget = RaceMonitoringWidget()
        self.tab_widget.addTab(self.race_monitoring_widget, "🏁 Competencia")
        
        # Tab 3: Configuración de Antenas (tu widget existente)
        self.antenna_config_widget = AntennaConfigWidget()
        self.antenna_config_widget.config_applied.connect(self.on_antenna_config_applied)
        self.tab_widget.addTab(self.antenna_config_widget, "📡 Config. Antenas")
        
        # Tab 4: Conexión RFID (tab simple inline)
        self.connection_tab = self.create_connection_tab()
        self.tab_widget.addTab(self.connection_tab, "🔌 Conexión RFID")
        
        # Tab 5: Info del Sistema (tab simple inline)
        self.info_tab = self.create_info_tab()
        self.tab_widget.addTab(self.info_tab, "ℹ️ Info Sistema")
    
    def create_connection_tab(self):
        """Crear tab de conexión simple"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Configuración
        config_group = QGroupBox("Configuración del Lector")
        config_layout = QHBoxLayout(config_group)
        
        config_layout.addWidget(QLabel("Host:"))
        self.host_input = QLineEdit("192.168.0.178")
        config_layout.addWidget(self.host_input)
        
        config_layout.addWidget(QLabel("Puerto:"))
        self.port_input = QSpinBox()
        self.port_input.setRange(1, 65535)
        self.port_input.setValue(4001)
        config_layout.addWidget(self.port_input)
        
        layout.addWidget(config_group)
        
        # Botones
        buttons_group = QGroupBox("Control")
        buttons_layout = QHBoxLayout(buttons_group)
        
        self.connect_btn = QPushButton("🔗 Conectar")
        self.connect_btn.clicked.connect(self.connect_scanner)
        buttons_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = QPushButton("❌ Desconectar")
        self.disconnect_btn.clicked.connect(self.disconnect_scanner)
        self.disconnect_btn.setEnabled(False)
        buttons_layout.addWidget(self.disconnect_btn)
        
        self.test_btn = QPushButton("🧪 Test")
        self.test_btn.clicked.connect(self.test_scanner)
        self.test_btn.setEnabled(False)
        buttons_layout.addWidget(self.test_btn)
        
        buttons_layout.addStretch()
        
        self.connection_status = QLabel("⚪ Desconectado")
        self.connection_status.setStyleSheet("font-weight: bold; color: red;")
        buttons_layout.addWidget(self.connection_status)
        
        layout.addWidget(buttons_group)
        
        # Log
        log_group = QGroupBox("Log de Conexión")
        log_layout = QVBoxLayout(log_group)
        
        self.connection_log = QTextEdit()
        self.connection_log.setMaximumHeight(200)
        self.connection_log.setReadOnly(True)
        log_layout.addWidget(self.connection_log)
        
        layout.addWidget(log_group)
        layout.addStretch()
        
        return tab
    
    def create_info_tab(self):
        """Crear tab de información del sistema"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        info_group = QGroupBox("Estado del Sistema")
        info_layout = QVBoxLayout(info_group)
        
        self.system_info = QTextEdit()
        self.system_info.setReadOnly(True)
        self.update_system_info()
        info_layout.addWidget(self.system_info)
        
        refresh_btn = QPushButton("🔄 Actualizar Estado")
        refresh_btn.clicked.connect(self.update_system_info)
        info_layout.addWidget(refresh_btn)
        
        layout.addWidget(info_group)
        
        return tab
    
    # Métodos de conexión
    @pyqtSlot()
    def connect_scanner(self):
        """Conectar al scanner"""
        host = self.host_input.text().strip()
        port = self.port_input.value()
        
        self.scanner.host = host
        self.scanner.port = port
        
        self.log("Intentando conectar...")
        if self.scanner.connect():
            self.connection_status.setText("🟢 Conectado")
            self.connection_status.setStyleSheet("font-weight: bold; color: green;")
            
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.test_btn.setEnabled(True)
            
            self.log("✓ Conectado exitosamente")
            self.status_label.setText("✓ Scanner RFID conectado")
            self.update_system_info()
        else:
            self.log("✗ Error de conexión")
            self.status_label.setText("✗ Error al conectar scanner")
    
    @pyqtSlot()
    def disconnect_scanner(self):
        """Desconectar del scanner"""
        self.scanner.disconnect()
        self.connection_status.setText("⚪ Desconectado")
        self.connection_status.setStyleSheet("font-weight: bold; color: red;")
        
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.test_btn.setEnabled(False)
        
        self.log("Desconectado")
        self.status_label.setText("Scanner desconectado")
        self.update_system_info()
    
    @pyqtSlot()
    def test_scanner(self):
        """Test del scanner"""
        self.log("Ejecutando test...")
        if hasattr(self.scanner, 'test_original_command'):
            success = self.scanner.test_original_command()
            if success:
                self.log("✓ Test exitoso")
            else:
                self.log("✗ Test falló")
        else:
            self.log("⚠ Método de test no disponible")
    
    # Métodos de eventos
    @pyqtSlot(str)
    def on_category_started(self, category_id):
        """Manejar inicio de categoría"""
        self.log(f"🏁 Categoría iniciada: {category_id}")
        
        # Inicializar race tracker si no existe
        if not self.race_tracker:
            event_manager = self.event_config_widget.get_event_manager()
            self.race_tracker = IntegratedRaceTracker(event_manager)
            
            # Aplicar configuración de antenas
            antenna_config = self.antenna_config_widget.get_current_config()
            enabled_antennas = {
                ant_id: config for ant_id, config in antenna_config.items() 
                if config['enabled']
            }
            self.race_tracker.set_antenna_config(enabled_antennas)
            
            # Conectar widget de monitoreo
            self.race_monitoring_widget.set_race_tracker(self.race_tracker)
            
            self.log("✓ Race tracker inicializado")
        
        self.status_label.setText(f"✓ Categoría activa: {category_id}")
        self.update_system_info()
    
    @pyqtSlot(str)
    def on_category_finished(self, category_id):
        """Manejar finalización de categoría"""
        self.log(f"🏁 Categoría finalizada: {category_id}")
        self.status_label.setText("Categoría finalizada")
    
    @pyqtSlot(dict)
    def on_antenna_config_applied(self, config_data):
        """Manejar configuración de antenas"""
        enabled_count = sum(1 for cfg in config_data.values() if cfg['enabled'])
        self.log(f"📡 Configuración aplicada: {enabled_count} antenas activas")
        
        if self.race_tracker:
            self.race_tracker.set_antenna_config(config_data)
        
        self.status_label.setText(f"✓ {enabled_count} antenas configuradas")
        self.update_system_info()
    
    # Métodos auxiliares
    def log(self, message):
        """Agregar mensaje al log"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.connection_log.append(f"[{timestamp}] {message}")
    
    def update_system_info(self):
        """Actualizar información del sistema"""
        info = []
        info.append("=== ESTADO DEL SISTEMA ===\n")
        info.append(f"Scanner Conectado: {'✓ Sí' if self.scanner.connected else '✗ No'}")
        info.append(f"Race Tracker Activo: {'✓ Sí' if self.race_tracker else '✗ No'}")
        
        # Info de antenas
        antenna_config = self.antenna_config_widget.get_current_config()
        enabled = sum(1 for cfg in antenna_config.values() if cfg['enabled'])
        info.append(f"Antenas Configuradas: {enabled}/{len(antenna_config)}")
        
        # Info de eventos
        if hasattr(self.event_config_widget, 'get_event_manager'):
            event_mgr = self.event_config_widget.get_event_manager()
            if event_mgr:
                categories = len(event_mgr.categories) if hasattr(event_mgr, 'categories') else 0
                info.append(f"Categorías Creadas: {categories}")
        
        info.append("\n=== COMPONENTES ===\n")
        info.append("✓ EventConfigWidget - Cargado")
        info.append("✓ RaceMonitoringWidget - Cargado")
        info.append("✓ AntennaConfigWidget - Cargado")
        
        self.system_info.setPlainText("\n".join(info))
    
    def closeEvent(self, event):
        """Manejar cierre"""
        if self.scanner.connected:
            reply = QMessageBox.question(
                self,
                'Confirmar Salida',
                'El scanner está conectado. ¿Desea desconectar y salir?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.scanner.disconnect()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Función principal"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    print("="*50)
    print("🚀 RFID Athletics Timer - Prueba Rápida")
    print("="*50)
    print("✓ Usando widgets existentes")
    print("✓ Tabs funcionales")
    print("✓ Sin refactorización completa")
    print("="*50)
    
    window = QuickTestMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()