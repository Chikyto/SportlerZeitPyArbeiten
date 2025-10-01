"""
Módulo de pestañas de la aplicación

Proporciona todos los tabs modulares de la interfaz
"""
from .base_tab import BaseTab
from .connection_tab import ConnectionTab
from .detection_tab import DetectionTab

__all__ = [
    'BaseTab',
    'ConnectionTab',
    'DetectionTab',
]