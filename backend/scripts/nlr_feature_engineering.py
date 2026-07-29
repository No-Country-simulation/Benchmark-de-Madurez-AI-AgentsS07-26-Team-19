import os
import pandas as pd

## Seteo de dataset
if not os.path.exists("data/dataset.csv"):
    raise FileNotFoundError("No existe el archivo")


df = pd.read_csv("data/dataset.csv", sep=",", decimal=",")

for columna in df.columns:

    if columna == "Timestamp":
        continue

    df[columna] = pd.to_numeric(
        df[columna].astype(str).str.replace(",", "."),
        errors="coerce"
    )

    minimo = df[columna].min()
    maximo = df[columna].max()

    df[columna] = (
        ((df[columna] - minimo) / (maximo - minimo)) * 100
    ).round()


datos_normalizados = df

## Formula para obtener porcentil visibilidad cross layer
def calcular_visibilidad_cross_layer():
    columnas = ["Cooling", "Energy", "Power IT"]

    return round(datos_normalizados[columnas].mean().mean())

## Formula para obtener porcentil atribucion de friccion
def calcular_atribucion_friccion():
    cooling = datos_normalizados["Cooling"]
    power_it = datos_normalizados["Power IT"]

    friccion = abs(power_it - cooling)

    promedio_friccion = friccion.mean()

    return round(promedio_friccion)

## Formula para obtener porcentil latencia de coordinacion
def calcular_latencia_coordinacion():
    cooling = datos_normalizados["Cooling"].tolist()
    power_it = datos_normalizados["Power IT"].tolist()

    cambios_workload = 0
    cambios_coordinados = 0

    for i in range(len(datos_normalizados)-1):

        if cooling[i] == 0 or power_it[i] == 0:
            continue

        cambio_cooling = abs(
            (cooling[i+1] - cooling[i]) / cooling[i]
        ) * 100

        cambio_power = abs(
            (power_it[i+1] - power_it[i]) / power_it[i]
        ) * 100

        if cambio_power > 10:
            cambios_workload += 1

            if cambio_cooling > 10:
                cambios_coordinados += 1


    if cambios_workload == 0:
        return 0

    resultado = (cambios_coordinados / cambios_workload) * 100

    return round(resultado)

## Formula para obtener porcentil auto cuantificacion
def calcular_auto_cuantificacion():
    cooling = datos_normalizados["Cooling"].tolist()
    power_it = datos_normalizados["Power IT"].tolist()
    diferencias = []

    for i in range(len(datos_normalizados)):
        diferencia = abs(power_it[i] - cooling[i])
        diferencias.append(diferencia)

    promedio = sum(diferencias) / len(diferencias)

    total = 100 - promedio

    return round(total)

## Formula para obtener porcentil bloqueantes
def calcular_bloqueantes():
    cooling = datos_normalizados["Cooling"].tolist()
    power_it = datos_normalizados["Power IT"].tolist()
    diferencias = []
    
    for i in range(len(datos_normalizados)):
        if(abs(power_it[i] - cooling[i]) > 10):
            diferencias.append(1)
        else:
            diferencias.append(0)

    bloqueantes = (sum(diferencias) / len(diferencias)) * 100

    return round(bloqueantes)





    