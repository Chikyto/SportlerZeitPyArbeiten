# RFID Athletics Timer

Sistema de control de tiempo para atletas usando lector RFID YR8900 e interfaz gráfica PyQt6.

## Descripción

Este sistema permite la detección automática de chips RFID SmarTrac para control de tiempo en eventos deportivos. Utiliza el lector YR8900 de Invelion con comunicación Ethernet y proporciona una interfaz gráfica intuitiva para monitoreo en tiempo real.

## Características

- **Comunicación Ethernet** con lector YR8900
- **Interfaz gráfica moderna** con PyQt6
- **Detección en tiempo real** de chips RFID
- **Múltiples antenas** soportadas (hasta 8)
- **Base de datos** para almacenamiento de eventos
- **Exportación de datos** en múltiples formatos
- **Sistema de logging** completo
- **Arquitectura modular** y extensible

## Requisitos del Sistema

- Python 3.8 o superior
- Lector RFID YR8900 (Invelion)
- Red Ethernet configurada
- Sistema operativo: Windows, Linux o macOS

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/rfid-athletics-timer.git
cd rfid-athletics-timer
```

### 2. Crear entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configuración inicial

```bash
python scripts/setup.py
```

## Configuración del Hardware

### Lector YR8900

1. **Conexión de red**: Conectar el lector a la red Ethernet
2. **IP por defecto**: 192.168.0.178:4001
3. **Configuración de antenas**: Hasta 8 antenas soportadas
4. **Potencia RF**: Configurable de 0-33 dBm

### Chips RFID

- **Tipo soportado**: SmarTrac
- **Frecuencia**: UHF 860-960 MHz
- **Protocolo**: EPC Class 1 Gen 2 (ISO 18000-6C)

## Uso Rápido

### Ejecutar la aplicación

```bash
python main.py
```

### Pasos básicos

1. **Conectar**: Configurar IP del lector y conectar
2. **Configurar**: Ajustar potencia y antena en uso
3. **Scanning**: Iniciar detección de chips
4. **Monitoreo**: Ver tags detectados en tiempo real
5. **Exportar**: Guardar datos del evento

## Estructura del Proyecto

```
rfid-athletics-timer/
├── src/                    # Código fuente
│   ├── core/              # Lógica del scanner
│   ├── gui/               # Interfaz gráfica
│   ├── data/              # Manejo de datos
│   └── utils/             # Utilidades
├── tests/                 # Tests unitarios
├── docs/                  # Documentación
├── data/                  # Datos del proyecto
└── scripts/               # Scripts auxiliares
```

## Configuración

### Archivo de configuración (src/core/config.py)

```python
# Configuración del lector RFID
RFID_HOST = "192.168.0.178"
RFID_PORT = 4001
SCAN_INTERVAL = 500  # ms

# Configuración de la base de datos
DATABASE_PATH = "data/databases/athletics.db"

# Configuración de logging
LOG_LEVEL = "INFO"
LOG_PATH = "data/logs/"
```

## API Principal

### RFIDScanner

```python
from src.core.rfid_scanner import RFIDScanner

scanner = RFIDScanner(host="192.168.0.178", port=4001)
scanner.connect_reader()
scanner.start_scanning()
```

### TagParser

```python
from src.core.tag_parser import TagParser

parser = TagParser()
tag_info = parser.parse_tag_data(raw_data)
```

## Testing

```bash
# Ejecutar todos los tests
python -m pytest tests/

# Test específico
python -m pytest tests/test_rfid_scanner.py

# Con cobertura
python -m pytest --cov=src tests/
```

## Desarrollo

### Configurar entorno de desarrollo

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Pre-commit hooks
pre-commit install

# Formateo de código
black src/
flake8 src/
```

### Agregar nuevas funcionalidades

1. Crear rama de feature: `git checkout -b feature/nueva-funcionalidad`
2. Implementar en el módulo correspondiente
3. Agregar tests unitarios
4. Actualizar documentación
5. Crear pull request

## Solución de Problemas

### Error de conexión al lector

1. Verificar conexión de red
2. Comprobar IP del lector: `ping 192.168.0.178`
3. Revisar puerto disponible: `telnet 192.168.0.178 4001`
4. Verificar configuración de firewall

### Chips no detectados

1. Verificar potencia RF
2. Comprobar conexión de antenas
3. Verificar tipo de chip compatible
4. Revisar distancia de lectura

### Problemas de rendimiento

1. Ajustar intervalo de scanning
2. Verificar recursos del sistema
3. Optimizar configuración de red
4. Revisar logs del sistema

## Logging

Los logs se almacenan en `data/logs/` con rotación automática:

- `application.log`: Log general de la aplicación
- `rfid.log`: Log específico del scanner RFID
- `database.log`: Log de operaciones de base de datos

## Exportación de Datos

Formatos soportados:
- **CSV**: Para análisis en Excel
- **JSON**: Para integración con APIs
- **PDF**: Para reportes impresos
- **SQLite**: Para backup de base de datos

## Contribuir

1. Fork del repositorio
2. Crear rama de feature
3. Commit con mensajes descriptivos
4. Push a la rama
5. Crear Pull Request

## Licencia

Este proyecto está licenciado bajo MIT License. Ver `LICENSE` para más detalles.

## Soporte

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/rfid-athletics-timer/issues)
- **Wiki**: [Documentación detallada](https://github.com/tu-usuario/rfid-athletics-timer/wiki)
- **Email**: soporte@tu-dominio.com

## Changelog

### v1.0.0 (2025-09-21)
- Implementación inicial
- Soporte para YR8900
- Interfaz gráfica PyQt6
- Sistema de base de datos
- Exportación de datos

---

**Desarrollado para sistemas de cronometraje deportivo** 🏃‍♂️🏃‍♀️