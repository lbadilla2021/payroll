"""
modulos/nomina/calculo/servicio_calculo.py
==========================================
Servicio que orquesta el motor de cálculo con los datos de la BD.

Responsabilidades:
  1. Cargar datos del trabajador (rrhh.trabajador + nomina.afp, isapre, etc.)
  2. Cargar parámetros del período (nomina.parametro_mensual)
  3. Cargar tramos tributarios vigentes
  4. Construir DatosTrabajador y DatosMovimiento
  5. Llamar al motor de cálculo
  6. Persistir resultados en movimiento_mensual
  7. Calcular por empresa (masivo)
"""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from modulos.nomina.calculo.motor import (
    DatosMovimiento, DatosTrabajador, MotorCalculo,
    ParametrosPeriodo, ResultadoCalculo,
)
from modulos.nomina.models import (
    Afp, MovimientoConcepto, MovimientoMensual, ParametroMensual,
    TramoAsignacionFamiliar, TramoImpuestoUnicoUTM,
)
from modulos.nomina.repositories import ParametroMensualRepository
from modulos.nomina.repositories_operacional import MovimientoMensualRepository
from modulos.rrhh.models import CargaFamiliar, Trabajador, TrabajadorApv


def _set_tenant(db: Session, tenant_id: UUID) -> None:
    db.execute(text("SET LOCAL app.current_tenant_id = :tid"), {"tid": str(tenant_id)})


class ServicioCalculo:
    """
    Orquestador del proceso de cálculo de liquidaciones.
    """

    # ── Carga de datos ────────────────────────────────────────────────────────

    @staticmethod
    def _cargar_parametros(db: Session, tenant_id: UUID,
                            anio: int, mes: int) -> ParametroMensual:
        params = ParametroMensualRepository.get_by_periodo(db, tenant_id, anio, mes)
        if not params:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No existen parámetros configurados para {anio}/{mes:02d}. "
                       "Configure los parámetros mensuales antes de calcular."
            )
        if params.bloqueado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El período {anio}/{mes:02d} está bloqueado."
            )
        if params.cerrado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El período {anio}/{mes:02d} ya fue cerrado."
            )
        return params

    @staticmethod
    def _cargar_tramos_af(db: Session, anio: int, mes: int) -> list:
        tramos = db.query(TramoAsignacionFamiliar).filter(
            TramoAsignacionFamiliar.anio == anio,
            TramoAsignacionFamiliar.mes == mes
        ).order_by(TramoAsignacionFamiliar.tramo).all()
        if not tramos:
            # Fallback al período más reciente disponible
            ultimo = db.query(
                TramoAsignacionFamiliar.anio,
                TramoAsignacionFamiliar.mes
            ).order_by(
                TramoAsignacionFamiliar.anio.desc(),
                TramoAsignacionFamiliar.mes.desc()
            ).first()
            if ultimo:
                tramos = db.query(TramoAsignacionFamiliar).filter(
                    TramoAsignacionFamiliar.anio == ultimo.anio,
                    TramoAsignacionFamiliar.mes == ultimo.mes
                ).order_by(TramoAsignacionFamiliar.tramo).all()
        return tramos

    @staticmethod
    def _cargar_tramos_iu(db: Session, anio: int, mes: int) -> list:
        tramos = db.query(TramoImpuestoUnicoUTM).filter(
            TramoImpuestoUnicoUTM.anio == anio,
            TramoImpuestoUnicoUTM.mes == mes
        ).order_by(TramoImpuestoUnicoUTM.orden).all()
        if not tramos:
            ultimo = db.query(
                TramoImpuestoUnicoUTM.anio,
                TramoImpuestoUnicoUTM.mes
            ).order_by(
                TramoImpuestoUnicoUTM.anio.desc(),
                TramoImpuestoUnicoUTM.mes.desc()
            ).first()
            if ultimo:
                tramos = db.query(TramoImpuestoUnicoUTM).filter(
                    TramoImpuestoUnicoUTM.anio == ultimo.anio,
                    TramoImpuestoUnicoUTM.mes == ultimo.mes
                ).order_by(TramoImpuestoUnicoUTM.orden).all()
        return tramos

    @staticmethod
    def _cargar_tasa_afp(db: Session, afp_id: Optional[int]) -> tuple[Decimal, Decimal]:
        """Retorna (tasa_trabajador, tasa_sis) de la AFP."""
        if not afp_id:
            return Decimal("0"), Decimal("0")
        afp = db.query(Afp).filter(Afp.id == afp_id).first()
        if not afp:
            return Decimal("0"), Decimal("0")
        return Decimal(str(afp.tasa_trabajador)), Decimal(str(afp.tasa_sis))

    @staticmethod
    def _cargar_cargas_familiares(db: Session, tenant_id: UUID,
                                   trabajador_id: UUID) -> tuple[int, int, int]:
        """Retorna (simples, invalidez, maternales) vigentes."""
        _set_tenant(db, tenant_id)
        cargas = db.query(CargaFamiliar).filter(
            CargaFamiliar.tenant_id == tenant_id,
            CargaFamiliar.trabajador_id == trabajador_id,
            CargaFamiliar.es_activa == True
        ).all()
        simples   = sum(1 for c in cargas if c.tipo_carga == "simple")
        invalidez = sum(1 for c in cargas if c.tipo_carga == "invalidez")
        maternal  = sum(1 for c in cargas if c.tipo_carga == "maternal")
        return simples, invalidez, maternal

    @staticmethod
    def _cargar_apv(db: Session, tenant_id: UUID,
                    trabajador_id: UUID) -> tuple[Decimal, bool]:
        """Retorna (monto_total_apv, alguno_rebaja_42bis)."""
        _set_tenant(db, tenant_id)
        apvs = db.query(TrabajadorApv).filter(
            TrabajadorApv.tenant_id == tenant_id,
            TrabajadorApv.trabajador_id == trabajador_id,
            TrabajadorApv.es_activo == True
        ).all()
        total = sum(Decimal(str(a.monto_trabajador)) for a in apvs)
        rebaja = any(a.rebaja_art42bis for a in apvs)
        return total, rebaja

    @staticmethod
    def _agregar_conceptos_movimiento(db: Session,
                                       movimiento_id: UUID) -> DatosMovimiento:
        """Suma los conceptos del movimiento en las categorías correctas."""
        from modulos.nomina.models import ConceptoRemuneracion
        conceptos = db.query(MovimientoConcepto).filter(
            MovimientoConcepto.movimiento_id == movimiento_id
        ).all()

        hab_imp = Decimal("0")
        hab_no_imp = Decimal("0")
        hab_trib = Decimal("0")
        hab_exento = Decimal("0")
        desc_varios = Decimal("0")
        desc_prestamos = Decimal("0")

        for mc in conceptos:
            concepto = db.query(ConceptoRemuneracion).filter(
                ConceptoRemuneracion.id == mc.concepto_id
            ).first()
            if not concepto:
                continue

            monto = Decimal(str(mc.valor)) * Decimal(str(mc.cantidad))

            if mc.tipo == "H":
                if concepto.es_imponible:
                    hab_imp += monto
                elif concepto.es_renta_exenta:
                    hab_exento += monto
                else:
                    hab_no_imp += monto
                if concepto.es_tributable:
                    hab_trib += monto
            else:  # Descuento
                if concepto.es_prestamo or concepto.es_prestamo_ccaf:
                    desc_prestamos += monto
                else:
                    desc_varios += monto

        # Retornar parcialmente — el llamador tiene el DatosMovimiento base
        return {
            "haberes_imponibles_adicionales":    hab_imp,
            "haberes_no_imponibles_adicionales": hab_no_imp,
            "haberes_tributables_adicionales":   hab_trib,
            "haberes_exentos_adicionales":       hab_exento,
            "descuentos_varios":                 desc_varios,
            "descuentos_prestamos":              desc_prestamos,
        }

    # ── Construcción de estructuras para el motor ─────────────────────────────

    @staticmethod
    def _construir_datos_trabajador(t: Trabajador, tasa_afp: Decimal,
                                     tasa_sis: Decimal, simples: int,
                                     invalidez: int, maternal: int,
                                     apv_monto: Decimal,
                                     apv_rebaja: bool) -> DatosTrabajador:
        return DatosTrabajador(
            trabajador_id        = str(t.id),
            rut                  = t.rut,
            tipo_sueldo          = t.tipo_sueldo,
            monto_sueldo         = Decimal(str(t.monto_sueldo)),
            horas_semana         = Decimal(str(t.horas_semana or 45)),
            dias_semana          = int(t.dias_semana or 5),
            tipo_gratificacion   = t.tipo_gratificacion,
            monto_gratificacion  = Decimal(str(t.monto_gratificacion or 0)),
            monto_movilizacion   = Decimal(str(t.monto_movilizacion)),
            monto_colacion       = Decimal(str(t.monto_colacion)),
            afp_id               = t.afp_id,
            tasa_afp             = tasa_afp,
            tasa_sis             = tasa_sis,
            cotiz_vol_afp        = Decimal(str(t.cotizacion_voluntaria_afp)),
            rebaja_imp_cotiz_vol = t.rebaja_imp_cotiz_vol,
            regimen_previsional  = t.regimen_previsional,
            regimen_salud        = t.regimen_salud,
            modalidad_isapre     = int(t.modalidad_isapre or 3),
            monto_isapre_pesos   = Decimal(str(t.monto_isapre_pesos)),
            monto_isapre_uf      = Decimal(str(t.monto_isapre_uf)),
            tiene_seg_cesantia   = t.tiene_seg_cesantia,
            contrato_plazo_fijo  = t.contrato_plazo_fijo,
            pct_asignacion_zona  = Decimal(str(t.pct_asignacion_zona)),
            incrementa_pct_zona  = t.incrementa_pct_zona,
            region_id            = t.region_id,
            impuesto_agricola    = t.impuesto_agricola,
            no_cotiza_sis        = t.no_cotiza_sis,
            tipo_trabajador      = t.tipo_trabajador,
            apv_monto            = apv_monto,
            apv_rebaja_42bis     = apv_rebaja,
            nro_cargas_simple    = simples,
            nro_cargas_invalidez = invalidez,
            nro_cargas_maternal  = maternal,
        )

    @staticmethod
    def _construir_datos_movimiento(m: MovimientoMensual,
                                     conceptos_extra: dict) -> DatosMovimiento:
        return DatosMovimiento(
            dias_ausentes        = Decimal(str(m.dias_ausentes)),
            dias_no_contratado   = Decimal(str(m.dias_no_contratado)),
            dias_licencia        = Decimal(str(m.dias_licencia)),
            dias_movilizacion    = Decimal(str(m.dias_movilizacion)),
            dias_colacion        = Decimal(str(m.dias_colacion)),
            dias_vacaciones      = Decimal(str(m.dias_vacaciones)),
            hh_extras_normales   = Decimal(str(m.hh_extras_normales)),
            hh_extras_nocturnas  = Decimal(str(m.hh_extras_nocturnas)),
            hh_extras_festivas   = Decimal(str(m.hh_extras_festivas)),
            otras_rentas         = Decimal(str(m.otras_rentas)),
            monto_isapre_otro    = Decimal(str(m.monto_isapre_otro)),
            monto_salud_iu       = Decimal(str(m.monto_salud_iu)),
            cargas_retro_simples    = m.cargas_retro_simples,
            cargas_retro_invalidez  = m.cargas_retro_invalidez,
            cargas_retro_maternales = m.cargas_retro_maternales,
            anticipo             = Decimal(str(m.anticipo)),
            codigo_movimiento    = m.codigo_movimiento,
            **conceptos_extra,
        )

    @staticmethod
    def _construir_params_periodo(p: ParametroMensual) -> ParametrosPeriodo:
        return ParametrosPeriodo(
            utm                  = Decimal(str(p.utm)),
            uf                   = Decimal(str(p.uf)),
            imm                  = Decimal(str(p.imm)),
            tope_imponible_afp   = Decimal(str(p.tope_imponible_afp)),
            tope_imponible_salud = Decimal(str(p.tope_imponible_salud)),
            tope_seg_cesantia    = Decimal(str(p.tope_seg_cesantia)),
            tasa_acc_trabajo     = Decimal(str(p.tasa_acc_trabajo)),
        )

    # ── Cálculo individual ────────────────────────────────────────────────────

    @staticmethod
    def calcular_movimiento(db: Session, tenant_id: UUID,
                             movimiento_id: UUID) -> ResultadoCalculo:
        """
        Calcula la liquidación de un movimiento mensual individual.
        Persiste los resultados y retorna el ResultadoCalculo.
        """
        _set_tenant(db, tenant_id)

        # Cargar movimiento
        movimiento = db.query(MovimientoMensual).filter(
            MovimientoMensual.tenant_id == tenant_id,
            MovimientoMensual.id == movimiento_id
        ).first()
        if not movimiento:
            raise HTTPException(status_code=404, detail="Movimiento no encontrado.")

        anio, mes = movimiento.anio, movimiento.mes

        # Cargar parámetros del período
        params_db = ServicioCalculo._cargar_parametros(db, tenant_id, anio, mes)

        # Cargar trabajador
        trabajador = db.query(Trabajador).filter(
            Trabajador.tenant_id == tenant_id,
            Trabajador.id == movimiento.trabajador_id
        ).first()
        if not trabajador:
            raise HTTPException(status_code=404,
                                detail=f"Trabajador {movimiento.trabajador_id} no encontrado.")

        # Cargar datos auxiliares
        tasa_afp, tasa_sis = ServicioCalculo._cargar_tasa_afp(db, trabajador.afp_id)
        simples, invalidez, maternal = ServicioCalculo._cargar_cargas_familiares(
            db, tenant_id, trabajador.id
        )
        apv_monto, apv_rebaja = ServicioCalculo._cargar_apv(db, tenant_id, trabajador.id)

        # Cargar tramos tributarios
        tramos_af = ServicioCalculo._cargar_tramos_af(db, anio, mes)
        tramos_iu = ServicioCalculo._cargar_tramos_iu(db, anio, mes)

        # Agregar conceptos del movimiento
        conceptos_extra = ServicioCalculo._agregar_conceptos_movimiento(db, movimiento_id)

        # Construir estructuras para el motor
        datos_t = ServicioCalculo._construir_datos_trabajador(
            trabajador, tasa_afp, tasa_sis, simples, invalidez, maternal,
            apv_monto, apv_rebaja
        )
        datos_m = ServicioCalculo._construir_datos_movimiento(movimiento, conceptos_extra)
        params  = ServicioCalculo._construir_params_periodo(params_db)

        # Ejecutar cálculo
        motor = MotorCalculo(params, tramos_af, tramos_iu)
        resultado = motor.calcular(datos_t, datos_m)

        # Persistir resultados
        MovimientoMensualRepository.marcar_calculado(db, movimiento, {
            "total_haberes":    resultado.total_haberes,
            "total_imponible":  resultado.total_imponible,
            "total_tributable": resultado.total_tributable,
            "descuento_afp":    resultado.descuento_afp,
            "descuento_salud":  resultado.descuento_salud,
            "impuesto_unico":   resultado.impuesto_unico,
            "total_descuentos": resultado.total_descuentos,
            "liquido_pagar":    resultado.liquido_a_pagar,
            "anticipo":         resultado.anticipo,
        })
        db.commit()

        return resultado

    # ── Cálculo masivo por empresa ─────────────────────────────────────────────

    @staticmethod
    def calcular_empresa(db: Session, tenant_id: UUID,
                          anio: int, mes: int) -> dict:
        """
        Calcula todos los movimientos pendientes del período.
        Retorna resumen: procesados, errores.
        """
        _set_tenant(db, tenant_id)

        # Verificar período
        ServicioCalculo._cargar_parametros(db, tenant_id, anio, mes)

        movimientos = db.query(MovimientoMensual).filter(
            MovimientoMensual.tenant_id == tenant_id,
            MovimientoMensual.anio == anio,
            MovimientoMensual.mes == mes,
            MovimientoMensual.estado.in_(["pendiente", "calculado"])
        ).all()

        procesados = 0
        errores = []

        for mov in movimientos:
            try:
                ServicioCalculo.calcular_movimiento(db, tenant_id, mov.id)
                procesados += 1
            except Exception as e:
                errores.append({
                    "movimiento_id": str(mov.id),
                    "trabajador_id": str(mov.trabajador_id),
                    "error": str(e)
                })
                db.rollback()  # Revertir solo este movimiento
                _set_tenant(db, tenant_id)  # Restaurar tenant tras rollback

        return {
            "anio": anio,
            "mes": mes,
            "total_movimientos": len(movimientos),
            "procesados": procesados,
            "errores": len(errores),
            "detalle_errores": errores,
        }
