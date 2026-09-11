# 🏃 Flujo de Trabajo - SportlerZeit

Guía paso a paso para preparar y ejecutar un evento de cronometraje con SportlerZeit.

---

## 📊 Vista General del Flujo

```
1. ⚙️  Configuración
   ↓
2. 📋 Gestión de Eventos
   ↓
3. 🏷️  Asignación de Chips
   ↓
4. 🏃 Competencia
   ↓
5. 🔍 Detección (Opcional - Debug)
```

---

## 1️⃣ Configuración (Primera Solapa)

### Objetivo
Conectar el lector RFID y configurar las antenas.

### Pasos

#### a) Conectar Lector RFID
1. Conectar el lector YR9011 por USB
2. En la solapa **⚙️ Configuración**, hacer clic en **"Conectar Scanner"**
3. Verificar que aparezca el mensaje: **"✅ Scanner conectado"**

#### b) Configurar Antenas
Definir el rol de cada antena según tu setup:

| Puerto | Rol | Ejemplo |
|--------|-----|---------|
| **Antena 2** | START | Línea de largada |
| **Antena 4** | CHECKPOINT | Control intermedio |
| **Antena 5** | CHECKPOINT | Segundo control |
| **Antena 6** | FINISH | Línea de meta |

**Opciones de rol:**
- 🟢 **START**: Línea de largada
- 🏁 **FINISH**: Línea de meta
- 🔵 **CHECKPOINT**: Puntos intermedios de control
- ⚫ **DISABLED**: Antena deshabilitada

**Notas:**
- Puedes tener múltiples antenas en START (ej: largada amplia)
- Puedes tener múltiples antenas en FINISH (ej: meta amplia)
- Los checkpoints se numeran automáticamente según el orden de paso

---

## 2️⃣ Gestión de Eventos (Segunda Solapa)

### Objetivo
Crear el evento deportivo y definir las categorías/distancias.

### Pasos

#### a) Información del Evento
1. Ir a la solapa **📋 Gestión de Eventos**
2. Completar:
   - **Nombre del evento**: "Ultra Trail Patagonia 2025"
   - **Fecha**: 2025-02-15

#### b) Crear Categorías
Hacer clic en **"Agregar Categoría"** y definir:

**Ejemplo 1: Ultra 100K**
- **ID**: `100k`
- **Nombre**: Ultra 100K
- **Distancia**: 100 km
- **Hora Largada**: 06:00
- **Checkpoints esperados**: 5

**Ejemplo 2: Trail 50K**
- **ID**: `50k`
- **Nombre**: Trail 50K
- **Distancia**: 50 km
- **Hora Largada**: 08:00
- **Checkpoints esperados**: 3

**Ejemplo 3: Media Maratón**
- **ID**: `21k`
- **Nombre**: Media Maratón
- **Distancia**: 21.1 km
- **Hora Largada**: 09:00
- **Checkpoints esperados**: 1

#### c) Registrar Participantes (Opcional)
Puedes registrar participantes manualmente:
- **Chip ID**: (dejar vacío por ahora)
- **Categoría**: Seleccionar de la lista
- **Nombre**: Nombre del corredor
- Hacer clic en **"Registrar"**

**Nota:** Los chips se asignan en el siguiente paso.

---

## 3️⃣ Asignación de Chips (Tercera Solapa)

### Objetivo
Asignar chips RFID a cada corredor.

### Pasos

#### Método 1: Escaneo en Vivo (Recomendado)
1. Ir a la solapa **🏷️ Asignación de Chips**
2. Hacer clic en **"Iniciar Escaneo"**
3. El sistema mostrará cada chip detectado
4. Seleccionar el corredor en la lista
5. Hacer clic en **"Asignar Chip"**
6. Repetir para cada participante

**Ventaja:** Rápido y sin errores de tipeo

#### Método 2: Asignación Manual
1. Seleccionar corredor en la lista
2. Ingresar Chip ID manualmente
3. Hacer clic en **"Asignar Manualmente"**

**Ventaja:** Útil si ya tienes la lista de chips

#### Verificación
- La columna **"Chips Asignados"** debe mostrar: `45/50` (ejemplo)
- **No es necesario tener todos los chips asignados para iniciar la carrera**
  - Algunos corredores pueden no presentarse
  - Algunos pueden olvidar su chip
  - La carrera se puede iniciar igual

---

## 4️⃣ Competencia (Cuarta Solapa)

### Objetivo
Iniciar las carreras y monitorear resultados en tiempo real.

### Pasos

#### a) Iniciar Categoría
1. Ir a la solapa **🏃 Competencia**
2. Seleccionar la categoría en la tabla
3. Hacer clic en **"Iniciar Categoría Seleccionada"**
4. La carrera comenzará a cronometrar

**El sistema mostrará:**
```
🚀 Categoría iniciada: Ultra 100K
   📊 Participantes: 50 | Chips: 45 asignados, 5 pendientes
```

#### b) Monitoreo en Vivo
La tabla de resultados se actualiza automáticamente cuando:
- Un corredor larga (START)
- Pasa por un checkpoint (CHECKPOINT)
- Llega a meta (FINISH)

**Información mostrada:**
- **Posición**: Clasificación actual
- **Dorsal**: Número de corredor
- **Nombre**: Nombre del atleta
- **Estado**: Not Started / Running / Finished
- **Tiempo**: Tiempo actual o final
- **Checkpoints**: Número de controles pasados

#### c) Eventos en Tiempo Real
Panel lateral muestra:
```
[09:00:15] 🟢 START - Juan Pérez (#101)
[09:05:42] 🔵 CHECKPOINT 1 - María López (#102)
[09:18:33] 🏁 FINISH - Pedro Ruiz (#103) - 18:33.250
```

#### d) Finalizar Categoría
Cuando todos hayan terminado:
1. Seleccionar la categoría
2. Hacer clic en **"Finalizar Categoría Seleccionada"**
3. Se genera la clasificación final

---

## 5️⃣ Detección (Quinta Solapa - Opcional)

### Objetivo
Debugging y auditoría de lecturas de chips.

### Uso
- Ver historial completo de todas las detecciones
- Filtrar por categoría, chip, antena
- Verificar lecturas duplicadas o problemáticas
- Auditar tiempos ante protestas

**Ejemplo de uso:**
```
Si un corredor protesta su tiempo, puedes:
1. Buscar su chip ID
2. Ver todas sus detecciones
3. Verificar timestamps exactos
4. Comprobar si hubo problemas técnicos
```

---

## 🎯 Flujo Completo - Ejemplo Práctico

### Evento: Trail Running 2025
**Día anterior al evento:**

1. **⚙️ Configuración**
   - Conectar lector RFID
   - Configurar antenas:
     - Puerto 2: START
     - Puerto 4: CHECKPOINT
     - Puerto 6: FINISH

2. **📋 Gestión de Eventos**
   - Crear evento "Trail Running 2025"
   - Crear categoría "21K" (21 km, 1 checkpoint)
   - Importar lista de inscritos

3. **🏷️ Asignación de Chips**
   - Iniciar escaneo
   - Asignar chips a cada corredor
   - Verificar: 47/50 chips asignados ✅

**Día del evento:**

4. **🏃 Competencia**
   - 09:00 - Iniciar categoría "21K"
   - Monitorear en tiempo real
   - Los corredores largan, pasan checkpoint, llegan a meta
   - 10:30 - Finalizar categoría
   - Exportar resultados

5. **🔍 Detección** (si es necesario)
   - Verificar tiempos ante dudas
   - Auditar detecciones

---

## ⚡ Características Automáticas

### Sistema de Latencia (Anti-Duplicados)
El sistema automáticamente:
- ✅ Ignora lecturas duplicadas (< 3 segundos en misma antena)
- ✅ Ignora si un corredor vuelve a START (< 45 segundos desde largada)
  - Ejemplo: Olvidó gel energético, vuelve a buscarlo

Ver `docs/SISTEMA_LATENCIA_CHIPS.md` para detalles.

### Sincronización entre Solapas
- Asignar chip → Actualiza Gestión de Eventos
- Iniciar categoría → Actualiza Competencia
- Todo se sincroniza automáticamente

---

## 🔧 Configuración Avanzada

### Ajustar Períodos de Latencia
```python
# Para carreras de velocidad (100m, 200m)
race_manager.min_read_interval = timedelta(seconds=1)
race_manager.start_grace_period = timedelta(seconds=10)

# Para ultra trails (50K+)
race_manager.min_read_interval = timedelta(seconds=5)
race_manager.start_grace_period = timedelta(minutes=2)
```

### Circuitos/Vueltas
Si los corredores pasan múltiples veces por START:
```python
race_manager.start_grace_period = timedelta(seconds=0)  # Desactivar
```

---

## 📚 Documentación Relacionada

- `docs/SISTEMA_LATENCIA_CHIPS.md` - Sistema anti-duplicados
- `docs/README.md` - Documentación general
- `test/` - Tests y ejemplos de código

---

## ✅ Checklist Pre-Evento

**1 semana antes:**
- [ ] Hardware conectado y testeado
- [ ] Antenas configuradas
- [ ] Evento creado con todas las categorías
- [ ] Lista de inscritos importada

**1 día antes:**
- [ ] Asignación de chips completada (o al menos 80%)
- [ ] Prueba de alcance de antenas en el terreno
- [ ] Backup de base de datos

**Día del evento:**
- [ ] Sistema encendido 1 hora antes
- [ ] Verificar que todas las antenas detectan
- [ ] Iniciar categorías a horario
- [ ] Monitoreo continuo

**Post-evento:**
- [ ] Exportar resultados
- [ ] Backup de datos
- [ ] Verificar protestas si las hay
