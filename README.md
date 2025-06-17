# 🎓 Chatbot Universidad de Extremadura

Un chatbot inteligente avanzado que utiliza IA y procesamiento de lenguaje natural para responder preguntas sobre la Universidad de Extremadura (UEx). El sistema extrae información actualizada del sitio web oficial y documentos PDF para proporcionar respuestas precisas y contextuales.

## ✨ Características Principales

- 🕷️ **Web Scraping Avanzado**: Extrae contenido automáticamente del sitio web de la UEx incluyendo documentos PDF
- 🧠 **IA Conversacional**: Sistema de respuestas contextuales inteligente sin dependencia de modelos generativos problemáticos
- 📚 **Base de Conocimiento Vectorial**: Sistema de búsqueda semántica con ChromaDB y embeddings multilingües
- 📄 **Procesamiento de PDFs**: Capacidad para extraer y procesar información de documentos PDF oficiales
- 🎯 **Filtrado de Dominio**: Solo responde preguntas relacionadas con la UEx con detección automática de temas
- 🌐 **Interfaz Web Moderna**: Aplicación Streamlit con diseño atractivo y funcional
- 📊 **Estadísticas en Tiempo Real**: Monitoreo del estado del sistema y métricas de contenido

## 🚀 Instalación y Configuración

### Prerrequisitos

- Python 3.8+ (recomendado 3.10)
- Conda o pip para gestión de paquetes
- Token de Hugging Face (opcional, para funcionalidades avanzadas)

### 1. Clonar e instalar dependencias

```bash
git clone <repo-url>
cd chatbot_uex

# Crear entorno conda (recomendado)
conda create -n chatbot_uex python=3.10
conda activate chatbot_uex

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Crear archivo `.env` en la raíz del proyecto:

```env
HUGGINGFACE_TOKEN=tu_token_aqui  # Opcional
```

### 3. Ejecutar el sistema completo

#### Paso 1: Extraer datos (Web Scraping)
```bash
python web_scraper.py
```
Este proceso:
- Extrae contenido de ~150 páginas del sitio web de la UEx
- Procesa documentos PDF automáticamente
- Genera el archivo `unex_content.json` con toda la información

#### Paso 2: Crear base de conocimiento
```bash
python knowledge_base.py
```
Este proceso:
- Procesa el contenido extraído en chunks semánticos
- Crea embeddings multilingües optimizados
- Genera la base de datos vectorial en `chroma_db/`

#### Paso 3: Ejecutar la interfaz web
```bash
streamlit run app.py
```
La aplicación estará disponible en: `http://localhost:8501`

## 🏗️ Arquitectura del Sistema

### Componentes Principales

1. **`web_scraper.py`** - Sistema de extracción de contenido
   - Scraping inteligente de páginas web
   - Procesamiento automático de PDFs con PyPDF2
   - Filtrado y limpieza de contenido
   - Estadísticas detalladas del proceso

2. **`knowledge_base.py`** - Base de conocimiento vectorial
   - Chunking semántico de documentos
   - Embeddings con `paraphrase-multilingual-MiniLM-L12-v2`
   - Almacenamiento en ChromaDB
   - Sistema de búsqueda por similitud

3. **`chatbot.py`** - Motor conversacional
   - Sistema de respuestas contextuales
   - Clasificación automática de preguntas
   - Respuestas estructuradas en Markdown
   - Detección de preguntas fuera del dominio

4. **`app.py`** - Interfaz de usuario
   - Aplicación Streamlit moderna
   - Chat interactivo en tiempo real
   - Botones de preguntas frecuentes
   - Exportación de conversaciones

5. **`config.py`** - Configuración centralizada
   - Parámetros del sistema
   - Configuración de modelos
   - Rutas y constantes

### Estructura del Proyecto

```
chatbot_uex/
├── .env                    # Variables de entorno
├── README.md              # Documentación
├── requirements.txt       # Dependencias del proyecto
├── config.py             # Configuración centralizada
├── web_scraper.py        # Extractor de contenido con soporte PDF
├── knowledge_base.py     # Base de datos vectorial
├── chatbot.py           # Motor conversacional inteligente
├── app.py               # Interfaz web Streamlit
├── unex_content.json    # Datos extraídos (generado automáticamente)
└── chroma_db/           # Base de datos vectorial (generada automáticamente)
    ├── chroma.sqlite3
    └── [archivos de índices vectoriales]
```

## 💡 Ejemplos de Uso

### Preguntas que puede responder:

- **Estudios**: "¿Qué grados puedo estudiar en la UEx?"
- **Campus**: "¿Dónde están ubicados los campus universitarios?"
- **Matrícula**: "¿Cómo me matriculo en un grado?"
- **PAU**: "¿Cómo funciona la prueba de acceso universitario?"
- **Becas**: "¿Qué becas están disponibles para estudiantes?"
- **Servicios**: "¿Qué servicios ofrece la biblioteca universitaria?"
- **Investigación**: "¿Qué grupos de investigación hay en la UEx?"
- **Noticias**: "¿Cuáles son las últimas noticias de la universidad?"

## 🔧 Características Técnicas

### Web Scraping Inteligente
- **Cobertura**: ~150 páginas del ecosistema unex.es
- **Formatos**: HTML y PDF
- **Filtrado**: Contenido relevante y limpieza automática
- **Respeto**: Pausas entre requests y headers apropiados

### Base de Conocimiento Avanzada
- **Motor**: ChromaDB para búsqueda vectorial
- **Embeddings**: Modelo multilingüe optimizado para español
- **Chunks**: Segmentación semántica inteligente
- **Búsqueda**: Top-k por similitud coseno

### Sistema Conversacional
- **Enfoque**: Respuestas contextuales sin modelos generativos problemáticos
- **Clasificación**: Detección automática de tipos de preguntas
- **Formato**: Respuestas estructuradas en Markdown
- **Dominio**: Filtrado inteligente de preguntas relevantes

### Interfaz Moderna
- **Framework**: Streamlit con diseño personalizado
- **Funciones**: Chat en tiempo real, preguntas frecuentes, exportación
- **Responsive**: Adaptable a diferentes dispositivos
- **Estadísticas**: Métricas del sistema en tiempo real

## 🛠️ Personalización y Extensión

### Modificar el alcance del scraping
```python
# En web_scraper.py
max_pages = 200  # Aumentar páginas a procesar
```

### Ajustar parámetros de búsqueda
```python
# En knowledge_base.py
chunk_size = 800  # Tamaño de chunks
n_results = 5     # Número de resultados relevantes
```

### Personalizar tipos de preguntas
```python
# En chatbot.py - agregar nuevas categorías
question_types = {
    "tu_categoria": ["palabra1", "palabra2", "palabra3"]
}
```

## 📊 Monitoreo y Estadísticas

El sistema proporciona estadísticas detalladas:

- **Scraping**: Páginas procesadas, PDFs extraídos, palabras totales
- **Base de conocimiento**: Número de chunks, embeddings generados
- **Chat**: Consultas procesadas, tipos de preguntas detectadas
- **Sistema**: Estado de componentes, tiempo de respuesta

## 🚨 Solución de Problemas

### Problema: Base de conocimiento vacía
```bash
# Solución: Regenerar datos
rm -rf chroma_db/ unex_content.json
python web_scraper.py
python knowledge_base.py
```

### Problema: Streamlit no inicia
```bash
# Verificar configuración
pip install --upgrade streamlit
streamlit config show
```

### Problema: Error de memoria
```bash
# Reducir parámetros en config.py
chunk_size = 500  # Reducir tamaño de chunks
max_pages = 50    # Reducir páginas a procesar
```

## 📦 Dependencias Principales

- **`transformers`**: Modelos de IA y tokenización
- **`sentence-transformers`**: Embeddings semánticos multilingües
- **`chromadb`**: Base de datos vectorial
- **`streamlit`**: Framework de interfaz web
- **`beautifulsoup4`**: Parsing de HTML
- **`PyPDF2`**: Procesamiento de documentos PDF
- **`requests`**: Cliente HTTP para scraping

## 🔄 Actualizaciones y Mantenimiento

### Actualizar contenido
```bash
# Ejecutar scraping periódicamente
python web_scraper.py
python knowledge_base.py
```

### Backup de datos
```bash
# Respaldar base de conocimiento
cp -r chroma_db/ chroma_db_backup/
cp unex_content.json unex_content_backup.json
```

## 🎯 Roadmap Futuro

- [ ] Integración con APIs oficiales de la UEx
- [ ] Soporte para más formatos de documentos (Word, Excel)
- [ ] Sistema de feedback de usuarios
- [ ] Métricas avanzadas de satisfacción
- [ ] Integración con sistemas de chat empresariales
- [ ] Modo offline completo

## 📄 Licencia

Este proyecto está desarrollado para fines educativos y de investigación relacionados con la Universidad de Extremadura.

---

**¡Disfruta explorando la Universidad de Extremadura con IA! 🎓✨**

Para soporte o preguntas sobre el desarrollo, consulta la documentación técnica en los archivos de código fuente.
