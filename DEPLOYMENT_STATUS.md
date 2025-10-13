# Learning Path Generator Lambda - Estado Actual

## ✅ DEPLOYMENT EXITOSO

### Infraestructura
- **Lambda Function**: `learnia-learning-path-generator-dev`
- **Region**: `us-east-2`
- **Runtime**: Python 3.12
- **Timeout**: 60 segundos
- **Memory**: 1024 MB
- **VPC**: ❌ REMOVIDO (acceso directo a internet)

### API Gateway
- **Endpoint**: `https://yhjk0mfvgc.execute-api.us-east-2.amazonaws.com/Prod/generate-learning-path`
- **Método**: POST
- **CORS**: Configurado para `https://www.learn-ia.app`

## ✅ CONECTIVIDAD VERIFICADA

Todos los servicios son accesibles:
- ✅ **MongoDB Atlas**: Conectado (público)
- ✅ **AWS Bedrock**: Conectado (público) 
- ✅ **PostgreSQL RDS**: Conectado (públicamente accesible)
- ✅ **Sin timeouts**: Respuestas en < 5 segundos

## ⚠️ ESTADO ACTUAL

### Problema Identificado
**Error**: `"No se encontraron suficientes cursos relevantes para generar la ruta solicitada"`

**Causa**: La base de datos MongoDB no tiene suficientes cursos (requiere mínimo 3).

### Verificación
La Lambda está funcionando correctamente:
- ✅ Validación de parámetros funciona
- ✅ Conexión a MongoDB funciona  
- ✅ Búsqueda vectorial funciona
- ✅ API Gateway responde correctamente
- ❌ No hay suficientes cursos en la colección `learnia_db.courses`

## 🧪 PRUEBAS

### Endpoint de Prueba
```bash
curl -X POST \
  https://yhjk0mfvgc.execute-api.us-east-2.amazonaws.com/Prod/generate-learning-path \
  -H "Content-Type: application/json" \
  -H "Origin: https://www.learn-ia.app" \
  -d '{
    "user_id": "test-user",
    "user_query": "I want to learn Python programming and data science",
    "user_level": "beginner",
    "estimated_weeks": 8,
    "time_per_week": 10,
    "num_courses": 5
  }'
```

### Respuesta Actual
```json
{
  "statusCode": 400,
  "error": "No se encontraron suficientes cursos relevantes para generar la ruta solicitada"
}
```

## 📋 PARÁMETROS REQUERIDOS

| Parámetro | Tipo | Validación | Descripción |
|-----------|------|-----------|-------------|
| `user_id` | string | Requerido | ID del usuario |
| `user_query` | string | 10-500 caracteres | Descripción de lo que quiere aprender |
| `user_level` | string | beginner/intermediate/advanced | Nivel del usuario |
| `estimated_weeks` | integer | 1-104 | Semanas estimadas para completar |
| `time_per_week` | integer | 1-40 | Horas por semana |
| `num_courses` | integer | 3-15 | Número de cursos deseados |

## 🎯 PRÓXIMOS PASOS

1. **Poblar MongoDB con cursos**:
   - La colección `learnia_db.courses` necesita datos
   - Mínimo 3 cursos para que la Lambda funcione
   - Los cursos deben tener embeddings para búsqueda vectorial

2. **Verificar índice de búsqueda vectorial**:
   - Índice: `default` 
   - Campo: `embedding`
   - Dimensión: 1024 (amazon.titan-embed-text-v2:0)

3. **Probar con datos reales**:
   - Una vez poblada la BD, la Lambda generará rutas de aprendizaje

## 💰 COSTOS OPTIMIZADOS

**Ahorro logrado**: ~$32/mes
- ❌ NAT Gateway: No necesario
- ✅ Lambda fuera de VPC: Cold starts más rápidos
- ✅ Acceso directo a internet: Sin costos adicionales

## 🔧 CAMBIOS REALIZADOS

### Archivos Modificados
1. `template.yaml`:
   - Removido `VpcConfig`
   - Removido parámetros `VpcSubnetIds` y `VpcSecurityGroupIds`
   - Removido `AWSLambdaVPCAccessExecutionRole`

2. `.github/workflows/deploy-learning-path-generator.yml`:
   - Removido parámetros de VPC del deploy

### Razón del Cambio
El RDS PostgreSQL tiene `PubliclyAccessible: true`, por lo que no se necesita VPC. MongoDB Atlas y Bedrock son servicios públicos de internet.
