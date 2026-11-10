import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.optimize import milp, LinearConstraint, Bounds

st.set_page_config(page_title="OptiCoffee Supply ERP", layout="wide", page_icon="☕")

st.markdown("""
<style>
    .main { background-color: #F8FAFC; }
    .header-box { background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); color: #FFFFFF; padding: 24px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
    .header-title { font-size: 26px; font-weight: 700; letter-spacing: 0.5px; margin: 0; color: #FFFFFF; }
    .header-subtitle { font-size: 14px; color: #94A3B8; margin-top: 6px; }
    div[data-testid="stMetric"] { background-color: #FFFFFF; border: 1px solid #E2E8F0; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .status-badge-success { background-color: #DEF7EC; color: #03543F; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 4px; display: inline-block; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { height: 44px; border-radius: 6px; padding: 0px 20px; background-color: #FFFFFF; border: 1px solid #E2E8F0; font-weight: 500; }
    .stTabs [aria-selected="true"] { background-color: #1E293B !important; color: #FFFFFF !important; border-color: #1E293B !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header-box"><div class="header-title">OPTICOFFEE | SISTEMA INTEGRAL DE OPTIMIZACIÓN DE COMPRAS</div><div class="header-subtitle">Módulo Ejecutivo de Asignación Inteligente de Proveedores por Programación Lineal Entera</div></div>', unsafe_allow_html=True)

st.sidebar.markdown("### CONFIGURACIÓN OPERATIVA")
st.sidebar.markdown("Ajuste los parámetros del escenario actual:")

presupuesto_max = st.sidebar.slider("Presupuesto Máximo ($)", min_value=100000, max_value=150000, value=130000, step=1000)
demanda_kg = st.sidebar.slider("Demanda Requerida (Kg)", min_value=300, max_value=800, value=600, step=50)

st.sidebar.markdown("---")
st.sidebar.markdown("**Estado del Algoritmo:**")
st.sidebar.markdown('<span class="status-badge-success">MOTOR SIMPLEX LP: ACTIVO</span>', unsafe_allow_html=True)

with st.sidebar.expander("Ver Parámetros de Proveedores"):
    st.markdown("**Proveedor A (Económico)**\n- Costo: $9,000 / lote\n- Calidad: 4 / 10\n- Tiempo: 2 días\n- Capacidad: Hasta 6 lotes\n\n**Proveedor B (Medio)**\n- Costo: $11,000 / lote\n- Calidad: 7 / 10\n- Tiempo: 3 días\n- Capacidad: Hasta 5 lotes\n\n**Proveedor C (Premium)**\n- Costo: $13,000 / lote\n- Calidad: 10 / 10\n- Tiempo: 5 días\n- Capacidad: Hasta 6 lotes")

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

if resultado.success:
    x_opt = np.round(resultado.x).astype(int)
    lotes_a, lotes_b, lotes_c = int(x_opt.item(0)), int(x_opt.item(1)), int(x_opt.item(2))
    calidad_total = (4 * lotes_a) + (7 * lotes_b) + (10 * lotes_c)
    gasto_total = (lotes_a * 9000) + (lotes_b * 11000) + (lotes_c * 13000)
    promedio_calidad = round(calidad_total / lotes_requeridos, 2)

    df_orden = pd.DataFrame({
        "Proveedor": ("Proveedor A (Económico)", "Proveedor B (Medio)", "Proveedor C (Premium)"),
        "Calidad Individual": ("4 / 10", "7 / 10", "10 / 10"),
        "Costo Unitario": (9000, 11000, 13000),
        "Lotes Adquiridos": (lotes_a, lotes_b, lotes_c),
        "Volumen (Kg)": (lotes_a * 50, lotes_b * 50, lotes_c * 50),
        "Subtotal Inversión": (lotes_a * 9000, lotes_b * 11000, lotes_c * 13000),
        "Puntos Calidad Aportados": (lotes_a * 4, lotes_b * 7, lotes_c * 10)
    })

    tab_dashboard, tab_restricciones, tab_exportar = st.tabs(["DASHBOARD Y ORDEN ÓPTIMA", "VERIFICACIÓN DE RESTRICCIONES", "EXPORTACIÓN Y DOCUMENTACIÓN"])

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
            st.download_button(label="DESCARGAR ORDEN DE COMPRA (CSV)", data=df_orden.to_csv(index=False).encode('utf-8'), file_name="Orden_Compra_OptiCoffee.csv", mime="text/csv", type="primary", use_container_width=True)

        with col_grafico_main:
            st.markdown("##### Distribución del Presupuesto por Proveedor")
            df_grafico = df_orden[df_orden["Lotes Adquiridos"] > 0]
            fig = px.pie(df_grafico, values='Subtotal Inversión', names='Proveedor', hole=0.4, color_discrete_sequence=('#1E293B', '#475569', '#94A3B8'))
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)

    with tab_restricciones:
        st.markdown("#### Auditoría de Cumplimiento de las 7 Restricciones del Negocio")
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.success(f"1. Demanda Exacta: {lotes_a + lotes_b + lotes_c} de {lotes_requeridos} lotes — CUMPLIDO")
            st.success(f"2. Presupuesto Máximo: ${gasto_total:,.2f} de ${presupuesto_max:,.2f} — CUMPLIDO")
            st.success(f"3. Calidad Mínima: {calidad_total} pts vs 70 pts exigidos — CUMPLIDO")
            st.success(f"4. Entregas Urgentes (<= 3 días): {lotes_a + lotes_b} lotes vs 7 mínimos — CUMPLIDO")
        with col_res2:
            st.success(f"5. Capacidad Máxima Proveedor A: {lotes_a} de 6 lotes — CUMPLIDO")
            st.success(f"6. Capacidad Máxima Proveedor B: {lotes_b} de 5 lotes — CUMPLIDO")
            st.success(f"7. Capacidad Máxima Proveedor C: {lotes_c} de 6 lotes — CUMPLIDO")

    with tab_exportar:
        st.markdown("#### Informe Técnico y Matriz Completa")
        st.dataframe(df_orden, hide_index=True, use_container_width=True)
        st.markdown("##### Resumen de Parámetros del Algoritmo Simplex")
        st.code(f"Función Objetivo: Max Z = 4*(Proveedor_A) + 7*(Proveedor_B) + 10*(Proveedor_C)\nVariables de Decisión: Proveedor_A = {lotes_a}, Proveedor_B = {lotes_b}, Proveedor_C = {lotes_c}\nValor Óptimo Alcanzado (Z): {calidad_total} Puntos de Calidad\nCosto Total de Adquisición: ${gasto_total:,.2f} MXN", language="text")

else:
    st.error(f"ALERTA DE FACTIBILIDAD: Con Presupuesto (${presupuesto_max:,.2f}) y Demanda ({demanda_kg} kg), es matemáticamente imposible cumplir las 7 restricciones simultáneamente. Ajuste los parámetros en el panel lateral.")
