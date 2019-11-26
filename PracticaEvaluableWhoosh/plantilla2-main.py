import os
import re
import urllib.parse
import urllib.request
from tkinter import Tk, Menu, messagebox, END, Toplevel, Frame, TOP, Label, LEFT, Entry, Scrollbar, RIGHT, Y, Listbox, \
    BOTTOM, BOTH
from urllib.error import HTTPError
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from whoosh.fields import Schema, TEXT, ID, DATETIME, NUMERIC, STORED
from whoosh.index import create_in, open_dir
from whoosh.qparser import QueryParser

BASE_URL = 'https://foros.derecho.com/'
THREADS_URL = 'foro/34-Derecho-Inmobiliario'

DIR_DOCS_1 = "hilos"
DIR_INDEX_1 = "Index1"

DIR_DOCS_2 = "respuestas"
DIR_INDEX_2 = "Index2"


# WHOOSH
def get_thread_schema():
    return Schema(titulo=TEXT(stored=True),
                  link=ID(stored=True),
                  autor=TEXT(stored=True),
                  fecha=DATETIME(stored=True),
                  respuestas=STORED,
                  visitas=STORED)


def get_response_schema():
    return Schema(link_tema=ID(stored=True),
                  fecha=DATETIME(stored=True),
                  texto=TEXT(stored=True),
                  autor=TEXT(stored=True))


def add_thread_doc(writer, titulo, link, autor, fecha, respuestas, visitas):
    writer.add_document(titulo=titulo, link=link, autor=autor, fecha=fecha, respuestas=respuestas, visitas=visitas)


def add_response_doc(writer, link_tema, fecha, texto, autor):
    writer.add_document(link_tema=link_tema, fecha=fecha, texto=texto, autor=autor)


# BeautifulSoup
def open_url(url):
    try:
        req = urllib.request.urlopen(url)
        return req.read()
    except HTTPError as e:
        print(e)
        return None


def extract_thread_data():
    raw_data = open_url(BASE_URL + THREADS_URL)
    if raw_data:
        soup = BeautifulSoup(raw_data, 'html.parser')
        threads = soup.find('ol', class_='threads').find_all('li', class_='threadbit')
        return threads


def extract_responses_data(thread_url):
    raw_data = open_url(BASE_URL + urllib.parse.quote(thread_url))
    if raw_data:
        soup = BeautifulSoup(raw_data, 'html.parser')
        responses = soup.find('ol', class_='posts').find_all('li', class_='postbitlegacy postbitim postcontainer old')
        return responses


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
    temas = extract_thread_data()

    for tema in temas:
        titulo = tema.find('h3', class_='threadtitle').text.strip()
        link = tema.find('h3', class_='threadtitle').find('a')['href']
        creador = [i for i in tema.find('div', class_='author').find('span').stripped_strings][1]
        fecha = [i for i in tema.find('div', class_='author').find('span').stripped_strings][2][2:]
        num_resp = [i for i in tema.find('ul', class_='threadstats td alt').find('li').stripped_strings][1]
        num_vis = re.findall(r'\d+', tema.find('ul', class_='threadstats td alt').find_all('li')[1].text)[0]

        date_form = datetime.strptime(fecha, '%d/%m/%Y %H:%M')

        add_thread_doc(writer1, titulo, urllib.parse.quote(BASE_URL + link, safe=':/'), creador, date_form,
                       int(num_resp),
                       int(num_vis))
        j += 1

        respuestas = extract_responses_data(link)

        for respuesta in respuestas:
            link_tema = BASE_URL + link
            fecha_respuesta = \
                [i for i in respuesta.find('div', class_='posthead').find('span', class_='date').stripped_strings][0][
                :-1]
            texto_respuesta = respuesta.find('blockquote', class_='postcontent restore').text.strip()

            tiene_autor = respuesta.find('div', class_='popupmenu memberaction')

            if tiene_autor:
                autor = [i for i in tiene_autor.stripped_strings][0]
            else:
                autor = 'Guest'

            if fecha_respuesta == 'Ayer':
                fecha_respuesta = (datetime.now() - timedelta(days=1)).strftime("%m/%d/%Y")

                date_resp = datetime.strptime(fecha_respuesta, '%d/%m/%Y')

                add_response_doc(writer2, urllib.parse.quote(link_tema, safe=':/'), date_resp, texto_respuesta, autor)

                messagebox.showinfo("Fin de indexado", "Se han indexado " + str(j) + " temas")
                writer1.commit()
                writer2.commit()


def search_by_title():
    def mostrar_lista(event):
        lb.delete(0, END)  # borra toda la lista
        ix = open_dir(DIR_INDEX_1)
        parameter = str(en.get())

        with ix.searcher() as searcher:
            query = QueryParser("titulo", ix.schema).parse(parameter)
            results = searcher.search(query)
            for r in results:
                lb.insert(END, f"Título: {r['titulo']}")
                lb.insert(END, f"Autor: {r['autor']}")
                lb.insert(END, f"Fecha: {r['fecha']}")
                lb.insert(END, f"Link: {r['link']}")
                lb.insert(END, '')

    v = Toplevel()
    v.title("Busqueda en el título")
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


def search_by_author():
    def mostrar_lista(event):
        lb.delete(0, END)  # borra toda la lista
        ix = open_dir(DIR_INDEX_1)
        parameter = str(en.get())

        with ix.searcher() as searcher:
            query = QueryParser("autor", ix.schema).parse(parameter)
            results = searcher.search(query)
            for r in results:
                lb.insert(END, f"Título: {r['titulo']}")
                lb.insert(END, f"Autor: {r['autor']}")
                lb.insert(END, f"Fecha: {r['fecha']}")
                lb.insert(END, '')

    v = Toplevel()
    v.title("Búsqueda por autor")
    f = Frame(v)
    f.pack(side=TOP)
    l = Label(f, text="Introduzca un nombre de autor:")
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


def ventana_principal():
    top = Tk()

    menubar = Menu(top)
    inicio_menu = Menu(menubar, tearoff=0)
    inicio_menu.add_command(label="Indexar", command=create_index)
    inicio_menu.add_command(label="Salir", command=top.quit)
    menubar.add_cascade(label="Inicio", menu=inicio_menu)

    buscar_menu = Menu(menubar, tearoff=0)

    temas_menu = Menu(menubar, tearoff=0)
    temas_menu.add_command(label="Título", command=search_by_title)
    temas_menu.add_command(label="Autor", command=search_by_author)

    respuestas_menu = Menu(menubar, tearoff=0)
    respuestas_menu.add_command(label='Texto', command=search_by_response)

    menubar.add_cascade(label="Buscar", menu=buscar_menu)

    buscar_menu.add_cascade(label='Temas', menu=temas_menu)
    buscar_menu.add_cascade(label='Respuestas', menu=respuestas_menu)

    top.config(menu=menubar)

    top.mainloop()


if __name__ == "__main__":
    ventana_principal()