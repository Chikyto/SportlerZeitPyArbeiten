#!/bin/bash
# Script de configuración para SportlerZeit RFID System
# Crea el entorno virtual e instala todas las dependencias

set -e  # Detener si hay errores

echo "=========================================="
echo "SportlerZeit RFID - Configuración Inicial"
echo "=========================================="
echo ""

# Verificar que Python 3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    echo "Por favor instala Python 3.8 o superior"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ Python detectado: $PYTHON_VERSION"
echo ""

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
    echo "✅ Entorno virtual creado"
else
    echo "✅ Entorno virtual ya existe"
fi
echo ""

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Actualizar pip
echo "📥 Actualizando pip..."
pip install --upgrade pip

echo ""
echo "📥 Instalando dependencias desde requirements.txt..."
echo ""

# Instalar dependencias
pip install -r requirements.txt

echo ""
echo "=========================================="
echo "✅ ¡Instalación completada exitosamente!"
echo "=========================================="
echo ""
echo "Para usar el sistema:"
echo "  1. Activa el entorno virtual:"
echo "     source venv/bin/activate"
echo ""
echo "  2. Ejecuta la aplicación:"
echo "     python main.py"
echo ""
echo "Para desactivar el entorno virtual:"
echo "     deactivate"
echo ""
