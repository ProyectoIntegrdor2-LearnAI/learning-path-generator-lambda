import json
import logging
import os

# Configure logging IMMEDIATELY - BEFORE any other imports
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log IMMEDIATELY to prove Python is running
print("=" * 80, flush=True)
print("LAMBDA MODULE LOADING STARTED", flush=True)
print("=" * 80, flush=True)
logger.critical("========== CRITICAL: Module import starting ==========")

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger.critical("Basic imports complete")

import numpy as np
logger.critical("NumPy imported")

import boto3
from botocore.exceptions import BotoCoreError, ClientError
logger.critical("Boto3 imported")

logger.info("About to import utils modules...")
from utils.bedrock_client import get_bedrock_client
logger.critical("Bedrock client imported")

from utils.mongodb_client import get_mongo_client
logger.critical("MongoDB client imported")

from utils.postgres_client import get_postgres_client
logger.critical("PostgreSQL client imported")

logger.critical("========== ALL IMPORTS SUCCESSFUL ==========")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "https://www.learn-ia.app",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Content-Type": "application/json",
}

ALLOWED_LEVELS = {"beginner", "intermediate", "advanced"}
MIN_QUERY_LENGTH = 10
MAX_QUERY_LENGTH = 500


class ValidationError(Exception):
    pass


class LearningPathGenerator:
    def __init__(self) -> None:
        logger.info("Initializing LearningPathGenerator...")
        logger.info("Getting Bedrock client...")
        self.bedrock = get_bedrock_client()
        logger.info("Bedrock client initialized")
        
        logger.info("Getting MongoDB client...")
        self.mongo_client = get_mongo_client()
        logger.info("MongoDB client initialized")
        
        logger.info("Getting PostgreSQL client...")
        self.postgres_client = get_postgres_client()
        logger.info("PostgreSQL client initialized")
        
        logger.info("Creating CloudWatch client...")
        self.cloudwatch = boto3.client("cloudwatch", region_name="us-east-2")
        logger.info("CloudWatch client initialized")
        
        self.max_courses = int(os.getenv("MAX_COURSES_IN_PATH", "10"))
        self.min_courses = int(os.getenv("MIN_COURSES_IN_PATH", "3"))
        self.default_weeks = int(os.getenv("DEFAULT_WEEKS_ESTIMATE", "12"))
        logger.info("LearningPathGenerator initialization complete")

    def handle(self, event: Dict[str, Any]) -> Dict[str, Any]:
        logger.critical("========== HANDLE METHOD STARTED ==========")
        total_start = time.time()
        
        logger.critical("Step 1: Extracting user_id...")
        user_id = self._extract_user_id(event)
        logger.critical(f"User ID extracted: {user_id}")
        
        logger.critical("Step 2: Parsing body...")
        body = self._parse_body(event)
        logger.critical(f"Body parsed successfully")
        
        logger.critical("Step 3: Validating request...")
        self._validate_request(body)
        logger.critical("Request validated")
        
        logger.info(
            json.dumps(
                {
                    "event": "path_generation_started",
                    "user_id": user_id,
                    "user_query": body["user_query"],
                    "num_courses": body["num_courses"],
                }
            )
        )
        
        logger.critical("Step 4: Generating embedding...")
        embedding_start = time.time()
        embedding = self.generate_embedding(body["user_query"])
        embedding_time_ms = int((time.time() - embedding_start) * 1000)
        logger.critical(f"Embedding generated in {embedding_time_ms}ms")
        self._emit_metric("EmbeddingGenerationTimeMs", embedding_time_ms)
        
        logger.critical("Step 5: Searching relevant courses...")
        search_start = time.time()
        courses = self.search_relevant_courses(
            embedding,
            body["num_courses"],
            {
                "user_level": body["user_level"],
                "max_price": body.get("preferences", {}).get("max_price"),
                "language": body.get("preferences", {}).get("language"),
                "preferred_platforms": body.get("preferences", {}).get("preferred_platforms"),
            },
        )
        search_time_ms = int((time.time() - search_start) * 1000)
        logger.critical(f"Course search completed in {search_time_ms}ms. Found {len(courses)} courses")
        
        if len(courses) < self.min_courses:
            raise ValidationError("No se encontraron suficientes cursos relevantes para generar la ruta solicitada")
        nova_start = time.time()
        nova_response = self.orchestrate_with_nova(
            body["user_query"],
            body["user_level"],
            body["time_per_week"],
            courses,
        )
        nova_time_ms = int((time.time() - nova_start) * 1000)
        self._emit_metric("NovaOrchestrationTimeMs", nova_time_ms)
        logger.info(
            json.dumps(
                {
                    "event": "nova_orchestration_completed",
                    "nova_time_ms": nova_time_ms,
                    "nodes_generated": len(nova_response.get("nodes", [])),
                }
            )
        )
        enriched_nodes = self._build_nodes_with_metadata(nova_response["nodes"], courses)
        persist_start = time.time()
        path_id = self.persist_learning_path(
            user_id,
            {
                "name": nova_response["name"],
                "description": nova_response["description"],
                "target_hours_per_week": body["time_per_week"],
            },
            enriched_nodes,
        )
        persistence_ms = int((time.time() - persist_start) * 1000)
        self._emit_metric("PostgresPersistenceTimeMs", persistence_ms)
        response = self.build_response(
            path_id,
            user_id,
            body,
            nova_response,
            enriched_nodes,
        )
        total_time_ms = int((time.time() - total_start) * 1000)
        self._emit_metric("TotalGenerationTimeMs", total_time_ms)
        self._emit_metric("CoursesInPath", len(enriched_nodes))
        self._emit_metric("PathsGeneratedCount", 1)
        return response

    def generate_embedding(self, text: str) -> List[float]:
        embedding = self.bedrock.generate_embedding(text)
        vector = np.array(embedding, dtype=float)
        norm = np.linalg.norm(vector)
        if not norm:
            raise ValueError("Embedding norm is zero")
        normalized = (vector / norm).tolist()
        return normalized

    def search_relevant_courses(
        self,
        query_embedding: List[float],
        num_results: int,
        filters: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        start = time.time()
        num_candidates = min(self.max_courses * 10, max(num_results, self.min_courses) * 10)
        courses = self.mongo_client.vector_search(query_embedding, num_results, num_candidates, filters)
        duration_ms = int((time.time() - start) * 1000)
        self._emit_metric("VectorSearchTimeMs", duration_ms)
        return courses

    def orchestrate_with_nova(
        self,
        user_query: str,
        user_level: str,
        time_per_week: int,
        courses: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        courses_payload = [self._project_course_for_prompt(course) for course in courses]
        user_prompt = self._build_nova_prompt(user_query, user_level, time_per_week, courses_payload)
        system_prompt = (
            "Eres un arquitecto de rutas de aprendizaje personalizado."
            " Diseña recorridos pedagógicos eficientes y motivadores."
        )
        try:
            raw_response = self.bedrock.invoke_nova(system_prompt, user_prompt)
        except (ClientError, BotoCoreError, ValueError) as exc:
            logger.error(json.dumps({"event": "nova_invoke_failed", "error": str(exc)}))
            raise
        text_output = self._extract_text_from_nova(raw_response)
        cleaned = self._strip_code_fences(text_output)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.error(
                json.dumps(
                    {
                        "event": "nova_json_parse_failed",
                        "error": str(exc),
                        "raw_output": cleaned[:5000],
                    }
                )
            )
            raise ValueError("La respuesta del orquestador Nova no es JSON válido")
        self._validate_nova_response(parsed, {course["course_id"] for course in courses})
        return parsed

    def persist_learning_path(
        self,
        user_id: str,
        path_data: Dict[str, Any],
        courses_data: List[Dict[str, Any]],
    ) -> str:
        ordered_courses = sorted(
            courses_data,
            key=lambda item: (item.get("lane", 0), item.get("order", 0)),
        )
        safe_path_data = {**path_data}
        fallback_path_id = safe_path_data.get("path_id", str(uuid.uuid4()))
        try:
            persisted_path_id = self.postgres_client.persist_learning_path(user_id, safe_path_data, ordered_courses)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                json.dumps(
                    {
                        "event": "postgres_persist_skipped",
                        "error": str(exc),
                        "user_id": user_id,
                        "courses_count": len(ordered_courses),
                    }
                )
            )
            self._emit_metric("PostgresPersistenceFailedCount", 1)
            return fallback_path_id
        return persisted_path_id

    def build_response(
        self,
        path_id: str,
        user_id: str,
        request_payload: Dict[str, Any],
        nova_response: Dict[str, Any],
        courses: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        created_at = datetime.now(timezone.utc).isoformat()
        nodes = sorted(courses, key=lambda item: (item.get("lane", 0), item.get("order", 0)))
        response_courses = []
        for node in nodes:
            response_courses.append(
                {
                    "course_id": node.get("course_id"),
                    "title": node.get("title"),
                    "platform": node.get("platform"),
                    "url": node.get("url"),
                    "rating": node.get("rating"),
                    "duration": node.get("duration"),
                    "lane": node.get("lane", 0),
                    "order": node.get("order", 0),
                    "reason": node.get("reason"),
                }
            )
        estimated_weeks = self._safe_positive_int(nova_response.get("estimated_weeks"), self.default_weeks)
        estimated_total_hours = self._safe_positive_int(
            nova_response.get("estimated_total_hours"),
            estimated_weeks * request_payload["time_per_week"],
        )
        response = {
            "path_id": path_id,
            "user_id": user_id,
            "name": nova_response.get("name"),
            "description": nova_response.get("description"),
            "courses": response_courses,
            "roadmap_text": nova_response.get("roadmap_text"),
            "estimated_weeks": estimated_weeks,
            "estimated_total_hours": estimated_total_hours,
            "difficulty_progression": nova_response.get("difficulty_progression", ""),
            "created_at": created_at,
            "status": "active",
            "user_query": request_payload.get("user_query"),
        }
        return response
    
    def map_to_frontend_format(self, backend_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mapea la respuesta del backend al formato esperado por el frontend.
        
        Convierte:
        - path_id -> id
        - name -> titulo
        - description -> descripcion
        - courses con formato completo para el frontend
        - estimated_weeks -> estimacion (formateado)
        - user_query -> promptOriginal
        """
        cursos_frontend = []
        for idx, curso in enumerate(backend_response.get("courses", [])):
            cursos_frontend.append(
                {
                    "titulo": curso.get("title", "Curso sin título"),
                    "descripcion": curso.get("reason", ""),
                    "duracion": curso.get("duration", "Tiempo estimado"),
                    "plataforma": curso.get("platform", "Plataforma Online"),
                    "url": curso.get("url", ""),
                    "nivel": self._map_difficulty_to_frontend(
                        backend_response.get("difficulty_progression", "Intermedio")
                    ),
                    "lane": curso.get("lane", 0),
                    "order": curso.get("order", idx),
                    "course_id": curso.get("course_id"),
                }
            )
        
        estimated_weeks = backend_response.get("estimated_weeks", 12)
        estimacion = f"{estimated_weeks} semanas"
        
        return {
            "id": backend_response.get("path_id"),
            "path_id": backend_response.get("path_id"),
            "titulo": backend_response.get("name", "Ruta de Aprendizaje"),
            "descripcion": backend_response.get("description", ""),
            "estimacion": estimacion,
            "nivel": self._map_difficulty_to_frontend(
                backend_response.get("difficulty_progression", "Intermedio")
            ),
            "cursos": cursos_frontend,
            "promptOriginal": backend_response.get("user_query", ""),
        }
    
    def _map_difficulty_to_frontend(self, difficulty: str) -> str:
        """Mapea la dificultad a un formato legible para el frontend."""
        difficulty_lower = difficulty.lower()
        if "beginner" in difficulty_lower or "básico" in difficulty_lower:
            return "Básico"
        elif "advanced" in difficulty_lower or "avanzado" in difficulty_lower:
            return "Avanzado"
        else:
            return "Intermedio"

    def _build_nodes_with_metadata(
        self,
        nodes: List[Dict[str, Any]],
        courses: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        courses_by_id = {course["course_id"]: course for course in courses}
        enriched = []
        for node in nodes:
            course_id = node.get("course_id")
            course_ref = courses_by_id.get(course_id)
            if not course_ref:
                raise ValidationError(f"Curso {course_id} no encontrado en la búsqueda semántica")
            merged = {**course_ref, **node}
            enriched.append(merged)
        return enriched

    def _emit_metric(self, name: str, value: float) -> None:
        try:
            self.cloudwatch.put_metric_data(
                Namespace="LearnIA/Lambda/LearningPathGenerator",
                MetricData=[
                    {
                        "MetricName": name,
                        "Timestamp": datetime.now(timezone.utc),
                        "Value": float(value),
                        "Unit": "Milliseconds" if name.endswith("Ms") else "Count",
                    }
                ],
            )
        except (ClientError, BotoCoreError) as exc:
            logger.warning(json.dumps({"event": "cloudwatch_metric_failed", "metric": name, "error": str(exc)}))

    def _extract_user_id(self, event: Dict[str, Any]) -> str:
        try:
            return event["requestContext"]["authorizer"]["claims"]["sub"]
        except KeyError:
            pass
        body = self._parse_body(event)
        user_id = body.get("user_id")
        
        if not user_id:
            logger.warning("No user_id found, using test user")
            return "test-user-123"
        
        return user_id

    def _parse_body(self, event: Dict[str, Any]) -> Dict[str, Any]:
        body = event.get("body")
        if body is None:
            raise ValidationError("El cuerpo de la solicitud es requerido")
        if isinstance(body, str):
            try:
                return json.loads(body)
            except json.JSONDecodeError as exc:
                raise ValidationError("El cuerpo de la solicitud debe ser JSON válido") from exc
        if isinstance(body, dict):
            return body
        raise ValidationError("Formato de cuerpo no soportado")

    def _validate_request(self, payload: Dict[str, Any]) -> None:
        query = payload.get("user_query", "")
        if not isinstance(query, str) or len(query) < MIN_QUERY_LENGTH or len(query) > MAX_QUERY_LENGTH:
            raise ValidationError("user_query debe tener entre 10 y 500 caracteres")
        level = payload.get("user_level")
        if level not in ALLOWED_LEVELS:
            raise ValidationError("user_level debe ser beginner, intermediate o advanced")
        time_per_week = payload.get("time_per_week")
        if not isinstance(time_per_week, int) or not 1 <= time_per_week <= 40:
            raise ValidationError("time_per_week debe ser un entero entre 1 y 40")
        num_courses = payload.get("num_courses")
        if not isinstance(num_courses, int) or not 3 <= num_courses <= 15:
            raise ValidationError("num_courses debe ser un entero entre 3 y 15")
        preferences = payload.get("preferences", {})
        if preferences:
            if not isinstance(preferences, dict):
                raise ValidationError("preferences debe ser un objeto JSON")
            max_price = preferences.get("max_price")
            if max_price is not None and (not isinstance(max_price, (int, float)) or max_price < 0):
                raise ValidationError("preferences.max_price debe ser un número mayor o igual a 0")
            language = preferences.get("language")
            if language and language not in {"es", "en"}:
                raise ValidationError("preferences.language debe ser es o en")
            platforms = preferences.get("preferred_platforms")
            if platforms and (not isinstance(platforms, list) or not all(isinstance(p, str) for p in platforms)):
                raise ValidationError("preferences.preferred_platforms debe ser una lista de strings")

    def _build_nova_prompt(
        self,
        user_query: str,
        user_level: str,
        time_per_week: int,
        courses: List[Dict[str, Any]],
    ) -> str:
        courses_json = json.dumps(courses, ensure_ascii=False, indent=2)
        prompt = f"""
Eres un experto diseñador de rutas de aprendizaje educativas.

OBJETIVO DEL ESTUDIANTE: {user_query}
NIVEL ACTUAL: {user_level}
TIEMPO DISPONIBLE: {time_per_week} horas/semana

CURSOS DISPONIBLES (ordenados por relevancia semántica):
{courses_json}

TAREA:
1. Analiza cada curso y determina su rol en la ruta de aprendizaje
2. Organízalos en 4 lanes de progresión:
   - Lane 0 (Fundamentos): Conceptos básicos necesarios
   - Lane 1 (Core): Conocimientos principales del objetivo
   - Lane 2 (Avanzado): Especialización y profundización
   - Lane 3 (Capstone): Proyecto integrador final

3. Para cada curso genera:
   - reason: Explicación detallada de por qué es relevante (100-150 palabras en español)
   - lane: Número de 0-3 según su posición en la progresión
   - order: Orden dentro del lane

4. Genera un roadmap_text completo explicando:
   - La progresión lógica entre las 4 etapas
   - Estimaciones de tiempo realistas
   - Consejos prácticos de estudio
   - Proyectos intermedios sugeridos

5. Calcula:
   - estimated_weeks: Estimación total en semanas
   - estimated_total_hours: Horas totales aproximadas

FORMATO DE RESPUESTA (JSON estricto, sin markdown):
{{
  "name": "Título descriptivo de la ruta",
  "description": "Resumen ejecutivo de la ruta (50-100 palabras)",
  "nodes": [
    {{
      "course_id": "id_del_curso_en_mongodb",
      "title": "título del curso",
      "reason": "explicación detallada de relevancia",
      "lane": 0,
      "order": 0
    }}
  ],
  "roadmap_text": "descripción completa del roadmap en markdown...",
  "estimated_weeks": 12,
  "estimated_total_hours": 240,
  "difficulty_progression": "beginner -> intermediate -> advanced"
}}

IMPORTANTE:
- Devuelve SOLO el JSON, sin texto adicional ni markdown
- Asegúrate de incluir TODOS los cursos proporcionados
- Los course_id deben coincidir exactamente con los IDs de MongoDB
- El roadmap_text debe estar en español y usar formato markdown
- Las explicaciones (reason) deben ser motivadoras y específicas
"""
        return prompt.strip()

    def _project_course_for_prompt(self, course: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "course_id": course.get("course_id"),
            "title": course.get("title"),
            "description": course.get("description"),
            "platform": course.get("platform"),
            "url": course.get("url"),
            "rating": course.get("rating"),
            "duration": course.get("duration"),
            "price": course.get("price"),
            "students_count": course.get("students_count"),
            "language": course.get("language"),
            "category": course.get("category"),
            "level": course.get("level"),
            "score": course.get("score"),
        }

    def _extract_text_from_nova(self, raw_response: Dict[str, Any]) -> str:
        if not raw_response:
            raise ValueError("Respuesta vacía de Nova")

        if "output" in raw_response:
            output = raw_response["output"]
            if isinstance(output, dict) and "message" in output:
                content = output["message"].get("content", [])
                if isinstance(content, list) and content:
                    text = content[0].get("text")
                    if text:
                        return text

        if "outputText" in raw_response:
            return raw_response["outputText"]

        if "message" in raw_response:
            content = raw_response["message"].get("content", [])
            if isinstance(content, list) and content:
                text = content[0].get("text")
                if text:
                    return text

        raise ValueError(f"Formato de respuesta de Nova no reconocido: {list(raw_response.keys())}")

    def _strip_code_fences(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            text = text[3:]
            if text.startswith("json"):
                text = text[4:]
            if text.endswith("```"):
                text = text[:-3]
        return text.strip()

    def _validate_nova_response(self, payload: Dict[str, Any], valid_ids: set[str]) -> None:
        required_fields = {"name", "description", "nodes", "roadmap_text"}
        missing = required_fields - payload.keys()
        if missing:
            raise ValidationError(f"La respuesta de Nova falta campos requeridos: {', '.join(missing)}")
        nodes = payload.get("nodes", [])
        if not isinstance(nodes, list) or not nodes:
            raise ValidationError("La respuesta de Nova debe incluir una lista de nodos")
        for node in nodes:
            if node.get("course_id") not in valid_ids:
                raise ValidationError(f"Nova retornó un course_id inválido: {node.get('course_id')}")
            if not isinstance(node.get("lane"), int) or node["lane"] not in {0, 1, 2, 3}:
                raise ValidationError("Cada nodo debe incluir lane entre 0 y 3")
            if not isinstance(node.get("order"), int) or node["order"] < 0:
                raise ValidationError("Cada nodo debe incluir order como entero >= 0")
            reason = node.get("reason")
            if not reason or len(reason.split()) < 10:
                raise ValidationError("Cada nodo debe incluir una razón detallada")

    def _safe_positive_int(self, value: Any, fallback: int) -> int:
        try:
            numeric = int(float(value))
        except (TypeError, ValueError):
            return fallback
        return numeric if numeric > 0 else fallback


generator_instance: Optional[LearningPathGenerator] = None


def get_generator() -> LearningPathGenerator:
    global generator_instance
    if generator_instance is None:
        generator_instance = LearningPathGenerator()
    return generator_instance


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    # Handle preflight OPTIONS request
    if event.get("httpMethod") == "OPTIONS" or event.get("requestContext", {}).get("http", {}).get("method") == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": "",
        }
    
    generator = get_generator()
    start = time.time()
    try:
        result = generator.handle(event)
        elapsed_ms = int((time.time() - start) * 1000)
        logger.info(json.dumps({"event": "path_generation_completed", "total_time_ms": elapsed_ms}))
        
        # Verificar si se solicita el formato del frontend
        body = {}
        try:
            body = json.loads(event.get("body", "{}")) if isinstance(event.get("body"), str) else event.get("body", {})
        except json.JSONDecodeError:
            pass
        
        format_type = body.get("response_format", "backend")
        
        if format_type == "frontend":
            # Devolver solo el formato del frontend
            frontend_data = generator.map_to_frontend_format(result)
            response_body = frontend_data
        elif format_type == "both":
            # Devolver ambos formatos
            response_body = {
                "backend": result,
                "frontend": generator.map_to_frontend_format(result)
            }
        else:
            # Por defecto, devolver formato backend original
            response_body = result
        
        return {
            "statusCode": 200,
            "headers": CORS_HEADERS,
            "body": json.dumps(response_body),
        }
    except ValidationError as exc:
        logger.warning(json.dumps({"event": "validation_error", "error": str(exc)}))
        return {
            "statusCode": 400,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": str(exc)}),
        }
    except Exception as exc:  # noqa: BLE001
        logger.error(json.dumps({"event": "unhandled_error", "error": str(exc)}))
        return {
            "statusCode": 500,
            "headers": CORS_HEADERS,
            "body": json.dumps({"error": "Error interno del servidor"}),
        }
