#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# GovernTrack Pro – Report Usage & KPI Centralization Intelligence Suite
# Streamlit App to monitor usage, centralization, training + quizzes & filters

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="GovernTrack Pro", layout="wide")
st.title("📊 GovernTrack Pro – Report Usage & KPI Centralization Intelligence")

# Upload CSVs
st.sidebar.header("📥 Upload Your Data")
usage_file = st.sidebar.file_uploader("Upload Report Usage CSV", type="csv")
centralization_file = st.sidebar.file_uploader("Upload Report Centralization CSV", type="csv")
training_file = st.sidebar.file_uploader("Upload Training Modules CSV", type="csv")

if usage_file and centralization_file:
    usage_df = pd.read_csv(usage_file, parse_dates=['used_at'])
    central_df = pd.read_csv(centralization_file)

    # Filters
    st.sidebar.header("🔎 Filters")
    departments = st.sidebar.multiselect("Select Departments", usage_df['department'].unique(), default=usage_df['department'].unique())
    countries = st.sidebar.multiselect("Select Countries", usage_df['country'].unique(), default=usage_df['country'].unique())
    usage_df = usage_df[usage_df['department'].isin(departments) & usage_df['country'].isin(countries)]

    st.header("🔍 Report Usage Overview")
    usage_counts = usage_df.groupby('report_name').size().reset_index(name='usage_count')
    fig_usage = px.bar(usage_counts, x='report_name', y='usage_count', title="Report Usage Frequency")
    st.plotly_chart(fig_usage, use_container_width=True)

    st.header("🌍 Centralization Adoption Map")
    merged = usage_df.merge(central_df, on='report_name', how='left')
    central_summary = merged.groupby(['country', 'is_standardized']).size().reset_index(name='count')
    fig_central = px.bar(central_summary, x='country', y='count', color='is_standardized', barmode='group',
                         title="Standardized vs Local Report Usage by Country")
    st.plotly_chart(fig_central, use_container_width=True)

    st.header("🕒 Usage Trend Over Time")
    usage_df['date'] = usage_df['used_at'].dt.date
    trend = usage_df.groupby('date').size().reset_index(name='usage_count')
    fig_trend = px.line(trend, x='date', y='usage_count', title="Daily Report Usage Trend")
    st.plotly_chart(fig_trend, use_container_width=True)

if training_file:
    training_df = pd.read_csv(training_file)
    st.header("📚 Training & Best Practices Hub")
    for _, row in training_df.iterrows():
        st.subheader(f"📘 {row['module_title']}")
        st.write(f"**Target Role:** {row['role_target']}")
        st.write(f"**Description/Link:** {row['link_or_description']}")

    st.markdown("---")
    st.subheader("📝 Training Quiz")
    st.write("Test your understanding of data governance!")
    score = 0
    if st.checkbox("Q1: What is a key benefit of standardized reports?"):
        answer1 = st.radio("", ["More customization", "Better cross-team alignment", "Faster dashboards"])
        if answer1 == "Better cross-team alignment":
            score += 1
    if st.checkbox("Q2: Who is typically responsible for maintaining KPI definitions?"):
        answer2 = st.radio(" ", ["Finance Analyst", "Report Consumer", "Data Steward"])
        if answer2 == "Data Steward":
            score += 1
    if st.checkbox("Q3: What does a usage log help identify?"):
        answer3 = st.radio("  ", ["System bugs", "Report frequency & adoption", "Training modules"])
        if answer3 == "Report frequency & adoption":
            score += 1
    if st.button("Submit Quiz"):
        st.success(f"You scored {score} out of 3")

st.sidebar.markdown("---")
st.sidebar.info("Upload CSVs for usage logs, centralization status, and training to begin analysis. Use filters for department and country.")

