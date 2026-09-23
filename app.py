import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium

# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================
st.set_page_config(
    page_title="Dashboard Cámaras de Seguridad",
    page_icon="🎥",
    layout="wide"
)

# ============================================================
# CARGA Y LIMPIEZA DE DATOS
# ============================================================
@st.cache_data
def cargar_datos():
    # Los encabezados reales están en la fila 2 del Excel
    df = pd.read_excel("Libro2.xlsx", header=1)
    df.columns = df.columns.astype(str).str.strip()

    # Eliminar filas vacías
    df = df.dropna(how="all")

    # Quedarnos solo con filas que tengan PILOTO válido
    df = df[df["PILOTO"].notna()].copy()
    df["PILOTO"] = df["PILOTO"].astype(str).str.strip()

    # Limpiar coordenadas
    def limpiar_coord(x):
        if pd.isna(x):
            return np.nan
        x = str(x).replace(",", ".").strip()
        try:
            return float(x)
        except:
            return np.nan

    def corregir_lat(x):
        if pd.isna(x):
            return np.nan
        if abs(x) > 90:
            x = x / 1_000_000
        return x

    def corregir_lon(x):
        if pd.isna(x):
            return np.nan
        if abs(x) > 180:
            x = x / 1_000_000
        return x

    df["LATITUD"] = df["LATITUD"].apply(limpiar_coord).apply(corregir_lat)
    df["LONGUITUD"] = df["LONGUITUD"].apply(limpiar_coord).apply(corregir_lon)
    df["ESTADO"] = df["ESTADO"].astype(str).str.strip().str.upper()

    return df


df = cargar_datos()

# ============================================================
# ENCABEZADO
# ============================================================
st.title("🎥 Dashboard de Cámaras de Seguridad")
st.markdown("Búsqueda por **código PILOTO** · Mapa gratuito (OpenStreetMap)")

# ============================================================
# RESUMEN GENERAL
# ============================================================
total = len(df)
funcionando = len(df[df["ESTADO"] == "FUNCIONANDO"])
no_funciona = len(df[df["ESTADO"] == "NO FUNCIONA"])
porcentaje = round((funcionando / total) * 100, 2) if total > 0 else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("✅ FUNCIONANDO", funcionando)
c2.metric("❌ NO FUNCIONA", no_funciona)
c3.metric("📹 TOTAL", total)
c4.metric("📈 DISPONIBILIDAD", f"{porcentaje}%")

st.divider()

# ============================================================
# BUSCADOR
# ============================================================
col_buscar, col_estado = st.columns([2, 1])

with col_buscar:
    codigo = st.text_input(
        "🔍 Escribe el código PILOTO:",
        placeholder="Ej: 746046"
    )

with col_estado:
    estados = ["TODOS"] + sorted(df["ESTADO"].dropna().unique().tolist())
    filtro_estado = st.selectbox("Filtrar por estado:", estados)

# ============================================================
# RESULTADOS
# ============================================================
if codigo:
    codigo = codigo.strip()
    resultado = df[df["PILOTO"] == codigo].copy()

    if resultado.empty:
        st.error(f"❌ No se encontró el piloto: {codigo}")
    else:
        # Aplicar filtro de estado si aplica
        if filtro_estado != "TODOS":
            resultado = resultado[resultado["ESTADO"] == filtro_estado]
            if resultado.empty:
                st.warning(f"⚠️ No hay cámaras con estado '{filtro_estado}' para este piloto.")

        if not resultado.empty:
            total_cam = len(resultado)
            lat = resultado["LATITUD"].dropna().iloc[0] if not resultado["LATITUD"].dropna().empty else None
            lon = resultado["LONGUITUD"].dropna().iloc[0] if not resultado["LONGUITUD"].dropna().empty else None
            estado = resultado["ESTADO"].iloc[0]

            st.subheader(f"📌 Resultado para el piloto: {codigo}")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🎥 Cámaras", total_cam)
            m2.metric("📊 Estado", estado)
            m3.metric("📍 Latitud", f"{lat:.6f}" if lat and not pd.isna(lat) else "N/D")
            m4.metric("📍 Longitud", f"{lon:.6f}" if lon and not pd.isna(lon) else "N/D")

            # Tabla detalle
            st.markdown("### 📋 Detalle de cámaras")
            columnas = ["CAMARA", "TIPO", "ESTADO", "DIRECCION", "MARCA", "MODELO", "SECTOR"]
            columnas = [c for c in columnas if c in resultado.columns]
            st.dataframe(resultado[columnas], use_container_width=True)

            # Mapa
            if lat and lon and not pd.isna(lat) and not pd.isna(lon):
                st.markdown("### 🗺️ Ubicación en el mapa")

                mapa = folium.Map(location=[lat, lon], zoom_start=17)

                popup_html = f"""
                <div style="font-family: Arial; font-size: 13px;">
                    <b>PILOTO:</b> {codigo}<br>
                    <b>Cámaras:</b> {total_cam}<br>
                    <b>Estado:</b> {estado}
                </div>
                """

                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"Piloto {codigo}",
                    icon=folium.Icon(color="red", icon="camera", prefix="fa")
                ).add_to(mapa)

                st_folium(mapa, width=800, height=500)

                # Enlace a Google Maps
                google_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                st.markdown(
                    f'<a href="{google_url}" target="_blank" '
                    f'style="display:inline-block; padding:10px 18px; '
                    f'background-color:#1a73e8; color:white; border-radius:6px; '
                    f'text-decoration:none; font-weight:bold;">'
                    f'🗺️ Abrir en Google Maps</a>',
                    unsafe_allow_html=True
                )
            else:
                st.info("⚠️ Este piloto no tiene coordenadas válidas para mostrar en el mapa.")
else:
    st.info("👆 Escribe un código PILOTO arriba para comenzar la búsqueda.")
