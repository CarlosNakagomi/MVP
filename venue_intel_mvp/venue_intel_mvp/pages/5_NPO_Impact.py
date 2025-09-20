
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="NPO Impact — Venue Intelligence", page_icon="🌱", layout="wide")

@st.cache_data
def load_all():
    venues = pd.read_csv("data/venues.csv")
    events = pd.read_csv("data/events.csv", parse_dates=["start_ts","end_ts"])
    tickets = pd.read_csv("data/tickets.csv", parse_dates=["sold_ts"], keep_default_na=False)
    stripe = pd.read_csv("data/stripe_transactions.csv", parse_dates=["created_ts"])
    return venues, events, tickets, stripe

venues, events, tickets, stripe = load_all()

st.title("🌱 NPO Impact")
st.caption("KPIs sociais (mock) — substitua por dados reais do seu CRM/CSV.")

# Mock social impact metrics derived from totals for demo
total_net = stripe.loc[stripe["status"]=="captured","net_amount"].sum() + stripe.loc[stripe["is_refund"]==1,"net_amount"].sum()
total_checkins = (tickets["checkin_ts"].str.len()>0).sum()

funds = max(total_net * 0.1, 50_000) # assume 10% directed to NPOs
beneficiaries = int(total_checkins * 1.2)
volunteers = int(total_checkins * 0.06)
campaign_success = 0.65 + np.random.rand()*0.1

c1,c2,c3,c4 = st.columns(4)
c1.metric("Funds Raised", f"${funds:,.0f}")
c2.metric("Beneficiaries Reached", f"{beneficiaries:,d}")
c3.metric("Volunteer Sign-ups", f"{volunteers:,d}")
c4.metric("Campaign Performance", f"{100*campaign_success:,.0f}%")

st.info("Estes números são exemplos. Conecte seu CRM/planilhas para alimentar este painel com dados reais.")
