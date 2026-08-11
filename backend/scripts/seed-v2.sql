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
-- Generadas con scripts/nlr_feature_engineering.py --window 10 desde el
-- dataset real de telemetría NLR HPC PUE (scripts/data/dataset.csv).
INSERT INTO public_dataset (source, source_type, visibility_score, friction_score, latency_score, quantification_score, blockers_score, overall_score, collected_at) VALUES
('nlr-hpc-pue', 'telemetria', 53.00, 53.00, 14.00, 47.00, 90.00, 51.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 44.00, 26.00, 67.00, 74.00, 80.00, 58.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 57.00, 47.00, 60.00, 53.00, 100.00, 63.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 61.00, 37.00, 67.00, 63.00, 90.00, 64.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 56.00, 42.00, 50.00, 58.00, 90.00, 59.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 40.00, 48.00, 33.00, 52.00, 80.00, 51.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 42.00, 30.00, 33.00, 70.00, 50.00, 45.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 52.00, 29.00, 33.00, 71.00, 50.00, 47.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 47.00, 39.00, 50.00, 61.00, 80.00, 55.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 43.00, 43.00, 50.00, 57.00, 90.00, 57.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 47.00, 45.00, 33.00, 55.00, 90.00, 54.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 55.00, 40.00, 43.00, 60.00, 80.00, 56.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 45.00, 27.00, 57.00, 73.00, 60.00, 52.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 37.00, 56.00, 25.00, 44.00, 80.00, 48.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 49.00, 29.00, 25.00, 71.00, 70.00, 49.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 36.00, 17.00, 50.00, 83.00, 70.00, 51.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 45.00, 43.00, 33.00, 57.00, 90.00, 54.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 41.00, 42.00, 33.00, 58.00, 90.00, 53.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 40.00, 42.00, 33.00, 58.00, 100.00, 55.00, '2016-06-12'),
('nlr-hpc-pue', 'telemetria', 33.00, 43.00, 50.00, 57.00, 80.00, 53.00, '2016-06-12');

-- Confirmación
SELECT 'preguntas' AS seccion, COUNT(*)::text AS total FROM question
UNION ALL
SELECT 'public_dataset', COUNT(*)::text FROM public_dataset;

COMMIT;