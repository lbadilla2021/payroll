# Dominio: nómina chilena

## Principios funcionales

- La nómina chilena se calcula normalmente sobre base mensual de 30 días para remuneraciones mensuales.
- Vacaciones no deben descontarse como ausencia para sueldo base si son pagadas.
- Licencias, permisos sin goce y días no cubiertos por contrato sí pueden afectar días trabajados y sueldo proporcional.
- No duplicar descuentos de días: si `dias_ausentes` ya consolida licencia, permisos y no contrato, el motor no debe volver a descontar esos componentes por separado.

## Situación del mes

La situación del mes se consolidó como regla backend.

Campos relevantes:

- `dias_permiso`
- `dias_no_contratado`
- `dias_licencia`
- `dias_ausentes`
- `dias_trabajados`

Regla general:

```text
dias_ausentes = dias_licencia + dias_permiso_sin_goce + dias_no_contratado
dias_trabajados = 30 - dias_ausentes
```

Aplicar topes para que días ausentes no excedan 30.

## Licencias

- Se obtienen desde la ficha del trabajador (`LicenciaMedica`).
- Se consideran días corridos intersectando el período de proceso.
- No deben ser editables en el movimiento mensual.

## Permisos

- Se obtienen desde ficha del trabajador (`FichaPermiso`).
- Sólo suman como ausencia si el tipo de permiso es **sin goce de sueldo**.
- El tipo de permiso tiene atributo `con_goce`; sólo considerar `con_goce == False` para días ausentes.
- Permisos con goce no deben afectar sueldo base ni días ausentes.

## Días no contrato

- Se calculan desde la fecha de contrato/ingreso del trabajador y/o finiquito.
- Ejemplo validado: si una persona ingresa el 16 de abril, los días no contrato son 15: días 1 al 15.
- Si hay finiquito dentro del mes, se consideran días posteriores al finiquito como no contrato.

## Sueldo base proporcional

En el motor, el sueldo base se calcula usando `dias_ausentes` consolidado:

```text
dias_trabajados = 30 - dias_ausentes
```

Luego:

- Sueldo mensual (`M`): `monto_sueldo * dias_trabajados / 30`.
- Sueldo diario (`D`): `monto_sueldo * dias_trabajados`.
- Sueldo por hora (`H`): `monto_sueldo * (dias_trabajados * horas_semana / dias_semana)`.
- Otros: monto completo.

## Total haberes

`total_haberes` no es lo mismo que sueldo base. Se compone de:

- Sueldo base proporcional.
- Horas extras.
- Gratificación.
- Haberes imponibles adicionales.
- Haberes no imponibles, incluyendo colación y movilización.
- Haberes exentos adicionales.

## Descuentos

Descuentos del trabajador incluyen, entre otros:

- AFP.
- Salud.
- Seguro de cesantía trabajador.
- Impuesto único.
- Otros descuentos.
- Préstamos.
- APV/cotización voluntaria si aplica.

En UI, si se muestra desglose, incluir **Otros descuentos** como remanente respecto de `total_descuentos` cuando no se tiene cada concepto individual persistido en el movimiento.
