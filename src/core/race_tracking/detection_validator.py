#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador de detecciones con ventanas de tiempo
src/core/race_tracking/detection_validator.py

Resuelve qué evento de carrera representa una lectura RFID (largada,
checkpoint N, meta) según los roles de la antena, el estado del atleta
y ventanas de tiempo físicas.

Principios:
- Las ventanas solo rechazan lo FÍSICAMENTE IMPOSIBLE (ej: "CP del km 7
  a los 30 segundos de largar"). Nunca hay ventana máxima: un corredor
  lento o lesionado llega tarde a todo, pero llega.
- Con checkpoints definidos (km + antena), cada CP se identifica por su
  antena física: si al corredor no le leyeron el CP1, su lectura en el
  CP2 se registra como CP2 (no corre la numeración).
- Una lectura repetida en el mismo CP nunca puede convertirse en el CP
  siguiente: el tramo entre ambos a tiempo ~cero es imposible.
- Lo rechazado queda registrado en el log y en el journal crudo
  (data/detections_*.jsonl): nada se pierde de verdad.
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from .models import AthleteStatus, EventType, RaceDistance, AthleteResult
from .checkpoint_config import (
    CheckpointDef, km_for_checkpoint,
    min_seconds_for_meters, MIN_SEGMENT_SECONDS
)

logger = logging.getLogger(__name__)


def resolve_event(
    roles: List[str],
    antenna_port: int,
    result: AthleteResult,
    distance: RaceDistance,
    timestamp: datetime,
) -> Tuple[Optional[EventType], Optional[int], str]:
    """
    Determinar el evento que representa una lectura.

    Args:
        roles: Roles de la antena ['start', 'checkpoint', 'finish']
        antenna_port: Puerto de la antena que leyó
        result: Resultado actual del atleta
        distance: Distancia en la que compite
        timestamp: Momento de la lectura

    Returns:
        (EventType, checkpoint_number, motivo). Si EventType es None,
        el motivo explica el rechazo.
    """
    # --- Largada ---
    if 'start' in roles and result.status == AthleteStatus.NOT_STARTED:
        return EventType.START, None, 'ok'

    if result.status != AthleteStatus.RUNNING:
        return None, None, (
            f"estado {result.status.value} no admite eventos "
            f"con roles {roles}"
        )

    # --- En carrera: meta tiene prioridad si su ventana es válida ---
    finish_reason = None
    if 'finish' in roles:
        ok, finish_reason = _validate_finish(result, distance, timestamp)
        if ok:
            return EventType.FINISH, None, 'ok'
        # Meta prematura: si la antena también es checkpoint, evaluar
        # como checkpoint en vez de descartar la lectura (antes este
        # caso se perdía por completo)

    if 'checkpoint' in roles:
        cp_number, cp_reason = _resolve_checkpoint(
            antenna_port, result, distance, timestamp
        )
        if cp_number is not None:
            return EventType.CHECKPOINT, cp_number, 'ok'
        if finish_reason:
            return None, None, f"{finish_reason}; {cp_reason}"
        return None, None, cp_reason

    if finish_reason:
        return None, None, finish_reason

    return None, None, f"roles {roles} no aplican al estado del atleta"


def _validate_finish(result: AthleteResult, distance: RaceDistance,
                     timestamp: datetime) -> Tuple[bool, str]:
    """Ventana de tiempo para la meta: distancia total a velocidad máxima"""
    if not result.start_time:
        return False, "sin hora de largada registrada"

    elapsed = (timestamp - result.start_time).total_seconds()
    min_secs = min_seconds_for_meters(
        distance.distance_meters, distance.distance_meters
    )
    if elapsed < min_secs:
        return False, (
            f"meta prematura: {elapsed:.1f}s < mínimo {min_secs:.0f}s "
            f"para {distance.distance_meters:.0f}m"
        )
    return True, 'ok'


def _resolve_checkpoint(
    antenna_port: int,
    result: AthleteResult,
    distance: RaceDistance,
    timestamp: datetime,
) -> Tuple[Optional[int], str]:
    """
    Determinar QUÉ checkpoint es esta lectura, y validar su ventana.

    Con checkpoints definidos (km), el CP se identifica por la antena
    física si está asignada, o por secuencia si no. Sin definiciones,
    se mantiene el comportamiento histórico (secuencial sin ventana).
    """
    defs = getattr(distance, 'checkpoints', None) or []

    # --- Sin definiciones: comportamiento histórico (secuencial) ---
    if not defs:
        return len(result.checkpoint_times) + 1, 'ok'

    # --- Identificar el candidato ---
    by_port = [cp for cp in defs if cp.antenna_port == antenna_port]
    if by_port:
        # CP identificado por antena física: el primero de esta antena
        # que el atleta aún no registró (soporta varios CP por antena)
        pending = [cp for cp in sorted(by_port, key=lambda c: c.number)
                   if cp.number not in result.checkpoint_times]
        if not pending:
            return None, (
                f"todos los CP de la antena {antenna_port} ya registrados "
                f"para {result.athlete.name}"
            )
        candidate = pending[0]
    else:
        # Antena sin CP asignado: secuencial sobre las definiciones
        next_num = len(result.checkpoint_times) + 1
        candidate = next((cp for cp in defs if cp.number == next_num), None)
        if candidate is None:
            return None, (
                f"CP{next_num} no está definido en el recorrido "
                f"({len(defs)} checkpoints configurados)"
            )

    # --- Ventana 1: tiempo total desde la largada ---
    if not result.start_time:
        return None, "sin hora de largada registrada"

    elapsed_total = (timestamp - result.start_time).total_seconds()
    min_total = min_seconds_for_meters(
        candidate.km * 1000.0, distance.distance_meters
    )
    if elapsed_total < min_total:
        return None, (
            f"CP{candidate.number} (km {candidate.km}) prematuro: "
            f"{elapsed_total:.1f}s desde largada < mínimo {min_total:.0f}s"
        )

    # --- Ventana 2: tiempo del tramo desde el último punto cronometrado ---
    prev_km, prev_ts = _previous_timing_point(result, defs, candidate)
    segment_secs = (timestamp - prev_ts).total_seconds()
    min_segment = min_seconds_for_meters(
        (candidate.km - prev_km) * 1000.0,
        distance.distance_meters,
        floor=MIN_SEGMENT_SECONDS,
    )
    if segment_secs < min_segment:
        return None, (
            f"CP{candidate.number} (km {candidate.km}) imposible: "
            f"tramo de {candidate.km - prev_km:.1f}km en {segment_secs:.1f}s "
            f"(mínimo {min_segment:.0f}s) — probable relectura"
        )

    return candidate.number, 'ok'


def _previous_timing_point(
    result: AthleteResult,
    defs: List[CheckpointDef],
    candidate: CheckpointDef,
) -> Tuple[float, datetime]:
    """
    Último punto cronometrado ANTES del candidato: el CP registrado de
    mayor km menor al del candidato, o la largada (km 0).
    """
    prev_km = 0.0
    prev_ts = result.start_time

    for number, ts in result.checkpoint_times.items():
        km = km_for_checkpoint(defs, number)
        if km is None or ts is None:
            continue
        if prev_km <= km < candidate.km:
            prev_km = km
            prev_ts = ts

    return prev_km, prev_ts


def checkpoint_km_for_event(distance: Optional[RaceDistance],
                            checkpoint_number: Optional[int]) -> Optional[float]:
    """
    Km del checkpoint de un evento (para enviar al backend / mostrar).

    Returns:
        float con el km, o None si no hay definición
    """
    if not distance or checkpoint_number is None:
        return None
    defs = getattr(distance, 'checkpoints', None) or []
    return km_for_checkpoint(defs, checkpoint_number)
