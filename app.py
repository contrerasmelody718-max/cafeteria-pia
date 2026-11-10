import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.optimize import milp, LinearConstraint, Bounds

# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO EMPRESARIAL
st.set_page_config(
    page_title="OptiCoffee Supply ERP", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para una interfaz ejecutiva y limpia
st.markdown("""
<style>
    .main {
        background-color: #F8FAFC;
    }
    .header-box {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: #FFFFFF;
        padding: 24px;
        border-radius: 12px;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .header-title {
        font-size: 26px;
        font-weight: 700;
        letter-spacing: 0.5px;
        margin: 0;
        color: #FFFFFF;
    }
    .header-subtitle {
        font-size: 14px;
        color: #94A3B8;
        margin-top: 6px;
    }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .status-badge-success {
        background-color: #DEF7EC;
        color: #03543F;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 4px;
        display: inline-block;
    }
    .status-badge-warning {
        background-color: #FDE8E8;
        color: #9B1C1C;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 4px;
        display: inline-block;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 6px;
        padding: 0px 20px;
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        border-color: #1E293B !important;
    }
</style>
""", unsafe_allow_html=True)

# 2. ENCABEZADO CORPORATIVO
st.markdown("""
<div class="header-box">
    <div class="header-title">OPTICOFFEE | SISTEMA INTEGRAL DE OPTIMIZACIÓN DE COMPRAS</div>
    <div class="header-subtitle">Módulo Ejecutivo de Asignación Inteligente de Proveedores por Programación Lineal Entera</div>
</div>
""", unsafe_allow_html=True)

# 3. PANEL LATERAL (PARÁMETROS OPERATIVOS)
st.sidebar.markdown("### CONFIGURACIÓN OPERATIVA")
st.sidebar.markdown("Ajuste los parámetros del escenario actual:")

presupuesto_max = st.sidebar.slider(
    "Presupuesto Máximo ($)", 
    min_value=100000, 
    max_value=150000, 
    value=130000, 
    step=1000,
    help="Límite financiero autorizado para la adquisición de la orden."
)

demanda_kg = st.sidebar.slider(
    "Demanda Requerida (Kg)", 
    min_value=300, 
    max_value=800, 
    value=600, 
    step=50,
    help="Volumen total de café necesario para abastecer las sucursales."
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Estado del Algoritmo:**")
st.sidebar.markdown('<span class="status-badge-success">MOTOR SIMPLEX LP: ACTIVO</span>', unsafe_allow_html=True)

with st.sidebar.expander("Ver Parámetros de Proveedores"):
    st.markdown("""
    **Proveedor A (Económico)**
    - Costo: $9,000 / lote
    - Calidad: 4 / 10
    - Tiempo: 2 días (Rápido)
    - Capacidad: Hasta 6 lotes
    
    **Proveedor B (Medio)**
    - Costo: $11,000 / lote
    - Calidad: 7 / 10
    - Tiempo: 3 días (Rápido)
    - Capacidad: Hasta 5 lotes
    
    **Proveedor C (Premium)**
    - Costo: $13,000 / lote
    - Calidad: 10 / 10
    - Tiempo: 5 días
    - Capacidad: Hasta 6 lotes
    """)

# 4. MODELO DE OPTIMIZACIÓN MATEMÁTICA (Motor estable SciPy MILP)
lotes_requeridos = int(demanda_kg / 50)

# Función Objetivo: Maximizar 4*x1 + 7*x2 + 10*x3
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

# 5. RENDERIZADO DE LA INTERFAZ USUARIO
if resultado.success:
    x_opt = np.round(resultado.x).astype(int)
    lotes_a = int(x_opt.item(0))
    lotes_b = int(x_opt.item(1))
    lotes_c = int(x_opt.item(2))
    
    calidad_total = (4 * lotes_a) + (7 * lotes_b) + (10 * lotes_c)
    gasto_total = (lotes_a * 9000) + (lotes_b * 11000) + (lotes_c * 13000)
    promedio_calidad = round(calidad_total / lotes_requeridos, 2)

    # Estructura de Datos
    datos_orden = {
        "Proveedor": ("Proveedor A (Económico)", "Proveedor B (Medio)", "Proveedor C (Premium)"),
        "Calidad Individual": ("4 / 10", "7 / 10", "10 / 10"),
        "Costo Unitario": (9000, 11000, 13000),
        "Lotes Adquiridos": (lotes_a, lotes_b, lotes_c),
        "Volumen (Kg)": (lotes_a * 50, lotes_b * 50, lotes_c * 50),
        "Subtotal Inversión": (lotes_a * 9000, lotes_b * 11000, lotes_c * 13000),
        "Puntos Calidad Aportados": (lotes_a * 4, lotes_b * 7, lotes_c * 10)
    }
    df_orden = pd.DataFrame(datos_orden)

    # NAVEGACIÓN POR PESTAÑAS ELEGANTES
    tab_dashboard, tab_restricciones, tab_exportar = st.tabs([
        "DASHBOARD Y ORDEN ÓPTIMA", 
        "VERIFICACIÓN DE RESTRICCIONES", 
        "EXPORTACIÓN Y DOCUMENTACIÓN"
    ])

    # --- PESTAÑA 1: DASHBOARD ---
    with tab_dashboard:
        st.markdown("#### Resumen General de la Solución Obtenida")
        
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        col_kpi1.metric("Puntuación de Calidad", f"{calidad_total} pts", delta=f"Promedio: {promedio_calidad}/10")
        col_kpi2.metric("Presupuesto Utilizado", f"${gasto_total:,.2f}", delta=f"Disponible: ${presupuesto_max - gasto_total:,.2f}")
        col_kpi3.metric("Lotes Totales (50 kg)", f"{int(lotes_requeridos)} lotes", delta=f"Total: {demanda_kg} Kg")
        col_kpi4.metric("Lotes Entrega Rápida", f"{lotes_a + lotes_b} lotes", delta="Cumple plazo <= 3 días")

        st.markdown("<br>", unsafe_allow_html=True)

        col_tabla_main, col_grafico_main = st.columns([1.4, 1])

        with col_tabla_main:
            st.markdown("##### Orden de Compra Generada")
            df_display = df_orden[["Proveedor", "Calidad Individual", "Lotes Adquiridos", "Subtotal Inversión", "Puntos Calidad Aportados"]].copy()
            df_display["Subtotal Inversión"] = df_display["Subtotal Inversión"].apply(lambda x: f"${x:,.2f}")
            
            st.dataframe(df_display, hide_index=True, use_container_width=True)
            
            st.download_button(
                label="DESCARGAR ORDEN DE COMPRA (CSV)",
                data=df_orden.to_csv(index=False).encode('utf-8'),
                file_name="Orden_Compra_OptiCoffee.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )

        with col_grafico_main:
            st.markdown("##### Distribución del Presupuesto por Proveedor")
            df_grafico = df_orden[df_orden["Lotes Adquiridos"] > 0]
            
            fig = px.pie(
                df_grafico, 
                values='Subtotal Inversión', 
                names='Proveedor', 
                hole=0.4,
                color_discrete_sequence=('#1E293B', '#475569', '#94A3B8')
            )
            fig.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

    # --- PESTAÑA 2: VERIFICACIÓN DE RESTRICCIONES ---
    with tab_restricciones:
        st.markdown("#### Auditoría de Cumplimiento de las 7 Restricciones del Negocio")
        st.markdown("El sistema valida matemáticamente que cada parámetro se encuentre dentro de los márgenes estipulados:")

        col_res1, col_res2 = st.columns(2)

        with col_res1:
            st.markdown("""
            **1. Restricción de Demanda Exacta:**
            - Requerido: %d lotes (%d kg)
            - Asignado: %d lotes (%d kg)
            - Estado: <span class="status-badge-success">CUMPLIDO</span>
            <hr style="margin:10px 0;">
            **2. Restricción de Presupuesto Máximo:**
            - Límite Autorizado: $%s
            - Inversión Calculada: $%s
            - Estado: <span class="status-badge-success">CUMPLIDO</span>
            <hr style="margin:10px 0;">
            **3. Restricción de Calidad Mínima:**
            - Umbral Exigido: 70 puntos
            - Obtenido: %d puntos
            - Estado: <span class="status-badge-success">CUMPLIDO</span>
            <hr style="margin:10px 0;">
            **4. Restricción de Entregas Urgentes (<= 3 días):**
            - Mínimo Requerido: 7 lotes
            - Asignado (A + B): %d lotes
            - Estado: <span class="status-badge-success">CUMPLIDO</span>
            """ % (
                lotes_requeridos, demanda_kg,
                lotes_a + lotes_b + lotes_c, (lotes_a + lotes_b + lotes_c) * 50,
                f"{presupuesto_max:,.2f}", f"{gasto_total:,.2f}",
                calidad_total,
                lotes_a + lotes_b
            ), unsafe_allow_html=True)

        with col_res2:
            st.markdown("""
