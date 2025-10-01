#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excepciones personalizadas del sistema de cronometraje
timing_system/config/exceptions.py
"""

class TimingSystemError(Exception):
    """Excepción base del sistema de cronometraje"""
    pass

class ReaderConnectionError(TimingSystemError):
    """Error de conexión con el lector RFID"""
    pass

class AntennaError(TimingSystemError):
    """Error relacionado con antenas"""
    pass

class ConfigurationError(TimingSystemError):
    """Error de configuración del sistema"""
    pass

class ProtocolError(TimingSystemError):
    """Error en el protocolo de comunicación"""
    pass

class ValidationError(TimingSystemError):
    """Error de validación de datos"""
    pass