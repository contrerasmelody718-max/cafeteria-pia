import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog

st.set_page_config(page_title="Optimizador Simplex - Compras de Café", layout="wide")

st.title("☕ Sistema Óptimo de Selección de Proveedores de Café")
st.markdown("Modelo de Programación Lineal (**Método Simplex**) con 3 variables y 6 restricciones dinámicas.")

# PANEL IZQUIERDO: RESTRICCIONES MÓVILES
st.sidebar.header("⚙️ Parámetros y Restricciones (6)")

presupuesto_max = st.sidebar.number_input(
    "R1. Presupuesto Máximo ($)", min_value=10000, max_value=1000000, value=130000, step=5000
)

demanda_min = st.sidebar.number_input(
    "R2. Demanda Mínima Requerida (Kg)", min_value=100, max_value=10000, value=1000, step=50
)

tiempo_max = st.sidebar.slider(
    "R3. Tiempo Promedio Máximo de Entrega (Días)", min_value=1.0, max_value=30.0, value=7.0, step=0.5
)

calidad_min_avg = st.sidebar.slider(
    "R4. Puntaje Mínimo de Calidad Promedio (SCA)", min_value=50.0, max_value=95.0, value=80.0, step=1.0
)

usar_r5 = st.sidebar.checkbox("Activar R5: Limitar Proveedor Económico", value=True)
limite_economico_pct = st.sidebar.slider(
    "   % Máximo permitido del Económico (X3)", min_value=0, max_value=100, value=15, disabled=not usar_r5
)

usar_r6 = st.sidebar.checkbox("Activar R6: Exigir Normativas Vigentes", value=True)

# PANEL CENTRAL: TABLA EDITABLE DE PROVEEDORES
st.subheader("1. Matriz de Proveedores (Edita los valores en tiempo real)")
st.info("💡 Haz doble clic en cualquier celda para modificar precios, puntajes, stock o tiempos.")

datos_iniciales = pd.DataFrame({
    "Variable": ["X1 (Premium)", "X2 (Medio)", "X3 (Económico)"],
    "Precio_Kg ($)": [180.0, 120.0, 85.0],
    "Puntaje_Calidad": [94.0, 83.0, 68.0],
    "Dias_Entrega": [5.0, 6.0, 12.0],
    "Stock_Max_Kg": [600.0, 1200.0, 2000.0],
    "Cumple_Normativa": [True, True, True]
})

df_prov = st.data_editor(
    datos_iniciales,
    column_config={
        "Variable": st.column_config.TextColumn("Proveedor", disabled=True),
        "Precio_Kg ($)": st.column_config.NumberColumn("Precio / Kg ($)", min_value=1.0, format="$%.2f"),
        "Puntaje_Calidad": st.column_config.NumberColumn("Calidad (0-100)", min_value=1.0, max_value=100.0),
        "Dias_Entrega": st.column_config.NumberColumn("Entrega (Días)", min_value=1.0, max_value=60.0),
        "Stock_Max_Kg": st.column_config.NumberColumn("Stock Máximo (Kg)", min_value=0.0),
        "Cumple_Normativa": st.column_config.CheckboxColumn("¿Cumple Normativas?")
    },
    hide_index=True,
    use_container_width=True
)

# MOTOR MATEMÁTICO (MÉTODO SIMPLEX)
precios = df_prov["Precio_Kg ($)"].values
calidades = df_prov["Puntaje_Calidad"].values
tiempos = df_prov["Dias_Entrega"].values
stocks = df_prov["Stock_Max_Kg"].values
normativas = df_prov["Cumple_Normativa"].values

c = -1 * calidades

A_ub = []
b_ub = []
nombres_restricciones = []

A_ub.append(precios)
b_ub.append(presupuesto_max)
nombres_restricciones.append("R1: Presupuesto ($)")

A_ub.append([-1.0, -1.0, -1.0])
b_ub.append(-demanda_min)
nombres_restricciones.append("R2: Demanda Mínima (Kg)")

A_ub.append(tiempos - tiempo_max)
b_ub.append(0.0)
nombres_restricciones.append("R3: Tiempo Entrega Promedio")

A_ub.append(calidad_min_avg - calidades)
b_ub.append(0.0)
nombres_restricciones.append("R4: Calidad Mínima Promedio")

if usar_r5:
    pct = limite_economico_pct / 100.0
    A_ub.append([-pct, -pct, 1.0 - pct])
    b_ub.append(0.0)
    nombres_restricciones.append(f"R5: Máx {limite_economico_pct}% Económico")

bounds = []
for i in range(3):
    max_permitido = stocks[i] if (not usar_r6 or normativas[i]) else 0.0
    bounds.append((0, max_permitido))

resultado = linprog(c, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")

# PANEL DE RESULTADOS Y TABLA SIMPLEX
st.divider()
st.subheader("2. Resultado Óptimo del Sistema")

if resultado.success:
    x_opt = resultado.x
    kilos_totales = np.sum(x_opt)
    gasto_total = np.sum(x_opt * precios)
    calidad_total_puntos = -resultado.fun
    calidad_promedio_final = calidad_total_puntos / kilos_totales if kilos_totales > 0 else 0
    tiempo_promedio_final = np.sum(x_opt * tiempos) / kilos_totales if kilos_totales > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Puntaje Calidad Promedio", f"{calidad_promedio_final:.2f} pts", f"Mínimo: {calidad_min_avg}")
    col2.metric("Presupuesto Utilizado", f"${gasto_total:,.2f}", f"Holgura: ${presupuesto_max - gasto_total:,.2f}")
    col3.metric("Volumen Total Comprado", f"{kilos_totales:,.1f} Kg", f"Meta: {demanda_min} Kg")
    col4.metric("Tiempo Entrega Promedio", f"{tiempo_promedio_final:.1f} días", f"Límite: {tiempo_max} días")

    col_izq, col_der = st.columns([1.2, 1])

    with col_izq:
        st.markdown("#### 📦 Plan Óptimo de Compra por Proveedor")
        porcentajes = np.round((x_opt / kilos_totales) * 100, 1) if kilos_totales > 0 else [0.0, 0.0, 0.0]
        df_res = pd.DataFrame({
            "Proveedor": df_prov["Variable"],
            "Kilos a Comprar (X)": np.round(x_opt, 2),
            "% del Lote": porcentajes,
            "Inversión ($)": np.round(x_opt * precios, 2),
            "Aporte Calidad (Pts)": np.round(x_opt * calidades, 1)
        })
        st.dataframe(df_res, hide_index=True, use_container_width=True)

    with col_der:
        st.markdown("#### 📊 Distribución Visual de Kilos")
        chart_data = pd.DataFrame({"Kilos": x_opt}, index=df_prov["Variable"])
        st.bar_chart(chart_data)

    with st.expander("🔍 Ver Matriz Simplex, Holguras (S) y Precios Sombra"):
        holguras = resultado.slack
        precios_sombra = resultado.ineqlin.marginals if hasattr(resultado, "ineqlin") else [0.0]*len(holguras)
        
        df_simplex = pd.DataFrame({
            "Restricción": nombres_restricciones,
            "Holgura (S)": np.round(holguras, 2),
            "Precio Sombra (Marginal)": np.round(-np.array(precios_sombra), 4),
            "Estado": ["Saturada (Límite alcanzado)" if abs(h) < 1e-4 else "Con margen disponible" for h in holguras]
        })
        st.dataframe(df_simplex, hide_index=True, use_container_width=True)

else:
    st.error("⚠️ **Solución Infactible:** Con los límites actuales es matemáticamente imposible cumplir todas las restricciones al mismo tiempo.")
    st.warning("💡 **Sugerencia:** Intenta aumentar el presupuesto ($130,000), reducir los kilos mínimos requeridos, bajar un poco el puntaje mínimo de calidad o aumentar los días de entrega.")
