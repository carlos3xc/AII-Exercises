import datetime
import locale
import os
from tkinter import END, Toplevel, Frame, TOP, Label, LEFT, Entry, Scrollbar, RIGHT, Y, Listbox, BOTTOM, BOTH

from whoosh.fields import Schema, TEXT, ID, DATETIME, STORED, KEYWORD
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser

DIR_DOCS_1 = "hilos"
DIR_INDEX = "Index1"

DIR_DOCS_2 = "respuestas"
DIR_INDEX_2 = "Index2"


# Schemas
# Titulo, fecha_inicio, fecha_fin, descripcion, categoria(s)
def get_schema():
    return Schema(titulo=TEXT(stored=True),
                  fecha_inicio=DATETIME(stored=True),
                  fecha_fin=DATETIME(stored=True),
                  descripcion=TEXT(stored=True),
                  categorias=KEYWORD(stored=True, commas=True, scorable=True))

# Add methods
def add_doc(writer, evento: dict):
    writer.add_document(titulo=evento['titulo'], fecha_inicio=evento['fecha_inicio'], fecha_fin=evento['fecha_fin'], descripcion=evento['descripcion'], categorias=evento['categorias'])


# Search methods
def search_by_title_and_desc():
    def mostrar_lista(event):
        lb.delete(0, END)  # borra toda la lista
        ix = open_dir(DIR_INDEX)
        parameters = en.get().split()

        with ix.searcher() as searcher:
            #query = parameters
            for p in parameters:
                query = f'{query} descripcion:{p.strip()}'
                # Comprobar que se parsea correctamente
                query = QueryParser('titulo', ix.schema).parse(query)

            results = searcher.search(query)
            for r in results:
                lb.insert(END, f"Título: {r['titulo']}")
                lb.insert(END, f"Rango de fechas: {r['fecha_inicio']} - {r['fecha_fin']}")
                lb.insert(END, '')

    v = Toplevel()
    v.title("Busqueda en el título y la descripción")
    f = Frame(v)
    f.pack(side=TOP)
    l = Label(f, text="Introduzca una o varias palabras:")
    l.pack(side=LEFT)
    en = Entry(f)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, yscrollcommand=sc.set)
    lb.pack(side=BOTTOM, fill=BOTH)
    sc.config(command=lb.yview)


def search_by_fecha():
    def mostrar_lista(event):
        lb.delete(0, END)  # borra toda la lista
        ix = open_dir(DIR_INDEX)
        locale.setlocale(locale.LC_ALL, 'es_ES')
        parameter = str(en.get())
        fecha_parameter = datetime.strptime(parameter, '%d de %B de %Y').strftime('%Y%m%d')
        fecha_past = (datetime.now() - datetime.timedelta(years=50)).strftime('%Y%m%d')

        with ix.searcher() as searcher:
            query = QueryParser("fecha", ix.schema).parse(f"[{fecha_past} to {fecha_parameter}]")
            results = searcher.search(query)
            for r in results:
                lb.insert(END, f"Título: {r['titulo']}")
                lb.insert(END, f"Rango de fechas: {r['fecha_inicio']} - {r['fecha_fin']}")
                lb.insert(END, '')

    v = Toplevel()
    v.title("Búsqueda por fecha")
    f = Frame(v)
    f.pack(side=TOP)
    l = Label(f, text="Introduzca una fecha en formato DD de MMM de YYYY:")
    l.pack(side=LEFT)
    en = Entry(f)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, yscrollcommand=sc.set)
    lb.pack(side=BOTTOM, fill=BOTH)
    sc.config(command=lb.yview)


def search_by_response():
    def mostrar_lista(event):
        lb.delete(0, END)  # borra toda la lista
        ix2 = open_dir(DIR_INDEX_2)
        parameter = str(en.get())

        ix1 = open_dir(DIR_INDEX_1)

        with ix2.searcher() as searcher2:
            query2 = QueryParser("texto", ix2.schema).parse(parameter)
            results = searcher2.search(query2, limit=None)
            for r in results:
                link_url = r['link_tema']
                with ix1.searcher() as searcher1:
                    query1 = QueryParser("link", ix1.schema).parse(f'{link_url}')
                    temas = searcher1.search(query1)

                    lb.insert(END, f"Título del tema: {temas[0]['titulo']}")
                    lb.insert(END, f"Autor: {r['autor']}")
                    lb.insert(END, f"Fecha: {r['fecha']}")
                    lb.insert(END, f"Texto: {r['texto']}")
                    lb.insert(END, f"Link: {r['link_tema']}")
                    lb.insert(END, '')

    v = Toplevel()
    v.title("Búsqueda por respuesta")
    f = Frame(v)
    f.pack(side=TOP)
    l = Label(f, text="Introduzca un término:")
    l.pack(side=LEFT)
    en = Entry(f)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, yscrollcommand=sc.set)
    lb.pack(side=BOTTOM, fill=BOTH)
    sc.config(command=lb.yview)


# Se integra con el load_data del scraping
def create_index():
    if not os.path.exists(DIR_INDEX_1):
        os.mkdir(DIR_INDEX_1)

    if not os.path.exists(DIR_INDEX_2):
        os.mkdir(DIR_INDEX_2)

    ix1 = create_in(DIR_INDEX_1, schema=get_thread_schema())
    writer1 = ix1.writer()

    ix2 = create_in(DIR_INDEX_2, schema=get_response_schema())
    writer2 = ix2.writer()

    j = 0


create_index()
