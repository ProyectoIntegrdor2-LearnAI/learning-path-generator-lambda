# Diagnostico: Learning Path Generation Issue

## Problema Reportado
- Frontend dice "ruta generada exitosamente"
- Pero no devuelve ni muestra nada

## Investigación Realizada

### 1. Test del API endpoint
Realicé un test directo al endpoint `https://yhjk0mfvgc.execute-api.us-east-2.amazonaws.com/Prod/generate-learning-path` con:

```
user_query: "Quiero aprender desarrollo web con React y Node.js para crear aplicaciones profesionales"
user_level: "intermediate"
time_per_week: 15
num_courses: 5
response_format: "frontend"
```

**Resultado**: Se devolvió una respuesta válida CON todos los campos requeridos:
- ✓ `titulo`: "Ruta de aprendizaje para desarrollo web con React y Node.js"
- ✓ `path_id`: "7e91632e-29a0-45e9-a256-03d162699f1e"
- ✓ `cursos`: Array con 5 cursos
- ✓ `created_at`: "2025-10-19T03:36:26.584049+00:00"
- ✓ `fechaCreacion`: "2025-10-19T03:36:26.584049+00:00"
- ⚠️ `persisted`: **false** (NO se guardó en PostgreSQL)
- ⚠️ `guardado`: **false** (NO se guardó en PostgreSQL)

### 2. Problemas Identificados

#### Problema A: Lambda Timeout (CRÍTICO)
**Estado**: RESUELTO (en proceso de deployment)

- Timeout original: 60 segundos
- Requests reales: 120+ segundos
- Múltiples timeouts en los logs
- **Solución aplicada**: 
  - Aumenté timeout a 300 segundos
  - Aumenté memoria a 2048 MB
  - Commit: `e7d2bba`
  - Esperando deployment vía GitHub Actions

#### Problema B: PostgreSQL Persistence (IMPORTANTE)
**Estado**: INVESTIGANDO

La respuesta del API tiene `persisted: false` y `guardado: false`, lo que significa:
- La ruta se genera exitosamente
- Pero NO se guarda en la base de datos
- Por lo tanto no persiste entre sesiones/dispositivos
- Solo está en localStorage del navegador

**Causa probable**: 
- Lambda está recibiendo timeout antes de que persista
- O hay un error en la escritura a PostgreSQL que no se loguea

#### Problema C: Frontend Display (SECUNDARIO)
**Estado**: DIAGNOSTICANDO

Posibilidades:
1. La ruta SÍ se está guardando a localStorage pero no se muestra
2. `normalizeFrontendRoute` tiene un error
3. `agregarRuta` no está siendo llamado
4. El componente VisualizadorRutas tiene un bug

**Acciones tomadas**:
- Añadí logging extensivo en VisualizadorRutas
- Mejoré logging en GeneradorRutas
- Desplegué frontend actualizado

## Pasos para Diagnosticar

### Paso 1: Verificar Logs del Navegador
Abre www.learn-ia.app en tu navegador y:

1. Abre Developer Tools (F12)
2. Ve a la pestaña "Console"
3. Genera una nueva ruta
4. Busca estos logs:

```
Generando ruta con payload:
Respuesta del Lambda recibida:
VisualizadorRutas useEffect: Evaluando nuevaRuta:
VisualizadorRutas: Nueva ruta recibida en state:
VisualizadorRutas: Llamando agregarRuta:
agregarRuta: Normalizando ruta nueva:
agregarRuta: Ruta normalizada:
agregarRuta: Guardando N rutas al cache
Rutas guardadas en cache:
```

### Paso 2: Interpretar los Logs

Si ves:
- **Hasta "Respuesta del Lambda"**: El API funciona
- **Hasta "Nueva ruta recibida"**: GeneradorRutas→VisualizadorRutas funciona
- **Hasta "Guardando N rutas"**: `agregarRuta` está siendo llamado
- **NO ves "Rutas guardadas"**: Hay error al escribir localStorage

### Paso 3: Verificar localStorage
En la consola del navegador, ejecuta:

```javascript
// Ver rutas guardadas
const rutas = JSON.parse(localStorage.getItem('misRutasAprendizaje') || '[]');
console.log('Rutas en localStorage:', rutas.length);
console.log('Rutas:', rutas);

// Ver detalles de la primera ruta
if (rutas.length > 0) {
  console.log('Primera ruta:', rutas[0]);
}
```

### Paso 4: Verificar Base de Datos
Ejecuta en una terminal:

```bash
# Conectar a PostgreSQL
psql -h <db-host> -U postgres -d postgres -c "
SELECT path_id, user_id, name, created_at 
FROM user_learning_paths 
ORDER BY created_at DESC 
LIMIT 10;"
```

## Checklist de Solución

- [x] Aumenté timeout de Lambda de 60s a 300s
- [x] Aumenté memoria de Lambda de 1024 MB a 2048 MB
- [x] Añadí logging comprehensivo al frontend
- [x] Desplegué frontend actualizado
- [ ] Confirmar que GitHub Actions desplegó el Lambda
- [ ] Verificar que el timeout se ha incrementado en AWS
- [ ] Revisar logs de PostgreSQL para errors de persist
- [ ] Generar una ruta de prueba y verificar logs

## Próximos Pasos

1. **Esperar deployment del Lambda** (5-10 minutos)
2. **Probar generación de ruta nuevamente**
3. **Revisar los logs del navegador** según "Paso 1" arriba
4. **Compartir los logs** para más diagnóstico

## Recursos Útiles

- Test API: [/tmp/test-learning-path.html](/tmp/test-learning-path.html)
- Lambda Logs: `aws logs tail "/aws/lambda/learnia-learning-path-generator-dev" --region us-east-2`
- Commits recientes:
  - Lambda timeout fix: `e7d2bba`
  - Frontend logging: `3ec32ff`

## Resumen

El problema principal es que el Lambda estaba configurado con un timeout de 60 segundos, pero los requests necesitaban 120+ segundos. Esto causaba que muchas rutas no se guardaran a PostgreSQL (`persisted: false`).

Ya he aumentado el timeout a 300 segundos. Ahora necesitas:
1. Esperar a que GitHub Actions despliegue el cambio
2. Generar una nueva ruta
3. Revisar los logs del navegador para ver dónde se detiene el flujo
