# Learning Path Generator Lambda

Lambda function for LearnIA that builds personalized learning paths using semantic search on MongoDB Atlas, orchestration with Bedrock Nova Lite, and persistence in PostgreSQL. The implementation follows a hexagonal-inspired layering with reusable infrastructure clients and an application-oriented handler.

## Project Structure

```
learning_path_generator/
├── src/
│   ├── learning_path_generator.py     # Lambda handler and application logic
│   ├── requirements.txt
│   └── utils/
│       ├── __init__.py
│       ├── bedrock_client.py          # Bedrock runtime wrapper with retry + embedding cache
│       ├── mongodb_client.py          # Atlas vector search helper
│       └── postgres_client.py         # Connection pool and persistence helpers
└── template.yaml                      # AWS SAM template
```

## Prerequisites

- Python 3.12
- AWS SAM CLI >= 1.115
- Docker (for `sam local invoke`)
- AWS credentials with permissions for Lambda, Bedrock `InvokeModel`, CloudWatch metrics, Amazon S3 (for SAM deploy), and the referenced VPC/security groups if required
- Existing MongoDB Atlas cluster with the `courses` collection and vector index `default`
- PostgreSQL database with the `user_learning_paths` and `course_progress` tables
- Bedrock access to `amazon.titan-embed-text-v2:0` and `amazon.nova-lite-v1:0`

## Configuration

Set the required environment variables before deploying or invoking locally. Sensitive values should be stored in AWS Secrets Manager or AWS SSM Parameter Store when running in production.

| Variable | Description |
| --- | --- |
| `ATLAS_URI` | MongoDB SRV connection string |
| `DATABASE_NAME` | Atlas database name (default `learnia_db`) |
| `COLLECTION_NAME` | Collection containing courses (default `courses`) |
| `ATLAS_SEARCH_INDEX` | Atlas vector search index (default `default`) |
| `POSTGRES_HOST` | PostgreSQL host |
| `POSTGRES_PORT` | PostgreSQL port (default `5432`) |
| `POSTGRES_DB` | PostgreSQL database (default `postgres`) |
| `POSTGRES_USER` | PostgreSQL user (default `postgres`) |
| `POSTGRES_PASSWORD` | PostgreSQL password |
| `DB_SSL` | Enable SSL when connecting to PostgreSQL (`true`/`false`) |
| `DB_CA_PATH` | Path to CA bundle (mounted via Lambda layer) |
| `AWS_REGION` | Region for Bedrock and CloudWatch (default `us-east-2`) |
| `EMBEDDING_MODEL` | Bedrock embedding model id |
| `NOVA_MODEL` | Bedrock orchestration model id |
| `NOVA_TEMPERATURE` | Nova temperature (float) |
| `MAX_COURSES_IN_PATH` | Hard cap for results returned to Nova |
| `MIN_COURSES_IN_PATH` | Minimum courses required to build a path |
| `DEFAULT_WEEKS_ESTIMATE` | Fallback number of weeks when Nova omits estimates |

## Install Dependencies

```bash
cd learning_path_generator
pip install -r src/requirements.txt
```

## SAM Build and Deploy

```bash
cd learning_path_generator
sam build
sam deploy \
  --stack-name learnia-learning-path-generator \
  --parameter-overrides \
      Environment=dev \
      AtlasUri="<mongodb+srv://...>" \
      PostgresHost="<postgres-endpoint>" \
      PostgresPassword="<password>" \
  --capabilities CAPABILITY_IAM
```

Ensure the `layer-certs/` directory contains the RDS CA bundle before running `sam build`.

## Local Invocation

```bash
sam local invoke LearningPathGeneratorFunction \
  -e events/generate-learning-path.json \
  --parameter-overrides Environment=local AtlasUri="mongodb+srv://..." PostgresHost="..." PostgresPassword="..."
```

Create `events/generate-learning-path.json` with a payload similar to:

```json
{
  "requestContext": {
    "authorizer": {
      "claims": {
        "sub": "c9b0e74d-5226-4656-8c02-f1307da91234"
      }
    }
  },
  "body": "{\n    \"user_query\": \"Desarrollador Full Stack con React y Node.js\",\n    \"user_level\": \"intermediate\",\n    \"time_per_week\": 15,\n    \"num_courses\": 8,\n    \"preferences\": {\n      \"max_price\": 100,\n      \"preferred_platforms\": [\"Coursera\", \"Udemy\"],\n      \"language\": \"es\"\n    }\n  }"
}
```

## Example HTTPS Invocation

```bash
curl -X POST "https://{api_id}.execute-api.us-east-2.amazonaws.com/prod/api/generate-learning-path" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <JWT>" \
  -d '{
        "user_query": "Quiero convertirme en desarrollador Full Stack con React y Node.js",
        "user_level": "beginner",
        "time_per_week": 10,
        "num_courses": 8,
        "preferences": {
          "max_price": 500,
          "preferred_platforms": ["Coursera", "Udemy"],
          "language": "es"
        }
      }'
```

## Manual Test Scenarios

1. **Básico:** `{"user_query": "Aprender Python desde cero", "user_level": "beginner", "time_per_week": 5, "num_courses": 5}`
2. **Con Filtros:** `{"user_query": "Desarrollador Full Stack con React y Node.js", "user_level": "intermediate", "time_per_week": 15, "num_courses": 8, "preferences": {"max_price": 100, "preferred_platforms": ["Coursera", "Udemy"], "language": "es"}}`
3. **Avanzado:** `{"user_query": "Machine Learning y Deep Learning para visión computacional", "user_level": "advanced", "time_per_week": 20, "num_courses": 10, "preferences": {"language": "en"}}`

Monitor CloudWatch Logs and the custom metrics `VectorSearchTimeMs`, `NovaOrchestrationTimeMs`, `PostgresPersistenceTimeMs`, `TotalGenerationTimeMs`, `CoursesInPath`, and `PathsGeneratedCount` to validate performance and throughput.
