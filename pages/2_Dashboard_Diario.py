"""
pages/2_Dashboard_Diario.py - Dashboard diario
Muestra métricas del día actual vs metas
"""

import streamlit as st
from datetime import date
from storage import load_carga_diaria, load_metas
from utils import (
    tasa_a_porcentaje, formatear_pesos, formatear_uf,
    generar_diagnostico, generar_plan_accion,
    generar_excel_report
)

# ─── Auth guard ────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.switch_page("app.py")

user = st.session_state.user
username = user["username"]
nombre = user.get("nombre", username)

st.markdown(f"# 📊 Dashboard Diario — {nombre}")

# ─── Botón descargar Excel ────────────────────────────────────────────
col_title, col_btn = st.columns([3, 1])
with col_btn:
    excel_bytes = generar_excel_report(username)
    st.download_button(
        label="📥 Descargar Excel",
        data=excel_bytes,
        file_name=f"informe_kpis_{username}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

entries = load_carga_diaria(username)
metas = load_metas(username)

today_str = date.today().strftime("%Y-%m-%d")

# Find today's entry or latest entry
today_entry = None
for e in entries:
    if e.get("fecha") == today_str:
        today_entry = e
        break

if not today_entry and entries:
    # Mostrar el último registro disponible
    today_entry = entries[-1]
    st.info(f"📌 No hay datos para hoy ({today_str}). Mostrando el último registro disponible: **{today_entry.get('fecha')}**")
elif not today_entry and not entries:
    st.warning("📭 No hay registros cargados. Ve a **Carga Diaria** para ingresar datos.")
    st.stop()

# ─── Métricas principales ─────────────────────────────────────────────
e = today_entry

st.markdown(f"""
<div style="background:#1E1E2E;border-radius:12px;padding:16px;margin:16px 0;">
    <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
            <span style="font-size:20px;">📅</span>
            <span style="font-size:18px;font-weight:600;">{e.get('dia', '')} — {e.get('fecha', '')}</span>
        </div>
        <div>
            <span style="font-size:14px;color:#9E9E9E;">{e.get('semana', '')}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Tarjetas de KPI vs Meta ──────────────────────────────────────────
st.markdown("### 🎯 KPIs vs Metas")

def metric_card(label, valor, meta, formato="tasa", unidad=""):
    """Render a KPI card comparing value vs goal."""
    if formato == "tasa":
        val_str = tasa_a_porcentaje(valor)
        meta_str = tasa_a_porcentaje(meta)
    elif formato == "uf":
        val_str = formatear_uf(valor)
        meta_str = formatear_uf(meta)
    elif formato == "pesos":
        val_str = formatear_pesos(valor)
        meta_str = formatear_pesos(meta)
    else:
        val_str = f"{valor}{unidad}"
        meta_str = f"{meta}{unidad}"

    if meta > 0 and valor is not None:
        pct = (valor / meta) * 100
        if pct >= 100:
            status = "green"
            color = "#4CAF50"
        elif pct >= 80:
            status = "orange"
            color = "#FF9800"
        else:
            status = "red"
            color = "#EF5350"
    else:
        status = "neutral"
        color = "#9E9E9E"
        pct = 0

    st.markdown(f"""
    <div class="metric-card {status}">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color:{color}">{val_str}</div>
        <div style="font-size:13px;color:#9E9E9E;">Meta: {meta_str} · {pct:.0f}%</div>
    </div>
    """, unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    metric_card("📞 Tasa de Contacto",
                e.get("tasa_contacto", 0), metas["tasa_contacto"])
    metric_card("📅 Tasa de Agendamiento",
                e.get("tasa_agendamiento", 0), metas["tasa_agendamiento"])
    metric_card("🏢 Tasa Efectividad",
                e.get("tasa_show", 0), metas["tasa_show"])

with col2:
    metric_card("✅ Tasa de Reserva",
                e.get("tasa_reserva", 0), metas["tasa_reserva"])
    metric_card("🏆 Tasa de Cierre",
                e.get("tasa_cierre", 0), metas["tasa_cierre"])
    metric_card("💰 UF Vendidas",
                e.get("uf_vendidas", 0), metas["uf_promedio_venta"], formato="uf")

with col3:
    # ─── Meta de Reuniones Agendadas ───────────────────────────────────
    meta_agend = metas.get("meta_reuniones_agendadas", 5)
    val_agend = e.get("agendas", 0) or 0
    if meta_agend > 0:
        pct_agend = (val_agend / meta_agend) * 100
        color_agend = "#4CAF50" if pct_agend >= 100 else ("#FF9800" if pct_agend >= 80 else "#EF5350")
        status_agend = "green" if pct_agend >= 100 else ("orange" if pct_agend >= 80 else "red")
    else:
        pct_agend = 0
        color_agend = "#9E9E9E"
        status_agend = "neutral"

    # ─── Meta de Reuniones Efectuadas ─────────────────────────────────
    meta_efect = metas.get("meta_reuniones_efectuadas", 3)
    val_efect = e.get("reuniones", 0) or 0
    if meta_efect > 0:
        pct_efect = (val_efect / meta_efect) * 100
        color_efect = "#4CAF50" if pct_efect >= 100 else ("#FF9800" if pct_efect >= 80 else "#EF5350")
        status_efect = "green" if pct_efect >= 100 else ("orange" if pct_efect >= 80 else "red")
    else:
        pct_efect = 0
        color_efect = "#9E9E9E"
        status_efect = "neutral"

    st.markdown(f"""
    <div class="metric-card {status_agend}">
        <div class="metric-label">📅 Reuniones Agendadas</div>
        <div class="metric-value" style="color:{color_agend}">{val_agend}</div>
        <div style="font-size:13px;color:#9E9E9E;">Meta: {meta_agend} · {pct_agend:.0f}%</div>
    </div>
    <div class="metric-card {status_efect}">
        <div class="metric-label">🏢 Reuniones Efectuadas</div>
        <div class="metric-value" style="color:{color_efect}">{val_efect}</div>
        <div style="font-size:13px;color:#9E9E9E;">Meta: {meta_efect} · {pct_efect:.0f}%</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">👥 Leads / Llamadas</div>
        <div class="metric-value">{e.get('leads_nuevos', 0)} / {e.get('llamadas', 0)}</div>
        <div style="font-size:13px;color:#9E9E9E;">Contactos: {e.get('contactos', 0)}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">✅ Reservas / Ventas</div>
        <div class="metric-value">{e.get('reservas', 0)} / {e.get('ventas', 0)}</div>
        <div style="font-size:13px;color:#9E9E9E;">UF: {formatear_uf(e.get('uf_vendidas', 0))}</div>
    </div>
    <div class="metric-card {'green' if (e.get('ingreso_bruto', 0) or 0) > 0 else ''}">
        <div class="metric-label">💵 Ingreso Bruto Estimado</div>
        <div class="metric-value">{formatear_pesos(e.get('ingreso_bruto', 0))}</div>
        <div style="font-size:13px;color:#9E9E9E;">UF: {formatear_uf(e.get('uf_vendidas', 0))}</div>
    </div>
    """, unsafe_allow_html=True)

# ─── Diagnóstico y Plan de Acción (a todo ancho) ────────────────────
st.markdown("### 📋 Diagnóstico del Día")

diagnostico = generar_diagnostico(e, metas)

st.markdown(f'<div class="diagnosis-box">{diagnostico}</div>', unsafe_allow_html=True)

# Plan de acción (siempre recalculado)
plan = generar_plan_accion(e, metas)

st.markdown(f'<div class="diagnosis-box" style="border-left-color:#FF9800;">{plan}</div>', unsafe_allow_html=True)

# ─── Embudo de Conversión ────────────────────────────────────────────
st.markdown("### 🔄 Embudo de Conversión")

if (e.get("leads_nuevos", 0) or 0) > 0:
    import plotly.graph_objects as go

    funnel_data = [
        ("👥 Leads", e.get("leads_nuevos", 0)),
        ("📞 Llamadas", e.get("llamadas", 0)),
        ("🤝 Contactos", e.get("contactos", 0)),
        ("📅 Reuniones Agendadas", e.get("agendas", 0)),
        ("🏢 Reuniones Efectuadas", e.get("reuniones", 0)),
        ("✅ Reservas", e.get("reservas", 0)),
        ("🏆 Ventas", e.get("ventas", 0)),
    ]

    fig = go.Figure(go.Funnel(
        y=[f[0] for f in funnel_data],
        x=[f[1] for f in funnel_data],
        textposition="inside",
        textinfo="value+percent initial",
        marker=dict(
            color=["#1E88E5", "#42A5F5", "#64B5F6", "#90CAF9", "#BBDEFB", "#E3F2FD", "#FF9800"],
        ),
    ))
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E0E0E0"),
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("📊 El embudo de conversión estará disponible cuando ingreses leads.")

# ─── Observaciones ────────────────────────────────────────────────────
if e.get("observaciones"):
    with st.expander("📝 Ver observaciones"):
        st.write(e["observaciones"])

