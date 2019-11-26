# encoding:utf-8
from tkinter import *
import re
import urllib.request
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from tkinter import messagebox
import os
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, KEYWORD, STORED, DATETIME
from datetime import datetime
from whoosh.qparser import QueryParser
from whoosh.qparser import MultifieldParser
from whoosh.qparser.dateparse import DateParserPlugin


def open_url(page: int, req_url):
    try:
        if (page > 1):
            req = urllib.request.urlopen(f"{req_url}{page}")
        else:
            req = urllib.request.urlopen(f"{req_url}")
        return req.read()
    except HTTPError as e:
        print(e)
        return None


def extract_data(page: int, base_url, req_url):
    raw_data = open_url(page, req_url)
    noticias = []
    if raw_data:
        soup = BeautifulSoup(raw_data, 'html.parser')
        noticias_cards = soup.find_all('div', class_='news-card')

        for noticia_card in noticias_cards:
            categoria = re.sub(r"^NOTICIAS - ", "", noticia_card.find('div', class_='meta-category').text, 1)
            titulo = noticia_card.find('h2', class_='meta-title').a.get_text("", strip=True)
            img_element = noticia_card.find('img')

            if 'b-loaded' in img_element.get('class') :
                imagen = img_element.find('img').get('data-src')
            else:
                imagen = img_element.get('src')

            noticia_subscraper \
                = extract_data_subscraper(
                re.sub(r'/noticias/', '', base_url)
                + noticia_card.find('a', class_='meta-title-link').get('href'))
            ##Clases de cards: news-card-full, news-card-row, news-card

            noticia = {
                "categoria": categoria,
                "titulo": titulo,
                "imagen": imagen,
                "descripcion": noticia_subscraper['descripcion'],
                "fecha": noticia_subscraper['fecha'],
            }
            print(noticia)
            noticias.append(noticia)
    return noticias


def extract_data_subscraper(url):
    # print(f"Opening URL...={link}")
    raw_data = urllib.request.urlopen(url)
    noticia = {
        "descripcion": "",
        "fecha": ""
    }
    if raw_data:
        soup = BeautifulSoup(raw_data, 'html.parser')
        fecha = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", soup.find('span', class_='titlebar-subtile-txt').text).group()
        if re.fullmatch(r"^.*\/noticias\/.*$", url):
            descripcion = soup.find('div', id='article-content').find('p') \
                .get_text(" ", strip=True)
        else:
            descripcion = soup.find('p', class_="article-lead").get_text(" ", strip=True)

        noticia['fecha'] = datetime.strptime(fecha, '%d/%m/%Y')
        noticia['descripcion'] = descripcion

    return noticia


def add_doc(writer, noticia):
    writer.add_document(categoria=noticia['categoria'], titulo=noticia['titulo'],
                        imagen=noticia['imagen'], descripcion=noticia['descripcion'], fecha=noticia['fecha'])


def get_schema():
    return Schema(categoria=STORED, titulo=TEXT(stored=True),
                  imagen=STORED, descripcion=TEXT(stored=True), fecha=DATETIME(stored=True))


def apartado_a_cargar(page: int, base_url, req_url, dirindex):
    noticias = []
    for i in range(1, page + 1):
        noticias.extend(extract_data(i, base_url, req_url))

    if not os.path.exists(dirindex):
        os.mkdir(dirindex)

    print('Indexing documents...')
    ix_sensacine = create_in(dirindex, schema=get_schema())
    writer = ix_sensacine.writer()
    i = 0
    for noticia in noticias:
        add_doc(writer, noticia)
        i += 1
    messagebox.showinfo("Fin de indexado", f"Se han indexado {str(i)} noticias")
    writer.commit()


def apartado_b_tyd(dirindex):
    def mostrar_lista(event):
        lb.delete(0, END)  # Borra la lista
        ix_sensacine = open_dir(dirindex)
        with ix_sensacine.searcher() as searcher:
            query = MultifieldParser(["titulo", "descripcion"], ix_sensacine.schema).parse(str(en.get()))
            results = searcher.search(query)
            for r in results:
                lb.insert(END, r['categoria'])
                lb.insert(END, r['titulo'])
                lb.insert(END, r['fecha'])
                lb.insert(END, '')

    top_b_tyd = Toplevel()
    top_b_tyd.title("Busqueda por Título y Descripción")
    f = Frame(top_b_tyd)
    f.pack(side=TOP)
    l = Label(f, text="Introduzca una o varias palabras:")
    l.pack(side=LEFT)
    en = Entry(f)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
    sc = Scrollbar(top_b_tyd)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(top_b_tyd, yscrollcommand=sc.set)
    lb.pack(side=BOTTOM, fill=BOTH)
    sc.config(command=lb.yview)

def apartado_b_fecha(dirindex):
    def mostrar_lista(event):
        lb.delete(0, END)  # Borra la lista
        ix_sensacine = open_dir(dirindex)
        with ix_sensacine.searcher() as searcher:
            fechas_str_list = en.get().split(" ")
            date_query = ""
            if len(fechas_str_list) > 1:
                fechainicio = parse_fecha(fechas_str_list[0])
                fechafin = parse_fecha(fechas_str_list[1])
                date_query = f":[{fechainicio.strftime('%Y%m%d')} TO {fechafin.strftime('%Y%m%d')}]"
            elif len(fechas_str_list) == 1:
                fechainicio = parse_fecha(fechas_str_list[0])
                fechafin = datetime.today()
                date_query = f"[{fechainicio.strftime('%Y%m%d')} TO {fechafin.strftime('%Y%m%d')}]"

            print(f"{date_query}")
            query = QueryParser("fecha", ix_sensacine.schema).parse(date_query)
            results = searcher.search(query)
            print(f"Resultados recuperados: {results}")
            for r in results:
                lb.insert(END, r['titulo'])
                lb.insert(END, r['fecha'])
                lb.insert(END, '')
    def parse_fecha(fecha_str):
        return datetime.strptime(fecha_str, '%d/%m/%Y')

    top_b_d = Toplevel()
    top_b_d.title("Busqueda por Descripción")
    f = Frame(top_b_d)
    f.pack(side=TOP)
    l = Label(f, text="Introduzca un rango de fechas en formato DD/MM/AAAA DD/MM/AAAA")
    l.pack(side=LEFT)
    en = Entry(f)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
    sc = Scrollbar(top_b_d)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(top_b_d, yscrollcommand=sc.set)
    lb.pack(side=BOTTOM, fill=BOTH)
    sc.config(command=lb.yview)

def apartado_b_d(dirindex):
    def mostrar_lista(event):
        lb.delete(0, END)  # Borra la lista
        ix_sensacine = open_dir(dirindex)
        with ix_sensacine.searcher() as searcher:
            query = QueryParser("descripcion", ix_sensacine.schema).parse(str(en.get()))
            results = searcher.search(query)
            for r in results:
                lb.insert(END, r['titulo'])
                lb.insert(END, r['imagen'])
                lb.insert(END, r['descripcion'])
                lb.insert(END, '')

    top_b_d = Toplevel()
    top_b_d.title("Busqueda por Descripción")
    f = Frame(top_b_d)
    f.pack(side=TOP)
    l = Label(f, text="Introduzca una frase:")
    l.pack(side=LEFT)
    en = Entry(f)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
    sc = Scrollbar(top_b_d)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(top_b_d, yscrollcommand=sc.set)
    lb.pack(side=BOTTOM, fill=BOTH)
    sc.config(command=lb.yview)


def ventana_principal():
    # Instanciando el ejercicio...
    DIRINDEX = "index-sensacine"
    BASE_URL = 'http://www.sensacine.com/noticias/'
    REQ_URL = f'{BASE_URL}?page='
    PAGES = 3

    top = Tk()
    top.title('Práctica de Whoosh 1')

    menubar = Menu(top)

    datos_menu = Menu(menubar, tearoff=0)
    datos_menu.add_command(label="Cargar", command=lambda: apartado_a_cargar(PAGES, BASE_URL, REQ_URL, DIRINDEX))
    datos_menu.add_command(label="Salir", command=lambda: top.destroy())

    menubar.add_cascade(label="Inicio", menu=datos_menu)

    buscar_menu = Menu(menubar, tearoff=0)
    buscar_menu.add_command(label="Titulo y Descripción", command=lambda: apartado_b_tyd(DIRINDEX))
    buscar_menu.add_command(label="Fecha", command=lambda: apartado_b_fecha(DIRINDEX))
    buscar_menu.add_command(label="Descripción", command=lambda: apartado_b_d(DIRINDEX))

    menubar.add_cascade(label="Buscar", menu=buscar_menu)

    top.config(menu=menubar)

    top.mainloop()


if __name__ == '__main__':
    ventana_principal()
