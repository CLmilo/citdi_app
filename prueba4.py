from matplotlib.figure import Figure
import numpy as np
from tkinter import Tk, Frame,Button,Label, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk

ventana = Tk()
ventana.geometry('642x535')
ventana.state("zoomed")

Menup = ctk.CTkFrame(ventana)
Collect_Wire = ctk.CTkFrame(ventana)

def raise_frame(frame):
    frame.tkraise()


for frame in (Menup, Collect_Wire):
    frame.grid_rowconfigure(0,weight=1)
    frame.grid_columnconfigure(0,weight=1)
    frame.grid(row=0, column=0, sticky='nsew')

x = np.arange(-3, 3, 0.01)
j = 1
y = np.sin( np.pi*x*j ) / ( np.pi*x*j )
fig = Figure()


ax = fig.add_subplot(111)
#plot a line along points x,y
line, = ax.plot(x, y)

Menup = Frame(ventana,  bg='gray22',bd=3)

canvas = FigureCanvasTkAgg(fig, master = frame)
canvas.draw()
canvas.get_tk_widget().pack(padx=5, pady=5 , expand=1, fill='both') 


def salir():
    frame.destroy()
    Menup.destroy()

def cambiar():
    global x, y
    print(1)
    x = []
    y = []
    fig.clear()
    ax = fig.add_subplot(111)
    x = np.arange(-3, 3, 0.01)
    j = 3
    y = np.sin( np.pi*x*j ) / ( np.pi*x*j )
    line, = ax.plot(x, y)
    canvas.draw()
    print(2)

Button(frame, text='Salir', command=salir).pack()
Button(frame, text="cambiar", command=lambda:cambiar()).pack()


raise_frame(Menup)

ventana.mainloop()
