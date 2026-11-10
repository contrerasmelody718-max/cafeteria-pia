import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.optimize import milp, LinearConstraint, Bounds
from datetime import datetime

# 1. CONFIGURACIÓN DE PÁGINA CÁLIDA Y COMERCIAL
st.set_page_config(
    page_title="OptiCoffee | Portal de Proveedores", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilo CSS personalizado
st.markdown("""
<style>
    .stApp { background-color: #FAF7F2; color: #2D2420; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .brand-navbar { background-color: #3C2A21; color: #F4EAE0; padding: 20px 30px; border-radius: 16px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(60, 42, 33, 0.08); }
    .brand-title { font-size: 24px; font-weight: 700; letter-spacing: 0.5px; margin: 0; color: #F4EAE0; }
    .brand-tag { background-color: #D5CEA3; color: #1A120B; font-size: 12px; font-weight: 600; padding: 6px 14px; border-radius: 20px; }
    .section-header { color: #3C2A21; font-size: 18px; font-weight: 700; margin-bottom: 15px; }
    .stTabs [data-baseweb="tab-list"] { gap: 12px; }
    .stTabs [data-baseweb="tab"] { height: 48px; border-radius: 10px; padding: 0px 24px; background-color: #EAE3D2; color: #3C2A21; border: none; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #D5CEA3 !important; color: #1A120B !important; }
    .stButton>button { border-radius: 10px; font-weight: 600; }
    .notice-card { background-color: #FFF8F0; border: 1px solid #E6C5A5; border-left: 5px solid #C87D55; padding: 20px; border-radius: 12px; margin-top: 15px; }
</style>
""", unsafe_allow_html=True)

# 2. ENCABEZADO SUPERIOR TIPO PORTAL EMPRESARIAL
st.markdown("""
<div class="brand-navbar">
    <div>
        <h1 class="brand-title">OptiCoffee Supply Portal</h1>
        <span style="font-size: 13px; opacity: 0.8;">Gestión de Proveedores y Planeación de Pedidos</span>
    </div>
    <span class="brand-tag">Módulo de Operaciones</span>
</div>
""", unsafe_allow_html=True)

# 3. ACCIONES RÁPIDAS SUPERIORES
col_action1, col_action2, col_action3 = st.columns([1, 1, 1])

with col_action1:
    with st.popover("📅 Agendar Cita con Proveedor", use_container_width=True):
        st.markdown("### Agendar Cita de Negociación")
        proveedor_cita = st.selectbox("Seleccionar Proveedor", ["Proveedor A (Económico)", "Proveedor B (Medio)", "Proveedor C (Premium)"])
        fecha_cita = st.date_input("Fecha sugerida", datetime.now())
        hora_cita = st.time_input("Hora requerida")
        motivo_cita = st.text_area("Motivo de la reunión", "Revisión de volumen de lotes y tiempos de entrega.")
        if st.button("Confirmar Solicitud de Cita", type="primary", use_container_width=True):
            st.success(f"Solicitud enviada para reunión con {proveedor_cita} el {fecha_cita} a las {hora_cita}.")

with col_action2:
    with st.popover("💬 Chat con Proveedores", use_container_width=True):
        st.markdown("### Centro de Mensajes Directo")
        prov_chat = st.selectbox("Canal de conversación", ["Proveedor A", "Proveedor B", "Proveedor C"])
        st.chat_message("assistant").write(f"Hola, estás conectado con la mesa de atención de {prov_chat}. ¿En qué podemos ayudarte con tu orden?")
        msg_user = st.text_input("Escribe tu mensaje aquí...")
        if st.button("Enviar Mensaje"):
            if msg_user:
                st.chat_message("user").write(msg_user)
                st.chat_message("assistant").write("Mensaje recibido. Un ejecutivo de cuenta te responderá a la brevedad.")

with col_action3:
    with st.popover("📋 Ver Políticas de Compra", use_container_width=True):
        st.markdown("### Políticas Operativas y Logísticas")
        st.write("- **Demanda esperada:** Lotes cerrados de 50 kg.")
        st.write("- **Ventana de urgencia:** Entrega garantizada <= 3 días para sucursales críticas.")
        st.write("- **Calidad mínima aprobada:** Evaluación de grano no menor a 70 puntos totales.")

st.markdown("<br>", unsafe_allow_html=True)

# 4. CAPTURA DE DATOS (CAMPOS NUMÉRICOS DIRECTOS)
st.markdown('<div class="section-header">Configuración del Pedido de Café</div>', unsafe_allow_html=True)

col_input1, col_input2 = st.columns(2)

with col_input1:
    presupuesto_max = st.number_input("Presupuesto Disponible ($ MXN)", min_value=10000, max_value=500000, value=130000, step=5000)

with col_input2:
    demanda_kg = st.number_input("Volumen Requerido (Kilogramos)", min_value=50, max_value=2000, value=600, step=50)

st.markdown("<br>", unsafe_allow_html=True)

# 5. MOTOR DE OPTIMIZACIÓN ESTABLE (SCIPY MILP)
lotes_requeridos = int(demanda_kg / 50)

c = np.array([-4.0, -7.0, -10.0])
integrality = np.ones(3)
bounds = Bounds(lb=np.zeros(3), ub=np.array([6.0, 5.0, 6.0]))

A = np.array([
    [1.0, 1.0, 1.0],
    [9000.0, 11000.0, 13000.0],
    [4.0, 7.0, 10.0],
    [1.0, 1.0, 0.0]
])

b_inf = np.array([lotes_requeridos, -np.inf, 70.0, 7.0], dtype=float)
b_sup = np.array([lotes_requeridos, presupuesto_max, np.inf, np.inf], dtype=float)

restricciones = LinearConstraint(A, b_inf, b_sup)
resultado = milp(c=c, integrality=integrality, bounds=bounds, constraints=restricciones)

# 6. PESTAÑAS Y CONTROL DE ERRORES AMIGABLE
if resultado.success:
    x_opt = np.round(resultado.x).astype(int)
    lotes_a, lotes_b, lotes_c = int(x_opt.item(0)), int(x_opt.item(1)), int(x_opt.item(2))
    
    calidad_total = (4 * lotes_a) + (7 * lotes_b) + (10 * lotes_c)
    gasto_total = (lotes_a * 9000) + (lotes_b * 11000) + (lotes_c * 13000)
    promedio_calidad = round(calidad_total / lotes_requeridos, 2) if lotes_requeridos > 0 else 0

    df_orden = pd.DataFrame({
        "Proveedor": ("Proveedor A (Económico)", "Proveedor B (Medio)", "Proveedor C (Premium)"),
        "Calidad del Grano": ("4 / 10", "7 / 10", "10 / 10"),
        "Precio por Lote": ("$9,000", "$11,000", "$13,000"),
        "Lotes a Solicitar": (lotes_a, lotes_b, lotes_c),
        "Kilos Totales": (lotes_a * 50, lotes_b * 50, lotes_c * 50),
        "Inversión": (lotes_a * 9000, lotes_b * 11000, lotes_c * 13000)
    })

    tab_pedido, tab_proveedores = st.tabs(["🛒 Resumen de Pedido Sugerido", "🏪 Directorio de Proveedores"])

    with tab_pedido:
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Índice de Calidad del Café", f"{promedio_calidad} / 10", delta=f"{calidad_total} pts totales")
        col_m2.metric("Inversión Calculada", f"${gasto_total:,.2f}", delta=f"${presupuesto_max - gasto_total:,.2f} remanente")
        col_m3.metric("Lotes Totales a Pedir", f"{lotes_requeridos} Lotes", delta=f"{lotes_a + lotes_b} de entrega rápida")

        st.markdown("<br>", unsafe_allow_html=True)
        col_t, col_g = st.columns([1.3, 1])

        with col_t:
            st.markdown("##### Detalle de la Orden de Compra")
            df_display = df_orden[["Proveedor", "Calidad del Grano", "Lotes a Solicitar", "Kilos Totales", "Inversión"]].copy()
            df_display["Inversión"] = df_display["Inversión"].apply(lambda x: f"${x:,.2f}")
            st.dataframe(df_display, hide_index=True, use_container_width=True)

            csv = df_orden.to_csv(index=False).encode('utf-8')
            st.download_button(label="Descargar Orden de Compra (CSV)", data=csv, file_name="Orden_Compra_Cafeterias.csv", mime="text/csv", type="primary", use_container_width=True)

        with col_g:
            st.markdown("##### Distribución del Pedido")
            df_grafico = df_orden[df_orden["Lotes a Solicitar"] > 0]
            fig = px.pie(df_grafico, values='Inversión', names='Proveedor', hole=0.45, color_discrete_sequence=('#A0522D', '#CD853F', '#DEB887'))
            fig.update_layout(margin=dict(t=20, b=20, l=10, r=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5))
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

    with tab_proveedores:
        st.markdown("##### Catálogo de Proveedores Evaluados")
        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            st.markdown("**Proveedor A (Económico)**\n- Calificación: 4/10\n- Precio/Lote: $9,000\n- Entrega: 2 días (Rápido)\n- Stock disponible: 6 lotes")
        with col_p2:
            st.markdown("**Proveedor B (Medio)**\n- Calificación: 7/10\n- Precio/Lote: $11,000\n- Entrega: 3 días (Rápido)\n- Stock disponible: 5 lotes")
        with col_p3:
            st.markdown("**Proveedor C (Premium)**\n- Calificación: 10/10\n- Precio/Lote: $13,000\n- Entrega: 5 días\n- Stock disponible: 6 lotes")

else:
    st.markdown("""
    <div class="notice-card">
        <h4 style="color: #8C4A27; margin: 0 0 8px 0;">No es posible cumplir con el pedido utilizando el presupuesto o el volumen indicado.</h4>
        <p style="margin: 0; color: #4A3B32;">Por favor, ajusta los valores de <b>presupuesto</b> o <b>demanda requerida</b> en las casillas superiores para encontrar una combinación factible.</p>
        <ul style="margin-top: 10px; padding-left: 20px; color: #665246; font-size: 14px;">
            <li>Verifica que el presupuesto sea suficiente para cubrir los kilogramos solicitados.</li>
            <li>Recuerda que la capacidad combinada de los 3 proveedores es de máximo 17 lotes (850 kg).</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
