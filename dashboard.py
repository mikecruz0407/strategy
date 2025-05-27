import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
from datetime import datetime
from scipy.stats import linregress
from analyze import analyze_stock
from utils import load_favorites, save_favorites
from ticker import get_ticker_from_name
import time

# ── Streamlit Setup ──
st.set_page_config(page_title="📈 Stock Projection Dashboard", layout="wide")
st.session_state.setdefault('symbol_input', '')

# ── Interval Selection ──
col1, col2 = st.columns([1, 12])
with col1:
    interval = st.selectbox("⏱", ["1h", "1d", "1wk", "1mo"], index=0, label_visibility="collapsed")

# ── TradingView Embed ──
def embed_tradingview_chart(symbol="AAPL", interval="60"):
    interval_map = {"1h": "60", "1d": "D", "1wk": "W", "1mo": "M"}
    tv_interval = interval_map.get(interval, "60")
    st.components.v1.html(f"""
    <iframe src="https://s.tradingview.com/widgetembed/?symbol={symbol}&interval={tv_interval}&theme=light&style=1&timezone=America/New_York&withdateranges=1&hide_side_toolbar=0&allow_symbol_change=0"
            width="100%" height="600" frameborder="0" allowtransparency="true" scrolling="no" style="display: block;"></iframe>
    """, height=600)

# ── Utilities ──
@st.cache_data(show_spinner=False)
def get_logo_url(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get("logo_url") or "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg"
    except:
        return "https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg"

# ── Format Analysis ──
def format_projection_analysis(proj, signal):
    buy_signal = proj['rise_probability'] >= 70
    sell_signal = proj['fall_probability'] >= 70
    rsi_value = proj['rsi']
    if rsi_value < 30:
        rsi_comment = "📉 Oversold"
    elif rsi_value < 45:
        rsi_comment = "⚠️ Weak"
    elif rsi_value < 55:
        rsi_comment = "🔄 Neutral"
    elif rsi_value < 70:
        rsi_comment = "✅ Healthy"
    else:
        rsi_comment = "🔹 Overbought"

    sentiment = (
        "🟢 Momentum is building — buyers showing strength" if buy_signal else
        "🔴 Sellers gaining control — caution advised" if sell_signal else
        "🟡 Choppy range — wait for confirmation"
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"""
### 📊 Projection Analysis

**Technical Signal**: **{signal}**  
**🔄 RSI**: {rsi_value} — _{rsi_comment}_  

**RSI Guide**  
- **< 30** = 📉 Oversold — potential bounce  
- **30–45** = ⚠️ Weak momentum  
- **45–55** = 🔄 Neutral  
- **55–70** = ✅ Healthy buying  
- **> 70** = 🔹 Overbought — caution
""")

    with col2:
        st.markdown(f"""
**🟢 Probability of Rise**: {proj['rise_probability']}%  
**🔴 Probability of Drop**: {proj['fall_probability']}%  
🗓 Time Horizon: short-term  
🗓 **Near-Term Outlook**: {proj['eod_projection']}  

**Market Sentiment**: {sentiment}
""")

# ── Input ──
user_input = st.text_input("🔍 Search by Company or Ticker", st.session_state.symbol_input).strip()
symbol = get_ticker_from_name(user_input)
st.session_state.symbol_input = user_input

# ── Live Placeholders ──
chart_placeholder = st.empty()
price_placeholder = st.empty()
analysis_placeholder = st.empty()
watchlist_container = st.empty()

# ── Watchlist ──
def render_watchlist():
    favs = load_favorites()
    rows = []

    for sym in favs:
        try:
            res = analyze_stock(sym, interval=interval)
            if not res or "data" not in res:
                raise ValueError(f"No data returned for {sym}")
            df = res["data"]
            proj = res.get("projection") or {}

            rise = proj.get('rise_probability', 0)
            fall = proj.get('fall_probability', 0)
            rsi = proj.get('rsi', 0)
            breakout = "✅" if proj.get('trendline_breakout') else "❌"

            if rsi < 30:
                rsi_status = "📉 Oversold"
            elif rsi < 45:
                rsi_status = "⚠️ Weak"
            elif rsi < 55:
                rsi_status = "🔄 Neutral"
            elif rsi < 70:
                rsi_status = "✅ Healthy"
            else:
                rsi_status = "🔹 Overbought"

            if rise >= 70:
                sentiment = "🟢 Buyers strong"
            elif fall >= 70:
                sentiment = "🔴 Sellers strong"
            else:
                sentiment = "🟡 Sideways"

            analysis_summary = f"↑{rise:.2f}% ↓{fall:.2f}% | RSI {rsi:.2f} {rsi_status} | {breakout}"
            action = "CALL" if rise >= 70 else "PUT" if fall >= 70 else "HOLD"
            outlook = res.get("near_term_outlook", "—")

            rows.append({
                "Ticker": sym,
                "Close": f"${df['Close'].iloc[-1]:.2f}",
                "Signal": res['signal'],
                "Action": action,
                "Analysis": analysis_summary,
                "Sentiment": sentiment,
                "🗓 Outlook": outlook
            })
        except Exception as e:
            rows.append({
                "Ticker": sym,
                "Close": "—",
                "Signal": "Error",
                "Action": "—",
                "Analysis": "—",
                "Sentiment": "—",
                "🗓 Outlook": "—"
            })

    df_summary = pd.DataFrame(rows)

    def highlight(row):
        if row["Action"] == "CALL":
            return ['background-color: #003300; color: lime'] * len(row)
        elif row["Action"] == "PUT":
            return ['background-color: #330000; color: red'] * len(row)
        return [''] * len(row)

    styled_df = df_summary.style.apply(highlight, axis=1)
    table_height = min(700, 40 * (len(df_summary) + 1))
    watchlist_container.dataframe(styled_df, use_container_width=True, height=table_height)

# ── Chart ──
if symbol:
    with chart_placeholder:
        embed_tradingview_chart(symbol, interval)

# ── Watchlist Title ──
col1, col2 = st.columns([1, 2])
with col1:
    st.markdown("## ⭐ Watchlist")
with col2:
    st.markdown("""
    <div style="font-size: 0.875rem; line-height: 1.4; padding-top: 10px;">
        <b>Key:</b> &nbsp;
        <span style="background-color: #003300; color: #90ee90; padding: 2px 8px; border-radius: 4px;">CALL</span>
        = Upside opportunity &nbsp;&nbsp;
        <span style="background-color: #330000; color: #ff7f7f; padding: 2px 8px; border-radius: 4px;">PUT</span>
        = Downside risk &nbsp;&nbsp;
        <span style="color: #bbb;">HOLD</span>
        = Neutral/Wait
    </div>
    """, unsafe_allow_html=True)

# ── Live Refresh Loop ──
if symbol:
    logo = get_logo_url(symbol)
    while True:
        try:
            res = analyze_stock(symbol, interval=interval)
            df = res["data"]
            close = df['Close'].iloc[-1]
            prev = df['Close'].iloc[-2]
            pnl, pct = close - prev, (close - prev) / prev * 100
            color = "lime" if pnl > 0 else "red"

            price_placeholder.markdown(
                f"## <img src='{logo}' width='32' style='vertical-align:middle;'> {symbol} — "
                f"${close:.2f} <span style='color:{color}'>{pnl:+.2f} ({pct:+.2f}%)</span> | Signal: **{res['signal']}**",
                unsafe_allow_html=True
            )

            proj = res.get("projection") or {}
            with analysis_placeholder:
                format_projection_analysis(proj, res['signal'])

            render_watchlist()
            time.sleep(0)

        except Exception as e:
            st.error(f"⚠️ Error updating data: {e}")
            break

# ── Alerts ──
now = datetime.now()
if now.minute == 0:
    st.warning("🕒 Hourly Alert: Review setups now.")
if now.hour == 15 and now.minute >= 30:
    st.error("⏰ 3:30 PM: Final watchlist check before close.")
