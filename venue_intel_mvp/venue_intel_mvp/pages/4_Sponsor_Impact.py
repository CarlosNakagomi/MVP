
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Sponsor Impact — Venue Intelligence", page_icon="🤝", layout="wide")

@st.cache_data
def load_all():
    venues = pd.read_csv("data/venues.csv")
    events = pd.read_csv("data/events.csv", parse_dates=["start_ts","end_ts"])
    tickets = pd.read_csv("data/tickets.csv", parse_dates=["sold_ts"], keep_default_na=False)
    stripe = pd.read_csv("data/stripe_transactions.csv", parse_dates=["created_ts"])
    return venues, events, tickets, stripe

venues, events, tickets, stripe = load_all()

tickets["checked_in"] = (tickets["checkin_ts"].str.len()>0).astype(int)
events["date"] = events["start_ts"].dt.date

# Aggregate per event
ev_tix = tickets.groupby("event_id", as_index=False).agg(
    sold=("order_id","count"),
    checkins=("checked_in","sum"),
    cancellations=("cancel_ts", lambda s: (s.str.len()>0).sum())
)
ev_rev = stripe.groupby("event_id", as_index=False)["net_amount"].sum()
ev = events.merge(ev_tix, on="event_id", how="left").merge(ev_rev, on="event_id", how="left").fillna({"sold":0,"checkins":0,"cancellations":0,"net_amount":0.0})
ev["checkin_rate"] = np.where(ev["sold"]>0, ev["checkins"]/ev["sold"], 0.0)

st.title("🤝 Sponsor Impact")
st.caption("Comparativo entre eventos patrocinados vs. não patrocinados.")

grp = ev.groupby("is_sponsored", as_index=False).agg(
    avg_event_rev=("net_amount","mean"),
    avg_checkin_rate=("checkin_rate","mean"),
    events=("event_id","count")
)
grp["label"] = grp["is_sponsored"].map({True:"Sponsored", False:"Non-sponsored"})
st.dataframe(grp[["label","events","avg_event_rev","avg_checkin_rate"]], use_container_width=True)

fig = px.bar(grp, x="label", y="avg_event_rev", title="Avg Event Revenue (Sponsored vs Non)")
st.plotly_chart(fig, use_container_width=True)

fig2 = px.bar(grp, x="label", y="avg_checkin_rate", title="Avg Check-in Rate (Sponsored vs Non)")
st.plotly_chart(fig2, use_container_width=True)
