import random
import time
from tkinter import *
from datetime import datetime
from matplotlib import style
from matplotlib.figure import Figure
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
from obspy.core.trace import Trace
import xlsxwriter

import socket

host = "192.168.0.10"
print(host)
port = 65432
BUFFER_SIZE = 16
MESSAGE = 'Hola, mundo!' # Datos que queremos enviar

#Fuentes
fontTITULO = ('@Microsoft YaHei',100)
fontBARRA = ('@Microsoft YaHei Light',40)
fontSUBcoll = ('@Microsoft YaHei',26)
fontTEXTcoll = ('@Microsoft YaHei Light',18)

port = 65432
BUFFER_SIZE = 16
MESSAGE = 'Hola, mundo!' # Datos que queremos enviar
cont = 0

extension = ""
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

def linea_cero_KALLPA_acelerometros(acel, freq, before_time=10):
    data = np.array(acel)
    idx_impact = int((before_time)*freq)
    # Aceleracion antes del impacto
    A_ai = data[:idx_impact]
    # Aceleracion despues del impacto
    A_di = data[idx_impact:]

    trace_ai = Trace(data=A_ai).copy()
    trace_di = Trace(data=A_di).copy()

    trace_ai.stats.sampling_rate = freq*1000
    trace_di.stats.sampling_rate = freq*1000
    
    trace_ai.detrend(type = "polynomial", order = 2)
    trace_di.detrend(type = "polynomial", order = 2)

    # Concatenar
    A_linea_cero = np.concatenate((trace_ai.data, trace_di.data))
    #A_linea_cero = np.concatenate((A_ai, trace_di.data))

    return A_linea_cero

def cuentas_a_aceleracion(cuentas, freq):
    tr = Trace(data=np.array(cuentas))
    tr.stats.sampling_rate = freq*1000
    tr.detrend("polynomial", order = 2).detrend("demean").taper(0.1)
    
    return tr.data

def filtro_acelerometro(aceleracion, freq, lugar):
    tr = Trace(data=np.array(aceleracion))
    tr.stats.sampling_rate = freq*1000
    tr.filter(type= "lowpass", freq=3000)
    #tr.filter(type= "bandpass",freqmin=1,freqmax=3000)
    if lugar==1:  
        z = np.ndarray.tolist(tr.data*1)
    elif lugar==2:
        z = np.ndarray.tolist(tr.data*1)
    return z

def cuentas_a_aceleracion2(cuentas, freq, before_time=10):
    data = np.array(cuentas)
    idx_impact = int((before_time)*freq)
    # Aceleracion antes del impacto
    A_ai = data[:idx_impact]
    # Aceleracion despues del impacto
    A_di = data[idx_impact:]

    trace_ai = Trace(data=A_ai).copy()
    trace_di = Trace(data=A_di).copy()

    trace_ai.stats.sampling_rate = freq*1000
    trace_di.stats.sampling_rate = freq*1000
    
    #trace_ai.detrend(type = "polynomial", order = 2)
    #trace_di.detrend(type = "polynomial", order = 2)
    
    trace_ai.detrend(type = "linear")
    trace_di.detrend(type = "linear")

    # Concatenar
    D_linea_cero = np.concatenate((trace_ai.data, trace_di.data))

    tr = Trace(data=D_linea_cero)
    tr.stats.sampling_rate = freq*1000
    tr.detrend("demean").taper(0.1)
    return tr.data

def cuentas_a_deformacion(cuentas, freq):
    tr = Trace(data=np.array(cuentas))
    tr.stats.sampling_rate = freq*1000
    tr.detrend("polynomial",order=2).detrend("demean").taper(0.1)
    
    return tr.data

def cuentas_a_deformacion2(cuentas, freq, before_time=10):
    data = np.array(cuentas)
    idx_impact = int((before_time)*freq)
    # Deformacion antes del impacto
    D_ai = data[:idx_impact]
    # Deformacion despues del impacto
    D_di = data[idx_impact:]

    trace_ai = Trace(data=D_ai).copy()
    trace_di = Trace(data=D_di).copy()

    trace_ai.stats.sampling_rate = freq*1000
    trace_di.stats.sampling_rate = freq*1000
    
    #trace_ai.detrend(type = "polynomial", order = 2)
    #trace_di.detrend(type = "polynomial", order = 2)
    
    trace_ai.detrend(type = "linear")
    trace_di.detrend(type = "linear")

    # Concatenar
    D_linea_cero = np.concatenate((trace_ai.data, trace_di.data))

    tr = Trace(data=D_linea_cero)
    tr.stats.sampling_rate = freq*1000
    tr.detrend("demean").taper(0.1)
    return tr.data

def filtro_deformimetro(deformacion, freq, lugar):
    tr = Trace(data=np.array(deformacion))
    tr.stats.sampling_rate = freq*1000
    tr.filter(type= "lowpass", freq=5000)
    if lugar==3:
        z = np.ndarray.tolist(tr.data*2)
    elif lugar==4:
        z = np.ndarray.tolist(tr.data*2)
    elif lugar==5:
        z = np.ndarray.tolist(tr.data*2)
    elif lugar==6:
        z = np.ndarray.tolist(tr.data*2)
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


def Obtencion_data_serial(num):
    global extension
    global frecuencia_muestreo, matriz_data_archivos, pile_area, EM_valor_original, ET_valor_original, segundo_final, segundo_inicial
    global orden_sensores, ruta_data_inicial
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

    print("Estamos en obtencion data serial")
    print("El orden de los sensores es2: ", orden_sensores)

    dic_orden_sensores = {"1":A3, "2":A4, "3":S1, "4":S2, "5":S1, "6":S2, "0":NULL}
    dic_orden_sensores2 = {"1":SIN1, "2":SIN2, "3":SIN3, "4":SIN4, "5":SIN3, "6":SIN4, "0": NULL}

    orden = str(orden_sensores[-1]).replace(" ","").split("|")
    print("la fila orden es", orden_sensores[-1])

    if len(orden[4])>1:
        frecuencia_muestreo.append(int(orden[4]))

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
    
    extension = ruta_data_inicial.split("/")[-1].split(".")[-1]
    if extension == "ctn":
        data = matriz_data_archivos[num]
        
        for linea in data:
            linea = linea.split("|")
            segundos.append(float(linea[0])/10)
            for j in range(4):
                dic_orden_sensores2[orden[j]].append(round(float(linea[j+1]),2))
        segundo_inicial = segundos[0]
        segundo_final = segundos[-1]

        for i in range(4):

            if ((int(orden[i]) == 1)) or (int(orden[i]) == 2):
                for datos in dic_orden_sensores2[orden[i]]:
                    dic_orden_sensores[orden[i]].append(datos)
            elif (int(orden[i])!=0):
                for datos in dic_orden_sensores2[orden[i]]:               
                    dic_orden_sensores[orden[i]].append(datos)
        
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

        frecuencia = int(frecuencia_muestreo[-1])
        for i in range(4):
            lugar = int(orden[i])
            if ((lugar== 1)) or (lugar == 2):
                #for datos in dic_orden_sensores2[orden[i]]:
                #for datos in cuentas_a_aceleracion(dic_orden_sensores2[orden[i]],frecuencia):
                for datos in filtro_acelerometro(cuentas_a_aceleracion2(dic_orden_sensores2[orden[i]],frecuencia),frecuencia,lugar):
                    dic_orden_sensores[orden[i]].append(datos)
            elif (lugar!=0):
                #for datos in dic_orden_sensores2[orden[i]]:  
                #for datos in cuentas_a_deformacion(dic_orden_sensores2[orden[i]],frecuencia):  
                for datos in filtro_deformimetro(cuentas_a_deformacion2(dic_orden_sensores2[orden[i]],frecuencia),frecuencia,lugar):              
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

for frame in (Menup, Review, Collect_Wire, Opciones):
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
lista_botones = ["Salir", "Review", "Preparar Data", "Collet Wire", "Manual", "About"]

for i in range(len(lista_botones)):
    container4c.grid_columnconfigure(i, weight=1)

Entry_Profundidad_inicial = ''
Entry_Profundidad_final = ''

def limpiar_entrys():
    global Entry_Profundidad_inicial, Entry_Profundidad_final
    Entry_Profundidad_inicial.configure(text='')
    Entry_Profundidad_final.configure(text='')

#Button(container4, text=lista_botones[0], bg=azul_oscuro, font=fontBARRA, fg='#FFFFFF',command=lambda:root.destroy()).grid(row=4,column=0, sticky='nsew')
ctk.CTkButton(container4c, text=lista_botones[0], font=fontBARRA, command=lambda:root.destroy()).grid(row=0,column=0, sticky='nsew', padx=5, pady=5)
ctk.CTkButton(container4c, text=lista_botones[1], font=fontBARRA, command=lambda:[browseFiles(), Creacion_Grafica("arriba","aceleracion", 1, "original", "NO", "NO"), Creacion_Grafica("abajo", "deformacion", 1, "original", "NO", "NO"), eliminar_columna_muestreo(), raise_frame(Review)]).grid(row=0,column=1, sticky='nsew', pady=5, padx=(0,5))
ctk.CTkButton(container4c, text=lista_botones[2], font=fontBARRA, command=lambda:create_toplevel_preparar()).grid(row=0,column=2, sticky='nsew', pady=5, padx=(0,5))
ctk.CTkButton(container4c, text=lista_botones[3], font=fontBARRA, command=lambda:[raise_frame(Collect_Wire), limpiar_entrys()]).grid(row=0,column=3, sticky='nsew', pady=5, padx=(0,5))
ctk.CTkButton(container4c, text=lista_botones[4], font=fontBARRA, command=lambda:print("manual")).grid(row=0,column=4, sticky='nsew', pady=5, padx=(0,5))
ctk.CTkButton(container4c, text=lista_botones[5], font=fontBARRA, command=lambda:create_toplevel_about()).grid(row=0,column=5, sticky='nsew', pady=5, padx=(0,5))

# Mostrar Hora
def Obtener_hora_actual():
    return datetime.now().strftime("%H:%M:%S\n%d/%m/%y")

def refrescar_reloj():
    hora_actual.set(Obtener_hora_actual())
    container4b.after(300, refrescar_reloj)

hora_actual = StringVar(container4b, value=Obtener_hora_actual())

refrescar_reloj()

# AÑADIR PORTADA

#img.convert("RGB")

def resolver_ruta(ruta_relativa):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, ruta_relativa)
    return os.path.join(os.path.abspath('.'), ruta_relativa)

nombre_archivo_portada = resolver_ruta("CITDI_LOGO_SINFONDO.png")

imagen = PhotoImage(file=nombre_archivo_portada)
imagen = imagen.zoom(2, 2)
new_imagen = imagen.subsample(5, 5)

ctk.CTkLabel(container4b, image=new_imagen, text="").grid(row=0,column=1, columnspan=2, padx=(40), pady=40)

ctk.CTkLabel(container4b, font=fontTITULO, text="Kallpa Processor").grid(row=0, column=0, sticky='nsw', padx=(40,0), pady=20)

switch_var = ctk.StringVar(value="off")

def cambiar_tema(color):
    ctk.set_appearance_mode(color)

switch_1 = ""

def switch_event():
    global switch_1
    print(str(switch_var.get()))
    if str(switch_var.get()) == "on":
        cambiar_tema("dark")
        switch_1.configure(text="Tema Claro")
    else:
        cambiar_tema("light")
        switch_1.configure(text="Tema Oscuro")

switch_1 = ctk.CTkSwitch(container4b, text="Tema Oscuro", font=fontBARRA, command=switch_event,
                                   variable=switch_var, onvalue="on", offvalue="off")

switch_1.grid(row=2, column=2, sticky='nse', padx= 40, pady=20)
ctk.CTkLabel(container4b, textvariable=hora_actual, font=fontBARRA).grid(row=2, column=0, sticky='nsw', padx= 20, pady=20)

# FRAME DE OPERACIONES

container = ctk.CTkFrame(Review)
container.grid(row=0, column=0, sticky='nsew')

container.grid_rowconfigure(0,weight=1)
container.grid_columnconfigure(0, weight=1)
container.grid_columnconfigure(1, weight=1)
container.grid_columnconfigure(2, weight=1)


#---------------------------------------------------------------
# Frame de la izquierda

container1 = ctk.CTkFrame(container)
container1.grid(row=0, column=0, sticky='nsew')
container1.grid_columnconfigure(0, weight=1)

# Frames internos

container1_0 = ctk.CTkFrame(container1)

container1_0.grid(row=0, column=0, padx=20, pady=(40,10), sticky='new')

ctk.CTkButton(container1_0, text='Regresar', command=lambda:raise_frame(Menup)).grid(row=0,column=0, sticky='nsew', padx=(5,0) , pady=5)

container1_1 = ctk.CTkFrame(container1)
container1_1.grid(row=1, column=0, padx=20, pady=(0,10), sticky='new')
container1_1.grid_columnconfigure(0, weight=1)
container1_1.grid_columnconfigure(1, weight=1)

container1_2 = ctk.CTkFrame(container1)
container1_2.grid(row=2, column=0, padx=20, pady=10, sticky='new')
container1_2.grid_columnconfigure(0, weight=1)
container1_2.grid_columnconfigure(1, weight=1)

# Textos y Entrys Primer Frame
textos_primer_frame = ["Área(cm^2)", "M. Elasticidad(MPa)", "Energía Teórica(J)"]

#ET_Entry

ctk.CTkLabel(container1_1, text=textos_primer_frame[0]).grid(row=0,column=0, padx=10, pady=5, sticky='nw')
pile_area_label = ctk.CTkLabel(container1_1, text=str(round(float(pile_area),2)))
pile_area_label.grid(row=0, column=1, padx=10, pady=5, sticky='new')
ctk.CTkLabel(container1_1, text=textos_primer_frame[1]).grid(row=1,column=0, padx=10, pady=5, sticky='nw') 
EM_label = ctk.CTkLabel(container1_1, text=str(round(float(EM_valor_original),2)))
EM_label.grid(row=1, column=1, padx=10, pady=5, sticky='new')
ctk.CTkLabel(container1_1, text=textos_primer_frame[2]).grid(row=2,column=0, padx=10, pady=5, sticky='nw')
ET_label = ctk.CTkLabel(container1_1, text=str("0"))
ET_label.grid(row=2, column=1, padx=10, pady=5, sticky='new')

# Textos y Entrys Segundo Frame
#textos_segundo_frame = ["BL #", "RSP(kN)", "RMX(kN)", "RSU(kN)", "FMX(kN)", "VMX(m/s)", "EMX(kN.m)", "DMX(mm)", "DFN(mm)", "CSX(MPa)", "TSX(MPa)", "BTA"]

Label_Num_Grafica = ctk.CTkLabel(container1_2, text="")
Label_Num_Grafica.grid(row=0,column=0, columnspan=2, padx=10, pady=5, sticky='new') 

textos_segundo_frame = ["FMX(kN)", "VMX(m/s)", "EMX(J)", "DMX(cm)", "ETR", "CE", "CSX(MPa)", "DFN(mm)", "MEX", "AMX(g's)"]
valores_segundo_frame_arriba = ["", "", "", "", "", "", "", "", "", ""]
valores_segundo_frame_abajo = ["", "", "", "", "", "", "", "", "", ""]
# labels fijos de texto
for i in range(len(textos_segundo_frame)):
    ctk.CTkLabel(container1_2, text=textos_segundo_frame[i]).grid(row=i+1,column=0, padx=10, pady=5, sticky='nw') 


L_FMX = ctk.CTkLabel(container1_2, text=valores_segundo_frame_arriba[0])
L_FMX.grid(row=1, column=1,padx=10, pady=5, sticky='nwe')

L_VMX = ctk.CTkLabel(container1_2, text=valores_segundo_frame_arriba[1])
L_VMX.grid(row=2, column=1,padx=10, pady=5, sticky='nwe')

L_EMX = ctk.CTkLabel(container1_2, text=valores_segundo_frame_arriba[2])
L_EMX.grid(row=3, column=1,padx=10, pady=5, sticky='nwe')

L_DMX = ctk.CTkLabel(container1_2, text=valores_segundo_frame_arriba[3])
L_DMX.grid(row=4, column=1,padx=10, pady=5, sticky='nwe')  
 
L_ETR = ctk.CTkLabel(container1_2, text=valores_segundo_frame_arriba[4])
L_ETR.grid(row=5, column=1,padx=10, pady=5, sticky='nwe')

L_CE = ctk.CTkLabel(container1_2, text=valores_segundo_frame_arriba[5])
L_CE.grid(row=6, column=1,padx=10, pady=5, sticky='nwe')  

L_CSX = ctk.CTkLabel(container1_2, text=valores_segundo_frame_arriba[6])
L_CSX.grid(row=7, column=1,padx=10, pady=5, sticky='nwe')

L_DFN = ctk.CTkLabel(container1_2, text=valores_segundo_frame_arriba[7])
L_DFN.grid(row=8, column=1,padx=10, pady=5, sticky='nwe')

L_MEX = ctk.CTkLabel(container1_2, text=valores_segundo_frame_arriba[8])
L_MEX.grid(row=9, column=1,padx=10, pady=5, sticky='nwe')  

L_AMX = ctk.CTkLabel(container1_2, text=valores_segundo_frame_arriba[9])
L_AMX.grid(row=10, column=1,padx=10, pady=5, sticky='nwe')  



def modificar_datos_segundo_frame(posicion,texto_label_num_grafica, V_FMX, V_VMX, V_EMX, V_DMX, V_ETR, V_CE, V_CSX, V_DFN, V_MEX, V_AMX):
    global valores_segundo_frame_arriba, valores_segundo_frame_abajo
    global Label_Num_Grafica
    global L_FMX, L_VMX, L_EMX, L_DMX, L_ETR, L_CE, L_CSX, L_DFN, L_MEX, L_AMX
    Label_Num_Grafica.configure(text= str(texto_label_num_grafica), font=fontTEXTcoll)
    L_FMX.configure(text = str(V_FMX))
    L_VMX.configure(text = str(V_VMX))
    L_EMX.configure(text = str(V_EMX))
    L_DMX.configure(text = str(V_DMX))
    L_ETR.configure(text = str(V_ETR))
    L_CE.configure(text = str(V_CE))
    L_CSX.configure(text = str(V_CSX))
    L_DFN.configure(text = str(V_DFN))
    L_MEX.configure(text = str(V_MEX))
    L_AMX.configure(text = str(V_AMX))

    if posicion == 'arriba':
        valores_segundo_frame_arriba = [texto_label_num_grafica, V_FMX, V_VMX, V_EMX, V_DMX, V_ETR, V_CE, V_CSX, V_DFN, V_MEX, V_AMX]
    else:
        valores_segundo_frame_abajo = [texto_label_num_grafica, V_FMX, V_VMX, V_EMX, V_DMX, V_ETR, V_CE, V_CSX, V_DFN, V_MEX, V_AMX]

#--------------------------------------------------
# Frame Principal del medio
container2 = ctk.CTkFrame(container)
container2.grid_columnconfigure(0, weight=30)
container2.grid_columnconfigure(1, weight=1)
container2.grid_rowconfigure(0, weight=1)
container2.grid_rowconfigure(1, weight=1)

container2.grid(row=0,column=1, padx=(30,10), pady=(30))


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
container2_1_1.grid_columnconfigure(0, weight=1)
container2_1_1.grid_columnconfigure(1, weight=20)
container2_1_1.grid_columnconfigure(2, weight=1)
container2_1_1.grid_rowconfigure(0, weight=1)

container2_1_2 = ctk.CTkFrame(container2_1, fg_color="#1359BB")
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
container2_2_1.grid_columnconfigure(0, weight=1)
container2_2_1.grid_columnconfigure(1, weight=20)
container2_2_1.grid_columnconfigure(2, weight=1)
container2_2_1.grid_rowconfigure(0, weight=1)

container2_2_2 = ctk.CTkFrame(container2_2, fg_color="#94e7ff")
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

dic_magnitud_botones = {0:'aceleracion', 1:'velocidad', 2:'deformacion', 3:'fuerza', 4:'desplazamiento', 5:'fuerzaxvelocidad', 6:'avged', 7:'wu', 8:'wd'}
dic_ultima_grafica_magnitud = {"arriba": ultima_magnitud_arriba, "abajo": ultima_magnitud_abajo}

def actualizar_magnitud(posicion,i):
    global ultima_magnitud_abajo
    global ultima_magnitud_arriba
    dic_ultima_grafica_magnitud[posicion] = dic_magnitud_botones[i]

texto_botones_frame= ["ACELERACIÓN", "VELOCIDAD", "DEFORMACIÓN", "FUERZA", "DESPLAZAMIENTO", "F vs V", "Avg ED", "WU", "WD"]

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
        case "WU":
            cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
            actualizar_magnitud("arriba", texto_botones_frame.index(value))
        case "WD":
            cambiar_magnitud_grafica("arriba", texto_botones_frame.index(value))
            actualizar_magnitud("arriba", texto_botones_frame.index(value))
    print("En la grafica de arriba es ",value)
            
def segmented_button_callback2(value):
    global texto_botones_frame
    print("el valor seleccionado es: ",value)
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
        case "WU":
            cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
            actualizar_magnitud("abajo", texto_botones_frame.index(value))
        case "WD":
            cambiar_magnitud_grafica("abajo", texto_botones_frame.index(value))
            actualizar_magnitud("abajo", texto_botones_frame.index(value))    
    print("En la grafica de abajo es ",value)

Button_num_grafica_arriba = ctk.CTkButton(container2_1_1, text="1", command=lambda:colorear_botones_seleccion_grafica(1))
Button_num_grafica_arriba.grid(row=0, column=0, sticky='nsw', pady=5)

Button_num_grafica_abajo = ctk.CTkButton(container2_2_1, text="1", command=lambda:colorear_botones_seleccion_grafica(2))
Button_num_grafica_abajo.grid(row=0, column=0, sticky='nsw', pady=5)

segemented_button_var1 = ctk.StringVar(value="ACELERACIÓN")
segemented_button = ctk.CTkSegmentedButton(container2_1_1, values=texto_botones_frame, command=segmented_button_callback1, variable=segemented_button_var1)
segemented_button.grid(row=0,column=1, sticky='nsew', pady=5, padx=(5,0))

segemented_button_var2 = ctk.StringVar(value="DEFORMACIÓN")
segemented_button2 = ctk.CTkSegmentedButton(container2_2_1, values=texto_botones_frame, command=segmented_button_callback2, variable=segemented_button_var2)
segemented_button2.grid(row=0,column=1, sticky='nsew', pady=5, padx=(5,0))

# Barra lateral de la columna de la derecha

container2_3 = ctk.CTkFrame(container2, corner_radius=0)
container2_3.grid(row=0, rowspan=2, column=1, sticky='nsew')
container2_3.grid_rowconfigure(0, weight=1)
container2_3.grid_columnconfigure(0, weight=1)


def colorear_botones_seleccion_grafica(num):
    global ultima_grafica_seleccionada, valores_segundo_frame_arriba, valores_segundo_frame_abajo, container2_1_2, container2_2_2
    
    if num == 1:
        ultima_grafica_seleccionada = 'arriba'
        container2_1_2.configure(fg_color="#1359BB")
        container2_2_2.configure(fg_color="#94e7ff")
        v_vec = valores_segundo_frame_arriba.copy()
        modificar_datos_segundo_frame('arriba', v_vec[0], v_vec[1], v_vec[2], v_vec[3], v_vec[4], v_vec[5], v_vec[6], v_vec[7], v_vec[8], v_vec[9], v_vec[10])
    else:
        ultima_grafica_seleccionada = 'abajo'
        container2_2_2.configure(fg_color="#1359BB")
        container2_1_2.configure(fg_color="#94e7ff")
        v_vec = valores_segundo_frame_abajo.copy()
        modificar_datos_segundo_frame('abajo', v_vec[0], v_vec[1], v_vec[2], v_vec[3], v_vec[4], v_vec[5], v_vec[6], v_vec[7], v_vec[8], v_vec[9], v_vec[10])


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
    global extension
    print("estoy entrando a velocity", extension)
    tr_a = Trace(data=np.array(acel)*9.81)
    tr_a.stats.sampling_rate = freq*1000
    tr_v = tr_a.copy()
    tr_v.integrate(method = "cumtrapz")
    if extension == 'ctn':
        print("estoy entrando a ctn")
        idx_impact = int(0.01*freq*1000)
        # Velocity before impact
        V_bi = tr_v.data[:idx_impact]
        # Velocity after impatc
        V_ai = tr_v.data[idx_impact:]

        tr_V_ai0 = Trace(data=V_ai)
        tr_V_ai = tr_V_ai0.copy()
        tr_V_ai.stats.sampling_rate = freq*1000
        tr_V_ai.detrend("simple")

        # Concatenating again
        V_bl = np.concatenate((V_bi, tr_V_ai.data))

        # Making a trace
        tr_v_bl = Trace(data=V_bl)
        tr_v_bl.stats.sampling_rate = freq*1000
        return tr_v_bl
    else:
        idx_impact = int(0.01*freq*1000)
        # Velocity before impact
        V_bi = tr_v.data[:idx_impact]
        # Velocity after impatc
        V_ai = tr_v.data[idx_impact:]

        tr_V_ai0 = Trace(data=V_ai)
        tr_V_ai = tr_V_ai0.copy()
        tr_V_ai.stats.sampling_rate = freq*1000
        #tr_V_ai.detrend("polynomial",order=2)
        tr_V_ai.detrend("polynomial",order=2)
        # Concatenating again
        V_bl = np.concatenate((V_bi, tr_V_ai.data))

        # Making a trace
        tr_v_bl = Trace(data=V_bl)
        tr_v_bl.stats.sampling_rate = freq*1000
        return tr_v_bl

def calculo_wu(F, V_transformado):
    suma = []
    for i in range(len(F)):
        suma.append((F[i]-V_transformado[i])/2)
    return suma

def calculo_wd(F, V_transformado):
    suma = []
    for i in range(len(F)):
        suma.append((F[i]+V_transformado[i])/2)
    return suma

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

for posicion in ['arriba', 'abajo']:
    B1_izquierda = ctk.CTkButton(dic_posicion[posicion][2], text="<", width=30, height=30, command=lambda:moverlimite(posicion, magnitud, dic_ultima_grafica[posicion], 'mantener', condicion, 'MODIFICAR', '1', 'izquierda'))
    B1_izquierda.grid(row=0, column=0, padx=(5,5))
    B1_derecha = ctk.CTkButton(dic_posicion[posicion][2], text=">",  width=30, height=30, command=lambda:moverlimite(posicion, magnitud, dic_ultima_grafica[posicion], 'mantener', condicion, 'MODIFICAR', '1', 'derecha'))
    B1_derecha.grid(row=0, column=1, padx=(0,5))
    B2_izquierda = ctk.CTkButton(dic_posicion[posicion][2], text="<",  width=30, height=30, command=lambda:moverlimite(posicion, magnitud, dic_ultima_grafica[posicion], 'mantener', condicion, 'MODIFICAR', '2', 'izquierda'))
    B2_izquierda.grid(row=0, column=2, padx=(0,5))
    B2_derecha = ctk.CTkButton(dic_posicion[posicion][2], text=">",  width=30, height=30, command=lambda:moverlimite(posicion, magnitud, dic_ultima_grafica[posicion], 'mantener', condicion, 'MODIFICAR', '2', 'derecha'))
    B2_derecha.grid(row=0, column=3, padx=(0,5))


def Creacion_Datos_Graficas(posicion, magnitud, num, direccion, mantener_limites, a_primera_marca=0, a_segunda_marca=0):
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
    WU = []
    WD = []
    V_Transformado = []
    V_Transformado_valor_real = []
    global L_EMX, L_FMX, L_VMX, L_DMX, L_CE, L_ETR, LIM_IZQ, LIM_DER
    global desplazado_arriba, desplazado_abajo

    print("el gráfico que se hace es ", num)
    segundos, S1, S2, A3, A4 = Obtencion_data_serial(num)
    Z = 0
    EM = float(EM_valor_original)
    AR = float(pile_area)
    factor = EM * AR
    longitud = max(len(S1), len(S2))
    longitud2 = max(len(A3), len(A4))
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
        if S1 != [] and len(S1) == longitud:
            F1.append(m1)
        if S2 != [] and len(S2) == longitud:
            F2.append(m2)
        F.append(promedio)
    
    print("longitudes de Str", len(S1), len(S2))
    if len(S1) != longitud:
        S1 = S2
        F = F2
        F1 = F2
    if len(S2) != longitud:
        S2 = S1
        F = F1
        F2 = F1
    MEX = round(max(max(S1), max(S2)),2) 
    if len(A3) != longitud2:
        A3 = A4
    if len(A4) != longitud2:
        A4 = A3
    AMX = round(max(max(A3), max(A4)),2) 
    print("longitudes de Str2", len(S1), len(S2))    
    if S1 == []:
        F = F2
    elif S2 == []:
        F = F1
    Fmax = round(max(F), 2)
    Fmax_original = max(F)
    
    print("longitudes de fuerza", len(F1), len(F2), len(F))
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
    print("longitudes velocidad: ", len(V1), len(V2), len(V))

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
    DFN = round(D[-1],2)
    
    ajuste = 0
   
    Z = ((AR*(1000000))*EM*(0.0001))/(5103.44*1000)

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
    
    LIM_IZQ.configure(text = str(round(valor_primera_marca,2))+" ms")
    LIM_DER.configure(text = str(round(valor_segunda_marca,2))+" ms")
    
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
    if magnitud == 'fuerzaxvelocidad':
        ax1.axvline(valor_primera_marca, color='r', ls="dotted")
        ax1.axvline(valor_segunda_marca, color='r', ls="dotted")


    rango_inferior = segundos.index(round(valor_primera_marca,2))
    rango_superior = segundos.index(round(valor_segunda_marca,2))
    try:
        E = energy(F[rango_inferior:rango_superior],V[rango_inferior:rango_superior], int(frecuencia_muestreo[-1])).data
    except Exception as e:
        print(f"Error al calcular la Energía E {E}")
    j = 0
    segundos_Transformado = []
    for i in range(segundos.index(round(valor_primera_marca,2)),segundos.index(round(valor_segunda_marca,2))):
        n = round(valor_primera_marca+(j/(int(frecuencia_muestreo[-1]))),2)
        j+=1
        segundos_Transformado.append(n)
    
    Emax = round(max(E), 2)

    # anadiendo el calculo de wu
    try:
        WU = calculo_wu(F, V_Transformado)
    except Exception as e:
        print("Error al calcular el wu", e)
    try:
        WD = calculo_wd(F, V_Transformado)
    except Exception as e:
        print("Error al calcular el wd", e)
    
    if magnitud == 'avged':
        segundos = segundos_Transformado
    
    ET = float(ET_valor_original)
    ETR = round(100*(Emax/ET),2)
    CE = str(round(ETR*0.60,2))
    CSX = str(round(Fmax*10/AR,2))
    
    return A3, A4, S1, S2, F1, F2, V1, V2, E, D1, D2, F, V_Transformado, segundos, ET, ETR, CE, Fmax, Vmax, Emax, Dmax, Z, WU, WD, CSX, DFN, MEX, AMX
        
style.use('seaborn-v0_8-whitegrid')

# grafica 1
fig1 = Figure(figsize=(10, 5), dpi=100)

ax1 = fig1.add_subplot(111)

canvas1 = FigureCanvasTkAgg(fig1, dic_posicion['arriba'][0])
canvas1.draw()
canvas1.get_tk_widget().pack(side=TOP, expand=1, fill=BOTH, padx=10, pady=10)

toolbar = Toolbar(canvas1, dic_posicion['arriba'][1])
toolbar.config(background="#2A2A2A")
toolbar.update()
canvas1._tkcanvas.pack(side=BOTTOM, expand=1, fill=BOTH)
fig1.subplots_adjust(left=0.1,bottom=0.15,right=0.98,top=0.96)

t1, = ax1.plot(np.arange(1, 8001), np.zeros(8000))
t2, = ax1.plot(np.arange(1, 8001), np.zeros(8000))

# grafica 2
fig2 = Figure(figsize=(10, 5), dpi=100)

ax2 = fig2.add_subplot(111)

canvas2 = FigureCanvasTkAgg(fig2, dic_posicion['abajo'][0])
canvas2.draw()
canvas2.get_tk_widget().pack(side=TOP, expand=1, fill=BOTH, padx=10, pady=10)

toolbar = Toolbar(canvas2, dic_posicion['abajo'][1])
toolbar.config(background="#2A2A2A")
toolbar.update()
canvas2._tkcanvas.pack(side=BOTTOM, expand=1, fill=BOTH)
fig2.subplots_adjust(left=0.1,bottom=0.15,right=0.98,top=0.96)

t3, = ax2.plot(np.arange(1, 8001), np.zeros(8000))
t4, = ax2.plot(np.arange(1, 8001), np.zeros(8000))

estado = "aceleracion"

def Creacion_Grafica(posicion, magnitud, num, direccion, mantener_relacion_aspecto, mantener_limites, a_primera_marca=0, a_segunda_marca=0):
    global t1, t2, t3, t4, ax1, fig1, canvas1, ax2, fig2, canvas2
    global A3, A4, S1, S2, F1, F2, V1, V2, E, D1, D2, WU, WD
    A3, A4, S1, S2, F1, F2, V1, V2, E, D1, D2, F, V_Transformado, segundos, ET, ETR, CE, Fmax, Vmax, Emax, Dmax, Z, WU, WD, CSX, DFN, MEX, AMX = Creacion_Datos_Graficas(posicion, magnitud, num, direccion, mantener_limites, a_primera_marca=0, a_segunda_marca=0)
    dic_magnitud = {'aceleracion':[A3, A4], 'deformacion':[S1, S2], 'fuerza':[F1, F2], 'velocidad':[V1, V2], 'avged':[E, E], 'desplazamiento':[D1, D2], 'fuerzaxvelocidad':[F,V_Transformado], 'wu':[WU, WU], 'wd':[WD, WD]}
    dic_legenda = {'aceleracion':["A3", "A4"], 'deformacion':["S1", "S2"], 'fuerza':["F1", "F2"], 'velocidad':["V1", "V2"], 'avged':["E", "E"], 'desplazamiento':["D1", "D2"], 'fuerzaxvelocidad':["F", str(round(Z, 2))+"*V"], 'wu':['WU', 'WU'], 'wd':['WD', 'WD']}
    dic_unidades = {'aceleracion':["milisegundos", "g`s"], 'deformacion':["milisegundos", "micro strain"], 'fuerza':["milisegundos", "kN"], 'velocidad':["milisegundos", "m/s"], 'avged':["milisegundos", ""], 'desplazamiento':["milisegundos", "m"], 'fuerzaxvelocidad':["milisegundos", ""], 'wu':['milisegundos', ''], 'wd':['milisegundos', '']}

    texto_label_num_grafica = str(dic_ultima_grafica[posicion])+"/"+str(len(matriz_data_archivos)-1)
    
    if posicion == 'arriba': 
        Button_num_grafica_arriba.configure(text=dic_ultima_grafica[posicion])
    elif posicion == 'abajo': 
        Button_num_grafica_abajo.configure(text=dic_ultima_grafica[posicion])
    
    
    modificar_datos_segundo_frame(posicion, texto_label_num_grafica, Fmax, Vmax, Emax, Dmax, str(ETR) + "%", CE, CSX, DFN, MEX, AMX)

    if mantener_relacion_aspecto == 'SI':
        ax1.set_xlim(dic_posicion_zoom[posicion][0], dic_posicion_zoom[posicion][1])
        ax1.set_ylim(dic_posicion_zoom[posicion][2], dic_posicion_zoom[posicion][3])

    if posicion == 'arriba':
        fig1.clear()
        ax1 = fig1.add_subplot(111)
        t1, = ax1.plot(segundos, dic_magnitud[magnitud][0], label=dic_legenda[magnitud][0])
        t2, = ax1.plot(segundos, dic_magnitud[magnitud][1], label=dic_legenda[magnitud][1])
        ax1.set_xlabel(dic_unidades[magnitud][0])
        ax1.set_ylabel(dic_unidades[magnitud][1])
        try:
            ax1.legend(handles=[t1, t2])
        except:
            try:
                ax1.legend(handles=[t1])
            except:
                try:
                    ax1.legend(handles=[t2])
                except:
                    pass
        canvas1.draw()
    elif posicion == 'abajo':
        fig2.clear()
        ax2 = fig2.add_subplot(111)
        t3, = ax2.plot(segundos, dic_magnitud[magnitud][0], label=dic_legenda[magnitud][0])
        t4, = ax2.plot(segundos, dic_magnitud[magnitud][1], label=dic_legenda[magnitud][1])
        ax2.set_xlabel(dic_unidades[magnitud][0])
        ax2.set_ylabel(dic_unidades[magnitud][1])
        try:
            ax2.legend(handles=[t1, t2])
        except:
            try:
                ax2.legend(handles=[t1])
            except:
                try:
                    ax2.legend(handles=[t2])
                except:
                    pass
        canvas2.draw()

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
container3_1.grid_columnconfigure(0, weight=2)
container3_1.grid_columnconfigure(1, weight=1)
T_1 = ctk.CTkLabel(container3_1, text="Límites de la gráfica").grid(row=0,column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

container3_2 = ctk.CTkFrame(container3)
container3_2.grid(row=1, column=0, padx=20, pady=(20,10), sticky='new')

container3_2.grid_columnconfigure(0, weight=2)
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
container3_3.grid_columnconfigure(0, weight=2)
container3_3.grid_columnconfigure(1, weight=1)

container3_3.rowconfigure(0, weight=1)
container3_3.rowconfigure(1, weight=1)
container3_3.rowconfigure(2, weight=1)
container3_3.rowconfigure(3, weight=1)

T_2 = ctk.CTkLabel(container3_3, text="Límites input").grid(row=0,column=0, padx=10, pady=10, sticky='nsew')

ctk.CTkLabel(container3_3, text=textos_tercer_frame[0]).grid(row=1,column=0, padx=(10,0), pady=10, sticky='nw') 
LIM_IZQ_Entry = ctk.CTkEntry(container3_3)
LIM_IZQ_Entry.grid(row=1, column=1,padx=(0,10), pady=10, sticky='nwe')
ctk.CTkLabel(container3_3, text=textos_tercer_frame[1]).grid(row=2,column=0, padx=(10,0), pady=10, sticky='nw') 
LIM_DER_Entry = ctk.CTkEntry(container3_3)
LIM_DER_Entry.grid(row=2, column=1,padx=(0,10), pady=10, sticky='nwe')

ctk.CTkButton(container3_3, text='Actualizar', command=lambda:actualizar_limites()).grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky='nw')

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
container3_4.grid_columnconfigure(0, weight=2)
container3_4.grid_rowconfigure(0, weight=1)

ctk.CTkButton(container3_4, text='Exportar', command=lambda:[Seleccionar_ruta_guardado_pdf(), create_toplevel_export()]).grid(row=0, column=0, padx=10, pady=10, sticky='new')

def preparaciones_exportar(label_cantidad_golpes, label_inicio, label_final):
    global matriz_data_archivos
    # este "," no debe ser reemplazado a ";" debido a que es para identificar las profundidades
    longitudes = matriz_data_archivos[0][12:].split(",")
    print(longitudes)
    label_cantidad_golpes.configure(text='Cantidad de Golpes:'+str(len(matriz_data_archivos)-1))
    label_inicio.configure(text='Inicio:'+str(longitudes[0]))
    label_final.configure(text='Final:'+str(longitudes[1]))

#--------------------FRAME2------------------------------------------------------------

container5 = ctk.CTkFrame((Collect_Wire))
container5.grid(row=0, column=0, sticky='nsew')
container5.grid_rowconfigure(0, weight=1)
container5.grid_rowconfigure(1, weight=10)
container5.grid_rowconfigure(2, weight=1)
container5.grid_rowconfigure(3, weight=10)
container5.grid_columnconfigure(0, weight=1)
container5.grid_columnconfigure(1, weight=1)
container5.grid_columnconfigure(2, weight=1)


puertos=[""]
estado_puerto = False

def detectar_puertos():

    global socket_tcp, estado_puerto
    host = "192.168.0.10"
    port = 65432
    
    if estado_puerto == False:
        try:
            socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            socket_tcp.connect((host, port))
            estado_puerto = True
            MessageBox.showinfo(title="Conectado", message="Se ha conectado con éxito.")
        except:
            MessageBox.showerror("Error", "No se puede conectar")
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
    
container5_1 = ctk.CTkFrame(container5)

container5_1.grid(row=1, column=0, sticky='nsew', padx=20, pady=(20,10))
container5_1.grid_rowconfigure(0, weight=1)
container5_1.grid_rowconfigure(1, weight=8)
container5_1.grid_columnconfigure(0, weight=1)

container5_1_0 = ctk.CTkFrame(container5)

container5_1_0.grid(row=0, column=0, sticky='nsew', padx=20, pady=(10))
container5_1_0.grid_rowconfigure(0, weight=1)
container5_1_0.grid_rowconfigure(1, weight=1)
container5_1_0.grid_rowconfigure(2, weight=1)
container5_1_0.grid_columnconfigure(0, weight=1)

Label_titulo_1 = ctk.CTkLabel(container5_1_0, text='Selección de Sensores', font=fontSUBcoll)
Label_titulo_1.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

container5_1_1 = ctk.CTkFrame(container5_1)
container5_1_1.grid(row=0, column=0, sticky='nsew', padx=10, pady=(10,0))
container5_1_1.grid_rowconfigure(0, weight=1)
container5_1_1.grid_columnconfigure(0, weight=1)
container5_1_1.grid_columnconfigure(1, weight=1)


container5_1_2 = ctk.CTkFrame(container5_1)
container5_1_2.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
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
        print(orden_sensores[-1])
        orden = str(orden_sensores[-1]).replace(" ","").split("|")

        try:
            Label_sensor1_data.configure(text=dic_sensores[orden[0]], font=fontTEXTcoll)
            Label_sensor2_data.configure(text=dic_sensores[orden[1]], font=fontTEXTcoll)
            Label_sensor3_data.configure(text=dic_sensores[orden[2]], font=fontTEXTcoll)
            Label_sensor4_data.configure(text=dic_sensores[orden[3]], font=fontTEXTcoll)
        except:
            print("debe ser esto")
            pass
    except:
        print("No sabo")
        pass

Label_sensor1 = ctk.CTkLabel(container5_1_2, text="Sensor 1:", font=fontTEXTcoll)
Label_sensor1.grid(row=0, column=0, sticky='nsew', padx=(20,0), pady=(20,10))
Label_sensor2 = ctk.CTkLabel(container5_1_2, text="Sensor 2:", font=fontTEXTcoll)
Label_sensor2.grid(row=1, column=0, sticky='nsew', padx=(20,0), pady=(10,10))
Label_sensor3 = ctk.CTkLabel(container5_1_2, text="Sensor 3:", font=fontTEXTcoll)
Label_sensor3.grid(row=2, column=0, sticky='nsew', padx=(20,0), pady=(10,10))
Label_sensor4 = ctk.CTkLabel(container5_1_2, text="Sensor 4:", font=fontTEXTcoll)
Label_sensor4.grid(row=3, column=0, sticky='nsew', padx=(20,0), pady=(10,20))

Label_sensor1_data = ctk.CTkLabel(container5_1_2, text="No disponible", font=fontTEXTcoll, fg_color= ["#F9F9FA", "#343638"])
Label_sensor1_data.grid(row=0, column=1, sticky='nsew', padx=(0,20), pady=(20,10))
Label_sensor2_data = ctk.CTkLabel(container5_1_2, text="No disponible", font=fontTEXTcoll, fg_color= ["#F9F9FA", "#343638"])
Label_sensor2_data.grid(row=1, column=1, sticky='nsew', padx=(0,20), pady=(10,10))
Label_sensor3_data = ctk.CTkLabel(container5_1_2, text="No disponible", font=fontTEXTcoll, fg_color= ["#F9F9FA", "#343638"])
Label_sensor3_data.grid(row=2, column=1, sticky='nsew', padx=(0,20), pady=(10,10))
Label_sensor4_data = ctk.CTkLabel(container5_1_2, text="No disponible", font=fontTEXTcoll, fg_color= ["#F9F9FA", "#343638"])
Label_sensor4_data.grid(row=3, column=1, sticky='nsew', padx=(0,20), pady=(10,20))


ctk.CTkButton(container5_1_1, text="Conectar al servidor", font=fontTEXTcoll, command=lambda: [detectar_puertos()]).grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
ctk.CTkButton(container5_1_1, text="Actualizar orden de sensores", font=fontTEXTcoll,command=lambda: [verificacion_orden_sensores(), Generar_Tabla_Sensores()]).grid(row=0, column=1, sticky='nsew', padx=(0,5), pady=5)

container5_2 = ctk.CTkFrame(container5)
container5_2.grid(row= 1, column=1, sticky='nsew', padx=(10,20), pady=20)
container5_2.grid_rowconfigure(0, weight=1)
container5_2.grid_columnconfigure(0, weight=1)

container5_2_0 = ctk.CTkFrame(container5)
container5_2_0.grid(row=0, column=1, sticky='nsew', padx=(10,20), pady=(10))
container5_2_0.grid_rowconfigure(0, weight=1)
container5_2_0.grid_rowconfigure(1, weight=1)
container5_2_0.grid_rowconfigure(2, weight=1)
container5_2_0.grid_columnconfigure(0, weight=1)


Label_titulo_2 = ctk.CTkLabel(container5_2_0, text='Parámetros de la varilla', font=fontSUBcoll)
Label_titulo_2.grid(row=1, column=0, sticky='nsew', padx=10)

container5_2_2 = ctk.CTkFrame(container5_2)
container5_2_2.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

container5_2_2.grid_rowconfigure(0, weight=1)
container5_2_2.grid_rowconfigure(1, weight=1)
container5_2_2.grid_columnconfigure(0, weight=1)

container5_2_2_1 = ctk.CTkFrame(container5_2_2)
container5_2_2_1.grid(row=0, column=0, sticky='nsew', padx=(40), pady=(80,40))
container5_2_2_1.grid_rowconfigure(0, weight=1)
container5_2_2_1.grid_rowconfigure(1, weight=1)
container5_2_2_1.grid_rowconfigure(2, weight=1)
container5_2_2_1.grid_columnconfigure(0, weight=3)
container5_2_2_1.grid_columnconfigure(1, weight=2)
container5_2_2_1.grid_columnconfigure(2, weight=1)

container5_2_2_2 = ctk.CTkFrame(container5_2_2)
container5_2_2_2.grid(row=1, column=0, sticky='nsew', padx=(40), pady=(40,80))
container5_2_2_2.grid_rowconfigure(0, weight=1)
container5_2_2_2.grid_rowconfigure(1, weight=1)
container5_2_2_2.grid_rowconfigure(2, weight=1)
container5_2_2_2.grid_columnconfigure(0, weight=3)
container5_2_2_2.grid_columnconfigure(1, weight=2)
container5_2_2_2.grid_columnconfigure(2, weight=1)

Label_Area = ctk.CTkLabel(container5_2_2_1, text="Área", font=fontTEXTcoll).grid(row=1, column=0, sticky='nsew')
Entry_Area = ctk.CTkEntry(container5_2_2_1, font=fontTEXTcoll)
Entry_Area.grid(row=1, column=1, sticky='nsew')
Entry_Area.insert(0, "7.8")
Label_Area_unidad = ctk.CTkLabel(container5_2_2_1, text="cm2", font=fontTEXTcoll).grid(row=1, column=2, sticky='nsew', padx=(0,5))

Label_Modulo_Elasticidad = ctk.CTkLabel(container5_2_2_2, text="Módulo de \nElasticidad ", font=fontTEXTcoll).grid(row=1, column=0, sticky='nsew')
Entry_modulo_elasticidad = ctk.CTkEntry(container5_2_2_2, font=fontTEXTcoll)
Entry_modulo_elasticidad.grid(row=1, column=1, sticky='nsew')
Entry_modulo_elasticidad.insert(0, "207000")
Label_Modulo_Elasticidad_unidad = ctk.CTkLabel(container5_2_2_2, text="MPa", font=fontTEXTcoll).grid(row=1, column=2, sticky='nsew', padx=(0,5))


container5_3 = ctk.CTkFrame(container5)
container5_3.grid(row=3, column=0, sticky='nsew', padx=20, pady=(20))
container5_3.grid_rowconfigure(0, weight=1)
container5_3.grid_columnconfigure(0, weight=1)

conteiner5_3_0 = ctk.CTkFrame(container5)
conteiner5_3_0.grid(row=2, column=0, sticky='nsew', padx=20, pady=(10))
conteiner5_3_0.grid_rowconfigure(0, weight=1)
conteiner5_3_0.grid_rowconfigure(1, weight=1)
conteiner5_3_0.grid_rowconfigure(2, weight=1)
conteiner5_3_0.grid_columnconfigure(0, weight=1)

Label_titulo_3 = ctk.CTkLabel(conteiner5_3_0, text='Profundidad', font=fontSUBcoll)
Label_titulo_3.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

container5_3_1 = ctk.CTkFrame(container5_3)
container5_3_1.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
container5_3_1.grid_rowconfigure(0, weight=2)
container5_3_1.grid_rowconfigure(1, weight=2)
container5_3_1.grid_rowconfigure(2, weight=1)
container5_3_1.grid_columnconfigure(0, weight=1)
container5_3_1.grid_columnconfigure(1, weight=1)

container5_3_1_1 = ctk.CTkFrame(container5_3_1)
container5_3_1_1.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=10, pady=(60))
container5_3_1_1.grid_rowconfigure(0, weight=1)
container5_3_1_1.grid_columnconfigure(0, weight=5)
container5_3_1_1.grid_columnconfigure(1, weight=2)
container5_3_1_1.grid_columnconfigure(2, weight=1)
container5_3_1_1.grid_columnconfigure(3, weight=2)

Label_titulo_4 = ctk.CTkLabel(container5_3_1_1, text="Rango de \nProfundidades\n(m)", font=fontTEXTcoll).grid(row=0, column=0, sticky='nsew', padx=(10,0), pady=(30,20))

Entry_Profundidad_inicial = ctk.CTkEntry(container5_3_1_1, font=fontTEXTcoll, height=10)
Entry_Profundidad_inicial.grid(row=0, column=1, sticky='nsew', pady=(50,20))

ctk.CTkLabel(container5_3_1_1, text="-", font=fontTEXTcoll).grid(row=0, column=2, sticky='nsew', pady=(50,20))

Entry_Profundidad_final = ctk.CTkEntry(container5_3_1_1, font=fontTEXTcoll, height=10)
Entry_Profundidad_final.grid(row=0, column=3, sticky='nsew', padx=(0,10), pady=(50,20))

container5_3_1_2 = ctk.CTkFrame(container5_3_1)
container5_3_1_2.grid(row=1, column=0, sticky='nsew', padx=(10,5))
container5_3_1_2.grid_rowconfigure(0, weight=1)
container5_3_1_2.grid_columnconfigure(0, weight=3)
container5_3_1_2.grid_columnconfigure(1, weight=2)
container5_3_1_2.grid_columnconfigure(2, weight=1)

LabelLE = ctk.CTkLabel(container5_3_1_2, text="LE", font=fontTEXTcoll)
LabelLE.grid(row=0, column=0, sticky='nsew')
EntryLE = ctk.CTkEntry(container5_3_1_2, font=fontTEXTcoll)
EntryLE.insert(0, "0")
EntryLE.grid(row=0, column=1, sticky='nsew')
LabelLE_unidades = ctk.CTkLabel(container5_3_1_2, text="m", font=fontTEXTcoll)
LabelLE_unidades.grid(row=0, column=2, sticky='nsew')

container5_3_1_3 = ctk.CTkFrame(container5_3_1)
container5_3_1_3.grid(row=1, column=1, sticky='nsew', padx=(5,10))
container5_3_1_3.grid_rowconfigure(0, weight=1)
container5_3_1_3.grid_columnconfigure(0, weight=3)
container5_3_1_3.grid_columnconfigure(1, weight=2)
container5_3_1_3.grid_columnconfigure(2, weight=1)

LabelLR = ctk.CTkLabel(container5_3_1_3, text="LR", font=fontTEXTcoll)
LabelLR.grid(row=0, column=0, sticky='nsew')
EntryLR = ctk.CTkEntry(container5_3_1_3, font=fontTEXTcoll)
EntryLR.insert(0, "5")
EntryLR.grid(row=0, column=1, sticky='nsew')
LabelLR_unidades = ctk.CTkLabel(container5_3_1_3, text="m", font=fontTEXTcoll)
LabelLR_unidades.grid(row=0, column=2, sticky='nsew')

ctk.CTkButton(container5_3_1, text="Regresar", font=fontTEXTcoll, command=lambda: [detener_conexion_puerto(), raise_frame(Menup)]).grid(row=2, column=0, sticky='nsew', pady=(40,10))

container5_4 = ctk.CTkFrame(container5)
container5_4.grid(row=3, column=1, sticky='nsew', padx=(10,20), pady=20)
container5_4.grid_rowconfigure(0, weight=1)
container5_4.grid_columnconfigure(0, weight=1)

container5_4_0 = ctk.CTkFrame(container5)
container5_4_0.grid(row=2, column=1, sticky='nsew', padx=(10,20), pady=10)
container5_4_0.grid_rowconfigure(0, weight=1)
container5_4_0.grid_rowconfigure(1, weight=1)
container5_4_0.grid_rowconfigure(0, weight=1)
container5_4_0.grid_columnconfigure(0, weight=1)

ctk.CTkLabel(container5_4_0, text="Parámetros del Martillo", font = fontSUBcoll).grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

container5_4_1 = ctk.CTkFrame(container5_4)
container5_4_1.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)
container5_4_1.grid_rowconfigure(0, weight=1)
container5_4_1.grid_columnconfigure(0, weight=1)

container5_4_1_1 = ctk.CTkFrame(container5_4_1)
container5_4_1_1.grid(row=0, column=0, sticky='nsew', padx=10, pady=(60,30))
container5_4_1_1.grid_rowconfigure(0, weight=1)
container5_4_1_1.grid_rowconfigure(1, weight=1)
container5_4_1_1.grid_rowconfigure(2, weight=1)
container5_4_1_1.grid_rowconfigure(3, weight=1)
container5_4_1_1.grid_columnconfigure(0, weight=2)
container5_4_1_1.grid_columnconfigure(1, weight=2)
container5_4_1_1.grid_columnconfigure(2, weight=1)
container5_4_1_1.grid_columnconfigure(3, weight=3)

Label_Masa = ctk.CTkLabel(container5_4_1_1, text="Masa", font=fontTEXTcoll).grid(row=1, column=0, sticky='nsew', pady=(0,10))
Entry_masa = ctk.CTkEntry(container5_4_1_1, font=fontTEXTcoll)
Entry_masa.grid(row=1, column=1, sticky='nsew', pady=(0,10))
Entry_masa.insert(0, "63.5")
Label_Masa_unidades = ctk.CTkLabel(container5_4_1_1, text='kg', font=fontTEXTcoll).grid(row=1, column=2, sticky='nsew', pady=(0,10))

Label_Altura = ctk.CTkLabel(container5_4_1_1, text="Altura", font=fontTEXTcoll).grid(row=2, column=0, sticky='nsew', pady=(10,0))
Entry_altura = ctk.CTkEntry(container5_4_1_1, font=fontTEXTcoll)
Entry_altura.grid(row=2, column=1, sticky='nsew', pady=(10,0))
Entry_altura.insert(0, "0.76")
Label_Altura_unidades = ctk.CTkLabel(container5_4_1_1, text="m", font=fontTEXTcoll).grid(row=2, column=2, sticky='nsew', pady=(10,0))

Boton_calcular_energia = ctk.CTkButton(container5_4_1_1, text="Calcular Energía", font=fontTEXTcoll, command=lambda:calcular()).grid(row=1, column=3, rowspan=2, sticky='nsew', padx=10)

container5_4_1_2 = ctk.CTkFrame(container5_4_1)
container5_4_1_2.grid(row=1, column=0, sticky='nsew', padx=10, pady=(30,60))
container5_4_1_2.grid_rowconfigure(0, weight=1)
container5_4_1_2.grid_rowconfigure(1, weight=1)
container5_4_1_2.grid_rowconfigure(2, weight=1)
container5_4_1_2.grid_columnconfigure(0, weight=1)
container5_4_1_2.grid_columnconfigure(1, weight=1)
container5_4_1_2.grid_columnconfigure(2, weight=1)

Label_Energia = ctk.CTkLabel(container5_4_1_2, text="Energia", font=fontTEXTcoll).grid(row=1, column=0, sticky='nsew', padx=(10,0), pady=10)
Label_Energia_valor = ctk.CTkLabel(container5_4_1_2, text="473", font=fontTEXTcoll)
Label_Energia_valor.grid(row=1, column=1, sticky='nsew', pady=10)
Label_Energia_unidades = ctk.CTkLabel(container5_4_1_2, text="J", font=fontTEXTcoll).grid(row=1, column=2, sticky='nsew', padx=(0,10), pady=10)

def calcular():
    global Entry_masa, Entry_altura, producto, Label_Energia_valor
    producto = int(float(Entry_masa.get())* float(Entry_altura.get())*9.81)
    Label_Energia_valor.configure(text=str(producto))

container5_5 = ctk.CTkFrame(container5)
container5_5.grid(row=1, column=2, rowspan=3, sticky='nsew', padx=(10,20), pady=20)
container5_5.grid_rowconfigure(0, weight=1)
container5_5.grid_columnconfigure(0, weight=1)

container5_5_0 = ctk.CTkFrame(container5)
container5_5_0.grid(row=0, column=2, sticky='nsew', padx=(10,20), pady=10)
container5_5_0.grid_rowconfigure(0, weight=1)
container5_5_0.grid_rowconfigure(1, weight=1)
container5_5_0.grid_rowconfigure(2, weight=1)
container5_5_0.grid_columnconfigure(0, weight=1)

Label_titulo_5 = ctk.CTkLabel(container5_5_0, text="Parámetros de muestreo", font=fontSUBcoll).grid(row=1, column=0, sticky='nsew', padx=10, pady=10)

container5_5_1 = ctk.CTkFrame(container5_5)
container5_5_1.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

container5_5_1.grid_rowconfigure(0, weight=1)
container5_5_1.grid_rowconfigure(1, weight=4)
container5_5_1.grid_rowconfigure(2, weight=4)
container5_5_1.grid_columnconfigure(0, weight=1)
container5_5_1.grid_columnconfigure(1, weight=1)

ctk.CTkLabel(container5_5_1, text='Frecuencia de Muestreo', font=fontTEXTcoll).grid(row=0, column=0, columnspan=2, sticky='nsew', padx=20, pady=20)

container5_5_1_1 = ctk.CTkFrame(container5_5_1)
container5_5_1_1.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=10)
container5_5_1_1.grid_rowconfigure(0, weight=1)
container5_5_1_1.grid_rowconfigure(1, weight=1)
container5_5_1_1.grid_columnconfigure(0, weight=5)
container5_5_1_1.grid_columnconfigure(1, weight=1)
container5_5_1_1.grid_columnconfigure(2, weight=5)
container5_5_1_1.grid_columnconfigure(3, weight=1)

def mod_frecuencia_muestreo(n):
    global frecuencia_muestreo
    frecuencia_muestreo.append(n)

def colorear_botones(n):
    for termino in dic_botones_frecuencia:
        if termino == str(n):
            dic_botones_frecuencia[termino].select()
        else:
            dic_botones_frecuencia[termino].deselect()

B_50 = ctk.CTkButton(container5_5_1_1, text="50khz", command=lambda:[mod_frecuencia_muestreo(50), colorear_botones(50)], font=fontTEXTcoll)
B_50.grid(row=0, column=0, padx=(20,10), pady=(20,10), sticky='nsew')
B_50_radio = ctk.CTkRadioButton(container5_5_1_1, text ="", width= 20)
B_50_radio.grid(row=0, column=1, sticky = 'nswe')
B_100 = ctk.CTkButton(container5_5_1_1, text="100khz", command=lambda:[mod_frecuencia_muestreo(100), colorear_botones(100)], font=fontTEXTcoll)
B_100.grid(row=0, column=2, padx=(10,20), pady=(20,10), sticky='nsew')
B_100_radio = ctk.CTkRadioButton(container5_5_1_1, text ="", width= 20)
B_100_radio.grid(row=0, column=3, sticky = 'nswe')
B_150 = ctk.CTkButton(container5_5_1_1, text="150khz", command=lambda:[mod_frecuencia_muestreo(150), colorear_botones(150)], font=fontTEXTcoll)
B_150.grid(row=1, column=0, padx=(20,10), pady=(10,20), sticky='nsew')
B_150_radio = ctk.CTkRadioButton(container5_5_1_1, text ="", width= 20)
B_150_radio.grid(row=1, column=1, sticky = 'nswe')
B_200 = ctk.CTkButton(container5_5_1_1, text="200khz", command=lambda:[mod_frecuencia_muestreo(200), colorear_botones(200)], font=fontTEXTcoll)
B_200.grid(row=1, column=2, padx=(10,20), pady=(10,20), sticky='nsew')
B_200_radio = ctk.CTkRadioButton(container5_5_1_1, text ="", width= 20)
B_200_radio.grid(row=1, column=3, sticky = 'nswe')

dic_botones_frecuencia = {'50':B_50_radio, '100':B_100_radio, '150':B_150_radio, '200':B_200_radio}

B_50.invoke()


container5_5_1_2 = ctk.CTkFrame(container5_5_1)
container5_5_1_2.grid(row=2, column=0, columnspan=2, sticky='nsew', padx =10, pady=10)

container5_5_1_2.grid_rowconfigure(0, weight=4)
container5_5_1_2.grid_rowconfigure(1, weight=4)
container5_5_1_2.grid_rowconfigure(2, weight=1)
container5_5_1_2.grid_rowconfigure(3, weight=1)
container5_5_1_2.grid_rowconfigure(4, weight=2)
container5_5_1_2.grid_rowconfigure(5, weight=4)
container5_5_1_2.grid_columnconfigure(0, weight=3)
container5_5_1_2.grid_columnconfigure(1, weight=2)
container5_5_1_2.grid_columnconfigure(2, weight=1)

ctk.CTkLabel(container5_5_1_2, text="Tiempo de \nmuestreo:", font=fontTEXTcoll).grid(row=0, column=0, sticky='nsew', pady=(40,20))
Entry_tiempo_muestreo = ctk.CTkEntry(container5_5_1_2, font=fontTEXTcoll)
Entry_tiempo_muestreo.grid(row=0, column=1, sticky='nsew', pady=(40,20))
Entry_tiempo_muestreo.insert(0, "100")
ctk.CTkLabel(container5_5_1_2, text='ms', font=fontTEXTcoll).grid(row=0, column=2, sticky='nsew', pady=(40,20), padx=(0,10))

ctk.CTkLabel(container5_5_1_2, text="Tiempo de \nretardo", font=fontTEXTcoll).grid(row=1, column=0, sticky='nsew', pady=(20,80))
Entry_tiempo_Retardo = ctk.CTkEntry(container5_5_1_2, font=fontTEXTcoll)
Entry_tiempo_Retardo.grid(row=1, column=1, sticky='nsew', pady=(20,80))
Entry_tiempo_Retardo.insert(0, "10")
ctk.CTkLabel(container5_5_1_2, text='ms', font=fontTEXTcoll).grid(row=1, column=2, sticky='nsew', pady=(20,80), padx=(0,10))

ctk.CTkButton(container5_5_1_2, text= "Seleccionar ruta \nde guardado", font=fontTEXTcoll, command=lambda: [escoger_ruta_guardado()]).grid(row=2, column=1, columnspan=2, sticky='nsew', padx=20, pady=(20,10))

entry_ruta_guardado = ctk.CTkEntry(container5_5_1_2, font=fontTEXTcoll)
entry_ruta_guardado.grid(row=3, column=1, columnspan=2, sticky='nsew', padx=20, pady=(10))



ctk.CTkButton(container5_5_1_2, text= "Siguiente", font=fontTEXTcoll, command=lambda: [mostrar_alertas()]).grid(row=4, column=1, columnspan=2, sticky='nsew', padx=20, pady=(10,200))

def escoger_ruta_guardado():
    global ruta_guardado
    ruta_guardado = filedialog.askdirectory(initialdir = "/", title = "Selecciona una carpeta")
    ruta_guardado += "/"
    entry_ruta_guardado.insert(0, ruta_guardado)


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
        limpiar_review()
        raise_frame(Review)
        crear_columna_muestreo()

def limpiar_review():
    global LIM_IZQ, LIM_DER, LIM_IZQ_Entry, LIM_DER_Entry, t1, t2, t3, t4, fig1, fig2, canvas1, canvas2
    modificar_datos_segundo_frame('arriba', "", "", "", "", "", "", "", "", "", "","")
    modificar_datos_segundo_frame('abajo', "", "", "", "", "", "", "", "", "", "","")
    LIM_IZQ.configure(text="")
    LIM_DER.configure(text="")
    LIM_IZQ_Entry.delete(0)
    LIM_DER_Entry.delete(0)
    # arriba
    fig1.clear()
    ax1 = fig1.add_subplot(111)
    t1, = ax1.plot(np.arange(1, 8001), np.zeros(8000))
    t2, = ax1.plot(np.arange(1, 8001), np.zeros(8000))
    canvas1.draw()
    # abajo
    fig2.clear()
    ax2 = fig2.add_subplot(111)
    t3, = ax2.plot(np.arange(1, 8001), np.zeros(8000))
    t4, = ax2.plot(np.arange(1, 8001), np.zeros(8000))
    canvas2.draw()
    #clear_container('arriba')
    #clear_container('abajo')
    

def eliminar_columna_muestreo():
    global pile_area, pile_area_label, EM_valor_original, EM_label, ET_valor_original, ET_label, Button_num_grafica_arriba, Button_num_grafica_abajo, segemented_button, segemented_button2
    global segmented_button_callback1, segmented_button_callback2
    dic_ultima_grafica["abajo"] = 1
    dic_ultima_grafica["arriba"] = 1
    Button_num_grafica_arriba.configure(text=str(dic_ultima_grafica["arriba"]))
    Button_num_grafica_abajo.configure(text=str(dic_ultima_grafica["abajo"]))
    segemented_button2.set("DEFORMACIÓN")
    segmented_button_callback2("DEFORMACIÓN")
    segemented_button.set("ACELERACIÓN")
    segmented_button_callback1("ACELERACIÓN")
    

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
    global pile_area_label, EM_label, ET_label
    global numero_grafica_insertada, marca, L_T_Grafico, num_golpe, tipo_señal, bandera_grafica, matriz_data_archivos, Entry_Profundidad_inicial, Entry_Profundidad_final
    global Entry_altura, Entry_Area, Entry_masa, Entry_modulo_elasticidad
    matriz_data_archivos = []


    pile_area_label.configure(text=str(round(float(Entry_Area.get()),2)))
    EM_label.configure(text=str(round(float(Entry_modulo_elasticidad.get()),2)))
    ET_label.configure(text=str(round(int(float(Entry_masa.get())* float(Entry_altura.get())*9.81),2)))

    container1_3 = ctk.CTkFrame(container1)
    container1_3.grid(row=3, column=0, padx=20, pady=10, sticky='new')
    container1_3.grid_columnconfigure(0, weight=10)
    container1_3.grid_columnconfigure(1, weight=1)
    container1_3.grid_rowconfigure(0, weight=1)
    container1_3.grid_rowconfigure(1, weight=1)
    container1_3.grid_rowconfigure(2, weight=1)
    container1_3.grid_rowconfigure(3, weight=1)

    ctk.CTkLabel(container1_3, text="Total de Gráficas:", font=fontTEXTcoll).grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

    ctk.CTkLabel(container1_3, text="Frecuencia de muestreo:", font=fontTEXTcoll).grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
    ctk.CTkLabel(container1_3, text="Tiempo de muestreo:", font=fontTEXTcoll).grid(row=2, column=0, padx=10, pady=10, sticky='nsew')
    ctk.CTkLabel(container1_3, text="Tiempo de retardo:", font=fontTEXTcoll).grid(row=3, column=0, padx=10, pady=10, sticky='nsew')
    

    L_T_Grafico = ctk.CTkLabel(container1_3, text="0", font=fontTEXTcoll)
    L_T_Grafico.grid(row=0, column=1, padx=10, pady=10, sticky='ns')
    L_Frecuencia = ctk.CTkLabel(container1_3, text=str(frecuencia_muestreo[-1])+" khz", font=fontTEXTcoll)
    L_Frecuencia.grid(row=1, column=1, padx=10, pady=10, sticky='ns')
    L_T_Muestreo = ctk.CTkLabel(container1_3, text=Entry_tiempo_muestreo.get()+" ms", font=fontTEXTcoll)
    L_T_Muestreo.grid(row=2, column=1, padx=10, pady=10, sticky='ns')
    L_T_Retardo = ctk.CTkLabel(container1_3, text=Entry_tiempo_Retardo.get()+" ms", font=fontTEXTcoll)
    L_T_Retardo.grid(row=3, column=1, padx=10, pady=10, sticky='ns')
    matriz_data_archivos.append(str(Entry_Profundidad_inicial.get())+","+str(Entry_Profundidad_final.get()))
    orden_sensores2 = []
    orden_sensores2.append(str(orden_sensores[-1].replace("\n", ""))+str(frecuencia_muestreo[-1])+"|"+str(Entry_Area.get())+"|"+str(Entry_modulo_elasticidad.get())+"|"+str(int(float(Entry_masa.get())* float(Entry_altura.get())*9.81)))
    

    container3_5 = ctk.CTkFrame(container3)
    container3_5.grid(row=4, column=0, sticky='nsew', padx=(20))
    container3_5.grid_rowconfigure(0, weight=1)
    container3_5.grid_columnconfigure(0, weight=1)
    container3_5.grid_columnconfigure(1, weight=1)
    
    Boton_play = ctk.CTkButton(container3_5, text="►", font=('Times', 20), command=lambda:[cambio_boton_play()])
    Boton_play.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=(30), pady=(30,30))

    def graficas_tiempo_real(num):
        global bandera_grafica, L_T_Grafico, num_golpe, matriz_data_archivos
        global marca
        
        print(marca, bandera_grafica)
        
        def graficar():
            global bandera_grafica, marca, L_T_Grafico, num_golpe
            while bandera_grafica and marca:
                #time.sleep(0.2)
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
                bandera3 = 0

                string = ""
                vector = []
                acumulado = ""

                while ((bandera3 == 0 ) and (señal_continua == True)):
                    
                    print("recibiendo")
                    cata = socket_tcp.recv(10000).decode("cp437")
                   
                    if cata != "":
                        acumulado += cata


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

            #time.sleep(.2)

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
                for i in range(1,len(matriz_data_archivos)):
                    string += "INICIO_ARCHIVO\n"
                    string += "ARCHIVO:"+str(i)+"\n"
                    string += orden_sensores2[-1]+ "\n"
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
        Boton_stop = ctk.CTkButton(container3_5, text="STOP", font=('Times', 20), command=lambda:[cambio_boton_stop()])
        #Boton_pausa.grid(row=0, column=0, sticky='nsew', padx=(30,10), pady=(150,10))
        Boton_stop.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=(30), pady=(30,30))
        
        inicio_secuencia_grabado()

    def cambio_boton_pausa():
        global señal_continua, tipo_señal
        señal_continua = False
        tipo_señal = "F"
        eliminar_botones()

        socket_tcp.send("F".encode('utf-8'))
        #time.sleep(0.2)
        conexion.close()

        Boton_play = Button(container3_5, text="►", font=('Times', 20), command=lambda:[cambio_boton_play()])
        Boton_play.grid(row=0, column=0, columnspan=2, sticky='nsew', padx=(30), pady=(150,10))
    
    def cambio_boton_stop():
        mandar_alerta_boton_stop()


Num_golpes = []
Num_golpes_modificado = []

container6_1_1 = ""

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

boton_exportar_pdf_excel = ""

def create_toplevel_export():
    global Num_golpes, Num_golpes_modificado, filas, contador_fila, fila_grabada, filas, contador_fila, ruta, boton_exportar_pdf_excel
    export_frame = ctk.CTkToplevel()
    export_frame.resizable(False, False) 
    export_frame.grab_set()
    export_frame.focus()
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
    boton_exportar_pdf_excel = ctk.CTkButton(container6_2, text="Exportar \nPDF y Excel", command=lambda: [mostrar_alertas_exportar()])
    boton_exportar_pdf_excel.grid(row=0, column=3, sticky='nsew', padx=(10), pady=10)

    filas = []
    contador_fila = 1
    fila_grabada = []

    Num_golpes = []
    Num_golpes_modificado = []

    preparaciones_exportar(label_cantidad_golpes, label_inicio, label_final)

    for i in range(4):
        Insertar_Fila(container6_1_1)

    def mostrar_alertas_exportar():
        global filas, Num_golpes, Num_golpes_modificado, matriz_data_archivos, ruta_guardado_pdf, boton_exportar_pdf_excel
        contador = 0
        longitudes = matriz_data_archivos[0][12:].split(",")
        for fila in filas:
            for i in range(len(fila)):
                if str(fila[i].get()) != "":
                    contador += 1
        print(filas[0][0].get(), filas[-1][0].get())
        print("las longitudes son:", longitudes)
        if contador  != len(filas)*len(filas[0]):
            MessageBox.showerror("Error", "Inserte todos los datos") 
        elif str(float(filas[0][0].get())) != str(float(longitudes[1])) or str(float(filas[-1][0].get())) != str(float(longitudes[0])):
            MessageBox.showerror("Error", "Las longitudes iniciales y finales no coinciden")
        elif sum(Num_golpes) != len(matriz_data_archivos)-1:
            MessageBox.showerror("Error", "La cantidad de golpes insertada no concuerda con la del archivo")
        elif ruta_guardado_pdf == "":
            MessageBox.showerror("Error", "Seleccione una ruta de guardado")
        else:
            boton_exportar_pdf_excel.configure(state='disable')
            Calcular_Promedios()
            boton_exportar_pdf_excel.configure(state='enable')


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
    
    print("las unidades de la gráfica ", j)
    print(matriz_data_archivos[j][0].split("|"))
    print(matriz_data_archivos[j][1].split("|"))
    print(matriz_data_archivos[j][-2].split("|"))

    for index,linea in enumerate(matriz_data_archivos[j]):
        linea = linea.split("|")
        if index > 0 and index < len(matriz_data_archivos[j])-1:
            segundos.append(float(linea[0])/1000)
            for i in range(4):
                #dic_orden_sensores2[orden[i]].append(float(linea[i+1])*dic_factor_conversion_producto[orden[i]]+dic_factor_conversion_suma[orden[i]])
                dic_orden_sensores2[orden[i]].append(float(linea[i+1]))
        else:
            pass
          
    frecuencia = int(frecuencia_muestreo[-1])
    for i in range(4):
        lugar = int(orden[i])
        if ((lugar== 1)) or (lugar == 2):
            #for datos in dic_orden_sensores2[orden[i]]:
            #for datos in cuentas_a_aceleracion(dic_orden_sensores2[orden[i]],frecuencia):
            for datos in filtro_acelerometro(cuentas_a_aceleracion2(dic_orden_sensores2[orden[i]],frecuencia),frecuencia,lugar):
                dic_orden_sensores[orden[i]].append(datos)
        elif (lugar!=0):
            #for datos in dic_orden_sensores2[orden[i]]:  
            #for datos in cuentas_a_deformacion(dic_orden_sensores2[orden[i]],frecuencia):  
            for datos in filtro_deformimetro(cuentas_a_deformacion2(dic_orden_sensores2[orden[i]],frecuencia),frecuencia,lugar):              
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
        print("LA FUERZA EN ", j, "ES:", F[20])
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

    segundos_grafica = []
    Fuerzas_impedancia_maxima_grafica = []
    Velocidades_impedancia_maxima_grafica = []
    for i in range(len(segundos)):
        if segundos[i] > 4.9 and segundos[i] < 40.1: 
            segundos_grafica.append(segundos[i])
            Fuerzas_impedancia_maxima_grafica.append(Fuerzas_impedancia_maxima[i])
            Velocidades_impedancia_maxima_grafica.append(Velocidades_impedancia_maxima[i])

    t1, = a.plot(segundos_grafica, Fuerzas_impedancia_maxima_grafica, label= "F")
    t2, = a.plot(segundos_grafica, Velocidades_impedancia_maxima_grafica, label=str(round(Z, 2))+"*V")
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
    about_frame.resizable(False, False) 
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
    archivos = filedialog.askopenfilenames(initialdir = "/", title = "Seleccione los archivos a convertir")
    #ruta_guardado += "/"
    return archivos

def leer_data_cabecera(ruta, identificador):
    with open(ruta) as file:
        filas = file.readlines()
    for index, fila in enumerate(filas):
        fila = fila.replace("\n", "").split(identificador)
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
    
    ar = round(float(filas[ar_pos].replace("\n", "").split(identificador)[1]),2)
    em = round(float(filas[em_pos].replace("\n", "").split(identificador)[1]),2)
    efv = float(filas[efv_pos].replace("\n", "").split(identificador)[1])
    etr = float(filas[etr_pos].replace("\n", "").split(identificador)[1])
    et = round((efv/etr)*100,2)

    frecuencia = round(1/float(filas[frecuencia_post].replace("\n", "").split(identificador)[1])/1000)

    fila_orden = filas[frecuencia_post-3].replace("\n", "").split(identificador)
    print(fila_orden)
    orden = [fila_orden[2].split("@")[0], fila_orden[3].split("@")[0]]
    try:
        orden.append(fila_orden[4].split("@")[0])
    except:
        orden.append("0")

    try:
        orden.append(fila_orden[5].split("@")[0])
    except:
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
def lectura_data(frecuencia_post, filas, identificador):
    string_data = ""
    for i in range(frecuencia_post-1, len(filas)):
        fila = filas[i].replace("\n", "").split(identificador)
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

def crear_ctn(profundidad, ruta_guardado_combinado, identificador):
    texto = ""
    for index in range(len(ruta_guardado_combinado)):
        if index == 0:
            texto += "profundidad:"+profundidad
        frecuencia_post, filas, orden_string, frecuencia, ar, em, et = leer_data_cabecera(ruta_guardado_combinado[index], identificador)
        cabecera = orden_string+str(frecuencia)+"|"+str(ar)+"|"+str(em)+"|"+str(et)
        texto+="\nINICIO_ARCHIVO\nARCHIVO:"+str(index+1)+"\n"+cabecera+"\n"
        texto+=lectura_data(frecuencia_post, filas, identificador)
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

def boton_preparar(inicio, fin, identificador):
    global scrollable_frame, label_frecuencia, label_AR, label_EM, label_ET, ruta_guardado_combinado

    nombre = str(inicio) +","+str(fin)
    texto, frecuencia, ar, em, et = crear_ctn(nombre, ruta_combinados, identificador)

    label_frecuencia.configure(text=frecuencia)
    label_AR.configure(text=ar)
    label_EM.configure(text=em)
    label_ET.configure(text=et)

    with open(ruta_guardado_combinado+"\profundidad_"+str(inicio)+"-"+str(fin)+".ctn", "w") as file:
        file.write(texto)
    
    MessageBox.showinfo(message="Exportado con éxito", title="Éxito")

def escoger_ruta_combinado():
    global ruta_guardado_combinado, Entry_archivo_inicio, Entry_archivo_final, ruta_guardado_label_combinado
    ruta_guardado_combinado = filedialog.askdirectory(initialdir = "/", title = "Selecciona una carpeta")
    ruta_guardado_label_combinado.insert(0,ruta_guardado_combinado+"/profundidad_"+str(Entry_archivo_inicio.get())+"-"+str(Entry_archivo_final.get())+".ctn") 

def create_toplevel_preparar():
    global scrollable_frame, label_frecuencia, label_AR, label_EM, label_ET, Entry_archivo_final, Entry_archivo_inicio, ruta_guardado_label_combinado

    preparar_frame = ctk.CTkToplevel()

    preparar_frame.title("Preparar Datos")
    preparar_frame.resizable(False, False) 
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
    container8.grid_columnconfigure(2, weight=1)

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

    button_escoger_archivos = ctk.CTkButton(container8, text="Seleccionar archivos", font=fontTEXTcoll, command=lambda:[boton_escoger_archivos_combinar()])
    button_escoger_archivos.grid(row=2, column=0, sticky='nsew', padx=20, pady=(10,20))

    scrollable_frame = ctk.CTkTextbox(container8, width=150, height=200)
    scrollable_frame.grid(row=3, column=0, rowspan=3, sticky='nsew', padx=20, pady=(0,20))


    container8_1 = ctk.CTkFrame(container8)
    container8_1.grid(row=0, column=1, columnspan=2, rowspan=3, sticky='nsew', padx=(0,20), pady=20)
    container8_1.grid_rowconfigure(0, weight=1)
    container8_1.grid_rowconfigure(1, weight=1)
    container8_1.grid_rowconfigure(2, weight=1)
    container8_1.grid_rowconfigure(3, weight=1)
    container8_1.grid_columnconfigure(0, weight=1)
    container8_1.grid_columnconfigure(1, weight=1)

    container8_1_1 = ctk.CTkFrame(container8_1)
    container8_1_1.grid(row=0, column=0, sticky='nsew', padx=20, pady=(20,10))
    container8_1_1.grid_columnconfigure(0, weight=3)
    container8_1_1.grid_columnconfigure(1, weight=1)

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

    ctk.CTkLabel(container8, text="Separador del CSV:").grid(row=3, column=1, padx=20, pady=20)

    var_identificador = ctk.StringVar(value=",")
    boton_identificador = ctk.CTkSegmentedButton(container8, values=[",", ";"], variable=var_identificador)
    boton_identificador.grid(row=3, column=2, padx=20, pady=20)

    ctk.CTkButton(container8, text="Escoger Ruta Guardado", command=lambda:[escoger_ruta_combinado()]).grid(row=5, column=1, padx=20, pady=(20))

    ruta_guardado_label_combinado = ctk.CTkEntry(container8)
    ruta_guardado_label_combinado.grid(row=4, column=1, columnspan=2, sticky='nsew', padx=20, pady=10)

    ctk.CTkButton(container8, text="Unir", command=lambda:[boton_preparar(Entry_archivo_inicio.get(), Entry_archivo_final.get(), boton_identificador.get())]).grid(row=5, column=2, padx=20, pady=(20))



raise_frame(Menup)

root.mainloop()