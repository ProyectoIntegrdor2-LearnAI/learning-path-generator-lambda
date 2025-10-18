# 🧪 Guía de Pruebas de la Lambda

Esta guía explica cómo ejecutar las pruebas para verificar que la Lambda `learnia-learning-path-generator-dev` esté funcionando correctamente.

## 📋 Pre-requisitos

1. **AWS CLI configurado** con credenciales válidas
2. **Python 3.x** instalado
3. **Boto3** instalado: `pip install boto3`
4. Permisos para invocar la función Lambda en AWS

## 🚀 Scripts de Prueba Disponibles

### 1. `test_lambda_deployment.py` - Suite Completa de Pruebas

Este script ejecuta 4 pruebas predefinidas que cubren diferentes escenarios:

```bash
python3 test_lambda_deployment.py
```

**Casos de prueba incluidos:**
- ✅ Prueba Básica - Python para Análisis de Datos (beginner)
- ✅ Prueba Intermedia - Machine Learning (intermediate)
- ✅ Prueba Avanzada - Sistemas Distribuidos (advanced)
- ✅ Prueba - Desarrollo Web Full Stack (intermediate)

**Salida esperada:**
```
================================================================================
📊 RESUMEN DE PRUEBAS
================================================================================

✅ Pruebas Exitosas: 4/4
❌ Pruebas Fallidas: 0/4

⏱️  Tiempo Promedio de Respuesta: ~8 segundos
```

### 2. `test_lambda_single.py` - Prueba Individual Personalizada

Este script permite probar consultas personalizadas:

```bash
python3 test_lambda_single.py
```

**Personalizar la prueba:**

Edita el archivo y modifica los parámetros en la función `main()`:

```python
invoke_lambda_with_query(
    user_query="Tu consulta aquí",
    user_level="intermediate",  # beginner, intermediate, advanced
    num_courses=6,
    time_per_week=15,
    max_price=80,  # Opcional
    language="es",  # 'es' o 'en' - Opcional
    preferred_platforms=["Udemy", "Platzi"]  # Opcional
)
```

## 📊 Resultados de Pruebas

Ver el archivo `TEST_RESULTS.md` para un reporte detallado de las últimas pruebas ejecutadas.

## 🔧 Configuración

### Variables en los Scripts

```python
LAMBDA_FUNCTION_NAME = "learnia-learning-path-generator-dev"
USER_ID = "57eed54b-5749-47dc-9c15-c56d29ebbc6e"
AWS_REGION = "us-east-2"
```

### Formato de Request

```json
{
  "user_query": "Quiero aprender Python para análisis de datos",
  "user_level": "beginner",
  "num_courses": 5,
  "time_per_week": 10,
  "preferences": {
    "max_price": 100,
    "language": "es",
    "preferred_platforms": ["Coursera", "Udemy"]
  }
}
```

### Parámetros Válidos

#### `user_level` (requerido)
- `beginner` - Principiante
- `intermediate` - Intermedio
- `advanced` - Avanzado

#### `language` (opcional)
- `es` - Español
- `en` - Inglés

⚠️ **Nota:** Use `es` o `en`, NO use `Spanish` o `English`

#### `num_courses` (requerido)
- Mínimo: 3
- Máximo: 10

#### `time_per_week` (requerido)
- Horas disponibles por semana (entero positivo)

#### `preferences` (opcional)
```json
{
  "max_price": 100,
  "language": "es",
  "preferred_platforms": ["Coursera", "Udemy", "Platzi"]
}
```

## 📈 Interpretación de Resultados

### Respuesta Exitosa (200)

```json
{
  "path_id": "uuid",
  "user_id": "uuid",
  "name": "Nombre de la ruta",
  "description": "Descripción detallada",
  "estimated_weeks": 12,
  "estimated_total_hours": 120,
  "courses": [
    {
      "course_id": "id",
      "title": "Título del curso",
      "platform": "Plataforma",
      "url": "URL del curso",
      "rating": 4.5,
      "duration": 10,
      "lane": 0,
      "order": 0,
      "reason": "Razón de inclusión"
    }
  ],
  "created_at": "2025-10-17T..."
}
```

### Errores Comunes

#### 400 - Bad Request
```json
{
  "error": "preferences.language debe ser es o en"
}
```

**Solución:** Verificar que `language` sea `es` o `en`

#### 400 - Validation Error
```json
{
  "error": "user_level debe ser beginner, intermediate o advanced"
}
```

**Solución:** Usar uno de los valores válidos para `user_level`

#### 500 - Internal Server Error
```json
{
  "error": "Error interno del servidor",
  "details": "..."
}
```

**Solución:** Revisar los logs de CloudWatch de la Lambda

## 🔍 Verificación de Componentes

La Lambda integra múltiples servicios:

1. ✅ **Amazon Bedrock**
   - Titan Embeddings (generación de embeddings)
   - Amazon Nova (orquestación de rutas)

2. ✅ **MongoDB Atlas**
   - Búsqueda vectorial de cursos
   - Filtrado por preferencias

3. ✅ **PostgreSQL (RDS)**
   - Persistencia de rutas generadas
   - SSL habilitado

4. ✅ **CloudWatch**
   - Métricas de rendimiento
   - Logs de ejecución

## 📝 Logs y Debugging

### Ver logs en CloudWatch:

```bash
aws logs tail /aws/lambda/learnia-learning-path-generator-dev --follow
```

### Métricas disponibles:
- `EmbeddingGenerationTimeMs`
- `VectorSearchTimeMs`
- `NovaOrchestrationTimeMs`
- `PostgresPersistenceTimeMs`
- `TotalGenerationTimeMs`
- `CoursesInPath`
- `PathsGeneratedCount`

## 🎯 Ejemplos de Consultas

### Ejemplo 1: Principiante en Python
```python
invoke_lambda_with_query(
    user_query="Quiero aprender Python desde cero",
    user_level="beginner",
    num_courses=5,
    time_per_week=10,
    language="es"
)
```

### Ejemplo 2: Desarrollo Web Avanzado
```python
invoke_lambda_with_query(
    user_query="Arquitectura frontend moderna con React y TypeScript",
    user_level="advanced",
    num_courses=8,
    time_per_week=20,
    max_price=150,
    language="en",
    preferred_platforms=["Udemy", "Frontend Masters"]
)
```

### Ejemplo 3: Data Science
```python
invoke_lambda_with_query(
    user_query="Machine Learning y análisis de datos con Python",
    user_level="intermediate",
    num_courses=7,
    time_per_week=15,
    max_price=100,
    language="es",
    preferred_platforms=["Coursera", "Platzi"]
)
```

## ✅ Checklist de Verificación

- [ ] AWS CLI configurado correctamente
- [ ] Credenciales con permisos de Lambda
- [ ] Boto3 instalado
- [ ] Lambda desplegada en `us-east-2`
- [ ] User ID válido disponible
- [ ] Parámetros en formato correcto (`language`: `es`/`en`)

## 🆘 Soporte

Si encuentras problemas:

1. Verificar credenciales AWS
2. Revisar logs en CloudWatch
3. Verificar formato de parámetros
4. Revisar conectividad con MongoDB Atlas
5. Verificar conectividad con PostgreSQL RDS

## 📚 Recursos Adicionales

- [Documentación de AWS Lambda](https://docs.aws.amazon.com/lambda/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Amazon Bedrock](https://aws.amazon.com/bedrock/)

---

**Última actualización:** 17 de Octubre, 2025
