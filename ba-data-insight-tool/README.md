# BA Data Insight Tool

[![CI](https://github.com/ALonsoHSolis/Autoamatizacion-1/actions/workflows/ci.yml/badge.svg)](https://github.com/ALonsoHSolis/Autoamatizacion-1/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red?logo=streamlit)
![pandas](https://img.shields.io/badge/pandas-2.2+-green?logo=pandas)

BA Data Insight Tool es una aplicación web en Streamlit para convertir archivos Excel o CSV en un análisis ejecutivo de negocio. Está pensada para equipos que reciben bases operativas, pagos, ventas, conciliaciones, registros de personas o datos financieros simples y necesitan entender rápidamente qué está pasando, dónde está el impacto y qué revisar antes de tomar decisiones.

La interfaz guía al usuario en un **wizard de 4 pasos** (Inicio → Cargar datos → Confirmar columnas → Resumen ejecutivo) con avance automático entre pasos, sobre un dark mode premium con tarjetas glassmorphism. El Resumen ejecutivo agrupa Calidad de datos, Análisis, Insights y Exportar como subtabs, en vez de pasos separados.

## ✨ Funcionalidades principales

| Módulo | Descripción |
|--------|-------------|
| 📊 **6 modos de análisis** | General, Ventas, Pagos, Conciliaciones, Registros, Financiero |
| 🔍 **Calidad de datos** | Scoring 0-100, 13 validaciones, RUT chileno, emails, fechas |
| 📈 **Forecasting** | Proyección lineal con banda de confianza 95%, slider de períodos |
| 🎯 **Pareto / ABC** | Clasificación automática A/B/C con gráfico acumulado |
| 💰 **vs Presupuesto** | Variance analysis: real vs esperado por categoría |
| 🔗 **Correlaciones** | Matriz Pearson para detectar relaciones entre variables |
| 🌊 **Waterfall** | Contribución de cada categoría al total |
| 🗂️ **Pivot dinámico** | Tabla cruzada con agregación configurable en app |
| 🤖 **IA opcional** | Insights ejecutivos con Claude (Anthropic API) |
| 📄 **Exportación** | PDF con gráficos · PowerPoint ejecutivo · Excel multi-pestaña |
| 🔗 **Google Sheets** | Carga directa desde URL pública sin descargar |
| 🧪 **30+ tests** | pytest con integración end-to-end sobre sample_data |

## Qué problema resuelve

Muchos procesos de negocio dependen de planillas con datos incompletos, formatos mixtos, duplicados, pagos pendientes o montos atípicos. Esta herramienta automatiza una primera revisión analítica para reducir trabajo manual, detectar riesgos y entregar una narrativa clara para stakeholders no técnicos.

## Para quién sirve

- Business Analysts y Data Analysts.
- Equipos de finanzas, operaciones, pagos y conciliaciones.
- Personas que trabajan con registros, beneficiarios, clientes o usuarios.
- Portafolios profesionales BA/Data que quieran mostrar análisis técnico con criterio de negocio.

## Funcionalidades

- Carga de archivos CSV, XLSX y XLS, o directo desde una URL pública de Google Sheets.
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
- Revisión de calidad de datos con severidad Alta, Media y Baja, y un score 0-100.
- Validación de RUT chileno.
- Detección de anomalías por media y desviación estándar.
- Forecasting con regresión lineal, banda de confianza del 95 % y proyección configurable.
- Análisis de Pareto / ABC con clasificación automática.
- Comparación Real vs Presupuesto por categoría.
- Tabla pivot dinámica configurable desde la app.
- Gráficos interactivos con Plotly.
- Insights ejecutivos locales, cuantificados y accionables.
- Capa opcional de IA con `ANTHROPIC_API_KEY`, enviando solo agregados y no el archivo completo.
- Exportación a Excel, PDF ejecutivo (con gráficos embebidos) y PowerPoint ejecutivo.
- Datos demo con errores intencionales.
- Tests con pytest.

## 🛠️ Stack tecnológico

| Categoría | Tecnologías |
|-----------|-------------|
| Core | Python 3.11+ · pandas · numpy |
| UI | Streamlit |
| Visualización | Plotly |
| Exports | reportlab · python-pptx · XlsxWriter · kaleido |
| IA | Anthropic Claude API (opcional) |
| Testing | pytest |
| CI/CD | GitHub Actions |

> También se apoya en `openpyxl` (lectura de Excel) y `python-dotenv` (variables de entorno).

## 📸 Capturas de pantalla

> 💡 *Para ver la app en acción, clona el repositorio y ejecuta `streamlit run app.py` con los archivos de `sample_data/`.*

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
2. En el paso **Inicio**, usa "Probar con datos de ejemplo" o "Cargar archivo" para subir uno de los demo.
3. La app avanza automáticamente a **Confirmar columnas**: revisa las columnas sugeridas y el tipo de análisis.
4. Presiona `Ejecutar análisis` — avanza automáticamente a **Resumen ejecutivo**.
5. Explora las subtabs: Resumen, Calidad de datos, Análisis, Insights y recomendaciones, Exportar.
6. Descarga Excel, PDF o PowerPoint desde la subtab Exportar.

## IA opcional

La app funciona sin IA. Para activar insights asistidos:

1. Crea un archivo `.env` o define una variable de entorno.
2. Agrega `ANTHROPIC_API_KEY=tu_api_key`.
3. Opcionalmente define `ANTHROPIC_MODEL=claude-sonnet-4-6`.
4. La app detecta la API key automáticamente y mejora los insights sin pasos adicionales.

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
│   ├── utils.py
│   └── ui/
│       ├── styles.py        # CSS dark-mode/glassmorphism inyectado en la app
│       ├── header.py        # Título dinámico por paso del wizard
│       ├── empty_state.py   # Onboarding (paso "Inicio")
│       ├── sidebar.py       # Wizard de 4 pasos, fuente de datos, columnas
│       ├── dashboard.py     # KPIs, alertas, calidad, insights (bloques reutilizables)
│       └── tabs.py          # Subtabs de "Resumen ejecutivo"
├── sample_data/
│   ├── ventas_mensuales.csv
│   ├── pagos_demo.csv
│   └── registros_demo.xlsx
└── tests/
    ├── test_wizard_flow.py
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
- Persistencia de análisis históricos.
- Autenticación para despliegue interno.
- Configuración avanzada de reglas de calidad.
- Integración con más fuentes de datos externas.

## 💼 Valor para BA/DA

Este proyecto demuestra capacidad para:
- Diseñar herramientas analíticas orientadas a usuarios de negocio
- Calcular KPIs, detectar anomalías y generar insights accionables  
- Implementar análisis avanzados: forecasting, clustering, correlaciones
- Exportar resultados en formatos ejecutivos (PDF, PowerPoint, Excel)
- Desarrollar con buenas prácticas: tests, CI/CD, documentación
