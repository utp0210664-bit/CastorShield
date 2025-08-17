from pymongo import MongoClient
import datetime

# Tu cadena de conexión completa de MongoDB Atlas
MONGO_URI = "mongodb+srv://megamente044:dzoe3aKGojpkIAmL@cluster0.r8hg179.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

def connect_to_db():
    """Conecta a la base de datos de MongoDB y la retorna."""
    try:
        # Usa tu URI para crear el cliente
        client = MongoClient(MONGO_URI)
        
        # Selecciona tu base de datos específica
        db = client["antigroomingDB"]
        
        print("Conexión exitosa a la base de datos.")
        return db
    except Exception as e:
        print(f"Error al conectar: {e}")
        return None

def insert_minor_user(db):
    """Inserta un documento de un usuario menor en la colección 'users'."""
    users_collection = db.users
    
    # El documento a insertar
    minor_user = {
        "type": "minor",
        "username": "Laura_15",
        "email": "laura@example.com",
        "isVerified": {
            "age": True,
            "photo": True
        },
        "parentalConsent": {
            "isGiven": True,
            # Aquí es donde vincularías con el ObjectId real del tutor si ya lo tuvieras
            "guardianId": None 
        },
        "trustedContacts": [],
        "preferences": {
            "isGeolocationEnabled": False
        },
        "profileData": {
            "age": 15,
            "gender": "female",
            "biography": "Me gusta jugar videojuegos.",
            "emotionalState": "happy",
            "typicalPatterns": {
                "chatStyle": "friendly",
                "emojisUsed": ["😄", "🎮", "🌟"]
            }
        },
        "createdAt": datetime.datetime.utcnow(),
        "updatedAt": datetime.datetime.utcnow()
    }

    # Inserta el documento y maneja errores
    try:
        result = users_collection.insert_one(minor_user)
        print(f"Documento insertado con éxito. ID: {result.inserted_id}")
    except Exception as e:
        print(f"Error al insertar el documento: {e}")

if __name__ == "__main__":
    db = connect_to_db()
    if db is not None: # CAMBIO AQUÍ
        insert_minor_user(db)