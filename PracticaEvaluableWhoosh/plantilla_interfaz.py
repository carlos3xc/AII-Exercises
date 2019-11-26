from tkinter import Tk, Menu, Frame, Button, LEFT


def ventana_principal():
    top = Tk()

    menubar = Menu(top)

    # Menú normal
    datos_menu = Menu(menubar, tearoff=0)
    datos_menu.add_command(label="Cargar", command=lambda: print('Load data'))
    datos_menu.add_command(label="Mostrar", command=lambda: print('Show data'))
    datos_menu.add_command(label="Salir", command=top.quit)

    menubar.add_cascade(label="Datos", menu=datos_menu)

    buscar_menu = Menu(menubar, tearoff=0)
    buscar_menu.add_command(label="Autor", command=lambda: print('Opción 1'))
    buscar_menu.add_command(label="Fecha", command=lambda: print('Opción 2'))

    # Submenú
    sub_menu = Menu(menubar, tearoff=0)
    sub_menu.add_command(label='Respuestas', command=lambda: print('Submenú'))

    buscar_menu.add_cascade(label='Submenú', menu=sub_menu)
    menubar.add_cascade(label="Buscar", menu=buscar_menu)

    top.config(menu=menubar)

    frame = Frame(top)
    frame.pack()

    # Botones
    store = Button(frame, text="Opción 1", command=lambda: print('Load data'))
    store.pack(side=LEFT)

    list_j = Button(frame, text="Opción 2", command=lambda: print('Show data'))
    list_j.pack(side=LEFT)

    top.mainloop()


if __name__ == "__main__":
    ventana_principal()
