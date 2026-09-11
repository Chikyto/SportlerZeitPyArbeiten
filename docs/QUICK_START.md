# 🏃 Guía Rápida - Sistema de Timing RFID

## 📋 Resumen del Sistema Completo

Todo está listo y funcionando. Aquí tenés la guía completa para usar el sistema.

---

## 🎯 Flujo Completo del Día del Evento

```
1. ANTES → Importar atletas desde Firebase CSV
2. DÍA DEL EVENTO → Asignar chips RFID
3. INICIO → Iniciar categorías
4. DURANTE → Sistema detecta automáticamente
5. RESULTADOS → Visualización en tiempo real
```

---

## 📥 PASO 1: Importar Atletas

### Opción A: Desde Interfaz (Recomendado)

1. **Ejecutar aplicación:**
   ```bash
   python main.py
   ```

2. **Ir al tab:** 🏷️ Asignación de Chips

3. **Click en:** 📥 Importar desde Web

4. **Elegir:** CSV

5. **Seleccionar archivo** exportado de Firebase

6. **¡Listo!** Atletas cargados con dorsales automáticos

### Opción B: Script de Línea de Comandos

```bash
# Importar desde CSV
python scripts/import_csv.py inscriptos.csv

# Resultado:
# ✅ X atletas importados
# ✅ Dorsales asignados automáticamente
# ✅ Lista generada en output/lista_dorsales.csv
```

### Rangos de Dorsales por Categoría

```
5K:    1 - 999
10K:   1000 - 1999
21K:   2000 - 2999
30K:   3000 - 3999
42K:   4000 - 4999
50K:   5000 - 5999
100K:  6000 - 6999
```

---

## 🏷️ PASO 2: Asignar Chips RFID

### En el Tab "Asignación de Chips"

**Método Rápido (Escaneo):**

1. Buscar corredor en la tabla (por nombre o dorsal)
2. Click para seleccionar
3. Click en **📡 Escanear Chip**
4. Acercar chip al lector → **Auto-asigna**
5. Pasa al siguiente

**Método Manual:**

1. Buscar corredor
2. Seleccionar
3. Escribir chip ID manualmente
4. Click **Asignar**

### Validaciones Automáticas

- ✅ No permite asignar mismo chip a 2 atletas
- ✅ Muestra advertencia si chip ya usado
- ✅ Actualiza estado en tiempo real
- 🟨 Amarillo = Pendiente
- 🟩 Verde = Asignado

### Estadísticas en Vivo

```
Progreso General: 45/120 (37.5%)

Por Categoría:
• Ultra 100K: 15/30 (50%)
• Trail 50K: 20/50 (40%)
• Mountain 30K: 10/40 (25%)
```

---

## 🏁 PASO 3: Iniciar Carrera

### Tab "Gestión de Eventos"

1. **Ver categorías cargadas** con participantes
2. **Seleccionar categoría** a iniciar
3. **Click:** Iniciar Categoría Seleccionada
4. **Estado cambia:** PENDING → RUNNING ✅

### Múltiples Categorías

- Podés iniciar varias categorías simultáneamente
- Cada una con su propio timing
- Resultados separados por categoría

---

## 📡 PASO 4: Detección Automática

### Tab "Detección"

1. **Click:** 🟢 Iniciar Detección
2. Scanner lee chips automáticamente
3. Sistema procesa eventos:
   - **START:** Atleta pasa por antena de largada
   - **CHECKPOINT:** Pasa por punto intermedio
   - **FINISH:** Cruza la meta

### Lo que pasa internamente:

```
Chip detectado → Busca atleta → Determina evento → Registra tiempo
```

**Ejemplo:**
```
Tag "7662" detectado en Antena 1 (START)
→ Encuentra: Juan Pérez #125 (100K)
→ Evento: START
→ Registra: start_time = 14:30:25
→ Estado: NOT_STARTED → RUNNING
```

---

## 📊 PASO 5: Resultados en Tiempo Real

### Tab "Competencia"

**3 Pestañas:**

1. **Resumen de Categorías**
   - Estado de cada categoría
   - Participantes en carrera/finalizados
   - Última actividad

2. **Participantes**
   - Tabla completa con todos los corredores
   - Filtros: categoría, estado
   - Búsqueda por nombre/dorsal
   - Tiempos actuales
   - Checkpoints pasados
   - 🟡 En Carrera / 🟢 Finalizado

3. **Estadísticas**
   - Total inscritos/en carrera/finalizados
   - Por categoría
   - Total de detecciones

### Auto-refresh

- Actualiza cada 2 segundos
- Puede pausarse/reactivarse
- No requiere recargar

---

## 🎨 Estados Visuales

### En Tablas

| Color | Estado | Significado |
|-------|--------|-------------|
| 🟨 Amarillo | Pendiente | Sin chip asignado |
| 🟩 Verde | Asignado | Chip asignado, listo |
| ⚪ Blanco | No Iniciado | Esperando largada |
| 🟡 Amarillo | En Carrera | Corriendo ahora |
| 🟢 Verde | Finalizado | Llegó a meta |

---

## 🔧 Configuración de Antenas

### En Wizard (primera vez)

Ya está configurado desde el wizard inicial.

### Roles de Antena

- **START:** Línea de largada
- **FINISH:** Meta/llegada
- **CHECKPOINT:** Puntos intermedios

**Una antena puede tener múltiples roles:**
- Ejemplo: START + FINISH (para circuitos cerrados)

### Presets Disponibles

- Simple Setup (2 antenas: start + finish)
- Circuito Cerrado (start=finish)
- Arco de Meta (4 antenas finish)
- Start + Finish Arcos

---

## 📂 Archivos Importantes

### Input

```
inscriptos.csv          → Exportado de Firebase
config/firebase_config.json → Configuración API (opcional)
```

### Output

```
output/lista_dorsales.csv   → Para imprimir y entregar
output/import_state.json    → Estado de importación
```

### Logs

```
logs/timing.log        → Registro completo del sistema
```

---

## 🐛 Resolución de Problemas

### "No se detectan chips"

1. Verificar scanner conectado
2. Tab Detección → Iniciar Detección
3. Verificar antenas habilitadas

### "Atleta no encontrado"

1. Verificar que el chip está asignado
2. Tab Asignación → Buscar atleta
3. Ver estado de asignación

### "Evento no se registra"

1. Verificar que categoría está RUNNING
2. Verificar rol de antena (start/finish/checkpoint)
3. Ver logs para detalles

### "Dorsales duplicados"

- No puede pasar: sistema usa rangos por categoría
- Si pasa: revisar importación CSV

---

## 📞 Datos Técnicos

### Estructura CSV Esperada

```csv
Nombre,Apellido,Email,DNI,Fecha Nacimiento,Género,Teléfono,Distancia,Estado Pago,...
Juan,Pérez,juan@mail.com,27272828,20/04/1979,M,5.4266E+11,5K,approved,...
```

### Modelos de Datos

**Athlete:**
- athlete_id, tag_id, bib_number, name
- category_id, team, notes

**RaceCategory:**
- category_id, name, distance (metros)
- expected_checkpoints, participants, status

**AthleteResult:**
- start_time, finish_time, total_time
- checkpoint_times, splits, position, status

**DetectionEvent:**
- tag_id, timestamp, antenna_port
- event_type, checkpoint_number

---

## 🚀 Comandos Útiles

```bash
# Importar CSV
python scripts/import_csv.py inscriptos.csv

# Ejecutar aplicación
python main.py

# Ver logs en tiempo real
tail -f logs/timing.log

# Ejecutar tests (si los hay)
pytest test/

# Limpiar caché
find . -type d -name __pycache__ -exec rm -rf {} +
```

---

## ✅ Checklist Día del Evento

### Antes de Empezar

- [ ] CSV exportado de Firebase
- [ ] CSV importado al sistema
- [ ] Todos los atletas con dorsales asignados
- [ ] Lista de dorsales impresa
- [ ] Scanner RFID conectado y probado
- [ ] Antenas configuradas con roles correctos
- [ ] Potencia de antenas configurada

### Durante Asignación de Chips

- [ ] Cada atleta tiene chip RFID
- [ ] Todos aparecen como "Asignado" ✅
- [ ] Progreso 100% en todas las categorías
- [ ] Guardar asignaciones

### Al Iniciar Carrera

- [ ] Categorías creadas
- [ ] Participantes cargados
- [ ] Iniciar detección
- [ ] Iniciar categoría(s)
- [ ] Verificar primera detección

### Durante la Carrera

- [ ] Monitorear Tab Competencia
- [ ] Verificar detecciones en tiempo real
- [ ] Revisar que tiempos se registran
- [ ] Anotar cualquier anomalía

### Al Finalizar

- [ ] Finalizar categorías
- [ ] Verificar clasificaciones
- [ ] Exportar resultados (próximamente)
- [ ] Backup de datos

---

## 💡 Tips y Mejores Prácticas

### Asignación de Chips

- **Orden sugerido:** Por categoría y dorsal
- **Verificación:** Escanear chip antes de asignar
- **Problema:** Si se asignó mal, limpiar y reasignar

### Detección

- **Distancia:** Chip a 5-30cm del lector
- **Velocidad:** Chips se leen hasta 40 km/h
- **Validación:** Revisar primeros 5-10 atletas

### Timing

- **Sincronización:** Verificar hora del sistema
- **Backup:** Tener papel de respaldo para primeros/últimos
- **Internet:** Sistema funciona 100% offline

---

## 🎓 Conceptos Clave

### Máquina de Estados

```
Atleta: NOT_STARTED → RUNNING → FINISHED
Categoría: PENDING → RUNNING → FINISHED
```

### Determinación de Eventos

```
NOT_STARTED + antena START → START (inicia)
RUNNING + antena CHECKPOINT → CHECKPOINT (parcial)
RUNNING + antena FINISH → FINISH (termina)
```

### Cálculo de Tiempos

```
Total Time = finish_time - start_time
Split Time = checkpoint_time - start_time
```

---

## 📖 Documentación Adicional

- `docs/WEB_INTEGRATION_ARCHITECTURE.md` - Integración web
- `docs/INTEGRATION_GUIDE.md` - Guía Cloud Run + Vercel
- `README.md` - Información general del proyecto

---

## 🎯 ¡Listo para el Evento!

Todo está implementado y funcionando:

✅ Importación de atletas desde Firebase
✅ Generación automática de dorsales
✅ Asignación de chips RFID
✅ Detección automática de eventos
✅ Timing preciso con checkpoints
✅ Resultados en tiempo real
✅ Clasificación automática
✅ Múltiples categorías simultáneas

**¡Que tengas un gran evento! 🏁**
