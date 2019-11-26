from datetime import datetime
import urllib.request
import urllib.parse

from bs4 import BeautifulSoup

BASE_URL = 'https://www.meneame.net/'
REQ_URL = f'{BASE_URL}?page='
PAGES = 3


def open_url(url):
    cod_url = urllib.parse.quote(url, safe=':/?=')
    try:
        req = urllib.request.urlopen(cod_url)
        return req.read()
    except:
        print(f'----------Error---------- URL: {cod_url}')
        return None


def extract_data(page: int):
    raw_data = open_url(f"{REQ_URL}{page}")
    if raw_data:
        soup = BeautifulSoup(raw_data, 'html.parser')
        productos = soup.find_all('div', class_='news-summary')
        return productos


def extract_noticia(n):
    titulo = n.find('div', class_='center-content').h2.text.strip()
    enlace_fuente = n.find('div', class_='center-content').h2.a['href']
    autor = n.find('div', class_='news-submitted').find_all('a')[1].text
    fecha_hora = n.find_all('span', class_='ts visible')[1]['data-ts']
    contenido = n.find('div', class_='news-content').text

    # dt = datetime.utcfromtimestamp(int(fecha_hora)).strftime("%d/%m/%Y %H:%M:%S")
    dt = datetime.utcfromtimestamp(int(fecha_hora))

    return {
        'titulo': titulo,
        'enlace_fuente': enlace_fuente,
        'autor': autor,
        'dt': dt,
        'contenido': contenido
    }


def load_data():
    for p in range(1, PAGES + 1):
        noticias = extract_data(p)

        for n in noticias:
            noticia = extract_noticia(n)

            print(noticia['titulo'])
            print(noticia['enlace_fuente'])
            print(noticia['autor'])
            print(noticia['dt'])
            print(noticia['contenido'])


load_data()


