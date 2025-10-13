# 🔧 GUÍA: Crear Índice de Vector Search en MongoDB Atlas

## ⚠️ PROBLEMA IDENTIFICADO

Error en logs:
```
"embedding is not indexed as knnVector"
```

**Causa**: El índice creado NO es de tipo "Vector Search", es un índice normal o de tipo "Search".

## ✅ SOLUCIÓN: Crear Vector Search Index

### Paso 1: Ir a MongoDB Atlas Console
1. Ir a https://cloud.mongodb.com/
2. Seleccionar tu proyecto
3. Ir a tu cluster (donde está `learnia_db`)

### Paso 2: Crear Vector Search Index

**IMPORTANTE**: NO usar "Create Search Index" normal. Debes usar **"Atlas Vector Search"**.

#### Opción A: Desde la UI de Atlas
1. Click en tu cluster
2. Ir a la pestaña **"Search"**
3. Click en **"Create Search Index"**
4. Seleccionar **"Atlas Vector Search"** (NO "Atlas Search")
5. Seleccionar **"JSON Editor"**

#### Paso 3: Configuración del Índice

Usar esta configuración EXACTA:

```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 1024,
      "similarity": "cosine"
    }
  ]
}
```

**Detalles importantes:**
- **Database**: `learnia_db`
- **Collection**: `courses`
- **Index Name**: `default`

### Paso 4: Crear el Índice

1. Click en "Next"
2. Verificar que:
   - Index Name = `default`
   - Database = `learnia_db`
   - Collection = `courses`
3. Click en "Create Search Index"

### Paso 5: Esperar a que esté Activo

El índice debe construirse. Esto puede tomar 1-5 minutos.

**Estado**: Debe mostrar "Active" (no "Building" ni "Initial Sync")

## 🔍 VERIFICACIÓN

### Verificar el índice desde MongoDB Compass o Shell:

```javascript
// NO funcionará con getIndexes(), los índices vector search son separados
// Debes verificar en la UI de Atlas en la sección "Search"
```

### Verificar desde Atlas UI:
1. Ir a pestaña "Search"
2. Debes ver:
   - **Index Name**: default
   - **Type**: Vector Search ← IMPORTANTE
   - **Status**: Active
   - **Collection**: courses

## ⚠️ ERRORES COMUNES

### Error 1: Crear Atlas Search (normal) en lugar de Vector Search
**Síntoma**: Error "embedding is not indexed as knnVector"
**Solución**: Eliminar el índice y crear uno de tipo "Vector Search"

### Error 2: Dimensiones incorrectas
**Síntoma**: Error de dimensiones
**Solución**: Asegurarse que `numDimensions: 1024` (Titan Embeddings v2)

### Error 3: Índice en estado "Building"
**Síntoma**: Búsquedas no devuelven resultados
**Solución**: Esperar a que el estado sea "Active"

## 📝 DIFERENCIA ENTRE TIPOS DE ÍNDICES

| Característica | Atlas Search | Atlas Vector Search |
|----------------|--------------|---------------------|
| Tipo | Búsqueda de texto | Búsqueda semántica |
| Operador | `$search` | `$vectorSearch` |
| Para | Keywords, facets | Embeddings, similarity |
| Nuestro caso | ❌ NO usar | ✅ USAR ESTE |

## 🧪 DESPUÉS DE CREAR EL ÍNDICE

### Test rápido:

```bash
aws lambda invoke \
  --function-name learnia-learning-path-generator-dev \
  --region us-east-2 \
  --payload '{"body": "{\"user_id\": \"test\", \"user_query\": \"I want to learn JavaScript and TypeScript programming\", \"user_level\": \"intermediate\", \"estimated_weeks\": 10, \"time_per_week\": 10, \"num_courses\": 5}"}' \
  --cli-binary-format raw-in-base64-out \
  test_vector_search.json

# Ver resultado
cat test_vector_search.json | jq '.statusCode'
# Debe devolver: 200
```

## 📚 REFERENCIAS

- [MongoDB Atlas Vector Search Documentation](https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-overview/)
- [Create Vector Search Index](https://www.mongodb.com/docs/atlas/atlas-vector-search/create-index/)
- [Vector Search Operators](https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-stage/)

## 🎯 CHECKLIST

Antes de probar la Lambda, verificar:

- [ ] Índice es de tipo "Vector Search" (no "Search")
- [ ] Nombre del índice es exactamente: `default`
- [ ] Database: `learnia_db`
- [ ] Collection: `courses`  
- [ ] Campo: `embedding`
- [ ] Dimensiones: `1024`
- [ ] Similaridad: `cosine`
- [ ] Estado: **Active** (verde)

Una vez completado este checklist, la Lambda funcionará correctamente.
