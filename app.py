# -*- coding: utf-8 -*-
"""
Created on Tue Jun 16 16:33:08 2026
Codigo APP Episeq RAEH
@author: HAZAM DAVID BAQUERO CUERVO RAEH
"""
import streamlit as st
import pandas as pd
import io
from io import BytesIO
from joblib import load

# ==================================================
# CONFIGURACIÓN
# ==================================================

st.set_page_config(
    page_title="Clasificador de Carbapenemasas",
    page_icon="RAEH",
    layout="wide"
)

# ==================================================
# RUTA MODELOS
# ==================================================

from joblib import load

modelo_m13 = load("modelos/RF_M13.joblib")
modelo_m5  = load("modelos/RF_M5.joblib")
modelo_m3  = load("modelos/RF_M3.joblib")

columnas_modelos = load("modelos/Columnas_Modelos.joblib")

# ==================================================
# NOMBRES CLÍNICOS ANTIBIÓTICOS
# ==================================================

nombres_antibioticos = {
    "AMS": "Ampicilina/Sulbactam",
    "C/T": "Ceftolozano/Tazobactam",
    "CZA": "Ceftazidima/Avibactam",
    "AZT": "Aztreonam",
    "CAZ": "Ceftazidima",
    "FEP": "Cefepime",
    "PTZ": "Piperacilina/Tazobactam",
    "ERT": "Ertapenem",
    "IMI": "Imipenem",
    "MER": "Meropenem",
    "AMK": "Amikacina",
    "CIP": "Ciprofloxacina",
    "TGC": "Tigeciclina"
}

# ==================================================
# ENCABEZADO
# ==================================================

st.markdown("""
# Clasificador Fenotípico de Carbapenemasas en *Klebsiella pneumoniae*

## Grupo de Investigación en Resistencia Antimicrobiana y Epidemiología Hospitalaria (RAEH)  
**Universidad El Bosque**

---

Esta herramienta utiliza modelos de aprendizaje automático basados en Random Forest para la clasificación fenotípica de aislamientos de *Klebsiella pneumoniae* a partir de perfiles de MIC.

---

### Categorías de clasificación

- Serino-β-lactamasa tipo KPC  
- Coproducción KPC +  MBL (Metalo-β-lactamasas NDM, VIM)   
- No presenta KPC ni coproducción KPC + MBL  

---

### Selección del modelo

M13: modelo completo con mayor robustez de clasificación  
M5: modelo intermedio recomendado para un set pequeño de datos
M3: modelo mínimo para escenarios con datos limitados  

La reducción de datos (MICs) puede afectar la capacidad discriminativa del modelo.
""")

st.markdown("---")

# ==================================================
# SELECCIÓN MODELO
# ==================================================

st.sidebar.title("Selección de modelo")

modelo_opcion = st.sidebar.selectbox(
    "Nivel de disponibilidad de MICs",
    [
        "Completo (M13)",
        "Intermedio (M5)",
        "Básico (M3)"
    ]
)

modelos_dict = {
    "Completo (M13)": modelo_m13,
    "Intermedio (M5)": modelo_m5,
    "Básico (M3)": modelo_m3
}

modelo = modelos_dict[modelo_opcion]

mapa_modelos = {
    "Completo (M13)": "RF_M13",
    "Intermedio (M5)": "RF_M5",
    "Básico (M3)": "RF_M3"
}

nombre_modelo = mapa_modelos[modelo_opcion]
variables = columnas_modelos[nombre_modelo]

st.sidebar.info(f"Modelo: {nombre_modelo}\nVariables: {len(variables)} MICs")

# ==================================================
# MODO DE USO
# ==================================================

st.sidebar.title("Modo de uso")

modo = st.sidebar.radio(
    "Seleccione una opción",
    [
        "Clasificación individual",
        "Clasificación masiva"
    ]
)

# ==================================================
# VALORES MIC
# ==================================================

mic_values = [0.06,0.12,0.25,0.5,1,2,4,8,16,32,64,128,256]

# ==================================================
# INPUT MIC DINÁMICO
# ==================================================
if modo == "Clasificación individual":
st.subheader("Ingreso de MICs")

entradas = {}

col1, col2 = st.columns(2)

for i, ab in enumerate(variables):

    with (col1 if i % 2 == 0 else col2):

        entradas[ab] = st.select_slider(
            label=nombres_antibioticos.get(ab, ab),
            options=mic_values,
            value=4,
            key=ab
        )

# ==================================================
# FUNCIÓN LIMPIEZA CLASE
# ==================================================

def limpiar_clase(clase):

    traducciones = {
        "No_Carbapenemasa": "No presenta KPC ni coproducción KPC + MBL",
        "No_carbapenemasa": "No presenta KPC ni coproducción KPC + MBL",
        "KPC": "Serino-β-lactamasas tipo KPC",
        "Coproduccion": "Coproducción KPC + MBL"
    }

    return traducciones.get(clase, clase)

# ==================================================
# PREDICCIÓN
# ==================================================

if st.button("Realizar predicción"):

    X = pd.DataFrame([[
        entradas[ab] for ab in variables
    ]], columns=variables)

    pred = modelo.predict(X)[0]
    probs = modelo.predict_proba(X)[0]
    clases_raw = modelo.classes_
    clases = [limpiar_clase(c) for c in clases_raw]

    st.markdown("---")

    st.subheader("Resultado")

    st.success(f"Clase asignada: {limpiar_clase(pred)}")

    # ==================================================
    # PROBABILIDADES
    # ==================================================

    resultados = pd.DataFrame({
    "Clase": clases,
    "Probabilidad (%)": probs * 100
}).sort_values(by="Probabilidad (%)", ascending=False)

    st.subheader("Probabilidades")

    for clase, prob in zip(clases, probs):
        st.write(f"{limpiar_clase(clase)}: {prob*100:.2f}%")
        st.progress(float(prob))

    # ==================================================
    # TABLA
    # ==================================================

    st.subheader("Tabla de resultados")

    st.dataframe(resultados, use_container_width=True)

    # ==================================================
    # GRÁFICO
    # ==================================================

    st.subheader("Visualización")

    st.bar_chart(resultados.set_index("Clase"))

# ==================================================
# PIE DE PÁGINA
# ==================================================

st.markdown("---")

st.caption("RAEH - Universidad El Bosque")
st.caption("Modelo Random Forest para clasificación de carbapenemasas en Klebsiella pneumoniae")

# ==================================================
# CLASIFICACIÓN MASIVA
# ==================================================

if modo == "Clasificación masiva":

    st.subheader("Clasificación masiva de aislamientos")

    st.markdown(
        """
        Cargue un archivo Excel con múltiples aislamientos.
        La primera columna debe llamarse **ID** y contener el identificador del aislamiento.
        """
    )

    columnas_requeridas = ["ID"] + variables

    st.markdown("### Formato esperado")

    st.code(
        " | ".join(columnas_requeridas)
    )

# ==================================================
# Generar Plantilla
# =
    plantilla = pd.DataFrame(
        columns=columnas_requeridas
    )

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        plantilla.to_excel(
            writer,
            index=False
        )

    st.download_button(
        label=f"Descargar plantilla {nombre_modelo}",
        data=output.getvalue(),
        file_name=f"Plantilla_{nombre_modelo}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ==================================================
# Subir archivo
# =
    archivo = st.file_uploader(
        "Seleccione archivo Excel",
        type=["xlsx"]
    )
# ==================================================
# Revisar si falta alguna columna dentro del archivo
# =
    if archivo is not None:

        df = pd.read_excel(archivo)

        faltantes = [
            col
            for col in columnas_requeridas
            if col not in df.columns
        ]

        if faltantes:

            st.error(
                f"Faltan columnas: {', '.join(faltantes)}"
            )

        else:

            st.success(
                f"Archivo válido: {len(df)} aislamientos detectados"
            )
# ==================================================
# Boton de clasificación
# =

            if st.button("Clasificar aislamientos"):

                X = df[variables]

                predicciones = modelo.predict(X)

                probabilidades = modelo.predict_proba(X)

                clases_modelo = modelo.classes_

# ==================================================
# Agregar resultados
# =
                df_resultados = df.copy()

                df_resultados["Clasificacion"] = [
                    limpiar_clase(p)
                    for p in predicciones
                ]

                df_resultados["Confianza (%)"] = (
                    probabilidades.max(axis=1) * 100
                ).round(2)
# ==================================================
# Guardar probabilidades de cada clase
# =
                for i, clase in enumerate(clases_modelo):

                    nombre_columna = (
                        "Prob_" +
                        limpiar_clase(clase)
                    )

                    df_resultados[
                        nombre_columna
                    ] = (
                        probabilidades[:, i] * 100
                    ).round(2)
# ==================================================
# Vista previa
# =
                st.subheader(
                    "Vista previa de resultados"
                )

                st.dataframe(
                    df_resultados.head(),
                    use_container_width=True
                )
# ==================================================
# Generar excel descargable
# =
                salida = BytesIO()

                with pd.ExcelWriter(
                    salida,
                    engine="openpyxl"
                ) as writer:

                    df_resultados.to_excel(
                        writer,
                        index=False
                    )

# ==================================================
# Boton de descarga
# =
                st.download_button(
                    label="Descargar resultados",
                    data=salida.getvalue(),
                    file_name=f"Resultados_{nombre_modelo}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
