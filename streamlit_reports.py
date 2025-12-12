import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

st.set_page_config(
    page_title="Cow Reports Dashboard",
    page_icon="🐄",
    layout="wide"
)

# Title
st.title("🐄 Cow Reports Dashboard")
st.markdown("---")

# Helper function to fetch data
def fetch_data(endpoint):
    """Fetch data from API endpoint"""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

# Sidebar - Cow Selection
st.sidebar.header("🐄 Select Cow")

# Fetch list of cows
cows_data = fetch_data("/cows/")
if cows_data:
    cow_options = {f"{cow['name']} (ID: {cow['id'][:8]}...)": cow for cow in cows_data}
    selected_cow_name = st.sidebar.selectbox("Choose a cow", list(cow_options.keys()))
    selected_cow = cow_options[selected_cow_name]
    selected_cow_id = selected_cow['id']
    
    # Display cow info in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Cow Information")
    st.sidebar.write(f"**Name:** {selected_cow['name']}")
    st.sidebar.write(f"**ID:** `{selected_cow['id']}`")
    st.sidebar.write(f"**Birthdate:** {selected_cow['birthdate']}")
else:
    st.sidebar.error("Unable to load cows list")
    selected_cow_id = None
    selected_cow = None

# Navigation
st.sidebar.markdown("---")
st.sidebar.header("📊 Reports")
page = st.sidebar.radio(
    "Select Report",
    ["🏠 Overview", "🥛 Milk Summary", "📅 Daily Milk Report", "⚖️ Weight Report"]
)

# Only proceed if a cow is selected
if selected_cow_id:
    
    # Page 1: Overview
    if page == "🏠 Overview":
        st.header(f"Overview for {selected_cow['name']}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.info("### 🥛 Milk Summary\nView total milk production statistics")
        
        with col2:
            st.info("### 📅 Daily Report\nAnalyze milk production by date")
        
        with col3:
            st.info("### ⚖️ Weight Tracking\nMonitor cow weight and trends")
        
        st.markdown("---")
        st.markdown("👈 **Select a report from the sidebar to view detailed information**")
    
    # Page 2: Milk Summary
    elif page == "🥛 Milk Summary":
        st.header(f"🥛 Milk Production Summary - {selected_cow['name']}")
        
        summary = fetch_data(f"/reports/milk/summary/{selected_cow_id}")
        
        if summary:
            # Main metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="Total Milk Production",
                    value=f"{summary['total_liters']:.2f} L"
                )
            
            with col2:
                st.metric(
                    label="Total Measurements",
                    value=f"{summary['total_measurements']:,}"
                )
            
            with col3:
                st.metric(
                    label="Average per Measurement",
                    value=f"{summary['avg_per_measurement']:.2f} L"
                )
            
            st.markdown("---")
            
            # Date range
            col1, col2 = st.columns(2)
            
            with col1:
                if summary['first_measurement']:
                    first_date = pd.to_datetime(summary['first_measurement'])
                    st.info(f"**First Measurement:** {first_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col2:
                if summary['last_measurement']:
                    last_date = pd.to_datetime(summary['last_measurement'])
                    st.info(f"**Last Measurement:** {last_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Calculate days active
            if summary['first_measurement'] and summary['last_measurement']:
                days_active = (last_date.date() - first_date.date()).days + 1
                st.success(f"📊 **Active Days:** {days_active} days")
                
                if summary['total_measurements'] > 0:
                    avg_per_day = summary['total_liters'] / days_active
                    st.success(f"📈 **Average Production per Day:** {avg_per_day:.2f} L")
        else:
            st.warning("No milk production data available for this cow.")
    
    # Page 3: Daily Milk Report
    elif page == "📅 Daily Milk Report":
        st.header(f"📅 Daily Milk Report - {selected_cow['name']}")
        
        # Date picker
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_date = st.date_input(
                "Select Date",
                value=date.today(),
                max_value=date.today()
            )
        
        with col2:
            st.write("")
            st.write("")
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()
        
        # Fetch daily report
        daily_report = fetch_data(f"/reports/milk/daily/{selected_cow_id}/{selected_date}")
        
        if daily_report:
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📅 Date", selected_date.strftime("%Y-%m-%d"))
            
            with col2:
                st.metric("🥛 Total Production", f"{daily_report['total_liters']:.2f} L")
            
            with col3:
                st.metric("📊 Measurements", daily_report['measurement_count'])
            
            st.markdown("---")
            
            if daily_report['measurements']:
                # Convert to DataFrame
                df_measurements = pd.DataFrame(daily_report['measurements'])
                df_measurements['measured_at'] = pd.to_datetime(df_measurements['measured_at'])
                df_measurements = df_measurements.sort_values('measured_at')
                
                # Timeline chart
                st.subheader("Production Timeline")
                fig = px.line(
                    df_measurements,
                    x='measured_at',
                    y='value',
                    markers=True,
                    title=f'Milk Production Throughout {selected_date}',
                    labels={'measured_at': 'Time', 'value': 'Liters'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Statistics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Maximum", f"{df_measurements['value'].max():.2f} L")
                
                with col2:
                    st.metric("Minimum", f"{df_measurements['value'].min():.2f} L")
                
                with col3:
                    st.metric("Average", f"{df_measurements['value'].mean():.2f} L")
                
                st.markdown("---")
                
                # Detailed measurements table
                st.subheader("Detailed Measurements")
                display_df = df_measurements[['measured_at', 'value', 'sensor_id']].copy()
                display_df['measured_at'] = display_df['measured_at'].dt.strftime('%H:%M:%S')
                display_df.columns = ['Time', 'Liters', 'Sensor ID']
                
                st.dataframe(
                    display_df.style.format({'Liters': '{:.2f}'}),
                    use_container_width=True,
                    height=300
                )
            else:
                st.info("No measurements recorded for this date.")
        else:
            st.warning(f"No data available for {selected_date}")
    
    # Page 4: Weight Report
    elif page == "⚖️ Weight Report":
        st.header(f"⚖️ Weight Report - {selected_cow['name']}")
        
        weight_report = fetch_data(f"/reports/weight/{selected_cow_id}")
        
        if weight_report:
            # Main metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="Current Weight",
                    value=f"{weight_report['current_weight']:.2f} kg"
                )
            
            with col2:
                if weight_report['avg_weight_30_days']:
                    delta = weight_report['current_weight'] - weight_report['avg_weight_30_days']
                    st.metric(
                        label="30-Day Average",
                        value=f"{weight_report['avg_weight_30_days']:.2f} kg",
                        delta=f"{delta:+.2f} kg"
                    )
                else:
                    st.metric(
                        label="30-Day Average",
                        value="N/A"
                    )
            
            with col3:
                st.metric(
                    label="Measurements (30 days)",
                    value=weight_report['measurements_30_days']
                )
            
            st.markdown("---")
            
            # Current weight info
            col1, col2 = st.columns(2)
            
            with col1:
                if weight_report['current_weight_date']:
                    weight_date = pd.to_datetime(weight_report['current_weight_date'])
                    st.info(f"**Last Measured:** {weight_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col2:
                days_ago = (pd.Timestamp.now() - weight_date).days
                st.info(f"**Days Ago:** {days_ago} days")
            
            st.markdown("---")
            
            # Weight analysis
            st.subheader("Weight Analysis")
            
            if weight_report['avg_weight_30_days']:
                current = weight_report['current_weight']
                avg = weight_report['avg_weight_30_days']
                diff = current - avg
                diff_percent = (diff / avg) * 100
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        label="Difference from 30-Day Average",
                        value=f"{diff:+.2f} kg",
                        delta=f"{diff_percent:+.2f}%"
                    )
                
                with col2:
                    if diff > 0:
                        st.success("✅ Weight is above 30-day average")
                    elif diff < 0:
                        st.warning("⚠️ Weight is below 30-day average")
                    else:
                        st.info("➡️ Weight equals 30-day average")
                
                # Gauge chart
                st.subheader("Weight Status")
                fig = go.Figure(go.Indicator(
                    mode="gauge+number+delta",
                    value=current,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "Current Weight (kg)"},
                    delta={'reference': avg},
                    gauge={
                        'axis': {'range': [None, max(current, avg) * 1.2]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, avg * 0.9], 'color': "lightgray"},
                            {'range': [avg * 0.9, avg * 1.1], 'color': "lightgreen"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': avg
                        }
                    }
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data to calculate 30-day average weight.")
        else:
            st.warning("No weight data available for this cow.")

else:
    st.warning("⚠️ Please select a cow from the sidebar to view reports.")

# Footer
st.markdown("---")
st.markdown("**Cow Reports Dashboard** | Powered by FastAPI + Streamlit")
