import os
from whoosh.index import create_in
from whoosh.fields import *

doc_directory = "Correos"


def ventana_principal():
    documents_dir = "Correos"
    document_schema = Schema(doc_file=ID(stored=True), remitente=KEYWORD, destinatarios=KEYWORD,
                             asunto=TEXT, contenido=TEXT)
    doc_indexer(documents_dir, document_schema)


def doc_indexer(documents_dir, document_schema):
    if not os.path.exists("indexdir_correos"):
        os.mkdir("indexdir_correos")

    document_index = create_in("indexdir_correos",document_schema)
    document_list = []

    if os.path.isdir(documents_dir):
        for document_file in os.listdir(documents_dir):
            doc_file_path = f"{documents_dir}/{document_file}"
            document = open(doc_file_path)
            remitente = document.readline().strip()
            destinatarios = document.readline().strip()
            asunto = document.readline().strip()
            cuerpo = "".join(document.readlines()).strip()
            document.close()

            document_list.append({
                "doc_file_path" : doc_file_path,
                "remitente": remitente,
                "destinatarios": destinatarios,
                "asunto": asunto,
                "cuerpo": cuerpo
            })
    else:
        print("No existe el directorio")
    n_docs_added = add_document_to_index(document_index, document_list)
    print(f"Se han indexado {n_docs_added} documentos")


def add_document_to_index(document_index, document_list):
    index_writer = document_index.writer()
    n_docs_added = 0

    print("Reading document_list...")
    for document_dictionary in document_list:

        print(document_dictionary)
        doc_file_path = document_dictionary["doc_file_path"]
        remitente = document_dictionary["remitente"]
        destinatarios = document_dictionary["destinatarios"]
        asunto = document_dictionary["asunto"]
        cuerpo = document_dictionary["cuerpo"]

        was_added = index_writer.add_document(doc_file=doc_file_path, remitente=remitente, destinatarios=destinatarios,
                              asunto=asunto, contenido=cuerpo)
        n_docs_added += 1
    index_writer.commit()
    return n_docs_added



def doc_reader(document_path, line_number):
    result = ""
    document_file = open(document_path)
    assert line_number < len(document_file.readlines()), "The documents has less lines than what you want to read"
    for i, line in enumerate(document_file):
        if i == line_number:
            result = line
            break
    document_file.close()
    return result

if __name__ == '__main__':
    ventana_principal()
