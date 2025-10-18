## LearnIA — Learning Path Generator (AWS Lambda)

Función AWS Lambda que genera rutas de aprendizaje personalizadas a partir de una consulta del usuario. Combina búsqueda semántica en MongoDB Atlas, orquestación con AWS Bedrock (Titan Embeddings + Nova Lite) y persistencia en PostgreSQL (RDS). El proyecto sigue una separación por capas con clientes reutilizables de infraestructura y un handler de aplicación.


## Tabla de contenidos

- Descripción general
- Arquitectura y flujo
- Stack técnico
- Estructura del proyecto
- API: Endpoint, request y response
- Configuración y variables de entorno
- Desarrollo local
- Despliegue con AWS SAM
- Monitoreo y métricas
- Manejo de errores y validaciones
- Pruebas y utilidades
- Solución de problemas (FAQ)
- Seguridad
- Licencia


## Descripción general

Este servicio recibe una intención del usuario (por ejemplo: “Quiero ser desarrollador Full Stack con React y Node.js”), realiza embeddings con Bedrock Titan y ejecuta una búsqueda vectorial en MongoDB Atlas para localizar cursos relevantes. Luego, con Bedrock Nova Lite, orquesta una ruta de estudio coherente y estimaciones de tiempo. Finalmente, persiste la ruta en PostgreSQL para su seguimiento y visualización en la plataforma LearnIA.


## Arquitectura y flujo

1) Parseo y validación de la solicitud.
2) Generación de embeddings con Bedrock Titan: amazon.titan-embed-text-v2:0.
3) Búsqueda semántica en MongoDB Atlas (índice vectorial “default”).
4) Orquestación de la ruta con Bedrock Nova Lite: us.amazon.nova-lite-v1:0.
5) Persistencia de la ruta en PostgreSQL (tablas user_learning_paths y course_progress).
6) Respuesta JSON con cursos ordenados, roadmap y estimaciones.


## Stack técnico

- AWS Lambda (Python 3.12)
- AWS SAM para empaquetado y despliegue
- AWS Bedrock Runtime (Titan Embeddings + Nova Lite)
- MongoDB Atlas con búsqueda vectorial
- Amazon RDS for PostgreSQL (psycopg2-binary)
- CloudWatch Logs y métricas personalizadas


## Estructura del proyecto

```
.
├── README.md
├── template.yaml                  # Plantilla AWS SAM (API + Lambda + Layer)
├── layer-certs/
│   └── certs/
│       └── rds-us-east-2-bundle.pem   # CA bundle para SSL con RDS
└── src/
    ├── learning_path_generator.py # Lambda handler y lógica de aplicación
    ├── requirements.txt
    ├── test_connectivity.py       # Prueba simple de conectividad saliente
    └── utils/
        ├── __init__.py
        ├── bedrock_client.py      # Cliente Bedrock (embeddings y Nova + retry)
        ├── mongodb_client.py      # Búsqueda vectorial y filtros
        └── postgres_client.py     # Pool de conexiones y persistencia
```


## API

- Método: POST
- Ruta: /generate-learning-path
- CORS permitido: https://www.learn-ia.app
- Endpoint desplegado (ejemplo):
  https://{api_id}.execute-api.{region}.amazonaws.com/Prod/generate-learning-path

### Request (JSON)

```json
{
  "user_id": "uuid-opcional",
  "user_query": "Quiero convertirme en desarrollador Full Stack con React y Node.js",
  "user_level": "beginner|intermediate|advanced",
  "time_per_week": 10,
  "num_courses": 8,
  "preferences": {
    "max_price": 100,
    "preferred_platforms": ["Coursera", "Udemy"],
    "language": "es"
  }
}
``

Reglas de validación clave:

- user_query: 10–500 caracteres
- user_level: beginner | intermediate | advanced
- time_per_week: entero entre 1 y 40
- num_courses: entero entre 3 y 15
- preferences.language: es | en (opcional)

### Response (200)

```json
{
  "path_id": "uuid",
  "user_id": "uuid",
  "name": "Ruta de Aprendizaje Full Stack con React y Node.js",
  "description": "Resumen ejecutivo de la ruta...",
  "courses": [
    {
      "course_id": "656f...",
      "title": "Curso A",
      "platform": "Udemy",
      "url": "https://...",
      "rating": 4.8,
      "duration": "4 hours",
      "lane": 0,
      "order": 0,
      "reason": "Motivación y encaje con los objetivos..."
    }
  ],
  "roadmap_text": "Markdown con el plan de estudio...",
  "estimated_weeks": 12,
  "estimated_total_hours": 120,
  "difficulty_progression": "beginner -> intermediate -> advanced",
  "created_at": "2025-10-17T12:00:00Z",
  "status": "active"
}
```

Errores posibles: 400 (validación), 500 (error interno)


## Configuración y variables de entorno

Defina las siguientes variables (SAM las inyecta desde template.yaml). Para producción, use AWS Secrets Manager o SSM Parameter Store.

| Variable | Descripción | Default |
|---|---|---|
| ATLAS_URI | Cadena de conexión SRV a MongoDB Atlas | — |
| DATABASE_NAME | Base de datos de Atlas | learnia_db |
| COLLECTION_NAME | Colección con cursos | courses |
| ATLAS_SEARCH_INDEX | Índice de búsqueda vectorial | default |
| POSTGRES_HOST | Host de RDS PostgreSQL | — |
| POSTGRES_PORT | Puerto de PostgreSQL | 5432 |
| POSTGRES_DB | Base de datos | postgres |
| POSTGRES_USER | Usuario | postgres |
| POSTGRES_PASSWORD | Contraseña | — |
| DB_SSL | Habilitar SSL | true |
| DB_CA_PATH | Ruta al CA bundle (Layer) | /opt/certs/rds-us-east-2-bundle.pem |
| EMBEDDING_MODEL | Modelo de embeddings (Bedrock) | amazon.titan-embed-text-v2:0 |
| EMBEDDING_DIM | Dimensión esperada del embedding | 1024 |
| NOVA_MODEL | Perfil/ID de Nova Lite | us.amazon.nova-lite-v1:0 |
| NOVA_TEMPERATURE | Temperatura de inferencia | 0.7 |
| MAX_COURSES_IN_PATH | Límite superior de cursos | 10 |
| MIN_COURSES_IN_PATH | Mínimo de cursos necesarios | 3 |
| DEFAULT_WEEKS_ESTIMATE | Estimación por defecto de semanas | 12 |

Dependencias (src/requirements.txt): boto3, pymongo[srv], psycopg2-binary, numpy.


## Desarrollo local

1) Crear entorno y dependencias:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r src/requirements.txt
```

2) Crear archivo de evento local (ejemplo en events/generate-learning-path.json):

```json
{
  "requestContext": {"authorizer": {"claims": {"sub": "test-user-123"}}},
  "body": "{\n  \"user_query\": \"Desarrollador Full Stack con React y Node.js\",\n  \"user_level\": \"intermediate\",\n  \"time_per_week\": 15,\n  \"num_courses\": 8,\n  \"preferences\": {\n    \"max_price\": 100,\n    \"preferred_platforms\": [\"Coursera\", \"Udemy\"],\n    \"language\": \"es\"\n  }\n}"
}
```

3) Invocación local con SAM:

```bash
sam local invoke LearningPathGeneratorFunction \
  -e events/generate-learning-path.json \
  --parameter-overrides \
    Environment=local \
    AtlasUri="mongodb+srv://<user>:<pass>@<cluster>.mongodb.net" \
    PostgresHost="<rds-endpoint>" \
    PostgresPassword="<password>"
```

Requisitos: Docker en ejecución para `sam local invoke`.


## Despliegue con AWS SAM

Prerequisitos:

- AWS SAM CLI ≥ 1.115
- Docker (para build local)
- Credenciales AWS con permisos: Lambda, IAM, Bedrock InvokeModel, CloudWatch, S3, API Gateway
- Certificado CA en `layer-certs/certs/rds-us-east-2-bundle.pem`

Comandos:

```bash
sam build
sam deploy \
  --guided \
  --stack-name learnia-learning-path-generator \
  --parameter-overrides \
    Environment=dev \
    AtlasUri="mongodb+srv://<user>:<pass>@<cluster>.mongodb.net" \
    PostgresHost="<rds-endpoint>" \
    PostgresPassword="<password>"
```

La plantilla `template.yaml` crea:

- AWS::Serverless::Api con CORS restringido a https://www.learn-ia.app
- AWS::Serverless::Function (Python 3.12, 1024 MB, timeout 60s)
- Capa con el CA de RDS (ubicado en /opt/certs/ dentro del runtime)

Salida (Outputs): URL base del API y ARN de la función.


## Monitoreo y métricas

Se publican métricas personalizadas en CloudWatch (Namespace: LearnIA/Lambda/LearningPathGenerator):

- EmbeddingGenerationTimeMs
- VectorSearchTimeMs
- NovaOrchestrationTimeMs
- PostgresPersistenceTimeMs
- TotalGenerationTimeMs
- CoursesInPath
- PathsGeneratedCount

Revise además CloudWatch Logs para trazas detalladas (incluye logs de validación, tiempos y errores).


## Manejo de errores y validaciones

- Validaciones estrictas de entrada (400 para errores de usuario)
- Reintentos con backoff exponencial en llamadas a Bedrock
- Persistencia en PostgreSQL con transacción y upsert seguro de progreso
- Si la persistencia falla, se devuelve la ruta generada sin detener la respuesta


## Pruebas y utilidades

- `src/test_connectivity.py`: Lambda de diagnóstico para probar DNS/HTTP/HTTPS y resolución de endpoints críticos (Atlas y Bedrock). Útil para verificar problemas de red/VPC.


## Solución de problemas (FAQ)

PostgreSQL: timeouts o SSL
- Verifique que el security group permita 5432/TCP desde la Lambda
- Asegure que DB_SSL=true y DB_CA_PATH apunte al certificado en la capa
- Confirme host/usuario/contraseña en las variables de entorno

MongoDB Atlas: vector search
- Verifique que exista el índice `default` en el campo `embedding` y que la dimensión sea 1024
- Confirme credenciales en ATLAS_URI y acceso del clúster

Bedrock: límites/cuotas
- Verifique la región us-east-2 y permisos bedrock:InvokeModel
- Ajuste NOVA_TEMPERATURE y tokens si fuese necesario


## Seguridad

- SSL/TLS para conexiones a RDS (CA en Layer)
- Credenciales solo vía variables de entorno/Secrets Manager (nunca en código)
- IAM con privilegios mínimos (LambdaBasic + InvokeModel + PutMetricData)
- CORS restringido a https://www.learn-ia.app


## Esquema de base de datos (referencia rápida)

Ejemplo de DDL esperado por la función (adáptelo a su esquema):

```sql
CREATE TABLE IF NOT EXISTS user_learning_paths (
  path_id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  name TEXT,
  description TEXT,
  status TEXT DEFAULT 'active',
  target_hours_per_week INTEGER DEFAULT 5,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS course_progress (
  progress_id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  path_id UUID NOT NULL,
  mongodb_course_id TEXT NOT NULL,
  status TEXT DEFAULT 'not_started',
  progress_percentage FLOAT DEFAULT 0.0,
  sequence_order INTEGER,
  UNIQUE (path_id, mongodb_course_id)
);
```


## Licencia

Proprietary — LearnIA Project
