# Checklist para cambios

## Antes de modificar

- [ ] Revisar `git status --short`.
- [ ] Buscar `AGENTS.md`.
- [ ] Ubicar pantalla exacta solicitada; no asumir por nombre parecido.
- [ ] Buscar campos en frontend y backend con `rg`.
- [ ] Confirmar si el dato viene de movimiento persistido, preview de cálculo, ficha trabajador o catálogo.

## Durante implementación

- [ ] Si es regla de negocio, preferir backend/servicio.
- [ ] Si es sólo presentación, limitar cambio al frontend correspondiente.
- [ ] No duplicar lógica compleja de cálculo en UI salvo para desglose visual simple.
- [ ] Mantener campos calculados como read-only/disabled cuando corresponde.
- [ ] Cuidar nombres de campos reales (`descripcion` vs `nombre`).

## Antes de entregar

Ejecutar checks según archivos modificados.

Para HTML con script module:

```bash
python3 - <<'PY'
from pathlib import Path
html = Path('frontend/nomina/calculo.html').read_text()
start = html.index('<script type="module">') + len('<script type="module">')
end = html.index('</script>', start)
Path('/tmp/module.js').write_text(html[start:end])
PY
node --check /tmp/module.js
```

Para JS directo:

```bash
node --check frontend/static/js/nav.js
```

Para Python:

```bash
python3 -m py_compile <archivos.py>
```

Siempre:

```bash
git diff --check
```

## Commit y PR

- [ ] Hacer commit en la rama actual.
- [ ] Crear PR con `make_pr`.
- [ ] No terminar con cambios committeados sin PR.
- [ ] No crear PR sin commit.

## Respuesta final

Debe incluir:

- **Summary** con bullets y citas a archivos/líneas.
- **Testing** con comandos exactos y emoji de resultado.
