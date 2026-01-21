import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import pytz
import time
import json
import io
import numpy as np
from collections import Counter
import re

# Set page config
st.set_page_config(
    page_title="HubSpot Contacts Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark blue theme
st.markdown("""
<style>
    /* Main styling - Dark Blue Theme */
    .main {
        background-color: #0f172a;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    
    .main-header {
        font-size: 2.8rem;
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        font-weight: 800;
        text-align: center;
    }
    
    /* Card styling - Dark Blue */
    .metric-card {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(59, 130, 246, 0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
        backdrop-filter: blur(10px);
    }
    
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(59, 130, 246, 0.4);
        border-color: #3b82f6;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
    
    .metric-percentage {
        font-size: 1rem;
        font-weight: 600;
        color: #60a5fa;
        margin-top: 0.5rem;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #1e293b;
        padding: 6px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        background-color: transparent;
        transition: all 0.3s ease;
        color: #94a3b8;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    /* Button styling */
    .stButton button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: white !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.4);
    }
    
    .secondary-button button {
        background: #334155 !important;
        color: #f1f5f9 !important;
    }
    
    /* Dataframe styling */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #334155;
    }
    
    /* Custom containers */
    .info-container {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 5px solid #3b82f6;
        margin: 1rem 0;
        color: #f1f5f9;
        backdrop-filter: blur(10px);
    }
    
    .warning-container {
        background: rgba(234, 179, 8, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 5px solid #fbbf24;
        margin: 1rem 0;
        color: #fef3c7;
    }
    
    .success-container {
        background: rgba(34, 197, 94, 0.1);
        border-radius: 12px;
        padding: 1.5rem;
        border-left: 5px solid #22c55e;
        margin: 1rem 0;
        color: #dcfce7;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        color: white;
    }
    
    [data-testid="stSidebar"] .stButton button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: white !important;
    }
    
    /* Charts container */
    .chart-container {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        margin-bottom: 1.5rem;
        border: 1px solid rgba(59, 130, 246, 0.3);
        backdrop-filter: blur(10px);
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #64748b;
        font-size: 0.85rem;
        border-top: 1px solid #334155;
        margin-top: 2rem;
    }
    
    /* Feature cards */
    .feature-card {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        transition: transform 0.3s ease;
        text-align: center;
        height: 100%;
        border: 1px solid rgba(59, 130, 246, 0.3);
        backdrop-filter: blur(10px);
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(59, 130, 246, 0.4);
        border-color: #3b82f6;
    }
    
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .feature-card h3 {
        color: #f1f5f9;
        margin-bottom: 0.5rem;
    }
    
    .feature-card p {
        color: #94a3b8;
    }
    
    /* KPI Grid */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    /* Text colors */
    h1, h2, h3, h4, h5, h6 {
        color: #f1f5f9 !important;
    }
    
    p, label, div {
        color: #cbd5e1 !important;
    }
    
    /* Selectbox styling */
    .stSelectbox div[data-baseweb="select"] {
        background-color: #1e293b !important;
        border-color: #475569 !important;
    }
    
    .stSelectbox div[data-baseweb="select"]:hover {
        border-color: #3b82f6 !important;
    }
    
    /* Date input styling */
    .stDateInput div[data-baseweb="input"] {
        background-color: #1e293b !important;
        border-color: #475569 !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%) !important;
    }
    
    /* Metric value in streamlit */
    [data-testid="stMetricValue"] {
        color: #f8fafc !important;
        font-weight: 800 !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
    }
    
    /* Dataframe headers */
    .dataframe thead th {
        background-color: #1e293b !important;
        color: #f1f5f9 !important;
        border-color: #475569 !important;
    }
    
    .dataframe tbody td {
        background-color: #0f172a !important;
        color: #cbd5e1 !important;
        border-color: #334155 !important;
    }
    
    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 0.35em 0.65em;
        font-size: 0.75em;
        font-weight: 700;
        line-height: 1;
        text-align: center;
        white-space: nowrap;
        vertical-align: baseline;
        border-radius: 10rem;
        margin: 0.2rem;
    }
    
    .badge-primary {
        color: #fff;
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
    }
    
    .badge-success {
        color: #fff;
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    }
    
    .badge-warning {
        color: #fff;
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    }
    
    .badge-danger {
        color: #fff;
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }
</style>
""", unsafe_allow_html=True)

# Constants
HUBSPOT_API_BASE = "https://api.hubapi.com"
IST = pytz.timezone('Asia/Kolkata')

# Country code mapping
COUNTRY_CODES = {
    '+1': 'USA/Canada',
    '+91': 'India',
    '+44': 'United Kingdom',
    '+61': 'Australia',
    '+971': 'UAE',
    '+65': 'Singapore',
    '+60': 'Malaysia',
    '+86': 'China',
    '+49': 'Germany',
    '+33': 'France',
    '+81': 'Japan',
    '+82': 'South Korea',
    '+7': 'Russia',
    '+55': 'Brazil',
    '+34': 'Spain',
    '+39': 'Italy'
}

# Color scheme for dark theme
COLOR_SCHEME = ['#3b82f6', '#1d4ed8', '#60a5fa', '#93c5fd', '#1e40af']

# SECRET API KEY
try:
    if "HUBSPOT_API_KEY" in st.secrets:
        HUBSPOT_API_KEY = st.secrets["HUBSPOT_API_KEY"]
    else:
        st.error("❌ HUBSPOT_API_KEY not found in secrets. Please check your .streamlit/secrets.toml file.")
        st.stop()
except FileNotFoundError:
    st.error("❌ .streamlit/secrets.toml not found. Please create this file to store your API key safely.")
    st.stop()

def test_hubspot_connection(api_key):
    """Test if the HubSpot API key is valid."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts?limit=1"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return True, "✅ Connection successful! API key is valid."
        elif response.status_code == 401:
            error_data = response.json()
            error_message = error_data.get('message', 'Unknown error')
            
            if "Invalid token" in error_message or "expired" in error_message:
                return False, "❌ API key is invalid or expired. Please generate a new token from HubSpot."
            elif "scope" in error_message.lower():
                return False, f"❌ Missing required scopes. Error: {error_message}"
            else:
                return False, f"❌ Authentication failed. Status: {response.status_code}, Error: {error_message}"
        else:
            return False, f"❌ Connection failed. Status: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"❌ Connection error: {str(e)}"

def date_to_hubspot_timestamp(date_obj, is_end_date=False):
    """Convert date to HubSpot timestamp (milliseconds)."""
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
    
    if is_end_date:
        dt = datetime.combine(date_obj, datetime.max.time())
    else:
        dt = datetime.combine(date_obj, datetime.min.time())
    
    dt_ist = IST.localize(dt)
    dt_utc = dt_ist.astimezone(pytz.UTC)
    
    return int(dt_utc.timestamp() * 1000)

def fetch_hubspot_contacts_with_date_filter(api_key, date_field, start_date, end_date):
    """Fetch ALL contacts from HubSpot with server-side date filtering."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    start_timestamp = date_to_hubspot_timestamp(start_date, is_end_date=False)
    safe_end_date = end_date + timedelta(days=1)
    end_timestamp = date_to_hubspot_timestamp(safe_end_date, is_end_date=False)
    
    all_contacts = []
    after = None
    page_count = 0
    
    # Build filter groups
    if date_field == "Created Date":
        filter_groups = [
            {
                "filters": [
                    {
                        "propertyName": "createdate",
                        "operator": "GTE",
                        "value": start_timestamp
                    },
                    {
                        "propertyName": "createdate",
                        "operator": "LTE",
                        "value": end_timestamp
                    }
                ]
            }
        ]
    elif date_field == "Last Modified Date":
        filter_groups = [
            {
                "filters": [
                    {
                        "propertyName": "lastmodifieddate",
                        "operator": "GTE",
                        "value": start_timestamp
                    },
                    {
                        "propertyName": "lastmodifieddate",
                        "operator": "LTE",
                        "value": end_timestamp
                    }
                ]
            }
        ]
    else:
        filter_groups = [
            {
                "filters": [
                    {
                        "propertyName": "createdate",
                        "operator": "GTE",
                        "value": start_timestamp
                    },
                    {
                        "propertyName": "createdate",
                        "operator": "LTE",
                        "value": end_timestamp
                    }
                ]
            },
            {
                "filters": [
                    {
                        "propertyName": "lastmodifieddate",
                        "operator": "GTE",
                        "value": start_timestamp
                    },
                    {
                        "propertyName": "lastmodifieddate",
                        "operator": "LTE",
                        "value": end_timestamp
                    }
                ]
            }
        ]
    
    url = f"{HUBSPOT_API_BASE}/crm/v3/objects/contacts/search"
    
    # Create progress container
    progress_container = st.empty()
    with progress_container.container():
        st.markdown("""
        <div class="info-container">
            <h3>📡 Fetching HubSpot Data</h3>
            <p>Please wait while we fetch all contacts...</p>
        </div>
        """, unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.markdown(f"**Fetching ALL contacts with {date_field} filter from {start_date} to {end_date}...**")
    
    # Define all properties
    all_properties = [
        "hs_lead_status", "lifecyclestage", "hubspot_owner_id",
        "future_prospect_reasons", "hot_prospect_reason", 
        "neutral_prospect_reasons", "not_connected_reasons",
        "not_interested_reasons", "prospect_reasons",
        "other_enquiry_reasons", "lead_status",
        "course", "program", "product", "service", "offering",
        "course_name", "program_name", "product_name",
        "enquired_course", "interested_course", "course_interested",
        "program_of_interest", "course_of_interest", "product_of_interest",
        "service_of_interest", "training_program", "educational_program",
        "learning_program", "certification_program",
        "contact_reason", "reason_for_contact", "enquiry_reason",
        "disqualification_reason", "conversion_reason",
        "firstname", "lastname", "email", "phone", 
        "createdate", "lastmodifieddate", "hs_object_id",
        "company", "jobtitle", "country", "state", "city",
        "industry", "annualrevenue", "numemployees",
        "website", "mobilephone", "address",
        "hs_analytics_source", "hs_analytics_source_data_1",
        "hs_analytics_source_data_2"
    ]
    
    try:
        while True:
            body = {
                "filterGroups": filter_groups,
                "properties": all_properties,
                "limit": 100,
                "sorts": [{
                    "propertyName": "createdate" if date_field == "Created Date" else "lastmodifieddate",
                    "direction": "ASCENDING"
                }]
            }
            
            if after:
                body["after"] = after
            
            response = requests.post(url, headers=headers, json=body, timeout=30)
            
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 10))
                status_text.warning(f"⚠️ Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                continue
            
            response.raise_for_status()
            data = response.json()
            
            batch_contacts = data.get("results", [])
            
            if batch_contacts:
                all_contacts.extend(batch_contacts)
                page_count += 1
                
                progress = min(0.9, page_count / 10)
                progress_bar.progress(progress)
                status_text.markdown(f"**Fetched {len(all_contacts)} contacts (Page {page_count})...**")
                
                paging_info = data.get("paging", {})
                after = paging_info.get("next", {}).get("after")
                
                if not after:
                    progress_bar.progress(1.0)
                    status_text.markdown(f"**✅ Fetch complete! Total: {len(all_contacts)} contacts**")
                    break
                
                time.sleep(0.1)
            else:
                progress_bar.progress(1.0)
                status_text.markdown(f"**✅ No more results. Total: {len(all_contacts)} contacts**")
                break
        
        progress_container.empty()
        return all_contacts, len(all_contacts)
        
    except requests.exceptions.RequestException as e:
        progress_container.empty()
        st.error(f"❌ Error fetching data: {e}")
        return [], 0
    except Exception as e:
        progress_container.empty()
        st.error(f"❌ Unexpected error: {e}")
        return [], 0

def process_contacts_data(contacts):
    """Process raw contacts data into a clean DataFrame."""
    if not contacts:
        return pd.DataFrame()
    
    processed_data = []
    
    for contact in contacts:
        properties = contact.get("properties", {})
        
        # Format dates
        created_date = properties.get("createdate", "")
        if created_date:
            try:
                created_date = pd.to_datetime(int(created_date), unit='ms')
            except:
                pass
        
        last_modified = properties.get("lastmodifieddate", "")
        if last_modified:
            try:
                last_modified = pd.to_datetime(int(last_modified), unit='ms')
            except:
                pass
        
        # Extract COURSE/PROGRAM information
        course_info = ""
        course_priority_fields = [
            "course", "program", "product", "service", "offering",
            "course_name", "program_name", "product_name",
            "enquired_course", "interested_course", "course_interested",
            "program_of_interest", "course_of_interest", "product_of_interest",
            "service_of_interest", "training_program", "educational_program",
            "learning_program", "certification_program"
        ]
        
        for field in course_priority_fields:
            if field in properties and properties[field]:
                course_info = properties[field]
                break
        
        # Extract lead source
        lead_source = properties.get("hs_analytics_source", "")
        lead_source_data1 = properties.get("hs_analytics_source_data_1", "")
        lead_source_data2 = properties.get("hs_analytics_source_data_2", "")
        
        # Combine source information
        if lead_source_data2:
            lead_source_info = lead_source_data2
        elif lead_source_data1:
            lead_source_info = lead_source_data1
        else:
            lead_source_info = lead_source
        
        processed_data.append({
            "ID": contact.get("id", ""),
            "First Name": properties.get("firstname", ""),
            "Last Name": properties.get("lastname", ""),
            "Full Name": f"{properties.get('firstname', '')} {properties.get('lastname', '')}".strip(),
            "Email": properties.get("email", ""),
            "Phone": properties.get("phone", ""),
            "Mobile Phone": properties.get("mobilephone", ""),
            "Company": properties.get("company", ""),
            "Job Title": properties.get("jobtitle", ""),
            
            # COURSE/PROGRAM INFORMATION
            "Course/Program": course_info,
            
            # LEAD STATUS
            "Lead Status": properties.get("hs_lead_status", "") or properties.get("lead_status", ""),
            "Lifecycle Stage": properties.get("lifecyclestage", ""),
            
            # Prospect Reasons
            "Future Prospect Reasons": properties.get("future_prospect_reasons", ""),
            "Hot Prospect Reason": properties.get("hot_prospect_reason", ""),
            "Neutral Prospect Reasons": properties.get("neutral_prospect_reasons", ""),
            "Not Connected Reasons": properties.get("not_connected_reasons", ""),
            "Not Interested Reasons": properties.get("not_interested_reasons", ""),
            "Other Enquiry Reasons": properties.get("other_enquiry_reasons", ""),
            "Prospect Reasons": properties.get("prospect_reasons", ""),
            
            # Additional reason fields
            "Contact Reason": properties.get("contact_reason", ""),
            "Reason for Contact": properties.get("reason_for_contact", ""),
            "Enquiry Reason": properties.get("enquiry_reason", ""),
            "Disqualification Reason": properties.get("disqualification_reason", ""),
            "Conversion Reason": properties.get("conversion_reason", ""),
            
            # Source Information
            "Lead Source": lead_source_info,
            
            # Other contact info
            "Country": properties.get("country", ""),
            "State": properties.get("state", ""),
            "City": properties.get("city", ""),
            "Industry": properties.get("industry", ""),
            "Website": properties.get("website", ""),
            "Owner ID": properties.get("hubspot_owner_id", ""),
            "Created Date": created_date,
            "Last Modified Date": last_modified,
            "Has Email": 1 if properties.get("email") else 0,
            "Has Phone": 1 if properties.get("phone") else 0,
            "Has Course": 1 if course_info else 0,
            "Has Company": 1 if properties.get("company") else 0,
            "Has Job Title": 1 if properties.get("jobtitle") else 0
        })
    
    df = pd.DataFrame(processed_data)
    return df

def create_metric_card(title, value, percentage=None, icon="📊", color="#3b82f6"):
    """Create a metric card with count and percentage."""
    percentage_html = ""
    if percentage is not None:
        percentage_html = f"""
        <div class="metric-percentage">
            {percentage:.1f}%
        </div>
        """
    
    return f"""
    <div class="metric-card" style="border-left-color: {color};">
        <div class="metric-label">{icon} {title}</div>
        <div class="metric-value">{value}</div>
        {percentage_html}
    </div>
    """

def analyze_contact_data(df):
    """Perform comprehensive analysis on contacts data."""
    analysis = {}
    
    if df.empty:
        return analysis
    
    # 1. Lead Status Distribution
    if 'Lead Status' in df.columns:
        df['Lead_Status_Clean'] = df['Lead Status'].fillna('Unknown').str.strip()
        lead_status_dist = df['Lead_Status_Clean'].value_counts().reset_index()
        lead_status_dist.columns = ['Lead Status', 'Count']
        lead_status_dist = lead_status_dist.sort_values('Count', ascending=False)
        analysis['lead_status_distribution'] = lead_status_dist
    
    # 2. Course Distribution
    if 'Course/Program' in df.columns:
        df['Course_Clean'] = df['Course/Program'].fillna('').astype(str).str.strip()
        courses_with_data = df[df['Course_Clean'] != '']
        if not courses_with_data.empty:
            course_dist = courses_with_data['Course_Clean'].value_counts().reset_index()
            course_dist.columns = ['Course', 'Count']
            course_dist = course_dist.sort_values('Count', ascending=False)
            analysis['course_distribution'] = course_dist
    
    # 3. Prospect Reasons Analysis
    prospect_columns = [
        'Future Prospect Reasons',
        'Hot Prospect Reason',
        'Neutral Prospect Reasons',
        'Not Connected Reasons',
        'Not Interested Reasons',
        'Other Enquiry Reasons',
        'Prospect Reasons',
        'Contact Reason',
        'Reason for Contact',
        'Enquiry Reason',
        'Disqualification Reason',
        'Conversion Reason'
    ]
    
    available_columns = [col for col in prospect_columns if col in df.columns]
    results = {}
    
    for column in available_columns:
        df[column] = df[column].fillna('').astype(str).str.strip()
        non_empty = df[df[column] != ''][column]
        if not non_empty.empty:
            reason_dist = non_empty.value_counts().reset_index()
            reason_dist.columns = ['Reason', 'Count']
            reason_dist = reason_dist.sort_values('Count', ascending=False)
            results[column] = reason_dist
    
    if results:
        analysis['prospect_reasons'] = results
    
    # 4. Country Analysis
    if 'Country' in df.columns:
        country_dist = df['Country'].value_counts().reset_index()
        country_dist.columns = ['Country', 'Count']
        analysis['country_distribution'] = country_dist
    
    # 5. Industry Analysis
    if 'Industry' in df.columns:
        industry_dist = df['Industry'].value_counts().reset_index()
        industry_dist.columns = ['Industry', 'Count']
        analysis['industry_distribution'] = industry_dist
    
    # 6. Lead Source Analysis
    if 'Lead Source' in df.columns:
        source_dist = df['Lead Source'].value_counts().reset_index()
        source_dist.columns = ['Lead Source', 'Count']
        analysis['lead_source_distribution'] = source_dist
    
    # 7. Monthly Trend
    if 'Created Date' in df.columns:
        try:
            df['Created_Month'] = df['Created Date'].dt.to_period('M')
            monthly_trend = df.groupby('Created_Month').size().reset_index()
            monthly_trend.columns = ['Month', 'Count']
            monthly_trend['Month'] = monthly_trend['Month'].astype(str)
            analysis['monthly_trend'] = monthly_trend
        except:
            pass
    
    # 8. Contact Completeness Analysis
    total_contacts = len(df)
    completeness_data = {
        'Field': ['Email', 'Phone', 'Lead Status', 'Course/Program', 'Company', 'Country', 'Job Title'],
        'Count': [
            df['Has Email'].sum(),
            df['Has Phone'].sum(),
            df['Lead Status'].notna().sum(),
            df['Has Course'].sum(),
            df['Has Company'].sum(),
            df['Country'].notna().sum(),
            df['Has Job Title'].sum()
        ]
    }
    completeness_data['Percentage'] = [(count / total_contacts * 100) for count in completeness_data['Count']]
    analysis['completeness'] = pd.DataFrame(completeness_data)
    
    return analysis

def create_visualizations(analysis, df, total_contacts):
    """Create Plotly visualizations with dark theme."""
    visualizations = {}
    
    # Dark theme template
    dark_template = {
        'layout': {
            'paper_bgcolor': 'rgba(0,0,0,0)',
            'plot_bgcolor': 'rgba(0,0,0,0)',
            'font': {'color': '#cbd5e1'},
            'title': {'font': {'color': '#f1f5f9'}},
            'xaxis': {
                'gridcolor': '#334155',
                'linecolor': '#475569',
                'zerolinecolor': '#475569'
            },
            'yaxis': {
                'gridcolor': '#334155',
                'linecolor': '#475569',
                'zerolinecolor': '#475569'
            }
        }
    }
    
    # 1. Lead Status Bar Chart
    if 'lead_status_distribution' in analysis:
        lead_status_data = analysis['lead_status_distribution'].head(10)
        if not lead_status_data.empty:
            fig1 = px.bar(
                lead_status_data,
                x='Lead Status',
                y='Count',
                title='🎯 Top 10 Lead Statuses',
                color='Count',
                color_continuous_scale='blues',
                template='plotly_dark'
            )
            fig1.update_layout(
                xaxis_tickangle=-45,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cbd5e1')
            )
            visualizations['lead_status_bar'] = fig1
    
    # 2. Course Distribution Bar Chart
    if 'course_distribution' in analysis:
        course_data = analysis['course_distribution'].head(10)
        if not course_data.empty:
            fig2 = px.bar(
                course_data,
                x='Course',
                y='Count',
                title='📚 Top 10 Courses/Programs',
                color='Count',
                color_continuous_scale='tealgrn',
                template='plotly_dark'
            )
            fig2.update_layout(
                xaxis_tickangle=-45,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            visualizations['course_bar'] = fig2
    
    # 3. Monthly Trend Line Chart
    if 'monthly_trend' in analysis:
        trend_data = analysis['monthly_trend']
        if len(trend_data) > 1:
            fig3 = px.line(
                trend_data,
                x='Month',
                y='Count',
                title='📈 Monthly Contact Creation Trend',
                markers=True,
                template='plotly_dark',
                line_shape='spline'
            )
            fig3.update_traces(
                line=dict(width=3, color='#3b82f6'),
                marker=dict(size=8, color='#60a5fa')
            )
            visualizations['monthly_trend'] = fig3
    
    # 4. Lead Status Donut Chart
    if 'lead_status_distribution' in analysis:
        lead_status_data = analysis['lead_status_distribution'].head(8)
        if not lead_status_data.empty:
            fig4 = px.pie(
                lead_status_data,
                values='Count',
                names='Lead Status',
                title='🎯 Lead Status Distribution',
                hole=0.5,
                color_discrete_sequence=px.colors.sequential.Blues
            )
            fig4.update_traces(
                textposition='inside',
                textinfo='percent+label',
                marker=dict(line=dict(color='#1e293b', width=2))
            )
            fig4.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cbd5e1')
            )
            visualizations['lead_status_pie'] = fig4
    
    # 5. Course Donut Chart
    if 'course_distribution' in analysis:
        course_data = analysis['course_distribution'].head(8)
        if not course_data.empty:
            fig5 = px.pie(
                course_data,
                values='Count',
                names='Course',
                title='📚 Top Course Distribution',
                hole=0.5,
                color_discrete_sequence=px.colors.sequential.Teal
            )
            fig5.update_traces(
                textposition='inside',
                textinfo='percent+label',
                marker=dict(line=dict(color='#1e293b', width=2))
            )
            fig5.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cbd5e1')
            )
            visualizations['course_pie'] = fig5
    
    # 6. Completeness Gauge
    if 'completeness' in analysis and total_contacts > 0:
        completeness_score = (df['Has Email'].sum() + df['Has Phone'].sum()) / (total_contacts * 2) * 100
        
        fig6 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=completeness_score,
            title={'text': "📊 Data Completeness Score", 'font': {'color': '#cbd5e1'}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#cbd5e1"},
                'bar': {'color': "#3b82f6"},
                'bgcolor': "#1e293b",
                'borderwidth': 2,
                'bordercolor': "#334155",
                'steps': [
                    {'range': [0, 50], 'color': '#ef4444'},
                    {'range': [50, 80], 'color': '#f59e0b'},
                    {'range': [80, 100], 'color': '#22c55e'}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig6.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': "#cbd5e1"}
        )
        visualizations['completeness_gauge'] = fig6
    
    return visualizations

def display_kpi_metrics(df):
    """Display KPI metrics with counts and percentages."""
    total_contacts = len(df)
    
    if total_contacts == 0:
        return
    
    # Calculate metrics
    email_count = df['Has Email'].sum()
    phone_count = df['Has Phone'].sum()
    course_count = df['Has Course'].sum()
    company_count = df['Has Company'].sum()
    job_title_count = df['Has Job Title'].sum()
    lead_status_count = df['Lead Status'].notna().sum()
    
    # Calculate percentages
    email_percent = (email_count / total_contacts * 100)
    phone_percent = (phone_count / total_contacts * 100)
    course_percent = (course_count / total_contacts * 100)
    company_percent = (company_count / total_contacts * 100)
    job_title_percent = (job_title_count / total_contacts * 100)
    lead_status_percent = (lead_status_count / total_contacts * 100)
    
    # Create metric cards
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(create_metric_card(
            "Total Contacts",
            f"{total_contacts:,}",
            None,
            "👥",
            "#3b82f6"
        ), unsafe_allow_html=True)
        
        st.markdown(create_metric_card(
            "With Email",
            f"{email_count:,}",
            email_percent,
            "📧",
            "#22c55e"
        ), unsafe_allow_html=True)
    
    with col2:
        st.markdown(create_metric_card(
            "With Phone",
            f"{phone_count:,}",
            phone_percent,
            "📱",
            "#8b5cf6"
        ), unsafe_allow_html=True)
        
        st.markdown(create_metric_card(
            "With Course",
            f"{course_count:,}",
            course_percent,
            "📚",
            "#f59e0b"
        ), unsafe_allow_html=True)
    
    with col3:
        st.markdown(create_metric_card(
            "With Company",
            f"{company_count:,}",
            company_percent,
            "🏢",
            "#ef4444"
        ), unsafe_allow_html=True)
        
        st.markdown(create_metric_card(
            "With Lead Status",
            f"{lead_status_count:,}",
            lead_status_percent,
            "🎯",
            "#06b6d4"
        ), unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def analyze_email_validation(df):
    """Comprehensive email validation analysis."""
    if 'Email' not in df.columns:
        return pd.DataFrame()
    
    email_issues = []
    
    for idx, email in df['Email'].items():
        if pd.isna(email) or str(email).strip() == '':
            email_issues.append({
                'Record ID': df.loc[idx, 'ID'] if 'ID' in df.columns else idx,
                'Email': '',
                'Issue': 'Missing email'
            })
            continue
        
        email_str = str(email).lower().strip()
        
        # Check for common typos
        if '@gmal.com' in email_str:
            email_issues.append({
                'Record ID': df.loc[idx, 'ID'] if 'ID' in df.columns else idx,
                'Email': email_str,
                'Issue': 'Incorrect domain: gmal.com'
            })
        elif '@gmil.com' in email_str:
            email_issues.append({
                'Record ID': df.loc[idx, 'ID'] if 'ID' in df.columns else idx,
                'Email': email_str,
                'Issue': 'Incorrect domain: gmil.com'
            })
        elif '@gamil.com' in email_str:
            email_issues.append({
                'Record ID': df.loc[idx, 'ID'] if 'ID' in df.columns else idx,
                'Email': email_str,
                'Issue': 'Incorrect domain: gamil.com'
            })
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email_str):
            email_issues.append({
                'Record ID': df.loc[idx, 'ID'] if 'ID' in df.columns else idx,
                'Email': email_str,
                'Issue': 'Invalid email format'
            })
    
    return pd.DataFrame(email_issues)

def main():
    # Modern header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0;">
        <h1 class="main-header">HubSpot Contacts Analytics Dashboard</h1>
        <p style="color: #94a3b8; font-size: 1.2rem; margin-bottom: 2rem;">
            Advanced Analytics & Insights for Your HubSpot Contacts
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'contacts_df' not in st.session_state:
        st.session_state.contacts_df = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'visualizations' not in st.session_state:
        st.session_state.visualizations = None
    if 'email_validation' not in st.session_state:
        st.session_state.email_validation = None
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h3 style="color: #f1f5f9;">🔧 Configuration</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Connection status
        if st.button("🔗 Test API Connection", use_container_width=True):
            is_valid, message = test_hubspot_connection(HUBSPOT_API_KEY)
            if is_valid:
                st.success(message)
            else:
                st.error(message)
        
        st.divider()
        
        # Date Filter Section
        st.markdown("### 📅 Date Range Filter")
        
        date_field = st.selectbox(
            "Select date field:",
            ["Created Date", "Last Modified Date", "Both"]
        )
        
        # Default dates
        default_end = datetime.now(IST).date()
        default_start = default_end - timedelta(days=51)
        
        start_date = st.date_input("Start date", value=default_start)
        end_date = st.date_input("End date", value=default_end)
        
        if start_date > end_date:
            st.error("Start date must be before end date!")
            return
        
        days_diff = (end_date - start_date).days + 1
        st.info(f"Will fetch ALL contacts from {days_diff} day(s)")
        
        st.divider()
        
        # Quick Actions
        st.markdown("### ⚡ Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Fetch ALL", type="primary", use_container_width=True):
                if start_date > end_date:
                    st.error("Start date must be before end date.")
                else:
                    with st.spinner("Fetching ALL contacts..."):
                        success, message = test_hubspot_connection(HUBSPOT_API_KEY)
                        
                        if success:
                            contacts, total_fetched = fetch_hubspot_contacts_with_date_filter(
                                HUBSPOT_API_KEY, date_field, start_date, end_date
                            )
                            
                            if contacts:
                                df = process_contacts_data(contacts)
                                st.session_state.contacts_df = df
                                
                                analysis_results = analyze_contact_data(df)
                                st.session_state.analysis_results = analysis_results
                                
                                visualizations = create_visualizations(analysis_results, df, len(df))
                                st.session_state.visualizations = visualizations
                                
                                email_validation = analyze_email_validation(df)
                                st.session_state.email_validation = email_validation
                                
                                st.success(f"✅ Successfully loaded {len(contacts)} contacts!")
                                st.rerun()
                            else:
                                st.warning("No contacts found for the selected date range.")
                        else:
                            st.error(f"Connection failed: {message}")
        
        with col2:
            if st.button("🔄 Refresh", use_container_width=True, type="secondary"):
                if 'contacts_df' in st.session_state:
                    df = st.session_state.contacts_df
                    if df is not None and not df.empty:
                        analysis_results = analyze_contact_data(df)
                        st.session_state.analysis_results = analysis_results
                        
                        visualizations = create_visualizations(analysis_results, df, len(df))
                        st.session_state.visualizations = visualizations
                        
                        email_validation = analyze_email_validation(df)
                        st.session_state.email_validation = email_validation
                        
                        st.success("Analysis refreshed!")
                        st.rerun()
        
        if st.button("🗑️ Clear Data", use_container_width=True, type="secondary"):
            st.session_state.clear()
            st.rerun()
        
        st.divider()
        
        # Info section
        st.markdown("### 📊 Dashboard Info")
        st.markdown("""
        <div style="color: #94a3b8; font-size: 0.9rem;">
        <strong>Features:</strong>
        • Lead status distribution
        • Course/program analysis
        • Prospect reasons insights
        • Contact quality metrics
        • Geographic analysis
        • Data validation
        </div>
        """, unsafe_allow_html=True)
    
    # Main content area
    if st.session_state.contacts_df is not None and not st.session_state.contacts_df.empty:
        df = st.session_state.contacts_df
        
        # Show filter info
        st.markdown(f"""
        <div class="info-container">
            <h3>📊 Dashboard Overview</h3>
            <p><strong>Showing:</strong> {len(df):,} contacts | 
            <strong>Date Filter:</strong> {date_field} from {start_date} to {end_date} | 
            <strong>Last Updated:</strong> {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display KPI Metrics
        st.markdown("## 📈 Key Performance Indicators")
        display_kpi_metrics(df)
        
        st.divider()
        
        # Create tabs for different sections
        tab_titles = [
            "📊 Lead Analytics", 
            "📚 Course Insights",
            "🎯 Prospect Reasons",
            "🌍 Geographic View", 
            "📧 Data Quality",
            "📥 Export Data"
        ]
        
        tabs = st.tabs(tab_titles)
        
        with tabs[0]:  # Lead Analytics
            st.markdown("### 📊 Lead Status Analysis")
            
            if 'lead_status_distribution' in st.session_state.analysis_results:
                lead_data = st.session_state.analysis_results['lead_status_distribution']
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("#### 📋 Lead Status Distribution")
                    st.dataframe(lead_data, use_container_width=True, height=400)
                
                with col2:
                    # Top 5 lead statuses
                    st.markdown("#### 🏆 Top 5 Statuses")
                    top_5 = lead_data.head(5)
                    for idx, row in top_5.iterrows():
                        st.markdown(f"""
                        <div style="background: rgba(30, 41, 59, 0.8); padding: 1rem; border-radius: 8px; 
                                    margin: 0.5rem 0; border-left: 4px solid #3b82f6;">
                            <div style="color: #f1f5f9; font-weight: 600;">{row['Lead Status']}</div>
                            <div style="color: #60a5fa; font-size: 1.5rem; font-weight: 800;">{row['Count']:,}</div>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Charts
            if st.session_state.visualizations:
                visuals = st.session_state.visualizations
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'lead_status_bar' in visuals:
                        st.plotly_chart(visuals['lead_status_bar'], use_container_width=True)
                
                with col2:
                    if 'lead_status_pie' in visuals:
                        st.plotly_chart(visuals['lead_status_pie'], use_container_width=True)
                
                if 'monthly_trend' in visuals:
                    st.plotly_chart(visuals['monthly_trend'], use_container_width=True)
        
        with tabs[1]:  # Course Insights
            st.markdown("### 📚 Course & Program Analysis")
            
            if 'course_distribution' in st.session_state.analysis_results:
                course_data = st.session_state.analysis_results['course_distribution']
                
                if not course_data.empty:
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("#### 📋 Course Distribution")
                        st.dataframe(course_data, use_container_width=True, height=400)
                    
                    with col2:
                        st.markdown("#### 🏆 Top 5 Courses")
                        top_5 = course_data.head(5)
                        for idx, row in top_5.iterrows():
                            course_name = row['Course'][:20] + "..." if len(row['Course']) > 20 else row['Course']
                            st.markdown(f"""
                            <div style="background: rgba(30, 41, 59, 0.8); padding: 1rem; border-radius: 8px; 
                                        margin: 0.5rem 0; border-left: 4px solid #22c55e;">
                                <div style="color: #f1f5f9; font-weight: 600;">{course_name}</div>
                                <div style="color: #22c55e; font-size: 1.5rem; font-weight: 800;">{row['Count']:,}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Charts
                    if st.session_state.visualizations:
                        visuals = st.session_state.visualizations
                        
                        col3, col4 = st.columns(2)
                        
                        with col3:
                            if 'course_bar' in visuals:
                                st.plotly_chart(visuals['course_bar'], use_container_width=True)
                        
                        with col4:
                            if 'course_pie' in visuals:
                                st.plotly_chart(visuals['course_pie'], use_container_width=True)
                else:
                    st.info("No course/program data available")
        
        with tabs[2]:  # Prospect Reasons
            st.markdown("### 🎯 Prospect Reasons Analysis")
            
            if 'prospect_reasons' in st.session_state.analysis_results:
                prospect_reasons = st.session_state.analysis_results['prospect_reasons']
                
                if prospect_reasons:
                    # Show top reasons from all categories
                    all_reasons = []
                    for reason_type, reason_data in prospect_reasons.items():
                        for _, row in reason_data.head(3).iterrows():
                            all_reasons.append({
                                'Type': reason_type,
                                'Reason': row['Reason'],
                                'Count': row['Count']
                            })
                    
                    if all_reasons:
                        reasons_df = pd.DataFrame(all_reasons)
                        reasons_df = reasons_df.sort_values('Count', ascending=False)
                        
                        st.markdown("#### 🔝 Top Prospect Reasons")
                        st.dataframe(reasons_df, use_container_width=True, height=300)
                    
                    # Detailed analysis by category
                    st.markdown("#### 📊 Detailed Analysis by Category")
                    reason_categories = list(prospect_reasons.keys())[:4]
                    
                    for category in reason_categories:
                        with st.expander(f"📋 {category}"):
                            category_data = prospect_reasons[category]
                            st.dataframe(category_data, use_container_width=True, height=200)
                else:
                    st.info("No prospect reason data available")
        
        with tabs[3]:  # Geographic View
            st.markdown("### 🌍 Geographic Distribution")
            
            if 'country_distribution' in st.session_state.analysis_results:
                country_data = st.session_state.analysis_results['country_distribution']
                
                if not country_data.empty:
                    # Top 10 countries
                    top_countries = country_data.head(10)
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        fig = px.bar(
                            top_countries,
                            x='Country',
                            y='Count',
                            title='🌍 Top 10 Countries',
                            color='Count',
                            color_continuous_scale='blues',
                            template='plotly_dark'
                        )
                        fig.update_layout(
                            xaxis_tickangle=-45,
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.markdown("#### 🏆 Top 5 Countries")
                        top_5 = country_data.head(5)
                        for idx, row in top_5.iterrows():
                            country_name = row['Country'][:15] + "..." if len(row['Country']) > 15 else row['Country']
                            st.markdown(f"""
                            <div style="background: rgba(30, 41, 59, 0.8); padding: 1rem; border-radius: 8px; 
                                        margin: 0.5rem 0; border-left: 4px solid #8b5cf6;">
                                <div style="color: #f1f5f9; font-weight: 600;">{country_name}</div>
                                <div style="color: #8b5cf6; font-size: 1.5rem; font-weight: 800;">{row['Count']:,}</div>
                            </div>
                            """, unsafe_allow_html=True)
        
        with tabs[4]:  # Data Quality
            st.markdown("### 📧 Data Quality & Validation")
            
            # Email Validation
            if st.session_state.email_validation is not None:
                email_issues = st.session_state.email_validation
                
                if not email_issues.empty:
                    st.warning(f"Found {len(email_issues)} email issues")
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.dataframe(email_issues, use_container_width=True, height=250)
                    
                    with col2:
                        issue_counts = email_issues['Issue'].value_counts()
                        for issue, count in issue_counts.items():
                            st.metric(issue[:15], count)
                else:
                    st.success("✅ All emails appear valid!")
            
            # Data Completeness
            if 'completeness' in st.session_state.analysis_results:
                completeness_data = st.session_state.analysis_results['completeness']
                
                st.markdown("#### 📊 Data Completeness")
                
                for _, row in completeness_data.iterrows():
                    st.markdown(f"**{row['Field']}**")
                    col1, col2, col3 = st.columns([1, 3, 1])
                    
                    with col1:
                        st.write(f"{row['Count']:,}")
                    
                    with col2:
                        progress = row['Percentage'] / 100
                        st.progress(progress)
                    
                    with col3:
                        st.write(f"{row['Percentage']:.1f}%")
        
        with tabs[5]:  # Export Data
            st.markdown("### 📥 Export Options")
            
            # Export formats
            export_cols = st.columns(3)
            
            with export_cols[0]:
                # CSV Export
                csv_data = df.to_csv(index=False)
                st.download_button(
                    "📄 Download Full CSV",
                    csv_data,
                    f"hubspot_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    "text/csv",
                    use_container_width=True,
                    type="primary"
                )
            
            with export_cols[1]:
                # Excel Report
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='All Contacts', index=False)
                    
                    if st.session_state.analysis_results:
                        for key, data in st.session_state.analysis_results.items():
                            if isinstance(data, pd.DataFrame):
                                sheet_name = key[:30]
                                data.to_excel(writer, sheet_name=sheet_name, index=False)
                
                st.download_button(
                    "📊 Download Excel Report",
                    output.getvalue(),
                    f"hubspot_analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    type="primary"
                )
            
            with export_cols[2]:
                # Raw Data Viewer
                if st.button("👁️ View Raw Data", use_container_width=True):
                    st.dataframe(df, use_container_width=True, height=400)
            
            # Individual Exports
            st.markdown("---")
            st.markdown("#### Export Individual Analyses")
            
            if st.session_state.analysis_results:
                export_row2 = st.columns(3)
                
                with export_row2[0]:
                    if 'lead_status_distribution' in st.session_state.analysis_results:
                        csv = st.session_state.analysis_results['lead_status_distribution'].to_csv(index=False)
                        st.download_button(
                            "📊 Lead Status Report",
                            csv,
                            "lead_status_distribution.csv",
                            "text/csv",
                            use_container_width=True
                        )
                
                with export_row2[1]:
                    if 'course_distribution' in st.session_state.analysis_results:
                        csv = st.session_state.analysis_results['course_distribution'].to_csv(index=False)
                        st.download_button(
                            "📚 Course Distribution",
                            csv,
                            "course_distribution.csv",
                            "text/csv",
                            use_container_width=True
                        )
        
        # Footer
        st.divider()
        st.markdown(f"""
        <div class="footer">
            <strong>HubSpot Contacts Analytics Dashboard</strong> • Built with Streamlit • 
            Data last fetched: {datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")} IST
        </div>
        """, unsafe_allow_html=True)
    
    else:
        # Welcome screen
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem; background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;">📊</div>
            <h2 class="gradient-text" style="margin-bottom: 1rem;">Welcome to HubSpot Analytics Dashboard</h2>
            <p style="color: #94a3b8; font-size: 1.1rem; margin-bottom: 2rem;">
                Configure your date filters and click "Fetch ALL" to start analyzing your HubSpot contacts
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Feature cards
        st.markdown("### 🚀 Key Features")
        feature_cols = st.columns(3)
        
        with feature_cols[0]:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🎯</div>
                <h3>Lead Analytics</h3>
                <p>Analyze lead status distribution with counts and percentages</p>
            </div>
            """, unsafe_allow_html=True)
        
        with feature_cols[1]:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">📚</div>
                <h3>Course Insights</h3>
                <p>Track course/program distribution across all contacts</p>
            </div>
            """, unsafe_allow_html=True)
        
        with feature_cols[2]:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">📊</div>
                <h3>KPI Dashboard</h3>
                <p>Monitor key metrics with counts and completion percentages</p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
