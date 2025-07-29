import requests
from bs4 import BeautifulSoup

url_base = "http://books.toscrape.com/catalogue/page-{}.html"
headers = {"User-Agent": "Mozilla/5.0"}


def obtener_detalle_libro(url_relativa):
    # Construir URL absoluta
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
                libros.append((titulo, precio, genero, stock, url_completo))

    return libros


def imprimir_libros(lista, descripcion):
    if lista:
        print(f"\n{descripcion}\n")
        for titulo, precio, genero, stock, link in lista:
            print(
                f"Titulo: {titulo} - Precio: {precio} - Género: {genero} - Stock: {stock}\nLink: {link}\n"
            )
    else:
        print(f"¡No se encontraron {descripcion.lower()}!")


# --- Ejecutar búsquedas ---
libros_1 = obtener_libros_por_rating("One", paginas=5)
libros_3 = obtener_libros_por_rating("Three", paginas=5)
libros_5 = obtener_libros_por_rating("Five", paginas=5)


# --- Imprimir resultados ---
imprimir_libros(libros_1, "Libros con rating de 1 estrella encontrados:")
imprimir_libros(libros_3, "Libros con rating de 3 estrellas encontrados:")
imprimir_libros(libros_5, "Libros con rating de 5 estrellas encontrados:")
