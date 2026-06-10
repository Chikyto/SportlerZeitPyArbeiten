#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnóstico de la cola de sincronización con el backend.

Muestra el estado de sync_outbox en data/race_event.db: cuántos envíos
salieron, cuántos están pendientes y — lo más útil — qué respondió el
servidor para los que fallaron.

Uso:
    python scripts/show_outbox.py [ruta/al/race_event.db]
"""

import json
import sqlite3
import sys
from pathlib import Path


def main():
    db_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/race_event.db")
    if not db_path.exists():
        print(f"No existe {db_path}")
        return 1

    conn = sqlite3.connect(str(db_path))

    print("=" * 70)
    print(f"COLA DE SINCRONIZACIÓN — {db_path}")
    print("=" * 70)

    rows = conn.execute(
        "SELECT status, COUNT(*) FROM sync_outbox GROUP BY status"
    ).fetchall()
    counts = dict(rows)
    print(f"\nEnviados OK:  {counts.get('sent', 0)}")
    print(f"Pendientes:   {counts.get('pending', 0)}")
    print(f"Descartados:  {counts.get('dead', 0)}")

    problem_rows = conn.execute(
        "SELECT id, kind, status, attempts, created_at, sent_at, last_error, payload"
        " FROM sync_outbox WHERE status != 'sent' OR attempts > 1"
        " ORDER BY id DESC LIMIT 30"
    ).fetchall()

    if problem_rows:
        print("\n" + "-" * 70)
        print("ENVÍOS CON PROBLEMAS (más recientes primero):")
        print("-" * 70)
        for (row_id, kind, status, attempts, created_at,
             sent_at, last_error, payload) in problem_rows:
            try:
                p = json.loads(payload or '{}')
                detail = (f"tag={p.get('tag_id')} tipo={p.get('event_type')} "
                          f"atleta={p.get('athlete_name')}")
            except (ValueError, TypeError):
                detail = ""
            print(f"\n#{row_id} [{kind}] {status.upper()} — {attempts} intento(s)")
            print(f"   Creado: {created_at}")
            if detail.strip():
                print(f"   {detail}")
            if last_error:
                print(f"   Último error: {last_error[:200]}")
    else:
        print("\nSin envíos problemáticos 👍")

    conn.close()
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
