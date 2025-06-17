import os
import re
import logging
from typing import List, Dict, Tuple
from knowledge_base import KnowledgeBase

class UExChatbot:
    def __init__(self, hf_token: str = None):
        self.knowledge_base = KnowledgeBase()
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Palabras clave del dominio UEx
        self.uex_keywords = [
            'universidad', 'extremadura', 'uex', 'grado', 'master', 'doctorado',
            'facultad', 'escuela', 'badajoz', 'cáceres', 'mérida', 'plasencia',
            'investigación', 'estudiante', 'profesor', 'titulación', 'matrícula',
            'preinscripción', 'campus', 'biblioteca', 'pau', 'selectividad',
            'becas', 'erasmus', 'postgrado', 'máster', 'tesis', 'tfg', 'tfm'
        ]
        
        # Patrones de preguntas comunes mejorados
        self.question_patterns = {
            'estudios': ['qué estudios', 'qué grados', 'qué carreras', 'qué titulaciones', 'estudiar', 'carrera', 'ofertas', 'titulacion', 'grado'],
            'campus': ['dónde', 'campus', 'ubicación', 'lugar', 'sede', 'centros', 'facultades', 'donde está', 'donde se encuentra'],
            'matricula': ['matrícula', 'matricular', 'inscripción', 'preinscripción', 'inscribir', 'plazo', 'automatrícula', 'como matricular'],
            'pau': ['pau', 'selectividad', 'acceso', 'nota de corte', 'prueba acceso', 'evau'],
            'becas': ['becas', 'ayudas', 'financiación', 'beca', 'ayuda', 'económica'],
            'master': ['máster', 'master', 'postgrado', 'posgrado', 'especialización'],
            'doctorado': ['doctorado', 'tesis', 'phd', 'doctor', 'investigación'],
            'servicios': ['biblioteca', 'deportes', 'idiomas', 'servicios', 'comedor', 'residencia'],
            'noticias': ['noticias', 'novedades', 'eventos', 'últimas', 'nuevas', 'actualidad'],
            'contacto': ['contacto', 'teléfono', 'dirección', 'email', 'donde', 'como contactar']
        }
        
        self.logger.info("UEx Chatbot initialized successfully (Advanced context-based system)")
    
    def is_uex_related(self, question: str) -> bool:
        """Determina si la pregunta está relacionada con la UEx"""
        question_lower = question.lower()
        
        # Buscar palabras clave del dominio
        for keyword in self.uex_keywords:
            if keyword in question_lower:
                return True
        
        # Buscar contenido relacionado en la base de conocimiento
        search_results = self.knowledge_base.search(question, n_results=3)
        
        # Si encuentra resultados relevantes, considerar que está relacionado
        if search_results and len(search_results) > 0:
            # Verificar si el primer resultado tiene una puntuación razonable
            if search_results[0].get('score', 1.0) < 0.8:  # Umbral de similitud
                return True
        
        return False
    
    def classify_question_type(self, question: str) -> str:
        """Clasifica el tipo de pregunta para dar una respuesta más específica"""
        question_lower = question.lower()
        
        for category, patterns in self.question_patterns.items():
            for pattern in patterns:
                if pattern in question_lower:
                    return category
        
        return 'general'
    
    def get_context(self, question: str, max_context_length: int = 3000) -> List[Dict]:
        """Obtiene contexto relevante de la base de conocimiento"""
        search_results = self.knowledge_base.search(question, n_results=8)
        
        filtered_results = []
        total_length = 0
        
        for result in search_results:
            content = result['content']
            # Limpiar y mejorar el contenido
            content = self.clean_content(content)
            
            if content and len(content) > 50:  # Solo contenido significativo
                if total_length + len(content) < max_context_length:
                    result['content'] = content
                    filtered_results.append(result)
                    total_length += len(content)
                else:
                    # Añadir parte del contenido que quepa
                    remaining_space = max_context_length - total_length
                    if remaining_space > 200:
                        truncated_result = result.copy()
                        truncated_result['content'] = content[:remaining_space]
                        filtered_results.append(truncated_result)
                    break
        
        return filtered_results
    
    def clean_content(self, content: str) -> str:
        """Limpia y mejora el contenido extraído"""
        # Eliminar múltiples espacios en blanco
        content = re.sub(r'\s+', ' ', content)
        
        # Eliminar caracteres de control y extraños
        content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
        
        # Eliminar fragmentos muy cortos
        sentences = content.split('.')
        cleaned_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 15 and not sentence.startswith(('http', 'www')):
                cleaned_sentences.append(sentence)
        
        return '. '.join(cleaned_sentences)
    
    def extract_key_information(self, content_list: List[Dict], question_type: str, question: str) -> List[str]:
        """Extrae información clave del contenido basado en el tipo de pregunta"""
        key_info = []
        question_words = set(question.lower().split())
        
        for content_item in content_list:
            content = content_item['content']
            sentences = content.split('.')
            
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) < 20:
                    continue
                
                sentence_lower = sentence.lower()
                
                # Filtros específicos por tipo de pregunta
                if question_type == 'estudios':
                    if any(word in sentence_lower for word in ['grado', 'carrera', 'titulación', 'estudio', 'oferta', 'académica']):
                        key_info.append(sentence)
                elif question_type == 'campus':
                    if any(word in sentence_lower for word in ['campus', 'badajoz', 'cáceres', 'mérida', 'plasencia', 'facultad', 'centro']):
                        key_info.append(sentence)
                elif question_type == 'matricula':
                    if any(word in sentence_lower for word in ['matrícula', 'plazo', 'inscripción', 'preinscripción', 'automatrícula', 'proceso']):
                        key_info.append(sentence)
                elif question_type == 'pau':
                    if any(word in sentence_lower for word in ['pau', 'selectividad', 'acceso', 'prueba', 'calificación']):
                        key_info.append(sentence)
                elif question_type == 'becas':
                    if any(word in sentence_lower for word in ['beca', 'ayuda', 'financiación', 'económica']):
                        key_info.append(sentence)
                elif question_type == 'master':
                    if any(word in sentence_lower for word in ['máster', 'master', 'postgrado', 'posgrado']):
                        key_info.append(sentence)
                else:
                    # Para preguntas generales, buscar coincidencias de palabras
                    sentence_words = set(sentence_lower.split())
                    common_words = question_words.intersection(sentence_words)
                    if len(common_words) >= 2 or any(len(word) > 5 and word in sentence_lower for word in question_words):
                        key_info.append(sentence)
        
        # Eliminar duplicados manteniendo el orden
        seen = set()
        unique_info = []
        for info in key_info:
            if info not in seen:
                seen.add(info)
                unique_info.append(info)
        
        return unique_info[:5]  # Máximo 5 fragmentos clave
    
    def generate_structured_response(self, question: str, context_results: List[Dict], question_type: str) -> str:
        """Genera una respuesta estructurada basada en el contexto"""
        
        if not context_results:
            return self.get_default_response(question_type)
        
        # Extraer información clave
        key_info = self.extract_key_information(context_results, question_type, question)
        
        if not key_info:
            return self.generate_basic_response(context_results, question_type)
        
        # Generar respuesta según el tipo
        response = ""
        
        if question_type == 'estudios':
            response = "**Estudios en la Universidad de Extremadura:**\n\n"
            response += "La UEx ofrece una amplia variedad de titulaciones. Según la información oficial:\n\n"
            
        elif question_type == 'campus':
            response = "**Campus de la Universidad de Extremadura:**\n\n"
            
        elif question_type == 'matricula':
            response = "**Información sobre matrícula en la UEx:**\n\n"
            
        elif question_type == 'pau':
            response = "**Información sobre la PAU (Prueba de Acceso a la Universidad):**\n\n"
            
        elif question_type == 'becas':
            response = "**Becas y ayudas en la UEx:**\n\n"
            
        elif question_type == 'master':
            response = "**Másteres en la Universidad de Extremadura:**\n\n"
            
        else:
            response = "**Información de la Universidad de Extremadura:**\n\n"
        
        # Añadir la información clave
        for i, info in enumerate(key_info[:3], 1):
            response += f"{i}. {info}\n\n"
        
        # Añadir información adicional si hay más contexto
        if len(context_results) > 1:
            response += "**Información adicional:**\n"
            additional_info = []
            for result in context_results[1:3]:  # Usar 2-3 resultados adicionales
                content = result['content']
                sentences = content.split('.')[:2]  # Primeras 2 oraciones
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 30 and sentence not in response:
                        additional_info.append(sentence)
                        if len(additional_info) >= 2:
                            break
                if len(additional_info) >= 2:
                    break
            
            if additional_info:
                response += " ".join(additional_info[:2]) + "."
        
        # Añadir recomendación final
        response += "\n\n**Para más información detallada, consulta la web oficial de la UEx.**"
        
        return response
    
    def generate_basic_response(self, context_results: List[Dict], question_type: str) -> str:
        """Genera una respuesta básica cuando no hay información específica"""
        if not context_results:
            return self.get_default_response(question_type)
        
        # Usar el primer resultado como base
        main_content = context_results[0]['content']
        sentences = [s.strip() for s in main_content.split('.') if len(s.strip()) > 30]
        
        response = "Según la información disponible de la Universidad de Extremadura:\\n\\n"
        
        if sentences:
            response += sentences[0]
            if len(sentences) > 1:
                response += f". {sentences[1]}"
            response += "."
        
        response += "\\n\\nPara información más específica, te recomiendo consultar la web oficial de la UEx o contactar directamente con el servicio correspondiente."
        
        return response
    
    def get_default_response(self, question_type: str) -> str:
        """Respuestas por defecto mejoradas cuando no hay contexto"""
        defaults = {
            'estudios': """**Estudios en la Universidad de Extremadura:**

La UEx ofrece una amplia variedad de grados, másteres y programas de doctorado en diferentes áreas de conocimiento:

• **Grados:** Más de 60 titulaciones en áreas como Ingeniería, Ciencias de la Salud, Humanidades, Ciencias Sociales, etc.
• **Másteres:** Amplia oferta de másteres oficiales y títulos propios
• **Doctorados:** Programas de doctorado en diversas especialidades

Para consultar toda la oferta académica actualizada, visita la web oficial de la UEx.""",

            'campus': """**Campus de la Universidad de Extremadura:**

La UEx cuenta con campus distribuidos por toda Extremadura:

• **Badajoz:** Campus principal con múltiples facultades
• **Cáceres:** Importantes centros y facultades
• **Mérida:** Centro universitario especializado
• **Plasencia:** Centro universitario

Cada campus ofrece diferentes titulaciones y servicios especializados.""",

            'matricula': """**Matrícula en la UEx:**

El proceso de matrícula en la Universidad de Extremadura incluye:

• **Preinscripción:** Solicitud de plaza en las titulaciones deseadas
• **Matrícula:** Formalización de la inscripción una vez admitido
• **Automatrícula:** Sistema online para estudiantes

Consulta la sección de alumnado en la web oficial para conocer plazos, procedimientos y documentación necesaria.""",

            'pau': """**PAU - Prueba de Acceso a la Universidad:**

La PAU (también conocida como EVAU o Selectividad) es necesaria para acceder a los estudios universitarios:

• **Fechas:** Generalmente en junio y julio
• **Sedes:** Múltiples ubicaciones en Extremadura
• **Calificaciones:** Disponibles online tras la corrección

En alumnado.unex.es encontrarás toda la información actualizada sobre fechas, sedes, procedimientos y resultados.""",

            'becas': """**Becas y ayudas en la UEx:**

La Universidad de Extremadura ofrece diversas becas y ayudas:

• **Becas del Ministerio:** Becas generales de carácter estatal
• **Becas de la Junta de Extremadura:** Ayudas autonómicas
• **Becas propias de la UEx:** Ayudas específicas de la universidad
• **Becas de excelencia académica:** Para estudiantes destacados

Consulta el servicio de becas para información sobre convocatorias vigentes y requisitos.""",

            'master': """**Másteres en la UEx:**

La Universidad de Extremadura ofrece una amplia gama de másteres:

• **Másteres oficiales:** Títulos con validez en el Espacio Europeo de Educación Superior
• **Másteres propios:** Títulos especializados de la universidad
• **Modalidades:** Presencial, semipresencial y online según el programa

Consulta la oferta completa en la web oficial para encontrar el máster que mejor se adapte a tu perfil profesional.""",

            'general': """**Universidad de Extremadura - Información General:**

¿En qué puedo ayudarte sobre la UEx? Puedo proporcionarte información sobre:

• **Estudios:** Grados, másteres y doctorados
• **Campus:** Ubicaciones y centros
• **Matrícula:** Procesos y plazos
• **PAU:** Prueba de acceso a la universidad
• **Becas:** Ayudas y financiación
• **Servicios:** Biblioteca, deportes, idiomas, etc.

Pregúntame sobre cualquier aspecto específico de la Universidad de Extremadura."""
        }
        return defaults.get(question_type, defaults['general'])
    
    def chat(self, question: str) -> str:
        """Función principal del chatbot"""
        # Verificar si la pregunta está relacionada con la UEx
        if not self.is_uex_related(question):
            return ("Lo siento, solo puedo responder preguntas relacionadas con la "
                   "Universidad de Extremadura. ¿Tienes alguna consulta sobre la UEx?")
        
        # Clasificar tipo de pregunta
        question_type = self.classify_question_type(question)
        
        # Obtener contexto relevante
        context_results = self.get_context(question)
        
        # Generar respuesta estructurada
        response = self.generate_structured_response(question, context_results, question_type)
        
        return response

# Función para crear una instancia del chatbot
def create_chatbot(hf_token: str = None) -> UExChatbot:
    """Factory function para crear el chatbot"""
    return UExChatbot(hf_token=hf_token)

if __name__ == "__main__":
    # Cargar token desde variable de entorno
    hf_token = os.getenv('HUGGINGFACE_TOKEN')
    
    # Crear chatbot
    chatbot = create_chatbot(hf_token)
    
    # Chat interactivo
    print("Chatbot UEx inicializado. Escribe 'salir' para terminar.")
    print("Solo respondo preguntas sobre la Universidad de Extremadura.\\n")
    
    while True:
        question = input("Tú: ")
        if question.lower() in ['salir', 'exit', 'quit']:
            break
        
        response = chatbot.chat(question)
        print(f"Chatbot: {response}\\n")
