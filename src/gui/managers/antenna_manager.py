#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de Configuración de Antenas
src/gui/managers/antenna_manager.py

Responsabilidad única: Gestionar toda la información de configuración de antenas
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class AntennaManager:
    """
    Gestor de configuración de antenas
    
    Centraliza todo el acceso a información de antenas:
    - Configuración de cada antena
    - Roles asignados
    - Nombres personalizados
    - Antenas habilitadas
    """
    
    def __init__(self, wizard_config: Optional[Dict] = None):
        """
        Inicializar gestor
        
        Args:
            wizard_config: Configuración del wizard con estructura:
                {
                    'connection': {...},
                    'antennas': {
                        port(int): {
                            'enabled': bool,
                            'name': str,
                            'start': bool,
                            'finish': bool,
                            'checkpoint': bool,
                            ...
                        }
                    }
                }
        """
        self.wizard_config = wizard_config or {}
        self._validate_config()
    
    def _validate_config(self):
        """Validar y normalizar configuración"""
        if not self.wizard_config:
            logger.warning("⚠️  AntennaManager inicializado sin configuración")
            return
        
        # Asegurar que antennas existe
        if 'antennas' not in self.wizard_config:
            self.wizard_config['antennas'] = {}
            logger.warning("⚠️  No hay sección 'antennas' en config")
        
        # Normalizar keys a int si son strings
        antennas = self.wizard_config['antennas']
        normalized = {}
        for key, value in antennas.items():
            port_int = int(key) if isinstance(key, str) else key
            normalized[port_int] = value
        
        self.wizard_config['antennas'] = normalized
        
        logger.info(f"📡 AntennaManager configurado con {len(normalized)} antenas")
    
    def update_config(self, new_config: Dict):
        """
        Actualizar configuración completa
        
        Args:
            new_config: Nueva configuración del wizard
        """
        self.wizard_config = new_config
        self._validate_config()
        logger.info("🔄 Configuración de antenas actualizada")
    
    def get_antenna_config(self, port: int) -> Dict:
        """
        Obtener configuración completa de una antena específica
        
        Args:
            port: Número de puerto (1-8)
        
        Returns:
            Dict con configuración de la antena o dict vacío si no existe
        """
        if not self.wizard_config:
            return {}
        
        antennas = self.wizard_config.get('antennas', {})
        return antennas.get(port, {})
    
    def get_antenna_roles(self, port: int) -> List[str]:
        """
        Obtener TODOS los roles de una antena
        
        Args:
            port: Número de puerto (1-8)
        
        Returns:
            Lista de roles: ['start', 'finish', 'checkpoint']
        """
        config = self.get_antenna_config(port)
        roles = []
        
        if config.get('start', False):
            roles.append('start')
        if config.get('finish', False):
            roles.append('finish')
        if config.get('checkpoint', False):
            roles.append('checkpoint')
        
        return roles
    
    def get_antenna_role(self, port: int) -> str:
        """
        Obtener el rol PRINCIPAL de una antena
        Para compatibilidad con código existente
        
        Args:
            port: Número de puerto (1-8)
        
        Returns:
            str: 'start', 'finish', 'checkpoint', o 'unknown'
        """
        config = self.get_antenna_config(port)
        
        # Retornar el primer rol encontrado (por prioridad)
        if config.get('start', False):
            return 'start'
        elif config.get('finish', False):
            return 'finish'
        elif config.get('checkpoint', False):
            return 'checkpoint'
        
        return 'unknown'
    
    def get_antenna_name(self, port: int) -> str:
        """
        Obtener el nombre personalizado de una antena
        
        Args:
            port: Número de puerto (1-8)
        
        Returns:
            str: Nombre de la antena o "Antena X" por defecto
        """
        config = self.get_antenna_config(port)
        return config.get('name', f'Antena {port}')
    
    def get_enabled_antennas(self) -> List[int]:
        """
        Obtener lista de puertos habilitados
        
        Returns:
            Lista de puertos habilitados (ordenada)
        """
        if not self.wizard_config:
            return []
        
        antennas = self.wizard_config.get('antennas', {})
        enabled = [
            port for port, config in antennas.items()
            if config.get('enabled', False)
        ]
        
        return sorted(enabled)
    
    def is_antenna_enabled(self, port: int) -> bool:
        """
        Verificar si una antena está habilitada
        
        Args:
            port: Número de puerto (1-8)
        
        Returns:
            bool: True si está habilitada
        """
        config = self.get_antenna_config(port)
        return config.get('enabled', False)
    
    def get_antenna_power_level(self, port: int) -> int:
        """
        Obtener nivel de potencia de una antena
        
        Args:
            port: Número de puerto (1-8)
        
        Returns:
            int: Nivel de potencia (0-33 dBm)
        """
        config = self.get_antenna_config(port)
        return config.get('power_level', 25)
    
    def get_antennas_by_role(self, role: str) -> List[int]:
        """
        Obtener lista de antenas con un rol específico
        
        Args:
            role: 'start', 'finish', o 'checkpoint'
        
        Returns:
            Lista de puertos que tienen ese rol
        """
        result = []
        
        for port in self.get_enabled_antennas():
            roles = self.get_antenna_roles(port)
            if role in roles:
                result.append(port)
        
        return sorted(result)
    
    def get_start_antennas(self) -> List[int]:
        """Antenas configuradas como largada"""
        return self.get_antennas_by_role('start')
    
    def get_finish_antennas(self) -> List[int]:
        """Antenas configuradas como meta"""
        return self.get_antennas_by_role('finish')
    
    def get_checkpoint_antennas(self) -> List[int]:
        """Antenas configuradas como checkpoint"""
        return self.get_antennas_by_role('checkpoint')
    
    def get_all_antennas_config(self) -> Dict[int, Dict]:
        """
        Obtener configuración de todas las antenas
        
        Returns:
            Dict {port: config} solo con antenas habilitadas
        """
        if not self.wizard_config:
            return {}
        
        antennas = self.wizard_config.get('antennas', {})
        return {
            port: config for port, config in antennas.items()
            if config.get('enabled', False)
        }
    
    def has_configuration(self) -> bool:
        """
        Verificar si hay configuración válida
        
        Returns:
            bool: True si hay al menos una antena configurada
        """
        return len(self.get_enabled_antennas()) > 0
    
    def get_summary(self) -> str:
        """
        Obtener resumen de configuración en formato legible
        
        Returns:
            str: Resumen de configuración
        """
        if not self.has_configuration():
            return "Sin antenas configuradas"
        
        enabled = self.get_enabled_antennas()
        start_count = len(self.get_start_antennas())
        finish_count = len(self.get_finish_antennas())
        checkpoint_count = len(self.get_checkpoint_antennas())
        
        summary = f"{len(enabled)} antenas activas"
        
        if start_count > 0:
            summary += f" | {start_count} largada(s)"
        if finish_count > 0:
            summary += f" | {finish_count} meta(s)"
        if checkpoint_count > 0:
            summary += f" | {checkpoint_count} checkpoint(s)"
        
        return summary
    
    def __repr__(self) -> str:
        """Representación string del manager"""
        return f"<AntennaManager: {self.get_summary()}>"