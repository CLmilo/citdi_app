# import lib_platform

# username = lib_platform.username
# hostname = lib_platform.hostname

# print(username, hostname)
from tkinter import filedialog

def escoger_ruta_guardado():
    global ruta_guardado
    archivos = filedialog.askopenfilenames(initialdir = "/", title = "Seleccione los archivos a convertir")
    #ruta_guardado += "/"
    return archivos

archivos = escoger_ruta_guardado()
#print(archivos)

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
        pass
    dic_orden = {"S3":"3", "S4":"4", "S1":"3", "S2":"4", "A1":"1", "A2":"2", "A3":"1", "A4":"2"}
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
                nueva_fila = str(segundos) + "|" + str(V1) + "|" + str(V2) + "|" + str(V3) + "|"
            except:
                nueva_fila = str(segundos) + "|" + str(V1) + "|" + str(V2) + "|"
        string_data+=nueva_fila+"\n"
    return string_data

#archivos = ('E:/proyectos/Citdi/citdi_app/archivos_rpn/ejemplo1_part1.csv',)

def crear_ctn(profundidad):
    texto = ""
    for index in range(len(archivos)):
        if index == 0:
            texto += "profundidad:"+profundidad
        frecuencia_post, filas, orden_string, frecuencia, ar, em, et = leer_data_cabecera(archivos[0])
        cabecera = orden_string+str(frecuencia)+"|"+str(ar)+"|"+str(em)+"|"+str(et)
        texto+="\nINICIO_ARCHIVO\nARCHIVO:"+str(index+1)+"\n"+cabecera+"\n"
        texto+=lectura_data(frecuencia_post, filas)
        texto+="FIN_ARCHIVO"
    return texto

texto = crear_ctn("1,2")

with open("./nuevo_rpn"+"1,2.ctn", "w") as file:
    file.write(texto)



