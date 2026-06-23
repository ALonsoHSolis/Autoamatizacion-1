# Handoff: Rediseño visual de BA Data Insight Tool

> Pega este archivo (o todo el folder) en tu repo y dile a Claude Code:
> **"Lee `design_handoff_ba_redesign/CLAUDE_CODE.md` y aplica el rediseño."**

## Contexto del proyecto

App **Streamlit** en `ba-data-insight-tool/`. La UI se monta en `src/ui/`
(`styles.py`, `header.py`, `sidebar.py`, `dashboard.py`, `tabs.py`,
`empty_state.py`). El CSS se inyecta vía `inject_custom_css()` en `styles.py`
con variables CSS y clases reutilizables.

## Qué es este paquete

- `styles.py` — **reemplazo drop-in listo** de `src/ui/styles.py`. Misma firma
  `inject_custom_css()` y mismos nombres de clase. Es la entrega principal.
- `BA Insight Tool.dc.html` — maqueta HTML navegable de las 5 pantallas. Es
  **referencia visual**, NO código para copiar. Muestra el resultado esperado.
- Este `CLAUDE_CODE.md` — instrucciones e inventario de cambios.

## Tarea para Claude Code

1. **Reemplazar** `ba-data-insight-tool/src/ui/styles.py` por el `styles.py` de
   este folder. Es drop-in: no requiere cambios en otros archivos.
2. Correr la app (`streamlit run ...`) y verificar que las 5 pantallas
   (Inicio, Confirmar columnas, Resumen, Calidad, Insights/Exportar) respetan
   la nueva paleta y tipografía mostradas en `BA Insight Tool.dc.html`.
3. Aplicar los **ajustes finos opcionales** de la sección final si el usuario
   los quiere.

No reescribas la lógica de negocio (`kpi_engine.py`, `business_insights.py`,
etc.). Este rediseño es **solo capa visual**.

---

## Dirección de diseño (resumen)

Evolución del dark-mode glassmorphism actual hacia **premium fintech, limpio y
con foco en datos**:
- Acento azul **único** `#5B8DEF` — se elimina el degradado azul→cian→violeta.
- Tarjetas **planas** `#131A26` con borde fino `rgba(255,255,255,0.07)` — se
  reduce el glassmorphism y se quitan los glows/box-shadow azules.
- Tipografía: **Hanken Grotesk** (UI) + **JetBrains Mono** (cifras y etiquetas).
- Tabs con **subrayado** en vez de relleno.

## Design tokens (antes → ahora)

| Token              | Antes                        | Ahora        |
|--------------------|------------------------------|--------------|
| `--bg-main`        | `#050A13`                    | `#0A0E17`    |
| `--bg-sidebar`     | `#07101F`                    | `#0B1019`    |
| `--bg-panel`       | `#0B1324`                    | `#0F1420`    |
| `--bg-card`        | `rgba(15,23,42,.78)` (glass) | `#131A26` (plano) |
| `--primary-blue`   | `#2563EB`                    | `#5B8DEF`    |
| `--accent-cyan`    | `#38BDF8`                    | `#5B8DEF` (= acento) |
| `--accent-purple`  | `#7C3AED`                    | `#A78BFA`    |
| `--accent-green`   | `#22C55E`                    | `#45C08A`    |
| `--accent-amber`   | `#F59E0B`                    | `#E9A94A`    |
| `--accent-red`     | `#EF4444`                    | `#E8736B`    |
| `--text-main`      | `#F8FAFC`                    | `#EEF2F9`    |
| `--text-secondary` | `#CBD5E1`                    | `#9AA5B8`    |
| `--text-muted`     | `#64748B`                    | `#5E6A7E`    |
| `--border-soft`    | `rgba(148,163,184,.18)`      | `rgba(255,255,255,.07)` |
| `--gradient-brand` | degradado azul→cian→violeta  | **color plano** (acento) |

Tipografía / radios:
- Fuente UI: `'Hanken Grotesk', system-ui, sans-serif`
- Fuente datos: `'JetBrains Mono', monospace` (valores de `st.metric`, etiquetas)
- Radios: cards `14px`, tablas/inputs `12–13px`, pills `999px`, badges `999px`

## ⚠️ Punto de atención: `--gradient-brand`

Pasó de ser un degradado a un **color plano**. Si en `tabs.py`/`dashboard.py`
se usa como `background` de texto con `-webkit-background-clip: text`
(ej. `.hero-card .accent`), revisar que el texto siga visible. En el nuevo
`styles.py` ya se ajustó `.hero-card .accent` a color sólido; replica ese
patrón en cualquier otro uso de clip de texto.

## Clases preservadas (no requieren cambios en el markup)

`.card`, `.hero-card` (+ `.accent`, `.hero-subtitle`), `.icon-badge`,
`.step-card` (+ `.step-num/.step-title/.step-desc`), `.feature-card`,
`.detect-card`, `.alert-card` (+ `.card-title/.card-desc`), `.badge`
(+ `.badge-high/-medium/-low`), `.progress-complete`.

---

## Pantallas (referencia: `BA Insight Tool.dc.html`)

1. **Inicio** — hero con CTA "Cargar archivo" + ghost "Probar con datos de
   ejemplo"; grid "Cómo funciona" (4 step-cards) y "Qué obtendrás" (5
   feature-cards con icon-badge por color semántico).
2. **Confirmar columnas** — banda informativa de acento; grid de 4 detect-cards;
   pills de tipo de análisis; tabla preview (header mono en mayúsculas,
   números alineados a la derecha en mono); CTA "Ejecutar análisis".
3. **Resumen ejecutivo** — 5 KPI cards (valor en mono, delta verde/rojo);
   2 alert-cards con franja de severidad; gráfico de línea (área tenue de
   acento) + barras horizontales por categoría.
4. **Calidad de datos** — score circular SVG (anillo ámbar 78/100) + conteo por
   severidad; tabla de 13 validaciones con badges de severidad.
5. **Insights** — bloque "resumen ejecutivo" con fondo de acento tenue;
   hallazgos numerados (mono) con columnas Evidencia / Acción; lista de
   recomendaciones con checks verdes. Más pantalla **Exportar** (Excel/PDF/PPTX).

## Ajustes finos opcionales

- **Franja de severidad en alertas**: añadir `class="alert-card alert-high"`
  (o `-medium`/`-low`) en el markup; el CSS ya define el borde izquierdo.
- **Score circular de calidad**: renderizar como SVG vía
  `st.markdown(svg, unsafe_allow_html=True)`. (Pedir el snippet si se quiere
  idéntico a la maqueta.)
- **Fuentes offline**: el `styles.py` usa `<link>` a Google Fonts. Para
  despliegue sin internet, descargar Hanken Grotesk + JetBrains Mono y servirlas
  localmente con `@font-face`.
