import locale
import os
import re
import urllib.request
import urllib.parse
from datetime import datetime
from tkinter import Tk, Menu, messagebox, END, Toplevel, Frame, TOP, Label, LEFT, Entry, Scrollbar, Y, RIGHT, Listbox, \
    BOTTOM, BOTH, Spinbox

from bs4 import BeautifulSoup
from whoosh.fields import Schema, TEXT, DATETIME, KEYWORD
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser

BASE_URL = 'https://www.sevilla.org/ayuntamiento/alcaldia/comunicacion/calendario/agenda-actividades'

DIR_DOCS = "eventos"
DIR_INDEX = "Index"


def get_schema():
    return Schema(titulo=TEXT(stored=True),
                  fecha_inicio=DATETIME(stored=True),
                  fecha_fin=DATETIME(stored=True),
                  descripcion=TEXT(stored=True),
                  categorias=KEYWORD(stored=True, commas=True, scorable=True))


def add_doc(writer, evento: dict):
    writer.add_document(titulo=evento['titulo'], fecha_inicio=evento['fecha_inicio'], fecha_fin=evento['fecha_fin'],
                        descripcion=evento['descripcion'],
                        categorias=evento['categorias'])


def open_url(url):
    cod_url = urllib.parse.quote(url, safe=':/?=')
    try:
        req = urllib.request.urlopen(cod_url)
        return req.read()
    except:
        print(f'----------Error---------- URL: {cod_url}')
        return None


def extract_data():
    raw_data = open_url(BASE_URL)
    if raw_data:
        soup = BeautifulSoup(raw_data, 'html.parser')
        eventos = soup.find('div', id='content').find_all('article', class_='vevent tileItem')
        return eventos


def extract_evento(n):
    titulo = n.find('span', class_='summary').text
    descripcion = str(n.p.text) if n.p is not None else 'Sin descripción'

    fecha_inicio = n.find('abbr', class_='dtstart')
    if fecha_inicio is None:
        fecha_inicio = [i for i in n.find('div', class_='documentByLine').stripped_strings][0]
        fecha_ini_form = datetime.strptime(fecha_inicio, '%d/%m/%Y')
    else:
        fecha_inicio = fecha_inicio['title'].strip()
        try:
            fecha_ini_form = datetime.strptime(fecha_inicio, '%Y-%m-%dT%H:%M:%S%z')
        except:
            fecha_ini_form = datetime.strptime(fecha_inicio, '%Y-%m-%d')

    fecha_fin = n.find('abbr', class_='dtend')
    if fecha_fin is None:
        fecha_fin = fecha_inicio
        fecha_fin_form = fecha_ini_form
    else:
        fecha_fin = fecha_fin['title'].strip()
        try:
            fecha_fin_form = datetime.strptime(fecha_fin, '%Y-%m-%dT%H:%M:%S%z')
        except:
            fecha_fin_form = datetime.strptime(fecha_fin, '%Y-%m-%d')

    categorias = n.find('li', class_='category')
    categorias_evento = []
    if categorias is not None:
        categorias = n.find('li', class_='category').find_all('span')
        for i in categorias:
            categorias_evento.append(i.text)

    categorias_string = ",".join(categorias_evento) if categorias_evento is not None else ''

    return {
        'titulo': titulo,
        'fecha_inicio': fecha_ini_form,
        'fecha_fin': fecha_fin_form,
        'descripcion': descripcion,
        'categorias': categorias_string
    }


def load_data():
    if not os.path.exists(DIR_INDEX):
        os.mkdir(DIR_INDEX)

    ix = create_in(DIR_INDEX, schema=get_schema())
    writer = ix.writer()

    eventos = extract_data()

    j = 0
    for n in eventos:
        evento = extract_evento(n)

        add_doc(writer, evento)
        j += 1

    messagebox.showinfo("Fin de indexado", "Se han indexado " + str(j) + " eventos")
    writer.commit()


def search_by_title_and_desc():
    def mostrar_lista(event):
        lb.delete(0, END)  # borra toda la lista
        ix = open_dir(DIR_INDEX)
        parameters = en.get().split()

        with ix.searcher() as searcher:
            query = parameters
            for p in parameters:
                query = f'{query} descripcion:{p.strip()}'
                query = QueryParser('titulo', ix.schema).parse(query)

            results = searcher.search(query, limit=None)
            for r in results:
                lb.insert(END, f"Título: {r['titulo']}")
                lb.insert(END, f"Desc: {r['descripcion']}")
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
        parameter = str(en.get().strip())
        print(parameter)
        meses= {
            "Ene": 1,
            "Feb": 2,
            "Mar": 3,
            "Abr": 4,
            "May": 5,
            "Jun": 6,
            "Jul": 7,
            "Ago": 8,
            "Sep": 9,
            "Oct": 10,
            "Nov": 11,
            "Dic": 12
        }
        fecha_rexep = re.match(r'(\d{2}) de (\w{3}) de (\d{4})', parameter)
        year = int(fecha_rexep.group(3))
        month = meses[fecha_rexep.group(2)]
        dia = int(fecha_rexep.group(1))

        fecha_parameter = (datetime(year, month, dia)).strftime('%Y%m%d')

        with ix.searcher() as searcher:
            query = QueryParser("fecha_inicio", ix.schema).parse(f"[to {fecha_parameter}]")
            results = searcher.search(query, limit=None)
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


def listarCategorias():
    ix = open_dir(DIR_INDEX)
    list_cat = []
    with ix.searcher() as searcher:
        results = searcher.documents()
        for r in results:
            categorias = (r['categorias']).split(',')
            for c in categorias:
                if c not in list_cat and c is not '':
                    list_cat.append(c)

    return list_cat


def search_by_categoria():
    def mostrar_lista(event):
        v = Toplevel()
        sc = Scrollbar(v)
        sc.pack(side=RIGHT, fill=Y)
        lb = Listbox(v, width=150, yscrollcommand=sc.set)

        ix = open_dir(DIR_INDEX)
        parameter = str(w.get())

        with ix.searcher() as searcher:
            query = QueryParser("categorias", ix.schema).parse(f'"{parameter}"')
            results = searcher.search(query, limit=None)
            for r in results:
                lb.insert(END, f"Título: {r['titulo']}")
                lb.insert(END, f"Rango de fechas: {r['fecha_inicio']} - {r['fecha_fin']}")
                lb.insert(END, f"Cat: {r['categorias']}")
                lb.insert(END, '')
            lb.pack(side=LEFT, fill=BOTH)
            sc.config(command=lb.yview)

    categorias = listarCategorias()

    master = Tk()
    w = Spinbox(master, values=categorias)
    w.pack()

    w.bind("<Return>", mostrar_lista)
    w.pack(side=LEFT)


def ventana_principal():
    top = Tk()

    menubar = Menu(top)

    datos_menu = Menu(menubar, tearoff=0)
    datos_menu.add_command(label="Cargar", command=load_data)
    datos_menu.add_command(label="Salir", command=top.quit)

    menubar.add_cascade(label="Datos", menu=datos_menu)

    buscar_menu = Menu(menubar, tearoff=0)
    buscar_menu.add_command(label="Título y descripción", command=search_by_title_and_desc)
    buscar_menu.add_command(label="Fecha", command=search_by_fecha)
    buscar_menu.add_command(label="Categoría", command=search_by_categoria)

    menubar.add_cascade(label="Buscar", menu=buscar_menu)

    top.config(menu=menubar)

    top.mainloop()


if __name__ == "__main__":
    ventana_principal()
