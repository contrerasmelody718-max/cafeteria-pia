import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.optimize import milp, LinearConstraint, Bounds
from datetime import datetime
from estilos import aplicar_estilos, mostrar_barra
from vistas import mostrar_portal_proveedor, mostrar_centro_control

st.set_page_config(page_title="OptiCoffee | Portal B2B", layout="wide", initial_sidebar_state="collapsed")
aplicar_estilos()

USUARIOS = {
    "compras": {"pass": "1234", "rol": "Empresa", "nombre": "Gerencia de Compras"},
    "provA": {"pass": "1234", "rol": "Proveedor", "id": "A", "nombre": "Proveedor A (Económico)"},
    "provB": {"pass": "1234", "rol": "Proveedor", "id": "B", "nombre": "Proveedor B (Medio)"},
    "provC": {"pass": "1234", "rol": "Proveedor", "id": "C", "nombre": "Proveedor C (Premium)"}
}

if "user" not in st.session_state: st.session_state.user = None
if "provs" not in st.session_state:
    st.session_state.provs = {
        "A": {"nombre": "Proveedor A (Económico)", "precio": 9000, "calidad": 4, "stock": 6},
        "B": {"nombre": "Proveedor B (Medio)", "precio": 11000, "calidad": 7, "stock": 5},
        "C": {"nombre": "Proveedor C (Premium)", "precio": 13000, "calidad": 10, "stock": 6}
    }
if "citas" not in st.session_state:
    st.session_state.citas = [{"Proveedor": "Proveedor C (Premium)", "Fecha": "2026-11-12", "Motivo": "Catación de lote de altura"}]
if "chat" not in st.session_state:
    st.session_state.chat = [{"Hora": "09:30", "De": "Proveedor B (Medio)", "Mensaje": "Confirmamos disponibilidad inmediata de 5 sacos."}]
if "ordenes" not in st.session_state:
    st.session_state.ordenes = [{"Folio": "OC-100", "Fecha": "09/11/2026 16:20", "Total": "$130,000.00", "Kilos": 600, "Lotes_A": 2, "Lotes_B": 5, "Lotes_C": 5}]

# 1. LOGIN
if st.session_state.user is None:
    mostrar_barra("OptiCoffee Supply Portal", "Plataforma B2B de Abastecimiento y Proveedores", "Acceso Seguro")
    _, col_c, _ = st.columns([1, 1.4, 1])
    with col_c:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        st.subheader("Iniciar Sesión")
        u_in = st.text_input("Usuario", placeholder="compras, provA, provB o provC")
        p_in = st.text_input("Contraseña", type="password", placeholder="1234")
        if st.button("Ingresar al Sistema", type="primary", use_container_width=True):
            if u_in in USUARIOS and USUARIOS[u_in]["pass"] == p_in:
                st.session_state.user = USUARIOS[u_in]
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")
        with st.expander("🔑 Ver usuarios de prueba"):
            st.write("Empresa: `compras` / `1234` | Proveedores: `provA`, `provB`, `provC` / `1234`")
        st.markdown('</div>', unsafe_allow_html=True)

# 2. PORTAL PROVEEDORES
elif st.session_state.user["rol"] == "Proveedor":
    u = st.session_state.user
    c1, c2 = st.columns()
    with c1: mostrar_barra(f"Portal de Socios | {u['nombre']}", "Gestión de Inventario y Órdenes", "Socio Certificado")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state.user = None
            st.rerun()
    mostrar_portal_proveedor(u, u["id"], st.session_state.provs[u["id"]])

# 3. PORTAL COMPRAS
elif st.session_state.user["rol"] == "Empresa":
    c1, c2 = st.columns()
    with c1: mostrar_barra("OptiCoffee Supply Portal", "Planeación de Pedidos y Proveedores", "Gerencia de Compras")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    a1, a2, a3 = st.columns(3)
    with a1:
        with st.popover("📅 Agendar Cita", use_container_width=True):
            pc = st.selectbox("Proveedor", ["Proveedor A (Económico)", "Proveedor B (Medio)", "Proveedor C (Premium)"])
            fc = st.date_input("Fecha", datetime.now())
            mc = st.text_input("Motivo", "Revisión de entregas")
            if st.button("Confirmar Cita", type="primary", use_container_width=True):
                st.session_state.citas.append({"Proveedor": pc, "Fecha": str(fc), "Motivo": mc})
                st.rerun()
    with a2:
        with st.popover("💬 Chat Directo", use_container_width=True):
            pch = st.selectbox("Canal", ["Proveedor A", "Proveedor B", "Proveedor C"])
            mch = st.text_input("Escribe tu mensaje...")
            if st.button("Enviar Mensaje", type="primary", use_container_width=True):
                if mch:
                    st.session_state.chat.append({"Hora": datetime.now().strftime("%H:%M"), "De": f"Compras para {pch}", "Mensaje": mch})
                    st.rerun()
    with a3:
        with st.popover("📋 Políticas", use_container_width=True):
            st.write("• Sacos de 50 kg | Mín. 7 sacos rápidos | Calidad >= 70 pts")

    st.markdown("<br>", unsafe_allow_html=True)
    in1, in2 = st.columns(2)
    with in1: presupuesto = st.number_input("Presupuesto Disponible ($ MXN)", 10000, 500000, 130000, step=5000)
    with in2: demanda = st.number_input("Volumen Requerido (Kg)", 50, 2000, 600, step=50)

    pA, pB, pC = st.session_state.provs["A"], st.session_state.provs["B"], st.session_state.provs["C"]
    lotes_req = int(demanda / 50)
    res = milp(
        c=np.array([-float(pA["calidad"]), -float(pB["calidad"]), -float(pC["calidad"])]),
        integrality=np.ones(3),
        bounds=Bounds(lb=np.zeros(3), ub=np.array([float(pA["stock"]), float(pB["stock"]), float(pC["stock"])])),
        constraints=LinearConstraint(
            np.array([[1.0, 1.0, 1.0], [float(pA["precio"]), float(pB["precio"]), float(pC["precio"])], [float(pA["calidad"]), float(pB["calidad"]), float(pC["calidad"])], [1.0, 1.0, 0.0]]),
            np.array([lotes_req, -np.inf, 70.0, 7.0], dtype=float),
            np.array([lotes_req, presupuesto, np.inf, np.inf], dtype=float)
        )
    )

    if res.success:
        xo = np.round(res.x).astype(int)
        la, lb, lc = int(xo.item(0)), int(xo.item(1)), int(xo.item(2))
        cal_tot = (pA["calidad"]*la) + (pB["calidad"]*lb) + (pC["calidad"]*lc)
        gasto = (la*pA["precio"]) + (lb*pB["precio"]) + (lc*pC["precio"])
        prom = round(cal_tot / lotes_req, 2) if lotes_req > 0 else 0

        df_o = pd.DataFrame({
            "Proveedor": (pA["nombre"], pB["nombre"], pC["nombre"]),
            "Calidad": (f"{pA['calidad']}/10", f"{pB['calidad']}/10", f"{pC['calidad']}/10"),
            "Sacos (50 kg)": (la, lb, lc),
            "Kilos Totales": (la*50, lb*50, lc*50),
            "Inversión ($)": (f"${la*pA['precio']:,.2f}", f"${lb*pB['precio']:,.2f}", f"${lc*pC['precio']:,.2f}")
        })

        total_items = len(st.session_state.ordenes) + len(st.session_state.citas) + len(st.session_state.chat)
        tab1, tab2 = st.tabs(["🛒 Pedido Sugerido", f"🗂️ Centro de Control ({total_items})"])

        with tab1:
            m1, m2, m3 = st.columns(3)
            m1.metric("Calidad Promedio", f"{prom} / 10", f"{cal_tot} pts totales")
            m2.metric("Inversión Total", f"${gasto:,.2f}", f"${presupuesto - gasto:,.2f} disponible")
            m3.metric("Total Sacos", f"{lotes_req} Sacos", f"{la + lb} entrega rápida")

            ct, cg = st.columns([1.3, 1])
            with ct:
                st.dataframe(df_o, hide_index=True, use_container_width=True)
                if st.button("✅ Autorizar y Enviar Orden", type="primary", use_container_width=True):
                    fol = f"OC-{len(st.session_state.ordenes) + 100}"
                    st.session_state.ordenes.append({"Folio": fol, "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"), "Total": f"${gasto:,.2f}", "Kilos": demanda, "Lotes_A": la, "Lotes_B": lb, "Lotes_C": lc})
                    st.rerun()
            with cg:
                df_graf = pd.DataFrame({"Proveedor": (pA["nombre"], pB["nombre"], pC["nombre"]), "Monto": (la*pA["precio"], lb*pB["precio"], lc*pC["precio"])})
                fig = px.pie(df_graf[df_graf["Monto"] > 0], values="Monto", names="Proveedor", hole=0.45, color_discrete_sequence=("#A0522D", "#CD853F", "#DEB887"))
                fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig, use_container_width=True)
        with tab2:
            mostrar_centro_control()
    else:
        st.warning("No es posible cumplir el pedido con el presupuesto, volumen o stock actual.")
