import json
import logging
import os
import time
from typing import Any, Dict, Iterable, List, Optional

from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


class MongoDBClient:
    def __init__(self) -> None:
        self._uri = os.getenv("ATLAS_URI")
        if not self._uri:
            raise ValueError("ATLAS_URI environment variable is required")
        self._database_name = os.getenv("DATABASE_NAME", "learnia_db")
        self._collection_name = os.getenv("COLLECTION_NAME", "courses")
        self._search_index = os.getenv("ATLAS_SEARCH_INDEX", "default")
        self._client = None
        self._collection = None
        logger.info("MongoDBClient initialized (connection will be created on first use)")

    def _get_client(self) -> MongoClient:
        """Lazy initialization of MongoDB client"""
        if self._client is None:
            logger.info(f"Connecting to MongoDB Atlas database: {self._database_name}")
            self._client = MongoClient(
                self._uri,
                connectTimeoutMS=10000,
                socketTimeoutMS=20000,
                serverSelectionTimeoutMS=10000,
                appname="learning-path-generator",
                retryWrites=True,
            )
            logger.info("MongoDB client created successfully")
        return self._client

    def _get_collection(self) -> Collection:
        """Get the MongoDB collection (lazy initialization)"""
        if self._collection is None:
            client = self._get_client()
            self._collection = client[self._database_name][self._collection_name]
            logger.info(f"MongoDB collection '{self._collection_name}' ready")
        return self._collection

    def vector_search(
        self,
        query_embedding: List[float],
        limit: int,
        num_candidates: int,
        filters: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        pipeline = [
            {
                "$vectorSearch": {
                    "index": self._search_index,
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": num_candidates,
                    "limit": max(limit, 1),
                }
            },
            {
                "$project": {
                    "title": 1,
                    "description": 1,
                    "url": 1,
                    "platform": 1,
                    "instructor": 1,
                    "rating": 1,
                    "duration": 1,
                    "price": 1,
                    "students_count": 1,
                    "language": 1,
                    "category": 1,
                    "level": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]
        start = time.time()
        try:
            candidates = list(self._get_collection().aggregate(pipeline))
        except PyMongoError as exc:
            logger.error(json.dumps({"event": "mongodb_vector_search_failed", "error": str(exc)}))
            raise
        search_time_ms = int((time.time() - start) * 1000)
        filtered = self._apply_filters(candidates, filters)
        if len(filtered) < limit and self._has_active_filters(filters):
            relaxed = self._apply_filters(candidates, {})
            filtered = relaxed[:limit]
        else:
            filtered = filtered[:limit]
        avg_score = sum(item.get("score", 0.0) for item in filtered) / len(filtered) if filtered else 0.0
        logger.info(
            json.dumps(
                {
                    "event": "vector_search_completed",
                    "courses_found": len(filtered),
                    "avg_similarity_score": round(avg_score, 4),
                    "search_time_ms": search_time_ms,
                }
            )
        )
        return [self._serialize_course(doc) for doc in filtered]

    def fetch_courses_by_ids(self, ids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        object_ids = [ObjectId(course_id) for course_id in ids if ObjectId.is_valid(course_id)]
        if not object_ids:
            return {}
        try:
            documents = self._get_collection().find({"_id": {"$in": object_ids}})
        except PyMongoError as exc:
            logger.error(json.dumps({"event": "mongodb_fetch_failed", "error": str(exc)}))
            raise
        mapped: Dict[str, Dict[str, Any]] = {}
        for doc in documents:
            mapped[str(doc["_id"])] = self._serialize_course(doc)
        return mapped

    def _apply_filters(self, candidates: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        def matches(course: Dict[str, Any]) -> bool:
            if filters.get("user_level") == "beginner" and course.get("level") == "advanced":
                return False
            if language := filters.get("language"):
                if course.get("language") != language:
                    return False
            if platforms := filters.get("preferred_platforms"):
                if course.get("platform") not in set(platforms):
                    return False
            max_price = filters.get("max_price")
            if max_price is not None and course.get("price") is not None:
                if float(course.get("price", 0.0)) > float(max_price):
                    return False
            desired_level = filters.get("user_level")
            if desired_level:
                levels_order = {"beginner": 0, "intermediate": 1, "advanced": 2}
                course_level_num = levels_order.get(course.get("level"), 1)
                desired_level_num = levels_order.get(desired_level, 1)
                if course_level_num > desired_level_num + 1:
                    return False
            return True

        return [course for course in candidates if matches(course)]

    def _has_active_filters(self, filters: Dict[str, Any]) -> bool:
        return any(value for key, value in filters.items() if key != "user_level")

    def _serialize_course(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        serialized = doc.copy()
        serialized["course_id"] = str(doc.get("_id"))
        serialized.pop("_id", None)
        return serialized


_mongo_client: Optional[MongoDBClient] = None


def get_mongo_client() -> MongoDBClient:
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoDBClient()
    return _mongo_client
