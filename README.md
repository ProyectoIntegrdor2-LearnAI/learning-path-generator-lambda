# Learning Path Generator Lambda# Learning Path Generator Lambda



AWS Lambda function that generates personalized learning paths using AI-powered course recommendations.Lambda function for LearnIA that builds personalized learning paths using semantic search on MongoDB Atlas, orchestration with Bedrock Nova Lite, and persistence in PostgreSQL. The implementation follows a hexagonal-inspired layering with reusable infrastructure clients and an application-oriented handler.



## Overview## Project Structure



This service leverages:```

- **AWS Bedrock** (Titan embeddings + Nova Lite model) for AI-powered content generationlearning_path_generator/

- **MongoDB Atlas** with vector search for semantic course discovery├── src/

- **PostgreSQL RDS** for persistent storage of learning paths│   ├── learning_path_generator.py     # Lambda handler and application logic

- **AWS Lambda** for serverless execution│   ├── requirements.txt

│   └── utils/

## Architecture│       ├── __init__.py

│       ├── bedrock_client.py          # Bedrock runtime wrapper with retry + embedding cache

```│       ├── mongodb_client.py          # Atlas vector search helper

User Request│       └── postgres_client.py         # Connection pool and persistence helpers

    ↓└── template.yaml                      # AWS SAM template

[Parse & Validate]```

    ↓

[Generate Embedding] → AWS Bedrock Titan## Prerequisites

    ↓

[Vector Search] → MongoDB Atlas- Python 3.12

    ↓- AWS SAM CLI >= 1.115

[Orchestrate Roadmap] → AWS Bedrock Nova Lite- Docker (for `sam local invoke`)

    ↓- AWS credentials with permissions for Lambda, Bedrock `InvokeModel`, CloudWatch metrics, Amazon S3 (for SAM deploy), and the referenced VPC/security groups if required

[Persist Path] → PostgreSQL RDS- Existing MongoDB Atlas cluster with the `courses` collection and vector index `default`

    ↓- PostgreSQL database with the `user_learning_paths` and `course_progress` tables

Response (200 OK with learning path)- Bedrock access to `amazon.titan-embed-text-v2:0` and `amazon.nova-lite-v1:0`

```

## Configuration

## Deployment

Set the required environment variables before deploying or invoking locally. Sensitive values should be stored in AWS Secrets Manager or AWS SSM Parameter Store when running in production.

### Prerequisites

- AWS SAM CLI| Variable | Description |

- Python 3.12+| --- | --- |

- Environment variables configured for:| `ATLAS_URI` | MongoDB SRV connection string |

  - `ATLAS_URI` - MongoDB Atlas connection| `DATABASE_NAME` | Atlas database name (default `learnia_db`) |

  - `POSTGRES_HOST`, `POSTGRES_PASSWORD` - PostgreSQL credentials| `COLLECTION_NAME` | Collection containing courses (default `courses`) |

  - AWS credentials with Bedrock, Lambda, and RDS permissions| `ATLAS_SEARCH_INDEX` | Atlas vector search index (default `default`) |

| `POSTGRES_HOST` | PostgreSQL host |

### Deploy| `POSTGRES_PORT` | PostgreSQL port (default `5432`) |

```bash| `POSTGRES_DB` | PostgreSQL database (default `postgres`) |

sam build| `POSTGRES_USER` | PostgreSQL user (default `postgres`) |

sam deploy --guided| `POSTGRES_PASSWORD` | PostgreSQL password |

```| `DB_SSL` | Enable SSL when connecting to PostgreSQL (`true`/`false`) |

| `DB_CA_PATH` | Path to CA bundle (mounted via Lambda layer) |

## API Endpoint| `EMBEDDING_MODEL` | Bedrock embedding model id |

| `NOVA_MODEL` | Bedrock orchestration model id |

**POST** `/generate-learning-path`| `NOVA_TEMPERATURE` | Nova temperature (float) |

| `MAX_COURSES_IN_PATH` | Hard cap for results returned to Nova |

### Request Body| `MIN_COURSES_IN_PATH` | Minimum courses required to build a path |

```json| `DEFAULT_WEEKS_ESTIMATE` | Fallback number of weeks when Nova omits estimates |

{

  "user_id": "uuid-string",## Install Dependencies

  "user_query": "I want to learn...",

  "user_level": "beginner|intermediate|advanced",```bash

  "estimated_weeks": 10,cd learning_path_generator

  "time_per_week": 10,pip install -r src/requirements.txt

  "num_courses": 5,```

  "preferences": {

    "max_price": 100,## SAM Build and Deploy

    "language": "en",

    "preferred_platforms": ["Coursera", "Udemy"]```bash

  }cd learning_path_generator

}sam build

```sam deploy \

  --stack-name learnia-learning-path-generator \

### Response  --parameter-overrides \

```json      Environment=dev \

{      AtlasUri="<mongodb+srv://...>" \

  "path_id": "uuid",      PostgresHost="<postgres-endpoint>" \

  "user_id": "uuid",      PostgresPassword="<password>" \

  "name": "Learning Path Name",  --capabilities CAPABILITY_IAM

  "description": "...",```

  "courses": [

    {Ensure the `layer-certs/` directory contains the RDS CA bundle before running `sam build`.

      "course_id": "id",

      "title": "Course Title",## Local Invocation

      "url": "https://...",

      "rating": 4.8,```bash

      "duration": "4 hours",sam local invoke LearningPathGeneratorFunction \

      "reason": "Why this course matches your goals"  -e events/generate-learning-path.json \

    }  --parameter-overrides Environment=local AtlasUri="mongodb+srv://..." PostgresHost="..." PostgresPassword="..."

  ],```

  "roadmap_text": "Detailed learning roadmap",

  "estimated_weeks": 10,Create `events/generate-learning-path.json` with a payload similar to:

  "estimated_total_hours": 80,

  "difficulty_progression": "beginner -> intermediate -> advanced",```json

  "status": "active"{

}  "requestContext": {

```    "authorizer": {

      "claims": {

## Development        "sub": "c9b0e74d-5226-4656-8c02-f1307da91234"

      }

### Project Structure    }

```  },

src/  "body": "{\n    \"user_query\": \"Desarrollador Full Stack con React y Node.js\",\n    \"user_level\": \"intermediate\",\n    \"time_per_week\": 15,\n    \"num_courses\": 8,\n    \"preferences\": {\n      \"max_price\": 100,\n      \"preferred_platforms\": [\"Coursera\", \"Udemy\"],\n      \"language\": \"es\"\n    }\n  }"

├── learning_path_generator.py    # Main Lambda handler}

└── utils/```

    ├── bedrock_client.py          # Bedrock API client

    ├── mongodb_client.py           # MongoDB vector search## Example HTTPS Invocation

    └── postgres_client.py          # PostgreSQL persistence

layer-certs/                        # RDS CA certificate for SSL```bash

template.yaml                       # SAM templatecurl -X POST "https://{api_id}.execute-api.us-east-2.amazonaws.com/prod/api/generate-learning-path" \

```  -H "Content-Type: application/json" \

  -H "Authorization: Bearer <JWT>" \

### Local Testing  -d '{

```bash        "user_query": "Quiero convertirme en desarrollador Full Stack con React y Node.js",

python src/learning_path_generator.py  # Requires AWS credentials        "user_level": "beginner",

```        "time_per_week": 10,

        "num_courses": 8,

## Monitoring        "preferences": {

          "max_price": 500,

CloudWatch metrics are emitted for:          "preferred_platforms": ["Coursera", "Udemy"],

- `EmbeddingGenerationTimeMs` - Time to generate embeddings          "language": "es"

- `VectorSearchTimeMs` - MongoDB search latency        }

- `NovaOrchestrationTimeMs` - Nova model response time      }'

- `PostgresPersistenceTimeMs` - Database write latency```

- `TotalGenerationTimeMs` - End-to-end request time

- `CoursesInPath` - Number of courses in generated path## Manual Test Scenarios

- `PathsGeneratedCount` - Cumulative paths generated

1. **Básico:** `{"user_query": "Aprender Python desde cero", "user_level": "beginner", "time_per_week": 5, "num_courses": 5}`

## Error Handling2. **Con Filtros:** `{"user_query": "Desarrollador Full Stack con React y Node.js", "user_level": "intermediate", "time_per_week": 15, "num_courses": 8, "preferences": {"max_price": 100, "preferred_platforms": ["Coursera", "Udemy"], "language": "es"}}`

3. **Avanzado:** `{"user_query": "Machine Learning y Deep Learning para visión computacional", "user_level": "advanced", "time_per_week": 20, "num_courses": 10, "preferences": {"language": "en"}}`

The Lambda gracefully handles:

- MongoDB connectivity issues - falls back to top-N courses by ratingMonitor CloudWatch Logs and the custom metrics `VectorSearchTimeMs`, `NovaOrchestrationTimeMs`, `PostgresPersistenceTimeMs`, `TotalGenerationTimeMs`, `CoursesInPath`, and `PathsGeneratedCount` to validate performance and throughput.

- PostgreSQL timeouts - returns generated path without persistence
- Bedrock model failures - retries with exponential backoff
- Invalid user input - returns 400 with validation error

## Production Checklist

- [x] VPC/Network isolation removed (public endpoint access)
- [x] RDS security group accepts public traffic (port 5432)
- [x] Bedrock permissions granted across regions
- [x] Error handling and graceful degradation implemented
- [x] CloudWatch monitoring and metrics in place
- [x] SSL enabled for RDS connections
- [x] Lambda timeout set to 60 seconds
- [x] Memory allocation: 1024 MB

## Security

- SSL/TLS for all database connections
- Environment variables for sensitive credentials (never hardcoded)
- IAM policies follow least-privilege principle
- Request validation on all inputs
- CORS restricted to `https://www.learn-ia.app`

## Troubleshooting

### Postgres Connection Timeout
- Verify RDS security group allows inbound traffic on port 5432
- Check RDS is publicly accessible
- Confirm credentials and endpoint are correct

### MongoDB Vector Search Not Working
- Verify Atlas search index "default" exists with 1024 dimensions
- Check ATLAS_URI includes authentication credentials
- Ensure vector search is enabled on the cluster

### Bedrock Rate Limiting
- Check AWS Bedrock quota for us-east-2 region
- Implement request throttling if needed
- Monitor `NovaOrchestrationTimeMs` metrics

## License

Proprietary - LearnIA Project
