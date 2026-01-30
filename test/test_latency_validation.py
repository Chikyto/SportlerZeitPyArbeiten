#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del Sistema de Latencia y Anti-Duplicados
test/test_latency_validation.py

Prueba los períodos de latencia para evitar lecturas duplicadas
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Agregar src al path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.core.race_tracking.models import Athlete, RaceCategory, RaceStatus
from src.core.race_tracking.race_manager import RaceManager


def test_latencia_misma_antena():
    """Test: Lecturas duplicadas en la misma antena deben ignorarse"""
    print("\n" + "=" * 80)
    print("TEST 1: Lecturas Duplicadas en Misma Antena")
    print("=" * 80)

    # Setup
    manager = RaceManager()
    manager.min_read_interval = timedelta(seconds=3)

    # Crear categoría con atleta
    category = RaceCategory(
        category_id="test",
        name="Test",
        distance=1000.0,
        participants=[Athlete("CHIP001", 101, "Juan Test", "test")]
    )
    manager.add_category(category)
    manager.start_category("test")

    base_time = datetime.now()

    # Primera detección - debe aceptarse
    event1 = manager.process_detection(
        tag_id="CHIP001",
        timestamp=base_time,
        antenna_port=2,
        roles=['start']
    )
    print(f"T+0.0s: {event1 and '✅ ACEPTADA' or '❌ RECHAZADA'} - Primera largada")

    # Segunda detección 1 segundo después - debe rechazarse (< 3s)
    event2 = manager.process_detection(
        tag_id="CHIP001",
        timestamp=base_time + timedelta(seconds=1),
        antenna_port=2,
        roles=['start']
    )
    print(f"T+1.0s: {event2 and '✅ ACEPTADA' or '❌ RECHAZADA'} - Lectura duplicada (1s < 3s)")

    # Tercera detección 4 segundos después - podría aceptarse si no fuera por grace period
    event3 = manager.process_detection(
        tag_id="CHIP001",
        timestamp=base_time + timedelta(seconds=4),
        antenna_port=2,
        roles=['start']
    )
    print(f"T+4.0s: {event3 and '✅ ACEPTADA' or '❌ RECHAZADA'} - Después de intervalo (pero en grace period)")

    # Verificar resultados
    assert event1 is not None, "Primera detección debe aceptarse"
    assert event2 is None, "Segunda detección debe rechazarse (intervalo muy corto)"
    print("\n✅ Test pasado: Latencia por antena funciona correctamente\n")


def test_periodo_gracia_start():
    """Test: Re-largadas dentro del período de gracia deben ignorarse"""
    print("\n" + "=" * 80)
    print("TEST 2: Período de Gracia para START")
    print("=" * 80)

    # Setup
    manager = RaceManager()
    manager.min_read_interval = timedelta(seconds=3)
    manager.start_grace_period = timedelta(seconds=45)

    # Crear categoría con atleta
    category = RaceCategory(
        category_id="test",
        name="Test",
        distance=1000.0,
        participants=[Athlete("CHIP002", 102, "María Test", "test")]
    )
    manager.add_category(category)
    manager.start_category("test")

    base_time = datetime.now()

    # T+0s: Largada normal
    event1 = manager.process_detection(
        tag_id="CHIP002",
        timestamp=base_time,
        antenna_port=2,
        roles=['start']
    )
    print(f"T+0s:   {event1 and '✅ ACEPTADA' or '❌ RECHAZADA'} - Largada normal")

    # T+20s: María vuelve (olvidó algo) - debe rechazarse
    event2 = manager.process_detection(
        tag_id="CHIP002",
        timestamp=base_time + timedelta(seconds=20),
        antenna_port=2,
        roles=['start']
    )
    print(f"T+20s:  {event2 and '✅ ACEPTADA' or '❌ RECHAZADA'} - Volvió a largada (20s < 45s grace period)")

    # T+30s: María pasa por checkpoint - debe aceptarse
    event3 = manager.process_detection(
        tag_id="CHIP002",
        timestamp=base_time + timedelta(seconds=30),
        antenna_port=4,
        roles=['checkpoint']
    )
    print(f"T+30s:  {event3 and '✅ ACEPTADA' or '❌ RECHAZADA'} - Checkpoint normal")

    # T+60s: María pasa por meta - debe aceptarse
    event4 = manager.process_detection(
        tag_id="CHIP002",
        timestamp=base_time + timedelta(seconds=60),
        antenna_port=6,
        roles=['finish']
    )
    print(f"T+60s:  {event4 and '✅ ACEPTADA' or '❌ RECHAZADA'} - Meta normal")

    # Verificar resultados
    assert event1 is not None, "Largada inicial debe aceptarse"
    assert event2 is None, "Re-largada en grace period debe rechazarse"
    assert event3 is not None, "Checkpoint debe aceptarse"
    assert event4 is not None, "Meta debe aceptarse"

    print("\n✅ Test pasado: Período de gracia funciona correctamente\n")


def test_escenario_real_corredor_vuelve():
    """Test: Escenario real - corredor que se olvida algo y vuelve"""
    print("\n" + "=" * 80)
    print("TEST 3: Escenario Real - Corredor Vuelve a Buscar Algo")
    print("=" * 80)

    # Setup
    manager = RaceManager()
    manager.min_read_interval = timedelta(seconds=3)
    manager.start_grace_period = timedelta(seconds=45)

    # Crear categoría con atleta
    category = RaceCategory(
        category_id="10k",
        name="10K",
        distance=10000.0,
        participants=[Athlete("CHIP123", 55, "Pedro Runner", "10k")]
    )
    manager.add_category(category)
    manager.start_category("10k")

    print("\n📖 Historia:")
    print("   Pedro larga normalmente a las 09:00:00")
    print("   A los 15 segundos se da cuenta que olvidó su gel")
    print("   Vuelve corriendo, cruza START nuevamente a los 25s")
    print("   Continúa la carrera normalmente\n")

    base_time = datetime(2025, 1, 30, 9, 0, 0)

    # 09:00:00 - Largada normal
    event1 = manager.process_detection(
        tag_id="CHIP123",
        timestamp=base_time,
        antenna_port=2,
        roles=['start']
    )
    print(f"09:00:00 - START:       {event1 and '✅ Registrado' or '❌ Ignorado'}")

    # 09:00:25 - Vuelve (olvidó gel)
    event2 = manager.process_detection(
        tag_id="CHIP123",
        timestamp=base_time + timedelta(seconds=25),
        antenna_port=2,
        roles=['start']
    )
    print(f"09:00:25 - START:       {event2 and '✅ Registrado' or '❌ Ignorado'} (volvió - dentro de grace period)")

    # 09:05:30 - Checkpoint 1
    event3 = manager.process_detection(
        tag_id="CHIP123",
        timestamp=base_time + timedelta(minutes=5, seconds=30),
        antenna_port=4,
        roles=['checkpoint']
    )
    print(f"09:05:30 - CHECKPOINT:  {event3 and '✅ Registrado' or '❌ Ignorado'}")

    # 09:11:45 - Checkpoint 2
    event4 = manager.process_detection(
        tag_id="CHIP123",
        timestamp=base_time + timedelta(minutes=11, seconds=45),
        antenna_port=5,
        roles=['checkpoint']
    )
    print(f"09:11:45 - CHECKPOINT:  {event4 and '✅ Registrado' or '❌ Ignorado'}")

    # 09:18:22 - Meta
    event5 = manager.process_detection(
        tag_id="CHIP123",
        timestamp=base_time + timedelta(minutes=18, seconds=22),
        antenna_port=6,
        roles=['finish']
    )
    print(f"09:18:22 - FINISH:      {event5 and '✅ Registrado' or '❌ Ignorado'}")

    # Verificar resultado final
    result = manager.get_athlete_result("10k", category.participants[0].athlete_id)
    print(f"\n📊 Resultado Final:")
    print(f"   Atleta: {result.athlete.name}")
    print(f"   Estado: {result.status.value}")
    print(f"   Tiempo Total: {result.get_formatted_time()}")
    print(f"   Checkpoints: {len(result.checkpoint_times)}")

    assert event1 is not None, "Primera largada debe registrarse"
    assert event2 is None, "Re-largada debe ignorarse (grace period)"
    assert event3 is not None, "Checkpoint 1 debe registrarse"
    assert event4 is not None, "Checkpoint 2 debe registrarse"
    assert event5 is not None, "Meta debe registrarse"
    assert result.status.value == "finished", "Estado debe ser 'finished'"
    assert len(result.checkpoint_times) == 2, "Debe tener 2 checkpoints"

    print("\n✅ Test pasado: Escenario real manejado correctamente\n")


def test_configuracion_personalizada():
    """Test: Ajustar períodos según tipo de carrera"""
    print("\n" + "=" * 80)
    print("TEST 4: Configuración Personalizada por Tipo de Carrera")
    print("=" * 80)

    # Carrera de velocidad (100m) - períodos cortos
    print("\n📏 Carrera de Velocidad (100m):")
    manager_sprint = RaceManager()
    manager_sprint.min_read_interval = timedelta(seconds=1)
    manager_sprint.start_grace_period = timedelta(seconds=10)
    print(f"   min_read_interval: {manager_sprint.min_read_interval.total_seconds()}s")
    print(f"   start_grace_period: {manager_sprint.start_grace_period.total_seconds()}s")

    # Ultra Trail (100K) - períodos largos
    print("\n🏔️  Ultra Trail (100K):")
    manager_ultra = RaceManager()
    manager_ultra.min_read_interval = timedelta(seconds=5)
    manager_ultra.start_grace_period = timedelta(minutes=2)
    print(f"   min_read_interval: {manager_ultra.min_read_interval.total_seconds()}s")
    print(f"   start_grace_period: {manager_ultra.start_grace_period.total_seconds()}s")

    # Circuito/Vueltas - sin grace period
    print("\n🔄 Carrera de Vueltas (circuito):")
    manager_laps = RaceManager()
    manager_laps.min_read_interval = timedelta(seconds=2)
    manager_laps.start_grace_period = timedelta(seconds=0)  # Desactivado
    print(f"   min_read_interval: {manager_laps.min_read_interval.total_seconds()}s")
    print(f"   start_grace_period: {manager_laps.start_grace_period.total_seconds()}s (desactivado)")

    print("\n✅ Test pasado: Configuraciones personalizadas creadas\n")


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🧪 TESTS DEL SISTEMA DE LATENCIA Y ANTI-DUPLICADOS")
    print("=" * 80)

    try:
        test_latencia_misma_antena()
        test_periodo_gracia_start()
        test_escenario_real_corredor_vuelve()
        test_configuracion_personalizada()

        print("\n" + "=" * 80)
        print("✅ TODOS LOS TESTS PASARON EXITOSAMENTE")
        print("=" * 80)
        print("\n📚 Ver docs/SISTEMA_LATENCIA_CHIPS.md para más información\n")

    except AssertionError as e:
        print(f"\n❌ Test falló: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
