# Diagrama del Problema y Solución

## ¿QUÉ PASABA ANTES? (Problema)

```
Usuario genera ruta
    ↓
GeneradorRutas envía request al Lambda
    ↓
Lambda START REQUEST
    ├─ Genera embedding (Bedrock): ~40s
    ├─ Busca cursos (MongoDB): ~30s  
    ├─ Genera estructura (Nova): ~20s
    ├─ Persiste a DB (PostgreSQL): ~10s
    │  
    └─ TOTAL REQUERIDO: ~100 segundos
    
    PERO... Lambda timeout: 60 segundos
    
    ↓ (A los 60 segundos)
    TIMEOUT ❌
    
El Lambda se cancela antes de terminar:
- No persiste a PostgreSQL
- Devuelve error 504
- Frontend no sabe qué pasó
- Usuario ve pantalla en blanco
```

## ¿POR QUÉ NO SE MOSTRABA NADA?

```
Flujo esperado:
  GeneradorRutas → Lambda (éxito) → response con titulo ✓
    ↓
  navigate('/visualizador-rutas', { state: { nuevaRuta: response } })
    ↓
  VisualizadorRutas recibe nuevaRuta
    ↓
  agregarRuta(nuevaRuta) → localStorage
    ↓
  Mostrar ruta en pantalla ✓

Flujo REAL (con timeout):
  GeneradorRutas → Lambda ❌ TIMEOUT
    ↓
  No hay response con data
    ↓
  no navigate
    ↓
  Usuario ve pantalla de loading infinito
  O error silencioso en consola
```

## SOLUCIÓN APLICADA

### 1. Aumentar Timeout ✓
```diff
  FunctionName: learnia-learning-path-generator
  Runtime: python3.12
- Timeout: 60  ← ❌ Insuficiente
+ Timeout: 300 ← ✓ Suficiente (5 minutos)
  MemorySize: 1024 MB ← Limitaba CPU
+ MemorySize: 2048 MB ← Más CPU disponible
```

### 2. Añadir Logging ✓
Ahora el frontend loguea CADA PASO:

```
✓ Payload enviado al Lambda
✓ Respuesta recibida (titulo, cursos, path_id)
✓ Nueva ruta recibida en state
✓ agregarRuta llamado
✓ Ruta guardada en localStorage
```

Si algo falla, veremos exactamente en qué punto.

### 3. Completar Response del Lambda ✓
```diff
  Response del Lambda:
  {
+   "created_at": "2025-10-19T03:36:26.584049+00:00",
+   "fechaCreacion": "2025-10-19T03:36:26.584049+00:00",
    "path_id": "...",
    "titulo": "...",
    "cursos": [...],
    ...
  }
```

## NUEVO FLUJO (Con timeout aumentado)

```
Usuario genera ruta
    ↓
GeneradorRutas envía request al Lambda
  console.log('Generando ruta con payload:', payload) ← LOG 1
    ↓
Lambda START REQUEST
    ├─ Genera embedding (Bedrock): ~40s
    ├─ Busca cursos (MongoDB): ~30s  
    ├─ Genera estructura (Nova): ~20s
    └─ Persiste a DB (PostgreSQL): ~10s
    
    TOTAL: ~100 segundos
    TIMEOUT: 300 segundos ✓ SOBRADO
    
    ↓ (Antes de los 300 segundos)
    Lambda retorna response ✓
    
  console.log('Respuesta del Lambda recibida:', {...}) ← LOG 2
    ↓
  if (response && response.titulo) { ✓ PASS
    navigate('/visualizador-rutas', { state: { nuevaRuta: response } })
    
  console.log('VisualizadorRutas: Nueva ruta recibida') ← LOG 3
    ↓
  const rutaCreada = agregarRuta(nuevaRuta)
  console.log('agregarRuta: Guardando N rutas al cache') ← LOG 4
    ↓
  localStorage.setItem('misRutasAprendizaje', JSON.stringify([...]))
  console.log('Rutas guardadas en cache: N rutas') ← LOG 5
    ↓
  VisualizadorRutas muestra la ruta ✓
    ↓
Usuario ve la ruta generada ✓
```

## CÓMO VERIFICAR QUE FUNCIONA

### En el Navegador (F12 → Console):
```javascript
// Deberías ver esto cuando generas una ruta:

"Generando ruta con payload: {user_id: "...", user_query: "..."}"
"Respuesta del Lambda recibida: {tieneTitulo: true, titulo: "Ruta de...", cursosCount: 5}"
"VisualizadorRutas useEffect: Evaluando nuevaRuta"
"VisualizadorRutas: Nueva ruta recibida en state"
"VisualizadorRutas: Llamando agregarRuta"
"agregarRuta: Normalizando ruta nueva"
"agregarRuta: Ruta normalizada: {id: "...", titulo: "...", cursosCount: 5}"
"agregarRuta: Guardando 1 rutas al cache"
"Rutas guardadas en cache: 1 rutas, tamaño: 45234 bytes"

↓ Y luego verás tu ruta en la pantalla ✓
```

### En localStorage:
```javascript
// Abre console en navegador y ejecuta:
JSON.parse(localStorage.getItem('misRutasAprendizaje'))

// Deberías ver un array con tus rutas
[
  {
    id: "7e91632e-29a0-45e9-a256-03d162699f1e",
    pathId: "7e91632e-29a0-45e9-a256-03d162699f1e",
    titulo: "Ruta de aprendizaje para desarrollo web con React y Node.js",
    descripcion: "...",
    progreso: 0,
    cursos: [...],
    ...
  }
]
```

## CRONOGRAMA

```
October 18, 2025
  ├─ 03:22 UTC - Identifiqué problema con timeout (logs análisis)
  ├─ 03:35 UTC - Aumenté timeout de 60s → 300s
  ├─ 03:36 UTC - Desplegué frontend con logging
  └─ 03:40 UTC - Commit de cambios
  
October 19, 2025 (esperado)
  ├─ GitHub Actions despliegue Lambda (~5-10 min)
  ├─ Lambda actualizada con nuevo timeout
  └─ Siguiente generación de ruta debe funcionar ✓
```

## CHECKLIST FINAL

Cuando verifiques:

- [ ] GitHub Actions completó deployment de learning-path-generator
- [ ] Generé una nueva ruta
- [ ] Vi los logs en la consola (F12)
- [ ] Vi el log "Rutas guardadas en cache"
- [ ] La ruta se mostró en VisualizadorRutas
- [ ] La ruta permanece después de refrescar (F5)
- [ ] localStorage tiene la ruta

Si todo esto es SI ✓, el problema está resuelto.

Si alguno es NO ✗, comparte:
- El/los logs de la consola (F12 → Console → copia todo)
- Qué pasos seguiste
- Qué esperabas vs qué viste
