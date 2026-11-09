import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from scipy.optimize import milp, LinearConstraint, Bounds

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="OptiCoffee Supply", layout="wide")

st.title("☕ Sistema Inteligente de Asignación de Proveedores")
st.markdown("Generador automático de órdenes de compra por lotes (50 kg) para maximizar la calidad del café.")

# 2. PANEL IZQUIERDO (Barra lateral interactiva)
st.sidebar.header("⚙️ Panel de Parámetros")
st.sidebar.write("Ajuste las restricciones de su negocio:")

presupuesto_max = st.sidebar.slider("R1. Presupuesto Máximo ($)", min_value=80000, max_value=200000, value=130000, step=1000)
demanda_kg = st.sidebar.slider("R2. Demanda de Café (Kg)", min_value=300, max_value=850, value=600, step=50)
calidad_minima_req = st.sidebar.slider("R3. Calidad Total Mínima (Pts)", min_value=30, max_value=150, value=70, step=5)
entregas_rapidas_min = st.sidebar.slider("R4. Lotes Mínimos Entrega Rápida (A + B)", min_value=0, max_value=11, value=7, step=1)

st.sidebar.subheader("📦 Capacidad Máxima por Proveedor (Lotes)")
cap_a = st.sidebar.number_input("R5. Máx Lotes Proveedor A (Económico - 4 pts)", min_value=0, max_value=20, value=6)
cap_b = st.sidebar.number_input("R6. Máx Lotes Proveedor B (Medio - 7 pts)", min_value=0, max_value=20, value=5)
cap_c = st.sidebar.number_input("R7. Máx Lotes Proveedor C (Premium - 10 pts)", min_value=0, max_value=20, value=6)

# 3. LÓGICA DE OPTIMIZACIÓN (Motor SciPy MILP / Simplex)
lotes_requeridos = int(demanda_kg / 50)

# Función Objetivo: Maximizar 4*x1 + 7*x2 + 10*x3 (en SciPy se minimiza multiplicando por -1)
c = np.array([-4.0, -7.0, -10.0])

# Variables enteras (1 = Integer)
integrality = np.array([1, 1, 1])

# Límites individuales (R5, R6, R7)
bounds = Bounds(lb=np.array([0, 0, 0]), ub=np.array([cap_a, cap_b, cap_c]))

# Matriz de Restricciones (R1, R2, R3, R4)
A = np.array([
    [1.0, 1.0, 1.0],          # R2. Demanda Exacta
    [9000.0, 11000.0, 13000.0], # R1. Presupuesto Máximo
    [4.0, 7.0, 10.0],         # R3. Calidad Total Mínima
    [1.0, 1.0, 0.0]           # R4. Entregas Rápidas (A + B)
])

b_inf = np.array([lotes_requeridos, -np.inf, calidad_minima_req, entregas_rapidas_min])
b_sup = np.array([lotes_requeridos, presupuesto_max, np.inf, np.inf])

restricciones = LinearConstraint(A, b_inf, b_sup)

# Ejecutar el cálculo matemático
resultado = milp(c=c, integrality=integrality, bounds=bounds, constraints=restricciones)

# 4. PANEL DERECHO (Resultados y Gráficos)
if resultado.success:
    x_opt = np.round(resultado.x).astype(int)
    lotes_a, lotes_b, lotes_c = int(x_opt[0]), int(x_opt[1]), int(x_opt[2])
    
    calidad_total = (4 * lotes_a) + (7 * lotes_b) + (10 * lotes_c)
    calidad_promedio = calidad_total / lotes_requeridos if lotes_requeridos > 0 else 0
    gasto_total = (lotes_a * 9000) + (lotes_b * 11000) + (lotes_c * 13000)
    ahorro = presupuesto_max - gasto_total
    
    # Tarjetas de Indicadores (KPIs)
    st.subheader("📊 Indicadores de la Orden Óptima")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Puntuación Total", f"{calidad_total} pts", f"Promedio: {calidad_promedio:.1f} / 10")
    col2.metric("Presupuesto Utilizado", f"${gasto_total:,.0f}", f"Holgura: ${ahorro:,.0f}")
    col3.metric("Total Lotes (50 kg)", f"{lotes_requeridos} lotes", f"{demanda_kg} Kg exactos")
    col4.metric("Lotes Rápidos (A + B)", f"{lotes_a + lotes_b} lotes", f"Mínimo: {entregas_rapidas_min}")

    st.divider()

    # Tabla y Gráfica lado a lado
    col_tabla, col_graf = st.columns([1.2, 1])

    df_resultados = pd.DataFrame({
        "Proveedor": list(("Proveedor A (Económico)", "Proveedor B (Medio)", "Proveedor C (Premium)")),
        "Calidad (1-10)": list((4, 7, 10)),
        "Costo por Lote ($)": list((9000, 11000, 13000)),
        "Lotes Asignados (X)": list((lotes_a, lotes_b, lotes_c)),
        "Kilos Totales (Kg)": list((lotes_a * 50, lotes_b * 50, lotes_c * 50)),
        "Inversión Total ($)": list((lotes_a * 9000, lotes_b * 11000, lotes_c * 13000))
    })

    with col_tabla:
        st.subheader("📋 Desglose de Orden de Compra")
        st.dataframe(df_resultados, hide_index=True, use_container_width=True)

    with col_graf:
        st.subheader("🍩 Distribución de Inversión ($)")
        fig = px.pie(
            df_resultados[df_resultados["Lotes Asignados (X)"] > 0],
            values="Inversión Total ($)",
            names="Proveedor",
            hole=0.4,
            color_discrete_sequence=list(("#A67B5B", "#6F4E37", "#3B2F2F"))
        )
        st.plotly_chart(fig, use_container_width=True)

    # Desplegable con el estado de las 7 restricciones
    with st.expander("🔍 Ver Verificación de las 7 Restricciones"):
        df_rest = pd.DataFrame({
            "Restricción": list((
                "R1. Presupuesto Máximo",
                "R2. Demanda Exacta",
                "R3. Calidad Total Mínima",
                "R4. Entregas Rápidas (A + B)",
                "R5. Capacidad Máx Proveedor A",
                "R6. Capacidad Máx Proveedor B",
                "R7. Capacidad Máx Proveedor C"
            )),
            "Valor Obtenido": list((
                f"${gasto_total:,.0f}",
                f"{lotes_requeridos} lotes",
                f"{calidad_total} pts",
                f"{lotes_a + lotes_b} lotes",
                f"{lotes_a} lotes",
                f"{lotes_b} lotes",
                f"{lotes_c} lotes"
            )),
            "Límite Establecido": list((
                f"<= ${presupuesto_max:,.0f}",
                f"== {lotes_requeridos} lotes",
                f">= {calidad_minima_req} pts",
                f">= {entregas_rapidas_min} lotes",
                f"<= {cap_a} lotes",
                f"<= {cap_b} lotes",
                f"<= {cap_c} lotes"
            )),
            "Estado": list(("✅ Cumplida",) * 7)
        })
        st.dataframe(df_rest, hide_index=True, use_container_width=True)

else:
    st.error("⚠️ **Solución Infactible:** No existe ninguna combinación de lotes que cumpla todas las restricciones al mismo tiempo.")
    st.info("💡 **Sugerencia:** Intenta subir el presupuesto máximo, reducir los kilos demandados o bajar el mínimo de entregas rápidas (A + B).")
