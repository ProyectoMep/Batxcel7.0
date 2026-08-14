"""Motor de cumplimiento: calcula el % de cumplimiento de una métrica
(numerador/denominador vs umbral), reutilizando el motor de reglas.
Reemplaza la lógica de cumplimiento.py del sistema original.
"""
import pandas as pd
from models.metrica import Metrica
from services.reglas import evaluar_grupos


def calcular_cumplimiento(df: pd.DataFrame, metrica: Metrica) -> dict:
    """
    Calcula el cumplimiento de una métrica sobre un DataFrame ya resuelto
    (archivo leído + cruces aplicados). Retorna:
    {
      'metrica': str, 'aplica': bool, 'denominador': int, 'numerador': int,
      'resultado': float | None, 'umbral': float, 'estado': str
    }
    Si cumplimiento.aplica es False, retorna aplica=False sin calcular nada.
    """
    cfg = metrica.cumplimiento
    if not cfg.aplica:
        return {"metrica": metrica.nombre, "aplica": False}

    df_universo = df
    if cfg.excluir:
        mascara_excluir = evaluar_grupos(df_universo, cfg.excluir)
        excluidos = int(mascara_excluir.sum())
        df_universo = df_universo[~mascara_excluir]
        if excluidos:
            print(f"     ℹ️  {metrica.nombre}: {excluidos} fila(s) excluida(s) del universo")

    denominador = _calcular_total(df_universo, cfg)
    numerador = _calcular_favor(df_universo, cfg)

    resultado = (numerador / denominador) if denominador > 0 else None

    if resultado is None:
        estado = "Sin datos"
    elif cfg.operador == ">":
        estado = "Cumple" if resultado >= cfg.umbral else "No Cumple"
    elif cfg.operador == "<":
        estado = "Cumple" if resultado < cfg.umbral else "No Cumple"
    else:
        estado = "Desconocido"

    return {
        "metrica": metrica.nombre,
        "aplica": True,
        "denominador": denominador,
        "numerador": numerador,
        "resultado": round(resultado, 4) if resultado is not None else None,
        "umbral": cfg.umbral,
        "operador": cfg.operador,
        "estado": estado,
    }


def _calcular_total(df: pd.DataFrame, cfg) -> int:
    if cfg.criterio_total_fijo is not None:
        return int(cfg.criterio_total_fijo)
    if cfg.criterio_total:
        mascara = evaluar_grupos(df, cfg.criterio_total)
        return int(mascara.sum())
    return len(df)


def _calcular_favor(df: pd.DataFrame, cfg) -> int:
    if not cfg.criterio_favor:
        return 0
    mascara = evaluar_grupos(df, cfg.criterio_favor)
    return int(mascara.sum())


def calcular_cumplimientos_por_entidad(df: pd.DataFrame, metrica: Metrica,
                                       columna_entidad: str | None,
                                       identificadores_entidad: list[str]) -> dict:
    """
    Filtra el DataFrame para una sola entidad (usando la columna de
    separación y sus identificadores) y calcula el cumplimiento solo
    sobre ese subconjunto. Si no hay columna de entidad detectable,
    calcula sobre el DataFrame completo (mismo comportamiento del
    sistema original cuando no hay columna 'company').
    """
    if columna_entidad is None or columna_entidad not in df.columns:
        df_filtrado = df
    else:
        idents = [str(i).lower().strip() for i in identificadores_entidad]
        serie = df[columna_entidad].astype(str).str.lower().str.strip()
        mascara = serie.apply(lambda v: any(i in v for i in idents))
        df_filtrado = df[mascara]

    return calcular_cumplimiento(df_filtrado, metrica)