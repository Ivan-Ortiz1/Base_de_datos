# 📚 Scraper de Libros desde books.toscrape.com

---

## 📑 Índice

- [📄 Descripción del Proyecto]
- [🚧 Estado del Proyecto]
- [🎬 Demostración de funciones]
- [🔐 Acceso al Proyecto]
- [🛠️ Tecnologías Utilizadas]
- [👨‍💻 Persona Desarrolladora]

---

## 📄 Descripción del Proyecto

Este proyecto realiza scraping del sitio [books.toscrape.com](http://books.toscrape.com/) para extraer y almacenar información relevante sobre libros en una base de datos SQLite3 estructurada y relacional. Se procesan campos como:

- Título
- Precio (formato corregido en £)
- Rating (convertido de texto a número entero)
- Autor (opcionalmente usando Google Books API)
- Género
- Stock

Los datos se almacenan en tablas relacionales normalizadas: `libros`, `autores`, `generos` y `autor_libro`.

También incluye un script adicional para consultar y filtrar los libros por consola.

---

## 🚧 Estado del Proyecto

✅ Funcionalidad básica completa  
✅ Inserción en SQLite3 con relaciones  
✅ Visualización desde consola con filtros  
✅ Conversión de rating textual a entero  
✅ Limpieza de caracteres mal codificados (ej: "Â£" → "£")  
🚧 Posible mejora: scrapear todas las páginas en una sola ejecución  
🚧 Futuras mejoras: visualización gráfica, exportación a CSV, interfaz web  

---

## 🎬 Demostración de funciones

$ python base_de_datos.py
➤ Inserta libros con rating 'Five'
➤ Evita duplicados
➤ Utiliza la API de Google Books si hay clave en .env

$ python visualizar_libros.py
➤ Lista todos los libros
➤ Filtro por:
   - Género
   - Autor
   - Rating
   - Precio máximo
   - Disponibilidad
📌 Ejemplo de salida filtrada:

Título: It's Only the Himalayas
Autor: S. Bedford
Género: Travel
Precio: £45.17
Rating: 2
En stock: Sí

🔐 Acceso al Proyecto
Clona el repositorio y ejecuta los scripts:

git clone https://github.com/tu-usuario/scraper-libros.git
cd scraper-libros
python base_de_datos.py
python visualizar_libros.py
🔑 Si deseas activar la búsqueda de autores por API, crea un archivo .env con este contenido:

GOOGLE_BOOKS_API_KEY=tu_clave_aquí

🛠️ Tecnologías Utilizadas
Python 3.10+

SQLite3

requests

BeautifulSoup4

dotenv

Google Books API (opcional)

📦 Para instalar dependencias:

pip install -r requirements.txt

(Si aún no lo creaste, puedes generarlo así:)

pip freeze > requirements.txt

👨‍💻 Persona Desarrolladora

Nombre	GitHub	País

Iván ✨	@Ivan-Ortiz1	🇵🇾 Paraguay

💡 Ideas futuras
Scrapear todas las páginas automáticamente

Exportar resultados a CSV o Excel

Agregar interfaz gráfica (Tkinter, PyQt o web)

Dashboard de estadísticas con filtros dinámicos

Agregar tests unitarios y CI/CD

🧠 Lecciones aprendidas
Limpieza y normalización de datos

Relaciones muchos a muchos en SQLite

Uso de variables de entorno con .env

Manejo de errores y validación de datos antes de insertar

Separación de responsabilidades en módulos (scraping, db, visualización)
