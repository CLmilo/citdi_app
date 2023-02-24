from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
from tkinter import *

class App:

    def __init__(self, master):

        self.event_num = 1

        # Create a container
        frame = Frame(master)

        # Create 2 buttons
        self.button_left = Button(frame,text="< Previous Event",
                                    command=self.decrease)
        self.button_left.grid(row=0,column=0)
        self.button_right = Button(frame,text="Next Event >",
                                    command=self.increase)
        self.button_right.grid(row=0,column=1)


        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)

        self.line, = self.ax.plot(self.event_num,self.event_num,'.')


        self.canvas = FigureCanvasTkAgg(self.fig,master=master)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=1,column=0)
        frame.grid(row=0,column=0)

    def decrease(self):
        self.event_num -= 1
        print(self.event_num)
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self.line, = self.ax.plot(self.event_num,self.event_num,'+')
        self.canvas.draw()

    def increase(self):
        self.event_num += 1        
        print(self.event_num)
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self.line, = self.ax.plot(self.event_num,self.event_num,'*')
        self.canvas.draw()
root = Tk()
app = App(root)
root.mainloop()