import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, urlparse
from typing import List, Set
import json
import PyPDF2
import io
from pathlib import Path
import tempfile
import os

class WebScraper:
    def __init__(self, base_url: str = "https://www.unex.es/", max_pages: int = 150):
        self.base_url = base_url
        self.max_pages = max_pages
        self.visited_urls: Set[str] = set()
        self.content_data: List[dict] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # URLs importantes de la UEx que debemos incluir
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
            "https://comunicacion.unex.es/"
        ]
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Estadísticas
        self.pdf_count = 0
        self.html_count = 0
    
    def is_valid_unex_url(self, url: str) -> bool:
        """Verifica si la URL pertenece al dominio de la UEx"""
        parsed = urlparse(url)
        return 'unex.es' in parsed.netloc
    
    def clean_text(self, text: str) -> str:
        """Limpia y normaliza el texto extraído"""
        # Eliminar espacios múltiples y saltos de línea
        cleaned = ' '.join(text.split())
        return cleaned.strip()
    
    def is_pdf_url(self, url: str) -> bool:
        """Verifica si la URL apunta a un archivo PDF"""
        return url.lower().endswith('.pdf') or 'filetype=pdf' in url.lower()
    
    def extract_pdf_content(self, url: str) -> dict:
        """Extrae contenido de un archivo PDF"""
        try:
            self.logger.info(f"Descargando PDF: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(response.content)
                temp_file_path = temp_file.name
            
            try:
                # Extraer texto del PDF
                with open(temp_file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text_content = ""
                    
                    # Extraer texto de todas las páginas
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text_content += page.extract_text() + "\n"
                    
                    # Limpiar texto
                    cleaned_text = self.clean_text(text_content)
                    
                    if len(cleaned_text) > 100:  # Solo si tiene contenido suficiente
                        self.pdf_count += 1
                        return {
                            'url': url,
                            'title': f"PDF - {Path(url).name}",
                            'content': cleaned_text,
                            'content_type': 'pdf',
                            'word_count': len(cleaned_text.split())
                        }
                    
            finally:
                # Eliminar archivo temporal
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            self.logger.error(f"Error extrayendo PDF {url}: {str(e)}")
        
        return None
    
    def find_pdf_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Encuentra enlaces a PDFs en una página"""
        pdf_links = []
        
        # Buscar enlaces directos a PDFs
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href:
                full_url = urljoin(base_url, href)
                if self.is_pdf_url(full_url) and self.is_valid_unex_url(full_url):
                    pdf_links.append(full_url)
        
        return pdf_links
    
    def extract_content(self, url: str) -> dict:
        """Extrae contenido de una URL específica (HTML o PDF)"""
        try:
            # Verificar si es un PDF
            if self.is_pdf_url(url):
                return self.extract_pdf_content(url)
            
            # Procesar como HTML
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar PDFs en la página actual
            pdf_links = self.find_pdf_links(soup, url)
            
            # Eliminar scripts y estilos
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extraer título
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            # Extraer contenido principal
            main_content = ""
            
            # Buscar contenido en diferentes selectores comunes
            content_selectors = [
                'main', '.content', '.main-content', '.entry-content',
                'article', '.post-content', '#content', '.page-content',
                '.container', '.wrapper', '.site-content', '.primary',
                'section', '.section-content', '.text-content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    main_content = content_elem.get_text()
                    break
            
            # Si no encuentra contenido específico, toma el body pero filtra mejor
            if not main_content:
                body = soup.find('body')
                if body:
                    # Remover elementos no deseados
                    for unwanted in body.find_all(['nav', 'footer', 'header', 'aside', '.sidebar', '.menu']):
                        unwanted.decompose()
                    main_content = body.get_text()
            
            # Limpiar contenido
            main_content = self.clean_text(main_content)
            
            # Solo guardar si tiene contenido significativo
            if len(main_content) < 100:
                return None
            
            # Extraer enlaces internos (incluyendo PDFs)
            links = []
            for link in soup.find_all('a', href=True):
                full_url = urljoin(url, link['href'])
                if self.is_valid_unex_url(full_url) and full_url not in self.visited_urls:
                    links.append(full_url)
            
            # Añadir PDFs encontrados a los enlaces
            for pdf_url in pdf_links:
                if pdf_url not in self.visited_urls:
                    links.append(pdf_url)
            
            self.html_count += 1
            return {
                'url': url,
                'title': title_text,
                'content': main_content,
                'content_type': 'html',
                'links': links,
                'pdf_links': pdf_links,
                'word_count': len(main_content.split()),
                'scraped_at': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            return None
    
    def scrape_website(self) -> List[dict]:
        """Ejecuta el scraping completo del sitio web"""
        # Comenzar con URLs prioritarias
        urls_to_visit = self.priority_urls.copy()
        
        while urls_to_visit and len(self.visited_urls) < self.max_pages:
            current_url = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            self.logger.info(f"Scraping ({len(self.visited_urls)+1}/{self.max_pages}): {current_url}")
            self.visited_urls.add(current_url)
            
            content = self.extract_content(current_url)
            if content and content['content']:
                self.content_data.append(content)
                
                # Añadir nuevos enlaces a la cola (más enlaces por página)
                if 'links' in content:
                    for link in content['links'][:10]:  # Aumentar de 5 a 10
                        if link not in self.visited_urls and len(urls_to_visit) < 50:
                            urls_to_visit.append(link)
            
            # Pausa más corta para ser más eficiente
            time.sleep(0.5)
        
        # Mostrar estadísticas finales
        total_pages = len(self.content_data)
        total_words = sum([content.get('word_count', 0) for content in self.content_data])
        
        self.logger.info(f"=== SCRAPING COMPLETADO ===")
        self.logger.info(f"Total páginas procesadas: {total_pages}")
        self.logger.info(f"Páginas HTML: {self.html_count}")
        self.logger.info(f"Documentos PDF: {self.pdf_count}")
        self.logger.info(f"Total palabras extraídas: {total_words:,}")
        self.logger.info(f"Promedio palabras por página: {total_words//total_pages if total_pages > 0 else 0}")
        
        return self.content_data
    
    def save_data(self, filename: str = "unex_content.json"):
        """Guarda los datos extraídos en un archivo JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.content_data, f, ensure_ascii=False, indent=2)
        self.logger.info(f"Data saved to {filename}")

if __name__ == "__main__":
    scraper = WebScraper(max_pages=150)  # Aumentar a 150 páginas
    content = scraper.scrape_website()
    scraper.save_data()
    print(f"Scraping completado. {len(content)} páginas procesadas.")
