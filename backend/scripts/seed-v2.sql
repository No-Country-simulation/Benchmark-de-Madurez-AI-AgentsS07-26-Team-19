-- ============================================================
-- SEED v2 — Benchmark de Madurez AI Agents
-- Uso: psql -U nlr -d nlr_diagnostic -f scripts/seed-v2.sql
-- Idempotente: re-ejecutar limpia y recarga sin duplicar filas.
-- ============================================================

BEGIN;

TRUNCATE public_dataset, question RESTART IDENTITY CASCADE;

-- 👁️ VISIBILITY
INSERT INTO question (dimension, question, description, type, options, weight, order_index, is_active) VALUES
('visibility', '¿Tu organización cuenta con una vista unificada de energía, refrigeración y cargas de trabajo en tiempo real?',
 'Mide si existe una fuente única de verdad sobre energía, cooling y workloads.',
 'scale', '{"1":"No existe","2":"Baja","3":"Parcial","4":"Alta","5":"Vista única integrada"}', 1.00, 1, TRUE),
('visibility', '¿Los datos de consumo eléctrico, temperatura y uso de CPU/GPU están en un mismo dashboard?',
 NULL, 'scale', '{"1":"Nunca","2":"Rara vez","3":"A veces","4":"Casi siempre","5":"Siempre"}', 1.00, 2, TRUE),
('visibility', '¿Un mismo responsable puede revisar energía, refrigeración y workloads sin saltar entre sistemas?',
 NULL, 'scale', '{"1":"Nadie","2":"Con esfuerzo","3":"Parcialmente","4":"Bastante","5":"Totalmente centralizado"}', 1.00, 3, TRUE);

-- 🔥 FRICTION
INSERT INTO question (dimension, question, description, type, options, weight, order_index, is_active) VALUES
('friction', '¿Conocen el punto exacto de la cadena (eléctrica, cooling o cómputo) donde se pierde capacidad?',
 NULL, 'scale', '{"1":"Total desconocimiento","2":"Vago","3":"Aproximado","4":"Conocido","5":"Aislado con precisión"}', 1.00, 4, TRUE),
('friction', '¿Saben cuánta capacidad está "atrapada" no servida por falta de coordinación entre capas?',
 NULL, 'scale', '{"1":"No se sabe","2":"Estimado","3":"Parcial","4":"Medido","5":"Cuantificado"}', 1.00, 5, TRUE),
('friction', '¿Se identifica si la pérdida es por energía física, refrigeración o carga no procesada?',
 NULL, 'scale', '{"1":"Confuso","2":"Poco claro","3":"A veces","4":"Mayormente","5":"Claro y atribuido"}', 1.00, 6, TRUE);

-- ⏱️ LATENCY
INSERT INTO question (dimension, question, description, type, options, weight, order_index, is_active) VALUES
('latency', '¿Qué tan rápido se ajusta la refrigeración/energía ante un aumento de workload?',
 NULL, 'scale', '{"1":"Horas, manual","2":"Lento","3":"A veces","4":"Rápido","5":"Minutos, automático"}', 1.00, 7, TRUE),
('latency', '¿El cambio de demanda se refleja en la operación de refrigeración en tiempo real?',
 NULL, 'scale', '{"1":"No","2":"Rara vez","3":"A veces","4":"Casi siempre","5":"Siempre"}', 1.00, 8, TRUE),
('latency', '¿Cuál es el tiempo típico entre un pico de carga y la acción correctiva coordinada?',
 NULL, 'scale', '{"1":"Días","2":"Horas","3":"Media hora","4":"Minutos","5":"Near-real-time"}', 1.00, 9, TRUE);

-- 📊 QUANTIFICATION
INSERT INTO question (dimension, question, description, type, options, weight, order_index, is_active) VALUES
('quantification', '¿Conoces la cifra exacta de cuánta capacidad pagada está sin producir resultados?',
 NULL, 'scale', '{"1":"No","2":"Estimación","3":"Parcial","4":"Medido","5":"Con precisión"}', 1.00, 10, TRUE),
('quantification', '¿Mides el costo/valor de la capacidad no usada por descoordinación?',
 NULL, 'scale', '{"1":"No se mide","2":"Rara vez","3":"A veces","4":"Casi siempre","5":"Siempre"}', 1.00, 11, TRUE),
('quantification', '¿Comparas tu capacidad perdida (stranded capacity) entre trimestres?',
 NULL, 'scale', '{"1":"Nunca","2":"Rara vez","3":"A veces","4":"Casi siempre","5":"Siempre"}', 1.00, 12, TRUE);

-- 🚧 BLOCKERS
INSERT INTO question (dimension, question, description, type, options, weight, order_index, is_active) VALUES
('blockers', '¿Hay un dueño claro (owner) responsable de la capacidad total del data center?',
 NULL, 'scale', '{"1":"No","2":"Sin dueño claro","3":"Parcial","4":"Consolidado","5":"Owner definido"}', 1.00, 13, TRUE),
('blockers', '¿Cuál es el principal obstáculo para coordinar energía, refrigeración y cómputo?',
 NULL, 'single_choice', '{"silo":"Silo entre equipos","datos":"Falta de datos","presupuesto":"Presupuesto","cultura":"Cultura"}', 1.00, 14, TRUE),
('blockers', '¿Tu presupuesto prioriza explícitamente resolver el stranded capacity?',
 NULL, 'scale', '{"1":"No","2":"Mínimo","3":"Parcial","4":"Considerable","5":"Prioridad"}', 1.00, 15, TRUE);

-- 📊 DATOS PÚBLICOS DE REFERENCIA (20 filas)
INSERT INTO public_dataset (source, source_type, visibility_score, friction_score, latency_score, quantification_score, blockers_score, overall_score, collected_at) VALUES
('nlr-2023', 'estudio', 55.00, 42.00, 38.00, 30.00, 58.00, 44.60, '2023-01-15'),
('nlr-2023', 'estudio', 62.00, 50.00, 45.00, 55.00, 60.00, 54.40, '2023-02-03'),
('nlr-2023', 'estudio', 48.00, 60.00, 52.00, 45.00, 50.00, 51.00, '2023-03-01'),
('nlr-2023', 'encuesta', 70.00, 55.00, 60.00, 58.00, 65.00, 61.60, '2023-04-12'),
('nlr-2023', 'encuesta', 35.00, 65.00, 70.00, 62.00, 45.00, 55.40, '2023-05-20'),
('nlr-2024', 'estudio', 75.00, 60.00, 68.00, 70.00, 60.00, 66.60, '2024-01-10'),
('nlr-2024', 'estudio', 80.00, 72.00, 75.00, 78.00, 66.00, 74.20, '2024-02-22'),
('nlr-2024', 'encuesta', 52.00, 48.00, 55.00, 50.00, 62.00, 53.40, '2024-03-09'),
('nlr-2024', 'encuesta', 88.00, 78.00, 82.00, 84.00, 70.00, 80.40, '2024-04-15'),
('nlr-2024', 'estudio', 40.00, 58.00, 46.00, 30.00, 55.00, 45.80, '2024-05-05'),
('nlr-2024', 'estudio', 65.00, 60.00, 58.00, 60.00, 52.00, 59.00, '2024-06-18'),
('nlr-2024', 'encuesta', 74.00, 66.00, 70.00, 68.00, 64.00, 68.40, '2024-07-02'),
('nlr-2025', 'estudio', 90.00, 80.00, 85.00, 82.00, 75.00, 82.40, '2025-01-11'),
('nlr-2025', 'estudio', 58.00, 62.00, 55.00, 52.00, 60.00, 57.40, '2025-02-14'),
('nlr-2025', 'encuesta', 68.00, 70.00, 66.00, 72.00, 58.00, 66.80, '2025-03-08'),
('nlr-2025', 'encuesta', 85.00, 76.00, 80.00, 74.00, 68.00, 76.60, '2025-04-19'),
('nlr-2025', 'estudio', 45.00, 50.00, 48.00, 56.00, 62.00, 52.20, '2025-05-27'),
('nlr-2025', 'estudio', 72.00, 64.00, 62.00, 66.00, 60.00, 64.80, '2025-06-03'),
('nlr-2025', 'encuesta', 78.00, 70.00, 72.00, 76.00, 68.00, 72.80, '2025-07-30'),
('nlr-2025', 'encuesta', 55.00, 53.00, 50.00, 48.00, 56.00, 52.40, '2025-08-12');

-- Confirmación
SELECT 'preguntas' AS seccion, COUNT(*)::text AS total FROM question
UNION ALL
SELECT 'public_dataset', COUNT(*)::text FROM public_dataset;

COMMIT;