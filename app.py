# ==============================
# 📈 MARKET MAVERICKS — Admin Dashboard (2025)
# Single CSV Version (Lag-Free)
# ==============================

import streamlit as st
import pandas as pd
from pathlib import Path

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="Market Mavericks — Dashboard", layout="wide")

DATA_DIR = Path("MARKET_MAVERICKS")
MASTER_CSV = "market_master.csv"
TEAMS_CSV = "teams.csv"

# -------------------------
# STYLE (dark trading-floor)
# -------------------------
st.markdown("""
    <style>
    body { background-color: #0b0f14; color: #e6eef8; }
    .main > .block-container { padding: 1rem 1.5rem; }
    .title { font-size:28px; font-weight:700; color:#fff; }
    .card { background-color:#0f1720; padding:12px; border-radius:8px; box-shadow: 0 2px 6px rgba(0,0,0,0.6); }
    .small { font-size:13px; color:#9fb0c8; }
    </style>
""", unsafe_allow_html=True)

# -------------------------
# LOAD CSV DATA
# -------------------------
def clean_master_csv(path):
    if not Path(path).exists():
        st.error(f"❌ Missing file: {path}")
        st.stop()
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    df["company"] = df["company"].astype(str).str.strip()
    return df

def clean_teams_csv(path):
    if not Path(path).exists():
        st.error(f"❌ Missing file: {path}")
        st.stop()
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    return df

master_df = clean_master_csv(MASTER_CSV)
teams_df = clean_teams_csv(TEAMS_CSV)

if master_df.empty or teams_df.empty:
    st.error("❌ CSV files are empty or invalid.")
    st.stop()

st.success("✅ Loaded market and team data successfully!")

# -------------------------
# SESSION STATE
# -------------------------
if "teams" not in st.session_state:
    st.session_state.teams = {
        row["team_id"]: {"cash": int(row["cash"]), "holdings": {}} for _, row in teams_df.iterrows()
    }

if "current_round" not in st.session_state:
    st.session_state.current_round = 0

if "processed_rounds" not in st.session_state:
    st.session_state.processed_rounds = set()

if "history" not in st.session_state:
    st.session_state.history = []

if "pending_trades" not in st.session_state:
    st.session_state.pending_trades = []

# -------------------------
# HELPER FUNCTIONS
# -------------------------
def get_price_for_round(company, rnd):
    company = company.strip()
    if rnd == 0:
        return int(master_df.loc[master_df["company"] == company, "base_price"].values[0])
    col = f"r{rnd}"
    if col not in master_df.columns:
        st.error(f"⚠️ Missing column for round {rnd}")
        return 0
    row = master_df.loc[master_df["company"] == company, col]
    if row.empty:
        st.error(f"⚠️ No price for {company} in round {rnd}")
        return 0
    return int(row.values[0])

def portfolio_value(team_id):
    team = st.session_state.teams[team_id]
    total = team["cash"]
    for comp, qty in team["holdings"].items():
        price = get_price_for_round(comp, st.session_state.current_round)
        total += qty * price
    return total

def apply_trade(team_id, company, action, qty, price):
    team = st.session_state.teams[team_id]
    holdings = team["holdings"]
    holdings.setdefault(company, 0)
    qty = int(qty)

    if action == "Buy":
        cost = price * qty
        if cost > team["cash"]:
            return False, f"{team_id} doesn't have enough cash."
        team["cash"] -= cost
        holdings[company] += qty
        return True, f"{team_id} bought {qty} of {company} @ ₹{price}"

    elif action == "Sell":
        if qty > holdings.get(company, 0):
            return False, f"{team_id} doesn't own {qty} shares of {company}"
        proceeds = price * qty
        team["cash"] += proceeds
        holdings[company] -= qty
        return True, f"{team_id} sold {qty} of {company} @ ₹{price}"

    return True, "Hold - no action"

def recalculate_all_team_values():
    cur_round = st.session_state.current_round
    for team_id, team_data in st.session_state.teams.items():
        total_share_value = 0
        for comp, qty in team_data["holdings"].items():
            cur_price = get_price_for_round(comp, cur_round)
            total_share_value += qty * cur_price
        team_data["total_share_value"] = total_share_value
        team_data["total_portfolio_value"] = team_data["cash"] + total_share_value

def record_snapshot(rnd):
    snap = {tid: portfolio_value(tid) for tid in st.session_state.teams.keys()}
    st.session_state.history.append((rnd, snap))

# -------------------------
# UI LAYOUT
# -------------------------
st.markdown('<div class="title">📊 Market Mavericks — Admin Dashboard</div>', unsafe_allow_html=True)
left, center, right = st.columns([2, 3, 2])

# -------------------------
# LEFT PANEL (Admin Controls)
# -------------------------
with left:
    st.markdown('<div class="card"><div class="small">ADMIN CONTROLS</div></div>', unsafe_allow_html=True)
    selected_round = st.selectbox("Select Round", list(range(0, 8)), index=st.session_state.current_round)
    if st.button("Set Current Round"):
        st.session_state.current_round = selected_round
        st.success(f"✅ Round set to {selected_round}")

    st.markdown("---")
    st.markdown("### Pending Trades")
    if st.session_state.pending_trades:
        df = pd.DataFrame(st.session_state.pending_trades)
        st.dataframe(df, height=200)
        if st.button("Clear Pending Trades"):
            st.session_state.pending_trades = []
    else:
        st.write("No trades yet.")

    st.markdown("---")
    with st.form("add_trade_form", clear_on_submit=True):
        t_team = st.selectbox("Team", list(st.session_state.teams.keys()))
        t_company = st.selectbox("Company", master_df["company"])
        t_action = st.selectbox("Action", ["Buy", "Sell", "Hold"])
        t_qty = st.number_input("Quantity", min_value=1, value=10, step=1)
        submitted = st.form_submit_button("Add Trade")
        if submitted:
            st.session_state.pending_trades.append({
                "team_id": t_team, "company": t_company, "action": t_action, "qty": int(t_qty)
            })
            st.success(f"Added: {t_team} {t_action} {t_qty} {t_company}")

    st.markdown("---")
    if st.button("Process Round Trades"):
        rnd = st.session_state.current_round
        if rnd == 0:
            st.warning("⚠️ Round 0 is base round.")
        elif not st.session_state.pending_trades:
            st.error("No trades to process.")
        else:
            results = []
            for trade in st.session_state.pending_trades:
                team_id = trade["team_id"]
                comp = trade["company"]
                act = trade["action"]
                qty = int(trade["qty"])
                price = get_price_for_round(comp, rnd)
                ok, msg = apply_trade(team_id, comp, act, qty, price)
                results.append((ok, msg))

            for ok, msg in results:
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

            st.session_state.pending_trades = []
            st.session_state.processed_rounds.add(rnd)
            recalculate_all_team_values()
            record_snapshot(rnd)
            st.success(f"✅ All trades processed for round {rnd}")
            # Auto move to next round
            if st.session_state.current_round < 7:
                st.session_state.current_round += 1
                st.info(f"➡️ Moved to next round: {st.session_state.current_round}")

# -------------------------
# CENTER PANEL (Market Board)
# -------------------------
with center:
    st.markdown('<div class="card"><div class="small">MARKET BOARD</div></div>', unsafe_allow_html=True)
    st.write(f"**Round {st.session_state.current_round}** Market Status")

    prev_r = max(0, st.session_state.current_round - 1)
    data = []
    for _, r in master_df.iterrows():
        comp = r["company"]
        prev_p = get_price_for_round(comp, prev_r)
        cur_p = get_price_for_round(comp, st.session_state.current_round)
        change = round(((cur_p - prev_p) / prev_p) * 100, 2) if prev_p else 0
        data.append({"Company": comp, "Prev": prev_p, "Now": cur_p, "Change%": change})

    df = pd.DataFrame(data)
    styled = df.style.format({"Prev": "₹{:,}", "Now": "₹{:,}", "Change%": "{:+.2f}%"}).map(
        lambda v: "color:#2ecc71;font-weight:600;" if isinstance(v, (int,float)) and v > 0 else
                  "color:#ff5c5c;font-weight:600;" if isinstance(v, (int,float)) and v < 0 else "",
        subset=["Change%"]
    )
    st.dataframe(styled, height=420)

# -------------------------
# RIGHT PANEL (Leaderboard)
# -------------------------
with right:
    st.markdown('<div class="card"><div class="small">LEADERBOARD</div></div>', unsafe_allow_html=True)
    recalculate_all_team_values()
    leaderboard = []
    for tid, team_data in st.session_state.teams.items():
        leaderboard.append({
            "Team": tid,
            "Cash": team_data["cash"],
            "Share Value": team_data.get("total_share_value", 0),
            "Total Portfolio": team_data.get("total_portfolio_value", 0),
        })
    df_leader = pd.DataFrame(leaderboard).sort_values("Total Portfolio", ascending=False)
    df_leader["Cash"] = df_leader["Cash"].map("₹{:,.0f}".format)
    df_leader["Share Value"] = df_leader["Share Value"].map("₹{:,.0f}".format)
    df_leader["Total Portfolio"] = df_leader["Total Portfolio"].map("₹{:,.0f}".format)
    st.table(df_leader.reset_index(drop=True))

    # Optional: Highlight top 3
    st.markdown("""
        <style>
        tbody tr:nth-child(1) {background-color: #ffd70033 !important;}
        tbody tr:nth-child(2) {background-color: #c0c0c033 !important;}
        tbody tr:nth-child(3) {background-color: #cd7f3233 !important;}
        </style>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div class="card"><div class="small">TEAM DETAILS</div></div>', unsafe_allow_html=True)
    sel_team = st.selectbox("View team portfolio", list(st.session_state.teams.keys()))
    t = st.session_state.teams[sel_team]
    st.write(f"💰 **Cash:** ₹{t['cash']:,}")
    if t["holdings"]:
        df_hold = pd.DataFrame([
            {
                "Company": c,
                "Qty": q,
                "Price": get_price_for_round(c, st.session_state.current_round),
                "Value": q * get_price_for_round(c, st.session_state.current_round),
            }
            for c, q in t["holdings"].items() if q > 0
        ])
        df_hold["Value"] = df_hold["Value"].map("₹{:,.0f}".format)
        df_hold["Price"] = df_hold["Price"].map("₹{:,.0f}".format)
        st.table(df_hold)
    else:
        st.write("No holdings yet.")

# -------------------------
# HISTORY / CHARTS
# -------------------------
st.markdown("---")
st.markdown('<div class="card"><div class="small">PERFORMANCE OVER ROUNDS</div></div>', unsafe_allow_html=True)
if st.session_state.history:
    hist_data = []
    for rnd, snap in st.session_state.history:
        row = {"Round": rnd}
        row.update(snap)
        hist_data.append(row)
    hist_df = pd.DataFrame(hist_data).set_index("Round")
    st.line_chart(hist_df)
    st.dataframe(hist_df.style.format("₹{:,.0f}".format), height=250)
else:
    st.write("No rounds processed yet.")

st.markdown("---")
st.info("Tip: Admin enters trades for each round. App auto-calculates values & updates leaderboard instantly.")
