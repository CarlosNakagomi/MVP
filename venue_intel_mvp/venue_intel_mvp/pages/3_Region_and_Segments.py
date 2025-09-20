
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Region & Segments — Venue Intelligence", page_icon="🗺️", layout="wide")

@st.cache_data
def load_all():
    venues = pd.read_csv("data/venues.csv")
    events = pd.read_csv("data/events.csv", parse_dates=["start_ts","end_ts"])
    tickets = pd.read_csv("data/tickets.csv", parse_dates=["sold_ts"], keep_default_na=False)
    stripe = pd.read_csv("data/stripe_transactions.csv", parse_dates=["created_ts"])
    venues["region_path"] = venues["city"] + " > " + venues["borough"] + " > " + venues["neighborhood"]
    return venues, events, tickets, stripe

venues, events, tickets, stripe = load_all()

events_v = events.merge(venues[["venue_id","venue_name","city","borough","neighborhood","region_path","lat","lon"]], on="venue_id", how="left")
tickets["checked_in"] = (tickets["checkin_ts"].str.len()>0).astype(int)
tt = tickets.merge(events_v[["event_id","venue_id","region_path","city","borough","neighborhood"]], on="event_id", how="left")
rev = stripe.copy()
rev = rev.merge(events_v[["event_id","venue_id","region_path","city","borough","neighborhood"]], on="event_id", how="left")

agg = tt.groupby("region_path", as_index=False).agg(
    tickets_sold=("order_id","count"),
    checkins=("checked_in","sum"),
    cancellations=("cancel_ts", lambda s: (s.str.len()>0).sum())
)
rev_agg = rev.groupby("region_path", as_index=False)["net_amount"].sum()
agg = agg.merge(rev_agg, on="region_path", how="left").fillna({"net_amount":0.0})
agg.rename(columns={"net_amount":"net_revenue"}, inplace=True)
agg["rev_per_attendee"] = np.where(agg["checkins"]>0, agg["net_revenue"]/agg["checkins"], np.nan)

st.title("🗺️ Region & Segments")
st.caption("Ranking por região (City > Borough > Neighborhood).")

st.dataframe(agg.sort_values("net_revenue", ascending=False), use_container_width=True)

fig = px.bar(agg.sort_values("net_revenue", ascending=False).head(20), x="region_path", y="net_revenue", title="Top Regiões por Receita")
fig.update_layout(xaxis_tickangle=45)
st.plotly_chart(fig, use_container_width=True)
