"""
Crypto Signal Dashboard — Streamlit Web App
Τρέξε: streamlit run crypto_dashboard.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import requests
import json
import xml.etree.ElementTree as ET

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Crypto Signal Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Base ── */
    .stApp { background-color: #0d1117; }
    section[data-testid="stSidebar"] { background-color: #161b22; }

    /* ── Metrics ── */
    [data-testid="metric-container"] {
        background-color: #161b22;
        border: 1px solid #21262d;
        border-radius: 12px;
        padding: 16px;
    }
    [data-testid="metric-container"] label {
        color: #8b949e !important;
        font-size: 13px !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #e6edf3 !important;
        font-size: 22px !important;
        font-weight: bold;
    }

    /* ── Signals ── */
    .signal-badge { display:inline-block; padding:10px 28px; border-radius:50px; font-size:22px; font-weight:bold; letter-spacing:2px; text-align:center; width:100%; }
    .signal-STRONG-BUY  { background:#0d2818; color:#3fb950; border:2px solid #3fb950; }
    .signal-BUY         { background:#0d2818; color:#26c941; border:2px solid #26c941; }
    .signal-HOLD        { background:#2a2000; color:#d29922; border:2px solid #d29922; }
    .signal-SELL        { background:#2a0a0a; color:#f85149; border:2px solid #f85149; }
    .signal-STRONG-SELL { background:#2a0a0a; color:#ff4040; border:2px solid #ff4040; }

    /* ── General ── */
    h1,h2,h3 { color:#e6edf3 !important; }
    hr { border-color:#21262d; }
    .stButton > button { background-color:#1f6feb; color:white; border:none; border-radius:8px; padding:8px 20px; font-weight:bold; width:100%; }
    .stButton > button:hover { background-color:#388bfd; }
    .alert-buy  { background:#0d2818; border-left:4px solid #3fb950; padding:12px; border-radius:6px; color:#3fb950; margin-bottom:8px; }
    .alert-sell { background:#2a0a0a; border-left:4px solid #f85149; padding:12px; border-radius:6px; color:#f85149; margin-bottom:8px; }
    .alert-hold { background:#2a2000; border-left:4px solid #d29922; padding:12px; border-radius:6px; color:#d29922; margin-bottom:8px; }
    .pred-card  { background:#161b22; border:1px solid #21262d; border-radius:10px; padding:16px; text-align:center; }

    /* ── MOBILE ── */
    @media (max-width: 768px) {

        /* Λιγότερο padding στο κυρίως περιεχόμενο */
        .main .block-container {
            padding: 0.75rem 0.75rem 2rem 0.75rem !important;
            max-width: 100% !important;
        }

        /* Metrics πιο compact */
        [data-testid="metric-container"] {
            padding: 8px 10px !important;
            border-radius: 8px !important;
        }
        [data-testid="metric-container"] label {
            font-size: 10px !important;
        }
        [data-testid="metric-container"] [data-testid="stMetricValue"] {
            font-size: 14px !important;
        }
        [data-testid="stMetricDelta"] {
            font-size: 10px !important;
        }

        /* Signal badge πιο μικρό */
        .signal-badge {
            font-size: 16px !important;
            padding: 8px 12px !important;
            letter-spacing: 1px !important;
        }

        /* Alerts πιο compact */
        .alert-buy, .alert-sell, .alert-hold {
            padding: 8px 10px !important;
            font-size: 13px !important;
        }

        /* Τίτλοι */
        h1 { font-size: 20px !important; }
        h2 { font-size: 17px !important; }
        h3 { font-size: 15px !important; }

        /* Columns: stack vertically αντί side-by-side */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 120px !important;
        }

        /* Dataframes: scroll horizontally */
        [data-testid="stDataFrame"] {
            overflow-x: auto !important;
        }

        /* Selectbox & inputs μεγαλύτερα για touch */
        .stSelectbox > div, .stNumberInput > div {
            font-size: 16px !important;
        }

        /* Sidebar button πιο μεγάλο */
        [data-testid="collapsedControl"] {
            top: 0.5rem !important;
        }

        /* Expanders */
        .streamlit-expanderHeader {
            font-size: 13px !important;
        }

        /* Κρύψε το EMA 9/21 metric σε πολύ μικρή οθόνη */
        @media (max-width: 480px) {
            [data-testid="metric-container"] [data-testid="stMetricValue"] {
                font-size: 12px !important;
            }
        }
    }
</style>
""", unsafe_allow_html=True)


# ─── CONSTANTS ────────────────────────────────────────────────────────────────
SYMBOLS   = ["BTC-USD","ETH-USD","SOL-USD","BNB-USD","DOGE-USD",
             "ADA-USD","XRP-USD","AVAX-USD","MATIC-USD","DOT-USD","GC=F"]

SYMBOL_LABELS = {
    "BTC-USD":  "BTC",
    "ETH-USD":  "ETH",
    "SOL-USD":  "SOL",
    "BNB-USD":  "BNB",
    "DOGE-USD": "DOGE",
    "ADA-USD":  "ADA",
    "XRP-USD":  "XRP",
    "AVAX-USD": "AVAX",
    "MATIC-USD":"MATIC",
    "DOT-USD":  "DOT",
    "GC=F":     "XAU (Χρυσός)",
}
INTERVALS = {"1 λεπτό":"1m","5 λεπτά":"5m","15 λεπτά":"15m",
             "1 ώρα":"1h","4 ώρες":"4h","1 μέρα":"1d"}
PERIODS   = {"1 μέρα":"1d","5 μέρες":"5d","2 εβδομάδες":"14d",
             "1 μήνας":"30d","3 μήνες":"90d"}
SIGNAL_EMOJI = {"STRONG BUY":"🚀","BUY":"📈","HOLD":"⏸️","SELL":"📉","STRONG SELL":"🔻"}


# ─── DATA & INDICATORS ────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def fetch_data(symbol, period, interval):
    df = yf.download(symbol, period=period, interval=interval, progress=False)
    df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]
    df.dropna(inplace=True)
    return df


def add_indicators(df):
    close = df["close"]
    df["ema_9"]  = close.ewm(span=9,  adjust=False).mean()
    df["ema_21"] = close.ewm(span=21, adjust=False).mean()
    df["ema_50"] = close.ewm(span=50, adjust=False).mean()
    delta = close.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    df["rsi"] = 100 - (100 / (1 + gain.ewm(com=13, adjust=False).mean() /
                                   loss.ewm(com=13, adjust=False).mean()))
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["macd"]        = ema12 - ema26
    df["signal_line"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["hist"]        = df["macd"] - df["signal_line"]
    sma20 = close.rolling(20).mean()
    std20 = close.rolling(20).std()
    df["bb_upper"] = sma20 + 2 * std20
    df["bb_lower"] = sma20 - 2 * std20
    df["bb_mid"]   = sma20

    high_low   = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close  = (df["low"]  - df["close"].shift()).abs()
    tr         = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df["atr"]  = tr.ewm(span=14, adjust=False).mean()

    return df


def generate_signals(df):
    actions, scores = [], []
    for i in range(1, len(df)):
        row, prev = df.iloc[i], df.iloc[i - 1]
        score = 0
        if row["ema_9"] > row["ema_21"] and prev["ema_9"] <= prev["ema_21"]:   score += 2
        elif row["ema_9"] < row["ema_21"] and prev["ema_9"] >= prev["ema_21"]: score -= 2
        score += 1 if row["close"] > row["ema_50"] else -1
        rsi = row["rsi"]
        if   rsi < 30: score += 2
        elif rsi < 45: score += 1
        elif rsi > 70: score -= 2
        elif rsi > 55: score -= 1
        if row["macd"] > row["signal_line"] and prev["macd"] <= prev["signal_line"]:   score += 2
        elif row["macd"] < row["signal_line"] and prev["macd"] >= prev["signal_line"]: score -= 2
        elif row["hist"] > 0: score += 1
        else:                 score -= 1
        if   row["close"] < row["bb_lower"]: score += 1
        elif row["close"] > row["bb_upper"]: score -= 1
        if   score >= 4:  action = "STRONG BUY"
        elif score >= 2:  action = "BUY"
        elif score <= -4: action = "STRONG SELL"
        elif score <= -2: action = "SELL"
        else:             action = "HOLD"
        actions.append(action)
        scores.append(score)
    df = df.iloc[1:].copy()
    df["action"] = actions
    df["score"]  = scores
    return df


def predict_price(df, steps=24):
    close  = df["close"].values.astype(float)
    x      = np.arange(len(close))
    coeffs = np.polyfit(x, close, 1)
    slope  = coeffs[0]
    future_x  = np.arange(len(close), len(close) + steps)
    predicted = np.polyval(coeffs, future_x)
    trend_pct = (predicted[-1] - close[-1]) / close[-1] * 100
    window     = min(50, len(close))
    support    = float(np.min(close[-window:]))
    resistance = float(np.max(close[-window:]))
    return {
        "predicted_prices": predicted,
        "slope":      slope,
        "trend_pct":  trend_pct,
        "support":    support,
        "resistance": resistance,
        "target_bull": close[-1] * 1.03,
        "target_bear": close[-1] * 0.97,
        "stop_loss":   close[-1] * 0.985,
        "steps":       steps,
    }


def action_color(action):
    return {"STRONG BUY":"#3fb950","BUY":"#26c941","HOLD":"#d29922",
            "SELL":"#f85149","STRONG SELL":"#ff4040"}.get(action, "#e6edf3")


def run_backtest(df, tp_pct=0.03, sl_pct=0.015, max_candles=20):
    trades = []
    for i in range(len(df)):
        if df.iloc[i]["action"] not in ("BUY", "STRONG BUY"):
            continue
        entry_price = float(df.iloc[i]["close"])
        tp = entry_price * (1 + tp_pct)
        sl = entry_price * (1 - sl_pct)
        result, exit_price = "OPEN", entry_price
        for j in range(i + 1, min(i + max_candles + 1, len(df))):
            h = float(df.iloc[j]["high"])
            lo = float(df.iloc[j]["low"])
            if lo <= sl:
                result, exit_price = "LOSS", sl; break
            if h >= tp:
                result, exit_price = "WIN", tp; break
        if result == "OPEN":
            exit_price = float(df.iloc[min(i + max_candles, len(df) - 1)]["close"])
            result = "WIN" if exit_price >= entry_price else "LOSS"
        pnl = (exit_price - entry_price) / entry_price * 100
        trades.append({
            "Ώρα Εισόδου": str(df.index[i])[:16],
            "Signal":       df.iloc[i]["action"],
            "Είσοδος":      f"${entry_price:,.2f}",
            "Έξοδος":       f"${exit_price:,.2f}",
            "P&L %":        f"{pnl:+.2f}%",
            "Αποτέλεσμα":   result,
            "_pnl":         pnl,
        })
    return trades


@st.cache_data(ttl=300)
def fetch_mtf(symbol):
    timeframes = [("1H", "1h", "5d"), ("4H", "4h", "30d"), ("1D", "1d", "90d")]
    out = {}
    for name, iv, per in timeframes:
        try:
            d = fetch_data(symbol, per, iv)
            d = add_indicators(d)
            d = generate_signals(d)
            last = d.iloc[-1]
            out[name] = {
                "action": last["action"],
                "rsi":    float(last["rsi"]),
                "score":  int(last["score"]),
                "macd":   float(last["macd"]),
            }
        except Exception:
            out[name] = None
    return out


@st.cache_data(ttl=3600)
def fetch_heatmap_data(symbol):
    try:
        d = yf.download(symbol, period="365d", interval="1d", progress=False)
        d.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in d.columns]
        d["ret"] = d["close"].pct_change() * 100
        d.dropna(inplace=True)
        return d[["close", "ret"]].copy()
    except Exception:
        return None


def build_heatmap_chart(hmap_df):
    hmap_df = hmap_df.copy()
    hmap_df.index = pd.to_datetime(hmap_df.index)
    hmap_df["dow"]     = hmap_df.index.dayofweek
    iso_cal            = hmap_df.index.isocalendar()
    hmap_df["week"]    = iso_cal.week.values
    hmap_df["year"]    = hmap_df.index.year
    hmap_df["week_id"] = (hmap_df["year"] - hmap_df["year"].min()) * 54 + hmap_df["week"]
    weeks   = sorted(hmap_df["week_id"].unique())
    wmap    = {w: i for i, w in enumerate(weeks)}
    z       = np.full((7, len(weeks)), np.nan)
    texts   = [["" for _ in weeks] for _ in range(7)]
    for _, row in hmap_df.iterrows():
        wi = wmap[row["week_id"]]
        di = int(row["dow"])
        z[di][wi]      = row["ret"]
        texts[di][wi]  = f"{row.name.strftime('%d/%m/%y')}<br>{row['ret']:+.2f}%"
    fig = go.Figure(go.Heatmap(
        z=z, text=texts,
        hovertemplate="%{text}<extra></extra>",
        colorscale=[[0, "#f85149"], [0.45, "#2a0a0a"], [0.5, "#161b22"],
                    [0.55, "#0d2818"], [1, "#3fb950"]],
        zmid=0, zmin=-5, zmax=5,
        showscale=True,
        colorbar=dict(
            title=dict(text="% Απόδοση", font=dict(color="#e6edf3")),
            tickfont=dict(color="#e6edf3"),
            len=0.8,
        ),
        xgap=2, ygap=2,
    ))
    fig.update_layout(
        height=230, paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        margin=dict(l=50, r=80, t=10, b=20),
        font=dict(color="#e6edf3"),
        yaxis=dict(tickvals=list(range(7)),
                   ticktext=["Δευ", "Τρι", "Τετ", "Πεμ", "Παρ", "Σαβ", "Κυρ"],
                   gridcolor="#21262d", zeroline=False),
        xaxis=dict(showticklabels=False, gridcolor="#21262d"),
    )
    return fig


@st.cache_data(ttl=1800)
def fetch_news(symbol_name):
    coin = symbol_name.replace("-USD", "").lower()
    feeds = [
        ("CoinTelegraph", "https://cointelegraph.com/rss"),
        ("CoinDesk",      "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    ]
    articles = []
    for source, url in feeds:
        try:
            r = requests.get(url, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
            root = ET.fromstring(r.content)
            for item in root.iter("item"):
                title   = item.findtext("title", "").strip()
                link    = item.findtext("link",  "").strip()
                pubdate = item.findtext("pubDate", "")[:22].strip()
                if not title:
                    continue
                articles.append({
                    "title":  title,
                    "link":   link,
                    "date":   pubdate,
                    "source": source,
                    "relevant": coin in title.lower() or "crypto" in title.lower(),
                })
        except Exception:
            pass
    articles.sort(key=lambda x: (not x["relevant"], x["source"]))
    return articles[:16]


@st.cache_data(ttl=3600)
def fetch_fear_greed():
    """Fear & Greed Index από alternative.me API (δωρεάν)."""
    try:
        r = requests.get("https://api.alternative.me/fng/?limit=10", timeout=5)
        data = r.json()["data"]
        latest = data[0]
        history = [{"date": datetime.fromtimestamp(int(d["timestamp"])),
                    "value": int(d["value"]),
                    "label": d["value_classification"]} for d in data]
        return {
            "value":   int(latest["value"]),
            "label":   latest["value_classification"],
            "history": history,
            "ok":      True,
        }
    except Exception:
        return {"value": 50, "label": "Neutral", "history": [], "ok": False}


def fng_color(value):
    if value <= 25:  return "#f85149", "Extreme Fear"
    if value <= 45:  return "#ffa657", "Fear"
    if value <= 55:  return "#d29922", "Neutral"
    if value <= 75:  return "#26c941", "Greed"
    return "#3fb950", "Extreme Greed"


def fng_gauge(value):
    color, _ = fng_color(value)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"font": {"color": color, "size": 48}},
        gauge={
            "axis":  {"range": [0, 100], "tickcolor": "#8b949e",
                      "tickfont": {"color": "#8b949e", "size": 10}},
            "bar":   {"color": color, "thickness": 0.25},
            "bgcolor": "#161b22",
            "bordercolor": "#21262d",
            "steps": [
                {"range": [0,  25], "color": "#2a0a0a"},
                {"range": [25, 45], "color": "#2a1500"},
                {"range": [45, 55], "color": "#2a2000"},
                {"range": [55, 75], "color": "#0d200f"},
                {"range": [75,100], "color": "#0d2818"},
            ],
            "threshold": {"line": {"color": color, "width": 4},
                          "thickness": 0.8, "value": value},
        }
    ))
    fig.update_layout(
        height=260, margin=dict(l=20, r=20, t=20, b=10),
        paper_bgcolor="#0d1117", font=dict(color="#e6edf3")
    )
    return fig


@st.cache_data(ttl=300)
def fetch_eur_usd():
    try:
        t = yf.Ticker("EURUSD=X")
        rate = float(t.fast_info["last_price"])
        return rate if rate > 0 else 1.10
    except Exception:
        return 1.10


def usd_to_eur(usd, rate):
    return usd / rate


def get_live_price(symbol):
    try:
        t = yf.Ticker(symbol)
        p = t.fast_info["last_price"]
        return float(p)
    except Exception:
        return None


def portfolio_summary(holdings):
    """Υπολογίζει P&L για κάθε θέση."""
    rows = []
    total_invested = 0.0
    total_current  = 0.0

    for h in holdings:
        live = get_live_price(h["symbol"])
        if live is None:
            continue
        invested = h["amount"] * h["buy_price"]
        current  = h["amount"] * live
        pnl      = current - invested
        pnl_pct  = (pnl / invested * 100) if invested > 0 else 0
        total_invested += invested
        total_current  += current
        rows.append({
            "Crypto":       SYMBOL_LABELS.get(h["symbol"], h["symbol"].replace("-USD","")),
            "Ποσότητα":     h["amount"],
            "Τιμή Αγοράς":  f"${h['buy_price']:,.2f}",
            "Τιμή Τώρα":    f"${live:,.2f}",
            "Επενδύθηκαν":  f"${invested:,.2f}",
            "Αξία Τώρα":    f"${current:,.2f}",
            "P&L ($)":      f"{'+'if pnl>=0 else ''}{pnl:,.2f}",
            "P&L (%)":      f"{'+'if pnl_pct>=0 else ''}{pnl_pct:.2f}%",
            "_pnl":         pnl,
        })

    total_pnl     = total_current - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
    return rows, total_invested, total_current, total_pnl, total_pnl_pct


# ─── CHARTS ───────────────────────────────────────────────────────────────────
def build_main_chart(df):
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                        row_heights=[0.5,0.15,0.175,0.175], vertical_spacing=0.02,
                        subplot_titles=("","Volume","RSI","MACD"))
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        increasing_line_color="#3fb950", decreasing_line_color="#f85149",
        increasing_fillcolor="#0d2818", decreasing_fillcolor="#2a0a0a",
        name="Τιμή", showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["bb_upper"], line=dict(color="#58a6ff",width=1),
                             name="BB Upper", opacity=0.4), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["bb_lower"], line=dict(color="#58a6ff",width=1),
                             fill="tonexty", fillcolor="rgba(88,166,255,0.07)",
                             name="BB Lower", opacity=0.4), row=1, col=1)
    for col, color, name in [("ema_9","#ffa657","EMA 9"),("ema_21","#bc8cff","EMA 21"),("ema_50","#d29922","EMA 50")]:
        fig.add_trace(go.Scatter(x=df.index, y=df[col], line=dict(color=color,width=1.5), name=name), row=1, col=1)
    for act, sym, color, size in [("STRONG BUY","triangle-up","#3fb950",14),("BUY","triangle-up","#26c941",10),
                                    ("STRONG SELL","triangle-down","#f85149",14),("SELL","triangle-down","#e05c5c",10)]:
        mask = df["action"] == act
        if mask.any():
            fig.add_trace(go.Scatter(x=df.index[mask], y=df["close"][mask], mode="markers",
                                     marker=dict(symbol=sym, size=size, color=color,
                                                 line=dict(color="white",width=1)), name=act), row=1, col=1)
    vol_colors = ["#3fb950" if df["close"].iloc[i] >= df["open"].iloc[i] else "#f85149" for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df["volume"], marker_color=vol_colors, showlegend=False), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["rsi"], line=dict(color="#ffa657",width=1.5),
                             name="RSI", showlegend=False), row=3, col=1)
    fig.add_hline(y=70, line=dict(color="#f85149",width=1,dash="dash"), row=3, col=1)
    fig.add_hline(y=30, line=dict(color="#3fb950",width=1,dash="dash"), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["macd"], line=dict(color="#58a6ff",width=1.5),
                             showlegend=False), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["signal_line"], line=dict(color="#ffa657",width=1.5),
                             showlegend=False), row=4, col=1)
    hist_colors = ["#3fb950" if v >= 0 else "#f85149" for v in df["hist"]]
    fig.add_trace(go.Bar(x=df.index, y=df["hist"], marker_color=hist_colors, showlegend=False), row=4, col=1)
    fig.update_layout(height=750, paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
                      font=dict(color="#e6edf3", family="monospace"),
                      xaxis_rangeslider_visible=False, margin=dict(l=10,r=10,t=30,b=10),
                      legend=dict(bgcolor="#161b22", bordercolor="#21262d", borderwidth=1,
                                  font=dict(size=11), orientation="h", y=1.02),
                      hovermode="x unified",
                      hoverlabel=dict(bgcolor="#161b22", bordercolor="#21262d"))
    for i in range(1, 5):
        fig.update_xaxes(gridcolor="#21262d", showgrid=True, zeroline=False,
                         showspikes=True, spikecolor="#58a6ff", spikethickness=1, row=i, col=1)
        fig.update_yaxes(gridcolor="#21262d", showgrid=True, zeroline=False, row=i, col=1)
    fig.update_yaxes(tickprefix="$", tickformat=",.0f", row=1, col=1)
    fig.update_yaxes(range=[0, 100], row=3, col=1)
    return fig


def build_prediction_chart(df, pred):
    close   = df["close"].values.astype(float)
    recent  = df.tail(48)
    freq    = df.index[-1] - df.index[-2]
    fut_idx = [df.index[-1] + freq * (i + 1) for i in range(pred["steps"])]
    color   = "#3fb950" if pred["slope"] > 0 else "#f85149"

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=recent.index, y=recent["close"].astype(float),
                             line=dict(color="#e6edf3", width=2), name="Ιστορική Τιμή"))
    # Σύνδεση ιστορικής με predicted
    connect_x = [df.index[-1]] + fut_idx
    connect_y = [float(close[-1])] + list(pred["predicted_prices"])
    fig.add_trace(go.Scatter(x=connect_x, y=connect_y,
                             line=dict(color=color, width=2, dash="dot"),
                             name="Πρόβλεψη"))
    # Confidence band ±2%
    upper = [p * 1.02 for p in pred["predicted_prices"]]
    lower = [p * 0.98 for p in pred["predicted_prices"]]
    fig.add_trace(go.Scatter(
        x=fut_idx + fut_idx[::-1], y=upper + lower[::-1],
        fill="toself",
        fillcolor=f"rgba({'63,185,80' if pred['slope']>0 else '248,81,73'},0.12)",
        line=dict(color="rgba(0,0,0,0)"), name="Εύρος ±2%"))
    # Support / Resistance
    fig.add_hline(y=pred["resistance"], line=dict(color="#f85149", dash="dash", width=1.5),
                  annotation_text=f"  Resistance  ${pred['resistance']:,.0f}",
                  annotation_font_color="#f85149")
    fig.add_hline(y=pred["support"], line=dict(color="#3fb950", dash="dash", width=1.5),
                  annotation_text=f"  Support  ${pred['support']:,.0f}",
                  annotation_font_color="#3fb950")
    # Τρέχουσα τιμή
    fig.add_hline(y=float(close[-1]), line=dict(color="#58a6ff", dash="dot", width=1),
                  annotation_text=f"  Τώρα  ${float(close[-1]):,.0f}",
                  annotation_font_color="#58a6ff")
    fig.update_layout(
        height=380, paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
        font=dict(color="#e6edf3"), margin=dict(l=10, r=120, t=40, b=10),
        legend=dict(bgcolor="#161b22", bordercolor="#21262d", borderwidth=1),
        hovermode="x unified",
        title=dict(text=f"Πρόβλεψη επόμενων {pred['steps']} κεριών", font=dict(size=13, color="#8b949e")))
    fig.update_xaxes(gridcolor="#21262d", zeroline=False)
    fig.update_yaxes(gridcolor="#21262d", zeroline=False, tickprefix="$", tickformat=",.0f")
    return fig


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Ρυθμίσεις")
    st.markdown("---")
    symbol   = st.selectbox("🪙 Crypto", SYMBOLS, index=0,
                            format_func=lambda s: SYMBOL_LABELS.get(s, s))
    interval = st.selectbox("⏱️ Timeframe",  list(INTERVALS.keys()), index=3)
    period   = st.selectbox("📅 Περίοδος",   list(PERIODS.keys()),   index=3)
    pred_steps = st.slider("🔮 Κεριά πρόβλεψης", min_value=6, max_value=48, value=24, step=6)
    st.markdown("---")
    st.markdown("## ⚗️ Backtesting")
    bt_tp = st.slider("🎯 Take-Profit %", min_value=1.0, max_value=10.0, value=3.0, step=0.5)
    bt_sl = st.slider("🛡️ Stop-Loss %",   min_value=0.5, max_value=5.0,  value=1.5, step=0.5)
    st.markdown("---")
    auto_refresh = st.toggle("🔄 Auto Refresh (60s)", value=False)
    refresh_btn  = st.button("🔄 Refresh τώρα")

    # ── Οδηγός Χρήσης ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 📖 Οδηγός Χρήσης")

    with st.expander("🚦 Τι σημαίνουν τα Signals"):
        st.markdown("""
**🚀 STRONG BUY**
Πολύ δυνατό σήμα αγοράς. Όλοι οι indicators συμφωνούν ότι η τιμή θα ανέβει. Αγόρασε τώρα.

**📈 BUY**
Καλή στιγμή για αγορά. Οι περισσότεροι indicators είναι bullish.

**⏸️ HOLD**
Δεν υπάρχει καθαρό σήμα. Περίμενε. Μην κάνεις τίποτα.

**📉 SELL**
Καλή στιγμή για πώληση. Οι περισσότεροι indicators είναι bearish.

**🔻 STRONG SELL**
Πολύ δυνατό σήμα πώλησης. Πούλα άμεσα.
""")

    with st.expander("📊 RSI — Τι είναι"):
        st.markdown("""
**RSI (Relative Strength Index)**
Μετράει αν μια τιμή έχει ανέβει ή κατέβει πολύ γρήγορα.

| Τιμή | Σημαίνει | Ενέργεια |
|------|----------|----------|
| < 30 | Oversold — πολύ φθηνό | 🟢 Αγόρασε |
| 30–50 | Neutral / πτωτικό | ⏸️ Περίμενε |
| 50–70 | Neutral / ανοδικό | ⏸️ Περίμενε |
| > 70 | Overbought — πολύ ακριβό | 🔴 Πούλα |

**Παράδειγμα:** RSI = 25 → Το BTC έχει πέσει πολύ → Πιθανή ανάκαμψη → BUY
""")

    with st.expander("📉 MACD — Τι είναι"):
        st.markdown("""
**MACD (Moving Average Convergence Divergence)**
Μετράει την **ορμή** (momentum) της αγοράς — πόσο γρήγορα κινείται η τιμή.

**Αποτελείται από:**
- 🔵 **MACD line** = η "γρήγορη" γραμμή
- 🟠 **Signal line** = η "αργή" γραμμή
- **Histogram** = η διαφορά τους

**Signals:**
- MACD **κόβει από κάτω προς τα πάνω** το Signal → 🟢 **BUY**
- MACD **κόβει από πάνω προς τα κάτω** το Signal → 🔴 **SELL**
- Histogram **πράσινο & μεγαλώνει** → Ανοδική ορμή δυναμώνει
- Histogram **κόκκινο & μεγαλώνει** → Καθοδική ορμή δυναμώνει
""")

    with st.expander("📈 EMA 9 — Τι είναι"):
        st.markdown("""
**EMA 9 (Exponential Moving Average 9)** 🟠
Ο μέσος όρος της τιμής των **τελευταίων 9 κεριών**.

- Είναι η **πιο γρήγορη** γραμμή — ακολουθεί στενά την τιμή
- Όταν η τιμή είναι **πάνω** από EMA 9 → Βραχυπρόθεσμα ανοδικό
- Όταν η τιμή είναι **κάτω** από EMA 9 → Βραχυπρόθεσμα καθοδικό

**Χρήση:** Δείχνει άμεσες αλλαγές κατεύθυνσης. Χρήσιμο για scalping (γρήγορες συναλλαγές).
""")

    with st.expander("📈 EMA 21 — Τι είναι"):
        st.markdown("""
**EMA 21 (Exponential Moving Average 21)** 🟣
Ο μέσος όρος της τιμής των **τελευταίων 21 κεριών**.

- Είναι **μεσαία ταχύτητα** — πιο σταθερή από EMA 9
- Χρησιμοποιείται μαζί με EMA 9 για **crossover signals**

**Crossover (το πιο σημαντικό signal):**
- EMA 9 **ανεβαίνει πάνω** από EMA 21 → 🟢 **Golden Cross = BUY**
- EMA 9 **κατεβαίνει κάτω** από EMA 21 → 🔴 **Death Cross = SELL**

**Παράδειγμα:** Φαντάσου 2 αυτοκίνητα — το EMA 9 είναι το γρήγορο, το EMA 21 το αργό. Όταν το γρήγορο ξεπεράσει το αργό → η αγορά επιταχύνει ανοδικά.
""")

    with st.expander("📈 EMA 50 — Τι είναι"):
        st.markdown("""
**EMA 50 (Exponential Moving Average 50)** 🟡
Ο μέσος όρος της τιμής των **τελευταίων 50 κεριών**.

- Είναι η **πιο αργή** γραμμή — δείχνει το **μεγάλο trend**
- Λειτουργεί σαν **δυναμικό support/resistance**

**Ερμηνεία:**
- Τιμή **πάνω** από EMA 50 → Η αγορά είναι γενικά **ανοδική** (bullish)
- Τιμή **κάτω** από EMA 50 → Η αγορά είναι γενικά **καθοδική** (bearish)
- Τιμή **αγγίζει** EMA 50 από πάνω → Συχνά bounces back πάνω (support)
- Τιμή **αγγίζει** EMA 50 από κάτω → Συχνά bounces back κάτω (resistance)
""")

    with st.expander("💙 Bollinger Bands — Τι είναι"):
        st.markdown("""
**Bollinger Bands**
Τρεις γραμμές που δείχνουν το **κανονικό εύρος** τιμής.

- **Upper Band** (πάνω γραμμή) = Άνω όριο
- **Middle Band** (μεσαία) = SMA 20 (μέσος όρος 20 κεριών)
- **Lower Band** (κάτω γραμμή) = Κάτω όριο

**Signals:**
- Τιμή **αγγίζει Upper Band** → Overbought → 🔴 Πιθανή πτώση
- Τιμή **αγγίζει Lower Band** → Oversold → 🟢 Πιθανή άνοδος
- Bands **στενεύουν** (squeeze) → Μεγάλη κίνηση έρχεται!
- Bands **ανοίγουν** → Η τρέχουσα κίνηση συνεχίζεται

**Tip:** Η τιμή πάντα επιστρέφει στη μεσαία γραμμή — αυτό είναι "mean reversion".
""")

    with st.expander("📊 Volume — Τι είναι"):
        st.markdown("""
**Volume**
Πόση ποσότητα crypto αγοράστηκε/πουλήθηκε σε κάθε κερί.

- 🟢 **Πράσινη μπάρα** = Bullish candle (τιμή έκλεισε ψηλότερα)
- 🔴 **Κόκκινη μπάρα** = Bearish candle (τιμή έκλεισε χαμηλότερα)
- **Μεγάλο volume** = Πολλοί traders ενεργοί → Ισχυρή κίνηση
- **Μικρό volume** = Λίγοι traders → Αδύναμη κίνηση

**Κανόνας:** Ένα BUY signal με **μεγάλο volume** είναι πολύ πιο αξιόπιστο από ένα με μικρό volume.
""")

    with st.expander("🔮 Πώς δουλεύουν οι Προβλέψεις"):
        st.markdown("""
**Linear Regression Prediction**

Ο αλγόριθμος κοιτάει **όλες τις ιστορικές τιμές** και βρίσκει τη γραμμή που τις "ταιριάζει" καλύτερα — σαν να τραβάς μια ευθεία μέσα από τελείες.

**Τι δείχνει το γράφημα:**
- **Λευκή γραμμή** = Πραγματική τιμή (ιστορική)
- **Χρωματιστή διακεκομμένη** = Πρόβλεψη κατεύθυνσης
- **Σκιασμένη περιοχή ±2%** = Εύρος αβεβαιότητας
- **Πράσινη οριζόντια** = Support (κάτω όριο)
- **Κόκκινη οριζόντια** = Resistance (άνω όριο)

**Τι είναι τα "Κεριά Πρόβλεψης" (slider 6–48):**
Καθορίζει **πόσο μακριά** να κοιτάει η πρόβλεψη στο μέλλον. Ένα "κερί" = ένα χρονικό διάστημα ανάλογα με το timeframe σου:

| Timeframe | 24 κεριά | 48 κεριά |
|-----------|----------|----------|
| 1 λεπτό | 24 λεπτά | 48 λεπτά |
| 1 ώρα | 24 ώρες (1 μέρα) | 48 ώρες (2 μέρες) |
| 4 ώρες | 4 μέρες | 8 μέρες |
| 1 μέρα | 24 μέρες | 48 μέρες |

💡 **Συμβουλή:** Λιγότερα κεριά = πιο αξιόπιστη πρόβλεψη. Όσο πιο μακριά κοιτάς, τόσο πιο αβέβαιο γίνεται.

**Support & Resistance:**
- **Support** = Επίπεδο τιμής που "σταματά" η πτώση — εκεί οι αγοραστές είναι πολλοί
- **Resistance** = Επίπεδο τιμής που "σταματά" η άνοδος — εκεί οι πωλητές είναι πολλοί

⚠️ **Σημαντικό:** Οι προβλέψεις δείχνουν **τάση** βάσει παρελθόντος. Δεν λαμβάνουν υπόψη news, tweets, regulations. Χρησιμοποίησέ τες ως **ένδειξη**, όχι ως εγγύηση.
""")

    with st.expander("🎯 Πώς να χρησιμοποιήσω το Vantage"):
        st.markdown("""
**Βήμα-βήμα:**

1. Άνοιξε το dashboard και κοίτα το **signal**
2. Αν είναι **BUY / STRONG BUY:**
   - Πήγαινε στο Vantage
   - Άνοιξε **Long position** στο crypto
   - Βάλε **Stop-Loss** στο -1.5% κάτω από την τιμή αγοράς
   - Βάλε **Take-Profit** στο +3% πάνω
3. Αν είναι **SELL / STRONG SELL:**
   - Κλείσε την υπάρχουσα θέση σου
   - Ή άνοιξε **Short position**
4. Αν είναι **HOLD** — μην κάνεις τίποτα

**Κανόνες ασφαλείας:**
- ✅ Ποτέ μην ρισκάρεις > 5% του κεφαλαίου σου σε ένα trade
- ✅ Πάντα βάλε stop-loss
- ✅ Μην αγοράζεις βάσει ενός μόνο signal — περίμενε επιβεβαίωση
""")

    with st.expander("⏱️ Multi-Timeframe — Τι είναι"):
        st.markdown("""
**Multi-Timeframe Analysis**

Δείχνει το signal για το **ίδιο crypto** σε 3 διαφορετικά χρονικά πλαίσια ταυτόχρονα.

| Timeframe | Τι δείχνει |
|-----------|------------|
| **1H** | Βραχυπρόθεσμη τάση (επόμενες ώρες) |
| **4H** | Μεσοπρόθεσμη τάση (επόμενες μέρες) |
| **1D** | Μακροπρόθεσμη τάση (επόμενες εβδομάδες) |

**✅ = Συμφωνεί** με το τρέχον timeframe που έχεις επιλέξει.
**⚠️ = Διαφωνεί** — προσοχή, το σήμα μπορεί να είναι αδύναμο.

**Χρυσός κανόνας:** Αν και τα **3 timeframes δείχνουν BUY** → πολύ ισχυρό σήμα. Αν διαφωνούν → περίμενε.
""")

    with st.expander("📐 ATR & Position Sizing — Τι είναι"):
        st.markdown("""
**ATR (Average True Range)**

Μετράει την **volatility** (αστάθεια) της αγοράς — πόσο κινείται κατά μέσο όρο η τιμή σε κάθε κερί.

- **Μεγάλο ATR** = Αγρία αγορά, μεγάλες κινήσεις → χρειάζεσαι μεγαλύτερο stop-loss
- **Μικρό ATR** = Ήρεμη αγορά, μικρές κινήσεις → μπορείς στενότερο stop-loss

**Position Sizing (βάσει ATR):**
Το dashboard υπολογίζει αυτόματα:
- **Stop-Loss** = Τρέχουσα τιμή − (2 × ATR) → εκεί που "σπάει" η κίνηση
- **Take-Profit** = Τρέχουσα τιμή + (3 × ATR) → ρεαλιστικός στόχος κέρδους
- **Volatility %** = ATR ÷ Τιμή × 100 → πόσο % κινείται κατά μέσο όρο

💡 **Γιατί 2×ATR stop-loss;** Γιατί αν βάλεις στενότερο stop, η κανονική κίνηση της αγοράς θα σε "βγάλει" έξω πριν κάνεις κέρδος.
""")

    with st.expander("⚗️ Backtesting — Τι είναι"):
        st.markdown("""
**Τι είναι το Backtesting;**

Φαντάσου ότι έχεις μια μηχανή του χρόνου. Γυρνάς πίσω στο παρελθόν και κοιτάς:

> *"Αν είχα ακολουθήσει κάθε BUY signal που έβγαλε το dashboard, πόσα θα κέρδιζα ή θα έχανα;"*

Αυτό ακριβώς κάνει το backtesting — **δοκιμάζει τα signals στο ιστορικό** για να δεις αν λειτουργούν.

**Πώς δουλεύει:**
1. Βρίσκει κάθε BUY signal στο ιστορικό
2. Προσομοιώνει αγορά σε εκείνη την τιμή
3. Κλείνει τη θέση όταν:
   - Η τιμή ανεβεί κατά **Take-Profit %** → **WIN** ✅
   - Η τιμή πέσει κατά **Stop-Loss %** → **LOSS** ❌
   - Περάσουν 20 κεριά χωρίς να αγγίξει κανένα όριο → κλείνει στην τρέχουσα τιμή

**Τι σου δείχνει:**
- **Win Rate %** = Πόσες φορές στις 100 το signal ήταν σωστό
- **Expectancy** = Μέσο κέρδος/ζημιά ανά trade — αν είναι **θετικό**, η στρατηγική κερδίζει μακροπρόθεσμα
- **Equity Curve** = Γράφημα πώς εξελίσσεται το κεφάλαιό σου trade-by-trade

**Οι sliders TP/SL:** Μπορείς να αλλάξεις τα ποσοστά και να δεις αν η στρατηγική βελτιώνεται.

⚠️ Το backtesting δείχνει **ιστορική** απόδοση. Δεν εγγυάται ίδια αποτελέσματα στο μέλλον.
""")

    with st.expander("🗓️ Heatmap Αποδόσεων — Τι είναι"):
        st.markdown("""
**Heatmap Ημερήσιων Αποδόσεων**

Είναι σαν ημερολόγιο που δείχνει με χρώμα αν κάθε μέρα ήταν κερδοφόρα ή όχι.

- 🟢 **Πράσινο τετράγωνο** = Η τιμή έκλεισε ψηλότερα εκείνη τη μέρα (κέρδος)
- 🔴 **Κόκκινο τετράγωνο** = Η τιμή έκλεισε χαμηλότερα (ζημιά)
- **Πιο έντονο χρώμα** = Μεγαλύτερη κίνηση

Κάθε γραμμή = μια μέρα της εβδομάδας (Δευ–Κυρ), κάθε στήλη = μια εβδομάδα.

**Κάτω από το heatmap:** Bar chart με τη **μηνιαία απόδοση** — βλέπεις ποιοι μήνες ήταν καλοί και ποιοι κακοί.

💡 **Χρήση:** Αν βλέπεις πολλά κόκκινα τετράγωνα τις τελευταίες εβδομάδες → bearish τάση. Πολλά πράσινα → bullish momentum.
""")

    with st.expander("🔍 Multi-Crypto Screener — Τι είναι"):
        st.markdown("""
**Multi-Crypto Screener**

Δείχνει το **τρέχον signal** για όλα τα cryptos ταυτόχρονα σε έναν πίνακα, ώστε να βρεις γρήγορα ευκαιρίες χωρίς να αλλάζεις ένα-ένα.

- Ταξινομείται αυτόματα: **STRONG BUY πρώτα → STRONG SELL τελευταία**
- Το border κάθε κάρτας έχει το χρώμα του signal (πράσινο/κόκκινο/κίτρινο)
- Ανανεώνεται κάθε **2 λεπτά**

💡 **Χρήση:** Αν ο screener δείχνει πολλά BUY ταυτόχρονα → η αγορά είναι γενικά ανοδική (bullish). Αν όλα SELL → bearish αγορά, προσοχή.
""")

    with st.expander("📰 News Feed — Τι είναι"):
        st.markdown("""
**Crypto News Feed**

Εμφανίζει τα τελευταία νέα από **CoinTelegraph** και **CoinDesk** απευθείας μέσα στο dashboard.

- 🟢 **Πράσινο border** = Το άρθρο αφορά το crypto που έχεις επιλέξει
- Τα σχετικά νέα εμφανίζονται **πρώτα** αυτόματα
- Ανανεώνεται κάθε **30 λεπτά**

💡 **Γιατί είναι σημαντικό:** Τα signals βασίζονται σε αριθμούς — αλλά μια μεγάλη είδηση (π.χ. "SEC απαγορεύει το BTC") μπορεί να αναιρέσει οποιοδήποτε technical signal. Πάντα κοίτα τα news πριν ανοίξεις θέση.
""")

    st.markdown("---")
    st.markdown("<small style='color:#8b949e'>⚠️ Εργαλείο ανάλυσης. Όχι χρηματοοικονομική συμβουλή.</small>",
                unsafe_allow_html=True)


# ─── MAIN ─────────────────────────────────────────────────────────────────────
st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
""", unsafe_allow_html=True)
st.markdown("# 📈 Crypto Signal Dashboard")
st.markdown(f"<small style='color:#8b949e'>Τελευταία ενημέρωση: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</small>",
            unsafe_allow_html=True)
st.markdown("---")

with st.spinner(f"Φορτώνω δεδομένα για {symbol}..."):
    try:
        df = fetch_data(symbol, PERIODS[period], INTERVALS[interval])
        df = add_indicators(df)
        df = generate_signals(df)
    except Exception as e:
        st.error(f"Σφάλμα: {e}")
        st.stop()

last   = df.iloc[-1]
price  = float(last["close"])
prev_p = float(df.iloc[-2]["close"])
change = price - prev_p
pct    = (change / prev_p) * 100
action = last["action"]
rsi    = float(last["rsi"])
macd   = float(last["macd"])
sig    = float(last["signal_line"])
emoji  = SIGNAL_EMOJI.get(action, "")

# ── Metrics ───────────────────────────────────────────────────────────────────
atr_val   = float(last["atr"]) if "atr" in last.index else 0.0
sl_price  = price - 2 * atr_val
tp_price  = price + 3 * atr_val
eur_rate  = fetch_eur_usd()
price_eur = usd_to_eur(price, eur_rate)
change_eur = usd_to_eur(change, eur_rate)

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("💰 Τιμή (USD)",  f"${price:,.2f}",               f"{change:+.2f} ({pct:+.2f}%)")
c2.metric("💶 Τιμή (EUR)",  f"€{price_eur:,.2f}",           f"€{change_eur:+.2f} | 1€={eur_rate:.4f}$")
c3.metric("📊 RSI",         f"{rsi:.1f}",                   "Oversold" if rsi<30 else "Overbought" if rsi>70 else "Neutral")
c4.metric("📉 MACD",        f"{macd:.2f}",                  f"Signal: {sig:.2f}")
c5.metric("📈 EMA 50",      f"${float(last['ema_50']):,.2f}")
c6.metric("📐 ATR (14)",    f"${atr_val:,.2f}",             f"SL: ${sl_price:,.2f}")

st.markdown("<br>", unsafe_allow_html=True)

# ── Signal Badge ──────────────────────────────────────────────────────────────
css_class = "signal-" + action.replace(" ", "-")
st.markdown(f'<div class="signal-badge {css_class}">{emoji} &nbsp; {action}</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ── Alert ─────────────────────────────────────────────────────────────────────
score_val = int(last["score"])
if "BUY" in action:
    st.markdown(f"""<div class="alert-buy">
    🚀 <b>Σήμα Αγοράς!</b> — Εξέτασε αγορά <b>{symbol}</b> στο Vantage @ <b>${price:,.2f}</b> &nbsp;·&nbsp; <b>€{price_eur:,.2f}</b><br>
    <small>RSI: {rsi:.1f} | MACD: {macd:.4f} | Δύναμη signal: {score_val}/8</small>
    </div>""", unsafe_allow_html=True)
elif "SELL" in action:
    st.markdown(f"""<div class="alert-sell">
    🔻 <b>Σήμα Πώλησης!</b> — Εξέτασε πώληση <b>{symbol}</b> στο Vantage @ <b>${price:,.2f}</b> &nbsp;·&nbsp; <b>€{price_eur:,.2f}</b><br>
    <small>RSI: {rsi:.1f} | MACD: {macd:.4f} | Δύναμη signal: {score_val}/8</small>
    </div>""", unsafe_allow_html=True)
else:
    st.markdown(f"""<div class="alert-hold">
    ⏸️ <b>Περίμενε.</b> — Δεν υπάρχει καθαρό σήμα αυτή τη στιγμή.<br>
    <small>RSI: {rsi:.1f} | MACD: {macd:.4f} | Δύναμη signal: {score_val}/8 | EUR/USD: {eur_rate:.4f}</small>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Multi-Timeframe Analysis ──────────────────────────────────────────────────
st.markdown("---")
st.markdown("### ⏱️ Multi-Timeframe Analysis")
st.markdown("<small style='color:#8b949e'>Σύγκριση signal στα 3 βασικά timeframes. Αν συμφωνούν και τα 3 → πολύ ισχυρό σήμα.</small>",
            unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

with st.spinner("Φορτώνω multi-timeframe..."):
    mtf_data = fetch_mtf(symbol)

mtf_cols = st.columns(3)
tf_labels = {"1H": "1 Ώρα", "4H": "4 Ώρες", "1D": "1 Μέρα"}
for col, (tf, label) in zip(mtf_cols, tf_labels.items()):
    info = mtf_data.get(tf)
    if info is None:
        col.markdown(f"<div style='background:#161b22;border:1px solid #21262d;border-radius:10px;padding:18px;text-align:center;'><b style='color:#8b949e'>{label}</b><br><span style='color:#8b949e'>—</span></div>", unsafe_allow_html=True)
        continue
    act   = info["action"]
    color = action_color(act)
    emj   = SIGNAL_EMOJI.get(act, "")
    agree_icon = "✅" if act == action else "⚠️"
    col.markdown(f"""
<div style="background:#161b22;border:2px solid {color};border-radius:10px;padding:18px;text-align:center;">
  <div style="color:#8b949e;font-size:13px;font-weight:bold;">{label} {agree_icon}</div>
  <div style="color:{color};font-size:20px;font-weight:bold;margin:8px 0;">{emj} {act}</div>
  <div style="color:#8b949e;font-size:12px;">RSI {info['rsi']:.1f} | Score {info['score']}/8</div>
</div>""", unsafe_allow_html=True)

# ── ATR Position Sizing ───────────────────────────────────────────────────────
if atr_val > 0:
    st.markdown("<br>", unsafe_allow_html=True)
    risk_budget = 100.0
    pos_size    = risk_budget / (2 * atr_val / price * 100)
    st.markdown(f"""
<div style="background:#161b22;border:1px solid #21262d;border-radius:10px;padding:16px;">
  <span style="color:#8b949e;font-size:13px;font-weight:bold;">📐 ATR Position Sizing (βάσει 2% κινδύνου ανά $100 κεφάλαιο)</span><br><br>
  <span style="color:#e6edf3;">Stop-Loss: </span><span style="color:#f85149;font-weight:bold;">${price - 2*atr_val:,.2f}</span>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <span style="color:#e6edf3;">Take-Profit: </span><span style="color:#3fb950;font-weight:bold;">${price + 3*atr_val:,.2f}</span>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <span style="color:#e6edf3;">ATR: </span><span style="color:#58a6ff;font-weight:bold;">${atr_val:,.2f}</span>
  &nbsp;&nbsp;|&nbsp;&nbsp;
  <span style="color:#e6edf3;">Volatility: </span><span style="color:#ffa657;font-weight:bold;">{atr_val/price*100:.2f}%</span>
</div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Main Chart ────────────────────────────────────────────────────────────────
st.markdown("### 📊 Γράφημα Τιμής")
st.plotly_chart(build_main_chart(df), use_container_width=True)

# ── Προβλέψεις ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🔮 Προβλέψεις Τιμής")

pred       = predict_price(df, steps=pred_steps)
trend_dir  = "📈 Ανοδική" if pred["slope"] > 0 else "📉 Καθοδική"
trend_color= "#3fb950" if pred["slope"] > 0 else "#f85149"

p1,p2,p3,p4 = st.columns(4)
p1.metric("📐 Τάση",           trend_dir,                        f"{pred['trend_pct']:+.2f}%")
p2.metric("🎯 Take-Profit +3%", f"${pred['target_bull']:,.2f}",  "+3%")
p3.metric("🛡️ Stop-Loss -1.5%", f"${pred['stop_loss']:,.2f}",   "-1.5%")
p4.metric("⚠️ Worst Case -3%",  f"${pred['target_bear']:,.2f}", "-3%")

st.markdown("<br>", unsafe_allow_html=True)

sr1, sr2 = st.columns(2)
with sr1:
    st.markdown(f"""<div style="background:#0d2818;border:1px solid #3fb950;border-radius:10px;padding:20px;text-align:center;">
    <div style="color:#8b949e;font-size:13px;margin-bottom:6px;">🟢 Support — Κάτω Όριο</div>
    <div style="color:#3fb950;font-size:32px;font-weight:bold;">${pred['support']:,.2f}</div>
    <div style="color:#8b949e;font-size:12px;margin-top:6px;">Εδώ η τιμή συνήθως σταματά να πέφτει και ανακάμπτει</div>
    </div>""", unsafe_allow_html=True)
with sr2:
    st.markdown(f"""<div style="background:#2a0a0a;border:1px solid #f85149;border-radius:10px;padding:20px;text-align:center;">
    <div style="color:#8b949e;font-size:13px;margin-bottom:6px;">🔴 Resistance — Άνω Όριο</div>
    <div style="color:#f85149;font-size:32px;font-weight:bold;">${pred['resistance']:,.2f}</div>
    <div style="color:#8b949e;font-size:12px;margin-top:6px;">Εδώ η τιμή συνήθως σταματά να ανεβαίνει και πέφτει</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.plotly_chart(build_prediction_chart(df, pred), use_container_width=True)
st.markdown("<small style='color:#8b949e'>⚠️ Η πρόβλεψη βασίζεται σε Linear Regression ιστορικών τιμών. Δεν λαμβάνει υπόψη εξωτερικά γεγονότα. Χρησιμοποίησέ την ως ένδειξη τάσης.</small>",
            unsafe_allow_html=True)

# ── Signal History ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Ιστορικό Signals")
history = df[df["action"] != "HOLD"].tail(15)[["close","rsi","macd","score","action"]].copy()
history = history.iloc[::-1]
history.index = history.index.strftime("%d/%m %H:%M")
history.columns = ["Τιμή ($)","RSI","MACD","Score","Signal"]
history["Τιμή ($)"] = history["Τιμή ($)"].apply(lambda x: f"${float(x):,.2f}")
history["RSI"]      = history["RSI"].apply(lambda x: f"{float(x):.1f}")
history["MACD"]     = history["MACD"].apply(lambda x: f"{float(x):.4f}")
st.dataframe(history, use_container_width=True)

csv_data = history.reset_index().rename(columns={"index": "Ημερομηνία"})
csv_bytes = csv_data.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Κατέβασε Signals (CSV)",
    data=csv_bytes,
    file_name=f"{symbol}_signals_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
    mime="text/csv",
)

# ─── MULTI-CRYPTO SCREENER ────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🔍 Multi-Crypto Screener")
st.markdown("<small style='color:#8b949e'>Τρέχον signal για όλα τα cryptos με 1h timeframe.</small>",
            unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)


@st.cache_data(ttl=120)
def fetch_screener():
    results = []
    for sym in SYMBOLS:
        try:
            d = fetch_data(sym, "5d", "1h")
            d = add_indicators(d)
            d = generate_signals(d)
            last = d.iloc[-1]
            prev = d.iloc[-2]
            price     = float(last["close"])
            chg_pct   = (price - float(prev["close"])) / float(prev["close"]) * 100
            rsi_v     = float(last["rsi"])
            act       = last["action"]
            score_v   = int(last["score"])
            results.append({
                "Crypto":   SYMBOL_LABELS.get(sym, sym.replace("-USD", "")),
                "_price":   price,
                "_chg":     chg_pct,
                "_rsi":     rsi_v,
                "_action":  act,
                "_score":   score_v,
            })
        except Exception:
            pass
    return results


with st.spinner("Φορτώνω screener..."):
    screener_rows = fetch_screener()

if screener_rows:
    SIGNAL_ORDER = {"STRONG BUY": 0, "BUY": 1, "HOLD": 2, "SELL": 3, "STRONG SELL": 4}
    screener_rows.sort(key=lambda r: SIGNAL_ORDER.get(r["_action"], 2))

    sc_cols = st.columns(len(screener_rows))
    for col, r in zip(sc_cols, screener_rows):
        act    = r["_action"]
        color  = action_color(act)
        emoji  = SIGNAL_EMOJI.get(act, "")
        chg_c  = "#3fb950" if r["_chg"] >= 0 else "#f85149"
        chg_s  = f"+{r['_chg']:.2f}%" if r["_chg"] >= 0 else f"{r['_chg']:.2f}%"
        col.markdown(f"""
<div style="background:#161b22;border:1px solid {color};border-radius:10px;
            padding:12px 8px;text-align:center;">
  <div style="color:#e6edf3;font-size:14px;font-weight:bold;">{r['Crypto']}</div>
  <div style="color:#8b949e;font-size:11px;">${r['_price']:,.2f}</div>
  <div style="color:{chg_c};font-size:11px;">{chg_s}</div>
  <div style="color:{color};font-weight:bold;font-size:12px;margin-top:6px;">{emoji} {act}</div>
  <div style="color:#8b949e;font-size:10px;">RSI {r['_rsi']:.0f} | Score {r['_score']}</div>
</div>""", unsafe_allow_html=True)

# ─── BACKTESTING ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### ⚗️ Backtesting")
st.markdown(f"<small style='color:#8b949e'>Προσομοίωση BUY signals στο ιστορικό | TP: +{bt_tp}% | SL: -{bt_sl}%</small>",
            unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

trades = run_backtest(df, tp_pct=bt_tp/100, sl_pct=bt_sl/100)

if not trades:
    st.markdown("<div style='color:#8b949e;text-align:center;'>Δεν βρέθηκαν BUY signals στο ιστορικό.</div>",
                unsafe_allow_html=True)
else:
    wins        = sum(1 for t in trades if t["Αποτέλεσμα"] == "WIN")
    losses      = len(trades) - wins
    win_rate    = wins / len(trades) * 100
    avg_win     = np.mean([t["_pnl"] for t in trades if t["Αποτέλεσμα"] == "WIN"]) if wins  else 0
    avg_loss    = np.mean([t["_pnl"] for t in trades if t["Αποτέλεσμα"] == "LOSS"]) if losses else 0
    total_ret   = sum(t["_pnl"] for t in trades)
    expectancy  = (win_rate/100 * avg_win) + ((1 - win_rate/100) * avg_loss)

    bt1, bt2, bt3, bt4, bt5 = st.columns(5)
    bt1.metric("📊 Συνολικά Trades", len(trades))
    bt2.metric("✅ Wins",   f"{wins}",   f"{win_rate:.1f}%")
    bt3.metric("❌ Losses", f"{losses}", f"{100-win_rate:.1f}%")
    bt4.metric("💰 Avg Win / Loss", f"{avg_win:+.2f}% / {avg_loss:+.2f}%")
    bt5.metric("🎯 Expectancy / trade", f"{expectancy:+.2f}%",
               "Κερδοφόρο" if expectancy > 0 else "Ζημιογόνο")

    # Equity curve
    st.markdown("<br>", unsafe_allow_html=True)
    cumulative = [100.0]
    for t in trades:
        cumulative.append(cumulative[-1] * (1 + t["_pnl"] / 100))
    eq_color = "#3fb950" if cumulative[-1] >= cumulative[0] else "#f85149"
    fig_eq = go.Figure()
    fig_eq.add_trace(go.Scatter(
        y=cumulative, mode="lines+markers",
        line=dict(color=eq_color, width=2),
        marker=dict(size=4),
        fill="tozeroy",
        fillcolor=f"rgba({'63,185,80' if cumulative[-1]>=100 else '248,81,73'},0.1)",
        name="Equity",
        hovertemplate="Trade %{x}<br>$%{y:.2f}<extra></extra>",
    ))
    fig_eq.add_hline(y=100, line=dict(color="#21262d", dash="dot", width=1))
    fig_eq.update_layout(
        height=220, paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
        margin=dict(l=10, r=10, t=20, b=10),
        font=dict(color="#e6edf3"),
        xaxis=dict(title="Trade #", gridcolor="#21262d", zeroline=False),
        yaxis=dict(title="Κεφάλαιο ($)", gridcolor="#21262d", zeroline=False,
                   tickprefix="$"),
        showlegend=False,
    )
    st.plotly_chart(fig_eq, use_container_width=True)

    # Trade log
    with st.expander("📋 Αναλυτικό Trade Log"):
        bt_df = pd.DataFrame([{k: v for k, v in t.items() if k != "_pnl"} for t in trades])
        st.dataframe(bt_df, use_container_width=True)

# ─── FEAR & GREED INDEX ───────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 😱 Fear & Greed Index")
st.markdown("<small style='color:#8b949e'>Μετράει αν η αγορά είναι σε πανικό (Fear) ή ευφορία (Greed). Πηγή: alternative.me</small>",
            unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

fng = fetch_fear_greed()
fng_val   = fng["value"]
fng_label = fng["label"]
fng_col, fng_desc = fng_color(fng_val)

fg1, fg2 = st.columns([1, 1])

with fg1:
    st.plotly_chart(fng_gauge(fng_val), use_container_width=True)
    st.markdown(f"""
<div style="text-align:center; margin-top:-20px;">
  <span style="font-size:28px; font-weight:bold; color:{fng_col};">{fng_label}</span><br>
  <span style="color:#8b949e; font-size:13px;">Τρέχουσα κατάσταση αγοράς</span>
</div>""", unsafe_allow_html=True)

with fg2:
    st.markdown("**Τι σημαίνει κάθε επίπεδο:**")
    for rng, lbl, clr, desc in [
        ("0–25",  "Extreme Fear", "#f85149", "Ο κόσμος πουλά από πανικό → Καλή ευκαιρία αγοράς"),
        ("26–45", "Fear",         "#ffa657", "Αρνητική διάθεση αγοράς → Προσοχή"),
        ("46–55", "Neutral",      "#d29922", "Ουδέτερη αγορά → Περίμενε signal"),
        ("56–75", "Greed",        "#26c941", "Θετική διάθεση → Καλό για long positions"),
        ("76–100","Extreme Greed","#3fb950", "Ευφορία → Πρόσεχε, πιθανή διόρθωση"),
    ]:
        st.markdown(f"""
<div style="background:#161b22;border-left:3px solid {clr};padding:8px 12px;border-radius:4px;margin-bottom:6px;">
  <span style="color:{clr};font-weight:bold;">{rng} — {lbl}</span><br>
  <span style="color:#8b949e;font-size:12px;">{desc}</span>
</div>""", unsafe_allow_html=True)

    # Ιστορικό 10 ημερών
    if fng["history"]:
        st.markdown("<br>**Τελευταίες 10 μέρες:**", unsafe_allow_html=True)
        hist_vals  = [h["value"] for h in fng["history"]][::-1]
        hist_dates = [h["date"].strftime("%d/%m") for h in fng["history"]][::-1]
        hist_colors= [fng_color(v)[0] for v in hist_vals]
        fig_fng = go.Figure(go.Bar(
            x=hist_dates, y=hist_vals,
            marker_color=hist_colors,
            text=hist_vals, textposition="outside",
            textfont=dict(color="#e6edf3", size=11)
        ))
        fig_fng.update_layout(
            height=200, paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
            margin=dict(l=0,r=0,t=10,b=0), showlegend=False,
            yaxis=dict(range=[0,110], gridcolor="#21262d", zeroline=False),
            xaxis=dict(gridcolor="#21262d")
        )
        fig_fng.add_hline(y=50, line=dict(color="#21262d", dash="dot", width=1))
        st.plotly_chart(fig_fng, use_container_width=True)

# ─── HEATMAP ΑΠΟΔΟΣΕΩΝ ───────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🗓️ Heatmap Ημερήσιων Αποδόσεων")
st.markdown(f"<small style='color:#8b949e'>Κάθε τετράγωνο = 1 μέρα. 🟢 Κέρδος · 🔴 Ζημιά. Τελευταίοι 12 μήνες ({symbol}).</small>",
            unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

with st.spinner("Φορτώνω heatmap δεδομένα..."):
    hmap_df = fetch_heatmap_data(symbol)

if hmap_df is not None and not hmap_df.empty:
    hm1, hm2, hm3, hm4 = st.columns(4)
    pos_days  = int((hmap_df["ret"] > 0).sum())
    neg_days  = int((hmap_df["ret"] < 0).sum())
    best_day  = float(hmap_df["ret"].max())
    worst_day = float(hmap_df["ret"].min())
    hm1.metric("✅ Ανοδικές μέρες", f"{pos_days}",  f"{pos_days/(pos_days+neg_days)*100:.0f}%")
    hm2.metric("❌ Πτωτικές μέρες", f"{neg_days}",  f"{neg_days/(pos_days+neg_days)*100:.0f}%")
    hm3.metric("🚀 Καλύτερη μέρα",  f"+{best_day:.2f}%")
    hm4.metric("💥 Χειρότερη μέρα", f"{worst_day:.2f}%")
    st.markdown("<br>", unsafe_allow_html=True)
    st.plotly_chart(build_heatmap_chart(hmap_df), use_container_width=True)

    # Monthly summary bar
    hmap_df["month"] = pd.to_datetime(hmap_df.index).to_period("M").astype(str)
    monthly = hmap_df.groupby("month")["ret"].sum().reset_index()
    monthly.columns = ["Μήνας", "Απόδοση %"]
    m_colors = ["#3fb950" if v >= 0 else "#f85149" for v in monthly["Απόδοση %"]]
    fig_m = go.Figure(go.Bar(
        x=monthly["Μήνας"], y=monthly["Απόδοση %"],
        marker_color=m_colors,
        text=[f"{v:+.1f}%" for v in monthly["Απόδοση %"]],
        textposition="outside", textfont=dict(color="#e6edf3", size=10),
    ))
    fig_m.update_layout(
        height=240, paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
        margin=dict(l=10, r=10, t=10, b=40),
        font=dict(color="#e6edf3"),
        xaxis=dict(gridcolor="#21262d", tickangle=-45),
        yaxis=dict(gridcolor="#21262d", zeroline=True, zerolinecolor="#21262d",
                   ticksuffix="%"),
        showlegend=False,
    )
    fig_m.add_hline(y=0, line=dict(color="#21262d", width=1))
    st.plotly_chart(fig_m, use_container_width=True)
else:
    st.markdown("<div style='color:#8b949e;text-align:center;'>Δεν φορτώθηκαν δεδομένα heatmap.</div>",
                unsafe_allow_html=True)

# ─── PORTFOLIO TRACKER ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 💼 Portfolio Tracker")
st.markdown("<small style='color:#8b949e'>Παρακολούθησε τις επενδύσεις σου σε real-time.</small>",
            unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Αποθήκευση holdings στο session state
if "holdings" not in st.session_state:
    st.session_state.holdings = []

# ── Φόρμα προσθήκης θέσης ─────────────────────────────────────────────────────
with st.expander("➕ Πρόσθεσε νέα θέση", expanded=len(st.session_state.holdings) == 0):
    fa, fb, fc, fd = st.columns([2, 2, 2, 1])
    with fa:
        new_symbol = st.selectbox("Crypto", SYMBOLS, key="new_sym",
                                   format_func=lambda s: SYMBOL_LABELS.get(s, s))
    with fb:
        new_amount = st.number_input("Ποσότητα", min_value=0.000001, value=0.01,
                                     format="%.6f", key="new_amt")
    with fc:
        new_price  = st.number_input("Τιμή Αγοράς ($)", min_value=0.01, value=1000.0,
                                     format="%.2f", key="new_price")
    with fd:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Πρόσθεσε"):
            st.session_state.holdings.append({
                "symbol":    new_symbol,
                "amount":    new_amount,
                "buy_price": new_price,
            })
            st.rerun()

# ── Εμφάνιση Portfolio ────────────────────────────────────────────────────────
if not st.session_state.holdings:
    st.markdown("""
<div style="background:#161b22;border:1px dashed #21262d;border-radius:10px;padding:30px;text-align:center;">
  <span style="color:#8b949e;font-size:16px;">Δεν έχεις προσθέσει θέσεις ακόμα.<br>Χρησιμοποίησε τη φόρμα πάνω για να ξεκινήσεις.</span>
</div>""", unsafe_allow_html=True)
else:
    with st.spinner("Φορτώνω live τιμές..."):
        rows, total_inv, total_cur, total_pnl, total_pnl_pct = portfolio_summary(st.session_state.holdings)

    if rows:
        # Summary cards
        pt1, pt2, pt3, pt4 = st.columns(4)
        pt1.metric("💰 Επενδύθηκαν",   f"${total_inv:,.2f}")
        pt2.metric("📊 Αξία Τώρα",     f"${total_cur:,.2f}")
        pt3.metric("📈 P&L ($)",        f"{'+'if total_pnl>=0 else ''}{total_pnl:,.2f}",
                   f"{total_pnl_pct:+.2f}%")
        profit_color = "#3fb950" if total_pnl >= 0 else "#f85149"
        pt4.metric("🎯 Απόδοση",        f"{total_pnl_pct:+.2f}%")

        st.markdown("<br>", unsafe_allow_html=True)

        # Portfolio pie chart + table
        pc1, pc2 = st.columns([1, 2])

        with pc1:
            labels = [r["Crypto"] for r in rows]
            values = [float(r["Αξία Τώρα"].replace("$","").replace(",","")) for r in rows]
            colors = ["#3fb950","#58a6ff","#bc8cff","#ffa657","#f85149",
                      "#d29922","#26c941","#388bfd","#ff4040","#e6edf3"]
            fig_pie = go.Figure(go.Pie(
                labels=labels, values=values,
                marker=dict(colors=colors[:len(labels)], line=dict(color="#0d1117", width=2)),
                textfont=dict(color="#e6edf3", size=12),
                hole=0.4
            ))
            fig_pie.update_layout(
                height=280, paper_bgcolor="#0d1117",
                margin=dict(l=0,r=0,t=10,b=0),
                legend=dict(bgcolor="#161b22", bordercolor="#21262d",
                            font=dict(color="#e6edf3", size=11)),
                showlegend=True
            )
            fig_pie.add_annotation(text=f"${total_cur:,.0f}", x=0.5, y=0.5,
                                   font=dict(size=14, color="#e6edf3"), showarrow=False)
            st.plotly_chart(fig_pie, use_container_width=True)

        with pc2:
            # Πίνακας holdings
            display_rows = []
            for r in rows:
                pnl_val = r["_pnl"]
                emoji   = "🟢" if pnl_val >= 0 else "🔴"
                display_rows.append({
                    "": emoji,
                    "Crypto":      r["Crypto"],
                    "Ποσότητα":    r["Ποσότητα"],
                    "Αγορά":       r["Τιμή Αγοράς"],
                    "Τώρα":        r["Τιμή Τώρα"],
                    "Επενδύθηκαν": r["Επενδύθηκαν"],
                    "Αξία Τώρα":   r["Αξία Τώρα"],
                    "P&L ($)":     r["P&L ($)"],
                    "P&L (%)":     r["P&L (%)"],
                })
            st.dataframe(pd.DataFrame(display_rows), use_container_width=True, height=260)

        # Κουμπί διαγραφής
        st.markdown("<br>", unsafe_allow_html=True)
        del_col1, del_col2 = st.columns([3, 1])
        with del_col2:
            del_idx = st.selectbox("Διέγραψε θέση #",
                                   range(1, len(st.session_state.holdings) + 1),
                                   format_func=lambda i: f"#{i} {st.session_state.holdings[i-1]['symbol']}")
            if st.button("🗑️ Διέγραψε"):
                st.session_state.holdings.pop(del_idx - 1)
                st.rerun()

# ─── CONVERTER ───────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 💱 Crypto Converter")
st.markdown("<small style='color:#8b949e'>Μετάτρεψε οποιοδήποτε ποσό σε USD, EUR ή crypto.</small>",
            unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

@st.cache_data(ttl=60)
def fetch_all_prices():
    prices = {}
    for sym in SYMBOLS:
        try:
            t = yf.Ticker(sym)
            prices[sym] = float(t.fast_info["last_price"])
        except Exception:
            prices[sym] = None
    return prices

with st.spinner("Φορτώνω τιμές..."):
    all_prices = fetch_all_prices()

FIAT = ["USD", "EUR"]
conv_options = SYMBOLS + FIAT

col_from, col_arrow, col_to = st.columns([5, 1, 5])

with col_from:
    from_amount = st.number_input("Ποσό", min_value=0.0, value=1.0,
                                  format="%.6f", key="conv_amount")
    from_currency = st.selectbox("Από", conv_options, index=0,
                                 format_func=lambda s: SYMBOL_LABELS.get(s, s),
                                 key="conv_from")

with col_arrow:
    st.markdown("<div style='text-align:center;font-size:32px;margin-top:40px;color:#58a6ff;'>→</div>",
                unsafe_allow_html=True)

with col_to:
    to_currency = st.selectbox("Σε", conv_options, index=len(SYMBOLS),
                               format_func=lambda s: SYMBOL_LABELS.get(s, s),
                               key="conv_to")

def get_usd_value(currency, amount, prices, eur_rate):
    """Μετατρέπει οποιοδήποτε νόμισμα σε USD."""
    if currency == "USD":
        return amount
    if currency == "EUR":
        return amount * eur_rate
    p = prices.get(currency)
    return amount * p if p else None

def usd_to_currency(usd_val, currency, prices, eur_rate):
    """Μετατρέπει USD στο target νόμισμα."""
    if currency == "USD":
        return usd_val
    if currency == "EUR":
        return usd_val / eur_rate
    p = prices.get(currency)
    return usd_val / p if p else None

usd_val = get_usd_value(from_currency, from_amount, all_prices, eur_rate)

if usd_val is not None:
    result = usd_to_currency(usd_val, to_currency, all_prices, eur_rate)
    if result is not None:
        to_label   = SYMBOL_LABELS.get(to_currency, to_currency)
        from_label = SYMBOL_LABELS.get(from_currency, from_currency)
        sym_to     = "€" if to_currency == "EUR" else ("$" if to_currency == "USD" else "")
        fmt        = f"{result:,.8f}" if to_currency not in FIAT and result < 1 else f"{result:,.4f}" if to_currency not in FIAT else f"{result:,.2f}"

        st.markdown(f"""
<div style="background:#161b22;border:1px solid #3fb950;border-radius:12px;
            padding:24px;text-align:center;margin-top:10px;">
  <div style="color:#8b949e;font-size:14px;">{from_amount:,.6f} {from_label} =</div>
  <div style="color:#3fb950;font-size:42px;font-weight:bold;margin:8px 0;">
    {sym_to}{fmt} <span style="font-size:22px;">{to_label}</span>
  </div>
  <div style="color:#8b949e;font-size:12px;">≈ ${usd_val:,.2f} USD &nbsp;·&nbsp; ≈ €{usd_val/eur_rate:,.2f} EUR &nbsp;·&nbsp; Rate: 1€ = ${eur_rate:.4f}</div>
</div>""", unsafe_allow_html=True)

        # Πίνακας με όλα τα νομίσματα ταυτόχρονα
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<small style='color:#8b949e'>{from_amount:,.4f} {from_label} σε όλα τα νομίσματα:</small>",
                    unsafe_allow_html=True)

        rows_conv = []
        for sym in SYMBOLS:
            p = all_prices.get(sym)
            if p is None:
                continue
            equiv = usd_val / p
            rows_conv.append({
                "Crypto": SYMBOL_LABELS.get(sym, sym),
                "Ποσότητα": f"{equiv:.6f}" if equiv < 1 else f"{equiv:.4f}",
                "Τιμή (USD)": f"${p:,.2f}",
                "Τιμή (EUR)": f"€{p/eur_rate:,.2f}",
            })
        rows_conv.append({"Crypto": "USD 🇺🇸", "Ποσότητα": f"${usd_val:,.2f}", "Τιμή (USD)": "—", "Τιμή (EUR)": "—"})
        rows_conv.append({"Crypto": "EUR 🇪🇺", "Ποσότητα": f"€{usd_val/eur_rate:,.2f}", "Τιμή (USD)": "—", "Τιμή (EUR)": "—"})

        st.dataframe(pd.DataFrame(rows_conv), use_container_width=True, hide_index=True)
    else:
        st.warning("Δεν βρέθηκε τιμή για αυτό το νόμισμα.")

# ─── NEWS FEED ───────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📰 Crypto News")
st.markdown("<small style='color:#8b949e'>Τελευταία νέα από CoinTelegraph & CoinDesk. Σχετικά με το επιλεγμένο crypto εμφανίζονται πρώτα.</small>",
            unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

with st.spinner("Φορτώνω news..."):
    articles = fetch_news(symbol)

if not articles:
    st.markdown("<div style='color:#8b949e;text-align:center;'>Δεν φορτώθηκαν νέα αυτή τη στιγμή.</div>",
                unsafe_allow_html=True)
else:
    coin_name = SYMBOL_LABELS.get(symbol, symbol.replace("-USD", "")).split(" ")[0]
    for art in articles:
        border_color = "#3fb950" if art["relevant"] else "#21262d"
        tag = f"<span style='background:#0d2818;color:#3fb950;font-size:10px;padding:2px 6px;border-radius:4px;'>{coin_name}</span> " if art["relevant"] else ""
        source_color = "#58a6ff" if art["source"] == "CoinTelegraph" else "#bc8cff"
        link_html = f'<a href="{art["link"]}" target="_blank" style="color:#e6edf3;text-decoration:none;font-weight:bold;">{art["title"]}</a>' if art["link"] else f'<span style="color:#e6edf3;font-weight:bold;">{art["title"]}</span>'
        st.markdown(f"""
<div style="background:#161b22;border-left:3px solid {border_color};border-radius:6px;
            padding:10px 14px;margin-bottom:8px;">
  {tag}<span style="color:{source_color};font-size:11px;">{art['source']}</span>
  <span style="color:#8b949e;font-size:11px;"> · {art['date']}</span><br>
  {link_html}
</div>""", unsafe_allow_html=True)

# ── Auto Refresh ───────────────────────────────────────────────────────────────
if auto_refresh:
    time.sleep(60)
    st.cache_data.clear()
    st.rerun()
if refresh_btn:
    st.cache_data.clear()
    st.rerun()
