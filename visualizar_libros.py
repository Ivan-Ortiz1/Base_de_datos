import sqlite3
import csv
import os


def exportar_a_csv(libros):
    nombre_archivo = "libros_filtrados.csv"
    with open(nombre_archivo, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["Título", "Precio", "Stock", "Rating", "URL", "Género", "Autor(es)"]
        )
        for libro in libros:
            writer.writerow(libro)
    print(
        f"✅ Resultados exportados correctamente a '{os.path.abspath(nombre_archivo)}'"
    )


def conectar_db():
    return sqlite3.connect("libros.db")


def mostrar_menu():
    print("\n=== FILTROS DISPONIBLES ===")
    print("1. Filtrar por rating")
    print("2. Filtrar por precio máximo")
    print("3. Filtrar por género")
    print("4. Filtrar por autor")
    print("5. Filtrar por disponibilidad")
    print("6. Ver todos los libros")
    print("0. Salir")


def construir_query(opcion):
    query_base = """
    SELECT libros.titulo, libros.precio, libros.stock, libros.rating,
           libros.url, generos.nombre AS genero, GROUP_CONCAT(autores.nombre, ', ') AS autores
    FROM libros
    JOIN generos ON libros.genero_id = generos.id
    JOIN autor_libro ON libros.id = autor_libro.libro_id
    JOIN autores ON autores.id = autor_libro.autor_id
    """
    condiciones = []
    parametros = []

    if opcion == "1":
        while True:
            rating = input("⭐ Ingrese rating (1-5): ").strip()
            if rating.isdigit() and 1 <= int(rating) <= 5:
                break
            print("❌ Rating inválido. Debe ser un número del 1 al 5.")
        condiciones.append("libros.rating = ?")
        parametros.append(rating)

    elif opcion == "2":
        while True:
            precio_max = input("💰 Ingrese precio máximo (sin símbolo): ").strip()
            try:
                float(precio_max)
                break
            except ValueError:
                print("❌ Ingrese un número válido.")
        condiciones.append("CAST(SUBSTR(libros.precio, 2) AS REAL) <= ?")
        parametros.append(precio_max)

    elif opcion == "3":
        genero = input("📚 Ingrese nombre del género: ").strip()
        condiciones.append("generos.nombre LIKE ?")
        parametros.append(f"%{genero}%")

    elif opcion == "4":
        autor = input("👨‍💼 Ingrese nombre del autor: ").strip()
        condiciones.append("autores.nombre LIKE ?")
        parametros.append(f"%{autor}%")

    elif opcion == "5":
        condiciones.append("libros.stock NOT LIKE '%(0 available)%'")

    where_clause = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    query = f"""
    {query_base}
    {where_clause}
    GROUP BY libros.id
    ORDER BY libros.titulo;
    """
    return query, parametros


def mostrar_resultados(cursor):
    libros = cursor.fetchall()
    if not libros:
        print("\n📭 No se encontraron libros con ese filtro.")
        return

    print(f"\n📚 Resultados encontrados: {len(libros)}\n")
    for libro in libros:
        titulo, precio, stock, rating, url, genero, autores = libro
        print(
            f"📖 Título: {titulo}\n💵 Precio: {precio}\n📦 Stock: {stock}\n⭐ Rating: {rating}"
        )
        print(
            f"🎭 Género: {genero}\n👨‍💼 Autor(es): {autores}\n🔗 Link: {url}\n{'-'*40}"
        )

    exportar = (
        input("\n💾 ¿Desea exportar estos resultados a CSV? (s/n): ").strip().lower()
    )
    if exportar == "s":
        exportar_a_csv(libros)


def main():
    conn = conectar_db()
    cursor = conn.cursor()

    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "0":
            print("👋 Saliendo del visor...")
            break
        elif opcion in {"1", "2", "3", "4", "5"}:
            query, params = construir_query(opcion)
            cursor.execute(query, params)
            mostrar_resultados(cursor)
        elif opcion == "6":
            query, params = construir_query("6")  # sin filtros
            cursor.execute(query)
            mostrar_resultados(cursor)
        else:
            print("❌ Opción no válida. Intente nuevamente.")

    conn.close()


if __name__ == "__main__":
    main()
