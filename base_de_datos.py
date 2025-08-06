import os
import time
import requests
import sqlite3
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- Cargar variables de entorno ---
load_dotenv()
API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")

# --- Variables ---
BASE_URL = "http://books.toscrape.com/"
CATALOGUE_URL = BASE_URL + "catalogue/"
headers = {"User-Agent": "Mozilla/5.0"}
cache_autores = {}

# --- Conectar a la base de datos ---
conn = sqlite3.connect("libros.db")
cursor = conn.cursor()

# --- Crear tablas ---
cursor.executescript(
    """
CREATE TABLE IF NOT EXISTS autores (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    nombre TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS generos (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    nombre TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS libros (
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    titulo TEXT NOT NULL,
    precio TEXT NOT NULL,
    stock TEXT NOT NULL,
    url TEXT NOT NULL,
    rating INTEGER NOT NULL,
    genero_id INTEGER NOT NULL,
    FOREIGN KEY (genero_id) REFERENCES generos(id)
);

CREATE TABLE IF NOT EXISTS autor_libro (
    autor_id INTEGER NOT NULL,
    libro_id INTEGER NOT NULL,
    PRIMARY KEY (autor_id, libro_id),
    FOREIGN KEY (autor_id) REFERENCES autores(id),
    FOREIGN KEY (libro_id) REFERENCES libros(id)
);
"""
)

RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


# --- Funciones ---
def buscar_autor_google_books(titulo):
    if titulo in cache_autores:
        return cache_autores[titulo]

    url = "https://www.googleapis.com/books/v1/volumes"
    params = {"q": f"intitle:{titulo}", "key": API_KEY, "maxResults": 1}

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        if "items" in data:
            volumen = data["items"][0]["volumeInfo"]
            autores = volumen.get("authors", ["Desconocido"])
            autor = ", ".join(autores)
        else:
            autor = "No encontrado"
    except Exception:
        autor = "Error API"

    cache_autores[titulo] = autor
    time.sleep(1)
    return autor


def obtener_detalle_libro(url_relativa):
    url_libro = CATALOGUE_URL + url_relativa.lstrip("./")

    try:
        detalle = requests.get(url_libro, headers=headers, timeout=5)
        detalle.raise_for_status()
        soup = BeautifulSoup(detalle.text, "html.parser")

        # Género
        breadcrumb = soup.select("ul.breadcrumb li a")
        genero = breadcrumb[2].text.strip() if len(breadcrumb) >= 3 else "Desconocido"

        # Stock
        tabla = soup.find("table", class_="table table-striped")
        stock = (
            tabla.find_all("tr")[5].find("td").text.strip() if tabla else "Sin stock"
        )
    except Exception:
        genero = "Desconocido"
        stock = "Sin stock"

    return genero, stock, url_libro


def obtener_o_insertar_id(nombre, tabla):
    cursor.execute(f"SELECT id FROM {tabla} WHERE nombre = ?", (nombre,))
    resultado = cursor.fetchone() #averiguar
    if resultado:
        return resultado[0]
    cursor.execute(f"INSERT INTO {tabla} (nombre) VALUES (?)", (nombre,))
    return cursor.lastrowid # averiguar


def insertar_libro(autor_str, titulo, precio, genero_str, stock, url, rating):
    cursor.execute("SELECT id FROM libros WHERE titulo = ? AND url = ?", (titulo, url))
    if cursor.fetchone():
        print(f"🔁 Libro duplicado ignorado: {titulo}")
        return

    genero_id = obtener_o_insertar_id(genero_str, "generos")

    cursor.execute(
        """
        INSERT INTO libros (titulo, precio, stock, url, rating, genero_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
        (titulo, precio, stock, url, rating, genero_id),
    )
    libro_id = cursor.lastrowid

    for nombre_autor in [a.strip() for a in autor_str.split(",")]:
        autor_id = obtener_o_insertar_id(nombre_autor, "autores")
        cursor.execute(
            """
            INSERT OR IGNORE INTO autor_libro (autor_id, libro_id)
            VALUES (?, ?)
        """,
            (autor_id, libro_id),
        )

    conn.commit() #commit
    print(f"✅ Insertado: {titulo}")


def obtener_categorias():
    categorias = {}
    try:
        response = requests.get(BASE_URL, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        links = soup.select("div.side_categories ul li ul li a")
        for link in links:
            nombre = link.text.strip() # es necesario
            href = link.get("href").replace("index.html", "") # replace
            categorias[nombre] = BASE_URL + href
    except Exception as e:
        print("⚠️ Error al obtener categorías:", e)
    return categorias


def obtener_libros_de_categoria(nombre_categoria, url_categoria):
    libros = []
    pagina = 1

    while True:
        url_pagina = (
            url_categoria + f"page-{pagina}.html"
            if pagina > 1
            else url_categoria + "index.html"
        )
        try:
            response = requests.get(url_pagina, headers=headers, timeout=10)
            if response.status_code == 404:
                break
            response.raise_for_status()
        except Exception as e:
            print(f"[!] Error en {nombre_categoria}, página {pagina}: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        articulos = soup.find_all("article", class_="product_pod")
        if not articulos:
            break

        for libro in articulos:
            rating_texto = libro.find("p", class_="star-rating")["class"][1] #"class" y _
            rating_numero = RATING_MAP.get(rating_texto, 0)
            titulo = libro.h3.a["title"]
            precio = libro.find("p", class_="price_color").text.replace("Â", "")
            url_relativa = libro.h3.a["href"]

            genero, stock, url_completo = obtener_detalle_libro(url_relativa)
            autor = buscar_autor_google_books(titulo)

            libros.append(
                (autor, titulo, precio, genero, stock, url_completo, rating_numero)
            )

        pagina += 1

    return libros


# --- Ejecución principal ---
categorias = obtener_categorias()

for nombre, url_categoria in categorias.items():
    print(f"\n📚 Categoría: {nombre}")
    libros = obtener_libros_de_categoria(nombre, url_categoria)
    for libro in libros:
        insertar_libro(*libro)

print("\n✅ Todos los libros insertados correctamente.")
