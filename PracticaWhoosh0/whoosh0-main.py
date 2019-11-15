from tkinter import *
import re
import urllib.request
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from tkinter import messagebox
import os
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED, DATETIME
from datetime import datetime
from whoosh.qparser import QueryParser


def open_url(base_url, req_url, page_path="", page=0):
    try:
        if 1 < page:
            req = urllib.request.urlopen(f"{base_url}{req_url}")
        else:
            req = urllib.request.urlopen(f"{base_url}{req_url}{page_path}{str(page)}")
        return req.read()

    except HTTPError as e:
        print(f"It was not possible to open URL: {base_url}{req_url}")
        print(e)
        return None


def extract_data_temas(base_url, req_url):
    raw_data = open_url(base_url, req_url)

    if raw_data:
        soup = BeautifulSoup(raw_data, 'html.parser')
        temas_elements = soup.find_all('li', class_='threadbit')
        temas = []
        respuestas = []
        for tema_element in temas_elements:
            # Temas: Titulo, Link_tema, Autor, Fecha, Número de respuestas, Número de visitas
            tema_info = tema_element.find('div', class_='threadinfo')
            titulo = tema_info.find('a', class_="title").get('title').strip()
            req_url_tema = urllib.parse.quote(tema_info.find('a', class_="title").get('href').strip(), safe=':/')
            link_tema = base_url + req_url_tema
            autor = tema_element.find('a', class_='username understate').text.strip()
            fecha = re.search(r"(\d{1,2}/\d{1,2}/\d{4})",
                              tema_element.find('div', class_='threadmeta')
                              .find('span', class_='label').text.strip()).group().replace(",", "")
            tema_stats = tema_element.find('ul', class_='threadstats')
            n_respuestas = tema_stats.find('a', class_='understate').getText().strip()
            n_visitas = re.search(r"(\d,?\d*)", tema_stats.select('ul > li')[1].getText(" ", strip=True)) \
                .group().replace(",", "")
            tema = {
                "titulo": titulo,
                "link_tema": link_tema,
                "autor": autor,
                "fecha": fecha,
                "n_respuestas": n_respuestas,
                "n_visitas": n_visitas
            }
            print(tema)
            temas.append(tema)
            respuestas += extract_data_all_respuestas(base_url, req_url_tema)
        res = {
            "temas": temas,
            "respuestas": respuestas
        }
        return res


    else:
        print("No HTML page was received!")
        return None


def extract_data_respuestas_per_page(base_url, req_url, page):
    print("extract_data_respuestas_pag")

    if 1 < page:
        raw_data = open_url(base_url, req_url, "/page", page)
    else:
        raw_data = open_url(base_url, req_url)

    if raw_data:
        # Respuestas: Link al tema, fecha, texto, autor
        soup = BeautifulSoup(raw_data, 'html.parser')
        respuesta_elements = soup.find('ol', class_='posts').findAll('li', class_='postcontainer')
        respuestas = []
        for respuesta_element in respuesta_elements:
            print("Parseando respuesta...")
            # urllib.parse.quote(base_url + req_url, safe=':/') not necessary
            link_tema = base_url + req_url
            fecha = re.search(r"(\d{1,2}/\d{1,2}/\d{4})",
                              respuesta_element.find('span', class_='date').getText("", strip=True)).group()
            texto = respuesta_element.find('div', class_='content').getText(" ", strip=True)
            autor_not_guest = soup.find('a', class_='username')
            if autor_not_guest is not None:
                autor = autor_not_guest.getText("", strip=True)
            else:
                autor = soup.find('span', class_='usertitle').getText("", strip=True)

            resuesta = {
                "link_tema": link_tema,
                "fecha": fecha,
                "texto": texto,
                "autor": autor,
            }
            respuestas.append(resuesta)
            print(resuesta)
        return respuestas


def extract_data_all_respuestas(base_url, req_url):
    # How many pages does the thread has?
    raw_data = open_url(base_url, req_url)
    n_pages = 1
    respuestas = []
    if raw_data:
        soup = BeautifulSoup(raw_data, 'html.parser')
        pagination_bottom =  soup.find('div', id='pagination_bottom').find('form', 'pagination popupmenu nohovermenu')
        if pagination_bottom is not None:

            n_pages = int(re.search(r"(?<=\d de )\d", pagination_bottom.find('a', class_='popupctrl')
                                .getText("", strip=True)).group())
            print(f"El hilo tiene {n_pages}")

    respuestas += extract_data_respuestas_per_page(base_url, req_url, 1)
    return respuestas

    if 1 < n_pages:
        for i in range(2, n_pages + 1):
            respuestas.append(extract_data_respuestas_per_page(base_url, req_url, i))


def aparatado_a(base_url, req_url, dirindex_temas, dirindex_resp):
    documents = extract_data_temas(base_url, req_url)

    if not os.path.exists(dirindex_temas):
        os.mkdir(dirindex_temas)

    if not os.path.exists(dirindex_resp):
        os.mkdir(dirindex_resp)

    print('Indexing documents...')
    ix_derecho_temas = create_in(dirindex_temas, schema=get_schema_temas())
    ix_derecho_respuestas = create_in(dirindex_resp, schema=get_schema_respuestas())

    writer_temas = ix_derecho_temas.writer()
    writer_respuestas = ix_derecho_respuestas.writer()
    i_resp = 0
    i_temas = 0

    for tema in documents['temas']:
        add_doc_tema(writer_temas, tema)
        i_temas += 1

    print("All threads has been indexed!")

    for respuesta in documents['respuestas']:
        add_doc_respuestas(writer_respuestas, respuesta)
        i_resp += 1

    writer_temas.commit()
    writer_respuestas.commit()
    messagebox.showinfo("Fin de indexado", f"Se han indexado {str(i_temas)} temas y {str(i_resp)} respuestas.")


def apartado_b_tema_titulo(dirindex_temas):
    def mostrar_lista(event):
        lb.delete(0, END)  # borra toda la lista
        ix = open_dir(dirindex_temas)
        with ix.searcher() as searcher:
            query = QueryParser("titulo", ix.schema).parse(str(en.get()))
            results = searcher.search(query)
            for r in results:
                lb.insert(END, r['titulo'])
                lb.insert(END, r['autor'])
                lb.insert(END, r['fecha'])
                lb.insert(END, '')

    v = Toplevel()
    v.title("Buscar temas por título")
    f = Frame(v)
    f.pack(side=TOP)
    l = Label(f, text="Introduzca una palabra:")
    l.pack(side=LEFT)
    en = Entry(f)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, yscrollcommand=sc.set)
    lb.pack(side=BOTTOM, fill=BOTH)
    sc.config(command=lb.yview)

def apartado_b_tema_autor(dirindex_temas):
    def mostrar_lista(event):
        lb.delete(0, END)  # borra toda la lista
        ix = open_dir(dirindex_temas)
        with ix.searcher() as searcher:
            query = QueryParser("autor", ix.schema).parse(str(en.get()))
            results = searcher.search(query)
            for r in results:
                lb.insert(END, r['titulo'])
                lb.insert(END, r['autor'])
                lb.insert(END, r['fecha'])
                lb.insert(END, '')

    v = Toplevel()
    v.title("Buscar temas por autor")
    f = Frame(v)
    f.pack(side=TOP)
    l = Label(f, text="Introduzca el nombre del autor:")
    l.pack(side=LEFT)
    en = Entry(f)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, yscrollcommand=sc.set)
    lb.pack(side=BOTTOM, fill=BOTH)
    sc.config(command=lb.yview)

def apartado_b_respuestas(dirindex_temas, dirindex_respuestas):
    def mostrar_lista(event):
        lb.delete(0, END)  # borra toda la lista
        ix_respuestas = open_dir(dirindex_respuestas)
        with ix_respuestas.searcher() as searcher_resp:
            query = QueryParser("texto", ix_respuestas.schema).parse(str(en.get()))
            results = searcher_resp.search(query)
            for r in results:
                ix_temas = open_dir(dirindex_temas)
                with ix_temas.searcher() as searcher_temas:
                    query_tema = QueryParser("autor", ix_temas.schema).parse(str(f"link_tema:{str(r['link_tema'])}"))
                    result_tema = searcher_temas.search(query_tema)[0]
                    lb.insert(END, result_tema['titulo'])
                lb.insert(END, r['autor'])
                lb.insert(END, r['fecha'])
                lb.insert(END, '')

    v = Toplevel()
    v.title("Buscar respuestas por texto")
    f = Frame(v)
    f.pack(side=TOP)
    l = Label(f, text="Introduzca una palabra:")
    l.pack(side=LEFT)
    en = Entry(f)
    en.bind("<Return>", mostrar_lista)
    en.pack(side=LEFT)
    sc = Scrollbar(v)
    sc.pack(side=RIGHT, fill=Y)
    lb = Listbox(v, yscrollcommand=sc.set)
    lb.pack(side=BOTTOM, fill=BOTH)
    sc.config(command=lb.yview)


def add_doc_tema(writer, tema):
    print("Indexing thread...")
    print(tema)
    writer.add_document(titulo=tema['titulo'], link_tema=tema['link_tema'], autor=tema['autor'],
                        fecha=datetime.strptime(tema['fecha'], '%d/%m/%Y'), n_respuestas=tema['n_respuestas'],
                        n_visitas=tema['n_visitas'])


def add_doc_respuestas(writer, respuesta):
    print("Indexing answer...")
    print(respuesta)
    writer.add_document(link_tema=respuesta['link_tema'], fecha=datetime.strptime(respuesta['fecha'], '%d/%m/%Y'),
                        texto=respuesta['texto'], autor=respuesta['autor'])

def get_schema_temas():
    return Schema(titulo=TEXT(stored=True), link_tema=ID(unique=True, stored=True), autor=KEYWORD(stored=True),
                  fecha=DATETIME(stored=True), n_respuestas=STORED, n_visitas=STORED)


def get_schema_respuestas():
    return Schema(link_tema=ID(stored=True), fecha=DATETIME(stored=True), texto=TEXT(stored=True), autor=STORED)


def ventana_principal():
    # Instanciando la práctica...
    DIRINDEX_TEMAS = "index-temas"
    DIRINDEX_RESP = "index-resp"
    BASE_URL = 'https://foros.derecho.com/'
    REQ_URL = 'foro/34-Derecho-Inmobiliario'

    top = Tk()
    top.title('Práctica de Whoosh')
    menubar = Menu(top)

    # Apartado A
    inicio_menu = Menu(menubar, tearoff=0)
    inicio_menu.add_command(label="Indexar", command=lambda: aparatado_a(BASE_URL, REQ_URL,
                                                                         DIRINDEX_TEMAS, DIRINDEX_RESP))
    inicio_menu.add_command(label="Salir", command=lambda: top.destroy())

    # Apartado B.a
    buscar_menu = Menu(menubar, tearoff=0)

    # Apartado B.a
    buscar_menu_temas = Menu(buscar_menu, tearoff=0)
    buscar_menu_temas.add_command(label="Título", command=lambda: apartado_b_tema_titulo(DIRINDEX_TEMAS))
    buscar_menu_temas.add_command(label="Autor", command=lambda: apartado_b_tema_autor(DIRINDEX_TEMAS))

    # Apartado B.b
    buscar_menu_respuestas = Menu(buscar_menu, tearoff=0)
    buscar_menu_respuestas.add_command(label="Texto", command=lambda: apartado_b_respuestas(DIRINDEX_TEMAS,DIRINDEX_RESP))

    menubar.add_cascade(label="Inicio", menu=inicio_menu)
    buscar_menu.add_cascade(label="Temas", menu=buscar_menu_temas)
    buscar_menu.add_cascade(label="Respuestas", menu=buscar_menu_respuestas)
    menubar.add_cascade(label="Buscar", menu=buscar_menu)

    top.config(menu=menubar)

    top.mainloop()


if __name__ == '__main__':
    ventana_principal()
