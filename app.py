import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.optimize import milp, LinearConstraint, Bounds

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="OptiCoffee Supply", layout="wide", page_icon="☕")

# Control del estado de la pantalla (Navegación por botones)
if 'pantalla' not in st.session_state:
    st.session_state.pantalla = "Dashboard"

# 2. ENCABEZADO Y BARRA SUPERIOR DE BOTONES DE NAVEGACIÓN
st.title("☕ Sistema Inteligente de Asignación de Proveedores")
st.markdown("Generador automático de órdenes de compra para maximizar la calidad del café.")

# Botón desplegable / emergente para ver las 7 restricciones rápidamente desde cualquier pantalla
with st.popover("📜 Ver las 7 Restricciones del Modelo (Firma de Contrato)", help="Haga clic para consultar las reglas matemáticas activas"):
    st.markdown("### 📋 7 Restricciones Validadas del Negocio")
    st.markdown("""
    1. **Demanda Exacta:** Se deben surtir exactamente 12 lotes (600 kg de café).
    2. **Presupuesto Máximo:** La inversión total no puede superar los $130,000.
    3. **Calidad Mínima:** La suma de calidad acumulada debe ser de al menos 70 puntos.
    4. **Entregas Rápidas:** Al menos 7 lotes deben ser entregados en 3 días o menos (Proveedores A y B).
    5. **Capacidad Proveedor A:** Máximo 6 lotes disponibles.
    6. **Capacidad Proveedor B:** Máximo 5 lotes disponibles.
    7. **Capacidad Proveedor C:** Máximo 6 lotes disponibles.
    """)

st.divider()

# BOTONES DE NAVEGACIÓN ENTRE PANTALLAS
col_nav1, col_nav2, col_nav3 = st.columns(3)

with col_nav1:
    if st.button("📊 Pantalla 1: Dashboard Principal", use_container_width=True, type="primary" if st.session_state.pantalla == "Dashboard" else "secondary"):
        st.session_state.pantalla = "Dashboard"
        st.rerun()

with col_nav2:
    if st.button("🔍 Pantalla 2: Análisis de Restricciones", use_container_width=True, type="primary" if st.session_state.pantalla == "Restricciones" else "secondary"):
        st.session_state.pantalla = "Restricciones"
        st.rerun()

with col_nav3:
    if st.button("📄 Pantalla 3: Orden de Compra y Exportación", use_container_width=True, type="primary" if st.session_state.pantalla == "Orden" else "secondary"):
        st.session_state.pantalla = "Orden"
        st.rerun()

st.divider()

# 3. PANEL IZQUIERDO DE PARÁMETROS (Sidebar)
st.sidebar.header("⚙️ Panel de Parámetros")
st.sidebar.write("Ajuste las restricciones de su negocio:")

presupuesto_max = st.sidebar.slider("Presupuesto Máximo ($)", min_value=100000, max_value=150000, value=130000, step=1000)
demanda_kg = st.sidebar.slider("Demanda de Café (Kg)", min_value=300, max_value=800, value=600, step=50)

st.sidebar.divider()
st.sidebar.success("✅ Algoritmo Simplex Activo")

# 4. LÓGICA DE OPTIMIZACIÓN MATEMÁTICA (Motor estable SciPy MILP)
lotes_requeridos = int(demanda_kg / 50)

# Maximizar 4*x1 + 7*x2 + 10*x3
c = np.array([-4.0, -7.0, -10.0])
integrality = np.ones(3)

# Restricciones 5, 6 y 7: Capacidades máximas (x1 <= 6, x2 <= 5, x3 <= 6)
bounds = Bounds(lb=np.zeros(3), ub=np.array([6.0, 5.0, 6.0]))

# Restricciones 1, 2, 3 y 4
A = np.array([
    [1.0, 1.0, 1.0],            # R1: Demanda Exacta
    [9000.0, 11000.0, 13000.0], # R2: Presupuesto Máximo
    [4.0, 7.0, 10.0],           # R3: Calidad Mínima (>= 70)
    [1.0, 1.0, 0.0]             # R4: Entregas Rápidas (A + B >= 7)
])

b_inf = np.array([lotes_requeridos, -np.inf, 70.0, 7.0], dtype=float)
b_sup = np.array([lotes_requeridos, presupuesto_max, np.inf, np.inf], dtype=float)

restricciones = LinearConstraint(A, b_inf, b_sup)
resultado = milp(c=c, integrality=integrality, bounds=bounds, constraints=restricciones)

# 5. RENDERIZADO DE PANTALLAS SEGÚN EL BOTÓN SELECCIONADO
if resultado.success:
    x_opt = np.round(resultado.x).astype(int)
    lotes_a = int(x_opt.item(0))
    lotes_b = int(x_opt.item(1))
    lotes_c = int(x_opt.item(2))
    
    calidad_total = (4 * lotes_a) + (7 * lotes_b) + (10 * lotes_c)
    gasto_total = (lotes_a * 9000) + (lotes_b * 11000) + (lotes_c * 13000)

    datos_orden = {
        "Proveedor": ("Proveedor A (Económico)", "Proveedor B (Medio)", "Proveedor C (Premium)"),
        "Lotes a Comprar": (lotes_a, lotes_b, lotes_c),
        "Costo por Lote ($)": (9000, 11000, 13000),
        "Inversión Total ($)": (lotes_a * 9000, lotes_b * 11000, lotes_c * 13000),
        "Puntos Calidad": (lotes_a * 4, lotes_b * 7, lotes_c * 10)
    }
    df_orden = pd.DataFrame(datos_orden)

    # --- PANTALLA 1: DASHBOARD PRINCIPAL ---
    if st.session_state.pantalla == "Dashboard":
        st.subheader("📊 Pantalla Principal: Indicadores de la Orden")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Puntuación Total", f"{calidad_total} pts")
        col2.metric("Presupuesto Utilizado", f"${gasto_total:,.2f}")
        col3.metric("Lotes Totales", f"{int(lotes_requeridos)} lotes")
        col4.metric("Lotes Rápidos (A+B)", f"{lotes_a + lotes_b} lotes")
        
        st.divider()
        
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.markdown("### 🍩 Distribución de la Inversión")
            df_grafico = df_orden[df_orden["Lotes a Comprar"] > 0] 
            fig = px.pie(df_grafico, values='Inversión Total ($)', names='Proveedor', hole=0.5, 
                         color_discrete_sequence=px.colors.sequential.Teal)
            st.plotly_chart(fig, use_container_width=True)

        with col_graf2:
            st.markdown("### 📈 Aportación de Calidad por Proveedor")
            fig_bar = px.bar(df_grafico, x='Proveedor', y='Puntos Calidad', color='Proveedor',
                             color_discrete_sequence=px.colors.sequential.Teal)
            st.plotly_chart(fig_bar, use_container_width=True)

    # --- PANTALLA 2: ANÁLISIS DE RESTRICCIONES ---
    elif st.session_state.pantalla == "Restricciones":
        st.subheader("🔍 Pantalla de Verificación de Restricciones")
        st.write("Esta pantalla confirma cómo el modelo matemático cumple cada regla del negocio:")

        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.info(f"**Restricción 1 (Demanda):** {lotes_a + lotes_b + lotes_c} de {lotes_requeridos} lotes (Cumplido ✅)")
            st.info(f"**Restricción 2 (Presupuesto):** ${gasto_total:,.2f} de ${presupuesto_max:,.2f} máximo (Cumplido ✅)")
            st.info(f"**Restricción 3 (Calidad Mínima):** {calidad_total} pts acumulados vs 70 pts mínimos (Cumplido ✅)")
            st.info(f"**Restricción 4 (Urgencia <= 3 días):** {lotes_a + lotes_b} lotes entregados vs 7 mínimos (Cumplido ✅)")

        with col_r2:
            st.success(f"**Restricción 5 (Capacidad A):** {lotes_a} de 6 lotes permitidos (Dentro del límite ✅)")
            st.success(f"**Restricción 6 (Capacidad B):** {lotes_b} de 5 lotes permitidos (Dentro del límite ✅)")
            st.success(f"**Restricción 7 (Capacidad C):** {lotes_c} de 6 lotes permitidos (Dentro del límite ✅)")

    # --- PANTALLA 3: ORDEN DE COMPRA Y EXPORTACIÓN ---
    elif st.session_state.pantalla == "Orden":
        st.subheader("📄 Pantalla de Orden de Compra Ejecutiva")
        st.write("Detalle formal para enviar al departamento de finanzas y compras:")
        
        st.dataframe(df_orden, hide_index=True, use_container_width=True)
        
        st.divider()
        csv = df_orden.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Orden de Compra en formato CSV",
            data=csv,
            file_name='Orden_Compra_OptiCoffee.csv',
            mime='text/csv',
            type="primary",
            use_container_width=True
        )

else:
    st.error("⚠️ Alerta: Con el presupuesto o demanda actual, es matemáticamente imposible cumplir todas las reglas del negocio.")
