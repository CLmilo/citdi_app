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
import threading
from tkinter import messagebox as MessageBox
import numpy as np
from fpdf import FPDF
import customtkinter as ctk
from BaselineRemoval import BaselineRemoval
import obspy
from obspy.core.trace import Trace
import xlsxwriter

import socket

#colores
azul_oscuro = "#002060"
azul_claro = "#BDD7EE"
azul_celeste = "#2F6CDF"

ctk.set_appearance_mode("light")  # Modes: system (default), light, dark

ctk.set_default_color_theme("citdi_theme.json")

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
    tr = Trace(data=np.array(valores)*0.1475)
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
    tr.stats.sampling_rate = 50000
    st3 = tr.copy()
    #st3.filter(type="bandpass",freqmin=0.012,freqmax = 0.032)
    st3.filter(type="bandpass",freqmin=1,freqmax = 5000)
    z = np.ndarray.tolist(st3.data)
    return z

def filtrado2(valores):
    z = []
    nuevo = []
    nuevo.append(valores[0])
    for i in range(1,len(valores)-1):
        valor_anterior = valores[i-1]
        valor_despues = valores[i+1]
        valor_actual = valores[i]
        promedio = (valor_anterior+valor_despues)/2
        if valor_actual>70000 and (valor_anterior<30000 and valor_despues<30000):
            nuevo.append(promedio)
        else:
            nuevo.append(valor_actual)
    nuevo.append(valores[-1])
    print("esto es lo nuevo", len(nuevo))
    tr = Trace(data=np.array(nuevo))
    tr.stats.sampling_rate = 50000
    st3 = tr.copy()
    st3.filter(type="bandpass",freqmin=1,freqmax = 3000)
    z = np.ndarray.tolist(st3.data/200)
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
    ruta_data_inicial = filedialog.askopenfilename(initialdir = "/", title = "Select a File", filetypes = [("CT files", "*.ct*")])   
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
    global estado_parametros, frecuencia_muestreo, matriz_data_archivos, pile_area, EM_valor_original, ET_valor_original, segundo_final, segundo_inicial
    global orden_sensores, ruta_data_inicial
    global S1, S2, A3, A4
    global ET_valor_original, EM_valor_original_backup, pile_area_backup
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

    print("Estamos en obtencion data serial")
    print("El orden de los sensores es2: ", orden_sensores)

    dic_orden_sensores = {"1":A3, "2":A4, "3":S1, "4":S2, "5":S1, "6":S2, "0":NULL}
    dic_orden_sensores2 = {"1":SIN1, "2":SIN2, "3":SIN3, "4":SIN4, "5":SIN3, "6":SIN4, "0": NULL}

    orden = str(orden_sensores[-1]).replace(" ","").split("|")
    print("la fila orden es", orden_sensores[-1])

    if len(orden[4])>1:
        frecuencia_muestreo.append(int(orden[4]))

    if estado_parametros == "original":
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
        EM_valor_original_backup = EM_valor_original
        ET_valor_original_backup = ET_valor_original
        pile_area_backup = pile_area
    else:
        pass

    extension = ruta_data_inicial.split("/")[-1].split(".")[-1]
    print(extension)
    if extension == "ctn":
        data = matriz_data_archivos[num]
        
        for linea in data:
            linea = linea.split("|")
            segundos.append(float(linea[0])/10)
            for j in range(4):
                dic_orden_sensores[orden[j]].append(round(float(linea[j+1]),2))
        segundo_inicial = segundos[0]
        segundo_final = segundos[-1]

        
    else:
        for index,linea in enumerate(matriz_data_archivos[num]):
            linea = linea.split("|")
            if index > 0 and index < len(matriz_data_archivos[num])-1:
                segundos.append(float(linea[0])/1000)
                for i in range(4):
                    dic_orden_sensores2[orden[i]].append(float(linea[i+1]))
            else:
                pass
        segundo_inicial = segundos[0]
        segundo_final = segundos[-1]

        for i in range(4):

            if ((int(orden[i]) == 1)) or (int(orden[i]) == 2):
                for datos in filtrado(correcion_linea_cero(dic_orden_sensores2[orden[i]])):
                    dic_orden_sensores[orden[i]].append(datos)
            elif (int(orden[i])!=0):
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
Review = ctk.CTkFrame(root)
Menup = ctk.CTkFrame(root)
Collect_Wire = ctk.CTkFrame(root)
Opciones = ctk.CTkFrame(root)

for frame in (Menup, Review, Opciones):
    frame.grid_rowconfigure(0,weight=1)
    frame.grid_columnconfigure(0,weight=1)
    frame.grid(row=0, column=0, sticky='nsew')

# FRAME INICIAL
container4a = ctk.CTkFrame(master= Menup, corner_radius = 20)

container4a.grid_rowconfigure(0, weight=1)
container4a.grid_rowconfigure(1, weight=1)
container4a.grid_columnconfigure(0, weight=1)
container4a.grid(row=0, column=0, sticky='nsew', padx=40, pady=40)

container4b = ctk.CTkFrame(container4a, corner_radius=20, fg_color="#BADCF1")
container4b.grid(row=0, column=0, sticky='nsew', padx=40, pady=(40,0))

container4b.grid_rowconfigure(0, weight=10)
container4b.grid_rowconfigure(1, weight=2)
container4b.grid_columnconfigure(0, weight=1)
container4b.grid_columnconfigure(1, weight=10)
container4b.grid_columnconfigure(2, weight=1)


container4c = ctk.CTkFrame(container4a, corner_radius=10)
container4c.grid(row=1, column=0, sticky='nsew', padx=40, pady=(20,40))
container4c.grid_rowconfigure(0, weight=1)
# Botones
lista_botones = ["Salir", "Review", "New Review", "Preparar Data", "Manual", "About"]

for i in range(len(lista_botones)):
    container4c.grid_columnconfigure(i, weight=1)

#Button(container4, text=lista_botones[0], bg=azul_oscuro, font=('Arial', 25), fg='#FFFFFF',command=lambda:root.destroy()).grid(row=4,column=0, sticky='nsew')
ctk.CTkButton(container4c, text=lista_botones[0], font=('Arial', 25), command=lambda:root.destroy()).grid(row=0,column=0, sticky='nsew', padx=5, pady=5)
ctk.CTkButton(container4c, text=lista_botones[1], font=('Arial', 25), command=lambda:[browseFiles(), Creacion_Grafica("arriba","aceleracion", numero_grafica_actual, "original", "NO", "NO"), Creacion_Grafica("abajo", "deformacion", numero_grafica_actual, "original", "NO", "NO"), actualizar_valores_cabecera(), raise_frame(Review)]).grid(row=0,column=1, sticky='nsew', pady=5, padx=(0,5))
ctk.CTkButton(container4c, text=lista_botones[2], font=('Arial', 25), command=lambda:preview_data()).grid(row=0,column=2,sticky='nsew',padx=5,pady=5)
ctk.CTkButton(container4c, text=lista_botones[3], font=('Arial', 25), command=lambda:create_toplevel_preparar()).grid(row=0,column=3, sticky='nsew', pady=5, padx=(0,5))
ctk.CTkButton(container4c, text=lista_botones[4], font=('Arial', 25), command=lambda:print("manual")).grid(row=0,column=4, sticky='nsew', pady=5, padx=(0,5))
ctk.CTkButton(container4c, text=lista_botones[5], font=('Arial', 25), command=lambda:create_toplevel_about()).grid(row=0,column=5, sticky='nsew', pady=5, padx=(0,5))

# Mostrar Hora
def Obtener_hora_actual():
    return datetime.now().strftime("%d-%m-%y,%H:%M:%S")

def refrescar_reloj():
    hora_actual.set(Obtener_hora_actual())
    container4b.after(300, refrescar_reloj)

hora_actual = StringVar(container4b, value=Obtener_hora_actual())

refrescar_reloj()

# AÑADIR PORTADA

def resolver_ruta(ruta_relativa):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, ruta_relativa)
    return os.path.join(os.path.abspath('.'), ruta_relativa)


nombre_archivo_portada = resolver_ruta("CITDI_LOGO_SINFONDO.png")

imagen = PhotoImage(file=nombre_archivo_portada)
imagen = imagen.zoom(2, 2)
new_imagen = imagen.subsample(5, 5)

ctk.CTkLabel(container4b, image=new_imagen, text="").grid(row=0,column=1, columnspan=2, padx=(40), pady=40)

ctk.CTkLabel(container4b, font=('Arial', 100), text="Kallpa Processor").grid(row=0, column=0, sticky='nsw', padx=(40,0), pady=20)

switch_var = ctk.StringVar(value="off")

def cambiar_tema(color):
    ctk.set_appearance_mode(color)

def switch_event():
    print(str(switch_var.get()))
    if str(switch_var.get()) == "on":
        cambiar_tema("dark")
    else:
        cambiar_tema("light")

switch_1 = ctk.CTkSwitch(container4b, text="Tema Oscuro", font=('Arial', 25), command=switch_event,
                                   variable=switch_var, onvalue="on", offvalue="off")

switch_1.grid(row=2, column=2, sticky='nse', padx= 40, pady=20)
ctk.CTkLabel(container4b, textvariable=hora_actual, font=('Arial', 25)).grid(row=2, column=0, sticky='nsw', padx= 20, pady=20)

# FRAME DE OPERACIONES

container = ctk.CTkFrame(Review)
container.grid(row=0, column=0, sticky='nsew')

container.grid_rowconfigure(0,weight=1)
container.grid_columnconfigure(0, weight=1)
container.grid_columnconfigure(1, weight=20)
container.grid_columnconfigure(2, weight=1)


#---------------------------------------------------------------
# Frame de la izquierda

container1 = ctk.CTkFrame(container)
container1.grid(row=0, column=0, sticky='nsew')
container1.grid_columnconfigure(0, weight=1)

# Frames internos

container1_0 = ctk.CTkFrame(container1)
container1_0.grid(row=0, column=0, padx=20, pady=(40,10), sticky='new')
container1_0.grid_columnconfigure(0, weight=1)
container1_0.grid_columnconfigure(1, weight=1)

estado_parametros = "original"
EM_valor_original_backup = ""
ET_valor_original_backup = ""
pile_area_backup = ""

def actualizar_magnitud(posicion,i):
    global ultima_magnitud_abajo
    global ultima_magnitud_arriba
    dic_ultima_grafica_magnitud[posicion] = dic_magnitud_botones[i]

texto_botones_frame= ["ACELERACIÓN", "VELOCIDAD", "DEFORMACIÓN", "FUERZA", "DESPLAZAMIENTO", "F vs V", "Avg ED"]

# Estos botones están fuera de un bucle for por usar una función lambda dentro de sus comandos, los cuales dan i como 3 siempre que se ejecutan

def segmented_button_callback1(value):
    global texto_botones_frame
    colorear_botones_seleccion_grafica(1)
    match value:
        case "ACELERACIÓN":
            cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
            actualizar_magnitud("arriba", texto_botones_frame.index(value))
        case "VELOCIDAD":
            cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
            actualizar_magnitud("arriba", texto_botones_frame.index(value))
        case "DEFORMACIÓN":
            cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
            actualizar_magnitud("arriba", texto_botones_frame.index(value))
        case "FUERZA":
            cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
            actualizar_magnitud("arriba", texto_botones_frame.index(value))
        case "DESPLAZAMIENTO":
            cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
            actualizar_magnitud("arriba", texto_botones_frame.index(value))
        case "F vs V":
            cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
            actualizar_magnitud("arriba", texto_botones_frame.index(value))
        case "Avg ED":
            cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
            actualizar_magnitud("arriba", texto_botones_frame.index(value))
            
def segmented_button_callback2(value):
    global texto_botones_frame
    colorear_botones_seleccion_grafica(2)
    match value:
        case "ACELERACIÓN":
            cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
            actualizar_magnitud("abajo", texto_botones_frame.index(value))
        case "VELOCIDAD":
            cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
            actualizar_magnitud("abajo", texto_botones_frame.index(value))
        case "DEFORMACIÓN":
            cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
            actualizar_magnitud("abajo", texto_botones_frame.index(value))
        case "FUERZA":
            cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
            actualizar_magnitud("abajo", texto_botones_frame.index(value))
        case "DESPLAZAMIENTO":
            cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
            actualizar_magnitud("abajo", texto_botones_frame.index(value))
        case "F vs V":
            cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
            actualizar_magnitud("abajo", texto_botones_frame.index(value))
        case "Avg ED":
            cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
            actualizar_magnitud("abajo", texto_botones_frame.index(value))

def cambiar_valores(mod):
    global pile_area, EM_valor_original, ET_valor_original, estado_parametros
    global pile_area_entry, EM_Entry, ET_Entry
    global ET_valor_original, EM_valor_original_backup, pile_area_backup
    if mod == "modificado":
        estado_parametros = "modificado"
        pile_area = pile_area_entry.get()
        EM_valor_original = EM_Entry.get()
        ET_valor_original = ET_Entry.get()
        segmented_button_callback2("DEFORMACIÓN")
        segmented_button_callback1("ACELERACIÓN")
        
    else:
        estado_parametros = "original"
        pile_area_entry.delete(0, END)
        EM_Entry.delete(0, END)
        ET_Entry.delete(0, END)

        pile_area_entry.insert(0, pile_area_backup)
        EM_Entry.insert(0, EM_valor_original_backup)
        ET_Entry.insert(0, ET_valor_original)

        cambiar_magnitud_grafica("arriba", 0)
        actualizar_magnitud("arriba", 0)
        cambiar_magnitud_grafica("abajo", 0)
        actualizar_magnitud("abajo", 0)


ctk.CTkButton(container1_0, text='Regresar', command=lambda:raise_frame(Menup)).grid(row=0,column=0, sticky='nsew', padx=(5,0) , pady=5)
ctk.CTkButton(container1_0, text='Calcular', command=lambda:cambiar_valores("modificado")).grid(row=0,column=1, sticky='nsew', padx=(5) , pady=5)

container1_1 = ctk.CTkFrame(container1)
container1_1.grid(row=1, column=0, padx=20, pady=(0,10), sticky='new')
container1_1.grid_columnconfigure(0, weight=1)
container1_1.grid_columnconfigure(1, weight=1)

container1_2 = ctk.CTkFrame(container1)
container1_2.grid(row=2, column=0, padx=20, pady=10, sticky='new')
container1_2.grid_columnconfigure(0, weight=1)
container1_2.grid_columnconfigure(1, weight=1)

# Textos y Entrys Primer Frame
#textos_primer_frame = ["Pile ID", "Total Length(m)", "Pile Length(m)", "Penetration(m)", "Pile Area(m^2)", "Wave Speed(m/s)", "Overall WS(m/s)", "Density(m^3)", "Elastic Modulus(GPa)", "Jc" ]
textos_primer_frame = ["Área(cm^2)", "M. Elasticidad(MPa)", "Energía Teórica(J)"]

#ET_Entry

ctk.CTkLabel(container1_1, text=textos_primer_frame[0]).grid(row=0,column=0, padx=10, pady=10, sticky='nw')
pile_area_entry = ctk.CTkEntry(container1_1)
pile_area_entry.grid(row=0, column=1, padx=10, pady=10, sticky='new')

ctk.CTkLabel(container1_1, text=textos_primer_frame[1]).grid(row=1,column=0, padx=10, pady=10, sticky='nw') 
EM_Entry = ctk.CTkEntry(container1_1)
EM_Entry.grid(row=1, column=1, padx=10, pady=10, sticky='new')

ctk.CTkLabel(container1_1, text=textos_primer_frame[2]).grid(row=2,column=0, padx=10, pady=10, sticky='nw')
ET_Entry = ctk.CTkEntry(container1_1)
ET_Entry.grid(row=2, column=1, padx=10, pady=10, sticky='new')

ctk.CTkButton(container1_1, text='Restaurar', command=lambda:cambiar_valores("original")).grid(row=3,column=0, columnspan=2, sticky='nsew', padx=(10) , pady=10)

def actualizar_valores_cabecera():
    try:
        pile_area_entry.delete(0, END)
        pile_area_entry.insert(0, str(round(float(pile_area),2)))
    except:
        pile_area_entry.delete(0, END)
        pile_area_entry.insert(0, "7.56")
    try:
        EM_Entry.delete(0, END)
        EM_Entry.insert(0, str(round(float(EM_valor_original),2)))
    except:
        EM_Entry.delete(0, END)
        EM_Entry.insert(0, "20700")
    try:
        ET_Entry.delete(0, END)
        ET_Entry.insert(0, str(round(float(ET_valor_original),2)))
    except:
        ET_Entry.delete(0, END)
        ET_Entry.insert(0, "473")


# Textos y Entrys Segundo Frame
#textos_segundo_frame = ["BL #", "RSP(kN)", "RMX(kN)", "RSU(kN)", "FMX(kN)", "VMX(m/s)", "EMX(kN.m)", "DMX(mm)", "DFN(mm)", "CSX(MPa)", "TSX(MPa)", "BTA"]

Label_Num_Grafica = ctk.CTkLabel(container1_2, text="")
Label_Num_Grafica.grid(row=0,column=0, columnspan=2, padx=10, pady=10, sticky='new') 

textos_segundo_frame = ["FMX(kN)", "VMX(m/s)", "EMX(J)", "DMX(cm)", "ETR", "CE"]
valores_segundo_frame_arriba = ["","", "", "", "", "", ""]
valores_segundo_frame_abajo = ["","", "", "", "", "", ""]

ctk.CTkLabel(container1_2, text=textos_segundo_frame[0]).grid(row=1,column=0, padx=10, pady=10, sticky='nw') 
L_FMX = ctk.CTkLabel(container1_2, text=valores_segundo_frame_arriba[0])
L_FMX.grid(row=1, column=1,padx=10, pady=10, sticky='nwe')
ctk.CTkLabel(container1_2, text=textos_segundo_frame[1]).grid(row=2,column=0, padx=10, pady=10, sticky='nw') 
L_VMX = ctk.CTkLabel(container1_2, text=valores_segundo_frame_arriba[1])
L_VMX.grid(row=2, column=1,padx=10, pady=10, sticky='nwe')
ctk.CTkLabel(container1_2, text=textos_segundo_frame[2]).grid(row=3,column=0, padx=10, pady=10, sticky='nw') 
L_EMX = ctk.CTkLabel(container1_2, text=valores_segundo_frame_arriba[2])
L_EMX.grid(row=3, column=1,padx=10, pady=10, sticky='nwe')
ctk.CTkLabel(container1_2, text=textos_segundo_frame[3]).grid(row=4,column=0, padx=10, pady=10, sticky='nw') 
L_DMX = ctk.CTkLabel(container1_2, text=valores_segundo_frame_arriba[3])
L_DMX.grid(row=4, column=1,padx=10, pady=10, sticky='nwe')  
ctk.CTkLabel(container1_2, text=textos_segundo_frame[4],).grid(row=5,column=0, padx=10, pady=10, sticky='nw') 
L_ETR = ctk.CTkLabel(container1_2, text=valores_segundo_frame_arriba[4])
L_ETR.grid(row=5, column=1,padx=10, pady=10, sticky='nwe')
ctk.CTkLabel(container1_2, text=textos_segundo_frame[5]).grid(row=6,column=0, padx=10, pady=10, sticky='nw') 
L_CE = ctk.CTkLabel(container1_2, text=valores_segundo_frame_arriba[5])
L_CE.grid(row=6, column=1,padx=10, pady=10, sticky='nwe')  

def modificar_datos_segundo_frame(posicion,texto_label_num_grafica, V_FMX, V_VMX, V_EMX, V_DMX, V_ETR, V_CE):
    global valores_segundo_frame_arriba, valores_segundo_frame_abajo
    global Label_Num_Grafica
    global L_FMX, L_VMX, L_EMX, L_DMX, L_ETR, L_CE
    Label_Num_Grafica.configure(text= str(texto_label_num_grafica), font=('Times', 15))
    L_FMX.configure(text = str(V_FMX))
    L_VMX.configure(text = str(V_VMX))
    L_EMX.configure(text = str(V_EMX))
    L_DMX.configure(text = str(V_DMX))
    L_ETR.configure(text = str(V_ETR))
    L_CE.configure(text = str(V_CE))
    if posicion == 'arriba':
        valores_segundo_frame_arriba = [texto_label_num_grafica, V_FMX, V_VMX, V_EMX, V_DMX, V_ETR, V_CE]
    else:
        valores_segundo_frame_abajo = [texto_label_num_grafica, V_FMX, V_VMX, V_EMX, V_DMX, V_ETR, V_CE]

#--------------------------------------------------
# Frame Principal del medio
container2 = ctk.CTkFrame(container)
container2.grid_columnconfigure(0, weight=30)
container2.grid_columnconfigure(1, weight=1)
container2.grid_rowconfigure(0, weight=1)
container2.grid_rowconfigure(1, weight=1)

container2.grid(row=0,column=1, sticky='nsew', padx=(30,10), pady=(30))


# rectangulos principales

# frame de arriba
container2_1 = ctk.CTkFrame(container2)
container2_1.grid_columnconfigure(0, weight=1)
container2_1.grid_rowconfigure(0, minsize= 40, weight=1)
container2_1.grid_rowconfigure(1, weight=20)
container2_1.grid_rowconfigure(2, minsize=40, weight=1)
container2_1.grid(row=0, column=0, padx=10, pady=(10,5), sticky='nsew')

container2_1_1 = ctk.CTkFrame(container2_1, corner_radius=0)
container2_1_1.grid(row=0, column=0, sticky='new')
#for i in range(7):
#    container2_1_1.grid_columnconfigure(i, weight=8)
container2_1_1.grid_columnconfigure(0, weight=10)
container2_1_1.grid_columnconfigure(1, weight=1)
container2_1_1.grid_rowconfigure(0, weight=1)

container2_1_2 = ctk.CTkFrame(container2_1)
container2_1_2.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0,5))
container2_1_3 = ctk.CTkFrame(container2_1)
container2_1_3.grid(row=2, column=0, sticky='nsew', padx=10, pady=(0,5))

container2_1_3.grid_rowconfigure(0, weight=1)

container2_1_3.grid_columnconfigure(0, weight=250)
container2_1_3.grid_columnconfigure(1, weight=1)

container2_1_3_1 = ctk.CTkFrame(container2_1_3)
container2_1_3_1.grid(row=0, column=0, sticky='w')

container2_1_3_3 = ctk.CTkFrame(container2_1_3)
container2_1_3_3.grid(row=0, column=1, sticky='e')
container2_1_3_3.grid_columnconfigure(0, weight=1)
container2_1_3_3.grid_columnconfigure(1, weight=1)
container2_1_3_3.grid_columnconfigure(2, weight=1)
container2_1_3_3.grid_columnconfigure(3, weight=1)

# frame de abajo
container2_2 = ctk.CTkFrame(container2)
container2_2.grid_columnconfigure(0, weight=1)
container2_2.grid_rowconfigure(0, minsize=40, weight=1)
container2_2.grid_rowconfigure(1, weight=20)
container2_2.grid_rowconfigure(2, minsize=40, weight=1)
container2_2.grid(row=1, column=0, padx=10, pady=(5,10), sticky='new')

container2_2_1 = ctk.CTkFrame(container2_2, corner_radius=0)
container2_2_1.grid(row=0, column=0, sticky='new')
#for i in range(7):
#    container2_2_1.grid_columnconfigure(i, weight=8)
container2_2_1.grid_columnconfigure(0, weight=10)
container2_2_1.grid_columnconfigure(1, weight=1)
container2_2_1.grid_rowconfigure(0, weight=1)

container2_2_2 = ctk.CTkFrame(container2_2)
container2_2_2.grid(row=1, column=0, sticky='nsew', padx=10, pady=(0,5))
container2_2_3 = ctk.CTkFrame(container2_2)
container2_2_3.grid(row=2, column=0, sticky='nsew', padx=10, pady=(0,5))

container2_2_3.grid_rowconfigure(0, weight=1)
container2_2_3.grid_columnconfigure(0, weight=250)
container2_2_3.grid_columnconfigure(1, weight=1)

container2_2_3_1 = ctk.CTkFrame(container2_2_3)
container2_2_3_1.grid(row=0, column=0, sticky='sw')

container2_2_3_3 = ctk.CTkFrame(container2_2_3)
container2_2_3_3.grid(row=0, column=1, sticky='e')
container2_2_3_3.grid_columnconfigure(0, weight=1)
container2_2_3_3.grid_columnconfigure(1, weight=1)
container2_2_3_3.grid_columnconfigure(2, weight=1)
container2_2_3_3.grid_columnconfigure(3, weight=1)

# botones de los frames

dic_magnitud_botones = {0:'aceleracion', 1:'velocidad', 2:'deformacion', 3:'fuerza', 4:'desplazamiento', 5:'fuerzaxvelocidad', 6:'avged'}
dic_ultima_grafica_magnitud = {"arriba": ultima_magnitud_arriba, "abajo": ultima_magnitud_abajo}


segemented_button_var1 = ctk.StringVar(value="ACELERACIÓN")
segemented_button = ctk.CTkSegmentedButton(container2_1_1, values=texto_botones_frame, command=segmented_button_callback1, variable=segemented_button_var1)
segemented_button.grid(row=0,column=0, sticky='nsew', pady=5, padx=(5,0))

segemented_button_var2 = ctk.StringVar(value="DEFORMACIÓN")
segemented_button2 = ctk.CTkSegmentedButton(container2_2_1, values=texto_botones_frame, command=segmented_button_callback2, variable=segemented_button_var2)
segemented_button2.grid(row=0,column=0, sticky='nsew', pady=5, padx=(5,0))

Boton_seleccion_grafica1 = ctk.CTkRadioButton(container2_1_1, text="", width= 20, command=lambda: colorear_botones_seleccion_grafica(1), value=0)
Boton_seleccion_grafica1.grid(row=0,column=1,  sticky='ns', pady=5, padx=(5,5))
Boton_seleccion_grafica1.select()

Boton_seleccion_grafica2 = ctk.CTkRadioButton(container2_2_1, text="", width= 20, command=lambda: colorear_botones_seleccion_grafica(2), value=1)
Boton_seleccion_grafica2.grid(row=0,column=1, sticky='ns', pady=5, padx=(5,5))

# Barra lateral de la columna de la derecha

container2_3 = ctk.CTkFrame(container2, corner_radius=0)
container2_3.grid(row=0, rowspan=2, column=1, sticky='nsew')
container2_3.grid_rowconfigure(0, weight=1)
container2_3.grid_columnconfigure(0, weight=1)


def colorear_botones_seleccion_grafica(num):
    global ultima_grafica_seleccionada, Boton_seleccion_grafica2, Boton_seleccion_grafica1, valores_segundo_frame_arriba, valores_segundo_frame_abajo
    
    if num == 1:
        ultima_grafica_seleccionada = 'arriba'
        Boton_seleccion_grafica1.select()
        Boton_seleccion_grafica2.deselect()
        v_vec = valores_segundo_frame_arriba.copy()
        modificar_datos_segundo_frame('arriba', v_vec[0], v_vec[1], v_vec[2], v_vec[3], v_vec[4], v_vec[5], v_vec[6])
    else:
        ultima_grafica_seleccionada = 'abajo'
        Boton_seleccion_grafica1.deselect()
        Boton_seleccion_grafica2.select()
        v_vec = valores_segundo_frame_abajo.copy()
        modificar_datos_segundo_frame('abajo',  v_vec[0], v_vec[1], v_vec[2], v_vec[3], v_vec[4], v_vec[5], v_vec[6])


# cambiar magnitudes

def cambiar_magnitud_grafica(posicion,magnitud):

    if magnitud == 6:
        Creacion_Grafica(posicion, dic_magnitud_botones[magnitud], dic_ultima_grafica[posicion], "original", "NO", "SI")

    else:
        Creacion_Grafica(posicion, dic_magnitud_botones[magnitud], dic_ultima_grafica[posicion], "original", "NO", "NO")

dic_posicion = {"arriba":[container2_1_2, container2_1_3_1, container2_1_3_3], "abajo":[container2_2_2, container2_2_3_1, container2_2_3_3]}

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
    
class Toolbar(NavigationToolbar2TkAgg):
    def set_message(self, s):
        pass

def velocity(acel, freq):
    tr_a = Trace(data=np.array(acel)*9.81)
    tr_a.stats.sampling_rate = freq*1000
    tr_v = tr_a.copy()
    tr_v.integrate(method = "cumtrapz")
    return tr_v

def integrate(tr_00):
    tr_0 = tr_00.copy()
    tr_0.integrate(method = "cumtrapz")
    return tr_0

def energy(F, V, freq):
    E = []
    producto = np.multiply(np.array(F)*1000, V)
    tr_potencia = Trace(data=np.array(producto))
    tr_potencia.stats.sampling_rate = freq*1000
    tr_energy = tr_potencia.copy()
    tr_energy.integrate(method = "cumtrapz")
    return tr_energy


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
    print("El factor es ", factor)
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
    
    longitud = max(len(A3), len(A4))

    # Calculando velocidad 1
    try:
        V1 = velocity(np.array(A3[:longitud]), int(frecuencia_muestreo[-1]))
    except Exception as e:
        print(f"Error al calcular la velocidad V1 {e}")
    
    try:
        V2 = velocity(np.array(A4[:longitud]), int(frecuencia_muestreo[-1]))
    except Exception as e:
        print(f"Error al calcular la velocidad V2 {e}")

    if A3 == []:
        V = V2.data
    elif A4 == []:
        V = V1.data
    else:
        V = (V1.data + V2.data)/2
    


    Vmax = round(max(V), 2)

    Vmax_original = max(V)

    longitud = max(len(S1), len(S2))
    print("la longitud maxima es:", longitud)
    print("otras longitudes: ", len(V1), len(V2), len(V))

    try:
        D1 = integrate(V1)
    except Exception as e:
        print(f"Error al calcular el desplazamiento D1 {e}")
    
    try:
        D2 = integrate(V2)
    except Exception as e:
        print(f"Error al calcular el desplazamiento D2 {e}")

    if V1 == []:
        D = D2.data
    elif V2 == []:
        D = D1.data
    elif len(V1.data) == len(V2.data):
        D = (D1.data + D2.data)/2
    else:
        D = D1.data if len(V1.data) > len(V2.data) else D2.data

    Dmax = round(max(D), 2)
    
    ajuste = 0
   
    Z = Fmax_original/Vmax_original

    imax = F.index(Fmax_original)
    ajuste = list(V).index(Vmax_original)-imax

    print("el ajuste es ",ajuste)
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
            p_primera_marca = 0.0
        elif valor_primera_marca > segunda_marca:
            valor_primera_marca = segunda_marca
            
        valor_segunda_marca = segunda_marca + a_segunda_marca
        if valor_segunda_marca < primera_marca:
            valor_segunda_marca = primera_marca
        elif valor_segunda_marca > segunda_marca:
            valor_segunda_marca = segunda_marca
            p_segunda_marca = 0.0

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
    
    LIM_IZQ.configure(text = str(round(valor_primera_marca,2)))
    LIM_DER.configure(text = str(round(valor_segunda_marca,2)))
    
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

    B1_izquierda = ctk.CTkButton(dic_posicion[posicion][2], text="<", width=30, height=30, command=lambda:moverlimite(posicion, magnitud, dic_ultima_grafica[posicion], 'mantener', condicion, 'MODIFICAR', '1', 'izquierda'))
    B1_izquierda.grid(row=0, column=0, padx=(5,5))
    B1_derecha = ctk.CTkButton(dic_posicion[posicion][2], text=">",  width=30, height=30, command=lambda:moverlimite(posicion, magnitud, dic_ultima_grafica[posicion], 'mantener', condicion, 'MODIFICAR', '1', 'derecha'))
    B1_derecha.grid(row=0, column=1, padx=(0,5))
    B2_izquierda = ctk.CTkButton(dic_posicion[posicion][2], text="<",  width=30, height=30, command=lambda:moverlimite(posicion, magnitud, dic_ultima_grafica[posicion], 'mantener', condicion, 'MODIFICAR', '2', 'izquierda'))
    B2_izquierda.grid(row=0, column=2, padx=(0,5))
    B2_derecha = ctk.CTkButton(dic_posicion[posicion][2], text=">",  width=30, height=30, command=lambda:moverlimite(posicion, magnitud, dic_ultima_grafica[posicion], 'mantener', condicion, 'MODIFICAR', '2', 'derecha'))
    B2_derecha.grid(row=0, column=3, padx=(0,5))

    segundos_Transformado = []
    
    if magnitud == 'fuerzaxvelocidad':
        a.axvline(valor_primera_marca, color='r', ls="dotted")
        a.axvline(valor_segunda_marca, color='r', ls="dotted")


    rango_inferior = segundos.index(round(valor_primera_marca,2))
    rango_superior = segundos.index(round(valor_segunda_marca,2))

    try:
        E = energy(F[rango_inferior:rango_superior],V[rango_inferior:rango_superior], int(frecuencia_muestreo[-1])).data
    except Exception as e:
        print(f"Error al calcular la Energía E {E}")


    
    j = 0
    for i in range(segundos.index(round(valor_primera_marca,2)),segundos.index(round(valor_segunda_marca,2))):
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
    dic_unidades = {'aceleracion':["milisegundos", "g`s"], 'deformacion':["milisegundos", "micro strain"], 'fuerza':["milisegundos", "kN"], 'velocidad':["milisegundos", "m/s"], 'avged':["milisegundos", ""], 'desplazamiento':["milisegundos", "m"], 'fuerzaxvelocidad':["milisegundos", ""]}
    try:
        t1, = a.plot(segundos, dic_magnitud[magnitud][0], label=dic_legenda[magnitud][0])
    except:
        pass
    try:
        t2, = a.plot(segundos, dic_magnitud[magnitud][1], label=dic_legenda[magnitud][1])
    except:
        pass
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
        
    f.subplots_adjust(left=0.1,bottom=0.15,right=0.98,top=0.96)
    canvas = FigureCanvasTkAgg(f, dic_posicion[posicion][0])

    canvas.get_tk_widget().pack(side=TOP, expand=1, fill=BOTH)



    toolbar = Toolbar(canvas, dic_posicion[posicion][1])
    toolbar.config(background="#2A2A2A")
    toolbar.update()
    canvas._tkcanvas.pack(side=BOTTOM, expand=1, fill=BOTH)
    
    texto_label_num_grafica = str(dic_ultima_grafica[posicion])+"/"+str(len(matriz_data_archivos)-1)

    modificar_datos_segundo_frame(posicion, texto_label_num_grafica, Fmax, Vmax, Emax, Dmax, str(ETR) + "%", CE)

    try:
        #ctk.CTkLabel(dic_posicion[posicion][2], text="actual:"+str(dic_ultima_grafica[posicion])+",ultima:"+str(len(matriz_data_archivos)-1)+",total:"+str((len(matriz_data_archivos)-1))).pack(side=LEFT)     
        L_T_Grafico.configure(text=str(dic_ultima_grafica[posicion]))
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
        for index, num in enumerate(matriz_relacion_num):
            print(num)
            string += 'INICIO_ARCHIVO\nARCHIVO:'+str(index+1)+"\n"+str(orden_sensores[-1])+"\n"
            for fila in matriz_data_archivos[index+1]:
                string += fila+"\n"
            string += 'FIN_ARCHIVO\n'
        file.write(string)

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
    
    Creacion_Grafica(ultima_grafica_seleccionada, dic_ultima_grafica_magnitud[ultima_grafica_seleccionada], dic_ultima_grafica[ultima_grafica_seleccionada], direccion, "SI", "SI")

botones_barra_lateral = ['DEL','DD','DI','AJ','>','<','>>','<<']

for i in range(len(botones_barra_lateral)):
    container2_3.grid_rowconfigure(i, weight=1)

ctk.CTkButton(container2_3, text=botones_barra_lateral[0], font=ctk.CTkFont(size=20, weight="bold"), command=lambda: eliminar_grafica()).grid(row=0,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5,0)) 
ctk.CTkButton(container2_3, text=botones_barra_lateral[1], font=ctk.CTkFont(size=20, weight="bold"), command=lambda: desplazar_grafica("derecha")).grid(row=1,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5,0)) 
ctk.CTkButton(container2_3, text=botones_barra_lateral[2], font=ctk.CTkFont(size=20, weight="bold"), command=lambda: desplazar_grafica("izquierda")).grid(row=2,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5,0)) 
ctk.CTkButton(container2_3, text=botones_barra_lateral[3], font=ctk.CTkFont(size=20, weight="bold"), command=lambda: desplazar_grafica("centrar")).grid(row=3,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5,0)) 
ctk.CTkButton(container2_3, text=botones_barra_lateral[4], font=ctk.CTkFont(size=20, weight="bold"), command=lambda: cambiar_grafica("derecha")).grid(row=4,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5,0)) 
ctk.CTkButton(container2_3, text=botones_barra_lateral[5], font=ctk.CTkFont(size=20, weight="bold"), command=lambda: cambiar_grafica("izquierda")).grid(row=5,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5,0)) 
ctk.CTkButton(container2_3, text=botones_barra_lateral[6], font=ctk.CTkFont(size=20, weight="bold"), command=lambda: cambiar_grafica("derecha+")).grid(row=6,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5,0)) 
ctk.CTkButton(container2_3, text=botones_barra_lateral[7], font=ctk.CTkFont(size=20, weight="bold"), command=lambda: cambiar_grafica("izquierda+")).grid(row=7,column=0, columnspan=2, sticky='nsew', padx=10, pady=(5)) 

#----------------------------------------------------
# Frame de la derecha 
container3 = ctk.CTkFrame(container)
container3.grid(row=0,column=2,sticky='nsew')
container3.grid_columnconfigure(0, weight=1)

# Frames Principales
# Frame de arriba

container3_1 = ctk.CTkFrame(container3)
container3_1.grid(row=0, column=0, padx=20, pady=(20,5), sticky='new')
container3_1.grid_columnconfigure(0, weight=1)
container3_1.grid_columnconfigure(1, weight=1)
T_1 = ctk.CTkLabel(container3_1, text="Límites de la gráfica de arriba").grid(row=0,column=0, padx=10, pady=10, sticky='nsew')

container3_2 = ctk.CTkFrame(container3)
container3_2.grid(row=1, column=0, padx=20, pady=(20,10), sticky='new')

container3_2.grid_columnconfigure(0, weight=1)
container3_2.grid_columnconfigure(1, weight=1)

textos_tercer_frame = ["límite izquierda", "límite derecha"]

ctk.CTkLabel(container3_2, text=textos_tercer_frame[0]).grid(row=0,column=0, padx=10, pady=10, sticky='nw') 
LIM_IZQ = ctk.CTkLabel(container3_2, text='')
LIM_IZQ.grid(row=0, column=1,padx=10, pady=10, sticky='nwe')
ctk.CTkLabel(container3_2, text=textos_tercer_frame[1]).grid(row=1,column=0, padx=10, pady=10, sticky='nw') 
LIM_DER = ctk.CTkLabel(container3_2, text='')
LIM_DER.grid(row=1, column=1,padx=10, pady=10, sticky='nwe')



# Frame del medio

container3_3 = ctk.CTkFrame(container3)
container3_3.grid(row=2, column=0, padx=20, pady=10, sticky='new')
container3_3.grid_columnconfigure(0, weight=1)
container3_3.grid_columnconfigure(1, weight=1)

container3_3.rowconfigure(0, weight=1)
container3_3.rowconfigure(1, weight=1)
container3_3.rowconfigure(2, weight=1)
container3_3.rowconfigure(3, weight=1)


T_2 = ctk.CTkLabel(container3_3, text="Límites input").grid(row=0,column=0, padx=10, pady=10, sticky='nsew')

ctk.CTkLabel(container3_3, text=textos_tercer_frame[0]).grid(row=1,column=0, padx=10, pady=10, sticky='nw') 
LIM_IZQ_Entry = ctk.CTkEntry(container3_3)
LIM_IZQ_Entry.grid(row=1, column=1,padx=10, pady=10, sticky='nwe')
ctk.CTkLabel(container3_3, text=textos_tercer_frame[1]).grid(row=2,column=0, padx=10, pady=10, sticky='nw') 
LIM_DER_Entry = ctk.CTkEntry(container3_3)
LIM_DER_Entry.grid(row=2, column=1,padx=10, pady=10, sticky='nwe')

ctk.CTkButton(container3_3, text='Actualizar', command=lambda:actualizar_limites()).grid(row=3, column=0, padx=10, pady=10, sticky='nw')

def actualizar_limites():
    global contador_grafica_arriba
    global contador_grafica_abajo
    global ultima_grafica_seleccionada
    global ultima_magnitud_arriba
    global ultima_magnitud_abajo
    global LIM_IZQ_Entry, LIM_DER_Entry
    Creacion_Grafica(ultima_grafica_seleccionada, dic_ultima_grafica_magnitud[ultima_grafica_seleccionada], dic_ultima_grafica[ultima_grafica_seleccionada], 'original', "SI", 'MODIFICAR_EXACTO', float(LIM_IZQ_Entry.get()), float(LIM_DER_Entry.get()))


# Frame de abajo

container3_4 = ctk.CTkFrame(container3)
container3_4.grid(row=3, column=0, padx=20, pady=10, sticky='new')
container3_4.grid_columnconfigure(0, weight=1)
container3_4.grid_rowconfigure(0, weight=1)

ctk.CTkButton(container3_4, text='Exportar', command=lambda:[Seleccionar_ruta_guardado_pdf(), create_toplevel_export()]).grid(row=0, column=0, padx=10, pady=10, sticky='new')

def preparaciones_exportar(label_cantidad_golpes, label_inicio, label_final):
    global matriz_data_archivos
    longitudes = matriz_data_archivos[0][12:].split(",")
    label_cantidad_golpes.configure(text='Cantidad de Golpes:'+str(len(matriz_data_archivos)-1))
    label_inicio.configure(text='Inicio:'+str(longitudes[0]))
    label_final.configure(text='Final:'+str(longitudes[1]))

#--------------------FRAME2------------------------------------------------------------

def Eliminar_Fila():
        global filas
        for i in range(len(filas[-1])):
            filas[-1][i].destroy()
        filas.pop()
    
def Eliminar_todas_filas():
    for i in range(10):
        try:
            Eliminar_Fila()
        except:
            pass

filas = []
contador_fila = 1
fila_grabada = []

def Insertar_Fila(container6_1_1):
    global filas, contador_fila
    fila_grabada = []
    try:
        for i in range(7):
            fila_grabada.append(ctk.CTkEntry(container6_1_1)) 
            fila_grabada[i].grid(row=contador_fila, column=i, sticky='nsew')
        filas.append(fila_grabada)
        contador_fila +=1
    except Exception as e:
        print(e)

def Seleccionar_ruta_guardado_pdf():
    global ruta_guardado_pdf
    ruta_guardado_pdf = filedialog.askdirectory(initialdir = "/", title = "Selecciona una carpeta")


def create_toplevel_export():
    global Num_golpes, Num_golpes_modificado, filas, contador_fila, fila_grabada, filas, contador_fila, ruta
    export_frame = ctk.CTkToplevel()
    export_frame.title("Export")
    # create label on CTkToplevel window
    container6 = ctk.CTkFrame(export_frame)

    container6.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
    container6.grid_rowconfigure(0, weight=1)
    container6.grid_rowconfigure(1, weight=2)
    container6.grid_rowconfigure(2, weight=1)
    container6.grid_columnconfigure(0, weight=1)

    container6_0 = ctk.CTkFrame(container6)
    container6_0.grid(row=0, column=0, padx=(30), pady=(30,15), sticky= 'nsew')
    container6_0.grid_rowconfigure(0, weight=1)
    container6_0.grid_columnconfigure(0, weight=1)
    container6_0.grid_columnconfigure(1, weight=1)
    container6_0.grid_columnconfigure(2, weight=1)


    label_cantidad_golpes = ctk.CTkLabel(container6_0)
    label_cantidad_golpes.grid(row=0, column=0, padx=20, pady=10)

    label_inicio = ctk.CTkLabel(container6_0)
    label_inicio.grid(row=0, column=1, pady=10)

    label_final = ctk.CTkLabel(container6_0)
    label_final.grid(row=0, column=2, padx=20, pady=10)

    container6_1 = ctk.CTkFrame(container6)
    container6_1.grid(row=1, column=0, padx=(30), pady=(15), sticky= 'nsew')
    container6_1.grid_columnconfigure(0, weight=1)

    container6_1_1 = ctk.CTkFrame(container6_1)
    container6_1_1.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)

    texto_columnas_export = ["Profundidad (m)", "conteo de golpes", "Longitud de Incremento (m)", "BN remanente", "Tasa de golpes (bl/m)", "set/blow (mm/bl)", "Elevación (m)"]

    for i in range(7):
        container6_1_1.grid_columnconfigure(i, weight=1)
        ctk.CTkLabel(container6_1_1, text=texto_columnas_export[i]).grid(row=0, column=i, sticky='nsew')

    container6_2 = ctk.CTkFrame(container6)
    container6_2.grid(row=2, column=0, padx=(30), pady=(15,30), sticky= 'nsew')
    container6_2.grid_columnconfigure(0, weight=1)

    for i in range(4):
        container6_2.grid_columnconfigure(i, weight=1)

    ctk.CTkButton(container6_2, text="Insertar fila", command=lambda:Insertar_Fila(container6_1_1)).grid(row=0, column=0, sticky='nsew', padx=(10,0), pady=10)
    ctk.CTkButton(container6_2, text="Eliminar fila", command=lambda:Eliminar_Fila()).grid(row=0, column=1, sticky='nsew', padx=(10,0), pady=10)
    ctk.CTkButton(container6_2, text="Completar", command=lambda:Completar_Filas()).grid(row=0, column=2, sticky='nsew', padx=(10,0), pady=10)
    #ctk.CTkButton(container6_2, text="Seleccionar \Ruta", command=lambda:Seleccionar_ruta_guardado_pdf()).grid(row=0, column=3, sticky='nsew')
    ctk.CTkButton(container6_2, text="Exportar \nPDF", command=lambda: [mostrar_alertas_exportar()]).grid(row=0, column=3, sticky='nsew', padx=(10), pady=10)

    filas = []
    contador_fila = 1
    fila_grabada = []

    Num_golpes = []
    Num_golpes_modificado = []

    preparaciones_exportar(label_cantidad_golpes, label_inicio, label_final)

    for i in range(4):
        Insertar_Fila(container6_1_1)

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
            for datos in filtrado(correcion_linea_cero(dic_orden_sensores2[orden[i]])):
                dic_orden_sensores[orden[i]].append(datos)
        elif (int(orden[i])!=0):
            for datos in filtrado2(correcion_linea_cero2(dic_orden_sensores2[orden[i]])):               
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

    if len(S1) == 0:
        F = F2.copy()
        S = S2.copy()
    elif len(S2) == 0:
        F = F1.copy()
        S = S1.copy()
    else:
        S = []
        for i in range(len(S1)):
            S.append((S1[i]+S2[i])/2)

    Fmax = round(max(F), 2)
    Fmax_original = max(F)

    longitud = max(len(A3), len(A4))

    # Calculando velocidad 1
    try:
        V1 = velocity(np.array(A3[:longitud]), int(frecuencia_muestreo[-1]))
    except Exception as e:
        print(f"Error al calcular la velocidad V1 {e}")
    
    try:
        V2 = velocity(np.array(A4[:longitud]), int(frecuencia_muestreo[-1]))
    except Exception as e:
        print(f"Error al calcular la velocidad V2 {e}")

    if len(A3) == 0:
        V = V2.data
        A = A4.copy()
    elif len(A4) == 0:
        V = V1.data
        A = A3.copy()
    else:
        V = (V1.data + V2.data)/2
        A = []
        for i in range(len(A3)):
            A.append((A3[i]+A4[i])/2)
        
    print("velocidades", len(V), len(V1), len(V2) )
    Vmax = round(max(V), 2)
    Vmax_original = max(V)

    longitud = max(len(S1), len(S2))

    try:
        D1 = integrate(V1)
    except Exception as e:
        print(f"Error al calcular el desplazamiento D1 {e}")
    
    try:
        D2 = integrate(V2)
    except Exception as e:
        print(f"Error al calcular el desplazamiento D2 {e}")

    if len(V1) == 0:
        D = D2.data
    elif len(V2) == 0:
        D = D1.data
    else:
        D = (D1.data + D2.data)/2

    Dmax = round(max(D), 2)
    
    Z = Fmax_original/Vmax_original
    
    for i in range(len(V)):
        valor = V[i]*Z
        V_Transformado.append(valor)
        V_Transformado_valor_real.append(V[i])

    j = 0

    segundo_inicial = float(segundo_inicial)
    segundo_final = float(segundo_final)


    try:
        E = energy(F,V, int(frecuencia_muestreo[-1])).data
    except Exception as e:
        print(f"Error al calcular la Energía E {E}")

    try:
        Emax = round(max(E), 2)
    except:
        pass
    Energias.append(Emax)
    Velocidades.append(Vmax)
    Fuerzas.append(Fmax)
    Energias_teoricas.append(round(Emax*100/float(ET_valor_original),2))
    Impedancias.append(Fmax/Vmax)
    
    return F, V_Transformado, segundos, Z, E, V, D, A, S

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

    Aceleraciones_data = []
    Deformaciones_data = []
    Fuerzas_data = []
    Segundos_data = []
    Energias_data = []
    Velocidades_data = []
    Desplazamientos_data = []

    for j in range(1, len(matriz_data_archivos)):
        F, Velocidad_transformados, segundos, Z, E, V, D, A, S = obtener_datos_grafica(j)
        Aceleraciones_data.append(A)
        Deformaciones_data.append(S)
        Fuerzas_data.append(F)
        segundos_corregidos = []
        for i in segundos:
            segundos_corregidos.append(float(i)/10)
        Segundos_data.append(segundos_corregidos)
        Energias_data.append(E)
        Velocidades_data.append(V)
        Desplazamientos_data.append(D)
    
    maxZ = Impedancias.index(max(Impedancias))
    
    #Aquí se añade una fila más a cada variable de arriba Energias, fuerzas, etc, por lo cual se le quita una fila a cada una abajo



    Fuerzas_impedancia_maxima, Velocidades_impedancia_maxima, segundos, t, t, t, t, t, t = obtener_datos_grafica(maxZ+1)

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
    crear_excel(Segundos_data, Aceleraciones_data, Deformaciones_data, Fuerzas_data, Velocidades_data, Energias_data, Desplazamientos_data)

    MessageBox.showinfo(title="Exportado", message="Se ha exportado con éxito")

def crear_excel(Segundos, A, S, F, V, E, D):
    global ruta_guardado_pdf, ruta_data_inicial

    data = [Segundos, A, S, F, V, E, D]
    cadenas =ruta_data_inicial.split("/")[-1][:-3]
    nombre_archivo = 'Reporte_' + cadenas + '.xlsx'

    workbook = xlsxwriter.Workbook(ruta_guardado_pdf + "/" + nombre_archivo)
    
    for i in range(len(F)):
        worksheet = workbook.add_worksheet('Datos del impacto '+str(i+1))

        cell_format4 = workbook.add_format()
        cell_format4.set_align('center')
        cell_format4.set_align('vcenter')
        cell_format4.set_text_wrap()

        cell_format3 = workbook.add_format()
        cell_format3.set_text_wrap()
        cell_format3.set_align('center')
        cell_format3.set_align('vcenter')
        cell_format3.set_font_color('white')
        cell_format3.set_bold()
        cell_format3.set_bg_color('#1F246D')

        for j in range(len(data)):
            for k in range(len(data[j][i])):
                worksheet.write(k+2, j+1, data[j][i][k], cell_format4)
        
        columnas = ["Segundos", "Aceleración", "Deformación", "Fuerza", "Velocidad", "Energía", "Desplazamiento"]

        worksheet.set_column("A:A",5)
        worksheet.set_column("B:B",25)#
        worksheet.set_column("C:C",25)
        worksheet.set_column("D:D",25)
        worksheet.set_column("E:E",25)
        worksheet.set_column("F:F",25)#
        worksheet.set_column("G:G",25)
        worksheet.set_column("H:H",25)

        for i in range(1, len(columnas)+1):
            worksheet.write(1, i ,columnas[i-1], cell_format3)
        
    workbook.close()

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

def create_toplevel_about():
    about_frame = ctk.CTkToplevel()
    #about_frame.geometry("800x400")
    about_frame.title("About")
    about_frame.grab_set()
    about_frame.focus()
    # create label on CTkToplevel window
    container7 = ctk.CTkFrame((about_frame))
    container7.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)

    container7.grid_rowconfigure(0, weight=1)
    container7.grid_rowconfigure(1, weight=2)
    container7.grid_columnconfigure(0, weight=1)

    label1 = ctk.CTkLabel(container7, text="Kallpa Procesor hecho por el CITDI", font=('Times', 30))
    label1.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)
    label2 = ctk.CTkLabel(container7, text="Creado con colaboración de:\nCarmen Ortiz Salas\nGrover Rios Soto\nRoberto Raucana Sulca\nJoseph Mottoccanche Tantaruna", font=('Times', 20))
    label2.grid(row=1, column=0, sticky='nsew', padx=20, pady=(20))

# programa convertir rpn a ctn

def escoger_ruta_guardado2():
    global ruta_guardado
    archivos = filedialog.askopenfilenames(initialdir = "/", title = "Seleccione los archivos a convertir")
    #ruta_guardado += "/"
    return archivos

def leer_data_cabecera(ruta):
    with open(ruta) as file:
        filas = file.readlines()
    for index, fila in enumerate(filas):
        fila = fila.replace("\n", "").split(",")
        if fila[0] == "AR":
            ar_pos = index
        if fila[0] == "EM":
            em_pos = index
        if fila[0] == "EFV":
            efv_pos = index
        if fila[0] == "ETR":
            etr_pos = index
        if fila[0] == "Record":
            frecuencia_post = index+3
    
    ar = round(float(filas[ar_pos].replace("\n", "").split(",")[1]),2)
    em = round(float(filas[em_pos].replace("\n", "").split(",")[1]),2)
    efv = float(filas[efv_pos].replace("\n", "").split(",")[1])
    etr = float(filas[etr_pos].replace("\n", "").split(",")[1])
    et = round((efv/etr)*100,2)


    frecuencia = round(1/float(filas[frecuencia_post].replace("\n", "").split(",")[1])/1000)

    fila_orden = filas[frecuencia_post-3].replace("\n", "").split(",")
    print(fila_orden)
    orden = [fila_orden[2].split("@")[0], fila_orden[3].split("@")[0]]
    try:
        orden.append(fila_orden[4].split("@")[0])
        orden.append(fila_orden[5].split("@")[0])
    except:
        orden.append("0")
        orden.append("0")
        
    dic_orden = {"S3":"3", "S4":"4", "S1":"3", "S2":"4", "A1":"1", "A2":"2", "A3":"1", "A4":"2", "0":"0"}
    orden_string = ""
    for index, elemento in enumerate(orden):
        orden_string += dic_orden[elemento] +"|"
    print(orden_string)
    print(frecuencia)
    print(ar, em, et)
    return frecuencia_post, filas, orden_string, frecuencia, ar, em, et

    # lectura de la data 
def lectura_data(frecuencia_post, filas):
    string_data = ""
    for i in range(frecuencia_post-1, len(filas)):
        fila = filas[i].replace("\n", "").split(",")
        segundos = round(float(fila[1])*10000,2)
        V1 = float(fila[2])
        V2 = float(fila[3])
        try:
            V3 = float(fila[4])
        except:
            pass
        try:
            V4 = float(fila[5])
        except:
            pass
        try:
            nueva_fila = str(segundos) + "|" + str(V1) + "|" + str(V2) + "|" + str(V3) + "|" + str(V4) + "|"
        except:
            try:
                nueva_fila = str(segundos) + "|" + str(V1) + "|" + str(V2) + "|" + str(V3) + "|0|"
            except:
                nueva_fila = str(segundos) + "|" + str(V1) + "|" + str(V2) + "|0|0|"
        string_data+=nueva_fila+"\n"
    return string_data

def crear_ctn(profundidad, ruta_guardado_combinado):
    texto = ""
    for index in range(len(ruta_guardado_combinado)):
        if index == 0:
            texto += "profundidad:"+profundidad
        frecuencia_post, filas, orden_string, frecuencia, ar, em, et = leer_data_cabecera(ruta_guardado_combinado[index])
        cabecera = orden_string+str(frecuencia)+"|"+str(ar)+"|"+str(em)+"|"+str(et)
        texto+="\nINICIO_ARCHIVO\nARCHIVO:"+str(index+1)+"\n"+cabecera+"\n"
        texto+=lectura_data(frecuencia_post, filas)
        texto+="FIN_ARCHIVO"
    return texto, str(frecuencia), str(ar), str(em), str(et)

label_frecuencia = ""
label_AR = ""
label_EM = ""
label_ET = ""
Entry_archivo_inicio = ""
Entry_archivo_final = ""
ruta_guardado_combinado = ""
ruta_combinados = ""
scrollable_frame = ""
ruta_guardado_label_combinado = ""

def boton_escoger_archivos_combinar():
    global ruta_combinados
    ruta_combinados =  escoger_ruta_guardado2()
    string = ""
    for i in ruta_combinados:
        string += i +"\n"

    scrollable_frame.insert(0.0, string)

def boton_preparar(inicio, fin):
    global scrollable_frame, label_frecuencia, label_AR, label_EM, label_ET, ruta_guardado_combinado

    nombre = str(inicio) +","+str(fin)
    texto, frecuencia, ar, em, et = crear_ctn(nombre, ruta_combinados)

    label_frecuencia.configure(text=frecuencia)
    label_AR.configure(text=ar)
    label_EM.configure(text=em)
    label_ET.configure(text=et)

    with open(ruta_guardado_combinado+"\profundidad_"+str(inicio)+"-"+str(fin)+".ctn", "w") as file:
        file.write(texto)

def escoger_ruta_combinado():
    global ruta_guardado_combinado, Entry_archivo_inicio, Entry_archivo_final, ruta_guardado_label_combinado
    ruta_guardado_combinado = filedialog.askdirectory(initialdir = "/", title = "Selecciona una carpeta")
    ruta_guardado_label_combinado.insert(0,ruta_guardado_combinado+"/profundidad_"+str(Entry_archivo_inicio.get())+"-"+str(Entry_archivo_final.get())+".ctn") 

def f_select(event):
    data = textbox_content.index(INSERT).split('.')
    stringvar.set("CURSOR INFO | LINE: %s | POS: %s"%(data[0], data[1])) 

def preview_data():
    # ask for a file to read
    path_file = filedialog.askopenfilename(initialdir = "/", title = "Select a File to preview", filetypes = [("All Files","*.*"), ("Text File", "*.txt")])   
    try:
        f = open(path_file, 'r')
        lineas = f.read()
        f.close()
    except Exception as e:
        print(e)

    print(path_file)

    preview_frame = ctk.CTkToplevel()
    preview_frame.title("Previsualización de la Data")
    preview_frame.grab_set()
    preview_frame.focus()

    # Main Container of the toplevel widget
    main_container_preview = ctk.CTkFrame((preview_frame))
    main_container_preview.grid(row=0, column=0, sticky='nsew')
    # grid of the preview container
    main_container_preview.grid_rowconfigure(0, weight=1) # Show controls
    main_container_preview.grid_rowconfigure(1, weight=1) # Show content of the file
    main_container_preview.grid_columnconfigure(0, weight=1)

    # CONTAINER of the controls
    container_controls = ctk.CTkFrame(main_container_preview)
    container_controls.grid(row=0, column=0, sticky='nsew', padx=20, pady=10)
    container_controls.grid_rowconfigure(0, weight=1)
    container_controls.grid_rowconfigure(0, weight=1)
    main_container_preview.grid_columnconfigure(0, weight=1)
    main_container_preview.grid_columnconfigure(1, weight=1)
    main_container_preview.grid_columnconfigure(2, weight=1)

    label_first_line = ctk.CTkLabel(container_controls, text='First Line : ')
    label_first_line.grid(row=0, column=0, sticky='nsew', padx=20, pady=10)

    label_last_line = ctk.CTkLabel(container_controls, text='Last Line : ')
    label_last_line.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)

    entry_firt_line = ctk.CTkEntry(container_controls)
    entry_firt_line.grid(row = 0, column = 1, sticky='nsew', padx=20, pady=10)

    entry_last_line = ctk.CTkEntry(container_controls)
    entry_last_line.grid(row = 1, column = 1, sticky='nsew', padx=20, pady=10)

    # CONTAINER of the content
    container_content = ctk.CTkFrame(main_container_preview)
    container_content.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)
    container_content.grid_rowconfigure(0, weight=1)
    container_content.grid_rowconfigure(1, weight=1)
    container_content.grid_columnconfigure(0, weight=1)

    global stringvar
    stringvar = StringVar()
    stringvar.set("CURSOR INFO | LINE: %d | POS: %d"%(0,0))
    label_cursor = ctk.CTkLabel(container_content, textvariable = stringvar)
    label_cursor.grid(row = 1, columnspan = 2)
   
    global textbox_content
    textbox_content = ctk.CTkTextbox(container_content, width = 800, height = 600)
    textbox_content.grid(row=0, column=0, sticky='nsew')
    textbox_content.insert(INSERT, lineas)
    textbox_content.bind("<ButtonRelease-1>", command= f_select)

def create_toplevel_preparar():
    global scrollable_frame, label_frecuencia, label_AR, label_EM, label_ET, Entry_archivo_final, Entry_archivo_inicio, ruta_guardado_label_combinado

    preparar_frame = ctk.CTkToplevel()

    preparar_frame.title("Preparar Datos")
    preparar_frame.grab_set()
    preparar_frame.focus()
    # create label on CTkToplevel window
    container8 = ctk.CTkFrame((preparar_frame))
    container8.grid(row=0, column=0, sticky='nsew', padx=20, pady=20)

    container8.grid_rowconfigure(0, weight=1)
    container8.grid_rowconfigure(1, weight=1)
    container8.grid_rowconfigure(2, weight=1)
    container8.grid_rowconfigure(3, weight=1)
    container8.grid_rowconfigure(4, weight=1)
    container8.grid_rowconfigure(5, weight=1)
    container8.grid_columnconfigure(0, weight=1)
    container8.grid_columnconfigure(1, weight=1)

    ctk.CTkLabel(container8, text="Indique el inicio y fin de la profundidad").grid(row=0, column=0, sticky='nsew', padx=20, pady=10)

    container8_0 = ctk.CTkFrame(container8)
    container8_0.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)
    container8_0.grid_columnconfigure(0, weight=2)
    container8_0.grid_columnconfigure(1, weight=1)
    container8_0.grid_columnconfigure(2, weight=2)

    Entry_archivo_inicio = ctk.CTkEntry(container8_0)
    Entry_archivo_inicio.grid(row=0, column=0, sticky='nsew', padx=20, pady=(10))

    Entry_archivo_final = ctk.CTkEntry(container8_0)
    Entry_archivo_final.grid(row=0, column=2, sticky='nsew', padx=20, pady=10)

    ctk.CTkLabel(container8_0, text=" - ").grid(row=0, column=1, sticky='nsew', padx=5, pady=20)

    button_escoger_archivos = ctk.CTkButton(container8, text="Seleccionar archivos", font=('Times', 15), command=lambda:[boton_escoger_archivos_combinar()])
    button_escoger_archivos.grid(row=2, column=0, sticky='nsew', padx=20, pady=(10,20))

    scrollable_frame = ctk.CTkTextbox(container8, width=150, height=200)
    scrollable_frame.grid(row=3, column=0, rowspan=3, sticky='nsew', padx=20, pady=(0,20))


    container8_1 = ctk.CTkFrame(container8)
    container8_1.grid(row=0, column=1, rowspan=3, sticky='nsew', padx=(0,20), pady=20)
    container8_1.grid_rowconfigure(0, weight=1)
    container8_1.grid_rowconfigure(1, weight=1)
    container8_1.grid_rowconfigure(2, weight=1)
    container8_1.grid_rowconfigure(3, weight=1)
    container8_1.grid_columnconfigure(0, weight=1)
    container8_1.grid_columnconfigure(1, weight=1)

    container8_1_1 = ctk.CTkFrame(container8_1)
    container8_1_1.grid(row=0, column=0, sticky='nsew', padx=20, pady=(20,10))
    container8_1_1.grid_columnconfigure(0, weight=3)
    container8_1_1.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(container8_1_1, text="Frecuencia: ").grid(row=0, column=0, sticky='nswe', padx=20, pady=(20))
    label_frecuencia = ctk.CTkLabel(container8_1_1, text="")
    label_frecuencia.grid(row=0, column=1, sticky='nswe', padx=20, pady=(20))


    container8_1_2 = ctk.CTkFrame(container8_1)
    container8_1_2.grid(row=1, column=0, sticky='nsew', padx=20, pady=(10,20))
    container8_1_2.grid_columnconfigure(0, weight=3)
    container8_1_2.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(container8_1_2, text="AR: ").grid(row=0, column=0, sticky='nswe', padx=20, pady=(20))
    label_AR = ctk.CTkLabel(container8_1_2, text="")
    label_AR.grid(row=0, column=1, sticky='nswe', padx=20, pady=(20))

  
    container8_1_3 = ctk.CTkFrame(container8_1)
    container8_1_3.grid(row=0, column=1, sticky='nsew', padx=20,  pady=(20,10))
    container8_1_3.grid_columnconfigure(0, weight=3)
    container8_1_3.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(container8_1_3, text="EM: ").grid(row=0, column=0, sticky='nswe', padx=20, pady=20)
    label_EM = ctk.CTkLabel(container8_1_3, text="")
    label_EM.grid(row=0, column=1, sticky='nswe', padx=20, pady=10)

   
    container8_1_4 = ctk.CTkFrame(container8_1)
    container8_1_4.grid(row=1, column=1, sticky='nsew', padx=20, pady=(10,20))
    container8_1_4.grid_columnconfigure(0, weight=3)
    container8_1_4.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(container8_1_4, text="ET: ").grid(row=0, column=0, sticky='nswe', padx=20, pady=(20))
    label_ET = ctk.CTkLabel(container8_1_4, text="")
    label_ET.grid(row=0, column=1, sticky='nswe', padx=20, pady=(10,20))


    ctk.CTkButton(container8, text="Escoger Ruta Guardado", command=lambda:[escoger_ruta_combinado()]).grid(row=3, column=1, padx=20, pady=(20))

    ruta_guardado_label_combinado = ctk.CTkEntry(container8)
    ruta_guardado_label_combinado.grid(row=4, column=1, sticky='nsew', padx=20, pady=10)

    ctk.CTkButton(container8, text="Unir", command=lambda:[boton_preparar(Entry_archivo_inicio.get(), Entry_archivo_final.get())]).grid(row=5, column=1, padx=20, pady=(20))


raise_frame(Menup)

root.mainloop()