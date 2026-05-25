"""
pages/3_Dashboard_Semanal.py - Dashboard semanal
Agregación semanal con gráficos de tendencia
"""

import streamlit as st
from storage import load_carga_diaria, load_metas
from utils import (
    agregar_semanal, tasa_a_porcentaje, formatear_pesos,
    formatear_uf, render_ad_banner
)

# ─── Auth guard ────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.switch_page("app.py")

user = st.session_state.user
username = user["username"]
nombre = user.get("nombre", username)

st.markdown(f"# 📈 Dashboard Semanal — {nombre}")
st.markdown("<p style='color:#9E9E9E;'>Resumen semanal de indicadores y tendencias.</p>", unsafe_allow_html=True)

entries = load_carga_diaria(username)
metas = load_metas(username)

if not entries:
    st.warning("📭 No hay datos cargados. Ve a **Carga Diaria** para ingresar datos.")
    st.stop()

weekly = agregar_semanal(entries)

if not weekly:
    st.warning("⚠️ No se pudieron agregar datos semanales. Revisa que los registros tengan semana asignada.")
    st.stop()

# ─── Métricas acumuladas ──────────────────────────────────────────────
total_leads = sum(w.get("leads_nuevos", 0) for w in weekly)
total_ventas = sum(w.get("ventas", 0) for w in weekly)
total_uf = sum(w.get("uf_vendidas", 0) for w in weekly)
total_llamadas = sum(w.get("llamadas", 0) for w in weekly)
total_ingreso = sum(w.get("ingreso_bruto", 0) for w in weekly)

st.markdown("### 📊 Totales Acumulados")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📅 Semanas", len(weekly))
with col2:
    st.metric("👥 Leads Totales", int(total_leads))
with col3:
    st.metric("🏆 Ventas Totales", int(total_ventas))
with col4:
    st.metric("💰 UF Totales", f"{total_uf:,.1f}")

# ─── Gráfico de tendencia semanal ─────────────────────────────────────
st.markdown("### 📈 Tendencia Semanal")

import plotly.graph_objects as go
from plotly.subplots import make_subplots

semanas = [w.get("semana", f"Sem {i+1}") for i, w in enumerate(weekly)]
uf_data = [w.get("uf_vendidas", 0) for w in weekly]
ventas_data = [w.get("ventas", 0) for w in weekly]
leads_data = [w.get("leads_nuevos", 0) for w in weekly]
llamadas_data = [w.get("llamadas", 0) for w in weekly]

fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.12,
    subplot_titles=("UF Vendidas por Semana", "Actividad por Semana"),
)

fig.add_trace(
    go.Bar(x=semanas, y=uf_data, name="UF Vendidas",
           marker_color="#1E88E5", text=[f"{v:,.1f}" for v in uf_data],
           textposition="outside"),
    row=1, col=1
)

# Meta semanal de UF
meta_uf_semanal = metas.get("uf_vendidas_semana", 3750)
fig.add_hline(y=meta_uf_semanal, line_dash="dash", line_color="#FF9800",
              annotation_text=f"Meta: {meta_uf_semanal:,.0f} UF", row=1, col=1)

fig.add_trace(
    go.Scatter(x=semanas, y=leads_data, name="Leads",
               mode="lines+markers", line=dict(color="#42A5F5", width=2)),
    row=2, col=1
)
fig.add_trace(
    go.Scatter(x=semanas, y=llamadas_data, name="Llamadas",
               mode="lines+markers", line=dict(color="#66BB6A", width=2)),
    row=2, col=1
)

fig.update_layout(
    height=600,
    margin=dict(l=20, r=20, t=40, b=20),
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#E0E0E0"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
)
fig.update_xaxes(gridcolor="#333")
fig.update_yaxes(gridcolor="#333")

st.plotly_chart(fig, use_container_width=True)

# ─── Tasas semanales ──────────────────────────────────────────────────
st.markdown("### 📊 Tasas de Conversión Semanales")

tasas_fig = go.Figure()

tasa_contacto_data = [w.get("tasa_contacto", 0) * 100 for w in weekly]
tasa_agenda_data = [w.get("tasa_agendamiento", 0) * 100 for w in weekly]
tasa_show_data = [w.get("tasa_show", 0) * 100 for w in weekly]
tasa_reserva_data = [w.get("tasa_reserva", 0) * 100 for w in weekly]
tasa_cierre_data = [w.get("tasa_cierre", 0) * 100 for w in weekly]

tasas_fig.add_trace(go.Scatter(
    x=semanas, y=tasa_contacto_data, name="Contacto",
    mode="lines+markers", line=dict(width=2)))
tasas_fig.add_trace(go.Scatter(
    x=semanas, y=tasa_agenda_data, name="Agendamiento",
    mode="lines+markers", line=dict(width=2)))
tasas_fig.add_trace(go.Scatter(
    x=semanas, y=tasa_show_data, name="Show",
    mode="lines+markers", line=dict(width=2)))
tasas_fig.add_trace(go.Scatter(
    x=semanas, y=tasa_reserva_data, name="Reserva",
    mode="lines+markers", line=dict(width=2)))
tasas_fig.add_trace(go.Scatter(
    x=semanas, y=tasa_cierre_data, name="Cierre",
    mode="lines+markers", line=dict(width=2)))

# Líneas de meta
tasas_fig.add_hline(y=metas["tasa_contacto"] * 100, line_dash="dash",
                    line_color="#1E88E5", opacity=0.3)
tasas_fig.add_hline(y=metas["tasa_agendamiento"] * 100, line_dash="dash",
                    line_color="#EF5350", opacity=0.3)

tasas_fig.update_layout(
    height=450,
    margin=dict(l=20, r=20, t=20, b=20),
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#E0E0E0"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
    yaxis_title="Porcentaje (%)",
)
tasas_fig.update_xaxes(gridcolor="#333")
tasas_fig.update_yaxes(gridcolor="#333", ticksuffix="%")

st.plotly_chart(tasas_fig, use_container_width=True)

# ─── Tabla semanal detallada ──────────────────────────────────────────
st.markdown("### 📋 Detalle Semanal")

# Mostrar última semana primero
weekly_reversed = list(reversed(weekly))

for w in weekly_reversed:
    with st.expander(f"📅 {w['semana']} — {w['dias']} días"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**👥 Leads:** {w['leads_nuevos']}")
            st.markdown(f"**📞 Llamadas:** {w['llamadas']}")
            st.markdown(f"**🤝 Contactos:** {w['contactos']}")
            st.markdown(f"**📅 Agendas:** {w['agendas']}")
        with col2:
            st.markdown(f"**🏢 Reuniones:** {w['reuniones']}")
            st.markdown(f"**✅ Reservas:** {w['reservas']}")
            st.markdown(f"**🏆 Ventas:** {w['ventas']}")
            st.markdown(f"**💰 UF:** {w['uf_vendidas']:,.1f}")
        with col3:
            st.markdown(f"**📞 T. Contacto:** {tasa_a_porcentaje(w.get('tasa_contacto', 0))}")
            st.markdown(f"**📅 T. Agenda:** {tasa_a_porcentaje(w.get('tasa_agendamiento', 0))}")
            st.markdown(f"**🏆 T. Cierre:** {tasa_a_porcentaje(w.get('tasa_cierre', 0))}")
            st.markdown(f"**💵 Ingreso:** ${w.get('ingreso_bruto', 0):,.0f}")

# ─── Ad Banner ────────────────────────────────────────────────────────────
render_ad_banner()
