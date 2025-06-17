import json
import os
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import logging

class KnowledgeBase:
    def __init__(self, db_path: str = "./chroma_db"):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(
            name="unex_content",
            metadata={"description": "Universidad de Extremadura content"}
        )
        self.encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Divide el texto en chunks más pequeños para mejor recuperación"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Buscar el último punto o salto de línea antes del límite
            if end < len(text):
                last_sentence = text.rfind('.', start, end)
                last_newline = text.rfind('\n', start, end)
                
                if last_sentence > start:
                    end = last_sentence + 1
                elif last_newline > start:
                    end = last_newline
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap if end - overlap > start else end
        
        return chunks
    
    def add_documents(self, content_data: List[Dict]):
        """Añade documentos a la base de conocimiento"""
        documents = []
        metadatas = []
        ids = []
        
        for i, item in enumerate(content_data):
            if not item.get('content'):
                continue
                
            # Crear chunks del contenido
            chunks = self.chunk_text(item['content'])
            
            for j, chunk in enumerate(chunks):
                doc_id = f"doc_{i}_{j}"
                documents.append(chunk)
                metadatas.append({
                    'url': item['url'],
                    'title': item['title'],
                    'chunk_index': j,
                    'total_chunks': len(chunks)
                })
                ids.append(doc_id)
        
        self.logger.info(f"Adding {len(documents)} chunks to knowledge base")
        
        # Añadir en lotes para evitar problemas de memoria
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_metadata = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            self.collection.add(
                documents=batch_docs,
                metadatas=batch_metadata,
                ids=batch_ids
            )
        
        self.logger.info("Documents added successfully")
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """Busca contenido relevante basado en la consulta"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i],
                    'score': results['distances'][0][i] if results['distances'] else None
                })
        
        return formatted_results
    
    def load_from_json(self, json_file: str):
        """Carga datos desde un archivo JSON y los añade a la base de conocimiento"""
        if not os.path.exists(json_file):
            self.logger.error(f"File {json_file} not found")
            return
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Verificar si el archivo tiene el formato nuevo con metadatos
        if isinstance(data, dict) and 'content' in data:
            content_data = data['content']
            self.logger.info(f"Loading enhanced data format with {data.get('scraping_stats', {}).get('total_pages', len(content_data))} pages")
        else:
            # Formato antiguo
            content_data = data
        
        self.add_documents(content_data)
        self.logger.info(f"Knowledge base updated with data from {json_file}")

if __name__ == "__main__":
    kb = KnowledgeBase()
    
    # Buscar archivos de datos disponibles
    files_to_try = [
        "unex_content_enhanced.json",
        "unex_content.json"
    ]
    
    file_found = False
    for json_file in files_to_try:
        if os.path.exists(json_file):
            print(f"Encontrado archivo: {json_file}")
            kb.load_from_json(json_file)
            file_found = True
            break
    
    if not file_found:
        print("No se encontró ningún archivo de datos. Ejecuta primero web_scraper.py o web_scraper_new.py")
    else:
        # Prueba de búsqueda
        results = kb.search("¿Qué estudios se pueden hacer en la UEx?", n_results=3)
        for i, result in enumerate(results):
            print(f"\n--- Resultado {i+1} ---")
            print(f"URL: {result['metadata']['url']}")
            print(f"Contenido: {result['content'][:200]}...")
