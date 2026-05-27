"""
pages/1_Carga_Diaria.py - Formulario de carga diaria
Permite ingresar datos diarios con cálculo automático de tasas
"""

import streamlit as st
from datetime import datetime, date
from storage import load_carga_diaria, add_entry, delete_entry, load_metas
from utils import (
    get_dia_semana, get_semana_numero, calcular_tasas,
    calcular_ingreso, generar_diagnostico, generar_plan_accion,
    formatear_numero, tasa_a_porcentaje
)

# ─── Auth guard ────────────────────────────────────────────────────────
if "user" not in st.session_state or st.session_state.user is None:
    st.switch_page("app.py")

user = st.session_state.user
username = user["username"]
nombre = user.get("nombre", username)

st.markdown(f"# 📥 Carga Diaria — {nombre}")
st.markdown("<p style='color:#9E9E9E;'>Ingresa los datos del día y las tasas se calcularán automáticamente.</p>", unsafe_allow_html=True)

metas = load_metas(username)
entries = load_carga_diaria(username)

# ─── Tabs: Nuevo registro / Historial ─────────────────────────────────
tab1, tab2 = st.tabs(["📝 Nuevo Registro", "📋 Historial"])

with tab1:
    # Date selector - default to today
    today = date.today()
    fecha = st.date_input("📅 Fecha", value=today, max_value=today)

    fecha_str = fecha.strftime("%Y-%m-%d")
    dia_semana = get_dia_semana(fecha_str)
    semana_num = get_semana_numero(fecha_str)

    st.markdown(f"""
    <div style="background:#1E1E2E;border-radius:8px;padding:12px;margin:8px 0;">
        <b>{dia_semana}</b> — Semana {semana_num}
    </div>
    """, unsafe_allow_html=True)

    # Check if editing existing entry
    existing = None
    for e in entries:
        if e.get("fecha") == fecha_str:
            existing = e
            break

    if existing:
        st.info(f"✏️ Editando datos del {fecha_str} — se actualizará el registro existente.")

    # ─── Formulario en dos columnas ────────────────────────────────────
    with st.form("carga_diaria_form"):
        st.markdown("#### 📊 Datos de Actividad")

        col1, col2, col3 = st.columns(3)
        with col1:
            leads = st.number_input("👥 Leads Nuevos",
                min_value=0, value=existing.get("leads_nuevos", 0) if existing else 0, step=1)
        with col2:
            llamadas = st.number_input("📞 Llamadas Realizadas",
                min_value=0, value=existing.get("llamadas", 0) if existing else 0, step=1)
        with col3:
            contactos = st.number_input("🤝 Contactos Efectivos",
                min_value=0, value=existing.get("contactos", 0) if existing else 0, step=1)

        col1, col2, col3 = st.columns(3)
        with col1:
            agendas = st.number_input("📅 Reuniones Agendadas",
                min_value=0, value=existing.get("agendas", 0) if existing else 0, step=1,
                help="Agendas programadas para el día")
        with col2:
            reuniones = st.number_input("🏢 Reuniones Efectuadas",
                min_value=0, value=existing.get("reuniones", 0) if existing else 0, step=1,
                help="Reuniones que realmente se efectuaron")
        with col3:
            reservas = st.number_input("✅ Reservas",
                min_value=0, value=existing.get("reservas", 0) if existing else 0, step=1)

        col1, col2, col3 = st.columns(3)
        with col1:
            ventas = st.number_input("🏆 Ventas / Promesas",
                min_value=0, value=existing.get("ventas", 0) if existing else 0, step=1)
        with col2:
            uf_vendidas = st.number_input("💰 UF Vendidas",
                min_value=0.0, value=float(existing.get("uf_vendidas", 0.0)) if existing else 0.0, step=0.1, format="%.1f")


        # ─── Observaciones ──────────────────────────────────────────────
        st.markdown("#### 📝 Notas")
        observaciones = st.text_area("Observaciones",
            value=existing.get("observaciones", "") if existing else "",
            placeholder="Incidencias, novedades, comentarios del día...",
            max_chars=500)
        accion = st.text_area("Acción Correctiva",
            value=existing.get("accion_correctiva", "") if existing else "",
            placeholder="Acciones a tomar para mejorar...",
            max_chars=500)

        submitted = st.form_submit_button("💾 Guardar Registro", use_container_width=True)

    if submitted:
        # Build entry
        entry = {
            "fecha": fecha_str,
            "semana": semana_num,
            "dia": dia_semana,
            "leads_nuevos": leads,
            "llamadas": llamadas,
            "contactos": contactos,
            "agendas": agendas,
            "reuniones": reuniones,
            "reservas": reservas,
            "ventas": ventas,
            "uf_vendidas": uf_vendidas,
            "observaciones": observaciones,
            "accion_correctiva": accion,
        }

        # Calculate rates
        entry = calcular_tasas(entry)
        entry["ingreso_bruto"] = calcular_ingreso(entry, metas.get("precio_uf", 24000))
        entry["diagnostico"] = generar_diagnostico(entry, metas)
        entry["plan_accion"] = generar_plan_accion(entry, metas)

        # Save
        result = add_entry(username, entry)

        if result == "editada":
            st.success(f"✅ Registro del {fecha_str} **actualizado** exitosamente.")
        else:
            st.success(f"✅ Registro del {fecha_str} **guardado** exitosamente.")

        # Show diagnosis
        st.markdown("### 📋 Diagnóstico del día")
        st.markdown(f'<div class="diagnosis-box">{entry["diagnostico"]}</div>', unsafe_allow_html=True)

        with st.expander("📊 Ver tasas calculadas"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📞 Tasa Contacto", tasa_a_porcentaje(entry["tasa_contacto"]),
                         delta=None, delta_color="normal")
                st.metric("📅 Tasa Agendamiento", tasa_a_porcentaje(entry["tasa_agendamiento"]))
                st.metric("🏢 Tasa de Efectividad", tasa_a_porcentaje(entry["tasa_show"]))
            with col2:
                st.metric("✅ Tasa de Reserva", tasa_a_porcentaje(entry["tasa_reserva"]))
                st.metric("🏆 Tasa de Cierre", tasa_a_porcentaje(entry["tasa_cierre"]))
                st.metric("💰 Ingreso Bruto", f"${entry['ingreso_bruto']:,.0f}")

        st.balloons()
        st.rerun()

with tab2:
    # ─── Historial ────────────────────────────────────────────────────
    st.markdown("#### 📋 Registros Anteriores")

    if not entries:
        st.info("📭 No hay registros todavía. ¡Comienza cargando tu primer día!")
    else:
        # Filtro por mes
        meses_disponibles = sorted(set(
            e.get("fecha", "")[:7] for e in entries if e.get("fecha")
        ), reverse=True)

        if meses_disponibles:
            selected_mes = st.selectbox("Filtrar por mes", ["Todos"] + meses_disponibles)
            filtered = entries
            if selected_mes != "Todos":
                filtered = [e for e in entries if e.get("fecha", "").startswith(selected_mes)]
        else:
            filtered = entries

        # Show entries in a compact table
        for e in reversed(filtered[-50:]):  # Last 50 entries
            fecha_e = e.get("fecha", "?")
            dia_e = e.get("dia", "")
            with st.expander(f"📅 {fecha_e} — {dia_e}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**👥 Leads:** {e.get('leads_nuevos', 0)}")
                    st.markdown(f"**📞 Llamadas:** {e.get('llamadas', 0)}")
                    st.markdown(f"**🤝 Contactos:** {e.get('contactos', 0)}")
                    st.markdown(f"**📅 Reuniones Agendadas:** {e.get('agendas', 0)}")
                with col2:
                    st.markdown(f"**🏢 Reuniones Efectuadas:** {e.get('reuniones', 0)}")
                    st.markdown(f"**✅ Reservas:** {e.get('reservas', 0)}")
                    st.markdown(f"**🏆 Ventas:** {e.get('ventas', 0)}")
                    st.markdown(f"**💰 UF:** {e.get('uf_vendidas', 0):,.1f}")
                with col3:
                    st.markdown(f"**📞 T. Contacto:** {tasa_a_porcentaje(e.get('tasa_contacto', 0))}")
                    st.markdown(f"**📅 T. Agendamiento:** {tasa_a_porcentaje(e.get('tasa_agendamiento', 0))}")
                    st.markdown(f"**🏆 T. Cierre:** {tasa_a_porcentaje(e.get('tasa_cierre', 0))}")
                    st.markdown(f"**💵 Ingreso:** ${e.get('ingreso_bruto', 0):,.0f}")

                if e.get("observaciones"):
                    st.markdown(f"**📝 Obs:** {e['observaciones']}")

                if e.get("diagnostico"):
                    diag = e["diagnostico"].split("\n")[0]  # First line only
                    st.markdown(f"**📊 Diag:** {diag}")

                if st.button(f"🗑️ Eliminar {fecha_e}", key=f"del_{fecha_e}", type="secondary"):
                    st.session_state[f"confirm_del_{fecha_e}"] = True

                if st.session_state.get(f"confirm_del_{fecha_e}", False):
                    st.warning(f"¿Eliminar registro del {fecha_e}? Esta acción no se puede deshacer.")
                    col_conf1, col_conf2 = st.columns(2)
                    with col_conf1:
                        if st.button(f"✅ Sí, eliminar", key=f"confirm_yes_{fecha_e}"):
                            if delete_entry(username, fecha_e):
                                st.success(f"Registro del {fecha_e} eliminado.")
                                st.session_state[f"confirm_del_{fecha_e}"] = False
                                st.rerun()
                            else:
                                st.error("Error al eliminar.")
                    with col_conf2:
                        if st.button(f"❌ Cancelar", key=f"confirm_no_{fecha_e}"):
                            st.session_state[f"confirm_del_{fecha_e}"] = False
                            st.rerun()

