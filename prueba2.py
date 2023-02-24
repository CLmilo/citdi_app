from tkinter import Tk, Frame,Button,Label, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

fig, ax = plt.subplots(facecolor='#4F406A')
plt.title("Grafica en Tkinter con Matplotlib",color='white',size=16, family="Arial")

ax.tick_params(direction='out', length=6, width=2, 
	colors='white',
    grid_color='r', grid_alpha=0.5)

t = np.arange(0, 3, .01)
line, = ax.plot(t, 2 * np.sin(2 * np.pi * t), color='r', marker='o',
	linewidth=8, markersize=1, markeredgecolor='m')

estado = "cambiar1"

def animate(i):
	global estado 
	if estado == "cambiar1":
		line.set_ydata(5 * np.sin(3 * np.pi * t))
	else:
		line.set_ydata(2 * np.sin(6 * np.pi * t)) 
	return line,

def cambiar1():
	global estado
	estado = "cambiar1"

def cambiar2():
	global estado
	estado = "cambiar2"

def pausar():
	ani.event_source.stop() 

def reanudar():
	ani.event_source.start()

def salir():
    frame.destroy()
    ventana.destroy()

ventana = Tk()
ventana.geometry('642x535')
ventana.wm_title('Grafica Matplotlib Animacion')
ventana.minsize(width=642,height=535)

frame = Frame(ventana,  bg='gray22',bd=3)
frame.pack(expand=1, fill='both')

canvas = FigureCanvasTkAgg(fig, master = frame)  
canvas.get_tk_widget().pack(padx=5, pady=5 , expand=1, fill='both') 

ani = animation.FuncAnimation(fig, animate, 
		interval=30)	 
canvas.draw()


#Button(frame, text='Grafica Datos', width = 15, bg='purple4',fg='white', command=[iniciar]).pack(pady =5,side='left',expand=1)
#Button(frame, text='Pausar', width = 15, bg='salmon',fg='white', command=pausar).pack(pady =5,side='left',expand=1)
#Button(frame, text='Reanudar', width = 15, bg='green',fg='white', command=reanudar).pack(pady =5,side='left',expand=1)
Button(frame, text='cambiar1', command=cambiar1).pack()
Button(frame, text='cambiar2', command=cambiar2).pack()
Button(frame, text='Salir', command=salir).pack()

ventana.mainloop()