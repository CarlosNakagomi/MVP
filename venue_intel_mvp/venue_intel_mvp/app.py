
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date

st.set_page_config(page_title="Venue Intelligence MVP", page_icon="📊", layout="wide")

st.sidebar.title("Filters")
st.sidebar.caption("Use para filtrar a visualização por período, cidade e patrocínio.")

@st.cache_data
def load_all():
    venues = pd.read_csv("data/venues.csv")
    events = pd.read_csv("data/events.csv", parse_dates=["start_ts","end_ts"])
    tickets = pd.read_csv("data/tickets.csv", parse_dates=["sold_ts"], keep_default_na=False)
    stripe = pd.read_csv("data/stripe_transactions.csv", parse_dates=["created_ts"])
    venues["region_path"] = venues["city"] + " > " + venues["borough"] + " > " + venues["neighborhood"]
    return venues, events, tickets, stripe

venues, events, tickets, stripe = load_all()

# Date filter
min_date = min(events["start_ts"].min().date(), stripe["created_ts"].min().date())
max_date = max(events["start_ts"].max().date(), stripe["created_ts"].max().date())
start, end = st.sidebar.date_input("Date range", (min_date, max_date))
if isinstance(start, tuple):
    start, end = start
start = pd.to_datetime(start)
end = pd.to_datetime(end) + pd.Timedelta(days=1)

# City filter
cities = ["All"] + sorted(venues["city"].unique().tolist())
city_sel = st.sidebar.selectbox("City", cities, index=0)

# Sponsored filter
sponsored_opt = st.sidebar.selectbox("Sponsored events only?", ["All","Sponsored","Non-sponsored"], index=0)

# Apply filters
events_f = events[(events["start_ts"]>=start) & (events["start_ts"]<end)]
if city_sel != "All":
    v_ids = venues.loc[venues["city"]==city_sel, "venue_id"]
    events_f = events_f[events_f["venue_id"].isin(v_ids)]

if sponsored_opt == "Sponsored":
    events_f = events_f[events_f["is_sponsored"]==True]
elif sponsored_opt == "Non-sponsored":
    events_f = events_f[events_f["is_sponsored"]==False]

stripe_f = stripe[(stripe["created_ts"]>=start) & (stripe["created_ts"]<end)]
tickets_f = tickets.merge(events_f[["event_id","venue_id","start_ts"]], on="event_id", how="inner")

st.title("📊 Venue Intelligence MVP")
st.caption("KPIs essenciais: Receita, Presença, Conversão, Cancelamentos, Dias de Pico e Regiões.")

# KPI row
col1, col2, col3, col4 = st.columns(4)
net_revenue = stripe_f.loc[stripe_f["status"]=="captured","net_amount"].sum() + stripe_f.loc[stripe_f["is_refund"]==1,"net_amount"].sum()
tickets_sold = len(tickets_f)
checkins = (tickets_f["checkin_ts"].str.len()>0).sum()
cancellations = (tickets_f["cancel_ts"].str.len()>0).sum()
conv = (checkins / tickets_sold) if tickets_sold>0 else 0.0

col1.metric("Net Revenue", f"${net_revenue:,.0f}")
col2.metric("Tickets Sold", f"{tickets_sold:,d}")
col3.metric("Attendance (Check-ins)", f"{checkins:,d}")
col4.metric("Check-in Rate", f"{100*conv:,.1f}%")

col5, col6 = st.columns(2)
col5.metric("Cancellations", f"{cancellations:,d}")
if tickets_sold>0:
    col6.metric("Cancellation Rate", f"{100*cancellations/tickets_sold:,.1f}%")
else:
    col6.metric("Cancellation Rate", "0.0%")

st.markdown("---")
st.write("Use o menu **Pages** (barra lateral) para navegar entre Overview, Trends, Regiões, Patrocínio e Impacto NPO.")
st.info("Dica: Substitua os CSVs em `./data` pelos seus dados reais para ver os KPIs mudarem automaticamente.")
