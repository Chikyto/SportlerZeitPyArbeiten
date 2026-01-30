# Sistema de Latencia y Anti-Duplicados para Detección de Chips

## 📋 Descripción General

El sistema implementa **períodos de latencia** para evitar lecturas duplicadas y falsas detecciones, similar a sistemas profesionales de cronometraje como ChronoTrack, MyLaps, y Race Result.

## 🎯 Problemas que Resuelve

### 1. **Lecturas Duplicadas del Hardware**
- Los lectores RFID pueden detectar el mismo chip múltiples veces en un segundo
- **Solución**: Intervalo mínimo de 3 segundos entre lecturas en la misma antena

### 2. **Corredores que Vuelven a la Largada**
**Escenario real:**
```
09:00:00 - Juan larga normalmente
09:00:15 - Se da cuenta que olvidó su gel energético
09:00:30 - Vuelve corriendo, cruza la línea de largada nuevamente
```
**Sin protección**: El sistema registraría 2 largadas → datos incorrectos
**Con protección**: La segunda largada se ignora (dentro del período de gracia)

- **Solución**: Período de gracia de 45 segundos después de largar

## ⚙️ Configuración

### Parámetros Ajustables

En `src/core/race_tracking/race_manager.py`:

```python
# Intervalo mínimo entre lecturas en la misma antena
self.min_read_interval = timedelta(seconds=3)

# Período de gracia después de largar (evita re-largadas)
self.start_grace_period = timedelta(seconds=45)
```

### Valores Recomendados por Tipo de Carrera

| Tipo de Carrera | min_read_interval | start_grace_period | Notas |
|-----------------|-------------------|-------------------|--------|
| **Velocidad** (100m, 200m) | 1-2 segundos | 10-15 segundos | Carreras muy cortas |
| **Media Distancia** (5K, 10K) | 2-3 segundos | 30-45 segundos | Balance estándar |
| **Larga Distancia** (21K, 42K) | 3-5 segundos | 45-60 segundos | Más margen |
| **Ultra Trail** (50K+) | 3-5 segundos | 60-120 segundos | Máximo margen |
| **Circuitos/Vueltas** | 2-3 segundos | 0 segundos* | *Ver nota abajo |

**⚠️ Nota para Circuitos:** En carreras de vueltas (ej: NASCAR, atletismo en pista), desactiva el `start_grace_period` poniendo `timedelta(seconds=0)` ya que los corredores pasarán legítimamente por START múltiples veces.

## 🔍 Lógica de Validación

### Flujo de Procesamiento

```
1. Chip detectado en antena
   ↓
2. ¿Mismo chip/antena hace menos de 3 seg?
   → SÍ: IGNORAR (lectura duplicada)
   → NO: continuar
   ↓
3. ¿Es antena de START?
   → NO: ACEPTAR
   → SÍ: continuar
   ↓
4. ¿El corredor ya largó hace menos de 45 seg?
   → SÍ: IGNORAR (probablemente volvió)
   → NO: ACEPTAR (nueva largada válida)
```

### Logs Informativos

El sistema genera logs para auditoría:

```
⏱️  Detección ignorada (muy reciente): Juan Pérez en antena 2 (1.2s desde última lectura)
🔄 START ignorado (periodo de gracia): María López (18.5s desde largada) - Probablemente volvió a buscar algo
```

## 📊 Ejemplos de Uso

### Caso 1: Corredor que Vuelve

```python
# T+0s: Juan larga normalmente
09:00:00 - Detección START antena_2 → ✅ ACEPTADA (primera largada)

# T+20s: Juan vuelve (olvidó algo)
09:00:20 - Detección START antena_2 → ❌ IGNORADA (dentro de los 45s de gracia)

# T+120s: Juan pasa por checkpoint
09:02:00 - Detección CHECKPOINT antena_4 → ✅ ACEPTADA (corriendo normalmente)
```

### Caso 2: Lecturas Duplicadas del Hardware

```python
# El lector RFID detecta el chip 3 veces en 0.8 segundos
09:00:00.000 - Detección → ✅ ACEPTADA
09:00:00.400 - Detección → ❌ IGNORADA (0.4s < 3s)
09:00:00.800 - Detección → ❌ IGNORADA (0.8s < 3s)
```

## 🔧 Personalización Avanzada

### Ajustar Períodos según Evento

```python
# Para una carrera de 100m (muy corta)
race_manager.min_read_interval = timedelta(seconds=1)
race_manager.start_grace_period = timedelta(seconds=10)

# Para un ultra trail (muy larga)
race_manager.min_read_interval = timedelta(seconds=5)
race_manager.start_grace_period = timedelta(seconds=120)

# Para circuitos/vueltas (START = contador de vueltas)
race_manager.start_grace_period = timedelta(seconds=0)  # Desactivado
```

### Desactivar Validaciones (Solo para Testing)

```python
# ⚠️ NO recomendado en producción
race_manager.min_read_interval = timedelta(seconds=0)
race_manager.start_grace_period = timedelta(seconds=0)
```

## 🏭 Comparación con Sistemas Comerciales

| Sistema | Intervalo Mínimo | Período de Gracia START | Notas |
|---------|------------------|------------------------|--------|
| **ChronoTrack** | 2-3 segundos | 30-60 segundos | Configurable por evento |
| **MyLaps** | 1-2 segundos | 45 segundos | Detección basada en estado |
| **Race Result** | 2-5 segundos | 60 segundos | Múltiples algoritmos |
| **SportlerZeit (este sistema)** | **3 segundos** | **45 segundos** | Configurable, código abierto |

## 📚 Referencias

- ChronoTrack Technical Specifications
- MyLaps RFID Timing Documentation
- IAAF Competition Rules - Electronic Timing
- USATF Certification Standards

## ✅ Testing

Ver `test/test_latency_validation.py` para casos de prueba completos.
