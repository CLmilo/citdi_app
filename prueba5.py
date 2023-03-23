a = 3.0
a = round(float(a),2)

parte_entera = int(a)
parte_decimal = round(abs(a) - abs(int(a)),2)
if len(str(parte_decimal)) < 4:
    print(str(a)+"0")
else:
    print(str(a))