import random
import time
from tkinter import *
from datetime import datetime
from tkinter import ttk
from matplotlib import style
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavigationToolbar2TkAgg
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from PIL import Image
from tkinter import filedialog
import os, sys
import serial
import threading
from tkinter import messagebox as MessageBox
import numpy as np
from fpdf import FPDF
import customtkinter as ctk
from BaselineRemoval import BaselineRemoval
import obspy
from obspy.core.trace import Trace

import socket

host = "169.254.159.253"
print(host)
port = 65432
BUFFER_SIZE = 16
MESSAGE = 'Hola, mundo!' # Datos que queremos enviar

port = 65432
BUFFER_SIZE = 16
MESSAGE = 'Hola, mundo!' # Datos que queremos enviar
cont = 0


#colores
azul_oscuro = "#002060"
azul_claro = "#BDD7EE"
azul_celeste = "#2F6CDF"

ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
ctk.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

# Funcionalidades

ruta_data_inicial = ""
cuerpo_ruta = ""
archivo = ""
numero_grafica_actual = 1
archivos_existentes = []
frecuencia_muestreo = [50]
orden_sensores = []
pile_area = 10
EM_valor_original = 10
ET_valor_original = 981
ruta_guardado = ""
ruta_guardado_pdf = ""
L_T_Grafico = ""

F1 = []
F2 = []
F = []
V1 = []
V2 = []
V = []
E = []
D1 = []
D2 = []
D = []
V_Transformado = []
V_Transformado_valor_real = []


contador_grafica_arriba = 1
contador_grafica_abajo = 1



def detrend(trace,type=0):
    st = trace.copy()
    if type == 0:
        st.detrend(type = "constant")
    elif type == 1:
        st.detrend(type = "linear")
    elif type == 2:
        st.detrend(type = "polynomial", order = 2)
    elif type == 3:
        st.detrend(type = "polynomial", order = 3)
    elif type == 4:
        st.detrend(type = "spline", order = 2, dspline = 1000)
    
    return st

def filtered(stream, type, f1, f2):
    st = stream.copy()
    if type == 0:
        st.filter(type= "bandpass",freqmin=f1,freqmax=f2)
    elif type == 1:
        st.filter(type= "bandstop",freqmin=f1,freqmax=f2)
    elif type == 2:
        st.filter(type= "lowpass",freq=f1)
    elif type == 3:
        st.filter(type= "highpass",freq=f1)
    return st

def correcion_linea_cero(valores):
    z = []
    tr = Trace(data=np.array(valores))
    st2 = detrend(tr,type = 2)
    z = np.ndarray.tolist(st2.data)
    return z

def correcion_linea_cero2(valores):
    z = []
    tr = Trace(data=np.array(valores))
    st2 = detrend(tr,type = 1)
    z = np.ndarray.tolist(st2.data)
    return z

def filtrado(valores):
    z = []
    tr = Trace(data=np.array(valores))
    st3 = tr.copy()
    #st3.filter(type="bandpass",freqmin=0.012,freqmax = 0.032)
    st3.filter(type="bandpass",freqmin=0.0000000012,freqmax = 0.5)
    z = np.ndarray.tolist(st3.data)
    return z

def filtrado2(valores):
    z = []
    tr = Trace(data=np.array(valores))
    st3 = tr.copy()
    st3.filter(type="bandpass",freqmin=0.00012,freqmax = 0.5)
    z = np.ndarray.tolist(st3.data)
    return z

def velocidad(valores):
    z = []
    tr = Trace(data=np.array(valores))
    st3 = tr.copy()
    st3.integrate(method = "cumtrapz")
    
    z = np.ndarray.tolist(st3.data)

    return z

def filtrado_velocidad(valores):
    z = np.array(valores)
    baseObj = BaselineRemoval(z)
    zh = baseObj.ZhangFit()
    #zh = baseObj.IModPoly(3)
    return zh

matriz_data_archivos = []

def browseFiles():
    global ruta_data_inicial, contador_grafica_abajo, contador_grafica_arriba, matriz_data_archivos, orden_sensores
    print("esta es la ruta inicial: ", ruta_data_inicial)
    matriz_data_archivos = []
    ruta_data_inicial = filedialog.askopenfilename(initialdir = "/", title = "Select a File", filetypes = [("Text files", "*.ct")])   
    numero_grafica_actual = 1
    try:
        with open(ruta_data_inicial, "r") as file:
            lineas = file.readlines()
            matriz_data_archivos.append(str(lineas[0]).replace("\n", ""))
            vector = []
            estado = "noleyendo"
            j = 0
            for i in range(1,len(lineas)):
                linea = str(lineas[i]).replace("\n", "")
                if linea == 'INICIO_ARCHIVO':
                    estado = "leyendo"
                elif linea == 'FIN_ARCHIVO':
                    estado = "finalizado"
                if estado == "leyendo":
                    if j == 1:
                        n_archivo = linea[8:]
                    if j == 2:
                        orden_sensores.append(linea)
                    if j > 2:
                        vector.append(linea)
                    j += 1    
                if estado == "finalizado":
                    if vector != []:
                        matriz_data_archivos.append(vector)
                    vector = []
                    j = 0
    except:
        print("error2")            
    contador_grafica_arriba = 1
    contador_grafica_abajo = 1


x_zoom_grafica_arriba_1 = 0
x_zoom_grafica_arriba_2 = 0
y_zoom_grafica_arriba_1 = 0
y_zoom_grafica_arriba_2 = 0
x_zoom_grafica_abajo_1 = 0
x_zoom_grafica_abajo_2 = 0
y_zoom_grafica_abajo_1 = 0
y_zoom_grafica_abajo_2 = 0

dic_posicion_zoom = {'arriba':[x_zoom_grafica_arriba_1, x_zoom_grafica_arriba_2, y_zoom_grafica_arriba_1, y_zoom_grafica_arriba_2], 'abajo':[x_zoom_grafica_abajo_1, x_zoom_grafica_abajo_2, y_zoom_grafica_abajo_1, y_zoom_grafica_abajo_2]}

def on_xlims_change_arriba(event_ax):
    dic_posicion_zoom['arriba'][0], dic_posicion_zoom['arriba'][1] = event_ax.get_xlim()

def on_ylims_change_arriba(event_ax):
    dic_posicion_zoom['arriba'][2], dic_posicion_zoom['arriba'][3] = event_ax.get_ylim()

def on_xlims_change_abajo(event_ax):
    dic_posicion_zoom['abajo'][0], dic_posicion_zoom['abajo'][1] = event_ax.get_xlim()

def on_ylims_change_abajo(event_ax):
    dic_posicion_zoom['abajo'][2], dic_posicion_zoom['abajo'][3] = event_ax.get_ylim()

# Posiciones

posx = 0
posy = 0

def posicion_mouse(event):
    global posx, posy
    posx = event.x
    posy = event.y
    print ("clicked at", event.x, event.y)

ultima_grafica_seleccionada = "arriba"
ultima_magnitud_arriba = "aceleracion"
ultima_magnitud_abajo = "deformacion"


def click_grafica_arriba(event):
    global ultima_grafica_seleccionada, Boton_seleccion_grafica1, Boton_seleccion_grafica2
    ultima_grafica_seleccionada = "arriba"
    Boton_seleccion_grafica1.configure(bg="Green")
    Boton_seleccion_grafica2.configure(bg='#CACFD2')

def click_grafica_abajo(event):
    global ultima_grafica_seleccionada, Boton_seleccion_grafica1, Boton_seleccion_grafica2
    ultima_grafica_seleccionada = "abajo"
    Boton_seleccion_grafica2.configure(bg="Green")
    Boton_seleccion_grafica1.configure(bg='#CACFD2')


def Obtencion_data_serial(num):
    global frecuencia_muestreo, matriz_data_archivos, pile_area, EM_valor_original, ET_valor_original, segundo_final, segundo_inicial
    global orden_sensores
    global S1, S2, A3, A4
    segundos = []
    S1 = []
    S2 = []
    A3 = []
    A4 = []
    SIN1 = []
    SIN2 = []
    SIN3 = []
    SIN4 = []
    NULL = []

    #print("El orden de los sensores es: ", matriz_data_archivos[0])

    try:
        print("lo que hay en la matriz_data_archivos es ", num,  matriz_data_archivos[num][0], "separacion",  matriz_data_archivos[num][1], len(matriz_data_archivos[num]))
    except:
        print("no se guarda ninguna gráfica 1 todavía")

    dic_orden_sensores = {"1":A3, "2":A4, "3":S1, "4":S2, "5":S1, "6":S2, "0":NULL}
    dic_orden_sensores2 = {"1":SIN1, "2":SIN2, "3":SIN3, "4":SIN4, "5":SIN3, "6":SIN4, "0": NULL}

    orden = str(orden_sensores[-1]).replace(" ","").split("|")
    print("la fila orden es", orden_sensores[-1])

    if len(orden[4])>1:
        frecuencia_muestreo.append(orden[4])

    try:
        pile_area = orden[5]
    except:
        pile_area = "15.6"
    try:
        EM_valor_original = orden[6]
    except:
        EM_valor_original = "207000"

    try:
        ET_valor_original = orden[7]
    except:
        ET_valor_original = 981
    print(1)
    
    for index,linea in enumerate(matriz_data_archivos[num]):
        linea = linea.split("|")
        if index > 0 and index < len(matriz_data_archivos[num])-1:
            segundos.append(float(linea[0])/1000)

            for i in range(4):
                #dic_orden_sensores2[orden[i]].append(float(linea[i+1])*dic_factor_conversion_producto[orden[i]]+dic_factor_conversion_suma[orden[i]])
                dic_orden_sensores2[orden[i]].append(float(linea[i+1]))
        else:
            pass
    segundo_inicial = segundos[0]
    segundo_final = segundos[-1]

    print(2)

    for i in range(4):

        if ((int(orden[i]) == 1)) or (int(orden[i]) == 2):
            print('corregidos')
            for datos in filtrado(correcion_linea_cero(dic_orden_sensores2[orden[i]])):
                dic_orden_sensores[orden[i]].append(datos)
        elif (int(orden[i])!=0):
            print('sin corregir')
            for datos in filtrado2(correcion_linea_cero2(dic_orden_sensores2[orden[i]])):               
                dic_orden_sensores[orden[i]].append(datos)

    return segundos, S1, S2, A3, A4 

# Interfaz

def raise_frame(frame):
    frame.tkraise()

#root = Tk()
root = ctk.CTk()        

#root.state('zoomed')
root.attributes('-fullscreen',True)
root.resizable(0,0)
root.grid_rowconfigure(0,  weight=1)
root.grid_columnconfigure(0, weight=1)

#Menup = Frame(root)
Review = Frame(root)
Menup = ctk.CTkFrame(root)
Collect_Wire = Frame(root)
Opciones = Frame(root)
Export = Frame(root)
About = Frame(root)

for frame in (Menup, Review, Collect_Wire, Opciones, Export, About):
    frame.grid_rowconfigure(0,weight=1)
    frame.grid_columnconfigure(0,weight=1)
    frame.grid(row=0, column=0, sticky='nsew')

# FRAME INICIAL
container4a = ctk.CTkFrame(master= Menup, corner_radius = 20)

container4a.grid_rowconfigure(0, weight=1)
container4a.grid_rowconfigure(1, weight=1)
container4a.grid_columnconfigure(0, weight=1)
container4a.grid(row=0, column=0, sticky='nsew', padx=40, pady=40)

container4b = ctk.CTkFrame(container4a, corner_radius=20)
container4b.grid(row=0, column=0, sticky='nsew', padx=40, pady=(40,0))

container4b.grid_rowconfigure(0, weight=10)
container4b.grid_rowconfigure(1, weight=2)
container4b.grid_columnconfigure(0, weight=1)
container4b.grid_columnconfigure(0, weight=1)


container4c = ctk.CTkFrame(container4a, corner_radius=10)
container4c.grid(row=1, column=0, sticky='nsew', padx=40, pady=(20,40))
container4c.grid_rowconfigure(0, weight=1)
container4c.grid_columnconfigure(0, weight=1)
container4c.grid_columnconfigure(1, weight=1)
container4c.grid_columnconfigure(2, weight=1)
container4c.grid_columnconfigure(3, weight=1)
container4c.grid_columnconfigure(4, weight=1)
container4c.grid_columnconfigure(5, weight=1)

# Botones
lista_botones = ["Salir", "Review", "Settings", "Collet Wire", "Manual", "About"]

#Button(container4, text=lista_botones[0], bg=azul_oscuro, font=('Arial', 25), fg='#FFFFFF',command=lambda:root.destroy()).grid(row=4,column=0, sticky='nsew')
ctk.CTkButton(container4c, text=lista_botones[0], font=('Arial', 25), command=lambda:root.destroy()).grid(row=0,column=0, sticky='nsew', padx=5, pady=5)
ctk.CTkButton(container4c, text=lista_botones[1], font=('Arial', 25), command=lambda:[browseFiles(), Creacion_Grafica("arriba","aceleracion", numero_grafica_actual, "original", "NO", "NO"), Creacion_Grafica("abajo", "deformacion", numero_grafica_actual, "original", "NO", "NO"), eliminar_columna_muestreo(), raise_frame(Review)]).grid(row=0,column=1, sticky='nsew', pady=5, padx=(0,5))
ctk.CTkButton(container4c, text=lista_botones[2], font=('Arial', 25), command=lambda:print("settings")).grid(row=0,column=2, sticky='nsew', pady=5, padx=(0,5))
ctk.CTkButton(container4c, text=lista_botones[3], font=('Arial', 25), command=lambda:[raise_frame(Collect_Wire)]).grid(row=0,column=3, sticky='nsew', pady=5, padx=(0,5))
ctk.CTkButton(container4c, text=lista_botones[4], font=('Arial', 25), command=lambda:print("manual")).grid(row=0,column=4, sticky='nsew', pady=5, padx=(0,5))
ctk.CTkButton(container4c, text=lista_botones[5], font=('Arial', 25), command=lambda:raise_frame(About)).grid(row=0,column=5, sticky='nsew', pady=5, padx=(0,5))

# Mostrar Hora
def Obtener_hora_actual():
    return datetime.now().strftime("%d-%m-%y,%H:%M:%S")

def refrescar_reloj():
    hora_actual.set(Obtener_hora_actual())
    container4b.after(300, refrescar_reloj)

hora_actual = StringVar(container4b, value=Obtener_hora_actual())

ctk.CTkLabel(container4b, textvariable=hora_actual, font=('Arial', 25)).grid(row=2, column=0, sticky='nsw', padx= 20, pady=20)

refrescar_reloj()

# AÑADIR PORTADA

#img.convert("RGB")

def resolver_ruta(ruta_relativa):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, ruta_relativa)
    return os.path.join(os.path.abspath('.'), ruta_relativa)

nombre_archivo_portada = resolver_ruta("CITDI_LOGO.png")



imagen = PhotoImage(file=nombre_archivo_portada)
imagen = imagen.subsample(3)

ctk.CTkLabel(container4b, image=imagen, text="").grid(row=0,column=1, padx=40, pady=40)

ctk.CTkLabel(container4b, font=('Arial', 100), text="Kallpa Processor").grid(row=0, column=0, sticky='nsw', padx=(40,0), pady=20)


# FRAME DE OPERACIONES

container = Frame(Review, bg='green')
container.grid(row=0, column=0, sticky='nsew')

container.grid_rowconfigure(0,weight=1)
container.grid_columnconfigure(0, weight=1)
container.grid_columnconfigure(1, weight=20)
container.grid_columnconfigure(2, weight=1)


#---------------------------------------------------------------
# Frame de la izquierda

container1 = Frame(container, bg=azul_claro)
container1.grid(row=0, column=0, sticky='nsew')
#container1.grid_rowconfigure(0, weight=1)
#container1.grid_rowconfigure(1, weight=1)
container1.grid_columnconfigure(0, weight=1)

# Frames internos

container1_0 = Frame(container1, bg=azul_oscuro)
container1_0.grid(row=0, column=0, padx=20, pady=(40,0), sticky='new')

Button(container1_0, text='Regresar', command=lambda:raise_frame(Menup)).grid(row=0,column=0, sticky='nsew')

container1_1 = Frame(container1, bg=azul_oscuro)
container1_1.grid(row=1, column=0, padx=20, pady=(0,10), sticky='new')
container1_1.grid_columnconfigure(0, weight=1)
container1_1.grid_columnconfigure(1, weight=1)

container1_2 = Frame(container1, bg=azul_oscuro)
container1_2.grid(row=2, column=0, padx=20, pady=10, sticky='new')
container1_2.grid_columnconfigure(0, weight=1)
container1_2.grid_columnconfigure(1, weight=1)

# Textos y Entrys Primer Frame
#textos_primer_frame = ["Pile ID", "Total Length(m)", "Pile Length(m)", "Penetration(m)", "Pile Area(m^2)", "Wave Speed(m/s)", "Overall WS(m/s)", "Density(m^3)", "Elastic Modulus(GPa)", "Jc" ]
textos_primer_frame = ["Pile Area(cm^2)", "Elastic Modulus(MPa)", "Energía Teórica(J)"]

#ET_Entry

Label(container1_1, text=textos_primer_frame[0], bg=azul_oscuro, fg='#FFFFFF').grid(row=0,column=0, padx=10, pady=10, sticky='nw')
pile_area_label = Label(container1_1, text=str(round(float(pile_area),2)), bg='#D9D9D9', fg='black')
pile_area_label.grid(row=0, column=1, padx=10, pady=10, sticky='new')
Label(container1_1, text=textos_primer_frame[1], bg=azul_oscuro, fg='#FFFFFF').grid(row=1,column=0, padx=10, pady=10, sticky='nw') 
EM_label = Label(container1_1, text=str(round(float(EM_valor_original),2)), bg='#D9D9D9', fg='black')
EM_label.grid(row=1, column=1, padx=10, pady=10, sticky='new')
Label(container1_1, text=textos_primer_frame[2], bg=azul_oscuro, fg='#FFFFFF').grid(row=2,column=0, padx=10, pady=10, sticky='nw')
ET_label = Label(container1_1, text=str("0"), bg='#D9D9D9', fg='black')
ET_label.grid(row=2, column=1, padx=10, pady=10, sticky='new')



# Textos y Entrys Segundo Frame
#textos_segundo_frame = ["BL #", "RSP(kN)", "RMX(kN)", "RSU(kN)", "FMX(kN)", "VMX(m/s)", "EMX(kN.m)", "DMX(mm)", "DFN(mm)", "CSX(MPa)", "TSX(MPa)", "BTA"]

Label_Num_Grafica = Label(container1_2, text="", bg=azul_oscuro, fg='#FFFFFF')
Label_Num_Grafica.grid(row=0,column=0, columnspan=2, padx=10, pady=10, sticky='new') 

textos_segundo_frame = ["FMX(kN)", "VMX(m/s)", "EMX(J)", "DMX(cm)", "ETR", "CE"]
valores_segundo_frame_arriba = ["","", "", "", "", "", ""]
valores_segundo_frame_abajo = ["","", "", "", "", "", ""]

Label(container1_2, text=textos_segundo_frame[0], bg=azul_oscuro, fg='#FFFFFF').grid(row=1,column=0, padx=10, pady=10, sticky='nw') 
L_FMX = Label(container1_2, text=valores_segundo_frame_arriba[0], bg='#D9D9D9', fg='black')
L_FMX.grid(row=1, column=1,padx=10, pady=10, sticky='nwe')
Label(container1_2, text=textos_segundo_frame[1], bg=azul_oscuro, fg='#FFFFFF').grid(row=2,column=0, padx=10, pady=10, sticky='nw') 
L_VMX = Label(container1_2, text=valores_segundo_frame_arriba[1], bg='#D9D9D9', fg='black')
L_VMX.grid(row=2, column=1,padx=10, pady=10, sticky='nwe')
Label(container1_2, text=textos_segundo_frame[2], bg=azul_oscuro, fg='#FFFFFF').grid(row=3,column=0, padx=10, pady=10, sticky='nw') 
L_EMX = Label(container1_2, text=valores_segundo_frame_arriba[2], bg='#D9D9D9', fg='black')
L_EMX.grid(row=3, column=1,padx=10, pady=10, sticky='nwe')
Label(container1_2, text=textos_segundo_frame[3], bg=azul_oscuro, fg='#FFFFFF').grid(row=4,column=0, padx=10, pady=10, sticky='nw') 
L_DMX = Label(container1_2, text=valores_segundo_frame_arriba[3], bg='#D9D9D9', fg='black')
L_DMX.grid(row=4, column=1,padx=10, pady=10, sticky='nwe')  
Label(container1_2, text=textos_segundo_frame[4], bg=azul_oscuro, fg='#FFFFFF').grid(row=5,column=0, padx=10, pady=10, sticky='nw') 
L_ETR = Label(container1_2, text=valores_segundo_frame_arriba[4], bg='#D9D9D9', fg='black')
L_ETR.grid(row=5, column=1,padx=10, pady=10, sticky='nwe')
Label(container1_2, text=textos_segundo_frame[5], bg=azul_oscuro, fg='#FFFFFF').grid(row=6,column=0, padx=10, pady=10, sticky='nw') 
L_CE = Label(container1_2, text=valores_segundo_frame_arriba[5], bg='#D9D9D9', fg='black')
L_CE.grid(row=6, column=1,padx=10, pady=10, sticky='nwe')  

def modificar_datos_segundo_frame(posicion,texto_label_num_grafica, V_FMX, V_VMX, V_EMX, V_DMX, V_ETR, V_CE):
    global valores_segundo_frame_arriba, valores_segundo_frame_abajo
    global Label_Num_Grafica
    global L_FMX, L_VMX, L_EMX, L_DMX, L_ETR, L_CE
    Label_Num_Grafica.config(text= str(texto_label_num_grafica), font=('Times', 15))
    L_FMX.config(text = str(V_FMX))
    L_VMX.config(text = str(V_VMX))
    L_EMX.config(text = str(V_EMX))
    L_DMX.config(text = str(V_DMX))
    L_ETR.config(text = str(V_ETR))
    L_CE.config(text = str(V_CE))
    if posicion == 'arriba':
        valores_segundo_frame_arriba = [texto_label_num_grafica, V_FMX, V_VMX, V_EMX, V_DMX, V_ETR, V_CE]
    else:
        valores_segundo_frame_abajo = [texto_label_num_grafica, V_FMX, V_VMX, V_EMX, V_DMX, V_ETR, V_CE]

#--------------------------------------------------
# Frame Principal del medio
container2 = Frame(container, bg=azul_oscuro)
container2.grid_columnconfigure(0, weight=15)
container2.grid_columnconfigure(1, weight=1)
container2.grid_rowconfigure(0, weight=1)
container2.grid_rowconfigure(1, weight=1)

container2.grid(row=0,column=1, sticky='nsew')


# rectangulos principales

# frame de arriba
container2_1 = Frame(container2, bg=azul_oscuro)
container2_1.grid_columnconfigure(0, weight=1)
container2_1.grid_rowconfigure(0, minsize=25 ,weight=1)
container2_1.grid_rowconfigure(1, weight=1)
container2_1.grid_rowconfigure(2, minsize=25, weight=1)
container2_1.grid(row=0, column=0, padx=10, pady=(10,5), sticky='new')

container2_1_1 = Frame(container2_1)
container2_1_1.grid(row=0, column=0, sticky='new')
for i in range(8):
    container2_1_1.grid_rowconfigure(i, weight=1)

container2_1_2 = Frame(container2_1)
container2_1_2.grid(row=1, column=0, sticky='nsew')
container2_1_3 = Frame(container2_1, bg='White')
container2_1_3.grid(row=2, column=0, sticky='nsew')

container2_1_3.grid_rowconfigure(0, weight=1)
container2_1_3.grid_propagate(False)
container2_1_3.grid_columnconfigure(0, weight=250)
container2_1_3.grid_columnconfigure(1, weight=1)
container2_1_3.grid_columnconfigure(2, weight=1)

container2_1_3_1 = Frame(container2_1_3)
container2_1_3_1.grid(row=0, column=0, sticky='w')

container2_1_3_2 = Frame(container2_1_3, bg='White')
container2_1_3_2.grid(row=0, column=1, sticky='e')

container2_1_3_3 = Frame(container2_1_3, bg='White')
container2_1_3_3.grid(row=0, column=2, sticky='e')
container2_1_3_3.grid_columnconfigure(0, weight=1)
container2_1_3_3.grid_columnconfigure(1, weight=1)
container2_1_3_3.grid_columnconfigure(2, weight=1)
container2_1_3_3.grid_columnconfigure(3, weight=1)

# frame de abajo
container2_2 = Frame(container2, bg=azul_oscuro)
container2_2.grid_columnconfigure(0, weight=1)
container2_2.grid_rowconfigure(0, minsize=25, weight=1)
container2_2.grid_rowconfigure(1, weight=1)
container2_2.grid_rowconfigure(2, minsize=25, weight=1)
container2_2.grid(row=1, column=0, padx=10, pady=(5,10), sticky='new')

container2_2_1 = Frame(container2_2)
container2_2_1.grid(row=0, column=0, sticky='new')
for i in range(8):
    container2_2_1.grid_rowconfigure(i, weight=1)


container2_2_2 = Frame(container2_2)
container2_2_2.grid(row=1, column=0, sticky='nsew')
container2_2_3 = Frame(container2_2, bg='White')
container2_2_3.grid(row=2, column=0, sticky='nsew')

container2_2_3.grid_rowconfigure(0, weight=1)
container2_2_3.grid_propagate(False)
container2_2_3.grid_columnconfigure(0, weight=250)
container2_2_3.grid_columnconfigure(1, weight=1)
container2_2_3.grid_columnconfigure(2, weight=1)

container2_2_3_1 = Frame(container2_2_3)
container2_2_3_1.grid(row=0, column=0, sticky='sw')

container2_2_3_2 = Frame(container2_2_3, bg='White')
container2_2_3_2.grid(row=0, column=1, sticky='e')

container2_2_3_3 = Frame(container2_2_3, bg='White')
container2_2_3_3.grid(row=0, column=2, sticky='e')
container2_2_3_3.grid_columnconfigure(0, weight=1)
container2_2_3_3.grid_columnconfigure(1, weight=1)
container2_2_3_3.grid_columnconfigure(2, weight=1)
container2_2_3_3.grid_columnconfigure(3, weight=1)

# botones de los frames

dic_magnitud_botones = {0:'aceleracion', 1:'velocidad', 2:'deformacion', 3:'fuerza', 4:'desplazamiento', 5:'fuerzaxvelocidad', 6:'avged'}
dic_ultima_grafica_magnitud = {"arriba": ultima_magnitud_arriba, "abajo": ultima_magnitud_abajo}

def actualizar_magnitud(posicion,i):
    global ultima_magnitud_abajo
    global ultima_magnitud_arriba
    dic_ultima_grafica_magnitud[posicion] = dic_magnitud_botones[i]

texto_botones_frame= ["ACELERACIÓN", "VELOCIDAD", "DEFORMACIÓN", "FUERZA", "DESPLAZAMIENTO", "F vs V", "Avg ED"]

for i in range(len(texto_botones_frame)):
    container2_1_1.grid_columnconfigure(i, weight=1)
    container2_2_1.grid_columnconfigure(i, weight=1)
    
# Estos botones están fuera de un bucle for por usar una función lambda dentro de sus comandos, los cuales dan i como 3 siempre que se ejecutan

Button(container2_1_1, text=texto_botones_frame[0], bg=azul_claro, fg='#000000', command=lambda: [cambiar_magnitud_grafica("arriba", 0), actualizar_magnitud("arriba", 0)]).grid(row=0,column=0, sticky='nsew')
Button(container2_1_1, text=texto_botones_frame[1], bg=azul_claro, fg='#000000', command=lambda: [cambiar_magnitud_grafica("arriba", 1), actualizar_magnitud("arriba", 1)]).grid(row=0,column=1, sticky='nsew') 
Button(container2_1_1, text=texto_botones_frame[2], bg=azul_claro, fg='#000000', command=lambda: [cambiar_magnitud_grafica("arriba", 2), actualizar_magnitud("arriba", 2)]).grid(row=0,column=2, sticky='nsew') 
Button(container2_1_1, text=texto_botones_frame[3], bg=azul_claro, fg='#000000', command=lambda: [cambiar_magnitud_grafica("arriba", 3), actualizar_magnitud("arriba", 3)]).grid(row=0,column=3, sticky='nsew') 
Button(container2_1_1, text=texto_botones_frame[4], bg=azul_claro, fg='#000000', command=lambda: [cambiar_magnitud_grafica("arriba", 4), actualizar_magnitud("arriba", 4)]).grid(row=0,column=4, sticky='nsew') 
Button(container2_1_1, text=texto_botones_frame[5], bg=azul_claro, fg='#000000', command=lambda: [cambiar_magnitud_grafica("arriba", 5), actualizar_magnitud("arriba", 5)]).grid(row=0,column=5, sticky='nsew') 
Button(container2_1_1, text=texto_botones_frame[6], bg=azul_claro, fg='#000000', command=lambda: [cambiar_magnitud_grafica("arriba", 6), actualizar_magnitud("arriba", 6)]).grid(row=0,column=6, sticky='nsew') 
Boton_seleccion_grafica1 = Button(container2_1_1, text="O", bg='Green', fg='#000000', command=lambda: colorear_botones_seleccion_grafica(1))
Boton_seleccion_grafica1.grid(row=0,column=7, sticky='nsew') 


Button(container2_2_1, text=texto_botones_frame[0], bg=azul_claro, fg='#000000', command=lambda: [cambiar_magnitud_grafica("abajo", 0), actualizar_magnitud("abajo", 0)]).grid(row=0,column=0, sticky='nsew')
Button(container2_2_1, text=texto_botones_frame[1], bg=azul_claro, fg='#000000', command=lambda: [cambiar_magnitud_grafica("abajo", 1), actualizar_magnitud("abajo", 1)]).grid(row=0,column=1, sticky='nsew') 
Button(container2_2_1, text=texto_botones_frame[2], bg=azul_claro, fg='#000000', command=lambda: [cambiar_magnitud_grafica("abajo", 2), actualizar_magnitud("abajo", 2)]).grid(row=0,column=2, sticky='nsew') 
Button(container2_2_1, text=texto_botones_frame[3], bg=azul_claro, fg='#000000', command=lambda: [cambiar_magnitud_grafica("abajo", 3), actualizar_magnitud("abajo", 3)]).grid(row=0,column=3, sticky='nsew') 
Button(container2_2_1, text=texto_botones_frame[4], bg=azul_claro, fg='#000000', command=lambda: [cambiar_magnitud_grafica("abajo", 4), actualizar_magnitud("abajo", 4)]).grid(row=0,column=4, sticky='nsew') 
Button(container2_2_1, text=texto_botones_frame[5], bg=azul_claro, fg='#000000', command=lambda: [cambiar_magnitud_grafica("abajo", 5), actualizar_magnitud("abajo", 5)]).grid(row=0,column=5, sticky='nsew')
Button(container2_2_1, text=texto_botones_frame[6], bg=azul_claro, fg='#000000', command=lambda: [cambiar_magnitud_grafica("abajo", 6), actualizar_magnitud("abajo", 6)]).grid(row=0,column=6, sticky='nsew')  
Boton_seleccion_grafica2 = Button(container2_2_1, text="O", bg='#CACFD2', fg='#000000', command=lambda: colorear_botones_seleccion_grafica(2))
Boton_seleccion_grafica2.grid(row=0,column=7, sticky='nsew') 

def colorear_botones_seleccion_grafica(num):
    global ultima_grafica_seleccionada, Boton_seleccion_grafica2, Boton_seleccion_grafica1, valores_segundo_frame_arriba, valores_segundo_frame_abajo
    
    if num == 1:
        ultima_grafica_seleccionada = 'arriba'
        Boton_seleccion_grafica1.configure(bg="Green")
        Boton_seleccion_grafica2.configure(bg='#CACFD2')
        v_vec = valores_segundo_frame_arriba.copy()
        modificar_datos_segundo_frame('arriba', v_vec[0], v_vec[1], v_vec[2], v_vec[3], v_vec[4], v_vec[5], v_vec[6])
    else:
        ultima_grafica_seleccionada = 'abajo'
        Boton_seleccion_grafica1.configure(bg="#CACFD2")
        Boton_seleccion_grafica2.configure(bg='Green')
        v_vec = valores_segundo_frame_abajo.copy()
        modificar_datos_segundo_frame('abajo',  v_vec[0], v_vec[1], v_vec[2], v_vec[3], v_vec[4], v_vec[5], v_vec[6])


# cambiar magnitudes

def cambiar_magnitud_grafica(posicion,magnitud):

    if magnitud == 6:
        Creacion_Grafica(posicion, dic_magnitud_botones[magnitud], 1, "original", "NO", "SI")

    else:
        Creacion_Grafica(posicion, dic_magnitud_botones[magnitud], 1, "original", "NO", "NO")

dic_posicion = {"arriba":[container2_1_2, container2_1_3_1, container2_1_3_2, container2_1_3_3], "abajo":[container2_2_2, container2_2_3_1, container2_2_3_2, container2_2_3_3]}

def clear_container(posicion):
    for container in dic_posicion[posicion]:
        list = container.pack_slaves()
        for l in list:
            l.destroy()

desplazado_arriba = 0
desplazado_abajo = 0

p_primera_marca = 0.0
p_segunda_marca = 0.0



def moverlimite(posicion, magnitud, num, direccion, mantener_relacion_aspecto, mantener_limites, ind_limite, direccion_limite):
    global p_primera_marca, p_segunda_marca, frecuencia_muestreo
    dic_suma_limite = {'izquierda':-1/(int(frecuencia_muestreo[-1])), 'derecha':1/(int(frecuencia_muestreo[-1]))}

    print("p_primera_marca:", p_primera_marca, "p_segunda_marca:", p_segunda_marca)
    if ind_limite == '1':
        p_primera_marca += dic_suma_limite[direccion_limite]
    if ind_limite == '2':
        p_segunda_marca += dic_suma_limite[direccion_limite]
    print("p_primera_marca:", p_primera_marca, "p_segunda_marca:", p_segunda_marca)
    print("estoy moviendo los límites creando la siguiente gráfica: ", posicion, magnitud, num, direccion, mantener_relacion_aspecto, mantener_limites, p_primera_marca, p_segunda_marca)
    Creacion_Grafica(posicion, magnitud, num, direccion, mantener_relacion_aspecto, mantener_limites, p_primera_marca, p_segunda_marca)
    

def Creacion_Grafica(posicion, magnitud, num, direccion, mantener_relacion_aspecto, mantener_limites, a_primera_marca=0, a_segunda_marca=0):
    global frecuencia_muestreo, pile_area, EM_valor_original, ET_valor_original
    
    global x_zoom_grafica_abajo, y_zoom_grafica_abajo, x_zoom_grafica_arriba, y_zoom_grafica_arriba, L_T_Grafico
    global p_primera_marca, p_segunda_marca, segundo_inicial, segundo_final, Label_Num_Grafica
    F1 = []
    F2 = []
    F = []
    V1 = []
    V2 = []
    V = []
    E = []
    D1 = []
    D2 = []
    D = []
    V_Transformado = []
    V_Transformado_valor_real = []
    
    global L_EMX, L_FMX, L_VMX, L_DMX, L_CE, L_ETR, LIM_IZQ, LIM_DER
    clear_container(posicion)
    global desplazado_arriba, desplazado_abajo
    
    style.use('ggplot')
    f = Figure(figsize=(5,5), dpi=100)
    a = f.add_subplot(111)
    print("el gráfico que se hace es ", num)
    segundos, S1, S2, A3, A4 = Obtencion_data_serial(num)
    Z = 0
    EM = float(EM_valor_original)
    AR = float(pile_area)
    factor = EM*AR
    longitud = max(len(S1), len(S2))
    m1 = 0
    m2 = 0
    for i in range(longitud):
        try:
            m1 = S1[i]*factor/10000000
        except:
            pass
        try:
            m2 = S2[i]*factor/10000000
        except:
            pass
        promedio = (m1+m2)/2
        if S1 != []:
            F1.append(m1)
        if S2 != []:
            F2.append(m2)
        F.append(promedio)
    if S1 == []:
        F = F2
    elif S2 == []:
        F = F1
    Fmax = round(max(F), 2)
    Fmax_original = max(F)
    
    suma_velocidadv1 = 0
    suma_velocidadv2 = 0
    longitud = max(len(A3), len(A4))
    for i in range(longitud):
        try:
            if i == 0:
                suma_velocidadv1 += ((A3[i]+0)*9.81)*(1/(int(frecuencia_muestreo[-1])*1000))/2
            else:
                suma_velocidadv1 += ((A3[i]+A3[i-1])*9.81)*(1/(int(frecuencia_muestreo[-1])*1000))/2
            V1.append(suma_velocidadv1)
        except:
            pass

        try:
            if i == 0:
                suma_velocidadv2 += ((A4[i]+0)*9.81)*(1/(int(frecuencia_muestreo[-1])*1000))/2
            else:
                suma_velocidadv2 += ((A4[i]+A4[i-1])*9.81)*(1/(int(frecuencia_muestreo[-1])*1000))/2
            V2.append(suma_velocidadv2)
        except:
            pass
        promedio = (suma_velocidadv1 + suma_velocidadv2)/2
        V.append(promedio)
    if A3 == []:
        V = V2
    elif A4 == []:
        V = V1
        
    Vmax = round(max(V), 2)

    Vmax_original = max(V)

    suma_desplazamientov1 = 0
    suma_desplazamientov2 = 0
    longitud = max(len(S1), len(S2))
    for i in range(longitud):
        try:
            if i == 0:
                suma_desplazamientov1 += ((V1[i]+0)*9.81)*(1/(int(frecuencia_muestreo[-1])*1000))/2
            else:
                suma_desplazamientov1 += ((V1[i]+V1[i-1])*9.81)*(1/(int(frecuencia_muestreo[-1])*1000))/2
            D1.append(suma_desplazamientov1)
        except:
            pass
        try:
            if i == 0:
                suma_desplazamientov2 += ((V2[i]+0)*9.81)*(1/(int(frecuencia_muestreo[-1])*1000))/2
            else:
                suma_desplazamientov2 += ((V2[i]+V2[i-1])*9.81)*(1/(int(frecuencia_muestreo[-1])*1000))/2
            D2.append(suma_desplazamientov2)
        except:
            pass
        promedio = (suma_desplazamientov1 + suma_desplazamientov2)/2
        D.append(promedio)
    if V1 == []:
        D = D2
    elif V2 == []:
        D = D1
    
    Dmax = round(max(D), 2)
    
    ajuste = 0
   
    Z = Fmax_original/Vmax_original

    imax = F.index(Fmax_original)
    ajuste = V.index(Vmax_original)-imax
    #primera_marca = segundos[imax]
    primera_marca = segundo_inicial
    segunda_marca = segundo_final

    if mantener_limites =='NO':
        p_primera_marca = 0.0
        valor_primera_marca = primera_marca
        p_segunda_marca = 0.0
        valor_segunda_marca = segunda_marca
    elif mantener_limites == 'MODIFICAR':
        valor_primera_marca = primera_marca + a_primera_marca
        if valor_primera_marca < primera_marca:
            valor_primera_marca = primera_marca
        elif valor_primera_marca > segunda_marca:
            valor_primera_marca = segunda_marca
        valor_segunda_marca = segunda_marca + a_segunda_marca
        if valor_segunda_marca < primera_marca:
            valor_segunda_marca = primera_marca
        elif valor_segunda_marca > segunda_marca:
            valor_segunda_marca = segunda_marca

        print("valor original 1:", primera_marca, "valor original 2:", segunda_marca)
        print("valor añadido 1:", a_primera_marca, "valor añadido 2:", a_segunda_marca)
    elif mantener_limites == 'MODIFICAR_EXACTO':
        valor_primera_marca = a_primera_marca
        if valor_primera_marca < primera_marca:
            valor_primera_marca = primera_marca
            a_primera_marca = primera_marca
        elif valor_primera_marca > segunda_marca:
            valor_primera_marca = segunda_marca
            a_segunda_marca = segunda_marca
        
        valor_segunda_marca = a_segunda_marca
        if valor_segunda_marca < primera_marca:
            valor_segunda_marca = primera_marca
            a_primera_marca = primera_marca
        elif valor_segunda_marca > segunda_marca:
            valor_segunda_marca = segunda_marca
            a_segunda_marca = segunda_marca

        p_primera_marca = a_primera_marca - primera_marca
        p_segunda_marca = a_segunda_marca - segunda_marca
        
    else:
        valor_primera_marca = primera_marca + p_primera_marca
        valor_segunda_marca = segunda_marca + p_segunda_marca
    
    print("primera_marca:", valor_primera_marca, "segunda marca:", valor_segunda_marca)

    LIM_IZQ.config(text = str(round(valor_primera_marca,2)))
    LIM_DER.config(text = str(round(valor_segunda_marca,2)))
    
    for i in range(len(V)):
        valor = V[i]*Z
        V_Transformado.append(valor)
        V_Transformado_valor_real.append(V[i])
    dic_desplazamiento = {'izquierda': -1, 'derecha': 1, 'centrar': ajuste*-1, 'mantener': 0}
    if direccion != "original" or direccion == 'mantener':
        if posicion == "arriba":
            desplazado_arriba += dic_desplazamiento[direccion]
            if desplazado_arriba > 0:
                for i in range(desplazado_arriba):
                    V_Transformado.pop(-1)
                    V_Transformado_valor_real.pop(-1)
                    V_Transformado.insert(0,0)
                    V_Transformado_valor_real.insert(0,0)
            elif desplazado_arriba < 0:
                for i in range(abs(desplazado_arriba)):
                    V_Transformado.pop(0)
                    V_Transformado_valor_real.pop(0)
                    V_Transformado.append(0)
                    V_Transformado_valor_real.append(0)
            else:
                pass      
        elif posicion == "abajo":
            desplazado_abajo += dic_desplazamiento[direccion]
            if desplazado_abajo > 0:
                for i in range(desplazado_abajo):
                    V_Transformado.pop(-1)
                    V_Transformado_valor_real.pop(-1)
                    V_Transformado.insert(0,0)
                    V_Transformado_valor_real.insert(0,0)
            elif desplazado_abajo < 0:
                for i in range(abs(desplazado_abajo)):
                    V_Transformado.pop(0)
                    V_Transformado_valor_real.pop(0)
                    V_Transformado.append(0)
                    V_Transformado_valor_real.append(0)
    else:
        if posicion == "arriba":
            desplazado_arriba = 0
        elif posicion == "abajo":
            desplazado_abajo = 0
    
    if magnitud == 'avged':
        condicion = 'NO'
    else:
        condicion = 'SI'

    B1_izquierda = Button(dic_posicion[posicion][3], text="<", command=lambda:moverlimite(posicion, magnitud, dic_ultima_grafica[posicion], 'mantener', condicion, 'MODIFICAR', '1', 'izquierda'))
    B1_izquierda.grid(row=0, column=0, sticky='nsew')
    B1_derecha = Button(dic_posicion[posicion][3], text=">", command=lambda:moverlimite(posicion, magnitud, dic_ultima_grafica[posicion], 'mantener', condicion, 'MODIFICAR', '1', 'derecha'))
    B1_derecha.grid(row=0, column=1, sticky='nsew')
    B2_izquierda = Button(dic_posicion[posicion][3], text="<", command=lambda:moverlimite(posicion, magnitud, dic_ultima_grafica[posicion], 'mantener', condicion, 'MODIFICAR', '2', 'izquierda'))
    B2_izquierda.grid(row=0, column=2, sticky='nsew')
    B2_derecha = Button(dic_posicion[posicion][3], text=">", command=lambda:moverlimite(posicion, magnitud, dic_ultima_grafica[posicion], 'mantener', condicion, 'MODIFICAR', '2', 'derecha'))
    B2_derecha.grid(row=0, column=3, sticky='nsew')

    segundos_Transformado = []
    
    if magnitud == 'fuerzaxvelocidad':
        a.axvline(valor_primera_marca, color='r', ls="dotted")
        a.axvline(valor_segunda_marca, color='r', ls="dotted")

    suma_energia = 0
    j = 0
    for i in range(segundos.index(round(valor_primera_marca,2)),segundos.index(round(valor_segunda_marca,2))):
        if i == 0:
            suma_energia += ((V_Transformado_valor_real[i]*F[i])+(0))*(1/(int(frecuencia_muestreo[-1])))/2
        else:
            suma_energia += ((V_Transformado_valor_real[i]*F[i])+(V_Transformado_valor_real[i-1]*F[i-1]))*(1/(int(frecuencia_muestreo[-1])))/2
        E.append(suma_energia)
        n = round(valor_primera_marca+(j/(int(frecuencia_muestreo[-1]))),2)
        j+=1
        segundos_Transformado.append(n)
    
    Emax = round(max(E), 2)
    
    if magnitud == 'avged':
        segundos = segundos_Transformado
    
    
    ET = float(ET_valor_original)
    ETR = round(100*(Emax/ET),2)
    CE = str(round(ETR*0.60,2))
        
    dic_magnitud = {'aceleracion':[A3, A4], 'deformacion':[S1, S2], 'fuerza':[F1, F2], 'velocidad':[V1, V2], 'avged':[E, E], 'desplazamiento':[D1, D2], 'fuerzaxvelocidad':[F,V_Transformado]}
    dic_legenda = {'aceleracion':["A3", "A4"], 'deformacion':["S1", "S2"], 'fuerza':["F1", "F2"], 'velocidad':["V1", "V2"], 'avged':["E", "E"], 'desplazamiento':["D1", "D2"], 'fuerzaxvelocidad':["F", str(round(Z, 2))+"*V"]}
    dic_unidades = {'aceleracion':["milisegundos", "m/s2"], 'deformacion':["milisegundos", "m"], 'fuerza':["milisegundos", "kN"], 'velocidad':["milisegundos", "m/s"], 'avged':["milisegundos", ""], 'desplazamiento':["milisegundos", "m"], 'fuerzaxvelocidad':["milisegundos", ""]}
    try:
        t1, = a.plot(segundos, dic_magnitud[magnitud][0], label=dic_legenda[magnitud][0])
    except:
        print("señal de solo un sensor")
    try:
        t2, = a.plot(segundos, dic_magnitud[magnitud][1], label=dic_legenda[magnitud][1])
    except:
        print("señal de solo un sensor")
    a.set_xlabel(dic_unidades[magnitud][0])
    a.set_ylabel(dic_unidades[magnitud][1])
    try:
        a.legend(handles=[t1, t2])
    except:
        try:
            a.legend(handles=[t1])
        except:
            try:
                a.legend(handles=[t2])
            except:
                pass

    if posicion == 'arriba':
        a.callbacks.connect('xlim_changed', on_xlims_change_arriba)
        a.callbacks.connect('ylim_changed', on_ylims_change_arriba)
    elif posicion == 'abajo':
        a.callbacks.connect('xlim_changed', on_xlims_change_abajo)
        a.callbacks.connect('ylim_changed', on_ylims_change_abajo)
        
    f.subplots_adjust(left=0.07,bottom=0.1,right=0.98,top=0.96)
    canvas = FigureCanvasTkAgg(f, dic_posicion[posicion][0])

    canvas.get_tk_widget().pack(side=TOP, expand=1, fill=BOTH)

    toolbar = NavigationToolbar2TkAgg(canvas, dic_posicion[posicion][1])
    toolbar.update()
    canvas._tkcanvas.pack(side=BOTTOM, expand=1, fill=BOTH)
    
    texto_label_num_grafica = str(dic_ultima_grafica[posicion])+"/"+str(len(matriz_data_archivos)-1)

    modificar_datos_segundo_frame(posicion, texto_label_num_grafica, Fmax, Vmax, Emax, Dmax, str(ETR) + "%", CE)

    try:
        Label(dic_posicion[posicion][2], text="actual:"+str(dic_ultima_grafica[posicion])+",ultima:"+str(len(matriz_data_archivos)-1)+",total:"+str((len(matriz_data_archivos)-1))).pack(side=LEFT)     
        L_T_Grafico.config(text=str(dic_ultima_grafica[posicion]))
    except Exception as e:
        pass

    if mantener_relacion_aspecto == 'SI':
        a.set_xlim(dic_posicion_zoom[posicion][0], dic_posicion_zoom[posicion][1])
        a.set_ylim(dic_posicion_zoom[posicion][2], dic_posicion_zoom[posicion][3])

    try:
        if posicion == "arriba":
            dic_posicion[posicion][0].pack_slaves()[0].bind("<2>", click_grafica_arriba)
        elif posicion == "abajo":
            dic_posicion[posicion][0].pack_slaves()[0].bind("<2>", click_grafica_abajo)
    except:
        print("error1")
    
# Barra lateral de la columna de la derecha

container2_3 = Frame(container2)
container2_3.grid(row=0, rowspan=2, column=1, sticky='nsew')
container2_3.grid_columnconfigure(0, weight=1)
container2_3.grid_columnconfigure(1, weight=1)


# Configuración de los botones comandos

dic_direccion = {'derecha': 1, 'izquierda': -1, 'derecha+' :3, 'izquierda+': -3, 'nulo':0}
dic_ultima_grafica = {"arriba": contador_grafica_arriba, "abajo": contador_grafica_abajo}

def eliminar_grafica():
    global ultima_grafica_seleccionada, matriz_data_archivos, Label_Num_Grafica, ruta_data_inicial, orden_sensores
    matriz_relacion_num = [i for i in range(1,len(matriz_data_archivos))]
    matriz_data_archivos.pop(dic_ultima_grafica[ultima_grafica_seleccionada])
    matriz_relacion_num2 = matriz_relacion_num[:]
      
    matriz_relacion_num2.pop(dic_ultima_grafica[ultima_grafica_seleccionada]-1)
    matriz_relacion_num.pop(dic_ultima_grafica[ultima_grafica_seleccionada]-1)
    for i in range(len(matriz_relacion_num)):
        if i >= dic_ultima_grafica[ultima_grafica_seleccionada]-1:
            matriz_relacion_num2[i]=matriz_relacion_num2[i]-1
        
    string = str(matriz_data_archivos[0]) + "\n"   
    with open(ruta_data_inicial, "w") as file:
        print(matriz_relacion_num)
        for index, num in enumerate(matriz_relacion_num):
            print(num)
            string += 'INICIO_ARCHIVO\nARCHIVO:'+str(index+1)+"\n"+str(orden_sensores[-1])+"\n"
            for fila in matriz_data_archivos[index+1]:
                string += fila+"\n"
            string += 'FIN_ARCHIVO\n'
        file.write(string)
    


    print(matriz_relacion_num)


    #Label_Num_Grafica.configure(text=str(dic_ultima_grafica[ultima_grafica_seleccionada])+"/"+str(len(matriz_data_archivos)-1), font=('Times', 15))
    cambiar_grafica("nulo")

def cambiar_grafica(direccion):
    global matriz_data_archivos
    global ultima_grafica_seleccionada
    global ultima_magnitud_arriba
    global ultima_magnitud_abajo
    global p_primera_marca, p_segunda_marca
    dic_ultima_grafica[ultima_grafica_seleccionada] += dic_direccion[direccion]
    if dic_ultima_grafica[ultima_grafica_seleccionada] >= len(matriz_data_archivos):
        dic_ultima_grafica[ultima_grafica_seleccionada] = len(matriz_data_archivos)-1
    elif dic_ultima_grafica[ultima_grafica_seleccionada] < 1:
        dic_ultima_grafica[ultima_grafica_seleccionada] = 1
    p_primera_marca = 0.0
    p_segunda_marca = 0.0
    print("en cambiar gráfica el num de gráfica es: ", dic_ultima_grafica[ultima_grafica_seleccionada])
    if direccion == 'nulo':
        if ultima_grafica_seleccionada == 'arriba':
            Creacion_Grafica('abajo', dic_ultima_grafica_magnitud['abajo'], dic_ultima_grafica['abajo'], "original", "SI", "NO")
        else:
            Creacion_Grafica('arriba', dic_ultima_grafica_magnitud['arriba'], dic_ultima_grafica['arriba'], "original", "SI", "NO")
    Creacion_Grafica(ultima_grafica_seleccionada, dic_ultima_grafica_magnitud[ultima_grafica_seleccionada], dic_ultima_grafica[ultima_grafica_seleccionada], "original", "SI", "NO")
    

def desplazar_grafica(direccion):
    global contador_grafica_arriba, contador_grafica_abajo, ultima_grafica_seleccionada, ultima_magnitud_arriba, ultima_magnitud_abajo, desplazado_izquierda, desplazado_derecha
    
    #actualizar los límites movidos
    

    Creacion_Grafica(ultima_grafica_seleccionada, dic_ultima_grafica_magnitud[ultima_grafica_seleccionada], dic_ultima_grafica[ultima_grafica_seleccionada], direccion, "SI", "SI")

botones_barra_lateral = ['DEL','˄','˅','DD','DI','AJ','>','<','>>','<<']

for i in range(len(botones_barra_lateral)):
    container2_3.grid_rowconfigure(i, weight=1)

Button(container2_3, text=botones_barra_lateral[0], bg=azul_oscuro ,fg='#FFFFFF', font=('Arial', 20), command=lambda: eliminar_grafica()).grid(row=0,column=0, columnspan=2, sticky='nsew') 
Button(container2_3, text=botones_barra_lateral[1], bg=azul_oscuro ,fg='#FFFFFF', font=('Arial', 20), command=lambda: print(1)).grid(row=1,column=0, columnspan=2, sticky='nsew') 
Button(container2_3, text=botones_barra_lateral[2], bg=azul_oscuro ,fg='#FFFFFF', font=('Arial', 20), command=lambda: print(2)).grid(row=2,column=0, columnspan=2, sticky='nsew')
Button(container2_3, text=botones_barra_lateral[3], bg=azul_oscuro ,fg='#FFFFFF', font=('Arial', 20), command=lambda: desplazar_grafica("derecha")).grid(row=3,column=0, columnspan=2, sticky='nsew')
Button(container2_3, text=botones_barra_lateral[4], bg=azul_oscuro ,fg='#FFFFFF', font=('Arial', 20), command=lambda: desplazar_grafica("izquierda")).grid(row=4,column=0, columnspan=2, sticky='nsew')
Button(container2_3, text=botones_barra_lateral[5], bg=azul_oscuro ,fg='#FFFFFF', font=('Arial', 20), command=lambda: desplazar_grafica("centrar")).grid(row=5,column=0, columnspan=2, sticky='nsew')
Button(container2_3, text=botones_barra_lateral[6], bg=azul_oscuro ,fg='#FFFFFF', font=('Arial', 20), command=lambda: cambiar_grafica("derecha")).grid(row=6,column=0, columnspan=2, sticky='nsew')
Button(container2_3, text=botones_barra_lateral[7], bg=azul_oscuro ,fg='#FFFFFF', font=('Arial', 20), command=lambda: cambiar_grafica("izquierda")).grid(row=7,column=0, columnspan=2, sticky='nsew')
Button(container2_3, text=botones_barra_lateral[8], bg=azul_oscuro ,fg='#FFFFFF', font=('Arial', 20), command=lambda: cambiar_grafica("derecha+")).grid(row=8,column=0, columnspan=2, sticky='nsew')
Button(container2_3, text=botones_barra_lateral[9], bg=azul_oscuro ,fg='#FFFFFF', font=('Arial', 20), command=lambda: cambiar_grafica("izquierda+")).grid(row=9,column=0, columnspan=2, sticky='nsew')

#----------------------------------------------------
# Frame de la derecha 
container3 = Frame(container, bg=azul_claro)
container3.grid(row=0,column=2,sticky='nsew')
container3.grid_columnconfigure(0, weight=1)

# Frames Principales
# Frame de arriba

container3_1 = Frame(container3, bg=azul_oscuro)
container3_1.grid(row=0, column=0, padx=20, pady=(20,5), sticky='new')
container3_1.grid_columnconfigure(0, weight=1)
container3_1.grid_columnconfigure(1, weight=1)
T_1 = Label(container3_1, text="Límites de la gráfica de arriba", bg=azul_oscuro, fg='#FFFFFF').grid(row=0,column=0, padx=10, pady=10, sticky='nsew')

container3_2 = Frame(container3, bg=azul_oscuro)
container3_2.grid(row=1, column=0, padx=20, pady=(20,10), sticky='new')

container3_2.grid_columnconfigure(0, weight=1)
container3_2.grid_columnconfigure(1, weight=1)

textos_tercer_frame = ["límite izquierda", "límite derecha"]

Label(container3_2, text=textos_tercer_frame[0], bg=azul_oscuro, fg='#FFFFFF').grid(row=0,column=0, padx=10, pady=10, sticky='nw') 
LIM_IZQ = Label(container3_2, text='', bg='#D9D9D9', fg='black')
LIM_IZQ.grid(row=0, column=1,padx=10, pady=10, sticky='nwe')
Label(container3_2, text=textos_tercer_frame[1], bg=azul_oscuro, fg='#FFFFFF').grid(row=1,column=0, padx=10, pady=10, sticky='nw') 
LIM_DER = Label(container3_2, text='', bg='#D9D9D9', fg='black')
LIM_DER.grid(row=1, column=1,padx=10, pady=10, sticky='nwe')



# Frame del medio

container3_3 = Frame(container3, bg=azul_oscuro)
container3_3.grid(row=2, column=0, padx=20, pady=10, sticky='new')
container3_3.grid_columnconfigure(0, weight=1)
container3_3.grid_columnconfigure(1, weight=1)

container3_3.rowconfigure(0, weight=1)
container3_3.rowconfigure(1, weight=1)
container3_3.rowconfigure(2, weight=1)
container3_3.rowconfigure(3, weight=1)


T_2 = Label(container3_3, text="Límites input", bg=azul_oscuro, fg='#FFFFFF').grid(row=0,column=0, padx=10, pady=10, sticky='nsew')

Label(container3_3, text=textos_tercer_frame[0], bg=azul_oscuro, fg='#FFFFFF').grid(row=1,column=0, padx=10, pady=10, sticky='nw') 
LIM_IZQ_Entry = Entry(container3_3, bg='#D9D9D9', fg='black')
LIM_IZQ_Entry.grid(row=1, column=1,padx=10, pady=10, sticky='nwe')
Label(container3_3, text=textos_tercer_frame[1], bg=azul_oscuro, fg='#FFFFFF').grid(row=2,column=0, padx=10, pady=10, sticky='nw') 
LIM_DER_Entry = Entry(container3_3, bg='#D9D9D9', fg='black')
LIM_DER_Entry.grid(row=2, column=1,padx=10, pady=10, sticky='nwe')

Button(container3_3, text='Actualizar', bg='#D9D9D9', fg='black', command=lambda:actualizar_limites()).grid(row=3, column=0, padx=10, pady=10, sticky='nw')

def actualizar_limites():
    global contador_grafica_arriba
    global contador_grafica_abajo
    global ultima_grafica_seleccionada
    global ultima_magnitud_arriba
    global ultima_magnitud_abajo
    global LIM_IZQ_Entry, LIM_DER_Entry
    Creacion_Grafica(ultima_grafica_seleccionada, dic_ultima_grafica_magnitud[ultima_grafica_seleccionada], dic_ultima_grafica[ultima_grafica_seleccionada], 'original', "SI", 'MODIFICAR_EXACTO', float(LIM_IZQ_Entry.get()), float(LIM_DER_Entry.get()))


# Frame de abajo

container3_4 = Frame(container3, bg=azul_oscuro)
container3_4.grid(row=3, column=0, padx=20, pady=10, sticky='new')
container3_4.grid_columnconfigure(0, weight=1)
container3_4.grid_rowconfigure(0, weight=1)

Button(container3_4, text='Exportar', bg='#D9D9D9', fg='black', command=lambda:[preparaciones_exportar(),raise_frame(Export)]).grid(row=0, column=0, padx=10, pady=10, sticky='new')

def preparaciones_exportar():
    global matriz_data_archivos, inicio_final_label
    longitudes = matriz_data_archivos[0][12:].split(",")
    inicio_final_label.configure(text='Cantidad de Golpes:'+str(len(matriz_data_archivos)-1)+', Inicio:'+str(longitudes[0])+' - '+'Final:'+str(longitudes[1]), bg=azul_celeste, fg='White', font=('Times',15))

#--------------------FRAME2------------------------------------------------------------

container5 = Frame((Collect_Wire), bg=azul_oscuro)
container5.grid(row=0, column=0, sticky='nsew')
container5.grid_rowconfigure(0, weight=1)
container5.grid_rowconfigure(1, weight=1)
container5.grid_columnconfigure(0, weight=1)
container5.grid_columnconfigure(1, weight=1)
container5.grid_columnconfigure(2, weight=1)


puertos=[]
estado_puerto = False

def detectar_puertos():

    global socket_tcp, estado_puerto
    host = "169.254.159.253"
    port = 65432
    
    if estado_puerto == False:
        try:
            socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_tcp.connect((host, port))
            estado_puerto = True
        except:
            print("error en el socket")
        print("Conectado al puerto")
        print(host)
    else:
        print("el socket ya existe")

def detener_conexion_puerto():

    global socket_tcp, estado_puerto
    
    try:
        estado_puerto = False
        socket_tcp.close()
    except:
        pass

bandera = True

def detener_loop():
    global bandera
    bandera = False

conexion =""

def verificacion_orden_sensores():
    global bandera
    global conexion
    global orden_sensores
    global socket_tcp
    
    # socket_tcp.listen()
    # Convertimos str a bytes
    MESSAGE = "S"
    socket_tcp.send(MESSAGE.encode('utf-8'))
    BUFFER_SIZE = 1
    #data = socket_tcp.recv(BUFFER_SIZE)
    
    print("S")
    bandera = True
    #time.sleep(0.2)
    ordenes = ""
    while bandera == True:
        linea = socket_tcp.recv(1).decode()
        print(type(linea))
        print(linea)
        if linea == " ":
            orden_sensores.append(ordenes)
            print("ORDENES RECIBIDOS")
            break
        if linea != "":
            ordenes = ordenes + linea
            



dic_sensores = {'1':'Sensor Aceleración 1', '2':'Sensor Aceleración 2', '3':'Sensor SPT 1', '4':'Sensor SPT 2', '5':'Sensor DPT 1', '6':'Sensor DPT 2', '0':'No encontrado'}
    
container5_1 = Frame(container5, bg=azul_oscuro)

container5_1.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
container5_1.grid_rowconfigure(0, weight=1)
container5_1.grid_rowconfigure(1, weight=7)
container5_1.grid_columnconfigure(0, weight=1)


container5_1_1 = Frame(container5_1, bg=azul_oscuro)
container5_1_1.grid(row=0, column=0, sticky='nsew')
container5_1_1.grid_rowconfigure(0, weight=1)
container5_1_1.grid_rowconfigure(1, weight=8)
container5_1_1.grid_columnconfigure(0, weight=1)
container5_1_1.grid_columnconfigure(1, weight=2)
container5_1_1.grid_columnconfigure(2, weight=1)


Label_titulo_1 = Label(container5_1_1, text='Seleccion de Sensores', bg=azul_oscuro, fg='White')
Label_titulo_1.grid(row=0, column=1, sticky='nsew')

container5_1_2 = Frame(container5_1, bg=azul_claro)
container5_1_2.grid(row=1, column=0, sticky='nsew')
container5_1_2.grid_rowconfigure(0, weight=1)
container5_1_2.grid_rowconfigure(1, weight=1)
container5_1_2.grid_rowconfigure(2, weight=1)
container5_1_2.grid_rowconfigure(3, weight=1)
container5_1_2.grid_columnconfigure(0, weight=1)
container5_1_2.grid_columnconfigure(1, weight=3)

def Generar_Tabla_Sensores():
    global orden_sensores
    time.sleep(0.3)
    detener_loop()
    time.sleep(0.3)
    try:
        print("holi2")
        print(orden_sensores[-1])
        print("holi")
        orden = str(orden_sensores[-1]).replace(" ","").split("|")

        try:
            Label_sensor1_data.configure(text=dic_sensores[orden[0]], font=('Times',15))
            Label_sensor2_data.configure(text=dic_sensores[orden[1]], font=('Times',15))
            Label_sensor3_data.configure(text=dic_sensores[orden[2]], font=('Times',15))
            Label_sensor4_data.configure(text=dic_sensores[orden[3]], font=('Times',15))
        except:
            print("debe ser esto")
            pass
    except:
        print("No sabo")
        pass

Label_sensor1 = Label(container5_1_2, text="Sensor1", font=('Times',15), bg=azul_celeste, fg='White')
Label_sensor1.grid(row=0, column=0, sticky='nsew', padx=(20,0), pady=(20,10))
Label_sensor2 = Label(container5_1_2, text="Sensor2", font=('Times',15), bg=azul_celeste, fg='White')
Label_sensor2.grid(row=1, column=0, sticky='nsew', padx=(20,0), pady=(10,10))
Label_sensor3 = Label(container5_1_2, text="Sensor3", font=('Times',15), bg=azul_celeste, fg='White')
Label_sensor3.grid(row=2, column=0, sticky='nsew', padx=(20,0), pady=(10,10))
Label_sensor4 = Label(container5_1_2, text="Sensor4", font=('Times',15), bg=azul_celeste, fg='White')
Label_sensor4.grid(row=3, column=0, sticky='nsew', padx=(20,0), pady=(10,20))

Label_sensor1_data = Label(container5_1_2, text="No disponible", font=('Times',15), bg='White')
Label_sensor1_data.grid(row=0, column=1, sticky='nsew', padx=(0,20), pady=(20,10))
Label_sensor2_data = Label(container5_1_2, text="No disponible", font=('Times',15), bg='White')
Label_sensor2_data.grid(row=1, column=1, sticky='nsew', padx=(0,20), pady=(10,10))
Label_sensor3_data = Label(container5_1_2, text="No disponible", font=('Times',15), bg='White')
Label_sensor3_data.grid(row=2, column=1, sticky='nsew', padx=(0,20), pady=(10,10))
Label_sensor4_data = Label(container5_1_2, text="No disponible", font=('Times',15), bg='White')
Label_sensor4_data.grid(row=3, column=1, sticky='nsew', padx=(0,20), pady=(10,20))


lista_opciones =ttk.Combobox(container5_1_1, font=('Arial',10), state='readonly', values=puertos)
lista_opciones.grid(row=1, column=0, sticky='nsew')

Button(container5_1_1, text="Conectar al servidor", fg='Black', font=('Times',10), command=lambda: [detectar_puertos(), lista_opciones.configure(values=puertos)]).grid(row=1, column=1, sticky='nsew')
Button(container5_1_1, text="Actualizar orden de sensores", fg='Black', font=('Times',10),command=lambda: [verificacion_orden_sensores(), Generar_Tabla_Sensores()]).grid(row=1, column=2, sticky='nsew')

container5_2 = Frame(container5, bg=azul_oscuro)
container5_2.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)

container5_2.grid_rowconfigure(0, weight=1)
container5_2.grid_rowconfigure(1, weight=56)
container5_2.grid_columnconfigure(0, weight=1)

Label_titulo_2 = Label(container5_2, text='Parámetros de la varilla', bg=azul_oscuro, fg='White')
Label_titulo_2.grid(row=0, column=0, sticky='nsew')

container5_2_2 = Frame(container5_2, bg=azul_claro)
container5_2_2.grid(row=1, column=0, sticky='nsew')

container5_2_2.grid_rowconfigure(0, weight=1)
container5_2_2.grid_rowconfigure(1, weight=1)
container5_2_2.grid_columnconfigure(0, weight=3)
container5_2_2.grid_columnconfigure(1, weight=2)
container5_2_2.grid_columnconfigure(2, weight=1)

Label_Area = Label(container5_2_2, text="Área", font=('Times',15), bg=azul_celeste, fg='White').grid(row=0, column=0, sticky='nsew', padx=(40,0), pady=(60,30))
Entry_Area = Entry(container5_2_2, font=('Times',15))
Entry_Area.grid(row=0, column=1, sticky='nsew', pady=(60,30))
Label_Area_unidad = Label(container5_2_2, text="cm2", font=('Times',15), bg=azul_celeste, fg='White').grid(row=0, column=2, sticky='nsew', padx=(0,40), pady=(60,30))

Label_Modulo_Elasticidad = Label(container5_2_2, text="Módulo de \nElasticidad ", font=('Times',15), bg=azul_celeste, fg='White').grid(row=1, column=0, sticky='nsew', padx=(40,0), pady=(30,60))
Entry_modulo_elasticidad = Entry(container5_2_2, font=('Times',15))
Entry_modulo_elasticidad.grid(row=1, column=1, sticky='nsew', pady=(30,60))
Label_Modulo_Elasticidad_unidad = Label(container5_2_2, text="MPa", font=('Times',15), bg=azul_celeste, fg='White').grid(row=1, column=2, sticky='nsew', padx=(0,40), pady=(30,60))


container5_3 = Frame(container5, bg=azul_oscuro)
container5_3.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
container5_3.grid_rowconfigure(0, weight=1)
container5_3.grid_rowconfigure(1, weight=56)
container5_3.grid_columnconfigure(0, weight=1)

Label_titulo_3 = Label(container5_3, text='Profundidad', bg=azul_oscuro, fg='White')
Label_titulo_3.grid(row=0, column=0, sticky='nsew')

container5_3_1 = Frame(container5_3, bg=azul_claro)
container5_3_1.grid(row=1, column=0, sticky='nsew')
container5_3_1.grid_rowconfigure(0, weight=2)
container5_3_1.grid_rowconfigure(1, weight=2)
container5_3_1.grid_rowconfigure(2, weight=1)
container5_3_1.grid_columnconfigure(0, weight=1)
container5_3_1.grid_columnconfigure(1, weight=1)

container5_3_1_1 = Frame(container5_3_1, bg=azul_claro)
container5_3_1_1.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=10, pady=(0,40))
container5_3_1_1.grid_rowconfigure(0, weight=1)
container5_3_1_1.grid_columnconfigure(0, weight=5)
container5_3_1_1.grid_columnconfigure(1, weight=2)
container5_3_1_1.grid_columnconfigure(2, weight=1)
container5_3_1_1.grid_columnconfigure(3, weight=2)

Label_titulo_4 = Label(container5_3_1_1, text="Rango de \nProfundidades\n(m)", font=('Times',15), bg=azul_celeste, fg='White').grid(row=0, column=0, sticky='nsew', padx=(10,0), pady=(30,20))

Entry_Profundidad_inicial = Entry(container5_3_1_1, bg='White', font=('Times',15))
Entry_Profundidad_inicial.grid(row=0, column=1, sticky='nsew', pady=(30,20))

Label(container5_3_1_1, text="-", bg=azul_celeste, fg='White', font=('Times',15)).grid(row=0, column=2, sticky='nsew', pady=(30,20))

Entry_Profundidad_final = Entry(container5_3_1_1, bg='White', font=('Times',15))
Entry_Profundidad_final.grid(row=0, column=3, sticky='nsew', padx=(0,10), pady=(30,20))

container5_3_1_2 = Frame(container5_3_1, bg=azul_claro)
container5_3_1_2.grid(row=1, column=0, sticky='nsew', padx=(10,5))
container5_3_1_2.grid_rowconfigure(0, weight=1)
container5_3_1_2.grid_columnconfigure(0, weight=3)
container5_3_1_2.grid_columnconfigure(1, weight=2)
container5_3_1_2.grid_columnconfigure(2, weight=1)

LabelLE = Label(container5_3_1_2, text="LE", font=('Times',15), bg=azul_celeste, fg='White')
LabelLE.grid(row=0, column=0, sticky='nsew', )
EntryLE = Entry(container5_3_1_2, bg='White', font=('Times',15))
EntryLE.grid(row=0, column=1, sticky='nsew')
LabelLE_unidades = Label(container5_3_1_2, text="m", font=('Times',15), bg=azul_celeste, fg='White')
LabelLE_unidades.grid(row=0, column=2, sticky='nsew')

container5_3_1_3 = Frame(container5_3_1, bg=azul_claro)
container5_3_1_3.grid(row=1, column=1, sticky='nsew', padx=(5,10))
container5_3_1_3.grid_rowconfigure(0, weight=1)
container5_3_1_3.grid_columnconfigure(0, weight=3)
container5_3_1_3.grid_columnconfigure(1, weight=2)
container5_3_1_3.grid_columnconfigure(2, weight=1)

LabelLR = Label(container5_3_1_3, text="LR", font=('Times',15), bg=azul_celeste, fg='White')
LabelLR.grid(row=0, column=0, sticky='nsew')
EntryLE = Entry(container5_3_1_3, bg='White', font=('Times',15))
EntryLE.grid(row=0, column=1, sticky='nsew')
LabelLR_unidades = Label(container5_3_1_3, text="m", font=('Times',15), bg=azul_celeste, fg='White')
LabelLR_unidades.grid(row=0, column=2, sticky='nsew')

Button(container5_3_1, text="Regresar", font=('Times',15), fg='Black', command=lambda: [detener_conexion_puerto(), raise_frame(Menup)]).grid(row=2, column=0, sticky='nsew', pady=(40,0))


container5_4 = Frame(container5, bg=azul_oscuro)
container5_4.grid(row=1, column=1, sticky='nsew')

container5_4.grid_rowconfigure(0, weight=1)
container5_4.grid_rowconfigure(1, weight=54)
container5_4.grid_columnconfigure(0, weight=1)

Label(container5_4, text="Parámetros del Martillo", bg=azul_oscuro, fg='White').grid(row=0, column=0, sticky='nsew')


container5_4_1 = Frame(container5_4, bg=azul_claro)
container5_4_1.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
container5_4_1.grid_rowconfigure(0, weight=2)
container5_4_1.grid_rowconfigure(1, weight=1)
container5_4_1.grid_columnconfigure(0, weight=1)

container5_4_1_1 = Frame(container5_4_1, bg=azul_claro)
container5_4_1_1.grid(row=0, column=0, sticky='nsew', padx=30, pady=(60,30))
container5_4_1_1.grid_rowconfigure(0, weight=1)
container5_4_1_1.grid_rowconfigure(1, weight=1)
container5_4_1_1.grid_columnconfigure(0, weight=2)
container5_4_1_1.grid_columnconfigure(1, weight=2)
container5_4_1_1.grid_columnconfigure(2, weight=1)
container5_4_1_1.grid_columnconfigure(3, weight=3)

Label_Masa = Label(container5_4_1_1, text="Masa", font=('Times',15), bg=azul_celeste, fg='White').grid(row=0, column=0, sticky='nsew', pady=(0,10))
Entry_masa = Entry(container5_4_1_1, bg='White', font=('Times',15))
Entry_masa.grid(row=0, column=1, sticky='nsew', pady=(0,10))
Label_Masa_unidades = Label(container5_4_1_1, text='kg', font=('Times',15), bg=azul_celeste, fg='White').grid(row=0, column=2, sticky='nsew', pady=(0,10))

Label_Altura = Label(container5_4_1_1, text="Altura", font=('Times',15), bg=azul_celeste, fg='White').grid(row=1, column=0, sticky='nsew', pady=(10,0))
Entry_altura = Entry(container5_4_1_1, bg='White', font=('Times',15))
Entry_altura.grid(row=1, column=1, sticky='nsew', pady=(10,0))
Label_Altura_unidades = Label(container5_4_1_1, text="m", font=('Times',15), bg=azul_celeste, fg='White').grid(row=1, column=2, sticky='nsew', pady=(10,0))

Boton_calcular_energia = Button(container5_4_1_1, text="Calcular \Energía", font=('Times',15), command=lambda:calcular()).grid(row=0, column=3, rowspan=2, sticky='nsew', padx=10)

container5_4_1_2 = Frame(container5_4_1, bg=azul_claro)
container5_4_1_2.grid(row=1, column=0, sticky='nsew', padx=30, pady=(30,60))
container5_4_1_2.grid_rowconfigure(0, weight=1)
container5_4_1_2.grid_columnconfigure(0, weight=1)
container5_4_1_2.grid_columnconfigure(1, weight=1)
container5_4_1_2.grid_columnconfigure(2, weight=1)

Label_Energia = Label(container5_4_1_2, text="Energia", font=('Times',15), bg=azul_celeste, fg='White').grid(row=0, column=0, sticky='nsew')
Label_Energia_valor = Label(container5_4_1_2, text="      ", font=('Times',15), bg='White')
Label_Energia_valor.grid(row=0, column=1, sticky='nsew')
Label_Energia_unidades = Label(container5_4_1_2, text="J", font=('Times',15), bg=azul_celeste, fg='White').grid(row=0, column=2, sticky='nsew')

producto = "      "

def calcular():
    global Entry_masa, Entry_altura, producto, Label_Energia_valor
    producto = int(float(Entry_masa.get())* float(Entry_altura.get())*9.81)
    Label_Energia_valor.configure(text=str(producto))

container5_5 = Frame(container5, bg=azul_oscuro)
container5_5.grid(row=0, column=2, rowspan=2, sticky='nsew')
container5_5.grid_rowconfigure(0, weight=1)
container5_5.grid_rowconfigure(1, weight=56)
container5_5.grid_columnconfigure(0, weight=1)

Label_titulo_5 = Label(container5_5, text="Parámetros de muestreo", bg=azul_oscuro, fg='White').grid(row=0, column=0, sticky='nsew')

container5_5_1 = Frame(container5_5, bg=azul_claro)
container5_5_1.grid(row=1, column=0, sticky='nsew')

container5_5_1.grid_rowconfigure(0, weight=1)
container5_5_1.grid_rowconfigure(1, weight=4)
container5_5_1.grid_rowconfigure(2, weight=4)
container5_5_1.grid_rowconfigure(3, weight=4)
container5_5_1.grid_rowconfigure(4, weight=2)
container5_5_1.grid_columnconfigure(0, weight=1)
container5_5_1.grid_columnconfigure(1, weight=1)

Label(container5_5_1, text='Frecuencia de Muestreo', font=('Times',15), bg=azul_celeste, fg="White").grid(row=0, column=0, columnspan=2, sticky='nsew', padx=20, pady=20)

container5_5_1_1 = Frame(container5_5_1, bg=azul_claro)
container5_5_1_1.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=10)
container5_5_1_1.grid_rowconfigure(0, weight=1)
container5_5_1_1.grid_rowconfigure(1, weight=1)
container5_5_1_1.grid_columnconfigure(0, weight=1)
container5_5_1_1.grid_columnconfigure(1, weight=1)

def mod_frecuencia_muestreo(n):
    global frecuencia_muestreo
    frecuencia_muestreo.append(n)

B_50 = Button(container5_5_1_1, text="50khz", command=lambda:[mod_frecuencia_muestreo(50), colorear_botones(50)], bg="#ECF0F1", font=('Times',15))
B_50.grid(row=0, column=0, padx=(20,10), pady=(20,10), sticky='nsew')
B_100 = Button(container5_5_1_1, text="100khz", command=lambda:[mod_frecuencia_muestreo(100), colorear_botones(100)], bg="#ECF0F1", font=('Times',15))
B_100.grid(row=0, column=1, padx=(10,20), pady=(20,10), sticky='nsew')
B_150 = Button(container5_5_1_1, text="150khz", command=lambda:[mod_frecuencia_muestreo(150), colorear_botones(150)], bg="#ECF0F1", font=('Times',15))
B_150.grid(row=1, column=0, padx=(20,10), pady=(10,20), sticky='nsew')
B_200 = Button(container5_5_1_1, text="200khz", command=lambda:[mod_frecuencia_muestreo(200), colorear_botones(200)], bg="#ECF0F1", font=('Times',15))
B_200.grid(row=1, column=1, padx=(10,20), pady=(10,20), sticky='nsew')

dic_botones_frecuencia = {'50':B_50, '100':B_100, '150':B_150, '200':B_200}

def colorear_botones(n):
    for termino in dic_botones_frecuencia:
        if termino == str(n):
            dic_botones_frecuencia[termino].configure(bg="Yellow")
        else:
            dic_botones_frecuencia[termino].configure(bg='#ECF0F1')


container5_5_1_2 = Frame(container5_5_1, bg=azul_claro)
container5_5_1_2.grid(row=2, column=0, columnspan=2, sticky='nsew', padx =10)

container5_5_1_2.grid_rowconfigure(0, weight=1)
container5_5_1_2.grid_rowconfigure(1, weight=1)
container5_5_1_2.grid_columnconfigure(0, weight=3)
container5_5_1_2.grid_columnconfigure(1, weight=2)
container5_5_1_2.grid_columnconfigure(2, weight=1)

Label(container5_5_1_2, text="Tiempo de \nmuestreo:", font=('Times',15), bg=azul_celeste, fg="White").grid(row=0, column=0, sticky='nsew', pady=(40,20))
Entry_tiempo_muestreo = Entry(container5_5_1_2, bg='White', font=('Times',15))
Entry_tiempo_muestreo.grid(row=0, column=1, sticky='nsew', pady=(40,20))
Label(container5_5_1_2, text='ms', font=('Times',15), bg=azul_celeste, fg="White").grid(row=0, column=2, sticky='nsew', pady=(40,20))

Label(container5_5_1_2, text="Tiempo de \nretardo", font=('Times',15), bg=azul_celeste, fg="White").grid(row=1, column=0, sticky='nsew', pady=(20,400))
Entry_tiempo_Retardo = Entry(container5_5_1_2, bg='White', font=('Times',15))
Entry_tiempo_Retardo.grid(row=1, column=1, sticky='nsew', pady=(20,400))
Label(container5_5_1_2, text='ms', font=('Times',15), bg=azul_celeste, fg="White").grid(row=1, column=2, sticky='nsew', pady=(20,400))



Button(container5_5_1, text= "Seleccionar ruta \nde guardado", font=('Times', 15), fg='Black', command=lambda: [escoger_ruta_guardado()]).grid(row=3, column=1, sticky='nsew', padx=20, pady=20)

Button(container5_5_1, text= "Siguiente", font=('Times',15), fg='Black',command=lambda: [mostrar_alertas()]).grid(row=4, column=1, sticky='nsew')

def escoger_ruta_guardado():
    global ruta_guardado
    ruta_guardado = filedialog.askdirectory(initialdir = "/", title = "Selecciona una carpeta")
    print(ruta_guardado) 
    ruta_guardado += "/"


# Container creado solo para la vista Collect Wire

def mostrar_alertas():
    global orden_sensores
    global frecuencia_muestreo, ruta_guardado
    global socket_tcp
    try:
        orden = str(orden_sensores[-1]).replace(" ","").split("|")
    except:
        pass
    if int(Entry_tiempo_muestreo.get()) <50 or int(Entry_tiempo_muestreo.get()) >300:
        MessageBox.showerror("Error", "El tiempo de muestreo tiene que estar entre 50 y 300")
        pass
    elif int(Entry_tiempo_Retardo.get()) <10 or int(Entry_tiempo_Retardo.get()) >50:
        MessageBox.showerror("Error", "El tiempo de retardo tiene que estar entre 10 y 50")
        pass
    elif frecuencia_muestreo[-1] == []:
        MessageBox.showerror("Error", "Escoja una frecuencia")
        pass
    elif len(orden_sensores) == 0:
        MessageBox.showerror("Error", "Seleccione un puerto")
    
    elif not(("1" in orden or "2" in orden) and ("3" in orden or "4" in orden or "5" in orden or "6" in orden)):
        MessageBox.showerror("Error", "Se necesitan al menos un sensor de aceleración y un sensor de DPT o SPT")
    
    elif float(Entry_Profundidad_final.get()) < float(Entry_Profundidad_inicial.get()):
        MessageBox.showerror("Error", "La profundidad inicial es mayor que la final")
    elif ruta_guardado == "":
        MessageBox.showerror("Selecciona una carpeta para guardar el .ct")
    else:
        #conexion = serial.Serial(port=lista_opciones.get(), baudrate=1500000, timeout=0.1, write_timeout=1)
        #conexion.write("P".encode('utf-8'))
        socket_tcp.send("P".encode('utf-8'))
        time.sleep(0.2)
        valor = str(str(frecuencia_muestreo[-1])+"|"+str(Entry_tiempo_muestreo.get())+"|"+str(Entry_tiempo_Retardo.get())+"|")
        print(valor)
        socket_tcp.send(valor.encode('utf-8'))
        time.sleep(0.1)
        print("enviando datos de frecuencia")
        #conexion.write(valor.encode('utf-8'))
        #conexion.close()

        raise_frame(Review)
        crear_columna_muestreo()

def limpiar_review():
    global LIM_IZQ, LIM_DER, LIM_IZQ_Entry, LIM_DER_Entry
    modificar_datos_segundo_frame('arriba', "", "", "", "", "", "", "")
    modificar_datos_segundo_frame('abajo', "", "", "", "", "", "", "")
    LIM_IZQ.config(text = "", bg='#D9D9D9', fg='black')
    LIM_DER.config(text = "", bg='#D9D9D9', fg='black')
    LIM_IZQ_Entry.config(text = "")
    LIM_DER_Entry.config(text = "")
    clear_container('arriba')
    clear_container('abajo')
    

def eliminar_columna_muestreo():
    global pile_area, pile_area_label, EM_valor_original, EM_label, ET_valor_original, ET_label
    try:
        if len(container1.grid_slaves()) > 3:
            for index,l in enumerate(container1.grid_slaves()):
                if index == 0:
                    l.destroy()
            eliminar_botones_play_stop()
    except:
        pass
    try:
        pile_area_label.configure(text=str(round(float(pile_area),2)))
        EM_label.configure(text=str(round(float(EM_valor_original),2)))
        ET_label.configure(text=str(round(float(ET_valor_original),2)))
    except:
        pass


def eliminar_botones_play_stop():
    for index,l in enumerate(container3.grid_slaves()):
        if index == 0:        
            l.destroy()

numero_grafica_insertada = 0

marca = False

num_golpe = 1
tipo_señal = ""
bandera_grafica = False

def crear_columna_muestreo():
    global frecuencia_muestreo, ruta_guardado
    global lista_opciones, pile_area_label, EM_label, ET_label
    global numero_grafica_insertada, marca, L_T_Grafico, num_golpe, tipo_señal, bandera_grafica, matriz_data_archivos, Entry_Profundidad_inicial, Entry_Profundidad_final
    global Entry_altura, Entry_Area, Entry_masa, Entry_modulo_elasticidad
    matriz_data_archivos = []


    pile_area_label.configure(text=str(round(float(Entry_Area.get()),2)))
    EM_label.configure(text=str(round(float(Entry_modulo_elasticidad.get()),2)))
    ET_label.configure(text=str(round(int(float(Entry_masa.get())* float(Entry_altura.get())*9.81),2)))

    container1_3 = Frame(container1, bg=azul_oscuro)
    container1_3.grid(row=3, column=0, padx=20, pady=10, sticky='new')
    container1_3.grid_columnconfigure(0, weight=10)
    container1_3.grid_columnconfigure(1, weight=1)
    container1_3.grid_rowconfigure(0, weight=1)
    container1_3.grid_rowconfigure(1, weight=1)
    container1_3.grid_rowconfigure(2, weight=1)
    container1_3.grid_rowconfigure(3, weight=1)

    Label(container1_3, text="Total de Gráficas:", font=("Times", 15), bg=azul_claro).grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

    Label(container1_3, text="Frecuencia de muestreo:", font=("Times", 15), bg=azul_claro).grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
    Label(container1_3, text="Tiempo de muestreo:", font=("Times", 15), bg=azul_claro).grid(row=2, column=0, padx=10, pady=10, sticky='nsew')
    Label(container1_3, text="Tiempo de retardo:", font=("Times", 15), bg=azul_claro).grid(row=3, column=0, padx=10, pady=10, sticky='nsew')
    


    L_T_Grafico = Label(container1_3, text="0", font=("Times", 15), bg=azul_claro)
    L_T_Grafico.grid(row=0, column=1, padx=10, pady=10, sticky='ns')
    L_Frecuencia = Label(container1_3, text=str(frecuencia_muestreo[-1])+" khz", font=("Times", 15), bg=azul_claro)
    L_Frecuencia.grid(row=1, column=1, padx=10, pady=10, sticky='ns')
    L_T_Muestreo = Label(container1_3, text=Entry_tiempo_muestreo.get()+" ms", font=("Times", 15), bg=azul_claro)
    L_T_Muestreo.grid(row=2, column=1, padx=10, pady=10, sticky='ns')
    L_T_Retardo = Label(container1_3, text=Entry_tiempo_Retardo.get()+" ms", font=("Times", 15), bg=azul_claro)
    L_T_Retardo.grid(row=3, column=1, padx=10, pady=10, sticky='ns')
    matriz_data_archivos.append(str(Entry_Profundidad_inicial.get())+","+str(Entry_Profundidad_final.get()))
    orden_sensores.append(str(orden_sensores[-1].replace("\n", ""))+str(frecuencia_muestreo[-1])+"|"+str(Entry_Area.get())+"|"+str(Entry_modulo_elasticidad.get())+"|"+str(int(float(Entry_masa.get())* float(Entry_altura.get())*9.81)))
    

    container3_5 = Frame(container3, bg=azul_claro)
    container3_5.grid(row=4, column=0, sticky='nsew')
    container3_5.grid_rowconfigure(0, weight=1)
    container3_5.grid_columnconfigure(0, weight=1)
    container3_5.grid_columnconfigure(1, weight=1)
    

    Boton_play = Button(container3_5, text="►", font=('Times', 20), command=lambda:[cambio_boton_play()])
    Boton_play.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=(30), pady=(150,10))
    
    

    def graficas_tiempo_real(num):
        global bandera_grafica, L_T_Grafico, num_golpe, matriz_data_archivos
        global marca
        
        print(marca, bandera_grafica)
        
        def graficar():
            global bandera_grafica, marca, L_T_Grafico, num_golpe
            while bandera_grafica and marca:
                print(1)
                time.sleep(0.2)
   
                try:
                    marca = False
                    
                    print("Intentando graficar2 ", num)
                    try:
                        dic_ultima_grafica['arriba'] = int(num)
                        Creacion_Grafica("arriba","aceleracion", int(num), "original", "NO", "NO", 0, 0)
                    except Exception as e:
                        print("error en grafica arriba", e)
                    try:
                        dic_ultima_grafica['abajo'] = int(num)
                        Creacion_Grafica("abajo","deformacion", int(num), "original", "NO", "NO", 0, 0)
                    except:
                        print("error en grafica abajo")
                    try:
                        num_golpe += 1
                    except:
                        print("ni idea")
                except:
                    print("no hay Data")
        threading.Thread(target=graficar).start()


    def inicio_secuencia_grabado():
        global bandera_grafica, marca,señal_continua, num_golpe, matriz_data_archivos
        global socket_tcp

        def lectura():
            global bandera_grafica, marca, num_golpe, señal_continua
            global socket_tcp

            #conexion = serial.Serial(port=lista_opciones.get(), baudrate=1500000, timeout=0.1, write_timeout=1)
            #conexion.write("M".encode('utf-8'))
            MESSAGE = "M"
            socket_tcp.send(MESSAGE.encode('utf-8'))

            print("M")
            num = 0

            while señal_continua == True: 
                print("conexion abierta por inicio")
                bandera_grafica = True
                bandera2 = 1
                bandera3 = 0
                bandera4 = 1
                string = ""
                vector = []
                acumulado = ""

                while ((bandera3 == 0 ) and (señal_continua == True)):
                    
                    print("recibiendo")
                    #raw_string_b = conexion.read(200)
                    cata = socket_tcp.recv(10000).decode("cp437")
                    #raw_string_b = socket_tcp.recv(10)
                    #raw_string_s = raw_string_b.decode('utf-8')
                    #string = str(raw_string_s).replace("\x00", "")
                    #print(string)
                    #if string == "":
                    #    bandera2 = 0
                    
                    #if bandera2 == 0 and string != "":
                    if cata != "":
                        acumulado += cata
                        #print("123*0"+cata+"*0456")
                        bandera4 = 0
                    #if bandera2 == 0 and string == "" and bandera4==0:

                    if acumulado[-5:] == "FINAL":
                        acumulado = acumulado[:-5]
                        print("25")  
                        bandera3 = 1
                        data = acumulado.split("\n")
                        print("25")  
                        for linea in data:
                            vector.append(linea)
                        print("25578")  

                        matriz_data_archivos.append(vector)
                        print("una data registrada")
                        num = len(matriz_data_archivos) -1
                        vector = []
                        break
                print("conexion cerrada")
                
                marca = True
                print("intentado graficar")
                graficas_tiempo_real(num)

            time.sleep(.2)

            contador = 0
            bandera_grafica = False
            #conexion.close()
        threading.Thread(target=lectura).start()


    def mandar_alerta_boton_stop():
        global señal_continua, matriz_data_archivos, Entry_Profundidad_inicial, Entry_Profundidad_final, ruta_guardado
        global socket_tcp
        respuesta = MessageBox.askyesno(message="¿Desea continuar?, se detendrá el recibimiento de data.", title="Alerta")
        if respuesta == True:
            eliminar_botones()
            socket_tcp.send("F".encode('utf-8'))
            señal_continua = False
            nombre_archivo = "profundidad_" + str(Entry_Profundidad_inicial.get())+"-"+str(Entry_Profundidad_final.get())+".ct"

            with open(ruta_guardado+nombre_archivo, "w") as archivo:
                string = "profundidad:"+str(Entry_Profundidad_inicial.get())+","+str(Entry_Profundidad_final.get())+" \n"
                for i in range(1,len(matriz_data_archivos)-1):
                    string += "INICIO_ARCHIVO\n"
                    string += "ARCHIVO:"+str(i)+"\n"
                    string += orden_sensores[-1]+ "\n"
                    for fila in matriz_data_archivos[i]:
                        string += fila + "\n"
                    string += "FIN_ARCHIVO\n"
                archivo.write(string)
                archivo.close()     

            #Boton_play = Button(container3_5, text="►", font=('Times', 20), command=lambda:[cambio_boton_play()])
            #Boton_play.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=(30), pady=(150,10))
            
        elif respuesta == False:
            pass

    def eliminar_botones():
        for l in container3_5.grid_slaves():
            l.destroy()

    def cambio_boton_play():
        global señal_continua, tipo_señal, conexion
        if tipo_señal == "F":
            print("vengo del pause")
            tipo_señal = "M" 
        else:
            print("primera señal")
            tipo_señal = "M"
            
        señal_continua = True
        eliminar_botones()
        #Boton_pausa = Button(container3_5, text="〓", font=('Times', 20), command=lambda:[cambio_boton_pausa()])
        Boton_stop = Button(container3_5, text="STOP", font=('Times', 20), command=lambda:[cambio_boton_stop()])
        #Boton_pausa.grid(row=0, column=0, sticky='nsew', padx=(30,10), pady=(150,10))
        Boton_stop.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=(30), pady=(150,10))
        
        inicio_secuencia_grabado()

    def cambio_boton_pausa():
        global señal_continua, tipo_señal
        señal_continua = False
        tipo_señal = "F"
        eliminar_botones()

        socket_tcp.send("F".encode('utf-8'))
        time.sleep(0.2)
        conexion.close()

        Boton_play = Button(container3_5, text="►", font=('Times', 20), command=lambda:[cambio_boton_play()])
        Boton_play.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=(30), pady=(150,10))
    
    def cambio_boton_stop():

        mandar_alerta_boton_stop()


container6 = Frame((Export), bg=azul_oscuro)
container6.grid(row=0, column=0, sticky='nsew')
container6.grid_rowconfigure(0, weight=1)
container6.grid_rowconfigure(1, weight=20)
container6.grid_columnconfigure(0, weight=5)
container6.grid_columnconfigure(1, weight=1)


Button(container6, text='Regresar', command=lambda:[raise_frame(Review)]).grid(row=0,column=0, sticky='nw')
inicio_final_label = Label(container6, text="")
inicio_final_label.grid(row=0, column=1, sticky='nw')


container6_1 = Frame(container6, bg=azul_claro)
container6_1.grid(row=1, column=0, padx=(30,15), pady=30, sticky= 'nsew')
container6_1.grid_columnconfigure(0, weight=1)

container6_1_1 = Frame(container6_1, bg=azul_oscuro)
container6_1_1.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)

texto_columnas_export = ["Profundidad (m)", "conteo de golpes", "Longitud de Incremento (m)", "BN remanente", "Tasa de golpes (bl/m)", "set/blow (mm/bl)", "Elevación (m)"]

for i in range(7):
    container6_1_1.grid_columnconfigure(i, weight=1)
    Label(container6_1_1, text=texto_columnas_export[i]).grid(row=0, column=i, sticky='nsew')


container6_2 = Frame(container6, bg=azul_claro)
container6_2.grid(row=1, column=1, padx=(15,30), pady=30, sticky= 'nsew')
container6_2.grid_columnconfigure(0, weight=1)

for i in range(5):
    container6_2.grid_rowconfigure(i, weight=1)
Button(container6_2, text="Insertar fila", bg=azul_oscuro, fg='White', command=lambda:Insertar_Fila()).grid(row=0, column=0, sticky='nsew')
Button(container6_2, text="Eliminar fila", bg=azul_oscuro, fg='White', command=lambda:Eliminar_Fila()).grid(row=1, column=0, sticky='nsew')
Button(container6_2, text="Completar", bg=azul_oscuro, fg='White', command=lambda:Completar_Filas()).grid(row=2, column=0, sticky='nsew')
Button(container6_2, text="Seleccionar \Ruta", bg=azul_oscuro, fg='White', command=lambda:Seleccionar_ruta_guardado_pdf()).grid(row=3, column=0, sticky='nsew')
Button(container6_2, text="Exportar \nPDF", bg=azul_oscuro, fg='White', command=lambda: [mostrar_alertas_exportar()]).grid(row=4, column=0, sticky='nsew')

filas = []
contador_fila = 1
fila_grabada = []

def Seleccionar_ruta_guardado_pdf():
    global ruta_guardado_pdf
    ruta_guardado_pdf = filedialog.askdirectory(initialdir = "/", title = "Selecciona una carpeta")


def Insertar_Fila():
    global filas, contador_fila
    fila_grabada = []
    for i in range(7):
        fila_grabada.append(Entry(container6_1_1)) 
        fila_grabada[i].grid(row=contador_fila, column=i, sticky='nsew')
    filas.append(fila_grabada)
    contador_fila +=1

Num_golpes = []
Num_golpes_modificado = []

def Eliminar_Fila():
    global filas
    for i in range(len(filas[-1])):
        filas[-1][i].destroy()
    filas.pop()


def mostrar_alertas_exportar():
    global filas, Num_golpes, Num_golpes_modificado, matriz_data_archivos, ruta_guardado_pdf
    contador = 0
    longitudes = matriz_data_archivos[0][12:].split(",")
    for fila in filas:
        for i in range(len(fila)):
            if str(fila[i].get()) != "":
                contador += 1
    print(filas[0][0].get(), filas[-1][0].get())
    if contador  != len(filas)*len(filas[0]):
        MessageBox.showerror("Error", "Inserte todos los datos")  
    elif str(float(filas[0][0].get())) != str(float(longitudes[1])) or str(float(filas[-1][0].get())) != str(float(longitudes[0])):
        MessageBox.showerror("Error", "Las longitudes iniciales y finales no coinciden")
    elif sum(Num_golpes) != len(matriz_data_archivos)-1:
        MessageBox.showerror("Error", "La cantidad de golpes insertada no concuerda con la del archivo")
    elif ruta_guardado_pdf == "":
        MessageBox.showerror("Error", "Seleccione una ruta de guardado")
    else:
        Calcular_Promedios()


def Completar_Filas():
    global filas, Num_golpes, Num_golpes_modificado
    Num_golpes = []
    Num_golpes_modificado = []
    contador = 0
    
    for fila in filas:
        if fila[0].get() != "" and fila[1].get() != "":
            contador += 1 
    if contador == len(filas):
        for i in range(len(filas)):
            Num_golpes.append(int(filas[i][1].get()))
        Num_golpes_modificado = []
        total = sum(Num_golpes)

        for i in range(len(filas)):
            # proceso de borrado de las últimas columnas:
            for j in range(2, len(filas[0])):
                filas[i][j].delete(0, END)

        for i in range(len(Num_golpes)):
            print(i, total, Num_golpes[i])
            Num_golpes_modificado.append(total)
            total = total-Num_golpes[i]
        print(Num_golpes_modificado)
        

        for i in range(len(Num_golpes)):
            try:
                filas[i][2].insert(0, str(round(float(filas[i][0].get())-float(filas[i+1][0].get()),2)))
            except:
                filas[i][2].insert(0, 0)
            filas[i][3].insert(0, Num_golpes_modificado[i])
            try:
                filas[i][4].insert(0, str(round(Num_golpes[i]/float(filas[i][2].get()),3)))
            except:
                filas[i][4].insert(0, 0)
            try:
                filas[i][5].insert(0, str(round(float(filas[i][2].get())/Num_golpes[i],5)))
            except:
                filas[i][5].insert(0, 0)
            try:    
                filas[i][6].insert(0, str(float(filas[i][0].get())*-1))
            except:
                filas[i][6].insert(0, 0)

fila_resumen = []



def obtener_datos_grafica(j):
    global Energias, Fuerzas, Velocidades, Energias_teoricas, Impedancias, orden_sensores, frecuencia_muestreo, pile_area, EM_valor_original, ET_valor_original, matriz_data_archivos, Num_golpes, Num_golpes_modificado, segundo_inicial, segundo_final, fila_resumen
    orden = str(orden_sensores[-1]).replace(" ","").split("|")
    segundos = []
    S1 = []
    S2 = []
    A3 = []
    A4 = []
    F1 = []
    F2 = []
    F = []
    V1 = []
    V2 = []
    V = []
    E = []
    D1 = []
    D2 = []
    D = []
    SIN1 = []
    SIN2 = []
    SIN3 = []
    SIN4 = []
    NULL = []
    
    V_Transformado = []
    V_Transformado_valor_real = []
    dic_orden_sensores = {"1":A3, "2":A4, "3":S1, "4":S2, "5":S1, "6":S2, "0":NULL}
    dic_orden_sensores2 = {"1":SIN1, "2":SIN2, "3":SIN3, "4":SIN4, "5":SIN3, "6":SIN4, "0": NULL}
    
    for index,linea in enumerate(matriz_data_archivos[j]):
        linea = linea.split("|")
        if index > 0 and index < len(matriz_data_archivos[j])-1:
            segundos.append(float(linea[0])/1000)
            for i in range(4):
                #dic_orden_sensores2[orden[i]].append(float(linea[i+1])*dic_factor_conversion_producto[orden[i]]+dic_factor_conversion_suma[orden[i]])
                dic_orden_sensores2[orden[i]].append(float(linea[i+1]))
        else:
            pass
          

    for i in range(4):
        #dic_orden_sensores[orden[i]] = list(correcion_linea_cero(dic_orden_sensores2[orden[i]]))
        if ((int(orden[i]) == 1)) or (int(orden[i]) == 2):
            print('corregidos')
            for datos in filtrado(correcion_linea_cero(dic_orden_sensores2[orden[i]])):
                dic_orden_sensores[orden[i]].append(datos)
        elif (int(orden[i])!=0):
            print('sin corregir')
            for datos in dic_orden_sensores2[orden[i]]:               
                dic_orden_sensores[orden[i]].append(datos)
    
    EM = float(EM_valor_original)
    AR = float(pile_area)
    factor = EM*AR
    longitud = max(len(S1), len(S2))
    m1 = 0
    m2 = 0
    
    for i in range(longitud):
        try:
            m1 = S1[i]*factor/10000000
        except:
            pass
        try:
            m2 = S2[i]*factor/10000000
        except:
            pass
        promedio = (m1+m2)/2
        if S1 != []:
            F1.append(m1)
        if S2 != []:
            F2.append(m2)
        F.append(promedio)
    if S1 == []:
        F = F2
    elif S2 == []:
        F = F1
    Fmax = round(max(F), 2)
    Fmax_original = max(F)
    suma_velocidadv1 = 0
    suma_velocidadv2 = 0
    longitud = max(len(A3), len(A4))
    for i in range(longitud):
        try:
            if i == 0:
                suma_velocidadv1 += ((A3[i]+0)*9.81)*(1/(int(frecuencia_muestreo[-1])*1000))/2
            else:
                suma_velocidadv1 += ((A3[i]+A3[i-1])*9.81)*(1/(int(frecuencia_muestreo[-1])*1000))/2
            V1.append(suma_velocidadv1)
        except:
            pass
        try:    
            if i == 0:
                suma_velocidadv2 += ((A4[i]+0)*9.81)*(1/(int(frecuencia_muestreo[-1])*1000))/2
            else:
                suma_velocidadv2 += ((A4[i]+A4[i-1])*9.81)*(1/(int(frecuencia_muestreo[-1])*1000))/2
            V2.append(suma_velocidadv2)
        except:
            pass
        promedio = (suma_velocidadv1 + suma_velocidadv2)/2
        V.append(promedio)
    if A3 == []:
        V = V2
    elif A4 == []:
        V = V1
    Vmax = round(max(V), 2)
    Vmax_original = max(V)
    suma_desplazamientov1 = 0
    suma_desplazamientov2 = 0
    longitud = max(len(S1), len(S2))
    for i in range(longitud):
        try:
            if i == 0:
                suma_desplazamientov1 += ((V1[i]+0))*(1/(int(frecuencia_muestreo[-1])*1000))/2
            else:
                suma_desplazamientov1 += ((V1[i]+V1[i-1]))*(1/(int(frecuencia_muestreo[-1])*1000))/2
            D1.append(suma_desplazamientov1)
        except:
            pass
        try:
            if i == 0:
                suma_desplazamientov2 += ((V2[i]+0))*(1/(int(frecuencia_muestreo[-1])*1000))/2
            else:
                suma_desplazamientov2 += ((V2[i]+V2[i-1]))*(1/(int(frecuencia_muestreo[-1])*1000))/2
            D2.append(suma_desplazamientov2)
        except:
            pass
        promedio = (suma_desplazamientov1 + suma_desplazamientov2)/2
        D.append(promedio)
    if V1 == []:
        D = D2
    elif V2 == []:
        D = D1

    Dmax = round(max(D), 2)
    
    bandera = 0
    bandera2 = 0
    anterior = 0
    Z = Fmax_original/Vmax_original
    
    imax = F.index(Fmax_original)
    ajuste = V.index(Vmax_original)-imax
    
    for i in range(len(V)):
        valor = V[i]*Z
        V_Transformado.append(valor)
        V_Transformado_valor_real.append(V[i])
    suma_energia = 0
    j = 0
    segundos_Transformado = []
    segundo_inicial = float(segundo_inicial)
    segundo_final = float(segundo_final)
    for i in range(segundos.index(round(segundo_inicial,2)),segundos.index(round(segundo_final,2))):
        if i == 0:
            suma_energia += (((V_Transformado_valor_real[i]*F[i])+(0)))*(1/(int(frecuencia_muestreo[-1])))/2
        else:
            suma_energia += (((V_Transformado_valor_real[i]*F[i])+(V_Transformado_valor_real[i-1]*F[i-1])))*(1/(int(frecuencia_muestreo[-1])))/2
        E.append(suma_energia)
        n = round(segundo_inicial+(j/(int(frecuencia_muestreo[-1]))),2)
        j+=1
        segundos_Transformado.append(n)
    try:
        Emax = round(max(E), 2)
    except:
        pass
    Energias.append(Emax)
    Velocidades.append(Vmax)
    Fuerzas.append(Fmax)
    Energias_teoricas.append(round(Emax*100/float(ET_valor_original),2))
    Impedancias.append(Fmax/Vmax)
    
    return F, V_Transformado, segundos, Z

Energias = []
Fuerzas = []
Velocidades = []
Energias_teoricas = []
Impedancias = []

def Calcular_Promedios():
    global Energias, Fuerzas, Velocidades, Energias_teoricas, Impedancias, orden_sensores, frecuencia_muestreo, pile_area, EM_valor_original, ET_valor_original, matriz_data_archivos, Num_golpes, Num_golpes_modificado, segundo_inicial, segundo_final, fila_resumen
    orden = str(orden_sensores[-1]).replace(" ","").split("|")

    if len(orden[4])>1:
        frecuencia_muestreo.append(orden[4])

    try:
        pile_area = orden[5]
    except:
        pile_area = "15.6"
        print("algo está mal")
    try:
        EM_valor_original = orden[6]
    except:
        EM_valor_original = "207000"
        
    Energias = []
    Fuerzas = []
    Velocidades = [] 
    Energias_teoricas = []
    Impedancias = []
    for j in range(1, len(matriz_data_archivos)):
        obtener_datos_grafica(j)
        
    maxZ = Impedancias.index(max(Impedancias))
    
    #Aquí se añade una fila más a cada variable de arriba Energias, fuerzas, etc, por lo cual se le quita una fila a cada una abajo

    Fuerzas_impedancia_maxima, Velocidades_impedancia_maxima, segundos, Z = obtener_datos_grafica(maxZ+1)

    Energias.pop()
    Fuerzas.pop()
    Velocidades.pop()
    Energias_teoricas.pop()
    Energias_teoricas = [num*100 for num in Energias_teoricas]

    datas = [[["", "BL#", "BC", "FMX", "VMX", "BPM", "EFV", "ETR"],["", "", "/150mm", "tn", "m/s", "bpm", "J", "%"]], [], []]
    Num_golpes_modificado2 = []
    Num_golpes_modificado2.append(0)
    acumulado = 0
    
    for i in range(len(Num_golpes)-1):
        acumulado += Num_golpes[len(Num_golpes)-i-2]
        Num_golpes_modificado2.append(acumulado)

    #print("datos generacion pdf",Num_golpes, Num_golpes_modificado2, len(Energias), len(Velocidades), len(Fuerzas), len(matriz_data_archivos))
    # Estos Arreglos energias, velocidades, etc, son globales así que en las funciones obtener_datos_grafica ya se añaden los valores
    # recortando las energias, velocidades, fuerzas y energias teoricas máximas
        
    Energias_recortadas = Energias[Num_golpes[-2]:]
    Velocidades_recortadas = Velocidades[Num_golpes[-2]:]
    Fuerzas_recortadas = Fuerzas[Num_golpes[-2]:]
    Energias_teoricas_recortadas = Energias_teoricas[Num_golpes[-2]:]
    print("prueba",Energias_teoricas,Energias_teoricas_recortadas,Energias, Energias_recortadas, Num_golpes[-2])
    orden_golpes = []
    for i in range(len(Num_golpes)-1):
        orden_golpes.append(Num_golpes[len(Num_golpes)-i-2])
    fila_resumen = []
    fila_resumen.append('5') # primera columna del resumen
    fila_resumen.append(str(orden_golpes)) # los golpes en orden
    fila_resumen.append(str(sum(Num_golpes))) # total de golpes
    fila_resumen.append(str(round((sum(Num_golpes)*sum(Energias_teoricas_recortadas))/(len(Energias_teoricas_recortadas)*60),0))) # 
    fila_resumen.append(str(round(sum(Fuerzas_recortadas)/len(Fuerzas_recortadas),1)))
    fila_resumen.append(str(round(sum(Velocidades_recortadas)/len(Velocidades_recortadas),1)))
    fila_resumen.append(str(round(random.random()*30,2)))
    fila_resumen.append(str(round(sum(Energias_recortadas)/len(Energias_recortadas),1)))
    fila_resumen.append(str(round(sum(Energias_teoricas_recortadas)/len(Energias_teoricas_recortadas),1)))

    for j in range(3):
        for i in range(Num_golpes_modificado2[j],Num_golpes_modificado2[j+1]):
            try:
                datas[j].append(["",str(i+1),str(orden_golpes[j]),str(Fuerzas[i]), str(Velocidades[i]), str(round(random.random()*30,2)), str(round(float(Energias[i]),2)),str(round(float(Energias_teoricas[i]),2))])
            except Exception as e:
                print(i, j, e)
    #Graficar y convertirla en imagen
    
    style.use('ggplot')
    f = Figure(figsize=(15,5), dpi=300)
    a = f.add_subplot(111)
    t1, = a.plot(segundos, Fuerzas_impedancia_maxima, label= "F")
    t2, = a.plot(segundos, Velocidades_impedancia_maxima, label=str(round(Z, 2))+"*V")
    #a.axis('off')
    try:
        a.legend(handles=[t1, t2])
    except:
        try:
            a.legend(handles=[t1])
        except:
            try:
                a.legend(handles=[t2])
            except:
                pass
    a.tick_params (left = False ,
                 bottom = False,
                 labelleft = False ,
                 labelbottom = False )
    canvas = FigureCanvas(f)
    canvas.draw()
    img = Image.fromarray(np.asarray(canvas.buffer_rgba()))
    crear_pdf(datas, img)
    MessageBox.showinfo(title="Exportado", message="Se ha exportado con éxito")

def crear_pdf(datas, img):
    global pile_area, EM_valor_original, ET_valor_original, fila_resumen, ruta_data_inicial, ruta_guardado_pdf
    nombre_archivo = ""
    cadenas =ruta_data_inicial.split("/")[-1][:-3]
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Times", size=12)
    line_height = pdf.font_size * 1.5
    pdf.set_margin(20)
    pdf.cell(0, 10, "Kallpa Processor")
    pdf.set_font("Times", size=8)

    pdf.set_line_width(0.1)
    pdf.line(x1=20, y1=28, x2=185, y2=28)

    pdf.ln(line_height)
    pdf.cell(0, 10, "AR: "+ str(pile_area))
    pdf.ln(line_height*0.5)
    pdf.cell(0, 10, "EM: "+ str(EM_valor_original))
    pdf.ln(line_height*0.5)
    pdf.cell(0, 10, "ET: "+ str(ET_valor_original))
    pdf.ln(line_height*2)
    
    pdf.set_margin(10)

    pdf.line(x1=20, y1=40, x2=185, y2=40)

    pdf.image(img, w=pdf.epw, h=70, x=5)

    pdf.set_margin(20)
    col_width = pdf.epw / 2
    sensores = [["F1 : [590AW1] 204.51 PDICAL (1) FF2", "F2 : [590AW2] 203.63 PDICAL (1) FF2"],["A3 (PR): [K11669] 395.805 mv/6.4v/5000g (1) VF2", "A4 (PR): [K11670] 418.207 mv/6.4v/5000g (1) VF2"]]
    for row in sensores:
        for datum in row:
            pdf.multi_cell(col_width, line_height, datum, border=0,
                    new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
        pdf.ln(line_height)
    col_width = pdf.epw / 5
    legendas = ["FMX: Fuerza Máxima", "VMX: Velocidad Máxima", "BPM: Golpes/Minuto", "EFV: Energía Máxima", "ETR: Energía Teórica"]
    for datum in legendas:
        pdf.multi_cell(col_width, line_height, datum, border=0,
                new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
    pdf.ln(10)
    pdf.set_draw_color(r=0, g=0, b=0)

    pdf.set_line_width(0.1)
    pdf.line(x1=20, y1=138, x2=185, y2=138)

    col_width = pdf.epw / 8
    for row in datas[0]:
        for datum in row:
            pdf.multi_cell(col_width, line_height, datum, border=0,
                    new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
        pdf.ln(line_height)
    pdf.set_line_width(0.1)
    y = 138+len(datas[0])*line_height
    print(y)
    pdf.line(x1=20, y1=y, x2=185, y2=y)
    for row in datas[1]:
        for datum in row:
            pdf.multi_cell(col_width, line_height, datum, border=0,
                    new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
        pdf.ln(line_height)
    for row in datas[2]:
        for datum in row:
            pdf.multi_cell(col_width, line_height, datum, border=0,
                    new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
        pdf.ln(line_height)
    pdf.set_line_width(0.1)
    y= pdf.get_y()
    pdf.line(x1=20, y1=y, x2=185, y2=y)

    pdf.ln(10)
    pdf.cell(0, 10, "Resultado Resumen")
    pdf.ln(line_height)

    y= pdf.get_y()
    pdf.line(x1=20, y1=y, x2=185, y2=y)
    col_width = pdf.epw / 9
    cabezera_resumen = [["Instr.", "Blows", "N", "N60", "Average", "Average", "Average", "Average", "Average"], 
    ["Length", "Applied", "Value", "Value", "FMX", "VMX", "BPM", "EFV", "ETR"], ["m", "/150mm", "", "", "tn", "m/s", "bpm", "J", "%"]]

    for row in cabezera_resumen:
        for datum in row:
            pdf.multi_cell(col_width, line_height, datum, border=0,
                    new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
        pdf.ln(line_height)
    
    y= pdf.get_y()
    pdf.line(x1=20, y1=y, x2=185, y2=y)
    print(fila_resumen)
    for column in fila_resumen:
        pdf.multi_cell(col_width, line_height, column, border=0,
                    new_x="RIGHT", new_y="TOP", max_line_height=pdf.font_size)
    pdf.ln(line_height)
    
    y= pdf.get_y()
    pdf.line(x1=20, y1=y, x2=185, y2=y)
    
    pdf.set_font("Times", size=12)
    # Cuadro Resumen

    nombre_archivo = 'Informe_' + cadenas + '.pdf'
    print(nombre_archivo)
    pdf.output(ruta_guardado_pdf + "/" + nombre_archivo)

container7 = Frame((About), bg=azul_oscuro)
container7.grid(row=0, column=0, sticky='nsew')

container7.grid_rowconfigure(0, weight=1)
container7.grid_rowconfigure(1, weight=5)
container7.grid_rowconfigure(2, weight=15)
container7.grid_columnconfigure(0, weight=1)
container7.grid_columnconfigure(1, weight=5)
container7.grid_columnconfigure(2, weight=5)
container7.grid_columnconfigure(3, weight=1)

Button(container7, text="Regresar", command=lambda:raise_frame(Menup)).grid(row=0, column=0, sticky='nsew')

Label(container7, text="Kallpa Procesor hecho por el CITDI", font=('Times', 20), bg=azul_celeste, fg='White').grid(row=1, column=1, columnspan=2, sticky='nsew', padx=20, pady=20)
Label(container7, text="Creado con colaboración de:\nCarmen Ortiz Salas\nGrover Rios Soto\nRoberto Raucana Sulca\nJoseph Mottoccanche Tantaruna", font=('Times', 20), bg=azul_celeste, fg='White').grid(row=2, column=1, columnspan=2, sticky='nsew', padx=20, pady=(20,40))


raise_frame(Menup)

root.mainloop()