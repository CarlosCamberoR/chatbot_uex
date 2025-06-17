import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, urlparse, quote
from typing import List, Set, Dict, Optional
import json
import re
import tempfile
import os
from pathlib import Path
import fitz  # PyMuPDF - mejor que PyPDF2
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

class EnhancedWebScraper:
    def __init__(self, base_url: str = "https://www.unex.es/", max_pages: int = 200):
        self.base_url = base_url
        self.max_pages = max_pages
        self.visited_urls: Set[str] = set()
        self.visited_pdfs: Set[str] = set()
        self.content_data: List[dict] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # URLs importantes de la UEx
        self.priority_urls = [
            "https://www.unex.es/",
            "https://www.unex.es/conoce-la-uex",
            "https://www.unex.es/organizacion",
            "https://www.unex.es/alumnado",
            "https://www.unex.es/noticias",
            "https://alumnado.unex.es/pau/",
            "https://alumnado.unex.es/matricula-grados/",
            "https://alumnado.unex.es/grados/",
            "https://www.unex.es/estudiar-en-la-uex/estudios/",
            "https://comunicacion.unex.es/",
            "https://www.unex.es/organizacion/centros-departamentos",
            "https://www.unex.es/organizacion/servicios",
            "https://sede.unex.es/",
            "https://biblioteca.unex.es/",
            "https://www.unex.es/investigacion",
            "https://transferencia.unex.es/",
            "https://internacional.unex.es/"
        ]
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Estadísticas
        self.pdf_count = 0
        self.html_count = 0
        self.total_words = 0
        
        # Patrones para detectar PDFs
        self.pdf_patterns = [
            r'\.pdf$',
            r'\.pdf\?',
            r'filetype=pdf',
            r'type=pdf',
            r'formato=pdf',
            r'download.*\.pdf'
        ]
        
        # Elementos HTML a ignorar completamente
        self.ignore_elements = [
            'script', 'style', 'nav', 'footer', 'header', 'aside',
            'iframe', 'noscript', 'meta', 'link', 'title'
        ]
        
        # Clases/IDs a ignorar (comunes en sitios web universitarios)
        self.ignore_classes = [
            'menu', 'sidebar', 'navigation', 'breadcrumb', 'footer',
            'header', 'banner', 'advertisement', 'social', 'share',
            'related', 'comments', 'widget', 'plugin'
        ]

    def is_valid_unex_url(self, url: str) -> bool:
        """Verifica si la URL pertenece al dominio de la UEx"""
        try:
            parsed = urlparse(url)
            return 'unex.es' in parsed.netloc and url.startswith(('http://', 'https://'))
        except:
            return False

    def is_pdf_url(self, url: str) -> bool:
        """Detecta si una URL apunta a un PDF usando múltiples patrones"""
        url_lower = url.lower()
        return any(re.search(pattern, url_lower) for pattern in self.pdf_patterns)

    def clean_text(self, text: str) -> str:
        """Limpia y normaliza el texto extraído de forma agresiva"""
        if not text:
            return ""
        
        # Remover caracteres de control y espacios extraños
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]', ' ', text)
        
        # Normalizar espacios en blanco
        text = re.sub(r'\s+', ' ', text)
        
        # Remover líneas que son solo puntuación o caracteres especiales
        lines = text.split('\n')
        clean_lines = []
        for line in lines:
            line = line.strip()
            if len(line) > 3 and not re.match(r'^[^\w\s]*$', line):
                clean_lines.append(line)
        
        return ' '.join(clean_lines).strip()

    def extract_text_from_html(self, soup: BeautifulSoup) -> str:
        """Extrae texto limpio de HTML ignorando elementos no deseados"""
        # Remover elementos completos
        for element in soup(self.ignore_elements):
            element.decompose()
        
        # Remover elementos con clases/IDs específicos
        for class_name in self.ignore_classes:
            for element in soup.find_all(attrs={'class': re.compile(class_name, re.I)}):
                element.decompose()
            for element in soup.find_all(attrs={'id': re.compile(class_name, re.I)}):
                element.decompose()
        
        # Buscar contenido principal en orden de prioridad
        content_selectors = [
            'main',
            '.main-content',
            '.content',
            '.post-content',
            '.entry-content',
            'article',
            '.article-content',
            '#content',
            '.page-content',
            '.text-content',
            '.body-content'
        ]
        
        main_content = ""
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                main_content = content_elem.get_text(separator=' ', strip=True)
                break
        
        # Si no encuentra contenido específico, usar el body filtrado
        if not main_content:
            body = soup.find('body')
            if body:
                main_content = body.get_text(separator=' ', strip=True)
        
        return self.clean_text(main_content)

    def find_all_pdf_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Encuentra todos los enlaces a PDFs en una página de forma exhaustiva"""
        pdf_links = set()
        
        # Buscar en enlaces directos
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href:
                full_url = urljoin(base_url, href)
                if self.is_pdf_url(full_url) and self.is_valid_unex_url(full_url):
                    pdf_links.add(full_url)
        
        # Buscar en atributos src de objetos y embeds
        for element in soup.find_all(['object', 'embed'], src=True):
            src = element['src']
            if src:
                full_url = urljoin(base_url, src)
                if self.is_pdf_url(full_url) and self.is_valid_unex_url(full_url):
                    pdf_links.add(full_url)
        
        # Buscar en iframes que puedan contener PDFs
        for iframe in soup.find_all('iframe', src=True):
            src = iframe['src']
            if src:
                full_url = urljoin(base_url, src)
                if self.is_pdf_url(full_url) and self.is_valid_unex_url(full_url):
                    pdf_links.add(full_url)
        
        # Buscar patrones de PDF en el texto y atributos onclick
        text_content = soup.get_text()
        pdf_matches = re.findall(r'https?://[^\s<>"]+\.pdf[^\s<>"]*', text_content, re.IGNORECASE)
        for match in pdf_matches:
            if self.is_valid_unex_url(match):
                pdf_links.add(match)
        
        return list(pdf_links)

    def extract_pdf_content(self, url: str) -> Optional[dict]:
        """Extrae contenido de un archivo PDF usando PyMuPDF"""
        try:
            self.logger.info(f"📄 Procesando PDF: {url}")
            
            # Verificar si ya procesamos este PDF
            url_hash = hashlib.md5(url.encode()).hexdigest()
            if url_hash in self.visited_pdfs:
                return None
            self.visited_pdfs.add(url_hash)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Verificar que el contenido es realmente un PDF
            if not response.content.startswith(b'%PDF'):
                self.logger.warning(f"El archivo no parece ser un PDF válido: {url}")
                return None
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            try:
                # Extraer texto usando PyMuPDF
                doc = fitz.open(temp_file_path)
                text_content = ""
                
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    text_content += page.get_text() + "\n"
                
                doc.close()
                
                # Limpiar texto
                cleaned_text = self.clean_text(text_content)
                
                if len(cleaned_text) > 50:  # Contenido mínimo
                    self.pdf_count += 1
                    word_count = len(cleaned_text.split())
                    self.total_words += word_count
                    
                    return {
                        'url': url,
                        'title': f"PDF - {Path(urlparse(url).path).name}",
                        'content': cleaned_text,
                        'content_type': 'pdf',
                        'word_count': word_count,
                        'pages': len(doc) if 'doc' in locals() else 0,
                        'scraped_at': time.time()
                    }
                    
            finally:
                # Limpiar archivo temporal
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            self.logger.error(f"❌ Error procesando PDF {url}: {str(e)}")
        
        return None

    def extract_html_content(self, url: str) -> Optional[dict]:
        """Extrae contenido de una página HTML"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraer título
            title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else ""
            
            # Extraer contenido de texto limpio
            text_content = self.extract_text_from_html(soup)
            
            # Buscar todos los PDFs en la página
            pdf_links = self.find_all_pdf_links(soup, url)
            
            # Encontrar enlaces internos para continuar el crawling
            internal_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href:
                    full_url = urljoin(url, href)
                    if (self.is_valid_unex_url(full_url) and 
                        not self.is_pdf_url(full_url) and 
                        full_url not in self.visited_urls):
                        internal_links.append(full_url)
            
            # Solo guardar si tiene contenido significativo
            if len(text_content) < 100:
                return {
                    'url': url,
                    'title': title,
                    'content': "",
                    'content_type': 'html',
                    'internal_links': internal_links[:15],  # Limitar enlaces
                    'pdf_links': pdf_links,
                    'word_count': 0,
                    'scraped_at': time.time()
                }
            
            self.html_count += 1
            word_count = len(text_content.split())
            self.total_words += word_count
            
            return {
                'url': url,
                'title': title,
                'content': text_content,
                'content_type': 'html',
                'internal_links': internal_links[:15],  # Limitar para no saturar
                'pdf_links': pdf_links,
                'word_count': word_count,
                'scraped_at': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error procesando HTML {url}: {str(e)}")
            return None

    def process_single_url(self, url: str) -> Optional[dict]:
        """Procesa una URL única (HTML o PDF)"""
        if url in self.visited_urls:
            return None
            
        self.visited_urls.add(url)
        
        if self.is_pdf_url(url):
            return self.extract_pdf_content(url)
        else:
            return self.extract_html_content(url)

    def scrape_website(self) -> List[dict]:
        """Ejecuta el scraping completo del sitio web con procesamiento paralelo de PDFs"""
        urls_to_visit = self.priority_urls.copy()
        pdf_queue = []
        
        self.logger.info(f"🚀 Iniciando scraping de {self.max_pages} páginas máximo")
        
        while urls_to_visit and len(self.visited_urls) < self.max_pages:
            current_url = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
            
            progress = len(self.visited_urls) + 1
            self.logger.info(f"🔍 ({progress}/{self.max_pages}) Procesando: {current_url}")
            
            content = self.process_single_url(current_url)
            
            if content:
                self.content_data.append(content)
                
                # Agregar PDFs encontrados a la cola
                if 'pdf_links' in content and content['pdf_links']:
                    for pdf_url in content['pdf_links']:
                        if pdf_url not in [item['url'] for item in self.content_data]:
                            pdf_queue.append(pdf_url)
                    
                    self.logger.info(f"📎 Encontrados {len(content['pdf_links'])} PDFs en la página")
                
                # Agregar enlaces internos a la cola
                if 'internal_links' in content:
                    for link in content['internal_links']:
                        if link not in self.visited_urls and len(urls_to_visit) < 100:
                            urls_to_visit.append(link)
            
            # Pausa breve
            time.sleep(0.3)
        
        # Procesar PDFs encontrados
        if pdf_queue:
            self.logger.info(f"📚 Procesando {len(pdf_queue)} PDFs encontrados...")
            
            # Procesar PDFs con paralelización limitada
            with ThreadPoolExecutor(max_workers=3) as executor:
                pdf_futures = {executor.submit(self.extract_pdf_content, pdf_url): pdf_url 
                              for pdf_url in pdf_queue[:50]}  # Limitar PDFs
                
                for future in as_completed(pdf_futures):
                    pdf_content = future.result()
                    if pdf_content:
                        self.content_data.append(pdf_content)
        
        # Mostrar estadísticas finales
        self.print_statistics()
        return self.content_data

    def print_statistics(self):
        """Muestra estadísticas detalladas del scraping"""
        total_pages = len(self.content_data)
        avg_words = self.total_words // total_pages if total_pages > 0 else 0
        
        print("\n" + "="*60)
        print("📊 ESTADÍSTICAS DEL SCRAPING COMPLETADO")
        print("="*60)
        print(f"📄 Total páginas procesadas: {total_pages}")
        print(f"🌐 Páginas HTML: {self.html_count}")
        print(f"📋 Documentos PDF: {self.pdf_count}")
        print(f"📝 Total palabras extraídas: {self.total_words:,}")
        print(f"📊 Promedio palabras por página: {avg_words:,}")
        print(f"💾 URLs visitadas: {len(self.visited_urls)}")
        print("="*60)

    def save_data(self, filename: str = "unex_content_enhanced.json"):
        """Guarda los datos extraídos en un archivo JSON"""
        # Preparar metadatos
        metadata = {
            'scraping_stats': {
                'total_pages': len(self.content_data),
                'html_pages': self.html_count,
                'pdf_documents': self.pdf_count,
                'total_words': self.total_words,
                'scraped_at': time.time(),
                'urls_visited': len(self.visited_urls)
            },
            'content': self.content_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"💾 Datos guardados en {filename}")
        print(f"✅ Archivo guardado: {filename}")

if __name__ == "__main__":
    # Instalar dependencias necesarias si no están instaladas
    try:
        import fitz
    except ImportError:
        print("⚠️  PyMuPDF no está instalado. Instalando...")
        os.system("pip install PyMuPDF")
        import fitz
    
    scraper = EnhancedWebScraper(max_pages=200)
    content = scraper.scrape_website()
    scraper.save_data()
    
    print(f"\n🎉 Scraping completado exitosamente!")
    print(f"📄 {len(content)} páginas procesadas en total")
    print(f"📋 {scraper.pdf_count} documentos PDF extraídos")
    print(f"🌐 {scraper.html_count} páginas HTML procesadas")