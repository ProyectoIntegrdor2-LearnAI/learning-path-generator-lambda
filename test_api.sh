#!/bin/bash

# Test script para Learning Path Generator Lambda
# Prueba el endpoint de API Gateway con diferentes queries

API_ENDPOINT="https://yhjk0mfvgc.execute-api.us-east-2.amazonaws.com/Prod/generate-learning-path"

echo "════════════════════════════════════════════════════════"
echo "🧪 Testing Learning Path Generator API"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📡 Endpoint: $API_ENDPOINT"
echo ""

# Test 1: Python básico
echo "🔹 Test 1: Python básico para principiantes"
echo "───────────────────────────────────────────"
curl -X POST "$API_ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "Origin: https://www.learn-ia.app" \
  -d '{
    "user_id": "test-user-1",
    "user_query": "I want to learn Python programming basics",
    "user_level": "beginner",
    "estimated_weeks": 8,
    "time_per_week": 10,
    "num_courses": 5
  }' \
  -w "\n⏱️  Time: %{time_total}s\n" \
  -s | jq '.' 2>/dev/null || echo "Error al procesar JSON"

echo ""
echo "════════════════════════════════════════════════════════"
echo ""

# Test 2: Machine Learning
echo "🔹 Test 2: Machine Learning intermedio"
echo "───────────────────────────────────────────"
curl -X POST "$API_ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "Origin: https://www.learn-ia.app" \
  -d '{
    "user_id": "test-user-2",
    "user_query": "I want to learn machine learning and artificial intelligence",
    "user_level": "intermediate",
    "estimated_weeks": 12,
    "time_per_week": 15,
    "num_courses": 8
  }' \
  -w "\n⏱️  Time: %{time_total}s\n" \
  -s | jq '.' 2>/dev/null || echo "Error al procesar JSON"

echo ""
echo "════════════════════════════════════════════════════════"
echo ""

# Test 3: Data Science
echo "🔹 Test 3: Data Science avanzado"
echo "───────────────────────────────────────────"
curl -X POST "$API_ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "Origin: https://www.learn-ia.app" \
  -d '{
    "user_id": "test-user-3",
    "user_query": "I want to become a data scientist with advanced statistics and deep learning",
    "user_level": "advanced",
    "estimated_weeks": 16,
    "time_per_week": 20,
    "num_courses": 10
  }' \
  -w "\n⏱️  Time: %{time_total}s\n" \
  -s | jq '.' 2>/dev/null || echo "Error al procesar JSON"

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ Tests completados"
echo ""
echo "📝 Nota: Si ves el error 'No se encontraron suficientes cursos'"
echo "   significa que la base de datos necesita ser poblada con cursos."
echo "════════════════════════════════════════════════════════"
