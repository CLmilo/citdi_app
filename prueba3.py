import tkinter
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np

#------------------------------CREAR VENTANA---------------------------------
root = tkinter.Tk()
root.wm_title("Grafica insertada en Tkinter")

frame1 = tkinter.Frame(root)
frame1.grid(row=0, column=0)

frame2 = tkinter.Frame(root)
frame2.grid(row=0, column=1)
#------------------------------CREAR GRAFICA---------------------------------
fig = Figure(figsize=(5, 4), dpi=100)
t = np.arange(0, 3, .01)
y = np.arange(3, 6, .01)
y2 = np.arange(4, 7, .01)
ax = fig.add_subplot(111)
line, = ax.plot(t, y)
line2, = ax.plot(t, y2)

fig2 = Figure(figsize=(5, 4), dpi=100)
t2 = np.arange(0, 3, .01)
y3 = np.arange(3, 6, .01)
y4 = np.arange(4, 7, .01)
ax2 = fig2.add_subplot(111)
line3, = ax2.plot(t2, y3)
#line4, = ax2.plot(t2, y4)

def onclick(event):
    global fig2, line
    fig2.clear()
    ax2 = fig2.add_subplot(111)
    datax = line.get_xdata()
    datay = line.get_ydata()
    datax2 = line.get_xdata()[1]
    datay2 = line.get_ydata()[1]
    line3, = ax2.plot(datax, datay)
    line4, = ax2.plot(datax2, datay2)
    ax2.set_xlim(ax.get_xlim())
    ax2.set_ylim(ax.get_ylim())
    canvas2.draw()
    

canvas = FigureCanvasTkAgg(fig, master=frame1)  # CREAR AREA DE DIBUJO DE TKINTER.
canvas.draw()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
canvas.mpl_connect('motion_notify_event', onclick)

toolbar = NavigationToolbar2Tk(canvas, frame1)# barra de iconos
toolbar.update()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

canvas2 = FigureCanvasTkAgg(fig2, master=frame2)  # CREAR AREA DE DIBUJO DE TKINTER.
canvas2.draw()
canvas2.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

toolbar2 = NavigationToolbar2Tk(canvas2, frame2)# barra de iconos
toolbar2.update()
canvas2.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)


tkinter.mainloop()