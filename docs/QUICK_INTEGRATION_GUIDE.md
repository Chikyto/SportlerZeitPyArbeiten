# Guía Rápida de Integración

**Tiempo estimado**: 15 minutos

---

## 🎯 Objetivo

Conectar el Sistema de Timing RFID con tu Plataforma de Registro en 5 pasos simples.

---

## 📋 Pre-requisitos

- [ ] Sistema de Timing instalado y funcionando
- [ ] Acceso a la Plataforma de Registro
- [ ] Credenciales de API (URL, API Key, Event ID)

---

## 🚀 Paso a Paso

### 1. Obtener Credenciales (5 min)

Contacta al administrador de la plataforma y solicita:

- **API URL**: URL del backend (ej: `https://your-backend.run.app`)
- **API Key**: Clave de autenticación
- **Event ID**: Identificador de tu evento

**Dónde obtenerlas**:
- Panel de administración de la plataforma
- Email de bienvenida
- Contactar soporte técnico

---

### 2. Configurar Integración (2 min)

```bash
# 1. Copiar template
cd SportlerZeitPyArbeiten
cp config/api_config_template.json config/api_config.json

# 2. Editar configuración
# Abrir config/api_config.json y completar:
```

```json
{
  "api_url": "https://tu-backend.run.app",
  "api_key": "tu-api-key-aqui",
  "event_id": "tu-evento-id",
  "sync_enabled": true
}
```

---

### 3. Probar Conexión (3 min)

```bash
# Ejecutar script de testing
python scripts/test_integration.py
```

**Resultado esperado**:
```
======================================================================
  Test de Integración - Sistema de Timing ↔ Plataforma de Registro
======================================================================

[1/6] Cargando configuración...
[2/6] Probando conectividad...
[3/6] Verificando autenticación...
[4/6] Probando GET /categories...
[5/6] Probando GET /athletes...
[6/6] Probando POST /detection...

======================================================================
  Resultados
======================================================================

✓ Load Config: Configuración cargada: https://...
✓ Connectivity: Servidor accesible (HTTP 200)
✓ Authentication: API Key válido
✓ GET Categories: ✓ 3 categorías encontradas
✓ GET Athletes: ✓ 150 atletas encontrados
✓ POST Detection: ✓ Endpoint funcional (HTTP 200)

──────────────────────────────────────────────────────────────────
✓ Todos los tests pasaron (6/6)
  La integración está lista para usar!
======================================================================
```

---

### 4. Importar Participantes (3 min)

1. Abrir sistema de timing
2. Ir a tab **"Configuración de Evento"**
3. Click en botón **"📥 Importar desde Sistema Web"**
4. Esperar importación (5-30 segundos según cantidad)
5. Verificar que aparecen todas las categorías y atletas

**¿Qué se importa?**
- ✅ Categorías/Distancias
- ✅ Participantes con todos sus datos
- ✅ Información de contacto
- ✅ Datos médicos (si están disponibles)

---

### 5. ¡Listo! (2 min)

**Durante el evento**:

1. **Asignar chips**: Tab "Asignación de Chips"
2. **Iniciar carrera**: Click "Iniciar Carrera"
3. **Detecciones automáticas**: Sistema envía a plataforma en tiempo real
4. **Resultados en vivo**: Familiares ven en web

**Después del evento**:

5. **Exportar resultados**: Click "Exportar PDF"
6. **Publicar finales**: Click "Publicar Resultados Finales"

---

## ✅ Checklist Final

- [ ] `config/api_config.json` creado y completado
- [ ] `python scripts/test_integration.py` → Todos los tests pasaron
- [ ] Importación de participantes exitosa
- [ ] Chips asignados a participantes
- [ ] Verificar que detecciones aparecen en plataforma web

---

## 🐛 Troubleshooting

### Error: "No se pudo conectar al servidor"

**Causa**: URL incorrecta o servidor caído

**Solución**:
1. Verificar URL en `config/api_config.json`
2. Probar abrir URL en navegador
3. Contactar soporte de la plataforma

---

### Error: "API Key inválido (HTTP 401)"

**Causa**: API Key incorrecta o expirada

**Solución**:
1. Verificar API Key en config
2. Regenerar API Key en plataforma
3. Verificar que no haya espacios extra

---

### Error: "Evento no encontrado (HTTP 404)"

**Causa**: Event ID incorrecto

**Solución**:
1. Verificar Event ID en config
2. Consultar ID correcto en plataforma
3. Verificar que el evento esté activo

---

### Error: "Respuesta sin campo 'athletes'"

**Causa**: Formato de API diferente al esperado

**Solución**:
1. Contactar soporte técnico
2. Compartir respuesta de API
3. Ajustar mapeo de campos (requiere desarrollo)

---

### No se importan atletas (0 encontrados)

**Causa**: No hay participantes inscritos en plataforma

**Solución**:
1. Verificar que hay inscripciones en la plataforma
2. Verificar filtros (categoría, estado de pago)
3. Usar importación CSV manual como alternativa

---

### Detecciones no aparecen en web

**Causa**: Problema de sincronización

**Solución**:
1. Verificar `sync_enabled: true` en config
2. Revisar logs del sistema: `timing_system.log`
3. Verificar conectividad a internet
4. Sistema local sigue funcionando (datos en SQLite)

---

## 📞 Soporte

### Problemas con Sistema de Timing
- GitHub Issues: [enlace]
- Email: [tu-email]

### Problemas con Plataforma de Registro
- Contactar a tu proveedor de plataforma
- Email de soporte técnico
- Chat en vivo (si disponible)

---

## 📚 Documentación Completa

Para información detallada, ver:

- **Arquitectura completa**: `docs/SISTEMA_COMPLETO_Y_INTEGRACION.md`
- **Requisitos de API**: `docs/API_REQUIREMENTS.md`
- **Casos de uso**: Ver sección 8 en documento principal

---

## 🎉 Modo Standalone (Sin Integración)

**¿No tienes plataforma de registro?**

El sistema funciona perfectamente sin integración:

1. **Crear CSV manual** con participantes:
   ```csv
   bib_number,name,gender,birth_date,category_id
   1,Juan Pérez,M,1990-05-15,5k
   2,María González,F,1985-03-20,5k
   ```

2. **Importar CSV**: Click "Importar CSV" en evento

3. **Asignar chips** y correr carrera normalmente

4. **Exportar PDF** al finalizar

---

**¡Buena suerte con tu evento! 🏃‍♂️🏃‍♀️**
