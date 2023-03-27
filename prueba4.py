from matplotlib.figure import Figure
import numpy as np
from tkinter import Tk, Frame,Button,Label, ttk, Menu
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk

root = Tk()
#ventana.geometry('642x535')

menubar = Menu(root)
root.config(menu=menubar)

filemenu = Menu(menubar, tearoff=0)
filemenu.add_command(label="Nuevo")
filemenu.add_command(label="Abrir")
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


x = np.arange(-3, 3, 0.01)
j = 1
y = np.sin( np.pi*x*j ) / ( np.pi*x*j )
fig = Figure()


ax = fig.add_subplot(111)
#plot a line along points x,y
line, = ax.plot(x, y)

Menup = Frame(root, bg="red")

ventana = Frame(Menup,  bg='gray22',bd=3)
ventana.grid(row=0, column=0, sticky="nsew")

canvas = FigureCanvasTkAgg(fig, master = ventana)
canvas.draw()
canvas.get_tk_widget().pack(padx=5, pady=5 , expand=1, fill='both') 





def raise_frame(frame):
    Collect_Wire.pack_forget()
    Menup.pack_forget()
    frame.pack(fill="both", expand=1)
    
Menup = Frame(root, bg="red")
Menup.pack(fill="both", expand=1)
Collect_Wire = Frame(root, bg="blue")

#Button(Menup, text='Salir', command=salir).pack()
#Button(Menup, text="cambiar", command=lambda:cambiar()).pack()
Button(Menup, text="collect", command=lambda:raise_frame(Collect_Wire)).pack()

Button(Collect_Wire, text="menup", command=lambda:raise_frame(Menup)).pack()

root.mainloop()
