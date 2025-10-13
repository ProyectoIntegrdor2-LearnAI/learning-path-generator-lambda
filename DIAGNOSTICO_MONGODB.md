# 📊 DIAGNÓSTICO COMPLETO - Learning Path Generator Lambda

## ✅ ESTADO DE LA INFRAESTRUCTURA

### Lambda Function
- **Nombre**: `learnia-learning-path-generator-dev`
- **Estado**: ✅ Funcionando correctamente
- **VPC**: ❌ Removida (acceso directo a internet)
- **Timeout**: 60 segundos
- **Conectividad**: ✅ MongoDB, Bedrock, PostgreSQL

### API Gateway
- **Endpoint**: `https://yhjk0mfvgc.execute-api.us-east-2.amazonaws.com/Prod/generate-learning-path`
- **Estado**: ✅ Funcionando

## 📚 ESTADO DE MONGODB

### Colección: `learnia_db.courses`
```
Total de cursos: 20
├─ Beginner: 2 cursos
├─ Intermediate: 17 cursos
└─ Advanced: 1 curso

Embeddings: 20/20 (100%)
```

### Cursos disponibles:
1. Curso de Fundamentos de Machine Learning (intermediate)
2. Audiocurso de Métricas in Product Design (intermediate)
3. Curso de Svelte (intermediate)
4. Curso de Creación de Contenido Viral para Marketing (intermediate)
5. Curso de Marketing Digital (intermediate)
6. Curso de Adobe Premiere Pro (beginner)
7. Curso de Clean Code y Buenas Prácticas con JavaScript (intermediate)
8. Curso de Single Page Application con JavaScript Vanilla (intermediate)
9. Curso de Creación de Pitch para Clientes (intermediate)
10. Curso para Entender Cómo Funcionan los Employee Stock Options (intermediate)
11. Curso de Indicadores Económicos (intermediate)
12. Curso de Introducción a Celo con Solidity (intermediate)
13. Curso Básico de Programación con C (beginner)
14. Curso de Apps No-code con Bubble: Interfaz y Funcionalidad (intermediate)
15. Curso Gratis de Marca Personal (intermediate)
16. Curso de Técnicas de Influencia y Persuasión (intermediate)
17. Curso de TypeScript: Programación Orientada a Objetos (advanced)
18. Audiocurso de Comunicación Efectiva (intermediate)
19. Curso de Herramientas No-Code para la Productividad (intermediate)
20. Curso de Optimización de Bases de Datos en SQL Server (intermediate)

## ⚠️ PROBLEMA IDENTIFICADO

### Error:
```json
{
  "error": "No se encontraron suficientes cursos relevantes para generar la ruta solicitada"
}
```

### Causa Raíz:
**EL ÍNDICE DE BÚSQUEDA VECTORIAL DE ATLAS SEARCH NO ESTÁ CONFIGURADO CORRECTAMENTE**

### Análisis:
1. ✅ **Hay cursos en la BD** (20 cursos)
2. ✅ **Todos tienen embeddings** (20/20)
3. ✅ **La Lambda se conecta a MongoDB**
4. ❌ **La búsqueda vectorial ($vectorSearch) no devuelve resultados**

### Configuración actual:
- **ATLAS_SEARCH_INDEX**: `default`
- **EMBEDDING_MODEL**: `amazon.titan-embed-text-v2:0`
- **EMBEDDING_DIM**: `1024`

### Problema técnico:
El código usa `$vectorSearch` de MongoDB Atlas que requiere:
1. Un índice de tipo **"vector search"** (no un índice normal)
2. El índice debe estar en la colección `courses`
3. El índice debe llamarse `default`
4. Debe estar configurado para el campo `embedding`
5. Dimensión del vector: 1024

## 🔧 SOLUCIÓN REQUERIDA

### Opción 1: Crear el índice de Atlas Search Vector (RECOMENDADO)

Ir a MongoDB Atlas Console y crear un índice de búsqueda vectorial:

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

**Nombre del índice**: `default`
**Colección**: `learnia_db.courses`

### Opción 2: Verificar si el índice ya existe

Ejecutar en la consola de MongoDB Atlas o con mongosh:

```javascript
db.courses.getIndexes()
```

Si el índice `default` no es de tipo vector search, eliminarlo y recrearlo.

## 🧪 PRUEBAS REALIZADAS

### Test 1: Python básico
```bash
curl -X POST https://yhjk0mfvgc.execute-api.us-east-2.amazonaws.com/Prod/generate-learning-path \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test",
    "user_query": "I want to learn Python programming",
    "user_level": "beginner",
    "estimated_weeks": 8,
    "time_per_week": 10,
    "num_courses": 5
  }'
```
**Resultado**: ❌ "No se encontraron suficientes cursos"

### Test 2: JavaScript (hay 3 cursos de JS/TS)
```bash
curl -X POST https://yhjk0mfvgc.execute-api.us-east-2.amazonaws.com/Prod/generate-learning-path \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test",
    "user_query": "I want to learn JavaScript and TypeScript",
    "user_level": "intermediate",
    "estimated_weeks": 10,
    "time_per_week": 12,
    "num_courses": 5
  }'
```
**Resultado**: ❌ "No se encontraron suficientes cursos"

## 📋 PRÓXIMOS PASOS

1. **[URGENTE] Crear/Verificar el índice de Atlas Search Vector**
   - Ir a MongoDB Atlas Console
   - Database → Search → Create Search Index
   - Tipo: Vector Search
   - Nombre: `default`
   - Campo: `embedding`
   - Dimensiones: 1024
   - Similaridad: cosine

2. **Verificar que el índice esté activo**
   - El estado debe ser "Active", no "Building"

3. **Probar nuevamente la Lambda**
   - Una vez creado el índice, los mismos tests deberían funcionar

## 📝 LOGS Y DEBUGGING

Para verificar qué está pasando en la búsqueda vectorial:

```bash
aws logs tail /aws/lambda/learnia-learning-path-generator-dev \
  --region us-east-2 \
  --since 5m \
  --follow
```

Buscar líneas que contengan:
- `vector_search_completed`
- `courses_found`
- `avg_similarity_score`

Si `courses_found: 0`, confirma que el índice no está funcionando.

## 💡 INFORMACIÓN ADICIONAL

### Configuración de MongoDB Client
El código en `src/utils/mongodb_client.py` usa:
- `$vectorSearch` aggregation pipeline
- Index: `"default"`
- Path: `"embedding"`
- Devuelve score de similitud con `$meta: "vectorSearchScore"`

### Requisitos del índice
MongoDB Atlas Search Vector index requiere:
- MongoDB Atlas (✅ tenemos)
- M10+ cluster o superior
- Atlas Search habilitado
- Índice de tipo "vector" (no "search" normal)
