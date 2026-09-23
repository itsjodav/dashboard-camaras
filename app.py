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
@st.cache_data(ttl=300)  # Recarga cada 5 min
def cargar_datos():
    file_id = "1ngQlOe1gcTrXg6IVAZEU7qleprvCuy2o"  # 👈 Pega aquí tu ID
     url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=xlsx"

    df = pd.read_excel(url, header=1)
    df.columns = df.columns.astype(str).str.strip()

    df = df.dropna(how="all")
    df = df[df["PILOTO"].notna()].copy()
    df["PILOTO"] = df["PILOTO"].astype(str).str.strip()

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
        return x / 1_000_000 if abs(x) > 90 else x

    def corregir_lon(x):
        if pd.isna(x):
            return np.nan
        return x / 1_000_000 if abs(x) > 180 else x

    df["LATITUD"] = df["LATITUD"].apply(limpiar_coord).apply(corregir_lat)
    df["LONGUITUD"] = df["LONGUITUD"].apply(limpiar_coord).apply(corregir_lon)
    df["ESTADO"] = df["ESTADO"].astype(str).str.strip().str.upper()

    return df

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
            # ---- Datos generales ----
            total_cam = len(resultado)
            lat = resultado["LATITUD"].dropna().iloc[0] if not resultado["LATITUD"].dropna().empty else None
            lon = resultado["LONGUITUD"].dropna().iloc[0] if not resultado["LONGUITUD"].dropna().empty else None

            # ---- Separar por estado ----
            funcionando_df = resultado[resultado["ESTADO"] == "FUNCIONANDO"]
            no_funciona_df = resultado[resultado["ESTADO"] == "NO FUNCIONA"]
            otros_df = resultado[~resultado["ESTADO"].isin(["FUNCIONANDO", "NO FUNCIONA"])]

            cant_funcionando = len(funcionando_df)
            cant_no_funciona = len(no_funciona_df)
            cant_otros = len(otros_df)

            st.subheader(f"📌 Resultado para el piloto: {codigo}")

            # ---- Métricas principales ----
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🎥 Total cámaras", total_cam)
            m2.metric("✅ Funcionando", cant_funcionando)
            m3.metric("❌ No funcionan", cant_no_funciona)
            m4.metric(
                "📈 Disponibilidad",
                f"{round((cant_funcionando / total_cam) * 100, 1)}%" if total_cam > 0 else "0%"
            )

            # ---- Coordenadas ----
            c1, c2 = st.columns(2)
            c1.metric("📍 Latitud", f"{lat:.6f}" if lat and not pd.isna(lat) else "N/D")
            c2.metric("📍 Longitud", f"{lon:.6f}" if lon and not pd.isna(lon) else "N/D")

            st.divider()

            # ---- Cámaras FUNCIONANDO ----
            st.markdown(f"### ✅ Cámaras FUNCIONANDO ({cant_funcionando})")
            if cant_funcionando > 0:
                cols_mostrar = ["N. CAM", "COD_SITIMAS","CAMARA", "TIPO", "DIRECCION", "MARCA", "MODELO", "SECTOR"]
                cols_mostrar = [c for c in cols_mostrar if c in funcionando_df.columns]
                st.dataframe(
                    funcionando_df[cols_mostrar],
                    use_container_width=True,
                    hide_index=True
                )
                # Lista rápida de números de cámara
                lista_camaras = funcionando_df["CAMARA"].dropna().astype(str).tolist()
                if lista_camaras:
                    st.caption(f"📹 Números de cámara: {', '.join(lista_camaras)}")
            else:
                st.info("No hay cámaras funcionando en este piloto.")

            # ---- Cámaras NO FUNCIONA ----
            st.markdown(f"### ❌ Cámaras NO FUNCIONAN ({cant_no_funciona})")
            if cant_no_funciona > 0:
                cols_mostrar = ["N. CAM", "COD_SITIMAS", "CAMARA", "TIPO", "DIRECCION", "MARCA", "MODELO", "SECTOR", "OBSERVACION"]
                cols_mostrar = [c for c in cols_mostrar if c in no_funciona_df.columns]
                st.dataframe(
                    no_funciona_df[cols_mostrar],
                    use_container_width=True,
                    hide_index=True
                )
                lista_camaras = no_funciona_df["CAMARA"].dropna().astype(str).tolist()
                if lista_camaras:
                    st.caption(f"📹 Números de cámara: {', '.join(lista_camaras)}")

                # Mostrar observaciones si existen
                if "OBSERVACION" in no_funciona_df.columns:
                    obs = no_funciona_df["OBSERVACION"].dropna().astype(str)
                    obs = obs[obs.str.strip() != ""]
                    if not obs.empty:
                        st.warning("📝 Observaciones:")
                        for o in obs.unique():
                            st.write(f"- {o}")
            else:
                st.success("Todas las cámaras de este piloto están funcionando. ✅")

            # ---- Otros estados (si los hay) ----
            if cant_otros > 0:
                st.markdown(f"### ⚠️ Otras cámaras con estado distinto ({cant_otros})")
                cols_mostrar = ["CAMARA", "TIPO", "ESTADO", "DIRECCION", "OBSERVACION"]
                cols_mostrar = [c for c in cols_mostrar if c in otros_df.columns]
                st.dataframe(
                    otros_df[cols_mostrar],
                    use_container_width=True,
                    hide_index=True
                )

            st.divider()

            # ---- Mapa ----
            if lat and lon and not pd.isna(lat) and not pd.isna(lon):
                st.markdown("### 🗺️ Ubicación en el mapa")

                mapa = folium.Map(location=[lat, lon], zoom_start=17)

                # Color según disponibilidad
                if cant_no_funciona == 0:
                    color_marcador = "green"
                elif cant_funcionando == 0:
                    color_marcador = "red"
                else:
                    color_marcador = "orange"

                popup_html = f"""
                <div style="font-family: Arial; font-size: 13px;">
                    <b>PILOTO:</b> {codigo}<br>
                    <b>Total:</b> {total_cam}<br>
                    <b>✅ Funcionando:</b> {cant_funcionando}<br>
                    <b>❌ No funcionan:</b> {cant_no_funciona}
                </div>
                """

                folium.Marker(
                    [lat, lon],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=f"Piloto {codigo}",
                    icon=folium.Icon(color=color_marcador, icon="camera", prefix="fa")
                ).add_to(mapa)

                st_folium(mapa, width=800, height=500)

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
