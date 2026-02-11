#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Procesador de tags RFID detectados
src/core/tag_processor.py

Responsabilidad única: Procesar tags detectados y determinar roles
Lógica de negocio pura - Sin dependencias de PyQt
"""

import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class TagProcessor:
    """
    Procesador de tags RFID
    
    Maneja la lógica de:
    - Determinar rol de la antena donde se detectó
    - Clasificar detecciones por tipo de evento
    - Formatear información para presentación
    
    Esta clase NO tiene dependencias de PyQt, es lógica pura.
    """
    
    def __init__(self, antenna_roles: Dict[int, List[str]], signals=None):
        """
        Inicializar procesador
        
        Args:
            antenna_roles: Dict {port: [roles]} con roles de cada antena
            signals: (Opcional) Objeto AppSignals para emitir eventos
        """
        self.antenna_roles = antenna_roles
        self.signals = signals
    
    def update_antenna_roles(self, antenna_roles: Dict[int, List[str]]):
        """
        Actualizar roles de antenas
        
        Args:
            antenna_roles: Nuevo diccionario de roles
        """
        self.antenna_roles = antenna_roles
        logger.debug(f"📡 Roles actualizados: {list(antenna_roles.keys())}")
    
    def process_tag(self, tag_info: dict) -> Optional[dict]:
        """
        Procesar tag detectado
        
        Args:
            tag_info: Dict con info del tag:
                - number: ID del tag
                - antenna: Puerto donde se detectó
                - timestamp: Timestamp de detección
        
        Returns:
            dict con información procesada o None si hay error:
                - tag_id: ID del tag
                - port: Puerto
                - timestamp: Timestamp formateado
                - timestamp_obj: Timestamp original (datetime)
                - roles: Lista de roles
                - antenna_name: Nombre de la antena (por defecto "Puerto X")
                - color_code: Código de color como string
        """
        try:
            tag_number = tag_info['number']
            port = tag_info.get('antenna', 0)
            timestamp_obj = tag_info['timestamp']
            
            # Formatear timestamp
            if isinstance(timestamp_obj, datetime):
                timestamp = timestamp_obj.strftime('%H:%M:%S.%f')[:-3]
            else:
                timestamp = str(timestamp_obj)
            
            # Convertir port a int si es necesario
            port = int(port) if isinstance(port, str) else port

            logger.debug(f"🔍 TagProcessor: Procesando tag {tag_number} del puerto {port}")
            logger.debug(f"   Puertos configurados: {list(self.antenna_roles.keys())}")
            logger.debug(f"   Puerto en antenna_roles? {port in self.antenna_roles}")

            # Verificar que el puerto esté configurado
            if port not in self.antenna_roles:
                logger.warning(f"⚠️  Tag {tag_number} en puerto {port} no configurado")
                logger.warning(f"Puertos configurados: {list(self.antenna_roles.keys())}")
                logger.warning(f"Tipo del puerto detectado: {type(port)}")
                logger.warning(f"Tipos de keys en antenna_roles: {[type(k) for k in self.antenna_roles.keys()]}")
                return None

            # Obtener roles
            roles = self.antenna_roles.get(port, [])
            logger.debug(f"   Roles del puerto {port}: {roles}")
            
            # Si es string (compatibilidad), convertir a lista
            if isinstance(roles, str):
                roles = [roles]
            
            # Nombre de antena (por defecto)
            antenna_name = f"Puerto {port}"
            
            # Determinar código de color según roles
            color_code = self._get_color_code_for_roles(roles)
            
            # Emitir señales si están disponibles
            if self.signals:
                self._emit_signals(tag_number, port, timestamp, roles)
            
            return {
                'tag_id': tag_number,
                'port': port,
                'timestamp': timestamp,
                'timestamp_obj': timestamp_obj,
                'roles': roles,
                'antenna_name': antenna_name,
                'color_code': color_code
            }
            
        except Exception as e:
            logger.error(f"❌ Error procesando tag: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_color_code_for_roles(self, roles: List[str]) -> str:
        """
        Determinar código de color según roles
        
        Args:
            roles: Lista de roles de la antena
        
        Returns:
            str: Código de color ('orange', 'green', 'gold', 'blue', 'none')
        """
        if not roles:
            return 'none'
        
        # Combinaciones especiales
        if 'start' in roles and 'finish' in roles:
            return 'orange'  # Naranja (largada+meta)
        
        # Roles individuales
        if 'start' in roles:
            return 'green'   # Verde (largada)
        elif 'finish' in roles:
            return 'gold'    # Dorado (meta)
        elif 'checkpoint' in roles:
            return 'blue'    # Azul (checkpoint)
        
        return 'none'
    
    def get_color_rgb(self, color_code: str) -> Tuple[int, int, int]:
        """
        Convertir código de color a RGB
        
        Args:
            color_code: Código de color ('orange', 'green', 'gold', 'blue', 'none')
        
        Returns:
            Tuple[int, int, int]: (R, G, B)
        """
        color_map = {
            'orange': (255, 200, 100),  # Naranja
            'green': (144, 238, 144),   # Verde claro
            'gold': (255, 215, 0),      # Dorado
            'blue': (173, 216, 230),    # Azul claro
            'none': (255, 255, 255)     # Blanco
        }
        return color_map.get(color_code, (255, 255, 255))
    
    def _emit_signals(self, tag_id: str, port: int, timestamp: str, roles: List[str]):
        """
        Emitir señales apropiadas según roles
        
        Args:
            tag_id: ID del tag
            port: Puerto donde se detectó
            timestamp: Timestamp
            roles: Lista de roles de la antena
        """
        if not self.signals:
            return
        
        if 'start' in roles:
            self.signals.start_detected.emit(tag_id, timestamp)
            logger.info(f"🟢 LARGADA: Tag {tag_id}")
        
        if 'finish' in roles:
            self.signals.finish_detected.emit(tag_id, timestamp)
            logger.info(f"🏁 META: Tag {tag_id}")
        
        if 'checkpoint' in roles:
            self.signals.checkpoint_detected.emit(tag_id, port, timestamp)
            logger.info(f"🔵 CHECKPOINT {port}: Tag {tag_id}")
    
    def format_role_text(self, roles: List[str]) -> str:
        """
        Formatear texto de roles para mostrar en UI
        
        Args:
            roles: Lista de roles
        
        Returns:
            str: Texto formateado (ej: "🟢 Largada + 🏁 Meta")
        """
        if not roles:
            return "⚪ Sin rol"
        
        role_parts = []
        if 'start' in roles:
            role_parts.append('🟢 Largada')
        if 'finish' in roles:
            role_parts.append('🏁 Meta')
        if 'checkpoint' in roles:
            role_parts.append('🔵 Checkpoint')
        
        return ' + '.join(role_parts) if role_parts else '⚪ Sin rol'
    
    def get_role_emoji(self, role: str) -> str:
        """
        Obtener emoji para un rol específico
        
        Args:
            role: Nombre del rol ('start', 'finish', 'checkpoint')
        
        Returns:
            str: Emoji correspondiente
        """
        emoji_map = {
            'start': '🟢',
            'finish': '🏁',
            'checkpoint': '🔵',
        }
        return emoji_map.get(role, '⚪')
    
    def classify_detection(self, roles: List[str]) -> str:
        """
        Clasificar tipo de detección según roles
        
        Args:
            roles: Lista de roles de la antena
        
        Returns:
            str: Tipo de detección ('start', 'finish', 'checkpoint', 'mixed', 'unknown')
        """
        if not roles:
            return 'unknown'
        
        if len(roles) > 1:
            return 'mixed'
        
        return roles[0]  # 'start', 'finish', o 'checkpoint'
    
    def validate_detection(self, tag_info: dict) -> Tuple[bool, Optional[str]]:
        """
        Validar si una detección es válida
        
        Args:
            tag_info: Dict con información del tag
        
        Returns:
            Tuple[bool, Optional[str]]: (es_válido, mensaje_error)
        """
        # Verificar campos requeridos
        required_fields = ['number', 'antenna', 'timestamp']
        for field in required_fields:
            if field not in tag_info:
                return False, f"Campo requerido faltante: {field}"
        
        # Verificar que el puerto esté configurado
        port = tag_info.get('antenna', 0)
        port = int(port) if isinstance(port, str) else port
        
        if port not in self.antenna_roles:
            return False, f"Puerto {port} no está configurado"
        
        return True, None


# ============================================================================
# FUNCIONES AUXILIARES (sin clase)
# ============================================================================

def get_default_color_for_role(role: str) -> Tuple[int, int, int]:
    """
    Obtener color RGB por defecto para un rol
    
    Args:
        role: Nombre del rol
    
    Returns:
        Tuple[int, int, int]: Color RGB
    """
    color_map = {
        'start': (144, 238, 144),      # Verde
        'finish': (255, 215, 0),       # Dorado
        'checkpoint': (173, 216, 230), # Azul
    }
    return color_map.get(role, (255, 255, 255))


def format_timestamp(timestamp) -> str:
    """
    Formatear timestamp a string legible
    
    Args:
        timestamp: datetime object o string
    
    Returns:
        str: Timestamp formateado "HH:MM:SS.mmm"
    """
    if isinstance(timestamp, datetime):
        return timestamp.strftime('%H:%M:%S.%f')[:-3]
    return str(timestamp)