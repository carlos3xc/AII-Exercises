import urllib.request
import urllib.parse
from datetime import datetime
import locale
import os
from tkinter import Tk, Menu, messagebox, Toplevel, Frame, TOP, Label, LEFT, Entry, Scrollbar, RIGHT, Y, Listbox, BOTH, \
    BOTTOM, END

from bs4 import BeautifulSoup
from whoosh import fields
from whoosh.fields import Schema, TEXT, ID
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser

BASE_URL = 'http://www.sensacine.com'
PAGES = 3

DIR_DOCS = "noticias"
DIR_INDEX = "Index"


# WHOOSH
def get_schema():
    return Schema(titulo=TEXT(stored=True),
                  descripcion=TEXT(stored=True),
                  categoria=TEXT(stored=True),
                  enlace_imagen=ID(stored=True),
                  fecha=fields.DATETIME(stored=True))


def add_doc(writer, categoria, titulo, descripcion, enlace_imagen, fecha):
    writer.add_document(titulo=titulo, descripcion=descripcion,
                        categoria=categoria, enlace_imagen=enlace_imagen, fecha=fecha)


# BeautifulSoup
def open_url(url):
    cod_url = urllib.parse.quote(url, safe=':/?=')
    try:
        req = urllib.request.urlopen(cod_url)
        return req.read()
    except:
        print(f'----------Error---------- URL: {cod_url}')
        return None


def extract_data(page: int):
    raw_data = open_url(f'{BASE_URL}/noticias/?page={page}')
    if raw_data:
        soup = BeautifulSoup(raw_data, 'html.parser')
        noticias = soup.find('div', class_='col-left').find_all('div', class_='news-card')
        return noticias


def extract_description(enlace_noticia):
    raw_data = open_url(enlace_noticia)
    if raw_data:
        soup = BeautifulSoup(raw_data, 'html.parser')
        desc = soup.find('p', class_='article-lead').text
        return desc
    else:
        return 'Sin descripción'


def extract_noticia(noticia) -> dict:
    categoria = noticia.find('div', class_='meta').find('div', class_='meta-category').text.split(' - ')[
        1].strip()
    titulo = noticia.find('a', class_='meta-title-link').text.strip()
    enlace_imagen = noticia.find('img', class_='thumbnail-img')['src']
    fecha = noticia.find('div', class_='meta-date').text
    enlace_noticia = noticia.find('a', class_='meta-title-link')['href']

    locale.setlocale(locale.LC_ALL, 'es_ES')
    fecha = datetime.strptime(fecha, '%A, %d de %B de %Y')

    return {
        'categoria': categoria,
        'titulo': titulo,
        'enlace_imagen': enlace_imagen,
        'fecha': fecha,
        'enlace_noticia': enlace_noticia
    }


def load_data():
    if not os.path.exists(DIR_INDEX):
        os.mkdir(DIR_INDEX)

    ix = create_in(DIR_INDEX, schema=get_schema())
    writer = ix.writer()

    j = 0
    for i in range(1, PAGES + 1):
        noticias = extract_data(i)

        for noticia in noticias:
            n = extract_noticia(noticia)

            descripcion = extract_description(BASE_URL + n['enlace_noticia'])

            add_doc(writer, n['categoria'], n['titulo'], descripcion, n['enlace_imagen'], n['fecha'])
            j += 1

    messagebox.showinfo("Fin de indexado", "Se han indexado " + str(j) + " noticias")
    writer.commit()


def search_by_title_and_desc():
    def mostrar_lista(event):
        lb.delete(0, END)  # borra toda la lista
        ix = open_dir(DIR_INDEX)
        parameters = en.get().split()
        with ix.searcher() as searcher:
            query = str(en.get())
            for p in parameters:
                query = f'{query} descripcion:{p.strip()}'
                query = QueryParser('titulo', ix.schema).parse(query)
            # query1 = MultifieldParser(['titulo', 'descripcion'], ix.schema, group=qparser.AndGroup).parse(en.get())

            results = searcher.search(query, limit=None)
            for r in results:
                lb.insert(END, f"Título: {r['titulo']}")
                lb.insert(END, f"Descripción: {r['descripcion']}")
                lb.insert(END, f"Fecha: {r['fecha']}")
                lb.insert(END, '')

    v = Toplevel()
    v.title("Busqueda por título y descripción")
    f = Frame(v)
    f.pack(side=TOP)
    l = Label(f, text="Introduzca el término:")
    l.pack(side=LEFT)
    en = Entry(f)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, yscrollcommand=sc.set)
    lb.pack(side=BOTTOM, fill=BOTH)
    sc.config(command=lb.yview)


def search_by_dates():
    def mostrar_lista(event):
        lb.delete(0, END)  # borra toda la lista
        ix = open_dir(DIR_INDEX)
        dates = en.get().strip().split(' ')

        date1 = datetime.strptime(dates[0], '%d/%m/%Y').strftime('%Y%m%d')
        date2 = datetime.strptime(dates[1], '%d/%m/%Y').strftime('%Y%m%d')

        with ix.searcher() as searcher:
            query = QueryParser('fecha', ix.schema).parse(f"[{date1} to {date2}]")
            print(query)
            results = searcher.search(query, limit=None)
            for r in results:
                lb.insert(END, f"Título: {r['titulo']}")
                lb.insert(END, f"Fecha: {r['fecha']}")
                lb.insert(END, '')

    v = Toplevel()
    v.title("Busqueda por fechas")
    f = Frame(v)
    f.pack(side=TOP)
    l = Label(f, text="Fechas separadas por un espacio en formato DD/MM/AAAA:")
    l.pack(side=LEFT)
    en = Entry(f)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, yscrollcommand=sc.set)
    lb.pack(side=BOTTOM, fill=BOTH)
    sc.config(command=lb.yview)


def search_by_desc():
    def mostrar_lista(event):
        lb.delete(0, END)  # borra toda la lista
        ix = open_dir(DIR_INDEX)
        frase = en.get()

        with ix.searcher() as searcher:
            query = QueryParser("descripcion", ix.schema).parse(f'"{frase}"')
            results = searcher.search(query)
            for r in results:
                lb.insert(END, f"Título: {r['titulo']}")
                lb.insert(END, f"Enlace imagen: {r['enlace_imagen']}")
                lb.insert(END, f"Descripción: {r['descripcion']}")
                lb.insert(END, '')

    v = Toplevel()
    v.title("Busqueda en la descripción")
    f = Frame(v)
    f.pack(side=TOP)
    l = Label(f, text="Introduzca una frase:")
    l.pack(side=LEFT)
    en = Entry(f)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, yscrollcommand=sc.set)
    lb.pack(side=BOTTOM, fill=BOTH)
    sc.config(command=lb.yview)


def ventana_principal():
    top = Tk()

    menubar = Menu(top)

    datos_menu = Menu(menubar, tearoff=0)
    datos_menu.add_command(label="Cargar", command=load_data)
    datos_menu.add_command(label="Salir", command=top.quit)

    menubar.add_cascade(label="Datos", menu=datos_menu)

    buscar_menu = Menu(menubar, tearoff=0)
    buscar_menu.add_command(label="Título y descripción", command=search_by_title_and_desc)
    buscar_menu.add_command(label="Fecha", command=search_by_dates)
    buscar_menu.add_command(label="Descripción", command=search_by_desc)

    menubar.add_cascade(label="Buscar", menu=buscar_menu)

    top.config(menu=menubar)

    top.mainloop()


if __name__ == "__main__":
    ventana_principal()