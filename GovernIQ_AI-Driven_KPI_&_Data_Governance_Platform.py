#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# GovernIQ - AI-Driven KPI & Data Governance Platform 
# Streamlit + SQLite + Plotly 

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# Initialize DB
conn = sqlite3.connect("governiq.db")
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS kpis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    owner TEXT,
    department TEXT,
    created_at TEXT,
    data_source TEXT,
    frequency TEXT,
    status TEXT DEFAULT 'Draft'
)''')

c.execute('''CREATE TABLE IF NOT EXISTS usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kpi_id INTEGER,
    used_by TEXT,
    used_at TEXT,
    FOREIGN KEY (kpi_id) REFERENCES kpis(id)
)''')

c.execute('''CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kpi_id INTEGER,
    commenter TEXT,
    comment TEXT,
    timestamp TEXT,
    FOREIGN KEY (kpi_id) REFERENCES kpis(id)
)''')

c.execute('''CREATE TABLE IF NOT EXISTS workflow_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kpi_id INTEGER,
    action TEXT,
    actor TEXT,
    timestamp TEXT,
    FOREIGN KEY (kpi_id) REFERENCES kpis(id)
)''')

c.execute('''CREATE TABLE IF NOT EXISTS dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kpi_id INTEGER,
    upstream TEXT,
    downstream TEXT,
    FOREIGN KEY (kpi_id) REFERENCES kpis(id)
)''')

conn.commit()

# Sidebar Navigation
menu = ["📊 Dashboard", "➕ Add KPI", "📁 View KPIs", "📈 KPI Usage", "🔁 Workflow & Comments", "🔗 Data Lineage", "📥 Import / 📤 Export"]
choice = st.sidebar.selectbox("Navigate", menu)

# Dashboard
if choice == "📊 Dashboard":
    st.title("GovernIQ - AI-Driven KPI & Data Governance Platform ")
    kpi_count = pd.read_sql_query("SELECT COUNT(*) as total FROM kpis", conn).iloc[0]['total']
    st.metric("Total KPIs", kpi_count)
    dept_df = pd.read_sql_query("SELECT department, COUNT(*) as count FROM kpis GROUP BY department", conn)
    if not dept_df.empty:
        fig = px.pie(dept_df, names='department', values='count', title='KPIs by Department')
        st.plotly_chart(fig)

# Add KPI
elif choice == "➕ Add KPI":
    st.title("Add New KPI")
    with st.form("kpi_form"):
        name = st.text_input("KPI Name")
        description = st.text_area("Description")
        owner = st.text_input("Owner Name")
        department = st.selectbox("Department", ["Finance", "Sales", "Operations", "HR", "IT"])
        data_source = st.text_input("Data Source")
        frequency = st.selectbox("Update Frequency", ["Daily", "Weekly", "Monthly", "Quarterly"])
        status = st.selectbox("Initial Status", ["Draft", "Under Review", "Approved", "Deprecated"])
        submitted = st.form_submit_button("Submit")
        if submitted:
            created_at = datetime.now().isoformat()
            c.execute('''INSERT INTO kpis (name, description, owner, department, created_at, data_source, frequency, status)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (name, description, owner, department, created_at, data_source, frequency, status))
            conn.commit()
            st.success(f"KPI '{name}' added successfully.")

# View KPIs
elif choice == "📁 View KPIs":
    st.title("KPI Catalog")
    search = st.text_input("Search KPI by name or owner")
    query = "SELECT * FROM kpis WHERE name LIKE ? OR owner LIKE ?"
    kpis = pd.read_sql_query(query, conn, params=(f"%{search}%", f"%{search}%")) if search else pd.read_sql_query("SELECT * FROM kpis", conn)
    st.dataframe(kpis)

# KPI Usage
elif choice == "📈 KPI Usage":
    st.title("KPI Usage Monitoring")
    kpis = pd.read_sql_query("SELECT * FROM kpis", conn)
    kpi_options = {row['name']: row['id'] for _, row in kpis.iterrows()}
    with st.form("log_usage"):
        used_by = st.text_input("User")
        selected_kpi = st.selectbox("KPI Used", list(kpi_options.keys()))
        log_button = st.form_submit_button("Log Usage")
        if log_button:
            used_at = datetime.now().isoformat()
            c.execute("INSERT INTO usage_logs (kpi_id, used_by, used_at) VALUES (?, ?, ?)",
                      (kpi_options[selected_kpi], used_by, used_at))
            conn.commit()
            st.success("Usage logged successfully.")
    logs = pd.read_sql_query("SELECT k.name, u.used_by, u.used_at FROM usage_logs u JOIN kpis k ON u.kpi_id = k.id", conn)
    logs['used_at'] = pd.to_datetime(logs['used_at'], format='mixed', errors='coerce')
    st.dataframe(logs)
    if not logs.empty:
        logs_by_day = logs.groupby(logs['used_at'].dt.date).size().reset_index(name='count')
        fig = px.line(logs_by_day, x='used_at', y='count', title='KPI Usage Over Time')
        st.plotly_chart(fig)

# Workflow & Comments
elif choice == "🔁 Workflow & Comments":
    st.title("KPI Workflow & Comments")
    kpis = pd.read_sql_query("SELECT * FROM kpis", conn)
    if not kpis.empty:
        kpi_names = {row['name']: row['id'] for _, row in kpis.iterrows()}
        selected_kpi = st.selectbox("Select KPI", list(kpi_names.keys()))
        kpi_id = kpi_names[selected_kpi]

        st.subheader("Change KPI Status")
        new_status = st.selectbox("New Status", ["Draft", "Under Review", "Approved", "Deprecated"])
        actor = st.text_input("Your Name")
        if st.button("Update Status"):
            timestamp = datetime.now().isoformat()
            c.execute("UPDATE kpis SET status = ? WHERE id = ?", (new_status, kpi_id))
            c.execute("INSERT INTO workflow_logs (kpi_id, action, actor, timestamp) VALUES (?, ?, ?, ?)",
                      (kpi_id, f"Status changed to {new_status}", actor, timestamp))
            conn.commit()
            st.success("Status updated and logged.")

        st.subheader("Add Comment")
        comment = st.text_area("Write your comment")
        commenter = st.text_input("Your Name (for comments)")
        if st.button("Submit Comment"):
            timestamp = datetime.now().isoformat()
            c.execute("INSERT INTO comments (kpi_id, commenter, comment, timestamp) VALUES (?, ?, ?, ?)",
                      (kpi_id, commenter, comment, timestamp))
            conn.commit()
            st.success("Comment submitted.")

        st.subheader("Comments")
        comments_df = pd.read_sql_query("SELECT commenter, comment, timestamp FROM comments WHERE kpi_id = ?", conn, params=(kpi_id,))
        st.dataframe(comments_df)

        st.subheader("Workflow History")
        workflow_df = pd.read_sql_query("SELECT action, actor, timestamp FROM workflow_logs WHERE kpi_id = ?", conn, params=(kpi_id,))
        st.dataframe(workflow_df)

# Data Lineage
elif choice == "🔗 Data Lineage":
    st.title("Data Lineage & Dependencies")
    kpis = pd.read_sql_query("SELECT * FROM kpis", conn)
    kpi_names = {row['name']: row['id'] for _, row in kpis.iterrows()}
    selected_kpi = st.selectbox("Select KPI to view or define dependencies", list(kpi_names.keys()))
    kpi_id = kpi_names[selected_kpi]
    st.subheader("Add Dependency")
    upstream = st.text_input("Upstream Source (e.g., DB Table, External System)")
    downstream = st.text_input("Downstream Use (e.g., Dashboard Name)")
    if st.button("Save Dependency"):
        c.execute("INSERT INTO dependencies (kpi_id, upstream, downstream) VALUES (?, ?, ?)", (kpi_id, upstream, downstream))
        conn.commit()
        st.success("Dependency added.")
    st.subheader("Lineage Map")
    deps = pd.read_sql_query("SELECT upstream, downstream FROM dependencies WHERE kpi_id = ?", conn, params=(kpi_id,))
    if not deps.empty:
        nodes = list(set(deps['upstream']).union(set(deps['downstream'])))
        node_indices = {name: i for i, name in enumerate(nodes)}
        edges = [(node_indices[row['upstream']], node_indices[row['downstream']]) for _, row in deps.iterrows()]
        fig = go.Figure()
        for edge in edges:
            fig.add_trace(go.Scatter(
                x=[edge[0], edge[1]],
                y=[1, 0],
                mode="lines+markers+text",
                text=[nodes[edge[0]], nodes[edge[1]]],
                marker=dict(size=10),
                line=dict(width=2)
            ))
        fig.update_layout(title="KPI Lineage Graph", showlegend=False)
        st.plotly_chart(fig)
    else:
        st.info("No dependencies defined for this KPI.")

# Import / Export
elif choice == "📥 Import / 📤 Export":
    st.title("📥 Import & 📤 Export Data - Collibra Style")
    st.subheader("📥 Import CSV Files")
    kpi_file = st.file_uploader("Upload KPI Definitions CSV", type="csv")
    dep_file = st.file_uploader("Upload Dependencies CSV", type="csv")
    usage_file = st.file_uploader("Upload Usage Logs CSV", type="csv")
    if kpi_file:
        df_kpi = pd.read_csv(kpi_file)
        for _, row in df_kpi.iterrows():
            c.execute('''INSERT INTO kpis (name, description, owner, department, created_at, data_source, frequency, status)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      (row['name'], row['description'], row['owner'], row['department'], datetime.now().isoformat(), row['source'], row['frequency'], row['status']))
        conn.commit()
        st.success("KPI data imported.")
    if dep_file:
        df_dep = pd.read_csv(dep_file)
        for _, row in df_dep.iterrows():
            c.execute("SELECT id FROM kpis WHERE name = ?", (row['kpi_name'],))
            result = c.fetchone()
            if result:
                kpi_id = result[0]
                c.execute("INSERT INTO dependencies (kpi_id, upstream, downstream) VALUES (?, ?, ?)", (kpi_id, row['upstream'], row['downstream']))
        conn.commit()
        st.success("Dependency data imported.")
    if usage_file:
        df_usage = pd.read_csv(usage_file)
        for _, row in df_usage.iterrows():
            c.execute("SELECT id FROM kpis WHERE name = ?", (row['kpi_name'],))
            result = c.fetchone()
            if result:
                kpi_id = result[0]
                c.execute("INSERT INTO usage_logs (kpi_id, used_by, used_at) VALUES (?, ?, ?)", (kpi_id, row['used_by'], row['used_at']))
        conn.commit()
        st.success("Usage log data imported.")

    st.markdown("---")
    st.subheader("📤 Export CSV Files")
    def download_button(df, filename):
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(label=f"Download {filename}", data=csv, file_name=filename, mime='text/csv')

    df_kpis = pd.read_sql_query("SELECT * FROM kpis", conn)
    df_deps = pd.read_sql_query("SELECT * FROM dependencies", conn)
    df_usage = pd.read_sql_query("SELECT * FROM usage_logs", conn)

    download_button(df_kpis, "kpis.csv")
    download_button(df_deps, "dependencies.csv")
    download_button(df_usage, "usage_logs.csv")

conn.close()

