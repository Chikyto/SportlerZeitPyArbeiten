import sys
import json
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox

from src.gui.wizard.auto_wizard import AutoConfigurationWizard  # 🔥 Cambiado a AutoWizard
from src.gui.main_window import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CONFIG_FILE = Path("timing_system_config.json")

def load_config():
    """Carga configuración guardada"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                logger.info(f"✓ Configuración encontrada")
                
                # 🔥 VERIFICAR Y CORREGIR TIPOS DE KEYS
                if 'antennas' in config:
                    # Convertir keys a int si son strings
                    antennas_fixed = {}
                    for key, value in config['antennas'].items():
                        port_int = int(key) if isinstance(key, str) else key
                        antennas_fixed[port_int] = value
                    config['antennas'] = antennas_fixed
                    logger.info(f"📡 Puertos corregidos a int: {list(antennas_fixed.keys())}")
                
                return config
        except Exception as e:
            logger.error(f"Error cargando config: {e}")
    return None

def save_config(config):
    """Guarda configuración"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"✓ Configuración guardada")
    except Exception as e:
        logger.error(f"Error guardando config: {e}")

def run_wizard():
    """Ejecuta el wizard de configuración"""
    logger.info("Iniciando wizard de configuración...")
    wizard = AutoConfigurationWizard()
    
    if wizard.exec():
        config = wizard.get_configuration()
        
        # 🔥 DEBUG: Ver qué generó el wizard
        logger.info("=" * 60)
        logger.info("📦 CONFIGURACIÓN GENERADA POR WIZARD:")
        logger.info(f"   Connection: {config.get('connection')}")
        logger.info(f"   Antenas keys: {list(config.get('antennas', {}).keys())}")
        logger.info(f"   Tipos keys: {[type(k).__name__ for k in config.get('antennas', {}).keys()]}")
        for port, ant in config.get('antennas', {}).items():
            logger.info(f"   Puerto {port}: start={ant.get('start')}, "
                       f"finish={ant.get('finish')}, checkpoint={ant.get('checkpoint')}")
        logger.info("=" * 60)
        
        save_config(config)
        logger.info("✓ Wizard completado exitosamente")
        return config
    else:
        logger.info("Wizard cancelado por usuario")
        return None

def ask_use_existing_config(config):
    """Pregunta si usar la configuración existente"""
    antennas = config.get('antennas', {})
    conn = config.get('connection', {})
    
    summary = f"""Se encontró una configuración existente:

🔌 Conexión: {conn.get('host')}:{conn.get('port')}
📡 Antenas configuradas: {len(antennas)}
"""
    
    for port, ant_config in antennas.items():
        roles = []
        if ant_config.get('start'):
            roles.append('🟢 Largada')
        if ant_config.get('finish'):
            roles.append('🏁 Meta')
        if ant_config.get('checkpoint'):
            roles.append('🔵 Checkpoint')
        
        role_text = ' + '.join(roles) if roles else 'Sin rol'
        name = ant_config.get('name', f'Antena {port}')
        summary += f"  • Puerto {port}: {name} ({role_text})\n"
    
    summary += "\n¿Desea usar esta configuración?"
    
    reply = QMessageBox.question(
        None,
        "Configuración Existente",
        summary,
        QMessageBox.StandardButton.Yes | 
        QMessageBox.StandardButton.No |
        QMessageBox.StandardButton.Cancel,
        QMessageBox.StandardButton.Yes
    )
    
    if reply == QMessageBox.StandardButton.Yes:
        return 'use'
    elif reply == QMessageBox.StandardButton.No:
        return 'new'
    else:
        return 'cancel'

def install_excepthook():
    """Evita que PyQt6 cierre la app ante una excepción no manejada en un slot.

    Sin esto, cualquier error en un handler de botón/señal aborta el proceso
    sin mostrar nada. Acá lo logueamos y mostramos un diálogo de error.
    """
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.error(
            "Excepción no manejada",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

        try:
            QMessageBox.critical(
                None,
                "Error Inesperado",
                f"Ocurrió un error inesperado:\n\n{exc_type.__name__}: {exc_value}\n\n"
                f"La aplicación sigue funcionando, pero revisa los logs.\n"
                f"Si el problema persiste, reinicia la aplicación."
            )
        except Exception:
            pass  # Si no se puede mostrar el diálogo, al menos quedó el log

    sys.excepthook = handle_exception

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RFID Athletics Timer")
    app.setOrganizationName("RFID Sports")

    install_excepthook()
    
    try:
        # Cargar configuración si existe
        config = load_config()
        
        if config:
            choice = ask_use_existing_config(config)
            
            if choice == 'cancel':
                logger.info("Usuario canceló")
                return 0
            elif choice == 'new':
                logger.info("Usuario eligió nueva configuración")
                config = run_wizard()
                if not config:
                    return 0
        else:
            logger.info("No hay configuración. Ejecutando wizard...")
            config = run_wizard()
            
            if not config:
                logger.info("Wizard cancelado. Saliendo...")
                return 0
        
        # 🔥 DEBUG: Verificar config antes de MainWindow
        logger.info("=" * 80)
        logger.info("🚀 INICIANDO MAINWINDOW CON CONFIGURACIÓN:")
        logger.info("=" * 80)
        logger.info(f"Config disponible: {config is not None}")
        if config:
            logger.info(f"  Connection: {config.get('connection')}")
            logger.info(f"  Antenas keys: {list(config.get('antennas', {}).keys())}")
            logger.info(f"  Tipos keys: {[type(k).__name__ for k in config.get('antennas', {}).keys()]}")
            
            # Mostrar roles de cada antena
            for port, ant_config in config.get('antennas', {}).items():
                logger.info(f"  Puerto {port} ({type(port).__name__}):")
                logger.info(f"    name: {ant_config.get('name')}")
                logger.info(f"    start: {ant_config.get('start')}")
                logger.info(f"    finish: {ant_config.get('finish')}")
                logger.info(f"    checkpoint: {ant_config.get('checkpoint')}")
        logger.info("=" * 80)
        
        # Iniciar aplicación principal con configuración
        logger.info("Creando MainWindow...")
        main_window = MainWindow(wizard_config=config)
        
        logger.info("Mostrando MainWindow...")
        main_window.show()
        
        logger.info("Ejecutando event loop...")
        return app.exec()
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error("ERROR CRÍTICO EN MAIN")
        logger.error(f"Tipo: {type(e).__name__}")
        logger.error(f"Mensaje: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()
        
        QMessageBox.critical(
            None,
            "Error Fatal",
            f"Error iniciando aplicación:\n\n{type(e).__name__}: {str(e)}\n\n"
            f"Ver logs para más detalles."
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())