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

def insert_alert_document(db, minor_id, tutor_id, chat_id):
    """
    Inserta un documento de alerta en la colección 'alerts'.
    
    Args:
        db: El objeto de la base de datos.
        minor_id: El ObjectId del usuario menor de edad.
        tutor_id: El ObjectId del tutor.
        chat_id: El ObjectId del chat que generó la alerta.
    """
    alerts_collection = db.alerts
    
    # Crea el documento de la alerta
    new_alert = {
        "minorId": ObjectId(minor_id),
        "tutorId": ObjectId(tutor_id),
        "chatId": ObjectId(chat_id),
        "type": "grooming_pattern", # Puede ser otro tipo como "private_photo_request"
        "status": "pending",
        "message": "Se detectó un patrón de grooming en el chat del menor.",
        "riskDetails": {
            "suspiciousTerms": ["fotos", "secreto", "nos vemos"],
            "insistenceLevel": "high"
        },
        "createdAt": datetime.datetime.utcnow(),
        "resolvedAt": None
    }

    try:
        result = alerts_collection.insert_one(new_alert)
        print(f"Alerta insertada con éxito. ID de la alerta: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        print(f"Error al insertar la alerta: {e}")
        return None

if __name__ == "__main__":
    db = connect_to_db()
    
    # Reemplaza estos IDs con los de tus documentos de usuario y chat existentes
    # Por ejemplo: IDs de prueba para un menor, un tutor y un chat
    minor_user_id = "68a131cefccb7b61aa4352fb"  # ID del usuario menor
    tutor_user_id = "68a131cefccb7b61aa4352fa"  # ID del tutor
    chat_id = "68a13b637a0e3876fbc39599"       # ID del chat
    
    if db is not None:
        insert_alert_document(db, minor_user_id, tutor_user_id, chat_id)