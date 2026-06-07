import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="JC TRADER ANALYSIS", layout="wide")

# 1. LOGO Y CABECERA

# Creamos dos columnas. El parámetro [1, 6] le da más espacio al texto que al logo.
col1, col2 = st.columns([1, 6])

with col1:
    st.image("logo.png", width=200)  # Ajusté un poco el ancho para que guarde mejor proporción

with col2:
    # Usamos un espacio vacío para empujar el título un poco hacia abajo y alinearlo verticalmente con el logo
    st.markdown("###")
    st.markdown("# JC TRADER ANALYSIS")

st.markdown("---")

ticker = st.text_input("Ingresa Ticker (ej: TSLA):", value="TSLA").upper()

def get_data(ticker):
    try:
        data = {}
        d1 = yf.download(ticker, period="1y", interval="1d", progress=False)
        h1 = yf.download(ticker, period="5d", interval="1h", progress=False)
        m5 = yf.download(ticker, period="5d", interval="5m", progress=False)
        
        if d1.empty or h1.empty or m5.empty:
            st.error("No se encontraron datos para ese ticker. Revisa si está bien escrito.")
            return None

        for df in [d1, h1, m5]:
            if isinstance(df.columns, pd.MultiIndex): 
                df.columns = df.columns.get_level_values(0)
            df.columns = [str(c).lower() for c in df.columns]
            
        for name, df in [("D1", d1), ("H1", h1), ("M5", m5)]:
            close = df['close']
            ema200 = close.ewm(span=200).mean().iloc[-1]
            tendencia = "🟢 Alcista" if close.iloc[-1] > ema200 else ("🔴 Bajista" if close.iloc[-1] < ema200 else "🟡 Lateral")
            
            data[name] = {
                "close": float(close.iloc[-1]),
                "ema27": float(close.ewm(span=27).mean().iloc[-1]),
                "ema50": float(close.ewm(span=50).mean().iloc[-1]),
                "ema100": float(close.ewm(span=100).mean().iloc[-1]),
                "ema200": float(ema200),
                "rsi": float(100 - (100 / (1 + (close.diff().where(close.diff() > 0, 0).rolling(14).mean() / -close.diff().where(close.diff() < 0, 0).rolling(14).mean())).iloc[-1])),
                "macd": float((close.ewm(span=12).mean() - close.ewm(span=26).mean()).iloc[-1]),
                "tendencia": tendencia
            }
        data["max52"] = float(d1['high'].max())
        data["min52"] = float(d1['low'].min())
        return data
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return None

# --- CAMBIO AQUÍ ---
if st.button("Analizar Mercado"):
    # Añadimos un mensaje de estado que desaparece al terminar
    with st.status(f"🔍 Analizando {ticker}...", expanded=True) as status:
        data = get_data(ticker)
        if data:
            status.update(label=f"✅ Análisis de {ticker} completado", state="complete")
            
            conteo_alcista = sum(1 for tf in ["D1", "H1", "M5"] if "Alcista" in data[tf]["tendencia"])
            conteo_bajista = sum(1 for tf in ["D1", "H1", "M5"] if "Bajista" in data[tf]["tendencia"])
            
            if conteo_alcista == 3:
                label, color = f"🚀 COMPRA FUERTE EN {ticker}", "green"
            elif conteo_bajista == 3:
                label, color = f"📉 VENTA FUERTE EN {ticker}", "red"
            else:
                label, color = f"⚠️ {ticker}: NEUTRO / ESPERAR", "orange"
            
            st.markdown(f"<h1 style='color:{color};'>🎯 {label}</h1>", unsafe_allow_html=True)
            
            diff_dolares = data['max52'] - data['M5']['close']
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(f"Precio {ticker}", f"${data['M5']['close']:.2f}")
            c2.metric("Máx 52 Sem", f"${data['max52']:.2f}")
            c3.metric("Min 52 Sem", f"${data['min52']:.2f}")
            c4.metric("Bajo desde Máx ($)", f"-${diff_dolares:.2f}")
            
            st.write("### 📊 Detalle Técnico Completo")
            rows = []
            for tf in ["D1", "H1", "M5"]:
                v = data[tf]
                rsi_color = "green" if v['rsi'] >= 50 else "red"
                macd_color = "green" if v['macd'] >= 0 else "red"
                
                rows.append({
                    "TF": tf,
                    "Tendencia": v['tendencia'],
                    "EMA 27": f"{v['ema27']:.2f}",
                    "EMA 50": f"{v['ema50']:.2f}",
                    "EMA 100": f"{v['ema100']:.2f}",
                    "EMA 200": f"{v['ema200']:.2f}",
                    "RSI": f"<span style='color: {rsi_color}; font-weight:bold;'>{v['rsi']:.1f}</span>",
                    "MACD": f"<span style='color: {macd_color}; font-weight:bold;'>{v['macd']:.3f}</span>"
                })
            
            st.write(pd.DataFrame(rows).to_html(escape=False, index=False), unsafe_allow_html=True)