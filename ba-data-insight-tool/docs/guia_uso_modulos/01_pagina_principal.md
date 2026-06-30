# Pagina principal

## Objetivo

Seleccionar el espacio de trabajo que se quiere abrir dentro de APP BA.

## Como usar

1. Ejecuta la aplicacion con `streamlit run app.py`.
2. En la pantalla inicial revisa las tarjetas disponibles.
3. Presiona `Entrar` en el modulo que quieres usar.
4. Una vez dentro, usa el selector superior para cambiar de espacio sin volver al inicio.

## Modulos disponibles

- BA Insight: modulo activo para analisis de datos.
- Treasury Tower: MVP de tesoreria, liquidez, conciliacion, informes y comunicacion.
- ReconciliationE2E: MVP en desarrollo para conciliacion end-to-end.
- Model of Costs: MVP enterprise de costeo y pricing.

## Resultado esperado

La app abre el modulo seleccionado y mantiene el espacio activo en `st.session_state`.
