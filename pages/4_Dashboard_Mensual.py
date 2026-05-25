"""
pages/4_Dashboard_Mensual.py - Dashboard mensual
Agregación mensual con tendencias y comparativas
"""

import streamlit as st
from storage import load_carga_diaria, load_metas
from utils import (
    agregar_mensual, tasa_a_porcentaje, formatear_pesos, formatear_uf,
    render_ad_banner
)

# ─── Auth guard ────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.switch_page("app.py")

user = st.session_state.user
username = user["username"]
nombre = user.get("nombre", username)

st.markdown(f"# 📅 Dashboard Mensual — {nombre}")
st.markdown("<p style='color:#9E9E9E;'>Resumen mensual de indicadores y tendencias.</p>", unsafe_allow_html=True)

entries = load_carga_diaria(username)
metas = load_metas(username)

if not entries:
    st.warning("📭 No hay datos cargados. Ve a **Carga Diaria** para ingresar datos.")
    st.stop()

monthly = agregar_mensual(entries)

if not monthly:
    st.warning("⚠️ No se pudieron agregar datos mensuales.")
    st.stop()

# ─── Resumen mensual ──────────────────────────────────────────────────
st.markdown("### 📊 Resumen Mensual")

total_leads = sum(m.get("leads_nuevos", 0) for m in monthly)
total_ventas = sum(m.get("ventas", 0) for m in monthly)
total_uf = sum(m.get("uf_vendidas", 0) for m in monthly)
total_ingreso = sum(m.get("ingreso_bruto", 0) for m in monthly)
promedio_uf_venta = total_uf / total_ventas if total_ventas > 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📅 Meses", len(monthly))
with col2:
    st.metric("👥 Leads Totales", int(total_leads))
with col3:
    st.metric("🏆 Ventas Totales", int(total_ventas))
with col4:
    st.metric("💰 UF Totales", f"{total_uf:,.1f}")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("💵 Ingreso Total", formatear_pesos(total_ingreso))
with col2:
    st.metric("📊 UF Promedio/Venta", f"{promedio_uf_venta:,.1f}")
with col3:
    st.metric("🎯 Meta UF/Mes", formatear_uf(metas.get("uf_vendidas_semana", 3750) * 4))
with col4:
    tasa_conv = (total_ventas / total_leads * 100) if total_leads > 0 else 0
    st.metric("🔄 Conversión Total", f"{tasa_conv:.1f}%")

# ─── Gráficos mensuales ───────────────────────────────────────────────
st.markdown("### 📈 Tendencias Mensuales")

import plotly.graph_objects as go
from plotly.subplots import make_subplots

meses = [m.get("mes_nombre", f"Mes {m.get('mes_numero', '?')}") for m in monthly]
uf_mensual = [m.get("uf_vendidas", 0) for m in monthly]
ventas_mensual = [m.get("ventas", 0) for m in monthly]
leads_mensual = [m.get("leads_nuevos", 0) for m in monthly]
dias_mensual = [m.get("dias", 0) for m in monthly]

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=("UF Vendidas por Mes", "Ventas por Mes",
                    "Leads por Mes", "Días Registrados"),
    specs=[
        [{"type": "bar"}, {"type": "bar"}],
        [{"type": "bar"}, {"type": "bar"}],
    ],
)

fig.add_trace(
    go.Bar(x=meses, y=uf_mensual, name="UF",
           marker_color="#1E88E5",
           text=[f"{v:,.0f}" for v in uf_mensual],
           textposition="outside"),
    row=1, col=1
)

fig.add_trace(
    go.Bar(x=meses, y=ventas_mensual, name="Ventas",
           marker_color="#66BB6A",
           text=[str(v) for v in ventas_mensual],
           textposition="outside"),
    row=1, col=2
)

fig.add_trace(
    go.Bar(x=meses, y=leads_mensual, name="Leads",
           marker_color="#42A5F5",
           text=[str(v) for v in leads_mensual],
           textposition="outside"),
    row=2, col=1
)

fig.add_trace(
    go.Bar(x=meses, y=dias_mensual, name="Días",
           marker_color="#FF9800",
           text=[str(v) for v in dias_mensual],
           textposition="outside"),
    row=2, col=2
)

fig.update_layout(
    height=600,
    margin=dict(l=20, r=20, t=40, b=20),
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#E0E0E0"),
    showlegend=False,
    hovermode="x unified",
)
fig.update_xaxes(gridcolor="#333")
fig.update_yaxes(gridcolor="#333")

st.plotly_chart(fig, use_container_width=True)

# ─── Tasas mensuales ──────────────────────────────────────────────────
st.markdown("### 📊 Tasas de Conversión Mensuales")

tasas_fig = go.Figure()

tasa_contacto_m = [m.get("tasa_contacto", 0) * 100 for m in monthly]
tasa_agenda_m = [m.get("tasa_agendamiento", 0) * 100 for m in monthly]
tasa_show_m = [m.get("tasa_show", 0) * 100 for m in monthly]
tasa_reserva_m = [m.get("tasa_reserva", 0) * 100 for m in monthly]
tasa_cierre_m = [m.get("tasa_cierre", 0) * 100 for m in monthly]

tasas_fig.add_trace(go.Bar(
    x=meses, y=tasa_contacto_m, name="Contacto",
    marker_color="#1E88E5"))
tasas_fig.add_trace(go.Bar(
    x=meses, y=tasa_agenda_m, name="Agendamiento",
    marker_color="#42A5F5"))
tasas_fig.add_trace(go.Bar(
    x=meses, y=tasa_show_m, name="Show",
    marker_color="#64B5F6"))
tasas_fig.add_trace(go.Bar(
    x=meses, y=tasa_reserva_m, name="Reserva",
    marker_color="#90CAF9"))
tasas_fig.add_trace(go.Bar(
    x=meses, y=tasa_cierre_m, name="Cierre",
    marker_color="#FF9800"))

tasas_fig.update_layout(
    barmode="group",
    height=400,
    margin=dict(l=20, r=20, t=20, b=20),
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#E0E0E0"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    yaxis_title="Porcentaje (%)",
)
tasas_fig.update_xaxes(gridcolor="#333")
tasas_fig.update_yaxes(gridcolor="#333", ticksuffix="%")

st.plotly_chart(tasas_fig, use_container_width=True)

# ─── Detalle por mes ──────────────────────────────────────────────────
st.markdown("### 📋 Detalle por Mes")

monthly_reversed = list(reversed(monthly))

for m in monthly_reversed:
    with st.expander(f"📅 {m['mes_nombre']} — {m['dias']} días"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**👥 Leads:** {m['leads_nuevos']}")
            st.markdown(f"**📞 Llamadas:** {m['llamadas']}")
            st.markdown(f"**🤝 Contactos:** {m['contactos']}")
            st.markdown(f"**📅 Agendas:** {m['agendas']}")
        with col2:
            st.markdown(f"**🏢 Reuniones:** {m['reuniones']}")
            st.markdown(f"**✅ Reservas:** {m['reservas']}")
            st.markdown(f"**🏆 Ventas:** {m['ventas']}")
            st.markdown(f"**💰 UF:** {m['uf_vendidas']:,.1f}")
        with col3:
            st.markdown(f"**📞 T. Contacto:** {tasa_a_porcentaje(m.get('tasa_contacto', 0))}")
            st.markdown(f"**📅 T. Agenda:** {tasa_a_porcentaje(m.get('tasa_agendamiento', 0))}")
            st.markdown(f"**🏆 T. Cierre:** {tasa_a_porcentaje(m.get('tasa_cierre', 0))}")
            st.markdown(f"**💵 Ingreso:** ${m.get('ingreso_bruto', 0):,.0f}")

# ─── Ad Banner ────────────────────────────────────────────────────────────
render_ad_banner()
