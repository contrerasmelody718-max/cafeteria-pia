import streamlit as st
import pandas as pd
from datetime import datetime

def mostrar_portal_proveedor(u, pid, mi_p):
    t1, t2, t3 = st.tabs(["📦 Mis Órdenes", "⚙️ Mi Oferta y Stock", "📅 Citas y Mensajes"])
    with t1:
        mias = [o for o in st.session_state.ordenes if o[f"Lotes_{pid}"] > 0]
        if mias:
            for o in mias:
                lotes = o[f"Lotes_{pid}"]
                st.success(f"**Orden {o['Folio']}** ({o['Fecha']}) — **{lotes} sacos ({lotes*50} kg)** | Facturación: **${lotes * mi_p['precio']:,.2f} MXN**")
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
            st.success("Tarifa y disponibilidad actualizadas.")
    with t3:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### Reuniones Confirmadas")
            mc = [c for c in st.session_state.citas if pid in c["Proveedor"]]
            for cita in mc:
                st.info(f"📅 **{cita['Fecha']}** — {cita['Motivo']}")
            if not mc:
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

def mostrar_centro_control():
    st.markdown("#### Historial de Órdenes Autorizadas")
    for o in st.session_state.ordenes:
        resumen = []
        if o["Lotes_A"] > 0: resumen.append(f"Proveedor A: {o['Lotes_A']} sacos")
        if o["Lotes_B"] > 0: resumen.append(f"Proveedor B: {o['Lotes_B']} sacos")
        if o["Lotes_C"] > 0: resumen.append(f"Proveedor C: {o['Lotes_C']} sacos")
        st.success(f"**Folio {o['Folio']}** — {o['Fecha']} | Volumen: **{o['Kilos']} kg** | Total: **{o['Total']}**\n\n📦 *Asignación:* {' • '.join(resumen)}")

    st.markdown("---")
    b1, b2 = st.columns(2)
    with b1:
        st.markdown("#### 📅 Agenda de Reuniones")
        for c in st.session_state.citas:
            st.warning(f"**{c['Proveedor']}** — Fecha: **{c['Fecha']}**\n\n📝 *Asunto:* {c['Motivo']}")
    with b2:
        st.markdown("#### 💬 Buzón de Mensajes")
        for m in st.session_state.chat:
            with st.chat_message("assistant" if "Compras" in m["De"] else "user"):
                st.write(f"**{m['De']}** ({m['Hora']}): {m['Mensaje']}")
