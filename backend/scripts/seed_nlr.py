from nlr_feature_engineering import calcular_bloqueantes
from nlr_feature_engineering import calcular_auto_cuantificacion
from nlr_feature_engineering import calcular_latencia_coordinacion
from nlr_feature_engineering import calcular_atribucion_friccion
from nlr_feature_engineering import calcular_visibilidad_cross_layer

def scoring_dataset_public():
    try:
        visibilidad = calcular_visibilidad_cross_layer()
        atribucion = calcular_atribucion_friccion()
        latencia = calcular_latencia_coordinacion()
        cuantificacion = calcular_auto_cuantificacion()
        bloqueantes = calcular_bloqueantes()

        resultado = {
            "Visibilidad cross-layer": visibilidad,
            "Atribucion de friccion": atribucion,
            "Latencia de coordinacion": latencia,
            "Auto-cuantificacion": cuantificacion,
            "Bloqueantes": bloqueantes
        }

        return resultado

    except Exception as error:
        return {
            "error": True,
            "mensaje": str(error)
        }

print(scoring_dataset_public())






    