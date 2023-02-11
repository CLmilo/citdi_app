import xlsxwriter

def preparar_reporte_excel_detalle():
    ruta_reporte = "./reporte_excel"
    workbook = xlsxwriter.Workbook(ruta_reporte)
    worksheet = workbook.add_worksheet('Observaciones Implementadas')
    row = 1
    col = 0

    cell_format2 = workbook.add_format()
    cell_format2.set_align('center')
    cell_format2.set_align('vcenter')

    cell_format4 = workbook.add_format()
    cell_format4.set_align('center')
    cell_format4.set_align('vcenter')
    cell_format4.set_text_wrap()

    cell_format = workbook.add_format()
    cell_format.set_align('center')
    cell_format.set_align('vcenter')
    cell_format.set_font_color('white')
    cell_format.set_bold()
    cell_format.set_bg_color('#1F246D')

    cell_format3 = workbook.add_format()
    cell_format3.set_text_wrap()
    cell_format3.set_align('center')
    cell_format3.set_align('vcenter')
    cell_format3.set_font_color('white')
    cell_format3.set_bold()
    cell_format3.set_bg_color('#1F246D')



    for linea in resultado:
        for i in range(len(linea)):
            if i in [1,2,5]:
                worksheet.write(row, col + i , linea[i], cell_format4)
            else:
                worksheet.write(row, col + i , linea[i], cell_format2)
        row += 1

    
    columnas = ["Cod_Proyecto", "Titulo", "Titulo_Observacion Paterno", "Criticidad", "Estado_Recomendacion", "Unidad_Responsable", "Codigo_TeamCentral", "FECHA_CIERRE_OBS", "Auditor", "Supervisor"]
    
    
    worksheet.set_row(0,30)

    worksheet.set_column("A:A",15)
    worksheet.set_column("B:B",60)#
    worksheet.set_column("C:C",100)
    worksheet.set_column("D:D",20)
    worksheet.set_column("E:E",20)
    worksheet.set_column("F:F",40)#
    worksheet.set_column("G:G",10)
    worksheet.set_column("H:H",20)
    worksheet.set_column("I:I",30)
    worksheet.set_column("J:J",30)
    for i in range(len(columnas)):
        if i in [1,2,5]:
            worksheet.write(0, col + i ,columnas[i], cell_format3)
        else:
            worksheet.write(0, col + i ,columnas[i], cell_format)
    
    workbook.close()

preparar_reporte_excel_detalle()s



