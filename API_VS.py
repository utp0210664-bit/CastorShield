# --- IMPORTS NECESARIOS ---
from flask import Flask, request, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
import datetime
import os
from dotenv import load_dotenv
import boto3
import google.generativeai as genai
import io
from PIL import Image
import json # <--- IMPORTANTE: Se añade la librería para manejar JSON

# --- CARGA DE VARIABLES DE ENTORNO ---
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- CONFIGURACIÓN DE LA APP FLASK ---
app = Flask(__name__)

# --- CONEXIÓN A MONGODB ---
try:
    client = MongoClient(MONGO_URI)
    db = client["antigroomingDB"]
    print("✅ Conexión exitosa a MongoDB")
except Exception as e:
    print(f"❌ Error al conectar a MongoDB: {e}")
    db = None

# --- CONFIGURACIÓN DE CLIENTES DE SERVICIOS EXTERNOS ---
# Cliente de AWS S3
if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
else:
    s3_client = None
    print("⚠️  Advertencia: Credenciales de AWS no configuradas. El análisis de imágenes no funcionará.")

# Modelo Generativo de Google (Gemini)
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
else:
    gemini_model = None
    print("⚠️  Advertencia: Clave de API de Gemini no configurada. El análisis de IA no funcionará.")

# --- FUNCIONES AUXILIARES ---
def validate_objectid(id_str, field_name="id"):
    """Valida si una cadena es un ObjectId válido de MongoDB."""
    try:
        if not id_str:
            raise ValueError(f"El campo '{field_name}' no puede estar vacío")
        return ObjectId(id_str)
    except (InvalidId, TypeError):
        raise ValueError(f"'{field_name}' inválido: {id_str}")

def success_response(data=None, message="Operación exitosa", code=200):
    """Genera una respuesta JSON de éxito."""
    return jsonify({"success": True, "message": message, "data": data}), code

def error_response(message="Error en la operación", code=400):
    """Genera una respuesta JSON de error."""
    return jsonify({"success": False, "error": message}), code

# --- ENDPOINTS DE LA API ---

@app.route('/analyze/screenshot', methods=['POST'])
def analyze_screenshot():
    if db is None:
        return error_response("No hay conexión a la base de datos", 500)
    if not s3_client or not gemini_model:
        return error_response("Servicio de S3 o Gemini no disponible. Revisa tus credenciales.", 503)

    data = request.json or {}
    required_fields = ["s3_url", "minor_id", "tutor_id"]
    if not all(field in data for field in required_fields):
        return error_response(f"Faltan campos obligatorios: {', '.join(required_fields)}", 400)

    try:
        s3_url = data["s3_url"]
        minor_id_obj = validate_objectid(data["minor_id"], "minor_id")
        tutor_id_obj = validate_objectid(data["tutor_id"], "tutor_id")
        
        # MEJORA: Una forma un poco más segura de extraer bucket y key
        # Asume una URL como https://bucket-name.s3.region.amazonaws.com/key/name.jpg
        # O https://s3.region.amazonaws.com/bucket-name/key/name.jpg
        # Para este proyecto, se mantiene el bucket fijo y se extrae la clave.
        bucket_name = "hackbucket1angel" # Esto sigue fijo según tu código original
        if f'/{bucket_name}/' not in s3_url:
            return error_response("URL de S3 no contiene el bucket esperado.", 400)
        key_name = s3_url.split(f'/{bucket_name}/')[1]

        # Descargar la imagen de S3 a la memoria
        s3_object = s3_client.get_object(Bucket=bucket_name, Key=key_name)
        image_bytes = s3_object['Body'].read()
        
        # Convertir bytes a un objeto de imagen para Gemini
        img = Image.open(io.BytesIO(image_bytes))

        # Petición a la API de Gemini
        prompt = (
            "Analiza esta captura de pantalla de un chat. Detecta comportamientos de riesgo: grooming, lenguaje "
            "inapropiado, petición de información personal, o signos de peligro. "
            "Devuelve únicamente un objeto JSON con dos claves: 'riskScore' (un número de 0.0 a 1.0) y 'analysis' (una descripción breve del hallazgo). "
            "Si no hay riesgo, 'riskScore' debe ser 0.0."
        )
        
        response = gemini_model.generate_content([prompt, img])
        
        # === MEJORA PRINCIPAL: PARSEO CORRECTO DEL JSON ===
        # 1. Limpiar el texto de la respuesta para quitar formato markdown
        analysis_raw_text = response.text
        clean_text = analysis_raw_text.replace('```json', '').replace('```', '').strip()
        
        # 2. Convertir la cadena de texto JSON a un diccionario de Python
        try:
            analysis_data = json.loads(clean_text)
        except json.JSONDecodeError:
            print(f"Error al decodificar JSON. Respuesta de Gemini: {clean_text}")
            return error_response("La respuesta de la IA no tuvo un formato JSON válido.", 500)

        # 3. Obtener los valores del diccionario de forma segura
        risk_score = analysis_data.get("riskScore", 0.0)
        analysis_text = analysis_data.get("analysis", "No se proporcionó análisis.")
        # =======================================================

        # Si la puntuación de riesgo es alta, se inserta una alerta en MongoDB
        if risk_score > 0.5:
            new_alert = {
                "minorId": minor_id_obj,
                "tutorId": tutor_id_obj,
                "chatId": None, # Es una captura, no un chat de la DB
                "type": "screenshot_risk",
                "status": "pending",
                "message": f"Se detectó un posible riesgo en una captura de pantalla. Puntuación: {risk_score}",
                "riskDetails": {
                    "score": risk_score,
                    "analysis_summary": analysis_text,
                    "imageUrl": s3_url
                },
                "createdAt": datetime.datetime.utcnow(),
                "resolvedAt": None
            }
            db.alerts.insert_one(new_alert)
            return success_response({"riskScore": risk_score, "analysis": analysis_text}, "Riesgo detectado. Alerta creada.", 201)
        
        # Si el riesgo es bajo, no se guarda nada
        return success_response({"riskScore": risk_score, "analysis": analysis_text}, "Análisis completado. No se detectó un riesgo significativo.", 200)

    except ValueError as ve:
        return error_response(str(ve), 400)
    except Exception as e:
        # Es buena práctica registrar el error para depuración
        print(f"Error inesperado en /analyze/screenshot: {e}")
        return error_response(f"Error en el proceso de análisis: {e}", 500)

# ... (todo tu código anterior) ...
from waitress import serve # <-- Importa la función serve

# Aquí irían el resto de tus endpoints (users, chats, alerts, etc.)...

if __name__ == '__main__':
    # En lugar de app.run(), usamos serve de Waitress
    print("✅ Servidor Waitress iniciado en http://127.0.0.1:5000")
    serve(app, host='127.0.0.1', port=5000)