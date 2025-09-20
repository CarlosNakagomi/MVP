
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="Overview — Venue Intelligence", page_icon="🧭", layout="wide")

@st.cache_data
def load_all():
    venues = pd.read_csv("data/venues.csv")
    events = pd.read_csv("data/events.csv", parse_dates=["start_ts","end_ts"])
    tickets = pd.read_csv("data/tickets.csv", parse_dates=["sold_ts"], keep_default_na=False)
    stripe = pd.read_csv("data/stripe_transactions.csv", parse_dates=["created_ts"])
    venues["region_path"] = venues["city"] + " > " + venues["borough"] + " > " + venues["neighborhood"]
    return venues, events, tickets, stripe

venues, events, tickets, stripe = load_all()

st.title("🧭 Overview")
st.caption("Visão geral rápida dos principais KPIs e destaques.")

# Time window selector
min_date = min(events["start_ts"].min().date(), stripe["created_ts"].min().date())
max_date = max(events["start_ts"].max().date(), stripe["created_ts"].max().date())
period = st.selectbox("Janela de tempo", ["Últimos 30 dias","Últimos 90 dias","YTD","Tudo"])
if period == "Últimos 30 dias":
    start = pd.to_datetime(max_date) - pd.Timedelta(days=30)
elif period == "Últimos 90 dias":
    start = pd.to_datetime(max_date) - pd.Timedelta(days=90)
elif period == "YTD":
    start = pd.to_datetime(f"{datetime.now().year}-01-01")
else:
    start = pd.to_datetime(min_date)
end = pd.to_datetime(max_date) + pd.Timedelta(days=1)

stripe_f = stripe[(stripe["created_ts"]>=start) & (stripe["created_ts"]<end)]
events_f = events[(events["start_ts"]>=start) & (events["start_ts"]<end)]
tickets_f = tickets.merge(events_f[["event_id","venue_id","start_ts"]], on="event_id", how="inner")

net_revenue = stripe_f.loc[stripe_f["status"]=="captured","net_amount"].sum() + stripe_f.loc[stripe_f["is_refund"]==1,"net_amount"].sum()
tickets_sold = len(tickets_f)
checkins = (tickets_f["checkin_ts"].str.len()>0).sum()
cancellations = (tickets_f["cancel_ts"].str.len()>0).sum()

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Net Revenue", f"${net_revenue:,.0f}")
c2.metric("Tickets Sold", f"{tickets_sold:,d}")
c3.metric("Attendance", f"{checkins:,d}")
conv = (checkins/tickets_sold) if tickets_sold>0 else 0
c4.metric("Check-in Rate", f"{100*conv:,.1f}%")
c5.metric("Cancellations", f"{cancellations:,d}")

st.markdown("### Destaques")
top_events = tickets_f.groupby("event_id").agg(
    sold=("order_id","count"),
    checkins=("checkin_ts", lambda s: (s.str.len()>0).sum())
).reset_index().merge(events[["event_id","event_name","venue_id"]], on="event_id", how="left").merge(
    venues[["venue_id","venue_name","city","borough","neighborhood"]], on="venue_id", how="left"
)
top_events["checkin_rate"] = (top_events["checkins"]/top_events["sold"]).round(2)
st.dataframe(top_events.sort_values("sold", ascending=False).head(20), use_container_width=True)
