import tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np

#------------------------------CREAR VENTANA---------------------------------
root = tkinter.Tk()
root.wm_title("Grafica insertada en Tkinter")


#------------------------------CREAR GRAFICA---------------------------------
fig = Figure(figsize=(5, 4), dpi=100)
t = np.arange(0, 3, .01)
ax = fig.add_subplot(111)
line, = ax.plot(t, 2 * np.sin(2 * np.pi * t))

def onclick(event):
    print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
          ('double' if event.dblclick else 'single', event.button,
           event.x, event.y, event.xdata, event.ydata))

canvas = FigureCanvasTkAgg(fig, master=root)  # CREAR AREA DE DIBUJO DE TKINTER.
canvas.draw()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
canvas.mpl_connect('button_press_event', onclick)

#-----------------------AÑADIR BARRA DE HERRAMIENTAS--------------------------
toolbar = NavigationToolbar2Tk(canvas, root)# barra de iconos
toolbar.update()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

#-----------------------------BOTÓN "cerrar"----------------------------------
def cerrar():
    root.quit()     
    root.destroy()

def cambiar():
    j = 5
    t = np.arange(0, 3, .01)
    y2 = 2 * np.sin(j * np.pi * t)
    #update the line with the new data
    line.set_ydata(y2)

button = tkinter.Button(master=root, text="cerrar", command=cerrar)

button2 = tkinter.Button(master=root, text="cambiar_grafica", command=cambiar)

button.pack(side=tkinter.BOTTOM)
button2.pack(side=tkinter.BOTTOM)

tkinter.mainloop()