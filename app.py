import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.optimize import milp, LinearConstraint, Bounds
from datetime import datetime

st.set_page_config(page_title="OptiCoffee | Portal B2B", layout="wide", initial_sidebar_state="collapsed")

# ==============================================================================
# 1. BASE DE DATOS EN MEMORIA (USUARIOS, INVENTARIOS, CITAS Y ÓRDENES)
# ==============================================================================
USUARIOS_VALIDOS = {
    "compras": {"pass": "1234", "rol": "Empresa", "nombre": "Gerencia de Compras (OptiCoffee)"},
    "provA": {"pass": "1234", "rol": "Proveedor", "id_prov": "A", "nombre": "Proveedor A (Económico)"},
    "provB": {"pass": "1234", "rol": "Proveedor", "id_prov": "B", "nombre": "Proveedor B (Medio)"},
    "provC": {"pass": "1234", "rol": "Proveedor", "id_prov": "C", "nombre": "Proveedor C (Premium)"}
}

if "usuario_activo" not in st.session_state:
    st.session_state.usuario_activo = None

if "datos_proveedores" not in st.session_state:
    st.session_state.datos_proveedores = {
        "A": {"nombre": "Proveedor A (Económico)", "precio": 9000, "calidad": 4, "stock": 6, "dias": 2},
        "B": {"nombre": "Proveedor B (Medio)", "precio": 11000, "calidad": 7, "stock": 5, "dias": 3},
        "C": {"nombre": "Proveedor C (Premium)", "precio": 13000, "calidad": 10, "stock": 6, "dias": 5}
    }

if "citas_guardadas" not in st.session_state:
    st.session_state.citas_guardadas = []
if "historial_chat" not in st.session_state:
    st.session_state.historial_chat = []
if "ordenes_emitidas" not in st.session_state:
    st.session_state.ordenes_emitidas = []

# ==============================================================================
# 2. ESTILOS VISUALES CÁLIDOS Y CORPORATIVOS
# ==============================================================================
st.markdown("""
<style>
    .stApp { background-color: #FAF7F2; color: #2D2420; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .brand-navbar { background-color: #3C2A21; color: #F4EAE0; padding: 20px 30px; border-radius: 16px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(60, 42, 33, 0.08); }
    .brand-title { font-size: 24px; font-weight: 700; margin: 0; color: #F4EAE0; }
    .brand-tag { background-color: #D5CEA3; color: #1A120B; font-size: 12px; font-weight: 600; padding: 6px 14px; border-radius: 20px; }
    .login-card { background-color: #FFFFFF; padding: 35px; border-radius: 16px; border: 1px solid #E6D5B8; box-shadow: 0 8px 24px rgba(60, 42, 33, 0.06); }
    .info-card { background-color: #FFFFFF; padding: 20px; border-radius: 12px; border: 1px solid #EAE0D5; }
    .stTabs [data-baseweb="tab-list"] { gap: 12px; }
    .stTabs [data-baseweb="tab"] { height: 46px; border-radius: 10px; padding: 0px 22px; background-color: #EAE3D2; color: #3C2A21; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #D5CEA3 !important; color: #1A120B !important; }
    .stButton>button { border-radius: 10px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. PANTALLA DE INICIO DE SESIÓN (SI NO HAY USUARIO LOGUEADO)
# ==============================================================================
if st.session_state.usuario_activo is None:
    st.markdown("""
    <div class="brand-navbar">
        <div>
            <h1 class="brand-title">OptiCoffee Supply Portal</h1>
            <span style="font-size: 13px; opacity: 0.8;">Plataforma B2B de Abastecimiento y Socios Productores</span>
        </div>
        <span class="brand-tag">Acceso Seguro</span>
    </div>
    """, unsafe_allow_html=True)

    col_izq, col_centro, col_der = st.columns([1, 1.4, 1])
    with col_centro:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.markdown("### Iniciar Sesión en el Portal")
        st.write("Ingresa tus credenciales asignadas para acceder a tu panel operativo.")
        
        usuario_in = st.text_input("Usuario", placeholder="Ej. compras o provA")
        pass_in = st.text_input("Contraseña", type="password", placeholder="••••")
        
        if st.button("Ingresar al Sistema", type="primary", use_container_width=True):
            if usuario_in in USUARIOS_VALIDOS and USUARIOS_VALIDOS[usuario_in]["pass"] == pass_in:
                st.session_state.usuario_activo = USUARIOS_VALIDOS[usuario_in]
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos. Verifica tus datos.")
        
        st.markdown("---")
        with st.expander("🔑 Ver credenciales de prueba (Demo)"):
            st.markdown("""
            * **Portal Empresa (Compras):** Usuario `compras` | Clave `1234`
            * **Portal Proveedor A:** Usuario `provA` | Clave `1234`
            * **Portal Proveedor B:** Usuario `provB` | Clave `1234`
            * **Portal Proveedor C:** Usuario `provC` | Clave `1234`
            """)
        st.markdown('</div>', unsafe_allow_html=True)

# ==============================================================================
# 4. VISTA EXCLUSIVA PARA PROVEEDORES (SI ENTRA PROVA, PROVB O PROVC)
# ==============================================================================
elif st.session_state.usuario_activo["rol"] == "Proveedor":
    user = st.session_state.usuario_activo
    id_p = user["id_prov"]
    datos_mi_perfil = st.session_state.datos_proveedores[id_p]

    # Encabezado con botón de cerrar sesión
    c_head1, c_head2 = st.columns([4, 1])
    with c_head1:
        st.markdown(f"""
        <div class="brand-navbar">
            <div>
                <h1 class="brand-title">Portal Exclusivo de Socios | {user['nombre']}</h1>
                <span style="font-size: 13px; opacity: 0.8;">Gestión de Inventario, Órdenes Asignadas y Comunicación Directa</span>
            </div>
            <span class="brand-tag">Socio Certificado</span>
        </div>
        """, unsafe_allow_html=True)
    with c_head2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state.usuario_activo = None
            st.rerun()

    tab_p1, tab_p2, tab_p3 = st.tabs(["📦 Mis Órdenes Asignadas", "⚙️ Actualizar Mi Oferta y Stock", "📅 Mis Citas y Mensajes"])

    # Pestaña 1 del Proveedor: Ver solo sus órdenes
    with tab_p1:
        st.markdown("#### Órdenes de Compra Recibidas")
        mis_ordenes = [o for o in st.session_state.ordenes_emitidas if o[f"Lotes_{id_p}"] > 0]
        if mis_ordenes:
            for ord_item in mis_ordenes:
                lotes_mios = ord_item[f"Lotes_{id_p}"]
                monto_mio = lotes_mios * datos_mi_perfil["precio"]
                st.success(f"**Folio {ord_item['Folio']}** ({ord_item['Fecha']}) — Solicitud de **{lotes_mios} lotes ({lotes_mios*50} kg)** | Total a facturar: **${monto_mio:,.2f} MXN**")
        else:
            st.info("Aún no tienes órdenes de compra asignadas en este ciclo.")

    # Pestaña 2 del Proveedor: Modificar su stock y precio en tiempo real
    with tab_p2:
        st.markdown("#### Disponibilidad de Inventario y Tarifa Vigente")
        st.write("Actualiza tu capacidad disponible. Estos cambios se reflejarán automáticamente en el sistema de compras:")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            nuevo_stock = st.number_input("Sacos Disponibles para Entrega Inmediata (50 kg)", min_value=0, max_value=50, value=int(datos_mi_perfil["stock"]))
        with col_f2:
            nuevo_precio = st.number_input("Precio por Lote de 50 kg ($ MXN)", min_value=5000, max_value=25000, value=int(datos_mi_perfil["precio"]), step=500)
        
        if st.button("Guardar Actualización de Inventario", type="primary"):
            st.session_state.datos_proveedores[id_p]["stock"] = nuevo_stock
            st.session_state.datos_proveedores[id_p]["precio"] = nuevo_precio
            st.success("Tu inventario y tarifa han sido actualizados en la plataforma.")

    # Pestaña 3 del Proveedor: Sus citas y chat
    with tab_p3:
        col_pc1, col_pc2 = st.columns(2)
        with col_pc1:
            st.markdown("##### Citas Agendadas Conmigo")
            mis_citas = [c for c in st.session_state.citas_guardadas if id_p in c["Proveedor"]]
            if mis_citas:
                st.dataframe(pd.DataFrame(mis_citas), hide_index=True, use_container_width=True)
            else:
                st.info("No tienes reuniones programadas por el momento.")
        with col_pc2:
            st.markdown("##### Mensajes Directos con Compras")
            msg_prov = st.text_input("Enviar mensaje a Gerencia de Compras...")
            if st.button("Enviar al Equipo de Compras"):
                if msg_prov:
                    st.session_state.historial_chat.append({
                        "Hora": datetime.now().strftime("%H:%M"),
                        "Remitente": user["nombre"],
                        "Mensaje": msg_prov
                    })
                    st.success("Mensaje enviado a Compras.")
            if st.session_state.historial_chat:
                st.dataframe(pd.DataFrame(st.session_state.historial_chat), hide_index=True, use_container_width=True)

# ==============================================================================
# 5. VISTA EMPRESA / COMPRAS (SI ENTRA EL USUARIO "COMPRAS")
# ==============================================================================
elif st.session_state.usuario_activo["rol"] == "Empresa":
    c_head1, c_head2 = st.columns([4, 1])
    with c_head1:
        st.markdown("""
        <div class="brand-navbar">
            <div>
                <h1 class="brand-title">OptiCoffee Supply Portal | Gerencia de Compras</h1>
