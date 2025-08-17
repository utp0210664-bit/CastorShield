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

def insert_report_document(db, reporter_id, target_id, chat_id, message_index):
    """
    Inserta un documento de reporte en la colección 'reports'.
    
    Args:
        db: El objeto de la base de datos.
        reporter_id: El ObjectId del usuario que hace el reporte.
        target_id: El ObjectId del usuario reportado.
        chat_id: El ObjectId del chat que contiene la evidencia.
        message_index: El índice del mensaje dentro del chat que sirve de evidencia.
    """
    reports_collection = db.reports
    
    # Crea el documento del reporte
    new_report = {
        "reporterId": ObjectId(reporter_id),
        "targetId": ObjectId(target_id),
        "reason": "grooming_pattern", # Puede ser otro tipo como "suspicious_profile"
        "evidence": [
            {
                "chatId": ObjectId(chat_id),
                "messageIndex": message_index
            }
        ],
        "status": "pending",
        "createdAt": datetime.datetime.utcnow()
    }

    try:
        result = reports_collection.insert_one(new_report)
        print(f"Reporte insertado con éxito. ID del reporte: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        print(f"Error al insertar el reporte: {e}")
        return None

if __name__ == "__main__":
    db = connect_to_db()
    
    # Reemplaza estos IDs con los de tus documentos existentes
    reporter_id = "68a131cefccb7b61aa4352fb"     # ID del menor o tutor que reporta
    target_id = "68a131cefccb7b61aa4352fa"       # ID del usuario reportado
    chat_id = "68a13b637a0e3876fbc39599"         # ID del chat
    message_index = 5                            # Índice del mensaje dentro del chat

    if db is not None:
        insert_report_document(db, reporter_id, target_id, chat_id, message_index)