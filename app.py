import streamlit as st
import pulp
import pandas as pd
import plotly.express as px

# 1. CONFIGURACIÓN DE LA PÁGINA (Para que luzca como un software empresarial)
st.set_page_config(page_title="OptiCoffee Supply", layout="wide")

st.title("☕ Sistema Inteligente de Asignación de Proveedores")
st.markdown("Generador automático de órdenes de compra para maximizar la calidad del café.")

# 2. PANEL IZQUIERDO (Barra lateral para el cliente)
st.sidebar.header("⚙️ Panel de Parámetros")
st.sidebar.write("Ajuste las restricciones de su negocio:")

# Deslizadores interactivos
presupuesto_max = st.sidebar.slider("Presupuesto Máximo ($)", min_value=100000, max_value=150000, value=130000, step=1000)
demanda_kg = st.sidebar.slider("Demanda de Café (Kg)", min_value=300, max_value=800, value=600, step=50)

# Botón de acción principal
optimizar = st.sidebar.button("Generar Orden Óptima", type="primary")

# 3. LÓGICA DE OPTIMIZACIÓN (Oculta al cliente)
lotes_requeridos = demanda_kg / 50  # Cada lote tiene 50 kg

# Inicializar el modelo de Maximización
prob = pulp.LpProblem("Maximizacion_Calidad", pulp.LpMaximize)

# Variables de decisión (Lotes a comprar, deben ser números enteros)
x1 = pulp.LpVariable("Proveedor_A", lowBound=0, upBound=6, cat='Integer')
x2 = pulp.LpVariable("Proveedor_B", lowBound=0, upBound=5, cat='Integer')
x3 = pulp.LpVariable("Proveedor_C", lowBound=0, upBound=6, cat='Integer')

# Función Objetivo: Maximizar Calidad
prob += 4*x1 + 7*x2 + 10*x3, "Calidad_Total"

# Restricciones
prob += x1 + x2 + x3 == lotes_requeridos, "Demanda_Exacta"
prob += 9000*x1 + 11000*x2 + 13000*x3 <= presupuesto_max, "Presupuesto_Maximo"
prob += 4*x1 + 7*x2 + 10*x3 >= 70, "Calidad_Minima"
prob += x1 + x2 >= 7, "Entregas_Rapidas"

# Se ejecuta el cálculo en milisegundos cuando inicia o cuando presionan el botón
prob.solve()
estado = pulp.LpStatus[prob.status]

# 4. PANEL DERECHO (Resultados y Gráficos)
if estado == "Optimal":
    # Extraer los resultados de las variables
    lotes_a = int(x1.varValue)
    lotes_b = int(x2.varValue)
    lotes_c = int(x3.varValue)
    
    calidad_total = int(pulp.value(prob.objective))
    gasto_total = (lotes_a*9000) + (lotes_b*11000) + (lotes_c*13000)
    
    # Tarjetas de Indicadores (KPIs)
    st.subheader("📊 Indicadores de la Orden")
    col1, col2, col3 = st.columns(3)
    col1.metric("Puntuación de Calidad", f"{calidad_total} pts")
    col2.metric("Presupuesto Utilizado", f"${gasto_total:,.2f}")
    col3.metric("Lotes Asignados", f"{int(lotes_requeridos)} lotes")
    
    st.divider()

    # Zona inferior: Tabla y Gráfico
    col_tabla, col_grafico = st.columns(2)
    
    with col_tabla:
        st.subheader("📋 Orden de Compra Generada")
        datos_orden = {
            "Proveedor": ["Proveedor A", "Proveedor B", "Proveedor C"],
            "Lotes a Comprar": [lotes_a, lotes_b, lotes_c],
            "Inversión": [f"${lotes_a*9000:,}", f"${lotes_b*11000:,}", f"${lotes_c*13000:,}"]
        }
        df_orden = pd.DataFrame(datos_orden)
        st.dataframe(df_orden, hide_index=True, use_container_width=True)
        
        st.success(f"✅ Se garantizan {lotes_a + lotes_b} lotes de entrega rápida (≤ 3 días).")

    with col_grafico:
        # Gráfico circular (Donut) usando Plotly
        df_grafico = pd.DataFrame({
            "Proveedor": ["A", "B", "C"],
            "Lotes": [lotes_a, lotes_b, lotes_c]
        })
        # Filtramos los proveedores a los que no se les compró nada
        df_grafico = df_grafico[df_grafico["Lotes"] > 0] 
        
        fig = px.pie(df_grafico, values='Lotes', names='Proveedor', hole=0.5, 
                     title="Distribución de Lotes por Proveedor",
                     color_discrete_sequence=px.colors.sequential.Teal)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

else:
    # Manejo de escenarios imposibles
    st.error("⚠️ Alerta: Con el presupuesto o demanda actual, es matemáticamente imposible cumplir todas las reglas del negocio (entregas rápidas, calidad mínima o capacidades máximas de proveedores).")
    st.info("💡 Sugerencia: Intente aumentar el presupuesto o reducir la demanda en el panel izquierdo.")
