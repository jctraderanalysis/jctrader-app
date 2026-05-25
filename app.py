import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="JC TRADER ANALYSIS", layout="wide")

# LOGO Y CABECERA
st.image("logo.png", width=200)
st.markdown("# JC TRADER ANALYSIS")
st.markdown("---")

ticker = st.text_input("Ingresa Ticker (ej: TSLA):", value="TSLA").upper()

def get_data(ticker):
    try:
        data = {}
        configs = [("D1", "1y", "1d"), ("H1", "5d", "1h"), ("M5", "5d", "5m")]
        
        d1_raw = yf.download(ticker, period="1y", interval="1d", progress=False)
        if isinstance(d1_raw.columns, pd.MultiIndex): d1_raw.columns = d1_raw.columns.get_level_values(0)
        
        data["max52"] = float(d1_raw['High'].max())
        data["min52"] = float(d1_raw['Low'].min())
        
        for name, period, interval in configs:
            df = yf.download(ticker, period=period, interval=interval, progress=False)
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            df.columns = [c.lower() for c in df.columns]
            
            close = df['close']
            ema200 = close.ewm(span=200, adjust=False).mean()
            tendencia = "🟢 Alcista" if close.iloc[-1] > ema200.iloc[-1] else ("🔴 Bajista" if close.iloc[-1] < ema200.iloc[-1] else "🟡 Lateral")
            
            data[name] = {
                "df": df, "close": float(close.iloc[-1]),
                "ema27": float(close.ewm(span=27, adjust=False).mean().iloc[-1]),
                "ema50": float(close.ewm(span=50, adjust=False).mean().iloc[-1]),
                "ema100": float(close.ewm(span=100, adjust=False).mean().iloc[-1]),
                "ema200": float(ema200.iloc[-1]),
                "rsi": float(100 - (100 / (1 + (close.diff().where(close.diff() > 0, 0).rolling(14).mean() / -close.diff().where(close.diff() < 0, 0).rolling(14).mean())).iloc[-1])),
                "macd": float((close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()).iloc[-1]),
                "tendencia": tendencia
            }
        return data
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return None

if st.button("Analizar Mercado"):
    data = get_data(ticker)
    if data:
        # Lógica de decisión
        alcista = sum(1 for tf in ["D1", "H1", "M5"] if "Alcista" in data[tf]["tendencia"])
        bajista = sum(1 for tf in ["D1", "H1", "M5"] if "Bajista" in data[tf]["tendencia"])
        
        if alcista == 3: label, color = "🚀 COMPRA FUERTE", "green"
        elif bajista == 3: label, color = "📉 VENTA FUERTE", "red"
        else: label, color = "⚠️ NEUTRO / ESPERAR", "orange"
        
        st.markdown(f"<h1 style='text-align: center; color:{color};'>{label}</h1>", unsafe_allow_html=True)
        
        # Métricas
        diff = data['max52'] - data['M5']['close']
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Precio Actual", f"${data['M5']['close']:.2f}")
        c2.metric("Máx 52 Sem", f"${data['max52']:.2f}")
        c3.metric("Min 52 Sem", f"${data['min52']:.2f}")
        c4.metric("Dif. vs Máx ($)", f"-${diff:.2f}")
        
        # Gráficos
        tabs = st.tabs(["📊 Gráfico D1", "📊 Gráfico H1", "📊 Gráfico M5"])
        for i, tf in enumerate(["D1", "H1", "M5"]):
            with tabs[i]:
                df = data[tf]["df"]
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='Precio'))
                for span, col in [(27, 'magenta'), (50, 'blue'), (100, 'red'), (200, 'black')]:
                    ema = df['close'].ewm(span=span, adjust=False).mean()
                    fig.add_trace(go.Scatter(x=df.index, y=ema, line=dict(color=col, width=1.5), name=f'EMA {span}'))
                fig.update_layout(height=450, template="plotly_dark", xaxis_rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True)

        # Tabla Completa
        st.write("### 📊 Detalle Técnico Completo")
        rows = []
        for tf in ["D1", "H1", "M5"]:
            v = data[tf]
            rows.append({
                "TF": tf, "Tendencia": v['tendencia'],
                "EMA 27": f"{v['ema27']:.2f}", "EMA 50": f"{v['ema50']:.2f}",
                "EMA 100": f"{v['ema100']:.2f}", "EMA 200": f"{v['ema200']:.2f}",
                "RSI": f"<span style='color: {'green' if v['rsi'] >= 50 else 'red'}; font-weight:bold;'>{v['rsi']:.1f}</span>",
                "MACD": f"<span style='color: {'green' if v['macd'] >= 0 else 'red'}; font-weight:bold;'>{v['macd']:.3f}</span>"
            })
        st.write(pd.DataFrame(rows).to_html(escape=False, index=False), unsafe_allow_html=True)