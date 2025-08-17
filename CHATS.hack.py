from pymongo import MongoClient
import datetime
from bson.objectid import ObjectId

# Tu cadena de conexión completa de MongoDB Atlas
MONGO_URI = "mongodb+srv://megamente044:dzoe3aKGojpkIAmL@cluster0.r8hg179.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

def connect_to_db():
    """Conecta a la base de datos de MongoDB y la retorna."""
    try:
        client = MongoClient(MONGO_URI)
        db = client["antigroomingDB"]
        print("Conexión exitosa a la base de datos.")
        return db
    except Exception as e:
        print(f"Error al conectar: {e}")
        return None

def insert_chat_document(db, minor_id, other_user_id):
    """
    Inserta un documento de chat con un mensaje inicial.
    
    Args:
        db: El objeto de la base de datos.
        minor_id: El ObjectId del usuario menor de edad.
        other_user_id: El ObjectId del otro usuario en el chat.
    """
    chats_collection = db.chats
    
    # Crea el documento del chat con un mensaje de ejemplo
    new_chat = {
        "participants": [ObjectId(minor_id), ObjectId(other_user_id)],
        "messages": [
            {
                "senderId": ObjectId(minor_id),
                "content": "¡Hola! ¿Qué tal?",
                "timestamp": datetime.datetime.utcnow(),
                "isSafe": True,
                "riskScore": 0.0,
                "flaggedTerms": [],
                "flags": [],
                "analyzedByAI": True
            }
        ],
        "isEncrypted": False, # Lo puedes cambiar a True si implementas encriptación
        "riskLevel": "low",
        "createdAt": datetime.datetime.utcnow(),
        "updatedAt": datetime.datetime.utcnow()
    }

    try:
        result = chats_collection.insert_one(new_chat)
        print(f"Chat insertado con éxito. ID del chat: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        print(f"Error al insertar el chat: {e}")
        return None

if __name__ == "__main__":
    db = connect_to_db()
    
    # Asegúrate de reemplazar estos IDs con los de tus usuarios existentes
    # Por ejemplo: '68a131cefccb7b61aa4352fb' es el ID que insertaste anteriormente
    minor_user_id = "68a131cefccb7b61aa4352fb"
    other_user_id = "667d4f91d5828a071c863a13" # Reemplaza con un ID de un usuario tutor o amigo
    
    if db is not None:
        new_chat_id = insert_chat_document(db, minor_user_id, other_user_id)
        if new_chat_id:
            # Aquí podrías usar el new_chat_id para futuras operaciones
            print(f"El ID del nuevo chat es: {new_chat_id}")