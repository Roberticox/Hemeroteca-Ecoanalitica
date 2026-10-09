import re
import urllib.request
from datetime import datetime
import feedparser
from jinja2 import Environment, FileSystemLoader

feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# =====================================================================
# TUS ENLACES DE GOOGLE ALERTS
# =====================================================================
ENLACES_GOOGLE_ALERTS = [
    "https://www.google.com/alerts/feeds/15160592940813757516/11333699515346653149",
    "https://www.google.com/alerts/feeds/15160592940813757516/3482806660395977425",
    "PEGAR_AQUI_NUEVA_ALERTA_3"
]

# =====================================================================
# FILTRO ESTRICTO Y GENERADOR DE SECCIONES AUTOMÁTICAS
# =====================================================================
PALABRAS_CLAVE = [
    "ecoanalítica", "alejandro grisanti", "Graciela Urdaneta", "banco central de venezuela",
    "economía", "inflación", "dólar", "dolarización"
]

FUENTES = [
    {
        "nombre": "Ecoanalítica Oficial",
        "categoria": "Publicaciones",
        "url": "https://news.google.com/rss/search?q=site:ecoanalitica.com&hl=es-419&gl=VE&ceid=VE:es-419"
    },
    {
        "nombre": "Banca y Negocios",
        "categoria": "Prensa Financiera",
        "url": "https://news.google.com/rss/search?q=site:bancaynegocios.com&hl=es-419&gl=VE&ceid=VE:es-419"
    }
]

for i, enlace in enumerate(ENLACES_GOOGLE_ALERTS):
    if "PEGAR_AQUI" not in enlace:
        FUENTES.append({
            "nombre": f"Google Alerts (Alerta {i+1})",
            "categoria": "Prensa y Menciones",
            "url": enlace
        })

def limpiar_texto(texto_html):
    if not texto_html:
        return ""
    patron_tags = re.compile(r"<[^>]+>")
    texto = patron_tags.sub("", texto_html).strip()
    texto = texto.replace("Banca y Negocios", "") 
    return texto

def compilar_hemeroteca():
    articulos_totales = []
    enlaces_procesados = set()

    print("Iniciando escaneo de artículos con filtro estricto...")

    for fuente in FUENTES:
        print(f"Consultando: {fuente['nombre']}...")
        
        try:
            req = urllib.request.Request(
                fuente["url"], 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                xml_data = response.read()
                
            feed = feedparser.parse(xml_data)
            
            for entry in feed.entries:
                titulo = limpiar_texto(entry.get("title", "Sin título"))
                resumen = limpiar_texto(entry.get("summary", ""))
                enlace = entry.get("link", "#")
                
                titulo = titulo.split(" - ")[0]
                texto_completo = f"{titulo} {resumen}".lower()
                
                # Buscamos qué palabras clave exactas contiene esta noticia
                palabras_encontradas = [palabra for palabra in PALABRAS_CLAVE if palabra in texto_completo]
                
                if not palabras_encontradas:
                    continue
                
                if enlace in enlaces_procesados:
                    continue
                enlaces_procesados.add(enlace)
                
                articulos_totales.append({
                    "fuente": fuente["nombre"],
                    "categoria": fuente["categoria"],
                    "titulo": titulo,
                    "resumen": resumen[:220] + "..." if len(resumen) > 220 else resumen,
                    "enlace": enlace,
                    "fecha": entry.get("published", datetime.now().strftime("%d/%m/%Y")),
                    # Guardamos las palabras encontradas separadas por comas para el HTML
                    "tags": ",".join(palabras_encontradas) 
                })
        except Exception as e:
            print(f" -> Error al consultar {fuente['nombre']}: {e}")
            continue

    entorno = Environment(loader=FileSystemLoader("."))
    plantilla = entorno.get_template("template.html")

    html_salida = plantilla.render(
        articulos=articulos_totales,
        palabras_clave=PALABRAS_CLAVE, # Enviamos la lista de palabras al HTML
        fecha_actualizacion=datetime.now().strftime("%d/%m/%Y %H:%M")
    )

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_salida)

    print(f"\n¡Éxito! Hemeroteca compilada. Se inyectaron {len(articulos_totales)} artículos estrictamente filtrados en index.html")

if __name__ == "__main__":
    compilar_hemeroteca()