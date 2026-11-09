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
st.sidebar.divider()
optimizar = st.sidebar.button("Generar Orden Óptima", type="primary", use_container_width=True)

# 3. LÓGICA DE OPTIMIZACIÓN (Oculta al cliente)
# Aseguramos que los lotes sean un número entero
lotes_requeridos = int(demanda_kg / 50)  

# Inicializar el modelo de Maximización
prob = pulp.LpProblem("Maximizacion_Calidad", pulp.LpMaximize)

# Variables de decisión (Lotes a comprar, definidos de la forma más estable para la nube)
x1 = pulp.LpVariable("Proveedor_A", lowBound=0, cat='Integer')
x2 = pulp.LpVariable("Proveedor_B", lowBound=0, cat='Integer')
x3 = pulp.LpVariable("Proveedor_C", lowBound=0, cat='Integer')

# Función Objetivo: Maximizar Calidad
prob += 4*x1 + 7*x2 + 10*x3, "Calidad_Total"

# Restricciones Originales
prob += x1 + x2 + x3 == lotes_requeridos, "Demanda_Exacta"
prob += 9000*x1 + 11000*x2 + 13000*x3 <= presupuesto_max, "Presupuesto_Maximo"
prob += 4*x1 + 7*x2 + 10*x3 >= 70, "Calidad_Minima"
prob += x1 + x2 >= 7, "Entregas_Rapidas"

# Capacidades Máximas de Proveedores (Pasadas como restricciones para evitar errores)
prob += x1 <= 6, "Capacidad_A"
prob += x2 <= 5, "Capacidad_B"
prob += x3 <= 6, "Capacidad_C"

# Ejecutar el cálculo matemático
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
    col1.metric("Puntuación de Calidad", f"{calidad
