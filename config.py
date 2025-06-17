"""
Configuración centralizada para el chatbot UEx
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    # Hugging Face
    HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN')
    MODEL_NAME = os.getenv('MODEL_NAME', 'microsoft/DialoGPT-medium')
    
    # Web Scraping
    BASE_URL = os.getenv('BASE_URL', 'https://www.unex.es/')
    MAX_PAGES = int(os.getenv('MAX_PAGES', 50))
    
    # Base de datos
    CHROMA_DB_PATH = os.getenv('CHROMA_DB_PATH', './chroma_db')
    CONTENT_JSON_FILE = 'unex_content.json'
    
    # Configuración del chatbot
    MAX_CONTEXT_LENGTH = 1000
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50
    
    # Palabras clave del dominio UEx
    UEX_KEYWORDS = [
        'universidad', 'extremadura', 'uex', 'grado', 'master', 'doctorado',
        'facultad', 'escuela', 'badajoz', 'cáceres', 'mérida', 'plasencia',
        'investigación', 'estudiante', 'profesor', 'titulación', 'matrícula',
        'preinscripción', 'campus', 'biblioteca', 'pau', 'selectividad',
        'cursos', 'becas', 'prácticas', 'erasmus', 'siaa'
    ]
    
    @classmethod
    def validate_config(cls):
        """Valida la configuración"""
        issues = []
        
        if not cls.HUGGINGFACE_TOKEN or cls.HUGGINGFACE_TOKEN == 'tu_token_aqui':
            issues.append("Token de Hugging Face no configurado en .env")
        
        if not os.path.exists(cls.CONTENT_JSON_FILE):
            issues.append(f"Archivo {cls.CONTENT_JSON_FILE} no encontrado. Ejecuta web_scraper.py primero.")
        
        return issues

# Configuración global
config = Config()
