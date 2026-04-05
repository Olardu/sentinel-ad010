import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import date, datetime

# ─── AUTENTICACIÓN ─────────────────────────────────────────────────────────
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔒 Sentinel · AD010")
        password = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            if password == st.secrets["app"]["password"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
        st.stop()

check_password()

# ─── CONEXIÓN A GOOGLE SHEETS ──────────────────────────────────────────────
@st.cache_resource
def conectar_sheets():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=scopes
    )
    cliente = gspread.authorize(creds)
    sheet = cliente.open_by_key(st.secrets["google_sheets"]["spreadsheet_id"])
    return sheet

# ─── CONFIGURACIÓN DE PÁGINA ───────────────────────────────────────────────
st.set_page_config(page_title="Sentinel · AD010", page_icon="🚛", layout="centered")
st.title("🚛 Sentinel · AD010")
st.caption("Registro de turno")
st.divider()

# ─── CARGAR DATOS DE CAMIONES ──────────────────────────────────────────────
try:
    sheet = conectar_sheets()
    hoja_camiones = sheet.worksheet("camiones")
    camiones_data = hoja_camiones.get_all_records()
    lista_camiones = [c["camion_id"] for c in camiones_data if c["activo"] == "TRUE"]
except Exception as e:
    st.error(f"Error conectando a Google Sheets: {e}")
    st.stop()

# ─── FORMULARIO ────────────────────────────────────────────────────────────
with st.form("registro_turno"):
    fecha = st.date_input("📅 Fecha", value=date.today())
    camion_id = st.selectbox("🚛 Camión", lista_camiones)
    tipo_reporte = st.selectbox("📋 Tipo de turno", ["field", "shop"])

    col1, col2 = st.columns(2)
    with col1:
        hora_entrada = st.time_input("🟢 Entrada", value=datetime.strptime("05:00", "%H:%M").time())
    with col2:
        hora_salida = st.time_input("🔴 Salida", value=datetime.strptime("15:00", "%H:%M").time())

    # Campos dinámicos según tipo de turno
    millas_inicio = millas_fin = galones = 0
    if tipo_reporte == "field":
        col3, col4 = st.columns(2)
        with col3:
            millas_inicio = st.number_input("📍 Millas Inicio", min_value=0, step=1)
        with col4:
            millas_fin = st.number_input("🏁 Millas Fin", min_value=0, step=1)

        # Galones solo si camión AD
        if camion_id.startswith("AD"):
            galones = st.number_input("🪣 Galones Tack", min_value=0.0, step=0.5, format="%.1f")

    notas = st.text_input("📝 Notas (opcional)")
    guardar = st.form_submit_button("💾 Guardar Turno", use_container_width=True)

# ─── PROCESAMIENTO ─────────────────────────────────────────────────────────
if guardar:
    # Validaciones
    if hora_salida <= hora_entrada:
        st.error("⚠️ La hora de salida debe ser mayor que la entrada.")
        st.stop()
    if tipo_reporte == "field" and millas_fin < millas_inicio:
        st.error("⚠️ Las millas fin no pueden ser menores que las millas inicio.")
        st.stop()

    # Cálculos
    entrada_dt = datetime.combine(date.today(), hora_entrada)
    salida_dt = datetime.combine(date.today(), hora_salida)
    horas_trabajadas = round((salida_dt - entrada_dt).seconds / 3600, 2)
    millas_recorridas = millas_fin - millas_inicio if tipo_reporte == "field" else ""

    # Fila para Sheets
    nueva_fila = [
        str(fecha),
        camion_id,
        str(hora_entrada),
        str(hora_salida),
        horas_trabajadas,
        millas_inicio if tipo_reporte == "field" else "",
        millas_fin if tipo_reporte == "field" else "",
        millas_recorridas,
        galones if tipo_reporte == "field" and camion_id.startswith("AD") else "",
        tipo_reporte,
        notas
    ]

    try:
        hoja_turnos = sheet.worksheet("turnos")
        hoja_turnos.append_row(nueva_fila)
        st.success("✅ Turno guardado correctamente.")
    except Exception as e:
        st.error(f"❌ Error al guardar: {e}")
        st.stop()

    # ─── ALERTA CAMBIO DE ACEITE ───────────────────────────────────────────
    if tipo_reporte == "field" and camion_id.startswith("AD"):
        try:
            camion_actual = next(c for c in camiones_data if c["camion_id"] == camion_id)
            proximo_cambio = int(camion_actual["cambio_aceite_proximo"])
            config = sheet.worksheet("configuracion").get_all_records()
            alerta_millas = int(next(c["valor"] for c in config if c["clave"] == "alerta_aceite_millas"))
            if millas_fin >= proximo_cambio - alerta_millas:
                st.warning(f"⚠️ Cambio de aceite próximo — {camion_id} lleva {millas_fin} millas. Próximo cambio a las {proximo_cambio}.")
        except:
            pass

    # ─── REPORTE PARA FOREMAN ──────────────────────────────────────────────
    st.divider()
    st.subheader("📋 Reporte para Foreman")

    if tipo_reporte == "field":
        reporte = f"""{fecha.strftime('%m/%d/%y')} Truck {camion_id}
Hours: {hora_entrada.strftime('%H%M')}-{hora_salida.strftime('%H%M')}
Gallons: {int(galones)}"""
    else:
        reporte = f"""{fecha.strftime('%m/%d/%y')} Truck {camion_id}
Hours: {hora_entrada.strftime('%H%M')}-{hora_salida.strftime('%H%M')}"""

    st.code(reporte, language=None)
    st.caption("Mantén presionado para copiar en iPhone.")