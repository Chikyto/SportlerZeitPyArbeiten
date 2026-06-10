#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reencolar envíos pendientes desde una base archivada.

Cuando se archiva un evento (race_event_backup_*.db), los envíos que
quedaron pendientes en su sync_outbox se archivan con él. Este script
los copia a la base actual (data/race_event.db) como pendientes nuevos;
la app en ejecución los envía en su próximo ciclo (≤10 s).

Uso:
    python scripts/resend_outbox.py data/race_event_backup_XXXX.db
    python scripts/resend_outbox.py data/race_event_backup_XXXX.db --dead
        (--dead reencola también los descartados)

Atención: reenvía los datos al MISMO evento del backend del que salieron.
Si el live fue reseteado o es otro evento, evaluar antes si corresponde.
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    include_dead = '--dead' in sys.argv

    if not args:
        print(__doc__)
        return 1

    source_path = Path(args[0])
    target_path = Path(args[1]) if len(args) > 1 else Path("data/race_event.db")

    if not source_path.exists():
        print(f"No existe {source_path}")
        return 1
    if not target_path.exists():
        print(f"No existe {target_path} — abrí la app al menos una vez")
        return 1

    statuses = "('pending', 'dead')" if include_dead else "('pending')"

    src = sqlite3.connect(str(source_path))
    rows = src.execute(
        f"SELECT kind, url, headers, payload, created_at FROM sync_outbox"
        f" WHERE status IN {statuses} ORDER BY id"
    ).fetchall()
    src.close()

    if not rows:
        print(f"No hay envíos para reencolar en {source_path}")
        return 0

    dst = sqlite3.connect(str(target_path))
    with dst:
        for kind, url, headers, payload, created_at in rows:
            dst.execute(
                "INSERT INTO sync_outbox (kind, url, headers, payload,"
                " status, attempts, created_at, last_error)"
                " VALUES (?,?,?,?,'pending',0,?,?)",
                (kind, url, headers, payload,
                 datetime.now().isoformat(),
                 f"reencolado desde {source_path.name} (original: {created_at})")
            )
    dst.close()

    print(f"✅ {len(rows)} envío(s) reencolado(s) en {target_path}")
    print("   Si la app está abierta, salen en el próximo ciclo (≤10 s).")
    print("   Si no, salen al abrirla.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
