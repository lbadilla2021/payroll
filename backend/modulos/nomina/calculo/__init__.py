# modulos/nomina/calculo/__init__.py
"""
Motor de cálculo de liquidaciones de remuneraciones — legislación chilena.

Módulos:
  motor.py              → Algoritmos puros (sin BD), totalmente testeables
  servicio_calculo.py   → Orquestador: carga datos BD → motor → persiste
  schemas_calculo.py    → Schemas Pydantic de entrada/salida
  endpoints_calculo.py  → Rutas FastAPI
"""
