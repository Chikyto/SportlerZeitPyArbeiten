# Importación web para asignación de chips

## Qué se modificó

- La pantalla **Asignación de chips** acepta `config/api_config.json` tanto en
  formato plano como en el formato anidado `cloud` generado al importar un
  archivo `.szconfig`.
- La URL exportada por el frontend, que termina en `/api/v1`, se normaliza antes
  de consultar el endpoint de compatibilidad del hardware.

## Flujo y endpoint

1. En **Configuración**, importar el `.szconfig` generado para el evento.
2. En **Asignación de chips**, seleccionar **Importar desde Web**.
3. La aplicación ejecuta `GET /api/events/{event_id}/athletes` con
   `Authorization: Bearer <token>`.

El backend devuelve inscripciones con pago aprobado y dorsal, además de atletas
creados exclusivamente para timing. Los chips existentes llegan en `chip_code`.

## Cómo probar

```powershell
python -m unittest test.test_athlete_importer_api
```

Para la prueba manual, usar un `.szconfig` vigente cuyo token corresponda al
mismo `event_id`, importar desde Web y verificar dorsales y chips en la tabla.

## Riesgos y supuestos

- Los inscriptos pendientes o sin dorsal no aparecen por diseño del backend.
- Un token revocado o perteneciente a otro evento devuelve un error de
  autenticación/autorización.
