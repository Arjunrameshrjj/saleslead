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

# Custom CSS for modern, attractive UI
st.markdown("""
<style>
    /* Main styling */
    .main-header {
        font-size: 2.8rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
        font-weight: 800;
    }
    
    /* Card styling */
    .metric-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
        border: 1px solid #e0e0e0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.15);
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #2c3e50;
        line-height: 1;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #7f8c8d;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
    
    .metric-change {
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    /* Progress bars */
    .progress-container {
        background: #ecf0f1;
        border-radius: 10px;
        height: 10px;
        margin: 0.5rem 0;
    }
    
    .progress-bar {
        height: 100%;
        border-radius: 10px;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #f8f9fa;
        padding: 8px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        background-color: transparent;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #667eea !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Button styling */
    .stButton button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
    }
    
    .primary-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
    }
    
    /* Dataframe styling */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #e0e0e0;
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
        background-color: #667eea;
    }
    
    .badge-success {
        color: #fff;
        background-color: #38ef7d;
    }
    
    .badge-warning {
        color: #fff;
        background-color: #ff9a00;
    }
    
    .badge-danger {
        color: #fff;
        background-color: #ff4b5c;
    }
    
    /* Custom containers */
    .info-container {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        border-radius: 15px;
        padding: 1.5rem;
        border-left: 5px solid #667eea;
        margin: 1rem 0;
    }
    
    .warning-container {
        background: linear-gradient(135deg, #ff9a0015 0%, #ff6b6b15 100%);
        border-radius: 15px;
        padding: 1.5rem;
        border-left: 5px solid #ff9a00;
        margin: 1rem 0;
    }
    
    .success-container {
        background: linear-gradient(135deg, #38ef7d15 0%, #11998e15 100%);
        border-radius: 15px;
        padding: 1.5rem;
        border-left: 5px solid #38ef7d;
        margin: 1rem 0;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    [data-testid="stSidebar"] .stButton button {
        background: white;
        color: #667eea;
    }
    
    /* Charts container */
    .chart-container {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
        border: 1px solid #f0f0f0;
    }
    
    /* Gradient text */
    .gradient-text {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 1.5rem;
        color: #7f8c8d;
        font-size: 0.85rem;
        border-top: 1px solid #ecf0f1;
        margin-top: 2rem;
    }
    
    /* Status indicators */
    .status-indicator {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }
    
    .status-active {
        background-color: #38ef7d;
        box-shadow: 0 0 10px #38ef7d;
    }
    
    .status-inactive {
        background-color: #ff4b5c;
    }
    
    /* Loading animation */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    /* Feature cards on welcome page */
    .feature-card {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
        text-align: center;
        height: 100%;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    
    /* Dashboard header */
    .dashboard-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 2rem;
        color: white;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Constants
HUBSPOT_API_BASE = "https://api.hubapi.com"
IST = pytz.timezone('Asia/Kolkata')

# Country code mapping for phone analysis
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

# Lead status categories
LEAD_STATUS_CATEGORIES = {
    'Hot': '🔥 Hot',
    'Warm': '🌡️ Warm', 
    'Cold': '❄️ Cold',
    'Not Qualified': '🚫 Not Qualified',
    'Not Interested': '🙅 Not Interested',
    'Future Prospect': '📅 Future Prospect',
    'Not Connected': '📞 Not Connected',
    'Duplicate': '📋 Duplicate'
}

# Color schemes
COLOR_SCHEMES = {
    'primary': ['#667eea', '#764ba2', '#38ef7d', '#11998e', '#ff9a00', '#ff6b6b'],
    'sequential': px.colors.sequential.Viridis,
    'qualitative': px.colors.qualitative.Set3,
    'diverging': px.colors.diverging.RdBu
}

# SECRET API KEY - LOADED FROM SECRETS
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
    
    # Create progress container with custom styling
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
        
        # Parse revenue
        annual_revenue = properties.get("annualrevenue", "")
        if annual_revenue:
            try:
                annual_revenue = str(annual_revenue).replace('$', '').replace(',', '')
                annual_revenue = float(annual_revenue)
            except:
                annual_revenue = None
        
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
            "Annual Revenue": annual_revenue,
            "Employee Count": properties.get("numemployees", ""),
            "Website": properties.get("website", ""),
            "Owner ID": properties.get("hubspot_owner_id", ""),
            "Created Date": created_date,
            "Last Modified Date": last_modified,
            "Has Email": 1 if properties.get("email") else 0,
            "Has Phone": 1 if properties.get("phone") else 0,
            "Has Course": 1 if course_info else 0,
            "Has Company": 1 if properties.get("company") else 0
        })
    
    df = pd.DataFrame(processed_data)
    return df

def create_metric_card(title, value, change=None, icon="📊"):
    """Create a metric card with icon and optional change indicator."""
    change_html = ""
    if change is not None:
        change_color = "#38ef7d" if change >= 0 else "#ff4b5c"
        change_symbol = "↗" if change >= 0 else "↘"
        change_html = f"""
        <div class="metric-change" style="color: {change_color};">
            {change_symbol} {abs(change):.1f}%
        </div>
        """
    
    return f"""
    <div class="metric-card">
        <div class="metric-label">{icon} {title}</div>
        <div class="metric-value">{value}</div>
        {change_html}
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
    completeness_data = {
        'Field': ['Email', 'Phone', 'Lead Status', 'Course/Program', 'Company', 'Country', 'Industry'],
        'Count': [
            df['Has Email'].sum(),
            df['Has Phone'].sum(),
            df['Lead Status'].notna().sum(),
            df['Has Course'].sum(),
            df['Has Company'].sum(),
            df['Country'].notna().sum(),
            df['Industry'].notna().sum()
        ],
        'Percentage': [
            (df['Has Email'].sum() / len(df)) * 100,
            (df['Has Phone'].sum() / len(df)) * 100,
            (df['Lead Status'].notna().sum() / len(df)) * 100,
            (df['Has Course'].sum() / len(df)) * 100,
            (df['Has Company'].sum() / len(df)) * 100,
            (df['Country'].notna().sum() / len(df)) * 100,
            (df['Industry'].notna().sum() / len(df)) * 100
        ]
    }
    analysis['completeness'] = pd.DataFrame(completeness_data)
    
    # 9. Phone Number Country Analysis
    if 'Phone' in df.columns:
        phone_analysis = analyze_phone_numbers(df)
        analysis['phone_country_analysis'] = phone_analysis
    
    return analysis

def analyze_phone_numbers(df):
    """Analyze phone numbers by country codes."""
    if 'Phone' not in df.columns:
        return pd.DataFrame()
    
    results = []
    
    for phone in df['Phone'].dropna():
        phone_str = str(phone).strip()
        country = 'Unknown'
        country_code = 'Unknown'
        
        for code, country_name in COUNTRY_CODES.items():
            if phone_str.startswith(code):
                country = country_name
                country_code = code
                break
            elif phone_str.startswith(code.replace('+', '')):
                country = country_name
                country_code = code
                break
        
        # Check for Indian numbers
        if country == 'Unknown':
            if phone_str.startswith('91') and len(phone_str) >= 12:
                country = 'India'
                country_code = '+91'
            elif phone_str.startswith('0') and (len(phone_str) == 11 or len(phone_str) == 10):
                country = 'India (Local)'
                country_code = '+91'
            elif phone_str.isdigit() and len(phone_str) == 10:
                country = 'India (10 digit)'
                country_code = '+91'
        
        results.append({
            'Phone': phone_str,
            'Country': country,
            'Country_Code': country_code
        })
    
    if results:
        analysis_df = pd.DataFrame(results)
        country_dist = analysis_df['Country'].value_counts().reset_index()
        country_dist.columns = ['Country', 'Count']
        return country_dist
    return pd.DataFrame()

def create_visualizations(analysis, df):
    """Create Plotly visualizations with modern styling."""
    visualizations = {}
    
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
                color_continuous_scale='Viridis',
                template='plotly_white'
            )
            fig1.update_layout(
                xaxis_tickangle=-45,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(size=12)
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
                color_continuous_scale='Blues',
                template='plotly_white'
            )
            fig2.update_layout(
                xaxis_tickangle=-45,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            visualizations['course_bar'] = fig2
    
    # 3. Country Distribution Bar Chart
    if 'country_distribution' in analysis:
        country_data = analysis['country_distribution'].head(15)
        if not country_data.empty:
            fig3 = px.bar(
                country_data,
                x='Country',
                y='Count',
                title='🌍 Top 15 Countries',
                color='Count',
                color_continuous_scale='Greens',
                template='plotly_white'
            )
            fig3.update_layout(
                xaxis_tickangle=-45,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            visualizations['country_bar'] = fig3
    
    # 4. Monthly Trend Line Chart
    if 'monthly_trend' in analysis:
        trend_data = analysis['monthly_trend']
        if len(trend_data) > 1:
            fig4 = px.line(
                trend_data,
                x='Month',
                y='Count',
                title='📈 Monthly Contact Creation Trend',
                markers=True,
                template='plotly_white',
                line_shape='spline'
            )
            fig4.update_traces(
                line=dict(width=3, color='#667eea'),
                marker=dict(size=8, color='#764ba2')
            )
            fig4.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            visualizations['monthly_trend'] = fig4
    
    # 5. Lead Status Donut Chart
    if 'lead_status_distribution' in analysis:
        lead_status_data = analysis['lead_status_distribution'].head(8)
        if not lead_status_data.empty:
            fig5 = px.pie(
                lead_status_data,
                values='Count',
                names='Lead Status',
                title='🎯 Lead Status Distribution',
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig5.update_traces(
                textposition='inside',
                textinfo='percent+label',
                marker=dict(line=dict(color='#fff', width=2))
            )
            fig5.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=True
            )
            visualizations['lead_status_pie'] = fig5
    
    # 6. Course Donut Chart
    if 'course_distribution' in analysis:
        course_data = analysis['course_distribution'].head(8)
        if not course_data.empty:
            fig6 = px.pie(
                course_data,
                values='Count',
                names='Course',
                title='📚 Top Course Distribution',
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig6.update_traces(
                textposition='inside',
                textinfo='percent+label',
                marker=dict(line=dict(color='#fff', width=2))
            )
            fig6.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                showlegend=True
            )
            visualizations['course_pie'] = fig6
    
    # 7. Lead Source Bar Chart
    if 'lead_source_distribution' in analysis:
        source_data = analysis['lead_source_distribution'].head(10)
        if not source_data.empty:
            fig7 = px.bar(
                source_data,
                x='Lead Source',
                y='Count',
                title='📱 Top 10 Lead Sources',
                color='Count',
                color_continuous_scale='RdYlBu',
                template='plotly_white'
            )
            fig7.update_layout(
                xaxis_tickangle=-45,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            visualizations['lead_source_bar'] = fig7
    
    # 8. Completeness Gauge Chart
    if 'completeness' in analysis:
        completeness_data = analysis['completeness']
        fig8 = go.Figure()
        
        # Add gauge for email completeness
        fig8.add_trace(go.Indicator(
            mode = "gauge+number",
            value = completeness_data[completeness_data['Field'] == 'Email']['Percentage'].values[0],
            title = {'text': "📧 Email Completeness"},
            domain = {'row': 0, 'column': 0},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "#667eea"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"},
                    {'range': [80, 100], 'color': "darkgray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        visualizations['completeness_gauge'] = fig8
    
    return visualizations

def display_quality_analysis_table(df):
    """Display enhanced quality analysis table."""
    st.markdown("### 🎯 Lead Quality Analysis Dashboard")
    
    if 'Lead Status' not in df.columns:
        st.warning("Lead Status column not found in data")
        return
    
    # Create quality analysis dataframe
    quality_data = []
    
    # Check for lead source columns
    source_col = None
    for col in ['Lead Source', 'hs_analytics_source_data_2', 'Original source drill-down 2']:
        if col in df.columns:
            source_col = col
            break
    
    if source_col:
        # Group by source
        for source in df[source_col].unique():
            if pd.isna(source) or source == '':
                continue
            
            source_df = df[df[source_col] == source]
            total_leads = len(source_df)
            
            if total_leads == 0:
                continue
            
            # Count by status
            status_counts = source_df['Lead Status'].value_counts().to_dict()
            
            # Quality categorization
            not_connected = status_counts.get('Not Connected', 0)
            not_interested = status_counts.get('Not Interested', 0)
            not_qualified = status_counts.get('Not Qualified', 0)
            cold = status_counts.get('Cold', 0)
            duplicate = status_counts.get('Duplicate', 0)
            warm = status_counts.get('Warm', 0)
            hot = status_counts.get('Hot', 0)
            future_prospect = status_counts.get('Future Prospect', 0)
            
            # Calculate metrics
            low_quality = not_interested + not_qualified
            good_quality = warm + hot + future_prospect
            neutral_quality = cold
            
            low_quality_pct = (low_quality / total_leads * 100) if total_leads > 0 else 0
            good_quality_pct = (good_quality / total_leads * 100) if total_leads > 0 else 0
            neutral_quality_pct = (neutral_quality / total_leads * 100) if total_leads > 0 else 0
            
            # Determine quality score
            quality_score = (good_quality_pct * 0.7) - (low_quality_pct * 0.3)
            
            quality_data.append({
                'Lead Source': str(source)[:30],
                'Total Leads': total_leads,
                'Not Connected': not_connected,
                'Not Interested': not_interested,
                'Not Qualified': not_qualified,
                'Cold': cold,
                'Duplicate': duplicate,
                'Warm': warm,
                'Hot': hot,
                'Future Prospect': future_prospect,
                'Low Quality %': low_quality_pct,
                'Good Quality %': good_quality_pct,
                'Neutral Quality %': neutral_quality_pct,
                'Quality Score': quality_score
            })
    
    if quality_data:
        quality_df = pd.DataFrame(quality_data)
        quality_df = quality_df.sort_values('Quality Score', ascending=False)
        
        # Display with custom styling
        st.dataframe(
            quality_df.style.background_gradient(
                subset=['Low Quality %'], 
                cmap='RdYlGn_r'
            ).background_gradient(
                subset=['Good Quality %'], 
                cmap='RdYlGn'
            ).background_gradient(
                subset=['Quality Score'], 
                cmap='RdYlGn'
            ).format({
                'Low Quality %': '{:.1f}%',
                'Good Quality %': '{:.1f}%',
                'Neutral Quality %': '{:.1f}%',
                'Quality Score': '{:.1f}'
            }),
            use_container_width=True,
            height=400
        )
        
        # Summary metrics
        st.markdown("#### 📊 Quality Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_low_quality = quality_df['Low Quality %'].mean()
            st.metric("Avg Low Quality %", f"{avg_low_quality:.1f}%")
        
        with col2:
            avg_good_quality = quality_df['Good Quality %'].mean()
            st.metric("Avg Good Quality %", f"{avg_good_quality:.1f}%")
        
        with col3:
            high_risk_sources = (quality_df['Low Quality %'] > 40).sum()
            st.metric("High Risk Sources (>40%)", high_risk_sources)
        
        with col4:
            best_source = quality_df.iloc[0]['Lead Source']
            best_score = quality_df.iloc[0]['Quality Score']
            st.metric("Best Source", best_source[:15], delta=f"Score: {best_score:.1f}")
    else:
        st.info("No lead source data available for quality analysis")

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
    # Modern header with gradient
    st.markdown("""
    <div class="dashboard-header">
        <h1 style="margin: 0; color: white;">HubSpot Contacts Analytics Dashboard</h1>
        <p style="margin: 0.5rem 0 0 0; color: rgba(255,255,255,0.9); font-size: 1.2rem;">
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
    if 'date_filter' not in st.session_state:
        st.session_state.date_filter = {
            'field': 'Created Date',
            'start': (datetime.now(IST).date() - timedelta(days=51)),
            'end': datetime.now(IST).date()
        }
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem;">
            <h2 style="color: white;">🔧 Configuration</h2>
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
                                
                                visualizations = create_visualizations(analysis_results, df)
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
            if st.button("🔄 Refresh", use_container_width=True):
                if 'contacts_df' in st.session_state:
                    df = st.session_state.contacts_df
                    if df is not None and not df.empty:
                        analysis_results = analyze_contact_data(df)
                        st.session_state.analysis_results = analysis_results
                        
                        visualizations = create_visualizations(analysis_results, df)
                        st.session_state.visualizations = visualizations
                        
                        email_validation = analyze_email_validation(df)
                        st.session_state.email_validation = email_validation
                        
                        st.success("Analysis refreshed!")
                        st.rerun()
        
        if st.button("🗑️ Clear Data", use_container_width=True):
            st.session_state.clear()
            st.rerun()
        
        st.divider()
        
        # Info section
        st.markdown("### 📊 About")
        st.markdown("""
        <div style="color: white; font-size: 0.9rem;">
        This dashboard provides comprehensive analytics for HubSpot contacts including:
        • Lead status distribution
        • Course/program analysis
        • Prospect reasons insights
        • Contact quality metrics
        • Geographic analysis
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
        
        # Key Metrics Row
        st.markdown("## 📈 Key Performance Indicators")
        
        # Create metrics cards
        metric_cols = st.columns(4)
        
        with metric_cols[0]:
            total_contacts = len(df)
            st.markdown(create_metric_card(
                "Total Contacts", 
                f"{total_contacts:,}",
                change=None,
                icon="👥"
            ), unsafe_allow_html=True)
        
        with metric_cols[1]:
            email_count = df['Has Email'].sum()
            email_percent = (email_count / total_contacts * 100) if total_contacts > 0 else 0
            st.markdown(create_metric_card(
                "Email Coverage",
                f"{email_percent:.0f}%",
                change=None,
                icon="📧"
            ), unsafe_allow_html=True)
        
        with metric_cols[2]:
            course_count = df['Has Course'].sum()
            course_percent = (course_count / total_contacts * 100) if total_contacts > 0 else 0
            st.markdown(create_metric_card(
                "With Course",
                f"{course_percent:.0f}%",
                change=None,
                icon="📚"
            ), unsafe_allow_html=True)
        
        with metric_cols[3]:
            phone_count = df['Has Phone'].sum()
            phone_percent = (phone_count / total_contacts * 100) if total_contacts > 0 else 0
            st.markdown(create_metric_card(
                "Phone Coverage",
                f"{phone_percent:.0f}%",
                change=None,
                icon="📱"
            ), unsafe_allow_html=True)
        
        st.divider()
        
        # Create tabs for different sections
        tab_titles = [
            "🎯 Quality Dashboard", 
            "📊 Lead Analytics", 
            "📚 Course Insights",
            "🌍 Geographic View", 
            "📧 Data Quality",
            "📥 Export & Reports"
        ]
        
        tabs = st.tabs(tab_titles)
        
        with tabs[0]:  # Quality Dashboard
            st.markdown("### 🎯 Lead Quality & Source Analysis")
            display_quality_analysis_table(df)
            
            # Additional quality metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📈 Quality Distribution")
                if 'lead_status_distribution' in st.session_state.analysis_results:
                    lead_data = st.session_state.analysis_results['lead_status_distribution']
                    if not lead_data.empty:
                        fig = px.pie(
                            lead_data.head(5),
                            values='Count',
                            names='Lead Status',
                            title='Top 5 Lead Statuses',
                            hole=0.4,
                            color_discrete_sequence=['#667eea', '#764ba2', '#38ef7d', '#ff9a00', '#ff4b5c']
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### 📊 Source Performance")
                if 'lead_source_distribution' in st.session_state.analysis_results:
                    source_data = st.session_state.analysis_results['lead_source_distribution'].head(5)
                    if not source_data.empty:
                        fig = px.bar(
                            source_data,
                            x='Lead Source',
                            y='Count',
                            title='Top 5 Lead Sources',
                            color='Count',
                            color_continuous_scale='Viridis'
                        )
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
        
        with tabs[1]:  # Lead Analytics
            st.markdown("### 📊 Comprehensive Lead Analysis")
            
            if st.session_state.visualizations:
                visuals = st.session_state.visualizations
                
                # Row 1: Lead Status Charts
                col1, col2 = st.columns(2)
                
                with col1:
                    if 'lead_status_bar' in visuals:
                        st.plotly_chart(visuals['lead_status_bar'], use_container_width=True)
                
                with col2:
                    if 'lead_status_pie' in visuals:
                        st.plotly_chart(visuals['lead_status_pie'], use_container_width=True)
                
                # Row 2: Monthly Trend
                col3, col4 = st.columns(2)
                
                with col3:
                    if 'monthly_trend' in visuals:
                        st.plotly_chart(visuals['monthly_trend'], use_container_width=True)
                
                with col4:
                    if 'lead_source_bar' in visuals:
                        st.plotly_chart(visuals['lead_source_bar'], use_container_width=True)
                
                # Prospect Reasons Analysis
                st.markdown("### 🎯 Prospect Reasons Analysis")
                
                if 'prospect_reasons' in st.session_state.analysis_results:
                    prospect_reasons = st.session_state.analysis_results['prospect_reasons']
                    
                    if prospect_reasons:
                        reason_tabs = st.tabs(list(prospect_reasons.keys())[:4])
                        
                        for i, (reason_type, reason_data) in enumerate(list(prospect_reasons.items())[:4]):
                            with reason_tabs[i]:
                                if not reason_data.empty:
                                    st.dataframe(reason_data, use_container_width=True, height=200)
                                    
                                    # Chart for top reasons
                                    top_reasons = reason_data.head(10)
                                    fig = px.bar(
                                        top_reasons,
                                        x='Reason',
                                        y='Count',
                                        title=f"Top 10 - {reason_type}",
                                        color='Count',
                                        color_continuous_scale='Viridis'
                                    )
                                    fig.update_layout(xaxis_tickangle=-45, height=300)
                                    st.plotly_chart(fig, use_container_width=True)
        
        with tabs[2]:  # Course Insights
            st.markdown("### 📚 Course & Program Analysis")
            
            if 'course_distribution' in st.session_state.analysis_results:
                course_data = st.session_state.analysis_results['course_distribution']
                
                if not course_data.empty:
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown("#### 📋 Course Distribution")
                        st.dataframe(course_data, use_container_width=True, height=400)
                    
                    with col2:
                        st.markdown("#### 📊 Top Courses")
                        top_courses = course_data.head(5)
                        for idx, row in top_courses.iterrows():
                            course_name = row['Course'][:25] + "..." if len(row['Course']) > 25 else row['Course']
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); 
                                        padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
                                <div style="font-weight: 600; color: #2c3e50;">{course_name}</div>
                                <div style="color: #667eea; font-size: 1.5rem; font-weight: 800;">{row['Count']}</div>
                                <div style="color: #7f8c8d; font-size: 0.8rem;">contacts</div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Course charts
                    col3, col4 = st.columns(2)
                    
                    with col3:
                        if 'course_bar' in st.session_state.visualizations:
                            st.plotly_chart(st.session_state.visualizations['course_bar'], use_container_width=True)
                    
                    with col4:
                        if 'course_pie' in st.session_state.visualizations:
                            st.plotly_chart(st.session_state.visualizations['course_pie'], use_container_width=True)
                else:
                    st.info("No course/program data available")
        
        with tabs[3]:  # Geographic View
            st.markdown("### 🌍 Geographic Distribution")
            
            if 'country_distribution' in st.session_state.analysis_results:
                country_data = st.session_state.analysis_results['country_distribution']
                
                # Create map
                fig = px.choropleth(
                    country_data,
                    locations='Country',
                    locationmode='country names',
                    color='Count',
                    hover_name='Country',
                    title='🌍 Contact Distribution by Country',
                    color_continuous_scale='Viridis',
                    template='plotly_white'
                )
                fig.update_layout(
                    geo=dict(
                        showframe=False,
                        showcoastlines=True,
                        projection_type='equirectangular'
                    ),
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Country data table
                st.markdown("#### 📋 Country Statistics")
                st.dataframe(country_data, use_container_width=True, height=300)
        
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
                            st.metric(issue[:20], count)
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
        
        with tabs[5]:  # Export & Reports
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
                
                with export_row2[2]:
                    if 'prospect_reasons' in st.session_state.analysis_results:
                        all_reasons = pd.DataFrame()
                        for reason_type, reason_data in st.session_state.analysis_results['prospect_reasons'].items():
                            reason_data['Reason_Type'] = reason_type
                            all_reasons = pd.concat([all_reasons, reason_data])
                        
                        if not all_reasons.empty:
                            csv = all_reasons.to_csv(index=False)
                            st.download_button(
                                "🎯 All Prospect Reasons",
                                csv,
                                "all_prospect_reasons.csv",
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
        # Welcome screen with modern design
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 4rem; margin-bottom: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;">📊</div>
            <h2 class="gradient-text" style="margin-bottom: 1rem;">Welcome to HubSpot Analytics Dashboard</h2>
            <p style="color: #7f8c8d; font-size: 1.1rem; margin-bottom: 2rem;">
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
                <h3>Lead Quality Analysis</h3>
                <p>Analyze lead status distribution and quality metrics with detailed insights</p>
            </div>
            """, unsafe_allow_html=True)
        
        with feature_cols[1]:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">📚</div>
                <h3>Course Insights</h3>
                <p>Track course/program distribution and performance across all contacts</p>
            </div>
            """, unsafe_allow_html=True)
        
        with feature_cols[2]:
            st.markdown("""
            <div class="feature-card">
                <div class="feature-icon">🌍</div>
                <h3>Geographic Analysis</h3>
                <p>Visualize contact distribution by country with interactive maps</p>
            </div>
            """, unsafe_allow_html=True)
        
        # How to get started
        st.markdown("---")
        st.markdown("""
        <div class="info-container">
            <h3>📋 How to Get Started</h3>
            <ol>
                <li><strong>Configure Date Range</strong> - Select your date filters in the sidebar</li>
                <li><strong>Test Connection</strong> - Verify your HubSpot API connection</li>
                <li><strong>Fetch Data</strong> - Click "Fetch ALL" to load your contacts</li>
                <li><strong>Analyze</strong> - Explore the 6 comprehensive analysis tabs</li>
                <li><strong>Export</strong> - Download reports in CSV or Excel format</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
