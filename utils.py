"""
utils.py - Cálculos de KPIs, diagnóstico, fechas en español
"""

from datetime import datetime, date
import math

# ─── Días de la semana en español ─────────────────────────────────────

DIAS_SEMANA = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo",
}

MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

def get_dia_semana(fecha_str: str) -> str:
    """Return day name in Spanish from a date string (YYYY-MM-DD)."""
    try:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d")
        return DIAS_SEMANA[dt.weekday()]
    except (ValueError, KeyError):
        return ""

def get_semana_numero(fecha_str: str) -> str:
    """Return week number as 'Sem X' from a date string."""
    try:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d")
        # ISO week number
        week_num = dt.isocalendar()[1]
        return f"Sem {week_num}"
    except (ValueError):
        return ""

def get_mes_nombre(fecha_str: str) -> str:
    """Return month name in Spanish."""
    try:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d")
        return MESES[dt.month]
    except (ValueError, KeyError):
        return ""

def get_mes_numero(fecha_str: str) -> int:
    """Return month number."""
    try:
        dt = datetime.strptime(fecha_str, "%Y-%m-%d")
        return dt.month
    except ValueError:
        return 0

# ─── Cálculos de KPIs ─────────────────────────────────────────────────

def calcular_tasas(entry: dict) -> dict:
    """
    Calculate all rates from raw data in an entry.
    Returns the entry with calculated fields updated.
    """
    e = dict(entry)  # Copy to avoid mutation

    leads = e.get("leads_nuevos", 0) or 0
    llamadas = e.get("llamadas", 0) or 0
    contactos = e.get("contactos", 0) or 0
    agendas = e.get("agendas", 0) or 0
    reuniones = e.get("reuniones", 0) or 0
    reservas = e.get("reservas", 0) or 0
    ventas = e.get("ventas", 0) or 0
    uf_vendidas = e.get("uf_vendidas", 0) or 0.0

    # Tasa de Contacto = Contactos / Llamadas
    if llamadas > 0:
        e["tasa_contacto"] = round(contactos / llamadas, 4)
    else:
        e["tasa_contacto"] = 0.0

    # Tasa de Agendamiento = Agendas / Contactos
    if contactos > 0:
        e["tasa_agendamiento"] = round(agendas / contactos, 4)
    else:
        e["tasa_agendamiento"] = 0.0

    # Tasa de Show = Reuniones / Agendas
    if agendas > 0:
        e["tasa_show"] = round(reuniones / agendas, 4)
    else:
        e["tasa_show"] = 0.0

    # Tasa de Reserva = Reservas / Reuniones
    if reuniones > 0:
        e["tasa_reserva"] = round(reservas / reuniones, 4)
    else:
        e["tasa_reserva"] = 0.0

    # Tasa de Cierre = Ventas / Reservas
    if reservas > 0:
        e["tasa_cierre"] = round(ventas / reservas, 4)
    else:
        e["tasa_cierre"] = 0.0

    return e

def calcular_ingreso(entry: dict, precio_uf: float = 24000.0) -> float:
    """Calculate gross income from UF sold."""
    uf = entry.get("uf_vendidas", 0) or 0
    return round(uf * precio_uf, 0)

# ─── Diagnóstico Diario ───────────────────────────────────────────────

def generar_diagnostico(entry: dict, metas: dict) -> str:
    """
    Generate a focused daily diagnosis.
    Returns a concise diagnosis with top 2 critical issues sorted by severity.
    """
    e = calcular_tasas(entry)

    checks = [
        ("tasa_contacto", "📞 Contacto", metas.get("tasa_contacto", 0.5)),
        ("tasa_agendamiento", "📅 Agendamiento", metas.get("tasa_agendamiento", 0.15)),
        ("tasa_show", "🏢 Show", metas.get("tasa_show", 0.10)),
        ("tasa_reserva", "✅ Reserva", metas.get("tasa_reserva", 0.70)),
        ("tasa_cierre", "🏆 Cierre", metas.get("tasa_cierre", 0.70)),
    ]

    issues = []
    ok_count = 0
    total_checks = 0

    for key, short_name, goal in checks:
        val = e.get(key, 0)
        total_checks += 1
        if val >= goal and goal > 0:
            ok_count += 1
        elif goal > 0:
            deficit_pp = (goal - val) * 100  # percentage points
            deficit_pct = (goal - val) / goal * 100
            issues.append({
                "severity": deficit_pct,
                "text": f"{short_name}: {val:.1%} vs meta {goal:.0%} ({deficit_pp:.0f}pp abajo)"
            })

    # Coverage check
    leads = e.get("leads_nuevos", 0) or 0
    llamadas = e.get("llamadas", 0) or 0
    if leads > 0 and llamadas < leads:
        cobertura_pct = (leads - llamadas) / leads * 100
        issues.append({
            "severity": cobertura_pct,
            "text": f"📞 Cobertura: {llamadas}/{leads} leads llamados ({llamadas/leads:.0%})"
        })

    if not issues:
        return "✅ Todo en orden — todos los indicadores cumplen meta"

    # Sort by severity (biggest deficit first)
    issues.sort(key=lambda x: x["severity"], reverse=True)

    # Header según desempeño
    pct_ok = ok_count / total_checks * 100 if total_checks > 0 else 0
    if pct_ok >= 80:
        header = "🟡 Buen desempeño general, enfócate en:"
    elif pct_ok >= 50:
        header = "🟠 Desempeño regular — prioriza:"
    else:
        header = "🔴 Desempeño crítico — atiende urgente:"

    # Show only top 2 most critical issues
    top_issues = [i["text"] for i in issues[:2]]

    return header + "\n" + "\n".join(top_issues)

def generar_plan_accion(entry: dict, metas: dict) -> str:
    """Generate focused corrective actions, prioritized by severity."""
    e = calcular_tasas(entry)

    action_map = [
        ("tasa_contacto", metas.get("tasa_contacto", 0.5),
         "Capacitar en apertura de llamadas y manejo de objeciones"),
        ("tasa_agendamiento", metas.get("tasa_agendamiento", 0.15),
         "Reforzar propuesta de valor y beneficio de la reunión"),
        ("tasa_show", metas.get("tasa_show", 0.10),
         "Calificar mejor las agendas antes de agendar"),
        ("tasa_reserva", metas.get("tasa_reserva", 0.70),
         "Seguimiento post-reunión con ofertas personalizadas"),
        ("tasa_cierre", metas.get("tasa_cierre", 0.70),
         "Reforzar cierre con urgencia y beneficios concretos"),
    ]

    suggestions = []
    for key, goal, action in action_map:
        val = e.get(key, 0)
        if val < goal and goal > 0:
            deficit_pct = (goal - val) / goal * 100
            suggestions.append({"severity": deficit_pct, "action": action})

    # Coverage check
    leads = e.get("leads_nuevos", 0) or 0
    llamadas = e.get("llamadas", 0) or 0
    if leads > 0 and llamadas < leads:
        cobertura_pct = (leads - llamadas) / leads * 100
        suggestions.append({
            "severity": cobertura_pct,
            "action": "Aumentar cobertura: llamar a todos los leads del día"
        })

    if not suggestions:
        return "✅ Mantener estrategia actual — todos los indicadores cumplen meta"

    # Sort by severity and show top 2
    suggestions.sort(key=lambda x: x["severity"], reverse=True)

    return "📋 Prioriza:\n" + "\n".join(f"• {s['action']}" for s in suggestions[:2])

# ─── Agregaciones ─────────────────────────────────────────────────────

def agregar_semanal(entries: list) -> list:
    """Aggregate daily entries by week."""
    from collections import OrderedDict
    weeks = OrderedDict()

    for e in entries:
        semana = e.get("semana", "")
        if not semana:
            continue
        if semana not in weeks:
            weeks[semana] = {
                "semana": semana,
                "dias": 0,
                "leads_nuevos": 0, "llamadas": 0, "contactos": 0,
                "agendas": 0, "reuniones": 0, "reservas": 0,
                "ventas": 0, "uf_vendidas": 0.0, "ingreso_bruto": 0.0,
            }
        w = weeks[semana]
        w["dias"] += 1
        w["leads_nuevos"] += e.get("leads_nuevos", 0) or 0
        w["llamadas"] += e.get("llamadas", 0) or 0
        w["contactos"] += e.get("contactos", 0) or 0
        w["agendas"] += e.get("agendas", 0) or 0
        w["reuniones"] += e.get("reuniones", 0) or 0
        w["reservas"] += e.get("reservas", 0) or 0
        w["ventas"] += e.get("ventas", 0) or 0
        w["uf_vendidas"] += e.get("uf_vendidas", 0) or 0.0
        w["ingreso_bruto"] += e.get("ingreso_bruto", 0) or 0.0

    # Calculate weekly rates
    result = []
    for w in weeks.values():
        if w["llamadas"] > 0:
            w["tasa_contacto"] = round(w["contactos"] / w["llamadas"], 4)
        else:
            w["tasa_contacto"] = 0
        if w["contactos"] > 0:
            w["tasa_agendamiento"] = round(w["agendas"] / w["contactos"], 4)
        else:
            w["tasa_agendamiento"] = 0
        if w["agendas"] > 0:
            w["tasa_show"] = round(w["reuniones"] / w["agendas"], 4)
        else:
            w["tasa_show"] = 0
        if w["reuniones"] > 0:
            w["tasa_reserva"] = round(w["reservas"] / w["reuniones"], 4)
        else:
            w["tasa_reserva"] = 0
        if w["reservas"] > 0:
            w["tasa_cierre"] = round(w["ventas"] / w["reservas"], 4)
        else:
            w["tasa_cierre"] = 0
        result.append(w)

    return result

def agregar_mensual(entries: list) -> list:
    """Aggregate daily entries by month."""
    from collections import OrderedDict
    months = OrderedDict()

    for e in entries:
        mes = get_mes_numero(e.get("fecha", ""))
        if not mes:
            continue
        key = f"{mes:02d}"
        if key not in months:
            months[key] = {
                "mes_numero": mes,
                "mes_nombre": get_mes_nombre(e.get("fecha", "")),
                "dias": 0,
                "leads_nuevos": 0, "llamadas": 0, "contactos": 0,
                "agendas": 0, "reuniones": 0, "reservas": 0,
                "ventas": 0, "uf_vendidas": 0.0, "ingreso_bruto": 0.0,
            }
        m = months[key]
        m["dias"] += 1
        m["leads_nuevos"] += e.get("leads_nuevos", 0) or 0
        m["llamadas"] += e.get("llamadas", 0) or 0
        m["contactos"] += e.get("contactos", 0) or 0
        m["agendas"] += e.get("agendas", 0) or 0
        m["reuniones"] += e.get("reuniones", 0) or 0
        m["reservas"] += e.get("reservas", 0) or 0
        m["ventas"] += e.get("ventas", 0) or 0
        m["uf_vendidas"] += e.get("uf_vendidas", 0) or 0.0
        m["ingreso_bruto"] += e.get("ingreso_bruto", 0) or 0.0

    result = []
    for m in months.values():
        if m["llamadas"] > 0:
            m["tasa_contacto"] = round(m["contactos"] / m["llamadas"], 4)
        else:
            m["tasa_contacto"] = 0
        if m["contactos"] > 0:
            m["tasa_agendamiento"] = round(m["agendas"] / m["contactos"], 4)
        else:
            m["tasa_agendamiento"] = 0
        if m["agendas"] > 0:
            m["tasa_show"] = round(m["reuniones"] / m["agendas"], 4)
        else:
            m["tasa_show"] = 0
        if m["reuniones"] > 0:
            m["tasa_reserva"] = round(m["reservas"] / m["reuniones"], 4)
        else:
            m["tasa_reserva"] = 0
        if m["reservas"] > 0:
            m["tasa_cierre"] = round(m["ventas"] / m["reservas"], 4)
        else:
            m["tasa_cierre"] = 0
        result.append(m)

    # Sort by month number
    result.sort(key=lambda x: x["mes_numero"])
    return result

# ─── Exportar a Excel ───────────────────────────────────────────────────

def generar_excel_report(username: str) -> bytes:
    """
    Generate an Excel report with 3 sheets: Diario, Semanal, Mensual.
    Returns the Excel file as bytes.
    """
    import pandas as pd
    from io import BytesIO
    from storage import load_carga_diaria, load_metas

    entries = load_carga_diaria(username)

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # ─── Sheet 1: Diario ──────────────────────────────────────────
        if entries:
            # Ensure all calculated fields exist
            metas = load_metas(username)
            precio_uf = metas.get("precio_uf", 24000)
            processed = []
            for e in entries:
                e = calcular_tasas(e)
                e["ingreso_bruto"] = calcular_ingreso(e, precio_uf)
                processed.append(e)

            daily_cols = [
                "fecha", "dia", "semana",
                "leads_nuevos", "llamadas", "contactos",
                "tasa_contacto", "agendas", "tasa_agendamiento",
                "reuniones", "tasa_show", "reservas", "tasa_reserva",
                "ventas", "tasa_cierre",
                "uf_vendidas", "ingreso_bruto",
                "observaciones", "accion_correctiva",
            ]
            df_daily = pd.DataFrame(processed)
            # Keep only columns that exist
            df_daily = df_daily[[c for c in daily_cols if c in df_daily.columns]]
            # Format rates as percentages
            rate_cols = ["tasa_contacto", "tasa_agendamiento", "tasa_show", "tasa_reserva", "tasa_cierre"]
            for col in rate_cols:
                if col in df_daily.columns:
                    df_daily[col] = df_daily[col].apply(lambda x: f"{x*100:.1f}%" if x else "0.0%")
            # Format ingreso_bruto as currency
            if "ingreso_bruto" in df_daily.columns:
                df_daily["ingreso_bruto"] = df_daily["ingreso_bruto"].apply(
                    lambda x: f"${x:,.0f}" if x else "$0"
                )
            df_daily.to_excel(writer, sheet_name="Diario", index=False)
        else:
            pd.DataFrame({"Mensaje": ["No hay datos diarios cargados."]}).to_excel(
                writer, sheet_name="Diario", index=False
            )

        # ─── Sheet 2: Semanal ─────────────────────────────────────────
        if entries:
            weekly = agregar_semanal(entries)
            weekly_cols = [
                "semana", "dias",
                "leads_nuevos", "llamadas", "contactos", "agendas",
                "reuniones", "reservas", "ventas",
                "uf_vendidas", "ingreso_bruto",
                "tasa_contacto", "tasa_agendamiento", "tasa_show",
                "tasa_reserva", "tasa_cierre",
            ]
            df_weekly = pd.DataFrame(weekly)
            df_weekly = df_weekly[[c for c in weekly_cols if c in df_weekly.columns]]
            rate_cols = ["tasa_contacto", "tasa_agendamiento", "tasa_show", "tasa_reserva", "tasa_cierre"]
            for col in rate_cols:
                if col in df_weekly.columns:
                    df_weekly[col] = df_weekly[col].apply(lambda x: f"{x*100:.1f}%" if x else "0.0%")
            if "ingreso_bruto" in df_weekly.columns:
                df_weekly["ingreso_bruto"] = df_weekly["ingreso_bruto"].apply(
                    lambda x: f"${x:,.0f}" if x else "$0"
                )
            df_weekly.to_excel(writer, sheet_name="Semanal", index=False)
        else:
            pd.DataFrame({"Mensaje": ["No hay datos semanales disponibles."]}).to_excel(
                writer, sheet_name="Semanal", index=False
            )

        # ─── Sheet 3: Mensual ─────────────────────────────────────────
        if entries:
            monthly = agregar_mensual(entries)
            monthly_cols = [
                "mes_nombre", "mes_numero", "dias",
                "leads_nuevos", "llamadas", "contactos", "agendas",
                "reuniones", "reservas", "ventas",
                "uf_vendidas", "ingreso_bruto",
                "tasa_contacto", "tasa_agendamiento", "tasa_show",
                "tasa_reserva", "tasa_cierre",
            ]
            df_monthly = pd.DataFrame(monthly)
            df_monthly = df_monthly[[c for c in monthly_cols if c in df_monthly.columns]]
            rate_cols = ["tasa_contacto", "tasa_agendamiento", "tasa_show", "tasa_reserva", "tasa_cierre"]
            for col in rate_cols:
                if col in df_monthly.columns:
                    df_monthly[col] = df_monthly[col].apply(lambda x: f"{x*100:.1f}%" if x else "0.0%")
            if "ingreso_bruto" in df_monthly.columns:
                df_monthly["ingreso_bruto"] = df_monthly["ingreso_bruto"].apply(
                    lambda x: f"${x:,.0f}" if x else "$0"
                )
            df_monthly.to_excel(writer, sheet_name="Mensual", index=False)
        else:
            pd.DataFrame({"Mensaje": ["No hay datos mensuales disponibles."]}).to_excel(
                writer, sheet_name="Mensual", index=False
            )

    output.seek(0)
    return output.read()


# ─── Formateo ─────────────────────────────────────────────────────────

def formatear_numero(valor, decimales: int = 0) -> str:
    """Format number with thousands separator."""
    if valor is None:
        return "0"
    try:
        return f"{float(valor):,.{decimales}f}"
    except (ValueError, TypeError):
        return str(valor)

def formatear_uf(valor) -> str:
    """Format UF value."""
    return formatear_numero(valor, 1)

def formatear_pesos(valor) -> str:
    """Format CLP value."""
    if valor is None:
        return "$0"
    try:
        return f"${float(valor):,.0f}"
    except (ValueError, TypeError):
        return str(valor)

def tasa_a_porcentaje(tasa) -> str:
    """Convert rate (0.xx) to percentage string."""
    if tasa is None:
        return "0%"
    try:
        return f"{float(tasa) * 100:.1f}%"
    except (ValueError, TypeError):
        return str(tasa)


