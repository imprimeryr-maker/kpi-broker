"""
app.py - Punto de entrada principal
Login, registro y barra de navegación
"""

import streamlit as st
from auth import authenticate, create_user

st.set_page_config(
    page_title="KPI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Estilos CSS para mobile ──────────────────────────────────────────
st.markdown("""
<style>
    /* Mobile friendly */
    .stButton > button {
        width: 100%;
        min-height: 48px;
        font-size: 16px;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
        min-height: 44px;
    }
    .stNumberInput > div > div > input {
        font-size: 16px;
        min-height: 44px;
    }
    .stDateInput > div > div > input {
        font-size: 16px;
        min-height: 44px;
    }
    .metric-card {
        background: #1E1E2E;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        border-left: 4px solid #1E88E5;
    }
    .metric-card.green { border-left-color: #4CAF50; }
    .metric-card.red { border-left-color: #f44336; }
    .metric-card.orange { border-left-color: #FF9800; }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        margin: 4px 0;
    }
    .metric-label {
        font-size: 14px;
        color: #9E9E9E;
    }
    .login-box {
        max-width: 400px;
        margin: 80px auto;
        padding: 32px;
        background: #1E1E2E;
        border-radius: 16px;
        text-align: center;
    }
    .login-box h1 {
        font-size: 28px;
        margin-bottom: 8px;
    }
    .login-box p {
        color: #9E9E9E;
        margin-bottom: 24px;
    }
    .diagnosis-box {
        background: #1E1E2E;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        white-space: pre-line;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)


# ─── Inicializar session state ────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"
if "logged_out" not in st.session_state:
    st.session_state.logged_out = False


# ─── Helper para alternar entre login y registro ─────────────────────
def toggle_page():
    if st.session_state.login_page == "login":
        st.session_state.login_page = "register"
    else:
        st.session_state.login_page = "login"
    st.rerun()

if "login_page" not in st.session_state:
    st.session_state.login_page = "login"

# ─── Función de registro ──────────────────────────────────────────────
def register_page():
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("<h1>📝 Crear Cuenta</h1>", unsafe_allow_html=True)
    st.markdown("<p>Regístrate para usar el panel de KPIs</p>", unsafe_allow_html=True)

    with st.form("register_form"):
        new_user = st.text_input("Usuario", placeholder="Elige un nombre de usuario", key="reg_user")
        new_name = st.text_input("Nombre", placeholder="Tu nombre completo", key="reg_name")
        new_pass = st.text_input("Contraseña", type="password", placeholder="Mínimo 4 caracteres", key="reg_pass")
        new_pass2 = st.text_input("Confirmar Contraseña", type="password", placeholder="Repite la contraseña", key="reg_pass2")

        submitted = st.form_submit_button("✅ Crear Cuenta", use_container_width=True)

        if submitted:
            if not new_user or not new_pass:
                st.error("❌ Completa todos los campos obligatorios")
            elif new_pass != new_pass2:
                st.error("❌ Las contraseñas no coinciden")
            else:
                success, msg = create_user(new_user, new_pass, new_name)
                if success:
                    st.success(f"✅ {msg}")
                    st.info("🔑 Ahora inicia sesión con tu nuevo usuario.")
                    st.session_state.login_page = "login"
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    # Botón Volver fuera del formulario
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔙 Volver al inicio", use_container_width=True):
            st.session_state.login_page = "login"
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ─── Función de login ─────────────────────────────────────────────────
def login_page():
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown("<h1>📊 KPI Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p>Panel de control de indicadores comerciales</p>", unsafe_allow_html=True)

    with st.form("login_form"):
        username = st.text_input("Usuario", placeholder="Ingresa tu usuario", key="login_user")
        password = st.text_input("Contraseña", type="password", placeholder="Ingresa tu contraseña", key="login_pass")
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("🔑 Ingresar", use_container_width=True)
        with col2:
            st.form_submit_button("📝 Crear Cuenta", use_container_width=True, type="secondary", on_click=toggle_page)

    if submitted:
        if not username or not password:
            st.error("❌ Ingresa usuario y contraseña")
        else:
            success, user_data = authenticate(username, password)
            if success:
                st.session_state.user = user_data
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")

    st.markdown('<p style="text-align:center;color:#9E9E9E;font-size:13px;padding-top:16px;">¿No tienes cuenta? Crea una gratis desde el botón "Crear Cuenta".</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ─── Sidebar de navegación ────────────────────────────────────────────
def render_sidebar():
    if st.session_state.user:
        user = st.session_state.user
        with st.sidebar:
            st.markdown(f"""
            <div style="text-align:center;padding:16px 0;">
                <div style="font-size:40px;">👤</div>
                <div style="font-size:18px;font-weight:600;">{user.get('nombre', user['username'])}</div>
                <div style="font-size:13px;color:#9E9E9E;">@{user['username']}</div>
            </div>
            """, unsafe_allow_html=True)

            st.divider()
            st.markdown("### 📋 Navegación")

            if st.button("📥 Carga Diaria", use_container_width=True):
                st.switch_page("pages/1_Carga_Diaria.py")
            if st.button("📊 Dashboard Diario", use_container_width=True):
                st.switch_page("pages/2_Dashboard_Diario.py")
            if st.button("📈 Dashboard Semanal", use_container_width=True):
                st.switch_page("pages/3_Dashboard_Semanal.py")
            if st.button("📅 Dashboard Mensual", use_container_width=True):
                st.switch_page("pages/4_Dashboard_Mensual.py")
            if st.button("⚙️ Configurar Metas", use_container_width=True):
                st.switch_page("pages/5_Config_Metas.py")

            st.divider()
            if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
                st.session_state.user = None
                st.session_state.logged_out = True
                st.rerun()


# ─── Página principal (después del login) ─────────────────────────────
def main_page():
    user = st.session_state.user
    nombre = user.get("nombre", user["username"])
    st.markdown(f"## 👋 Bienvenido, {nombre}")

    st.markdown("""
    <div style="background:#1E1E2E;border-radius:12px;padding:24px;margin:16px 0;">
        <h3>🎯 Panel de Control de KPIs</h3>
        <p style="color:#9E9E9E;">
            Gestiona tus indicadores comerciales desde cualquier lugar.
            Usa el menú lateral para navegar entre las secciones:
        </p>
        <ul style="color:#B0B0B0;line-height:2;">
            <li><b>📥 Carga Diaria</b> — Ingresa los datos del día</li>
            <li><b>📊 Dashboard Diario</b> — Métricas vs metas del día</li>
            <li><b>📈 Dashboard Semanal</b> — Resumen semanal con gráficos</li>
            <li><b>📅 Dashboard Mensual</b> — Tendencias mensuales</li>
            <li><b>⚙️ Configurar Metas</b> — Ajusta tus objetivos</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    # Quick stats summary
    from storage import load_carga_diaria
    entries = load_carga_diaria(user["username"])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📋 Días cargados", len(entries))
    with col2:
        total_uf = sum(e.get("uf_vendidas", 0) or 0 for e in entries)
        st.metric("💰 UF Vendidas", f"{total_uf:,.1f}")
    with col3:
        total_ventas = sum(e.get("ventas", 0) or 0 for e in entries)
        st.metric("🏆 Ventas", int(total_ventas))
    with col4:
        total_leads = sum(e.get("leads_nuevos", 0) or 0 for e in entries)
        st.metric("👥 Leads", int(total_leads))

    st.info("💡 Selecciona una opción del menú lateral para comenzar.")


# ─── Routing principal ────────────────────────────────────────────────
if st.session_state.user:
    render_sidebar()
    main_page()
elif st.session_state.login_page == "register":
    register_page()
else:
    login_page()
