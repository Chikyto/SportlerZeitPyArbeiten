#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de configuración del sistema de cronometraje
timing_system/config/__init__.py
"""

from .exceptions import (
    TimingSystemError,
    ReaderConnectionError,
    AntennaError,
    ConfigurationError,
    ProtocolError,
    ValidationError
)

from .system_config import (
    AntennaFunction,
    ReaderConfig,
    AntennaConfig,
    SystemConfig
)

__all__ = [
    # Excepciones
    'TimingSystemError',
    'ReaderConnectionError',
    'AntennaError',
    'ConfigurationError',
    'ProtocolError',
    'ValidationError',
    # Configuración
    'AntennaFunction',
    'ReaderConfig',
    'AntennaConfig',
    'SystemConfig'
]