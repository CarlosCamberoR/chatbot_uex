import streamlit as st
import os
from dotenv import load_dotenv
from chatbot import create_chatbot
from knowledge_base import KnowledgeBase
import json
import time

# Cargar variables de entorno
load_dotenv()

def initialize_chatbot():
    """Inicializa el chatbot con caché"""
    if 'chatbot' not in st.session_state:
        hf_token = os.getenv('HUGGINGFACE_TOKEN')
        with st.spinner('🤖 Inicializando chatbot...'):
            st.session_state.chatbot = create_chatbot(hf_token)
    return st.session_state.chatbot

def initialize_knowledge_base():
    """Inicializa la base de conocimiento"""
    if 'kb_loaded' not in st.session_state:
        kb = KnowledgeBase()
        
        # Buscar archivos de datos disponibles
        files_to_try = [
            "unex_content_enhanced.json",
            "unex_content.json"
        ]
        
        for json_file in files_to_try:
            if os.path.exists(json_file):
                with st.spinner('📚 Cargando base de conocimiento...'):
                    kb.load_from_json(json_file)
                st.session_state.kb_loaded = True
                st.session_state.data_file = json_file
                return True
        
        return False
    return True

def format_response(response):
    """Mejora el formato de las respuestas"""
    # Si la respuesta tiene markdown, la mantenemos
    if "**" in response and ":" in response:
        return response
    
    # Si no, añadimos formato básico
    lines = response.split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            # Si es una línea con números (lista)
            if line.startswith(('1.', '2.', '3.', '•')):
                formatted_lines.append(f"• {line[2:].strip()}")
            else:
                formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)

def main():
    st.set_page_config(
        page_title="Chatbot Universidad de Extremadura",
        page_icon="🎓",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Estilo CSS personalizado mejorado
    st.markdown("""
    <style>
    /* Estilo general */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #1f4e79 0%, #2e5c8a 50%, #3a6ea5 100%);
        color: white;
        padding: 2rem 1rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(31, 78, 121, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.2rem;
        opacity: 0.9;
    }
    
    /* Contenedores de chat */
    .stChatMessage {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    [data-testid="stChatMessageContent"] {
        background: transparent;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: white;
        border-radius: 15px;
        margin: 1rem;
        padding: 1rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    /* Botones */
    .stButton > button {
        width: 100%;
        border-radius: 10px;
        border: 2px solid #2e5c8a;
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        color: #2e5c8a;
        font-weight: 600;
        padding: 0.6rem 1rem;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(46, 92, 138, 0.2);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #2e5c8a 0%, #1f4e79 100%);
        color: white;
        border-color: #1f4e79;
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(46, 92, 138, 0.4);
    }
    
    /* Input de chat */
    .stChatInputContainer {
        background: white;
        border-radius: 15px;
        border: 2px solid #e3f2fd;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    /* Métricas */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e3f2fd;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Alertas de estado */
    .status-success {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(40, 167, 69, 0.2);
    }
    
    .status-error {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        color: #721c24;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(220, 53, 69, 0.2);
    }
    
    /* Spinner personalizado */
    .stSpinner {
        color: #2e5c8a !important;
    }
    
    /* Títulos de secciones */
    .section-title {
        color: #1f4e79;
        font-weight: 700;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #e3f2fd;
    }
    
    /* Cards de información */
    .info-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border: 1px solid rgba(46, 92, 138, 0.1);
    }
    
    /* Animaciones */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header principal
    st.markdown("""
    <div class="main-header fade-in">
        <h1>🎓 Chatbot Universidad de Extremadura</h1>
        <p>Tu asistente virtual inteligente para consultas sobre la UEx</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar con información mejorada
    with st.sidebar:
        st.markdown('<h2 class="section-title">ℹ️ Información</h2>', unsafe_allow_html=True)
        
        # Estado de la base de conocimiento
        kb_status = initialize_knowledge_base()
        if kb_status:
            st.markdown("""
            <div class="status-success">
                <strong>✅ Sistema Operativo</strong><br>
                Base de conocimiento cargada correctamente
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-error">
                <strong>❌ Sistema No Disponible</strong><br>
                Base de conocimiento no disponible
            </div>
            """, unsafe_allow_html=True)
            st.info("💡 Ejecuta primero `python web_scraper_new.py` o `python web_scraper.py` para recopilar datos.")
        
        st.markdown("---")
        
        # Información sobre capacidades
        st.markdown("""
        <div class="info-card">
            <h4>🔍 ¿Qué puedo hacer?</h4>
            <ul>
                <li><strong>Estudios</strong> - Grados, másteres y doctorados</li>
                <li><strong>Campus</strong> - Ubicaciones y servicios</li>
                <li><strong>Matrícula</strong> - Procesos y requisitos</li>
                <li><strong>PAU</strong> - Pruebas de acceso universitario</li>
                <li><strong>Becas</strong> - Ayudas y convocatorias</li>
                <li><strong>Investigación</strong> - Grupos y proyectos</li>
                <li><strong>Noticias</strong> - Últimas actualizaciones</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Estadísticas del sistema
        if kb_status:
            st.markdown('<h4 class="section-title">📊 Estadísticas</h4>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Páginas", "102", "✅")
            with col2:
                st.metric("Chunks", "1325", "✅")
        
        st.markdown("---")
        
        # Información adicional
        st.markdown("""
        <div class="info-card">
            <h4>⚠️ Importante</h4>
            <p>Solo respondo preguntas relacionadas con la Universidad de Extremadura. 
            Para consultas específicas sobre tu expediente o trámites personales, 
            contacta directamente con los servicios universitarios.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Área principal
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<h2 class="section-title">💬 Chat Interactivo</h2>', unsafe_allow_html=True)
        
        # Verificar si la base de conocimiento está disponible
        if not initialize_knowledge_base():
            st.markdown("""
            <div class="status-error">
                <strong>⚠️ Sistema No Disponible</strong><br>
                La base de conocimiento no está disponible. Por favor, ejecuta primero el scraper de datos.
            </div>
            """, unsafe_allow_html=True)
            st.stop()
        
        # Inicializar historial de chat
        if 'messages' not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "¡Hola! 👋 Soy el asistente virtual de la Universidad de Extremadura. Estoy aquí para ayudarte con cualquier consulta sobre la UEx. ¿En qué puedo ayudarte hoy?"}
            ]
        
        # Contenedor de chat con scroll
        chat_container = st.container()
        with chat_container:
            # Mostrar historial de chat
            for i, message in enumerate(st.session_state.messages):
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # Input del usuario
        if prompt := st.chat_input("Escribe tu pregunta sobre la UEx... 💭"):
            # Mostrar mensaje del usuario
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generar respuesta
            with st.chat_message("assistant"):
                with st.spinner("🤔 Analizando tu consulta..."):
                    chatbot = initialize_chatbot()
                    response = chatbot.chat(prompt)
                st.markdown(response)
            
            # Añadir respuesta al historial
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    with col2:
        st.markdown('<h3 class="section-title">🔧 Herramientas</h3>', unsafe_allow_html=True)
        
        # Botón para limpiar chat
        if st.button("🗑️ Nuevo Chat", use_container_width=True, help="Limpia el historial de conversación"):
            st.session_state.messages = [
                {"role": "assistant", "content": "¡Hola! 👋 Soy el asistente virtual de la Universidad de Extremadura. Estoy aquí para ayudarte con cualquier consulta sobre la UEx. ¿En qué puedo ayudarte hoy?"}
            ]
            st.rerun()
        
        # Botón para exportar chat
        if len(st.session_state.messages) > 1:
            chat_text = "\n\n".join([f"**{msg['role'].title()}**: {msg['content']}" for msg in st.session_state.messages])
            st.download_button(
                "📥 Exportar Chat",
                chat_text,
                file_name="chat_uex.txt",
                mime="text/plain",
                use_container_width=True,
                help="Descarga el historial de conversación"
            )
        
        st.markdown("---")
        
        # Ejemplos de preguntas
        st.markdown('<h4 class="section-title">💡 Preguntas Frecuentes</h4>', unsafe_allow_html=True)
        
        example_questions = [
            ("📚 Estudios", "¿Qué grados puedo estudiar en la UEx?"),
            ("🏛️ Campus", "¿Dónde están los campus universitarios?"),
            ("📝 Matrícula", "¿Cómo me matriculo en un grado?"),
            ("📖 Biblioteca", "¿Qué servicios tiene la biblioteca?"),
            ("🎓 PAU", "¿Cómo accedo a la PAU?"),
            ("💰 Becas", "¿Qué becas están disponibles?"),
            ("📰 Noticias", "¿Cuáles son las últimas noticias?"),
            ("🔬 Investigación", "¿Qué grupos de investigación hay?")
        ]
        
        for emoji_title, question in example_questions:
            if st.button(f"{emoji_title}", use_container_width=True, help=question):
                # Añadir pregunta al chat
                st.session_state.messages.append({"role": "user", "content": question})
                
                # Generar respuesta
                chatbot = initialize_chatbot()
                response = chatbot.chat(question)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.rerun()
        
        st.markdown("---")
        
        # Footer con información
        st.markdown("""
        <div class="info-card">
            <small>
            <strong>🎓 Universidad de Extremadura</strong><br>
            Chatbot desarrollado para facilitar el acceso a la información universitaria.
            </small>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
