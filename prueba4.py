from matplotlib.figure import Figure
import numpy as np
from tkinter import Tk, Frame,Button,Label, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

ventana = Tk()
ventana.geometry('642x535')
ventana.wm_title('Grafica Matplotlib Animacion')
ventana.minsize(width=642,height=535)


x = np.arange(-3, 3, 0.01)
j = 1
y = np.sin( np.pi*x*j ) / ( np.pi*x*j )
fig = Figure()


ax = fig.add_subplot(111)
#plot a line along points x,y
line, = ax.plot(x, y)

frame = Frame(ventana,  bg='gray22',bd=3)
frame.pack(expand=1, fill='both')

canvas = FigureCanvasTkAgg(fig, master = frame)
canvas.draw()
canvas.get_tk_widget().pack(padx=5, pady=5 , expand=1, fill='both') 


def salir():
    frame.destroy()
    ventana.destroy()

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

ventana.mainloop()
