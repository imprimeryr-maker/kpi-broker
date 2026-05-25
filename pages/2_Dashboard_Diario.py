"""
pages/2_Dashboard_Diario.py - Dashboard diario
Muestra métricas del día actual vs metas
"""

import streamlit as st
from datetime import date
from storage import load_carga_diaria, load_metas
from utils import (
    tasa_a_porcentaje, formatear_pesos, formatear_uf,
    generar_diagnostico, generar_plan_accion, render_ad_banner
)

# ─── Auth guard ────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.switch_page("app.py")

user = st.session_state.user
username = user["username"]
nombre = user.get("nombre", username)

st.markdown(f"# 📊 Dashboard Diario — {nombre}")

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
            icon = "✅"
        elif pct >= 80:
            status = "orange"
            icon = "⚠️"
        else:
            status = "red"
            icon = "❌"
    else:
        status = "orange"
        icon = "➖"
        pct = 0

    st.markdown(f"""
    <div class="metric-card {status}">
        <div class="metric-label">{icon} {label}</div>
        <div class="metric-value">{val_str}</div>
        <div style="font-size:13px;color:#9E9E9E;">Meta: {meta_str} · {pct:.0f}%</div>
    </div>
    """, unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    metric_card("📞 Tasa de Contacto",
                e.get("tasa_contacto", 0), metas["tasa_contacto"])
    metric_card("📅 Tasa de Agendamiento",
                e.get("tasa_agendamiento", 0), metas["tasa_agendamiento"])
    metric_card("🏢 Tasa de Show",
                e.get("tasa_show", 0), metas["tasa_show"])

with col2:
    metric_card("✅ Tasa de Reserva",
                e.get("tasa_reserva", 0), metas["tasa_reserva"])
    metric_card("🏆 Tasa de Cierre",
                e.get("tasa_cierre", 0), metas["tasa_cierre"])
    metric_card("💰 UF Vendidas",
                e.get("uf_vendidas", 0), metas["uf_promedio_venta"], formato="uf")

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">👥 Leads</div>
        <div class="metric-value">{e.get('leads_nuevos', 0)}</div>
        <div style="font-size:13px;color:#9E9E9E;">Llamadas: {e.get('llamadas', 0)}</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">🤝 Contactos Efectivos</div>
        <div class="metric-value">{e.get('contactos', 0)}</div>
        <div style="font-size:13px;color:#9E9E9E;">Agendas: {e.get('agendas', 0)}</div>
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
        ("📅 Agendas", e.get("agendas", 0)),
        ("🏢 Reuniones", e.get("reuniones", 0)),
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

# ─── Ad Banner ────────────────────────────────────────────────────────────
render_ad_banner()
