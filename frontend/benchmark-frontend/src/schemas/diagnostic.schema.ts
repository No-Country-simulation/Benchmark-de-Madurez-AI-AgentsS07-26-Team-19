import { z } from 'zod'

export const SCALE_MIN = 1
export const SCALE_MAX = 5

export const ANSWER_VALUE_SCHEMA = z
  .number({ message: 'Selecciona una opción' })
  .int('El valor debe ser entero')
  .min(SCALE_MIN, 'El valor mínimo es 1')
  .max(SCALE_MAX, 'El valor máximo es 5')