
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Trends — Venue Intelligence", page_icon="📈", layout="wide")

@st.cache_data
def load_all():
    events = pd.read_csv("data/events.csv", parse_dates=["start_ts","end_ts"])
    tickets = pd.read_csv("data/tickets.csv", parse_dates=["sold_ts"], keep_default_na=False)
    stripe = pd.read_csv("data/stripe_transactions.csv", parse_dates=["created_ts"])
    return events, tickets, stripe

events, tickets, stripe = load_all()

# Daily revenue
rev = stripe.copy()
rev["date"] = rev["created_ts"].dt.date
rev_captured = rev[rev["status"]=="captured"].groupby("date", as_index=False)["net_amount"].sum()
rev_refunds = rev[rev["is_refund"]==1].groupby("date", as_index=False)["net_amount"].sum()
rev_daily = rev_captured.merge(rev_refunds, on="date", how="outer", suffixes=("_captured","_refunds")).fillna(0.0)
rev_daily["net_revenue"] = rev_daily["net_amount_captured"] + rev_daily["net_amount_refunds"]

# Attendance per day
events["date"] = events["start_ts"].dt.date
tickets["checked_in"] = (tickets["checkin_ts"].str.len()>0).astype(int)
att = tickets.merge(events[["event_id","date"]], on="event_id", how="left")
att_daily = att.groupby("date", as_index=False).agg(
    tickets_sold=("order_id","count"),
    checkins=("checked_in","sum"),
    cancellations=("cancel_ts", lambda s: (s.str.len()>0).sum())
)

st.title("📈 Trends")
st.caption("Receita e presença ao longo do tempo, com picos e sazonalidade.")

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(rev_daily, x="date", y="net_revenue", title="Net Revenue (Daily)")
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig2 = px.line(att_daily, x="date", y=["tickets_sold","checkins"], markers=True, title="Tickets vs. Check-ins (Daily)")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("### Peak Days (Top 10 por Receita)")
st.dataframe(rev_daily.sort_values("net_revenue", ascending=False).head(10), use_container_width=True)
