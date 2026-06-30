# Treasury Tower

## Objetivo

Gestionar liquidez, saldos, conciliacion diaria, informes y comunicacion operativa de tesoreria.

## Secciones

1. `Panel de liquidez`: carga saldos desde archivo o Google Sheets y revisa reservas minimas.
2. `Conciliacion diaria`: selecciona una fecha, detecta discrepancias y registra acciones correctivas.
3. `Informes`: genera informes en Excel, PDF o PowerPoint usando las exportaciones existentes.
4. `Comunicacion`: registra notas de coordinacion con proveedores o areas internas.

## Persistencia

Si no hay variables de entorno de base de datos, el modulo funciona en modo demo en memoria.

Para persistir en MySQL configura:

```env
TREASURY_DATABASE_URL=mysql+pymysql://ba_user:ba_password@localhost:3306/treasury
```

## Notas

El servidor MySQL debe estar instalado y la base creada antes de probar persistencia real.

