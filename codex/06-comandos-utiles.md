# Comandos útiles

## Búsqueda rápida

No usar `ls -R` ni `grep -R`. Usar `rg` y `find` acotado.

```bash
rg -n "texto" frontend backend -S
find . -maxdepth 3 -type f -name '*.html' -print
```

## Estado git

```bash
git status --short
git log --oneline -5
git diff --check
```

## Validar módulos JS embebidos en HTML

```bash
python3 - <<'PY'
from pathlib import Path
html = Path('frontend/nomina/reportes/liquidaciones.html').read_text()
start = html.index('<script type="module">') + len('<script type="module">')
end = html.index('</script>', start)
Path('/tmp/reportes-liquidaciones-module.js').write_text(html[start:end])
PY
node --check /tmp/reportes-liquidaciones-module.js
```

## Validar navegación

```bash
node --check frontend/static/js/nav.js
```

## Validar Python modificado

```bash
python3 -m py_compile backend/modulos/nomina/services_operacional.py backend/modulos/nomina/calculo/motor.py backend/modulos/nomina/calculo/servicio_calculo.py
```

Si los imports requieren configuración:

```bash
DATABASE_URL=postgresql://user:pass@localhost/db PYTHONPATH=backend python3 - <<'PY'
from modulos.nomina.services_operacional import _calcular_situacion_mes
from modulos.nomina.calculo.servicio_calculo import ServicioCalculo
print('imports ok')
PY
```

## Endpoints relevantes

- `GET /rrhh/trabajadores?size=500&solo_activos=true`
- `GET /rrhh/trabajadores/{id}`
- `GET /nomina/movimientos?anio=YYYY&mes=M`
- `GET /nomina/movimientos/{id}`
- `PATCH /nomina/movimientos/{id}`
- `POST /nomina/calculo/movimiento/{id}`
- `GET /nomina/calculo/movimiento/{id}/preview`
- `POST /nomina/calculo/empresa`
- `GET /nomina/empresa`
- `GET /nomina/tipos-contrato?size=200`
