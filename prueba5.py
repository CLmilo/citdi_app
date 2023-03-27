from tkinter import *

# Configuración de la raíz
root = Tk()
root.geometry('600x400')

menubar = Menu(root)
root.config(menu=menubar)

filemenu = Menu(menubar, tearoff=0)
filemenu.add_command(label="Nuevo")
filemenu.add_command(label="Abrir")
filemenu.add_command(label="Guardar")
filemenu.add_command(label="Cerrar")
filemenu.add_separator()
filemenu.add_command(label="Salir", command=root.quit)

editmenu = Menu(menubar, tearoff=0)
editmenu.add_command(label="Cortar")
editmenu.add_command(label="Copiar")
editmenu.add_command(label="Pegar")

helpmenu = Menu(menubar, tearoff=0)
helpmenu.add_command(label="Ayuda")
helpmenu.add_separator()
helpmenu.add_command(label="Acerca de...")

menubar.add_cascade(label="Archivo", menu=filemenu)
menubar.add_cascade(label="Editar", menu=editmenu)
menubar.add_cascade(label="Ayuda", menu=helpmenu)

Menup = Frame(root, bg="red")
Menup.pack(fill="both", expand=1)
Collect_Wire = Frame(root, bg="blue")

def raise_frame(frame):
    Collect_Wire.pack_forget()
    Menup.pack_forget()
    frame.pack(fill="both", expand=1)

def salir():
    root.destroy()

Button(Menup, text='Salir', command=salir).pack()
#Button(Menup, text="cambiar", command=lambda:cambiar()).pack()
Button(Menup, text="collect", command=lambda:raise_frame(Collect_Wire)).pack()

Button(Collect_Wire, text="menup", command=lambda:raise_frame(Menup)).pack()


# Finalmente bucle de la aplicación
root.mainloop()