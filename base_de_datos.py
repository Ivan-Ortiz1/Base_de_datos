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
url_base = "http://books.toscrape.com/catalogue/page-{}.html"
headers = {"User-Agent": "Mozilla/5.0"}
cache_autores = {}

# --- Conectar a la base de datos ---
conn = sqlite3.connect("libros.db")
cursor = conn.cursor()

# --- Crear tablas ---
cursor.executescript(
    """
CREATE TABLE IF NOT EXISTS autores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS generos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS libros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT,
    precio TEXT,
    stock TEXT,
    url TEXT,
    rating TEXT,
    genero_id INTEGER,
    FOREIGN KEY (genero_id) REFERENCES generos(id)
);

CREATE TABLE IF NOT EXISTS autor_libro (
    autor_id INTEGER,
    libro_id INTEGER,
    PRIMARY KEY (autor_id, libro_id),
    FOREIGN KEY (autor_id) REFERENCES autores(id),
    FOREIGN KEY (libro_id) REFERENCES libros(id)
);
"""
)


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
    url_libro = "http://books.toscrape.com/catalogue/" + url_relativa.lstrip("./")

    try:
        detalle = requests.get(url_libro, headers=headers, timeout=10)
        detalle.raise_for_status()
        soup = BeautifulSoup(detalle.text, "html.parser")

        # Género
        breadcrumb = soup.select("ul.breadcrumb li a")
        genero = breadcrumb[2].text if len(breadcrumb) >= 3 else "Desconocido"

        # Stock
        tabla = soup.find("table", class_="table table-striped")
        stock = (
            tabla.find_all("tr")[5].find("td").text.strip() if tabla else "Sin stock"
        )

    except Exception:
        genero = "Desconocido"
        stock = "Sin stock"

    return genero, stock, url_libro


def obtener_total_paginas():
    try:
        response = requests.get(url_base.format(1), headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        texto_paginacion = soup.select_one("li.current")
        if texto_paginacion:
            texto = texto_paginacion.text.strip()
            partes = texto.split("of")
            if len(partes) == 2:
                return int(partes[1].strip())
    except Exception as e:
        print("⚠️ Error al obtener total de páginas:", e)
    return 1  # En caso de fallo, por defecto 1


def obtener_libros_por_rating(rating_objetivo="One", paginas=5):
    libros = []

    for pagina in range(1, paginas + 1):
        url = url_base.format(pagina)
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"[!] Error en la página {pagina}:", e)
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        articulos = soup.find_all("article", class_="product_pod")

        for libro in articulos:
            rating = libro.find("p", class_="star-rating")["class"][1]
            if rating == rating_objetivo:
                titulo = libro.h3.a["title"]
                precio = libro.find("p", class_="price_color").text
                url_relativa = libro.h3.a["href"]

                genero, stock, url_completo = obtener_detalle_libro(url_relativa)
                autor = buscar_autor_google_books(titulo)

                libros.append(
                    (autor, titulo, precio, genero, stock, url_completo, rating)
                )

    return libros


def obtener_o_insertar_id(nombre, tabla):
    cursor.execute(f"SELECT id FROM {tabla} WHERE nombre = ?", (nombre,))
    resultado = cursor.fetchone()
    if resultado:
        return resultado[0]
    cursor.execute(f"INSERT INTO {tabla} (nombre) VALUES (?)", (nombre,))
    return cursor.lastrowid


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

    conn.commit()


def imprimir_libros(lista, descripcion):
    if lista:
        print(f"\n{descripcion}\n")
        for autor, titulo, precio, genero, stock, link, rating in lista:
            print(
                f"Autor: {autor}\nTítulo: {titulo}\nPrecio: {precio}\nGénero: {genero}\nStock: {stock}\nRating: {rating}\nLink: {link}\n"
            )
    else:
        print(f"¡No se encontraron {descripcion.lower()}!")


# --- Scraping e inserción ---
libros_1 = obtener_libros_por_rating("One", paginas=obtener_total_paginas)
libros_3 = obtener_libros_por_rating("Three", paginas=obtener_total_paginas)
libros_5 = obtener_libros_por_rating("Five", paginas=obtener_total_paginas)

imprimir_libros(libros_1, "Libros con rating de 1 estrella encontrados:")
imprimir_libros(libros_3, "Libros con rating de 3 estrellas encontrados:")
imprimir_libros(libros_5, "Libros con rating de 5 estrellas encontrados:")

for libro in libros_1 + libros_3 + libros_5:
    insertar_libro(*libro)

print("\n✅ Libros insertados correctamente en la base de datos.")
