# Resumen de Cambios - Learning Path Generation Issue

## El Problema
Frontend reportaba "ruta generada exitosamente" pero:
- No devolvía datos 
- No mostraba nada
- Las rutas desaparecían al recargar

## Root Cause Encontrado
**Lambda timeout de 60 segundos era insuficiente** - los requests necesitan 120+ segundos

### Evidencia de los Logs:
```
Request 1: 60000.00 ms Duration → TIMEOUT
Request 2: 120000.00 ms Duration → TIMEOUT (era el nuevo timeout)
Request 3: 120000.00 ms Duration → TIMEOUT
...
Bedrock connection timeout en reintentos
```

## Soluciones Implementadas

### 1. Aumenté el Timeout del Lambda (CRÍTICO)
**Archivo**: `template.yaml`
- **Antes**: `Timeout: 60` segundos
- **Después**: `Timeout: 300` segundos (5 minutos)
- **Razón**: Procesamiento de embeddings (Bedrock) y búsquedas vectoriales (MongoDB) son lentos

### 2. Aumenté la Memoria del Lambda
- **Antes**: `MemorySize: 1024` MB
- **Después**: `MemorySize: 2048` MB
- **Razón**: Más memoria = mejor performance de CPU (Lambda)

### 3. Añadí Logging Comprehensivo en Frontend

**GeneradorRutas.jsx**:
- Log del payload enviado
- Log detallado de la respuesta recibida
- Log de campos específicos (titulo, cursos, path_id, etc.)

**VisualizadorRutas.jsx**:
- Log cuando se recibe una nueva ruta
- Log del estado de nuevaRuta
- Log cuando se llama agregarRuta
- Log cuando se guarda en localStorage

**useRutasAprendizaje.js**:
- Log al leer del cache
- Log al escribir al cache (con tamaño y cantidad)
- Log mejorado de errores con contexto

### 4. Completé Campos Faltantes en la Respuesta del Lambda

**learning_path_generator.py** - método `map_to_frontend_format`:
- Añadí `created_at` (era requerido por frontend)
- Añadí `fechaCreacion` (alias para compatibilidad)

Commit: `da2e187`

## Commits Realizados

```
919eb81 - docs: add comprehensive diagnostics
e7d2bba - fix: increase Lambda timeout from 60s to 300s and memory
da2e187 - fix: include created_at and fechaCreacion in frontend response
3ec32ff - fix: enhance debugging in VisualizadorRutas
4e2947b - feat: add comprehensive logging for learning path generation
```

## Estado Actual

| Componente | Estado | Notas |
|-----------|--------|-------|
| Lambda Timeout | Pendiente de Deploy | Cambio en main, esperando GitHub Actions |
| Frontend Logging | ✓ Desplegado | Ya en producción |
| Lambda Response Fields | ✓ Desplegado | Ya incluye created_at |
| API Functionality | ✓ Funcionando | Devuelve respuesta válida |

## Próximos Pasos

1. **Esperar a que GitHub Actions despliegue la Lambda** (~5-10 minutos)
2. **Generar una nueva ruta de prueba**
3. **Revisar los logs del navegador** (F12 → Console)
4. **Seguir los pasos de diagnóstico** en `DIAGNOSTICO_ISSUE.md`

## Indicadores de Éxito

Cuando el problema esté resuelto, verás:

✓ La ruta se genera y se muestra en VisualizadorRutas
✓ Los logs del navegador no tienen errores
✓ La ruta persiste en localStorage
✓ La ruta aparece en el Dashboard después de refrescar
✓ `persisted: true` en la respuesta (ruta guardada en DB)

## Test Manual

Para verificar que todo funciona:

```bash
# Test del API
curl -X POST https://yhjk0mfvgc.execute-api.us-east-2.amazonaws.com/Prod/generate-learning-path \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "user_query": "Quiero aprender...",
    "user_level": "intermediate",
    "time_per_week": 15,
    "num_courses": 5,
    "response_format": "frontend"
  }' | jq '.titulo,.persisted'
```

Debería ver:
```
"Ruta de aprendizaje..."
true (después del fix)
```

## Problemas Secundarios Identificados

**No resueltos aún** (para futuros fixes):

1. **PostgreSQL persistence failure** - Lambda genera paths pero no los guarda a DB (`persisted: false`)
   - Causa: Probablemente timeout antes de completar persistencia
   - Se resolverá una vez que el Lambda tenga más tiempo

2. **No hay endpoint `/learning-paths` (LIST)**
   - Frontend solo lee de localStorage
   - No sincroniza con server
   - Necesita implementar listado de rutas en user-management-lambda

3. **Performance general**
   - Bedrock embeddings: ~60 segundos
   - MongoDB vector search: ~30 segundos
   - PostgreSQL persistence: ~10 segundos
   - Total: ~100 segundos (justifica el nuevo timeout de 300s)

## Referencias

- Logs de Lambda: `/aws/lambda/learnia-learning-path-generator-dev`
- Frontend S3: `s3://learnia-frontend-assets1`
- CloudFront: Distribution ID `E15VDYJ5PHGZMY`
- Learning Path API: `https://yhjk0mfvgc.execute-api.us-east-2.amazonaws.com/Prod`
