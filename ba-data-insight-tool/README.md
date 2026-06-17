# BA Data Insight Tool

[![CI](https://github.com/ALonsoHSolis/Autoamatizacion-1/actions/workflows/ci.yml/badge.svg)](https://github.com/ALonsoHSolis/Autoamatizacion-1/actions/workflows/ci.yml)

BA Data Insight Tool es una aplicación web en Streamlit para convertir archivos Excel o CSV en un análisis ejecutivo de negocio. Está pensada para equipos que reciben bases operativas, pagos, ventas, conciliaciones, registros de personas o datos financieros simples y necesitan entender rápidamente qué está pasando, dónde está el impacto y qué revisar antes de tomar decisiones.

## Qué problema resuelve

Muchos procesos de negocio dependen de planillas con datos incompletos, formatos mixtos, duplicados, pagos pendientes o montos atípicos. Esta herramienta automatiza una primera revisión analítica para reducir trabajo manual, detectar riesgos y entregar una narrativa clara para stakeholders no técnicos.

## Para quién sirve

- Business Analysts y Data Analysts.
- Equipos de finanzas, operaciones, pagos y conciliaciones.
- Personas que trabajan con registros, beneficiarios, clientes o usuarios.
- Portafolios profesionales BA/Data que quieran mostrar análisis técnico con criterio de negocio.

## Funcionalidades

- Carga de archivos CSV, XLSX y XLS.
- Selector de hoja cuando el Excel contiene múltiples hojas.
- Detección automática de columnas numéricas, categóricas, fechas, montos, estados, IDs, nombres, emails, teléfonos y RUT.
- Ajuste manual de columnas detectadas.
- Modos de análisis:
  - General.
  - Ventas.
  - Pagos.
  - Conciliaciones.
  - Registros/personas.
  - Financiero simple.
- KPIs generales y específicos por tipo de análisis.
- Revisión de calidad de datos con severidad Alta, Media y Baja.
- Validación de RUT chileno.
- Detección de anomalías por media y desviación estándar.
- Gráficos interactivos con Plotly.
- Insights ejecutivos locales, cuantificados y accionables.
- Capa opcional de IA con `ANTHROPIC_API_KEY`, enviando solo agregados y no el archivo completo.
- Exportación a Excel y PDF ejecutivo.
- Datos demo con errores intencionales.
- Tests con pytest.

## Stack tecnológico

- Python 3.11+
- Streamlit
- pandas
- numpy
- openpyxl
- plotly
- XlsxWriter
- reportlab
- python-dotenv
- anthropic opcional
- pytest

## Instalación

Linux/macOS:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Windows:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución local

```bash
streamlit run app.py
```

## Cómo usar archivos demo

La carpeta `sample_data/` incluye:

- `ventas_mensuales.csv`: ventas por fecha, categoría, clientes, ticket promedio y canal.
- `pagos_demo.csv`: pagos esperados, pagos realizados, estados y comprobantes.
- `registros_demo.xlsx`: base de personas con RUT, email, teléfono, fechas y observaciones.

Para probar:

1. Ejecuta `streamlit run app.py`.
2. Carga uno de los archivos demo.
3. Revisa las columnas sugeridas.
4. Elige el tipo de análisis correspondiente.
5. Presiona `Ejecutar análisis`.
6. Revisa KPIs, gráficos, calidad, anomalías e insights.
7. Descarga Excel o PDF.

## IA opcional

La app funciona sin IA. Para activar insights asistidos:

1. Crea un archivo `.env` o define una variable de entorno.
2. Agrega `ANTHROPIC_API_KEY=tu_api_key`.
3. Opcionalmente define `ANTHROPIC_MODEL=claude-sonnet-4-6`.
4. Marca `Mejorar insights con IA` en la barra lateral.

La app no envía el archivo completo a la IA. Solo envía un resumen agregado con KPIs, tendencias, anomalías, calidad y rankings.

## Tests

```bash
pytest
```

Los tests cubren:

- Detección de columnas.
- Validación de RUT chileno.
- Parseo de fechas ISO y formato local.
- Cálculo de KPIs.
- KPIs de pagos.
- Detección de anomalías.
- Perfilamiento y calidad de datos.

## Estructura del proyecto

```text
ba-data-insight-tool/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── src/
│   ├── ai_insights.py
│   ├── anomaly_detection.py
│   ├── business_insights.py
│   ├── charts.py
│   ├── data_loader.py
│   ├── data_profiler.py
│   ├── export_utils.py
│   ├── kpi_engine.py
│   └── utils.py
├── sample_data/
│   ├── ventas_mensuales.csv
│   ├── pagos_demo.csv
│   └── registros_demo.xlsx
└── tests/
    ├── test_anomaly_detection.py
    ├── test_data_profiler.py
    └── test_kpi_engine.py
```

## Cómo presentarlo en una entrevista BA/Data

Puedes presentar este proyecto como una herramienta interna para acelerar diagnóstico de datos operativos:

- Muestra cómo carga un archivo real o demo sin preparación previa.
- Explica la detección automática de columnas como una capa de reducción de fricción para usuarios no técnicos.
- Presenta KPIs y gráficos como puente entre análisis técnico y decisión de negocio.
- Destaca la calidad de datos: duplicados, nulos, RUT/email/teléfono, montos en cero o negativos.
- Usa las anomalías para explicar control operativo y priorización de revisión manual.
- Cierra con los insights ejecutivos: qué pasa, dónde pasa, cuánto impacta y qué acción tomar.
- Menciona que la IA es opcional y segura porque solo recibe agregados, no bases completas.

## Próximas mejoras

- Plantillas de reglas por industria o proceso.
- Comparación contra presupuesto o periodo externo.
- Persistencia de análisis históricos.
- Autenticación para despliegue interno.
- Reportes PDF con gráficos embebidos.
- Configuración avanzada de reglas de calidad.
- Integración con bases de datos o Google Sheets.
