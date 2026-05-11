# Estado funcional reciente

Este archivo resume decisiones y cambios recientes que deben respetarse.

## 1. `nomina/movimientos.html`

En el panel/modal de movimiento mensual:

- La sección **Situación del mes** muestra una fila con:
  1. Días permiso
  2. No Contrato
  3. Días licencia
  4. Días ausentes
  5. Días trabajados
- Esos campos son calculados/no editables.
- Ya no se muestra días vacaciones en esa fila.
- La UI no debe permitir edición manual de licencia, permisos, no contrato, ausentes o trabajados.

En el resultado de cálculo del panel:

- Deben existir secciones **Haberes** y **Descuentos**.
- En descuentos debe aparecer **Otros descuentos** después de **Impuesto único**.

## 2. `nomina/calculo.html`

En el panel de liquidación:

- La sección de haberes debe mostrar componentes, no sólo total:
  - Sueldo base
  - Gratificación
  - Horas extras
  - Movilización
  - Colación
  - Haberes / Otros haberes
  - Total haberes
- La sección debe llamarse **Descuentos**, no “Descuentos previsionales”.
- Debe incluir:
  - Descuento AFP
  - Descuento salud
  - Seguro cesantía
  - Impuesto único
  - Otros descuentos
  - Total descuentos
- El líquido del listado y el del modal deben provenir de la misma fuente lógica para evitar descuadres.

## 3. Ficha trabajador

En datos laborales del trabajador:

- El selector **Tipo de contrato** debe mostrar `descripcion`, no `nombre`, porque `/nomina/tipos-contrato` devuelve `descripcion`.
- El helper genérico de selects debe tener fallback robusto para `descripcion`, `nombre`, `nombre_completo`.

## 4. Reportes

Se creó grupo de menú **Reportes** entre **Nómina** y **Mantenedores**.

Ruta actual para liquidaciones PDF:

```text
frontend/nomina/reportes/liquidaciones.html
```

No volver a usar `frontend/nomina/reportes.html` salvo que se cree una página índice explícita.

La pantalla de reporte debe:

- Mostrar modal antes de generar.
- Permitir seleccionar un trabajador o **Todos los trabajadores**.
- Permitir seleccionar año y mes.
- Generar liquidaciones imprimibles/PDF con formato estándar:
  - Datos empresa.
  - Datos trabajador.
  - Situación del mes.
  - Haberes.
  - Descuentos.
  - Resumen final con líquido a pagar.
  - Firma de conformidad.

## 5. Advertencia sobre previews

Se está usando `/nomina/calculo/movimiento/{id}/preview` para obtener desglose completo del cálculo en UI/reportes.

Tener presente:

- `preview` recalcula y hace rollback.
- Es útil para desglose completo.
- Para listados masivos puede implicar muchas llamadas; si se vuelve lento, evaluar backend dedicado para reportes o endpoint batch.
