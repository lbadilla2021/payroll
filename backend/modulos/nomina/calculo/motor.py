"""
modulos/nomina/calculo/motor.py
================================
Motor de cálculo de remuneraciones — legislación laboral chilena.

Implementa en orden exacto el proceso de liquidación:
  1. Sueldo base proporcional (días trabajados)
  2. Horas extras (factor 1.5 normal, 2.0 nocturnas/festivas)
  3. Colación y movilización (exentas de imposiciones y tributación)
  4. Gratificación (Art. 50 CT — 25% imponible con tope 4.75 IMM)
  5. Otros haberes (fijos y variables del movimiento)
  6. Total imponible (base para cotizaciones previsionales)
  7. Cotización AFP (tasa_trabajador sobre imponible con tope 81.6 UF)
  8. SIS (Seguro de Invalidez y Sobrevivencia — cargo empleador)
  9. Cotización salud (7% con tope 60 UF o plan pactado Isapre)
 10. Seguro de Cesantía (trabajador y empleador, según tipo contrato)
 11. APV (rebaja o no de base tributaria según Art. 42 BIS)
 12. Base impuesto único (imponible - cotiz. previsionales - APV)
 13. Asignación de zona extrema (DL 889, regiones I, XI, XII, XV)
 14. Impuesto único 2ª categoría (tabla UTM progresiva)
 15. Cargas familiares (por tramos, exenta de todo)
 16. Descuentos varios (préstamos, anticipos, etc.)
 17. Líquido a pagar

Referencias legales:
  - Código del Trabajo Arts. 41, 42, 45, 50, 54, 55
  - DFL-1 Tributación: Art. 42 Nº1, 42 BIS Ley de la Renta
  - Ley 19.010 (indemnizaciones)
  - Ley 20.255 (Reforma Previsional — APV colectivo)
  - Ley 20.281 (ajuste sueldo base, semana corrida)
  - DL 3.500 (AFP)
  - DL 889 (asignación zona extrema)
  - Ley 19.728 (Seguro Cesantía — AFC)
"""

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP, ROUND_DOWN
from typing import Optional
import math


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES Y REDONDEO
# ─────────────────────────────────────────────────────────────────────────────

DIAS_MES = Decimal("30")
HORAS_DIA = Decimal("8")

# Factores horas extra (Art. 32 CT)
FACTOR_HH_NORMAL   = Decimal("1.5")
FACTOR_HH_NOCTURNA = Decimal("2.0")
FACTOR_HH_FESTIVA  = Decimal("2.0")

# Tasas Seguro de Cesantía (Ley 19.728)
TASA_SC_TRABAJADOR_INDEFINIDO  = Decimal("0.006")   # 0.6%
TASA_SC_EMPLEADOR_INDEFINIDO   = Decimal("0.024")   # 2.4%
TASA_SC_EMPLEADOR_PLAZO_FIJO   = Decimal("0.030")   # 3.0% (solo empleador)

# Topes imponibles (en UF — se convierten a pesos con UF del período)
TOPE_AFP_UF   = Decimal("81.6")
TOPE_SALUD_UF = Decimal("60.0")
TOPE_SC_UF    = Decimal("122.6")

# Gratificación Art. 50 CT
FACTOR_GRATIFICACION = Decimal("0.25")   # 25% de remuneración imponible
TOPE_GRATIFICACION_IMM = Decimal("4.75") # tope 4.75 IMM


def _redondear(valor: Decimal) -> Decimal:
    """Redondea a entero más cercano (pesos chilenos sin decimales)."""
    return valor.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _redondear_abajo(valor: Decimal) -> Decimal:
    """Trunca decimales (para algunos cálculos tributarios)."""
    return valor.quantize(Decimal("1"), rounding=ROUND_DOWN)


# ─────────────────────────────────────────────────────────────────────────────
# ESTRUCTURAS DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ParametrosPeriodo:
    """Valores del período (UTM, UF, IMM, topes, tasas)."""
    utm:                  Decimal
    uf:                   Decimal
    imm:                  Decimal
    tope_imponible_afp:   Decimal   # en pesos (81.6 UF convertidas)
    tope_imponible_salud: Decimal   # en pesos (60 UF convertidas)
    tope_seg_cesantia:    Decimal   # en pesos
    tasa_acc_trabajo:     Decimal   # % accidentes del trabajo (cargo empleador)


@dataclass
class DatosTrabajador:
    """Snapshot de los datos del trabajador necesarios para el cálculo."""
    # Identificación
    trabajador_id:        str
    rut:                  str

    # Sueldo base
    tipo_sueldo:          str       # M/D/H/E
    monto_sueldo:         Decimal
    horas_semana:         Decimal = Decimal("45")
    dias_semana:          int     = 5

    # Gratificación
    tipo_gratificacion:   str     = "calculada"
    monto_gratificacion:  Decimal = Decimal("0")

    # Colación/movilización (exentas)
    monto_movilizacion:   Decimal = Decimal("0")
    monto_colacion:       Decimal = Decimal("0")

    # AFP
    afp_id:               Optional[int] = None
    tasa_afp:             Decimal = Decimal("0.1144")  # tasa_trabajador
    tasa_sis:             Decimal = Decimal("0.0149")
    cotiz_vol_afp:        Decimal = Decimal("0")
    rebaja_imp_cotiz_vol: bool    = False
    regimen_previsional:  int     = 1  # 1=AFP, 2=Antiguo, 3=NoCotiza

    # Salud
    regimen_salud:        str     = "FONASA"
    modalidad_isapre:     int     = 3  # 3=7%
    monto_isapre_pesos:   Decimal = Decimal("0")
    monto_isapre_uf:      Decimal = Decimal("0")

    # Seguro cesantía
    tiene_seg_cesantia:   bool    = True
    contrato_plazo_fijo:  bool    = False

    # Zona extrema (DL 889)
    pct_asignacion_zona:  Decimal = Decimal("0")
    incrementa_pct_zona:  bool    = False
    region_id:            Optional[int] = None

    # Tributación
    impuesto_agricola:    bool    = False
    no_cotiza_sis:        bool    = False
    tipo_trabajador:      int     = 1

    # APV
    apv_monto:            Decimal = Decimal("0")
    apv_rebaja_42bis:     bool    = False

    # Cargas familiares activas
    nro_cargas_simple:    int     = 0
    nro_cargas_invalidez: int     = 0
    nro_cargas_maternal:  int     = 0


@dataclass
class DatosMovimiento:
    """Datos del movimiento mensual para el cálculo."""
    dias_ausentes:        Decimal = Decimal("0")
    dias_no_contratado:   Decimal = Decimal("0")
    dias_licencia:        Decimal = Decimal("0")
    dias_movilizacion:    Decimal = Decimal("0")
    dias_colacion:        Decimal = Decimal("0")
    dias_vacaciones:      Decimal = Decimal("0")

    hh_extras_normales:   Decimal = Decimal("0")
    hh_extras_nocturnas:  Decimal = Decimal("0")
    hh_extras_festivas:   Decimal = Decimal("0")

    otras_rentas:         Decimal = Decimal("0")   # renta otro empleador
    monto_isapre_otro:    Decimal = Decimal("0")
    monto_salud_iu:       Decimal = Decimal("0")

    cargas_retro_simples:    int  = 0
    cargas_retro_invalidez:  int  = 0
    cargas_retro_maternales: int  = 0

    # Conceptos adicionales (haberes y descuentos del movimiento)
    haberes_imponibles_adicionales:    Decimal = Decimal("0")
    haberes_no_imponibles_adicionales: Decimal = Decimal("0")
    haberes_tributables_adicionales:   Decimal = Decimal("0")
    haberes_exentos_adicionales:       Decimal = Decimal("0")
    descuentos_varios:                 Decimal = Decimal("0")
    descuentos_prestamos:              Decimal = Decimal("0")

    anticipo:             Decimal = Decimal("0")
    codigo_movimiento:    int     = 0


@dataclass
class ResultadoCalculo:
    """
    Resultado completo del cálculo de liquidación.
    Todos los valores en pesos chilenos (enteros).
    """
    # ── HABERES ───────────────────────────────────────────────────────────────
    sueldo_base_proporcional: Decimal = Decimal("0")
    valor_hora_extra:         Decimal = Decimal("0")
    hh_extra_normales_monto:  Decimal = Decimal("0")
    hh_extra_nocturnas_monto: Decimal = Decimal("0")
    hh_extra_festivas_monto:  Decimal = Decimal("0")
    total_horas_extra:        Decimal = Decimal("0")
    movilizacion:             Decimal = Decimal("0")
    colacion:                 Decimal = Decimal("0")
    gratificacion:            Decimal = Decimal("0")
    haberes_imponibles:       Decimal = Decimal("0")
    haberes_no_imponibles:    Decimal = Decimal("0")
    total_haberes:            Decimal = Decimal("0")

    # ── BASES DE CÁLCULO ──────────────────────────────────────────────────────
    total_imponible:          Decimal = Decimal("0")   # base cotizaciones
    total_tributable:         Decimal = Decimal("0")   # base impuesto (antes de descuentos prev.)

    # ── COTIZACIONES PREVISIONALES ────────────────────────────────────────────
    descuento_afp:            Decimal = Decimal("0")
    descuento_sis:            Decimal = Decimal("0")   # cargo empleador (informativo)
    descuento_salud:          Decimal = Decimal("0")   # 7% legal
    diferencia_isapre:        Decimal = Decimal("0")   # exceso sobre 7%
    descuento_seg_cesantia_t: Decimal = Decimal("0")   # trabajador
    descuento_seg_cesantia_e: Decimal = Decimal("0")   # empleador (informativo)
    cotiz_voluntaria_afp:     Decimal = Decimal("0")
    apv_monto:                Decimal = Decimal("0")

    # ── IMPUESTO ÚNICO ────────────────────────────────────────────────────────
    rebaja_zona_extrema:      Decimal = Decimal("0")
    base_impuesto_unico:      Decimal = Decimal("0")
    impuesto_unico:           Decimal = Decimal("0")

    # ── CARGAS FAMILIARES ─────────────────────────────────────────────────────
    asignacion_familiar:      Decimal = Decimal("0")

    # ── DESCUENTOS ────────────────────────────────────────────────────────────
    descuentos_varios:        Decimal = Decimal("0")
    descuentos_prestamos:     Decimal = Decimal("0")
    total_descuentos:         Decimal = Decimal("0")

    # ── RESULTADO FINAL ───────────────────────────────────────────────────────
    anticipo:                 Decimal = Decimal("0")
    liquido_a_pagar:          Decimal = Decimal("0")

    # ── APORTES EMPLEADOR (no afectan líquido, para centralización) ───────────
    aporte_acc_trabajo:       Decimal = Decimal("0")


# ─────────────────────────────────────────────────────────────────────────────
# MOTOR DE CÁLCULO
# ─────────────────────────────────────────────────────────────────────────────

class MotorCalculo:
    """
    Motor principal de cálculo de liquidaciones chilenas.
    Stateless: cada llamada a calcular() es independiente.
    """

    def __init__(self,
                 params: ParametrosPeriodo,
                 tramos_afp: list,           # list[TramoAsignacionFamiliar]
                 tramos_iu: list,            # list[TramoImpuestoUnicoUTM]
                 ):
        self.params = params
        self.tramos_af = tramos_afp
        self.tramos_iu = tramos_iu

    # ── PASO 1: Sueldo base proporcional ──────────────────────────────────────

    def _calcular_sueldo_base(self, t: DatosTrabajador,
                               m: DatosMovimiento) -> Decimal:
        """
        Proporcionaliza el sueldo base según días trabajados.
        Días trabajados = 30 - días_ausentes - días_no_contratado - días_licencia
        (los días de vacaciones SÍ se pagan — no se descuentan del sueldo)
        """
        dias_descuento = m.dias_ausentes + m.dias_no_contratado + m.dias_licencia
        dias_trabajados = DIAS_MES - dias_descuento
        if dias_trabajados < 0:
            dias_trabajados = Decimal("0")

        if t.tipo_sueldo == "M":
            sueldo = t.monto_sueldo * dias_trabajados / DIAS_MES
        elif t.tipo_sueldo == "D":
            sueldo = t.monto_sueldo * dias_trabajados
        elif t.tipo_sueldo == "H":
            horas_trabajadas = dias_trabajados * (t.horas_semana / t.dias_semana)
            sueldo = t.monto_sueldo * horas_trabajadas
        else:  # Empresarial
            sueldo = t.monto_sueldo
        return _redondear(sueldo)

    # ── PASO 2: Horas extras ──────────────────────────────────────────────────

    def _calcular_horas_extra(self, t: DatosTrabajador,
                               m: DatosMovimiento,
                               sueldo_base: Decimal) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        """
        Art. 32 CT: hora extra = (sueldo mensual / (días_semana * horas_semana * 4.33)) * factor
        Retorna: (valor_hora, monto_normales, monto_nocturnas, monto_festivas)
        """
        horas_mes = t.dias_semana * t.horas_semana * Decimal("4.33")
        if horas_mes <= 0:
            return Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0")

        valor_hora = t.monto_sueldo / horas_mes

        monto_normales  = _redondear(valor_hora * FACTOR_HH_NORMAL   * m.hh_extras_normales)
        monto_nocturnas = _redondear(valor_hora * FACTOR_HH_NOCTURNA  * m.hh_extras_nocturnas)
        monto_festivas  = _redondear(valor_hora * FACTOR_HH_FESTIVA   * m.hh_extras_festivas)

        return _redondear(valor_hora), monto_normales, monto_nocturnas, monto_festivas

    # ── PASO 3: Colación y movilización ───────────────────────────────────────

    def _calcular_colacion_movilizacion(self, t: DatosTrabajador,
                                         m: DatosMovimiento) -> tuple[Decimal, Decimal]:
        """
        Colación y movilización son EXENTAS de imposiciones y tributación.
        Se pagan proporcionalmente a los días de colación/movilización.
        """
        dias_col = m.dias_colacion if m.dias_colacion > 0 else (DIAS_MES - m.dias_ausentes - m.dias_no_contratado)
        dias_mov = m.dias_movilizacion if m.dias_movilizacion > 0 else (DIAS_MES - m.dias_ausentes - m.dias_no_contratado)

        if t.tipo_sueldo in ("D", "H"):
            colacion    = _redondear(t.monto_colacion * dias_col)
            movilizacion = _redondear(t.monto_movilizacion * dias_mov)
        else:
            colacion    = _redondear(t.monto_colacion * dias_col / DIAS_MES * DIAS_MES)
            movilizacion = _redondear(t.monto_movilizacion * dias_mov / DIAS_MES * DIAS_MES)

        return colacion, movilizacion

    # ── PASO 4: Gratificación ─────────────────────────────────────────────────

    def _calcular_gratificacion(self, t: DatosTrabajador,
                                 imponible_previo: Decimal) -> Decimal:
        """
        Art. 50 CT: 25% de remuneración imponible con tope 4.75 IMM.
        'calculada' y 'calculada_dict4232' aplican el mismo tope mensual.
        'informada' y 'proporcional' → retorna monto_gratificacion directamente.
        """
        if t.tipo_gratificacion == "no_paga":
            return Decimal("0")
        if t.tipo_gratificacion in ("informada", "proporcional"):
            return _redondear(t.monto_gratificacion or Decimal("0"))

        # calculada o calculada_dict4232
        tope_mensual = _redondear(self.params.imm * TOPE_GRATIFICACION_IMM / 12)
        gratificacion_calculada = _redondear(imponible_previo * FACTOR_GRATIFICACION)
        return min(gratificacion_calculada, tope_mensual)

    # ── PASO 5: Total imponible ───────────────────────────────────────────────

    def _calcular_imponible(self, sueldo_base: Decimal, horas_extra: Decimal,
                             gratificacion: Decimal,
                             haberes_imponibles: Decimal) -> Decimal:
        """
        Total imponible = sueldo_base + horas_extra + gratificacion + haberes_imponibles
        NO incluye colación ni movilización.
        """
        return _redondear(sueldo_base + horas_extra + gratificacion + haberes_imponibles)

    # ── PASO 6: Cotización AFP ────────────────────────────────────────────────

    def _calcular_afp(self, t: DatosTrabajador,
                       imponible: Decimal) -> tuple[Decimal, Decimal]:
        """
        DL 3.500: cotización obligatoria sobre imponible con tope 81.6 UF.
        Retorna: (descuento_trabajador, descuento_sis_empleador)
        """
        if t.regimen_previsional != 1:  # No AFP
            return Decimal("0"), Decimal("0")

        base = min(imponible, self.params.tope_imponible_afp)
        descuento = _redondear(base * t.tasa_afp)
        sis = Decimal("0") if t.no_cotiza_sis else _redondear(base * t.tasa_sis)
        return descuento, sis

    # ── PASO 7: Cotización salud ──────────────────────────────────────────────

    def _calcular_salud(self, t: DatosTrabajador,
                         imponible: Decimal,
                         uf: Decimal) -> tuple[Decimal, Decimal]:
        """
        7% sobre imponible con tope 60 UF.
        Si Isapre, la diferencia entre plan pactado y 7% legal es 'diferencia Isapre'.
        Retorna: (descuento_7pct_legal, diferencia_isapre)
        """
        base = min(imponible, self.params.tope_imponible_salud)
        descuento_legal = _redondear(base * Decimal("0.07"))

        if t.regimen_salud == "FONASA":
            return descuento_legal, Decimal("0")

        # Isapre
        if t.modalidad_isapre == 3:   # solo 7%
            return descuento_legal, Decimal("0")

        # Calcular monto plan pactado
        plan_uf_pesos   = _redondear(t.monto_isapre_uf * uf)
        plan_pesos      = t.monto_isapre_pesos

        if t.modalidad_isapre == 1:   # pesos
            plan_total = plan_pesos
        elif t.modalidad_isapre == 2: # UF
            plan_total = plan_uf_pesos
        elif t.modalidad_isapre == 4: # 7% + UF
            plan_total = descuento_legal + plan_uf_pesos
        elif t.modalidad_isapre == 5: # 7% + UF + Pesos
            plan_total = descuento_legal + plan_uf_pesos + plan_pesos
        elif t.modalidad_isapre == 6: # Pesos + UF
            plan_total = plan_pesos + plan_uf_pesos
        else:
            plan_total = descuento_legal

        diferencia = max(Decimal("0"), plan_total - descuento_legal)
        return descuento_legal, _redondear(diferencia)

    # ── PASO 8: Seguro de Cesantía ────────────────────────────────────────────

    def _calcular_seg_cesantia(self, t: DatosTrabajador,
                                imponible: Decimal) -> tuple[Decimal, Decimal]:
        """
        Ley 19.728 — AFC.
        Contrato indefinido: trabajador 0.6% + empleador 2.4%
        Contrato plazo fijo/obra: solo empleador 3.0%
        Tope imponible = 122.6 UF.
        Retorna: (descuento_trabajador, descuento_empleador)
        """
        if not t.tiene_seg_cesantia:
            return Decimal("0"), Decimal("0")

        base = min(imponible, self.params.tope_seg_cesantia)

        if t.contrato_plazo_fijo:
            return Decimal("0"), _redondear(base * TASA_SC_EMPLEADOR_PLAZO_FIJO)
        else:
            trab = _redondear(base * TASA_SC_TRABAJADOR_INDEFINIDO)
            empl = _redondear(base * TASA_SC_EMPLEADOR_INDEFINIDO)
            return trab, empl

    # ── PASO 9: Base impuesto único ───────────────────────────────────────────

    def _calcular_base_iu(self, imponible: Decimal,
                           descuento_afp: Decimal,
                           descuento_salud: Decimal,
                           descuento_sc_t: Decimal,
                           cotiz_vol: Decimal,
                           apv: Decimal,
                           rebaja_apv: bool,
                           otras_rentas: Decimal,
                           monto_salud_iu: Decimal) -> Decimal:
        """
        Base IU = imponible - cotiz.AFP - cotiz.salud_legal - SC_trabajador
                  - APV (si rebaja) - cotiz_voluntaria (si rebaja)
                  + otras_rentas (de otro empleador)
                  - monto_salud_iu (deducción especial otro empleador)
        """
        base = (imponible
                - descuento_afp
                - descuento_salud
                - descuento_sc_t
                - (cotiz_vol if True else Decimal("0"))   # cotiz vol siempre rebaja
                - (apv if rebaja_apv else Decimal("0"))
                + otras_rentas
                - monto_salud_iu)
        return max(Decimal("0"), _redondear(base))

    # ── PASO 10: Asignación de zona extrema ───────────────────────────────────

    def _calcular_zona_extrema(self, t: DatosTrabajador,
                                base_iu: Decimal,
                                leyes_sociales: Decimal,
                                imm_mensual: Decimal) -> Decimal:
        """
        DL 889: rebaja de zona para regiones I, XI, XII, XV y Chiloé-Palena.
        MIN{ [(REM-LS) * %AZ / (100+%AZ)] * 1.4 ; [GR1_EUS * %AZ/100] * 1.4 }
        Si marca incrementa_pct_zona: se incrementa el % en 40% antes de aplicar.
        """
        REGIONES_ZONA_EXTREMA = {1, 11, 12, 15}
        if t.pct_asignacion_zona <= 0:
            return Decimal("0")
        if t.region_id not in REGIONES_ZONA_EXTREMA:
            return Decimal("0")

        pct = t.pct_asignacion_zona
        if t.incrementa_pct_zona:
            pct = pct * Decimal("1.4")

        # GR1 EUS ≈ IMM mensual (sueldo 1ª escala única de sueldos)
        gr1_eus = imm_mensual

        opcion_a = ((base_iu - leyes_sociales) * pct / (100 + pct)) * Decimal("1.4")
        opcion_b = (gr1_eus * pct / 100) * Decimal("1.4")

        rebaja = min(opcion_a, opcion_b)
        return max(Decimal("0"), _redondear(rebaja))

    # ── PASO 11: Impuesto único 2ª categoría ──────────────────────────────────

    def _calcular_impuesto_unico(self, base_definitiva: Decimal,
                                  utm: Decimal) -> Decimal:
        """
        Tabla progresiva en UTM (Art. 43 Ley de la Renta).
        base_definitiva en pesos → convertir a UTM → aplicar tabla → convertir a pesos.
        """
        if base_definitiva <= 0:
            return Decimal("0")

        base_utm = base_definitiva / utm

        impuesto_utm = Decimal("0")
        for tramo in self.tramos_iu:
            utm_desde = Decimal(str(tramo.utm_desde))
            utm_hasta = tramo.utm_hasta
            tasa      = Decimal(str(tramo.tasa))
            rebaja    = Decimal(str(tramo.rebaja_utm))

            if utm_hasta is None or base_utm <= Decimal(str(utm_hasta)):
                if base_utm > utm_desde:
                    impuesto_utm = base_utm * tasa - rebaja
                    break
        else:
            # Último tramo (sin límite superior)
            if self.tramos_iu:
                ultimo = self.tramos_iu[-1]
                tasa   = Decimal(str(ultimo.tasa))
                rebaja = Decimal(str(ultimo.rebaja_utm))
                impuesto_utm = base_utm * tasa - rebaja

        impuesto_pesos = max(Decimal("0"), _redondear(impuesto_utm * utm))
        return impuesto_pesos

    # ── PASO 12: Asignación familiar ──────────────────────────────────────────

    def _calcular_asignacion_familiar(self, t: DatosTrabajador,
                                       m: DatosMovimiento,
                                       imponible: Decimal) -> Decimal:
        """
        SUAF: se paga directamente en la liquidación.
        Monto depende del tramo (renta imponible) y tipo de carga.
        Cargas retroactivas también se incluyen.
        """
        if not self.tramos_af:
            return Decimal("0")

        valor_carga = Decimal("0")
        for tramo in self.tramos_af:
            t_desde = Decimal(str(tramo.renta_desde))
            t_hasta = tramo.renta_hasta
            if imponible >= t_desde and (t_hasta is None or imponible <= Decimal(str(t_hasta))):
                valor_carga = Decimal(str(tramo.valor_carga))
                break

        total_cargas = (t.nro_cargas_simple + t.nro_cargas_invalidez + t.nro_cargas_maternal
                        + m.cargas_retro_simples + m.cargas_retro_invalidez + m.cargas_retro_maternales)

        # Cargas de invalidez tienen valor doble
        cargas_invalidez = t.nro_cargas_invalidez + m.cargas_retro_invalidez
        cargas_normales  = total_cargas - cargas_invalidez
        total_asig = _redondear(valor_carga * cargas_normales + valor_carga * 2 * cargas_invalidez)
        return total_asig

    # ── MOTOR PRINCIPAL ────────────────────────────────────────────────────────

    def calcular(self, t: DatosTrabajador, m: DatosMovimiento) -> ResultadoCalculo:
        """
        Ejecuta el proceso completo de cálculo en orden legislativo.
        Retorna ResultadoCalculo con todos los montos en pesos.
        """
        r = ResultadoCalculo()
        params = self.params

        # 1. Sueldo base proporcional
        r.sueldo_base_proporcional = self._calcular_sueldo_base(t, m)

        # 2. Horas extras
        r.valor_hora_extra, r.hh_extra_normales_monto, r.hh_extra_nocturnas_monto, \
            r.hh_extra_festivas_monto = self._calcular_horas_extra(t, m, r.sueldo_base_proporcional)
        r.total_horas_extra = (r.hh_extra_normales_monto
                               + r.hh_extra_nocturnas_monto
                               + r.hh_extra_festivas_monto)

        # 3. Colación y movilización (exentas)
        r.colacion, r.movilizacion = self._calcular_colacion_movilizacion(t, m)

        # Base pre-gratificación (sueldo + HHEE + haberes imponibles adicionales)
        base_pre_grat = (r.sueldo_base_proporcional
                         + r.total_horas_extra
                         + m.haberes_imponibles_adicionales)

        # 4. Gratificación
        r.gratificacion = self._calcular_gratificacion(t, base_pre_grat)

        # 5. Haberes imponibles y no imponibles
        r.haberes_imponibles  = _redondear(m.haberes_imponibles_adicionales)
        r.haberes_no_imponibles = _redondear(
            r.colacion + r.movilizacion + m.haberes_no_imponibles_adicionales
        )

        # 6. Total imponible
        r.total_imponible = self._calcular_imponible(
            r.sueldo_base_proporcional,
            r.total_horas_extra,
            r.gratificacion,
            r.haberes_imponibles
        )

        # Total haberes (imponible + no imponibles + exentos)
        r.total_haberes = _redondear(
            r.total_imponible
            + r.haberes_no_imponibles
            + m.haberes_exentos_adicionales
        )

        # 7. AFP
        r.descuento_afp, r.descuento_sis = self._calcular_afp(t, r.total_imponible)

        # 8. Salud
        r.descuento_salud, r.diferencia_isapre = self._calcular_salud(
            t, r.total_imponible, params.uf
        )

        # 9. Seguro de Cesantía
        r.descuento_seg_cesantia_t, r.descuento_seg_cesantia_e = self._calcular_seg_cesantia(
            t, r.total_imponible
        )

        # Cotización voluntaria AFP
        r.cotiz_voluntaria_afp = _redondear(t.cotiz_vol_afp)

        # APV
        r.apv_monto = _redondear(t.apv_monto)

        # 10. Base impuesto único
        leyes_sociales = r.descuento_afp + r.descuento_salud + r.descuento_seg_cesantia_t
        base_iu = self._calcular_base_iu(
            r.total_imponible,
            r.descuento_afp,
            r.descuento_salud,
            r.descuento_seg_cesantia_t,
            r.cotiz_voluntaria_afp,
            r.apv_monto,
            t.apv_rebaja_42bis,
            m.otras_rentas,
            m.monto_salud_iu
        )

        # 11. Zona extrema
        r.rebaja_zona_extrema = self._calcular_zona_extrema(
            t, base_iu, leyes_sociales, params.imm
        )
        r.base_impuesto_unico = max(Decimal("0"), base_iu - r.rebaja_zona_extrema)

        # 12. Impuesto único
        r.impuesto_unico = self._calcular_impuesto_unico(r.base_impuesto_unico, params.utm)

        # 13. Cargas familiares
        r.asignacion_familiar = self._calcular_asignacion_familiar(t, m, r.total_imponible)

        # 14. Descuentos varios
        r.descuentos_varios   = _redondear(m.descuentos_varios)
        r.descuentos_prestamos = _redondear(m.descuentos_prestamos)

        # 15. Total descuentos
        r.total_descuentos = _redondear(
            r.descuento_afp
            + r.descuento_salud
            + r.diferencia_isapre
            + r.descuento_seg_cesantia_t
            + r.cotiz_voluntaria_afp
            + r.apv_monto
            + r.impuesto_unico
            + r.descuentos_varios
            + r.descuentos_prestamos
        )

        # 16. Aportes empleador (no afectan líquido)
        r.aporte_acc_trabajo = _redondear(r.total_imponible * params.tasa_acc_trabajo)

        # 17. Anticipo
        r.anticipo = _redondear(m.anticipo)

        # 18. Líquido a pagar
        r.liquido_a_pagar = _redondear(
            r.total_haberes
            + r.asignacion_familiar
            - r.total_descuentos
            - r.anticipo
        )

        # Aplicar mínimo legal (sueldo mínimo neto si corresponde)
        if r.liquido_a_pagar < 0:
            r.liquido_a_pagar = Decimal("0")

        return r
