# Contexto para próximas conversaciones con Codex

Esta carpeta concentra el contexto mínimo y operativo para continuar el desarrollo del proyecto **Payroll** sin tener que repetir roles, reglas de negocio, arquitectura ni criterios de trabajo en cada conversación.

## Cómo usar esta carpeta

Antes de modificar código, revisar en este orden:

1. [`01-rol-y-forma-de-trabajo.md`](./01-rol-y-forma-de-trabajo.md): rol esperado, idioma, cautelas y forma de responder.
2. [`02-proyecto-y-arquitectura.md`](./02-proyecto-y-arquitectura.md): estructura general del sistema y módulos principales.
3. [`03-dominio-nomina-chile.md`](./03-dominio-nomina-chile.md): reglas funcionales relevantes para nómina chilena.
4. [`04-estado-funcional-reciente.md`](./04-estado-funcional-reciente.md): cambios recientes y decisiones ya tomadas.
5. [`05-checklist-para-cambios.md`](./05-checklist-para-cambios.md): checklist obligatorio antes de entregar cambios.
6. [`06-comandos-utiles.md`](./06-comandos-utiles.md): comandos de revisión, validación y navegación del repo.

## Resumen ejecutivo

Payroll es un sistema SaaS de gestión de remuneraciones para Chile. El usuario espera que Codex actúe como experto fullstack, arquitectura de software y nómina chilena, con especial cuidado en no romper flujos existentes.

El foco reciente ha estado en:

- Proceso mensual de nómina.
- Modal/panel de movimientos mensuales.
- Cálculo de situación del mes desde ficha del trabajador.
- Liquidaciones y reportes PDF.
- UI de `nomina/calculo.html`, `nomina/movimientos.html`, ficha de trabajador y navegación.

## Principio clave

Si hay una regla de negocio de nómina chilena, **no improvisar sólo en frontend**. Preferir centralizar la regla en backend/servicio y hacer que UI consuma datos calculados o endpoints existentes.
