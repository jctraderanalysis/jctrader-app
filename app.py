import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="JC TRADER ANALYSIS", layout="wide")

# CABECERA
st.markdown("# JC TRADER ANALYSIS")
st.markdown("---")
ticker = st.text_input("Ingresa Ticker (ej: TSLA):", value="TSLA").upper()

def get_data(ticker):
    try:
        data = {}
        d1 = yf.download(ticker, period="1y", interval="1d", progress=False)
        h1 = yf.download(ticker, period="5d", interval="1h", progress=False)
        m5 = yf.download(ticker, period="5d", interval="5m", progress=False)
        
        for df in [d1, h1, m5]:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
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

if st.button("Analizar Mercado"):
    data = get_data(ticker)
    if data:
        # Lógica de Decisión Inteligente
        conteo_alcista = sum(1 for tf in ["D1", "H1", "M5"] if "Alcista" in data[tf]["tendencia"])
        conteo_bajista = sum(1 for tf in ["D1", "H1", "M5"] if "Bajista" in data[tf]["tendencia"])
        
        if conteo_alcista == 3:
            label, color = "🚀 COMPRA FUERTE", "green"
        elif conteo_bajista == 3:
            label, color = "📉 VENTA FUERTE", "red"
        else:
            label, color = "⚠️ NEUTRO / ESPERAR", "orange"
        
        st.markdown(f"<h1 style='color:{color};'>🎯 {label}</h1>", unsafe_allow_html=True)
        
        # MÉTRICAS: Aquí recuperamos el MIN 52 y la DIFERENCIA
        diff_dolares = data['max52'] - data['M5']['close']
        
        # Usamos 4 columnas para que quepan los 4 datos importantes
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Precio Actual", f"${data['M5']['close']:.2f}")
        c2.metric("Máx 52 Sem", f"${data['max52']:.2f}")
        c3.metric("Min 52 Sem", f"${data['min52']:.2f}")
        c4.metric("Bajo desde Máx ($)", f"-${diff_dolares:.2f}")
        
        st.write("### 📊 Detalle Técnico Completo")
        rows = []
        for tf in ["D1", "H1", "M5"]:
            v = data[tf]
            rows.append({
                "TF": tf,
                "Tendencia": v['tendencia'],
                "EMA 27": f"{v['ema27']:.2f}",
                "EMA 50": f"{v['ema50']:.2f}",
                "EMA 100": f"{v['ema100']:.2f}",
                "EMA 200": f"{v['ema200']:.2f}",
                "RSI": f"<span style='color: {'green' if v['rsi'] > 0 else 'red'}; font-weight:bold; font-size:16px;'>{v['rsi']:.1f}</span>",
                "MACD": f"<span style='color: {'green' if v['macd'] > 0 else 'red'}; font-weight:bold; font-size:16px;'>{v['macd']:.3f}</span>"
            })
        
        st.write(pd.DataFrame(rows).to_html(escape=False, index=False), unsafe_allow_html=True)