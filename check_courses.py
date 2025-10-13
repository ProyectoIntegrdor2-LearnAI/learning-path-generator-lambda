import os
from pymongo import MongoClient

# Get connection details from environment or use defaults
atlas_uri = os.getenv('ATLAS_URI', '')
if not atlas_uri:
    print("❌ ATLAS_URI no está configurado")
    print("Por favor, configura la variable de entorno ATLAS_URI")
    exit(1)

try:
    print(f"🔗 Conectando a MongoDB Atlas...")
    client = MongoClient(atlas_uri, serverSelectionTimeoutMS=5000)
    
    db = client['learnia_db']
    collection = db['courses']
    
    # Count total courses
    total_courses = collection.count_documents({})
    print(f"✅ Total de cursos en la colección: {total_courses}")
    
    if total_courses > 0:
        print(f"\n📋 Primeros 3 cursos:")
        for i, course in enumerate(collection.find().limit(3), 1):
            print(f"\n{i}. {course.get('title', 'Sin título')}")
            print(f"   Provider: {course.get('provider', 'N/A')}")
            print(f"   Level: {course.get('level', 'N/A')}")
            print(f"   URL: {course.get('url', 'N/A')}")
        
        # Check if courses have embeddings
        courses_with_embeddings = collection.count_documents({'embedding': {'$exists': True}})
        print(f"\n🔢 Cursos con embeddings: {courses_with_embeddings}")
    else:
        print("\n⚠️  No hay cursos en la base de datos")
        print("Esto explica por qué la Lambda retorna 'No se encontraron suficientes cursos'")
    
    client.close()
    print("\n✅ Verificación completada")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    exit(1)
