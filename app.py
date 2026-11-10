import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.optimize import milp, LinearConstraint, Bounds
from datetime import datetime
from estilos import aplicar_estilos, mostrar_barra

st.set_page_config(page_title="OptiCoffee | Portal B2B", layout="wide", initial_sidebar_state="collapsed")
aplicar_estilos()

USUARIOS = {
    "compras": {"pass": "1234", "rol": "Empresa", "nombre": "Gerencia de Compras"},
    "provA": {"pass": "1234", "rol": "Proveedor", "id": "A", "nombre": "Proveedor A (Económico)"},
    "provB": {"pass": "1234", "rol": "Proveedor", "id": "B", "nombre": "Proveedor B (Medio)"},
    "provC": {"pass": "1234", "rol": "Proveedor", "id": "C", "nombre": "Proveedor C (Premium)"}
}

if "user" not in st.session_state:
    st.session_state.user = None
if "provs" not in st.session_state:
    st.session_state.provs = {
        "A": {"nombre": "Proveedor A (Económico)", "precio": 9000, "calidad": 4, "stock": 6},
        "B": {"nombre": "Proveedor B (Medio)", "precio": 11000, "calidad": 7, "stock": 5},
        "C": {"nombre": "Proveedor C (Premium)", "precio": 13000, "calidad": 10, "stock": 6}
    }
if "citas" not in st.session_state:
    st.session_state.citas = []
if "chat" not in st.session_state:
    st.session_state.chat = []
if "ordenes" not in st.session_state:
    st.session_state.ordenes = []

# 1. PANTALLA DE LOGIN
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
                st.error("Usuario o contraseña incorrectos.")
        with st.expander("🔑 Ver usuarios de prueba"):
            st.write("Empresa: `compras` / `1234` | Proveedores: `provA`, `provB`, `provC` / `1234`")
        st.markdown('</div>', unsafe_allow_html=True)

# 2. PORTAL EXCLUSIVO PROVEEDORES
elif st.session_state.user["rol"] == "Proveedor":
    u = st.session_state.user
    pid = u["id"]
    mi_p = st.session_state.provs[pid]

    c1, c2 = st.columns([4, 1])
    with c1:
        mostrar_barra(f"Portal de Socios | {u['nombre']}", "Gestión de Inventario y Órdenes Asignadas", "Socio Certificado")
    with c2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state.user = None
            st.rerun()

    t1, t2, t3 = st.tabs(["📦 Mis Órdenes", "⚙️ Mi Oferta y Stock", "📅 Citas y Mensajes"])
    with t1:
        mias = [o for o in st.session_state.ordenes if o[f"Lotes_{pid}"] > 0]
        if mias:
            for o in mias:
                lotes = o[f"Lotes_{pid}"]
                st.success(f"**Orden {o['Folio']}** ({o['Fecha']}) — Solicitud de **{lotes} sacos ({lotes*50} kg)** | Total a facturar: **${lotes * mi_p['precio']:,.2f} MXN**")
        else:
            st.info("Aún no tienes órdenes asignadas en este ciclo.")
    with t2:
        col1, col2 = st.columns(2)
        with col1:
            n_stock = st.number_input("Sacos Disponibles (50 kg)", 0, 50, int(mi_p["stock"]))
        with col2:
            n_precio = st.number_input("Precio por Lote ($ MXN)", 5000, 25000, int(mi_p["precio"]), step=500)
        if st.button("Actualizar Mi Oferta", type="primary"):
            st.session_state.provs[pid]["stock"] = n_stock
            st.session_state.provs[pid]["precio"] = n_precio
            st.success("Tu tarifa y disponibilidad se han actualizado.")
    with t3:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### Reuniones Confirmadas")
            mc = [c for c in st.session_state.citas if pid in c["Proveedor"]]
            if mc:
                for cita in mc:
                    st.info(f"📅 **{cita['Fecha']}** — {cita['Motivo']}")
            else:
                st.write("No tienes reuniones agendadas.")
        with col2:
            st.markdown("##### Conversación con Compras")
            for msg in st.session_state.chat:
                with st.chat_message("user" if "Proveedor" in msg["De"] else "assistant"):
                    st.write(f"**{msg['De']}** ({msg['Hora']}): {msg['Mensaje']}")
            mp = st.text_input("Escribe un mensaje para Compras...")
            if st.button("Enviar Mensaje"):
                if mp:
                    st.session_state.chat.append({"Hora": datetime.now().strftime("%H:%M"), "De": u["nombre"], "Mensaje": mp})
                    st.rerun()

# 3. PORTAL GERENCIA DE COMPRAS
elif st.session_state.user["rol"] == "Empresa":
    c1, c2 = st.columns([4, 1])
    with c1:
        mostrar_barra("OptiCoffee Supply Portal", "Planeación de Pedidos y Gestión de Proveedores", "Gerencia de Compras")
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
            mc = st.text_input("Motivo", "Revisión de entregas y calidad")
            if st.button("Confirmar Cita", type="primary", use_container_width=True):
                st.session_state.citas.append({"Proveedor": pc, "Fecha": str(fc), "Motivo": mc})
                st.success("Reunión agendada.")
    with a2:
        with st.popover("💬 Chat Directo", use_container_width=True):
            pch = st.selectbox("Canal", ["Proveedor A", "Proveedor B", "Proveedor C"])
            mch = st.text_input("Escribe tu mensaje...")
            if st.button("Enviar Mensaje", type="primary", use_container_width=True):
                if mch:
                    st.session_state.chat.append({"Hora": datetime.now().strftime("%H:%M"), "De": f"Compras para {pch}", "Mensaje": mch})
                    st.success("Mensaje enviado.")
    with a3:
        with st.popover("📋 Políticas", use_container_width=True):
            st.write("• Sacos cerrados de 50 kg.")
            st.write("• Mínimo 7 sacos de entrega urgente (≤ 3 días).")
            st.write("• Calidad mínima aprobada: 70 puntos.")

    st.markdown("<br>", unsafe_allow_html=True)
    in1, in2 = st.columns(2)
    with in1:
        presupuesto = st.number_input("Presupuesto Disponible ($ MXN)", 10000, 500000, 130000, step=5000)
    with in2:
        demanda = st.number_input("Volumen Requerido (Kg)", 50, 2000, 600, step=50)

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
            "Calidad": (f"{pA['calidad']} / 10", f"{pB['calidad']} / 10", f"{pC['calidad']} / 10"),
            "Sacos (50 kg)": (la, lb, lc),
            "Kilos Totales": (la*50, lb*50, lc*50),
            "Inversión ($)": (f"${la*pA['precio']:,.2f}", f"${lb*pB['precio']:,.2f}", f"${lc*pC['precio']:,.2f}")
        })

        tab1, tab2 = st.tabs(["🛒 Pedido Sugerido", "🗂️ Centro de Control"])
        with tab1:
            m1, m2, m3 = st.columns(3)
            m1.metric("Calidad Promedio", f"{prom} / 10", f"{cal_tot} pts totales")
            m2.metric("Inversión Total", f"${gasto:,.2f}", f"${presupuesto - gasto:,.2f} disponible")
            m3.metric("Total Sacos", f"{lotes_req} Sacos", f"{la + lb} entrega rápida")

            ct, cg = st.columns([1.3, 1])
            with ct:
                st.dataframe(df_o, hide_index=True, use_container_width=True)
                if st.button("✅ Autorizar y Enviar Orden", type="primary", use_container_width=True):
                    fol = f"OC-{len(st.session_state.ordenes) + 101}"
                    st.session_state.ordenes.append({
                        "Folio": fol, "Fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "Total": f"${gasto:,.2f}", "Kilos": demanda,
                        "Lotes_A": la, "Lotes_B": lb, "Lotes_C": lc
                    })
                    st.success(f"Orden {fol} autorizada y enviada a los proveedores.")
            with cg:
                df_graf = pd.DataFrame({"Proveedor": (pA["nombre"], pB["nombre"], pC["nombre"]), "Monto": (la*pA["precio"], lb*pB["precio"], lc*pC["precio"])})
