#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestor de Tabs de la Interfaz
src/gui/managers/tab_manager.py

Responsabilidad única: Crear, configurar y gestionar todos los tabs
"""

import logging
from PyQt6.QtWidgets import QTabWidget
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TabManager:
    """
    Gestor de tabs de la interfaz
    
    Responsabilidades:
    - Crear todos los tabs de la aplicación
    - Aplicar configuración a los tabs
    - Proporcionar acceso a tabs específicos
    """
    
    def __init__(self, tab_widget: QTabWidget, signals, scanner=None, antenna_manager=None, race_manager=None):
        """
        Inicializar gestor de tabs

        Args:
            tab_widget: QTabWidget donde se agregarán los tabs
            signals: Objeto AppSignals para comunicación
            scanner: Scanner RFID (opcional, se puede agregar después)
            antenna_manager: Gestor de antenas (opcional)
            race_manager: Gestor de carreras para timing (opcional)
        """
        self.tab_widget = tab_widget
        self.signals = signals
        self.scanner = scanner
        self.antenna_manager = antenna_manager
        self.race_manager = race_manager
        self.tabs = {}  # Dict para acceder a tabs por nombre

        logger.info("📋 TabManager inicializado")
    
    def set_scanner(self, scanner):
        """
        Establecer scanner (para cuando se inicializa después)

        Args:
            scanner: Instancia de AdvancedYR8900Scanner
        """
        self.scanner = scanner
        logger.info("🔄 Scanner asignado a TabManager")

        # Actualizar scanner en tabs que ya existen
        if 'chip_assignment' in self.tabs:
            chip_widget = self.tabs['chip_assignment']
            chip_widget.scanner = scanner
            logger.info("✅ Scanner actualizado en ChipAssignmentWidget")
    
    def set_antenna_manager(self, antenna_manager):
        """
        Establecer antenna manager
        
        Args:
            antenna_manager: Instancia de AntennaManager
        """
        self.antenna_manager = antenna_manager
        logger.info("🔄 AntennaManager asignado a TabManager")
    
    def create_all_tabs(self):
        """
        Crear todos los tabs de la aplicación

        Orden de tabs:
        1. Detección
        2. Gestión de Eventos
        3. Asignación de Chips
        4. Competencia
        5. Configuración
        """
        logger.info("=" * 80)
        logger.info("🏗️  Creando todos los tabs")
        logger.info("=" * 80)
        
        try:
            self.create_detection_tab()
            self.create_event_config_tab()
            self.create_chip_assignment_tab()
            self.create_race_monitoring_tab()
            self.create_configuration_tab()

            logger.info(f"✅ {len(self.tabs)} tabs creados exitosamente")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Error creando tabs: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def create_detection_tab(self):
        """Crear tab de detección de chips"""
        logger.info("📡 Creando DetectionTab...")
        
        from ..tabs import DetectionTab
        
        detection_tab = DetectionTab(signals=self.signals)
        self.tab_widget.addTab(detection_tab, "🔍 Detección")
        self.tabs['detection'] = detection_tab
        
        logger.info("✅ DetectionTab creado")
    
    def create_event_config_tab(self):
        """Crear tab de gestión de eventos"""
        logger.info("📋 Creando EventConfigWidget...")

        from ..widgets.event_config_widget import EventConfigWidget

        event_config_widget = EventConfigWidget(race_manager=self.race_manager)
        self.tab_widget.addTab(event_config_widget, "📋 Gestión de Eventos")
        self.tabs['events'] = event_config_widget

        logger.info("✅ EventConfigWidget creado")

    def create_chip_assignment_tab(self):
        """Crear tab de asignación de chips"""
        logger.info("🏷️ Creando ChipAssignmentWidget...")

        from ..widgets.chip_assignment_widget import ChipAssignmentWidget

        chip_widget = ChipAssignmentWidget(
            race_manager=self.race_manager,
            scanner=self.scanner,
            signals=self.signals
        )
        self.tab_widget.addTab(chip_widget, "🏷️ Asignación de Chips")
        self.tabs['chip_assignment'] = chip_widget

        logger.info("✅ ChipAssignmentWidget creado")

    def create_race_monitoring_tab(self):
        """Crear tab de monitoreo de carrera"""
        logger.info("🏃 Creando RaceMonitoringWidget...")

        from ..widgets.race_monitoring_widget import RaceMonitoringWidget

        race_monitoring_widget = RaceMonitoringWidget(race_manager=self.race_manager)
        self.tab_widget.addTab(race_monitoring_widget, "🏃 Competencia")
        self.tabs['race'] = race_monitoring_widget

        logger.info("✅ RaceMonitoringWidget creado")
    
    def create_configuration_tab(self):
        """Crear tab de configuración"""
        logger.info("⚙️  Creando ConfigurationTab...")
        
        from ..tabs import ConfigurationTab
        
        try:
            # Obtener wizard_config desde antenna_manager si existe
            wizard_config = None
            if self.antenna_manager and self.antenna_manager.wizard_config:
                wizard_config = self.antenna_manager.wizard_config
            
            config_tab = ConfigurationTab(
                scanner=self.scanner,
                signals=self.signals,
                wizard_config=wizard_config
            )
            self.tab_widget.addTab(config_tab, "⚙️ Configuración")
            self.tabs['configuration'] = config_tab
            
            logger.info("✅ ConfigurationTab creado")
            
        except Exception as e:
            logger.error(f"❌ Error creando ConfigurationTab: {e}")
            raise
    
    def get_tab(self, name: str):
        """
        Obtener referencia a un tab específico
        
        Args:
            name: Nombre del tab ('detection', 'events', 'race', 'configuration')
        
        Returns:
            Widget del tab o None si no existe
        """
        return self.tabs.get(name)
    
    def apply_config_to_all_tabs(self, config: Dict):
        """
        Aplicar configuración a todos los tabs que la necesiten
        
        Args:
            config: Configuración del wizard con estructura completa
        """
        logger.info("=" * 80)
        logger.info("🔄 Aplicando configuración a todos los tabs")
        logger.info("=" * 80)
        
        antennas_config = config.get('antennas', {})
        
        # Debug
        logger.info(f"📦 Configuración a aplicar:")
        logger.info(f"   Keys: {list(antennas_config.keys())}")
        logger.info(f"   Tipos: {[type(k).__name__ for k in antennas_config.keys()]}")
        
        # 1. Aplicar a DetectionTab
        self._apply_to_detection_tab(antennas_config)
        
        # 2. Aplicar a ConfigurationTab
        self._apply_to_configuration_tab(config)
        
        # 3. Otros tabs (si necesitan config)
        # ...
        
        logger.info("=" * 80)
        logger.info("✅ Configuración aplicada a todos los tabs")
        logger.info("=" * 80)
    
    def _apply_to_detection_tab(self, antennas_config: Dict):
        """Aplicar configuración al DetectionTab"""
        try:
            logger.info("📡 Actualizando DetectionTab...")
            
            detection_tab = self.get_tab('detection')
            if detection_tab and hasattr(detection_tab, 'update_antenna_roles_from_config'):
                detection_tab.update_antenna_roles_from_config(antennas_config)
                logger.info("✅ DetectionTab actualizado")
            else:
                logger.warning("⚠️  DetectionTab no tiene método update_antenna_roles_from_config")
                
        except Exception as e:
            logger.error(f"❌ Error actualizando DetectionTab: {e}")
            import traceback
            traceback.print_exc()
    
    def _apply_to_configuration_tab(self, config: Dict):
        """Aplicar configuración al ConfigurationTab"""
        try:
            logger.info("⚙️  Actualizando ConfigurationTab...")
            
            config_tab = self.get_tab('configuration')
            if config_tab and hasattr(config_tab, 'load_configuration'):
                config_tab.load_configuration(config)
                logger.info("✅ ConfigurationTab actualizado")
            else:
                logger.warning("⚠️  ConfigurationTab no tiene método load_configuration")
                
        except Exception as e:
            logger.error(f"❌ Error actualizando ConfigurationTab: {e}")
            import traceback
            traceback.print_exc()
    
    def get_tab_count(self) -> int:
        """Obtener número de tabs creados"""
        return len(self.tabs)
    
    def get_tab_names(self) -> list:
        """Obtener lista de nombres de tabs"""
        return list(self.tabs.keys())
    
    def has_tab(self, name: str) -> bool:
        """Verificar si existe un tab específico"""
        return name in self.tabs
    
    def __repr__(self) -> str:
        """Representación string del manager"""
        return f"<TabManager: {self.get_tab_count()} tabs ({', '.join(self.get_tab_names())})>"