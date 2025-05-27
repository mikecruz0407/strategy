import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime
from scipy.stats import linregress


def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / (avg_loss + 1e-6)
    return 100 - (100 / (1 + rs))


def analyze_projection(df):
    close = df['Close'].dropna()
    if len(close) < 20:
        return None

    rsi = compute_rsi(close)
    ma20 = close.rolling(20).mean()
    ma40 = close.rolling(40).mean()

    recent = close[-10:]
    x = np.arange(len(recent))
    slope, intercept, *_ = linregress(x, recent)
    trendline = intercept + slope * x

    deviation = (recent - trendline).abs().mean()
    confidence = max(0, 1 - deviation / recent.mean())

    trend_start_price = round(recent.iloc[0], 2)
    trend_start_time = recent.index[0].strftime('%m/%d/%Y %H:%M')
    trend_end_price = round(recent.iloc[-1], 2)
    trend_end_time = recent.index[-1].strftime('%m/%d/%Y %H:%M')

    breakout_price = breakout_time = None
    for i in range(len(recent)):
        if recent.iloc[i] > trendline[i]:
            breakout_price = recent.iloc[i]
            idx = recent.index[i]
            breakout_time = idx.strftime('%m/%d/%Y') if idx.hour == 0 else idx.strftime('%m/%d/%Y %H:%M')
            break

    ma20_diff = (close.iloc[-1] - ma20.iloc[-1]) / ma20.iloc[-1]
    ma40_diff = (close.iloc[-1] - ma40.iloc[-1]) / ma40.iloc[-1]
    ma20_score = np.clip(ma20_diff * 10, -1, 1)
    ma40_score = np.clip(ma40_diff * 10, -1, 1)
    rsi_score = np.clip((rsi.iloc[-1] - 50) / 20, -1, 1)
    slope_score = np.clip(slope * 100, -1, 1)

    score = 0.35 * ma20_score + 0.25 * ma40_score + 0.2 * rsi_score + 0.2 * slope_score
    score = np.clip(score, -1, 1)

    rise_prob = round((score + 1) / 2 * 100, 2)
    fall_prob = round(100 - rise_prob, 2)

    now = datetime.now()
    hours_left = max(0, 16 - now.hour)
    if hours_left <= 1 and confidence > 0.75:
        if slope < -0.1:
            eod_comment = "📉 Likely to decline before close."
        elif slope > 0.1:
            eod_comment = "📈 Likely to push higher before close."
        else:
            eod_comment = "🔄 Flat into close — no strong move."
    else:
        if slope > 0.15:
            eod_comment = "📈 Uptrend may continue next 2–3 days."
        elif slope < -0.15:
            eod_comment = "📉 Downtrend likely to extend 1–2 days."
        else:
            eod_comment = "🔄 Momentum unclear — watch closely."

    return {
        "rise_probability": rise_prob,
        "fall_probability": fall_prob,
        "trend_slope": slope,
        "trend_confidence": round(confidence, 2),
        "trendline_breakout": breakout_price is not None,
        "breakout_price": round(breakout_price, 2) if breakout_price else None,
        "breakout_time": breakout_time,
        "rsi": round(rsi.iloc[-1], 2),
        "ma20": round(ma20.iloc[-1], 2),
        "ma40": round(ma40.iloc[-1], 2),
        "trend_start_price": trend_start_price,
        "trend_start_time": trend_start_time,
        "trend_end_price": trend_end_price,
        "trend_end_time": trend_end_time,
        "eod_projection": eod_comment
    }


def analyze_stock(symbol, interval="60m"):
    ticker = yf.Ticker(symbol)
    period_map = {
        "1h": "2mo", "1d": "6mo", "1wk": "2y", "1mo": "5y"
    }
    hist = ticker.history(period=period_map[interval], interval=interval)

    if hist.empty or len(hist) < 20:
        return None

    for w in [20, 40, 100, 200]:
        hist[f"MA{w}"] = hist["Close"].rolling(window=w).mean()

    latest = hist.iloc[-1]
    price = latest["Close"]

    total_calls = total_puts = call_put_ratio = trend_ratio = 0
    best_strike = None
    strategy_note = ""
    try:
        exp = ticker.options[0]
        chain = ticker.option_chain(exp)
        total_calls = int(chain.calls.volume.sum())
        total_puts = int(chain.puts.volume.sum())
        call_put_ratio = total_calls / (total_puts + 1)
        avg_c = chain.calls.groupby("strike").volume.mean().mean() + 1e-6
        avg_p = chain.puts.groupby("strike").volume.mean().mean() + 1e-6
        trend_ratio = avg_c / avg_p
    except Exception:
        pass

    opt_cost = cost_signal = None
    cost_map = {
        'SPY': 0.30, 'QQQ': 0.30, 'META': 0.80, 'AAPL': 0.80,
        'AMZN': 0.80, 'NFLX': 2.50, 'MRNA': 2.00, 'TSLA': 2.50,
        'TNA': 0.80, 'GLD': 0.80, 'SLV': 0.20, 'USO': 0.20,
        'BAC': 0.20, 'CVX': 0.80, 'XOM': 0.80, 'NVDA': 0.80
    }
    try:
        if symbol in cost_map:
            calls = ticker.option_chain(exp).calls
            atm_strike = min(calls['strike'], key=lambda s: abs(s - price))
            atm = calls[calls['strike'] == atm_strike].iloc[0]
            mid = (atm.bid + atm.ask) / 2.0
            opt_cost = mid
            cost_signal = "GREEN" if mid <= cost_map[symbol] else "RED"
    except:
        pass

    if call_put_ratio > 1.2 and trend_ratio > 1.1 and price > hist["MA20"].iloc[-1]:
        signal, advice = "BUY", "Momentum favors calls."
    elif call_put_ratio < 0.8 and trend_ratio < 0.9 and price < hist["MA20"].iloc[-1]:
        signal, advice = "SELL", "Puts dominate."
    else:
        signal, advice = "HOLD", "Neutral market flow."

    try:
        if signal in ["BUY", "SELL"]:
            opt = chain.calls if signal == "BUY" else chain.puts
            target_pct = 0.02 if signal == "BUY" else -0.02
            target_price = price * (1 + target_pct)
            strikes = opt['strike'].dropna().values
            best_strike = min(strikes, key=lambda s: abs(s - target_price))
            strategy_note = f"Suggested {'CALL' if signal == 'BUY' else 'PUT'} @ {round(best_strike, 2)}"
    except:
        best_strike = None
        strategy_note = "No strike suggestion."

    proj = analyze_projection(hist)

    return {
        "symbol": symbol,
        "price": round(price, 2),
        "signal": signal,
        "advice": advice,
        "total_calls": total_calls,
        "total_puts": total_puts,
        "call_put_ratio": round(call_put_ratio, 2),
        "trend_ratio": round(trend_ratio, 2),
        "data": hist,
        "opt_cost": opt_cost,
        "cost_signal": cost_signal,
        "recommended_strike": round(best_strike, 2) if best_strike else None,
        "strategy_note": strategy_note,
        "projection": proj,
        "near_term_outlook": proj["eod_projection"] if proj else "—"
    }


def analyze_projection(df):
    close = df['Close'].dropna()
    if len(close) < 20:
        return None

    rsi = compute_rsi(close)
    ma20 = close.rolling(20).mean()
    ma40 = close.rolling(40).mean()

    recent = close[-10:]
    x = np.arange(len(recent))
    slope, intercept, *_ = linregress(x, recent)
    trendline = intercept + slope * x

    deviation = (recent - trendline).abs().mean()
    confidence = max(0, 1 - deviation / recent.mean())

    trend_start_price = round(recent.iloc[0], 2)
    trend_start_time = recent.index[0].strftime('%m/%d/%Y %H:%M')
    trend_end_price = round(recent.iloc[-1], 2)
    trend_end_time = recent.index[-1].strftime('%m/%d/%Y %H:%M')

    breakout_price = breakout_time = None
    for i in range(len(recent)):
        if recent.iloc[i] > trendline[i]:
            breakout_price = recent.iloc[i]
            idx = recent.index[i]
            breakout_time = idx.strftime('%m/%d/%Y') if idx.hour == 0 else idx.strftime('%m/%d/%Y %H:%M')
            break

    ma20_diff = (close.iloc[-1] - ma20.iloc[-1]) / ma20.iloc[-1]
    ma40_diff = (close.iloc[-1] - ma40.iloc[-1]) / ma40.iloc[-1]
    ma20_score = np.clip(ma20_diff * 10, -1, 1)
    ma40_score = np.clip(ma40_diff * 10, -1, 1)
    rsi_score = np.clip((rsi.iloc[-1] - 50) / 20, -1, 1)
    slope_score = np.clip(slope * 100, -1, 1)

    score = 0.35 * ma20_score + 0.25 * ma40_score + 0.2 * rsi_score + 0.2 * slope_score
    score = np.clip(score, -1, 1)

    rise_prob = round((score + 1) / 2 * 100, 2)
    fall_prob = round(100 - rise_prob, 2)

    now = datetime.now()
    hours_left = max(0, 16 - now.hour)
    if hours_left <= 1 and confidence > 0.75:
        if slope < -0.1:
            eod_comment = "📉 Likely to decline before close."
        elif slope > 0.1:
            eod_comment = "📈 Likely to push higher before close."
        else:
            eod_comment = "🔄 Flat into close — no strong move."
    else:
        if slope > 0.15:
            eod_comment = "📈 Uptrend may continue next 2–3 days."
        elif slope < -0.15:
            eod_comment = "📉 Downtrend likely to extend 1–2 days."
        else:
            eod_comment = "🔄 Momentum unclear — watch closely."

    return {
        "rise_probability": rise_prob,
        "fall_probability": fall_prob,
        "trend_slope": slope,
        "trend_confidence": round(confidence, 2),
        "trendline_breakout": breakout_price is not None,
        "breakout_price": round(breakout_price, 2) if breakout_price else None,
        "breakout_time": breakout_time,
        "rsi": round(rsi.iloc[-1], 2),
        "ma20": round(ma20.iloc[-1], 2),
        "ma40": round(ma40.iloc[-1], 2),
        "trend_start_price": trend_start_price,
        "trend_start_time": trend_start_time,
        "trend_end_price": trend_end_price,
        "trend_end_time": trend_end_time,
        "eod_projection": eod_comment
    }
