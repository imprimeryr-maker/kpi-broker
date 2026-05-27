"""
pages/5_Config_Metas.py - Configuración de metas
Permite a cada usuario ajustar sus propios objetivos
"""

import streamlit as st
from storage import load_metas, save_metas
from utils import formatear_pesos

# ─── Auth guard ────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.switch_page("app.py")

user = st.session_state.user
username = user["username"]
nombre = user.get("nombre", username)

st.markdown(f"# ⚙️ Configurar Metas — {nombre}")
st.markdown("<p style='color:#9E9E9E;'>Define los objetivos de cada indicador. Estos valores se usarán en los dashboards para evaluar el desempeño.</p>", unsafe_allow_html=True)

metas = load_metas(username)

st.markdown("""
<div style="background:#1E1E2E;border-radius:12px;padding:16px;margin:16px 0;">
    <h4>📌 ¿Cómo funcionan las metas?</h4>
    <p style="color:#B0B0B0;font-size:14px;">
        Las metas son los objetivos contra los que se comparan tus indicadores diarios.
        Si un indicador alcanza o supera la meta, se marca como <span style="color:#4CAF50;">✅</span>.
        Si está por debajo, se marca como <span style="color:#f44336;">❌</span> y se generan recomendaciones.
    </p>
</div>
""", unsafe_allow_html=True)

with st.form("config_metas_form"):
    st.markdown("#### 🎯 Tasas de Conversión (en %)")

    col1, col2, col3 = st.columns(3)
    with col1:
        tc = st.number_input("📞 Tasa de Contacto (%)",
            min_value=0.0, max_value=100.0,
            value=float(metas.get("tasa_contacto", 0.5) * 100),
            step=1.0, format="%.1f",
            help="% de llamadas que resultan en contacto efectivo")
    with col2:
        ta = st.number_input("📅 Tasa de Agendamiento (%)",
            min_value=0.0, max_value=100.0,
            value=float(metas.get("tasa_agendamiento", 0.15) * 100),
            step=1.0, format="%.1f",
            help="% de contactos que resultan en reunión agendada")
    with col3:
        ts = st.number_input("🏢 Tasa de Efectividad (%)",
            min_value=0.0, max_value=100.0,
            value=float(metas.get("tasa_show", 0.10) * 100),
            step=1.0, format="%.1f",
            help="% de reuniones agendadas que realmente se efectúan")

    col1, col2, col3 = st.columns(3)
    with col1:
        tr = st.number_input("✅ Tasa de Reserva (%)",
            min_value=0.0, max_value=100.0,
            value=float(metas.get("tasa_reserva", 0.70) * 100),
            step=1.0, format="%.1f",
            help="% de reuniones que resultan en reserva")
    with col2:
        tci = st.number_input("🏆 Tasa de Cierre (%)",
            min_value=0.0, max_value=100.0,
            value=float(metas.get("tasa_cierre", 0.70) * 100),
            step=1.0, format="%.1f",
            help="% de reservas que se convierten en ventas")
    with col3:
        cobertura = st.number_input("📞 Cobertura de Llamadas (%)",
            min_value=0.0, max_value=100.0,
            value=float(metas.get("cobertura_llamados", 1.0) * 100),
            step=5.0, format="%.0f",
            help="% de leads que deben ser llamados")

    st.divider()
    st.markdown("#### 🎯 Metas de Reuniones")

    col1, col2, col3 = st.columns(3)
    with col1:
        meta_reu_agend = st.number_input("📅 Reuniones Agendadas por Día",
            min_value=0,
            value=int(metas.get("meta_reuniones_agendadas", 5)),
            step=1, format="%d",
            help="Cuántas reuniones deberías agendar cada día")
    with col2:
        meta_reu_efect = st.number_input("🏢 Reuniones Efectuadas por Día",
            min_value=0,
            value=int(metas.get("meta_reuniones_efectuadas", 3)),
            step=1, format="%d",
            help="Cuántas reuniones deberías efectivamente realizar cada día")
    with col3:
        st.markdown("<div style='padding-top:28px;'></div>", unsafe_allow_html=True)
        st.caption("📌 Las reuniones agendadas son las que programas; las efectuadas son las que realmente ocurren.")

    st.divider()
    st.markdown("#### 💰 Metas Comerciales")

    col1, col2, col3 = st.columns(3)
    with col1:
        uf_sem = st.number_input("💰 UF Vendidas por Semana",
            min_value=0.0,
            value=float(metas.get("uf_vendidas_semana", 3750)),
            step=50.0, format="%.1f",
            help="Meta semanal de UF vendidas")
    with col2:
        uf_prom = st.number_input("📊 UF Promedio por Venta",
            min_value=0.0,
            value=float(metas.get("uf_promedio_venta", 3500)),
            step=100.0, format="%.1f",
            help="UF promedio esperado por cada venta")
    with col3:
        precio_uf = st.number_input("💵 Precio de la UF ($)",
            min_value=0,
            value=int(metas.get("precio_uf", 24000)),
            step=100, format="%d",
            help="Valor de la UF en pesos chilenos")

    st.divider()
    st.markdown(f"**💵 Con estos valores, el ingreso estimado semanal es:** {formatear_pesos(uf_sem * precio_uf)}")

    saved = st.form_submit_button("💾 Guardar Metas", use_container_width=True)

if saved:
    metas.update({
        "tasa_contacto": tc / 100.0,
        "tasa_agendamiento": ta / 100.0,
        "tasa_show": ts / 100.0,
        "tasa_reserva": tr / 100.0,
        "tasa_cierre": tci / 100.0,
        "cobertura_llamados": cobertura / 100.0,
        "uf_vendidas_semana": uf_sem,
        "uf_promedio_venta": uf_prom,
        "precio_uf": precio_uf,
        "meta_reuniones_agendadas": meta_reu_agend,
        "meta_reuniones_efectuadas": meta_reu_efect,
    })
    save_metas(username, metas)
    st.success("✅ Metas guardadas exitosamente.")
    st.balloons()

# ─── Vista previa de las metas ────────────────────────────────────────
st.markdown("### 📋 Resumen de Metas Actuales")

metas_actuales = load_metas(username)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📞 Tasa Contacto", f"{metas_actuales['tasa_contacto']:.0%}")
    st.metric("📅 Tasa Agendamiento", f"{metas_actuales['tasa_agendamiento']:.0%}")
    st.metric("🏢 Tasa Efectividad", f"{metas_actuales['tasa_show']:.0%}")
with col2:
    st.metric("✅ Tasa de Reserva", f"{metas_actuales['tasa_reserva']:.0%}")
    st.metric("🏆 Tasa de Cierre", f"{metas_actuales['tasa_cierre']:.0%}")
    st.metric("📞 Cobertura", f"{metas_actuales['cobertura_llamados']:.0%}")
with col3:
    st.metric("💰 UF/Semana", f"{metas_actuales['uf_vendidas_semana']:,.1f}")
    st.metric("📊 UF Promedio/Venta", f"{metas_actuales['uf_promedio_venta']:,.1f}")
    st.metric("💵 Precio UF", formatear_pesos(metas_actuales['precio_uf']))

st.markdown("#### 📅 Metas de Reuniones")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📅 Reuniones Agendadas/Día", f"{metas_actuales.get('meta_reuniones_agendadas', 5)}")
with col2:
    st.metric("🏢 Reuniones Efectuadas/Día", f"{metas_actuales.get('meta_reuniones_efectuadas', 3)}")
with col3:
    st.metric("📊 Tasa Efectividad", f"{metas_actuales['tasa_show']:.0%}")

