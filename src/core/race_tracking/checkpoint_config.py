#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuración de checkpoints con kilometraje
src/core/race_tracking/checkpoint_config.py

Define la posición de cada checkpoint dentro del recorrido de una
distancia. El kilometraje es el dato que permite validar detecciones
con ventanas de tiempo físicas: una lectura solo puede ser el CP del
km 7 si pasó tiempo suficiente para correr 7 km.

No hace falta que el km sea exacto: la velocidad máxima plausible ya
da margen (±20% de error en el km no afecta la validación).
"""

from dataclasses import dataclass
from typing import List, Optional

# Pisos de tiempo (segundos) para cualquier validación
MIN_SEGMENT_SECONDS = 3.0
MIN_TOTAL_SECONDS = 5.0


def ref_speed_mps(total_distance_meters: float) -> float:
    """
    Velocidad máxima plausible según el tipo de carrera.

    Es deliberadamente generosa (nivel élite mundial): la ventana solo
    debe rechazar lo físicamente imposible, nunca a un corredor rápido.

    Args:
        total_distance_meters: Distancia TOTAL de la carrera (define el
            tipo: sprint / medio fondo / fondo)

    Returns:
        Velocidad de referencia en m/s
    """
    if total_distance_meters < 800:
        return 12.0   # sprints: ~43 km/h
    elif total_distance_meters < 3000:
        return 8.0    # medio fondo: ~29 km/h
    else:
        return 6.0    # fondo: ~22 km/h


def min_seconds_for_meters(segment_meters: float,
                           total_distance_meters: float,
                           floor: float = MIN_TOTAL_SECONDS) -> float:
    """
    Tiempo mínimo plausible para cubrir un tramo.

    Args:
        segment_meters: Metros del tramo a validar
        total_distance_meters: Distancia total (define la velocidad ref.)
        floor: Piso en segundos (nunca menos que esto)

    Returns:
        Segundos mínimos para aceptar el tramo
    """
    if segment_meters <= 0:
        return floor
    return max(floor, segment_meters / ref_speed_mps(total_distance_meters))


@dataclass
class CheckpointDef:
    """
    Definición de un checkpoint dentro del recorrido.

    Attributes:
        number: Número de checkpoint (1, 2, 3... en orden de recorrido)
        km: Kilómetro del recorrido donde está ubicado (desde largada)
        antenna_port: Puerto de la antena física que lo cubre (None si
            no está asignado; en ese caso se identifica por secuencia)
    """
    number: int
    km: float
    antenna_port: Optional[int] = None

    def __post_init__(self):
        if self.number <= 0:
            raise ValueError("number debe ser >= 1")
        if self.km < 0:
            raise ValueError("km no puede ser negativo")

    def to_dict(self) -> dict:
        return {'number': self.number, 'km': self.km,
                'antenna_port': self.antenna_port}

    @classmethod
    def from_dict(cls, data: dict) -> 'CheckpointDef':
        return cls(
            number=int(data['number']),
            km=float(data['km']),
            antenna_port=data.get('antenna_port'),
        )


def checkpoints_from_list(data: Optional[list]) -> List[CheckpointDef]:
    """Deserializar lista de checkpoints (tolerante a None/errores)"""
    if not data:
        return []
    result = []
    for item in data:
        try:
            result.append(CheckpointDef.from_dict(item))
        except (KeyError, ValueError, TypeError):
            continue
    return sorted(result, key=lambda c: c.number)


def km_for_checkpoint(checkpoints: List[CheckpointDef],
                      number: int) -> Optional[float]:
    """Km de un checkpoint por su número, o None si no está definido"""
    for cp in checkpoints:
        if cp.number == number:
            return cp.km
    return None
