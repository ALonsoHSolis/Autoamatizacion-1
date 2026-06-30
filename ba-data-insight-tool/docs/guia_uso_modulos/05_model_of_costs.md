# Model of Costs

## Objetivo

Operar un MVP enterprise de costeo y pricing con dominio separado, motor financiero y UI ejecutiva.

## Secciones

1. `Inicio ejecutivo`: revisa KPIs base, issues de calidad y mapa enterprise.
2. `Proveedores`: consulta proveedores, paises, metodos, fees y SLA.
3. `Rutas wizard`: crea rutas draft con proveedor, pais origen/destino y metodo.
4. `Motor de costeo`: calcula y guarda simulaciones con costos, revenue, spread, impuestos, profit, margen, ROI y break-even.
5. `Simulador`: compara escenarios de volumen.
6. `Dashboard`: visualiza profit, margen promedio y break-even de simulaciones guardadas.
7. `Calidad`: revisa validaciones automaticas.
8. `Auditoria`: consulta eventos audit-like de la sesion.
9. `Versionado`: revisa versiones de rutas/reglas.
10. `Configuracion`: consulta reglas de pricing.
11. `Integraciones`: revisa interfaces futuras para Salesforce, SAP, Oracle, Webhooks y REST.

## Notas tecnicas

El motor financiero vive en `src/cost_jc/engine.py`.
La UI vive en `src/ui/cost_jc.py`.
La documentacion tecnica esta en `docs/cost_jc_architecture.md`.
