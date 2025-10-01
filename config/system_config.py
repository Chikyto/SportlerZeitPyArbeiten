#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración del sistema de cronometraje
timing_system/config/system_config.py
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict
import json

class AntennaFunction(Enum):
    """Funciones posibles de antenas"""
    LARGADA = "largada"
    CHECKPOINT = "checkpoint"
    LLEGADA = "llegada"
    DISABLED = "disabled"

@dataclass
class ReaderConfig:
    """Configuración del lector RFID"""
    host: str = "192.168.0.178"
    port: int = 4001
    reader_address: int = 0xF3
    timeout: float = 3.0

@dataclass
class AntennaConfig:
    """Configuración de una antena individual"""
    port: int
    enabled: bool = False
    function: AntennaFunction = AntennaFunction.DISABLED
    power_level: int = 25
    description: str = ""

class SystemConfig:
    """Configuración completa del sistema"""
    
    def __init__(self):
        self.reader = ReaderConfig()
        self.antennas: Dict[int, AntennaConfig] = {}
        self.event_type = "carrera_lineal"
        self.system_name = "Sistema de Cronometraje RFID"
    
    def save_to_file(self, filename: str) -> bool:
        """Guarda configuración a archivo JSON"""
        try:
            data = {
                "reader": {
                    "host": self.reader.host,
                    "port": self.reader.port,
                    "reader_address": self.reader.reader_address,
                    "timeout": self.reader.timeout
                },
                "antennas": {
                    str(port): {
                        "port": config.port,
                        "enabled": config.enabled,
                        "function": config.function.value,
                        "power_level": config.power_level,
                        "description": config.description
                    } for port, config in self.antennas.items()
                },
                "event_type": self.event_type,
                "system_name": self.system_name
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error guardando configuración: {e}")
            return False
    
    def load_from_file(self, filename: str) -> bool:
        """Carga configuración desde archivo JSON"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Cargar configuración del reader
            reader_data = data.get("reader", {})
            self.reader = ReaderConfig(
                host=reader_data.get("host", "192.168.0.178"),
                port=reader_data.get("port", 4001),
                reader_address=reader_data.get("reader_address", 0xF3),
                timeout=reader_data.get("timeout", 3.0)
            )
            
            # Cargar configuración de antenas
            self.antennas = {}
            antennas_data = data.get("antennas", {})
            for port_str, antenna_data in antennas_data.items():
                port = int(port_str)
                self.antennas[port] = AntennaConfig(
                    port=port,
                    enabled=antenna_data.get("enabled", False),
                    function=AntennaFunction(antenna_data.get("function", "disabled")),
                    power_level=antenna_data.get("power_level", 25),
                    description=antenna_data.get("description", "")
                )
            
            self.event_type = data.get("event_type", "carrera_lineal")
            self.system_name = data.get("system_name", "Sistema de Cronometraje RFID")
            
            return True
            
        except FileNotFoundError:
            print(f"Archivo no encontrado: {filename}")
            return False
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            return False
    
    def get_enabled_antennas(self) -> Dict[int, AntennaConfig]:
        """Retorna solo las antenas habilitadas"""
        return {port: config for port, config in self.antennas.items() 
                if config.enabled}
    
    def get_antennas_by_function(self, function: AntennaFunction) -> Dict[int, AntennaConfig]:
        """Retorna antenas por función específica"""
        return {port: config for port, config in self.antennas.items() 
                if config.enabled and config.function == function}