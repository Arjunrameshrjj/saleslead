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
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1a1a1a;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #666;
        margin-bottom: 1rem;
    }
    .stats-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff7a59;
        margin-bottom: 1rem;
    }
    .date-info {
        background-color: #e8f4fd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.9rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
    }
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 0.5rem;
        color: white;
        margin-bottom: 2rem;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        border: 1px solid #ffeaa7;
    }
    .reason-tab {
        background-color: #f8f9fa;
        padding: 0.5rem;
        border-radius: 0.3rem;
        margin: 0.2rem 0;
    }
    .course-badge {
        background-color: #e3f2fd;
        color: #1565c0;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-size: 0.9rem;
        display: inline-block;
        margin: 0.2rem;
    }
    .quality-high-red {
        background-color: #f8d7da !important;
        color: #721c24 !important;
        font-weight: bold;
    }
    .quality-high-green {
        background-color: #d4edda !important;
        color: #155724 !important;
        font-weight: bold;
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

# 🔥 FINAL LEAD STATUS MAPPING (FORCE MERGE OLD → NEW)
LEAD_STATUS_MAP = {
    # ✅ ACTIVE STATUSES (CURRENT IN UI)
    "cold": "Cold",
    "warm": "Warm", 
    "hot": "Hot",
    "new": "New Lead",
    "open": "New Lead",
    
    # 🔥 CRITICAL: FORCE MERGE OLD VALUES TO NEW (FIXES YOUR ISSUE!)
    "neutral_prospect": "Cold",      # Old → Cold
    "prospect": "Warm",              # Old → Warm  
    "hot_prospect": "Hot",           # Old → Hot
    
    # ❌ DISQUALIFIED STATUSES
    "not_connected": "Not Connected (NC)",
    "not_interested": "Not Interested", 
    "unqualified": "Not Qualified",
    "not_qualified": "Not Qualified",
    
    # 👤 CUSTOMER / DUPLICATE
    "customer": "Customer",
    "duplicate": "Duplicate",
    "junk": "Duplicate",
    
    # 🎯 CATCH ALL UNKNOWN
    "": "Unknown",
    None: "Unknown",
    "unknown": "Unknown",
    "other": "Unknown"
}

# 🔥 PROSPECT REASONS MAPPING (FORCE MERGE)
PROSPECT_REASON_MAP = {
    # 🔥 HOT STATUS MAPPING
    "hot_prospect": "Hot",
    "hot": "Hot",
    "urgent": "Hot",
    
    # 🔥 WARM STATUS MAPPING  
    "warm_prospect": "Warm",
    "prospect": "Warm",
    "interested": "Warm",
    "follow_up": "Warm",
    
    # 🔥 COLD STATUS MAPPING
    "cold_prospect": "Cold", 
    "neutral_prospect": "Cold",
    "neutral": "Cold",
    "future_prospect": "Cold",
    
    # ❌ DISQUALIFIED REASONS
    "not_connected": "Not Connected",
    "not_interested": "Not Interested",
    "no_interest": "Not Interested",
    "unqualified": "Not Qualified",
    "not_qualified": "Not Qualified",
    
    # 📞 CONTACT REASONS
    "call_back_later": "Call Back Later",
    "callback": "Call Back Later",
    "follow_up_later": "Call Back Later",
    
    # 💰 PRICE/BUDGET
    "price_issue": "Price Issue",
    "budget_issue": "Budget Issue",
    "too_expensive": "Price Issue",
    
    # 🏢 BUSINESS REASONS
    "no_requirement": "No Requirement",
    "no_need": "No Requirement",
    "competitor": "Competitor",
    "using_competitor": "Competitor",
    
    # 📋 GENERAL
    "demo_requested": "Demo Requested",
    "quote_requested": "Quote Requested",
    "info_requested": "Information Requested",
    "trial_requested": "Trial Requested",
    
    # Fallback: Clean up any remaining values
    "": "",
    None: ""
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
    
    # Try a simple API endpoint
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
    
    # Create datetime at start or end of day
    if is_end_date:
        dt = datetime.combine(date_obj, datetime.max.time())
    else:
        dt = datetime.combine(date_obj, datetime.min.time())
    
    # Localize to IST and convert to UTC timestamp
    dt_ist = IST.localize(dt)
    dt_utc = dt_ist.astimezone(pytz.UTC)
    
    # Convert to milliseconds
    return int(dt_utc.timestamp() * 1000)

def fetch_hubspot_contacts_with_date_filter(api_key, date_field, start_date, end_date):
    """Fetch ALL contacts from HubSpot with server-side date filtering - NO LIMIT."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Convert dates to timestamps
    start_timestamp = date_to_hubspot_timestamp(start_date, is_end_date=False)
    
    # IMPORTANT: Add one day to end date for safe boundary to ensure we get all records
    safe_end_date = end_date + timedelta(days=1)
    end_timestamp = date_to_hubspot_timestamp(safe_end_date, is_end_date=False)
    
    all_contacts = []
    after = None
    page_count = 0
    
    # Build filter groups based on selected date field
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
    else:  # Both - created OR modified in date range
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
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.text(f"📡 Fetching ALL contacts with {date_field} filter from {start_date} to {end_date}...")
    
    # IMPORTANT: Define ALL properties including course/program related
    all_properties = [
        # Lead status and basic info
        "hs_lead_status", "lifecyclestage", "hubspot_owner_id",
        
        # Prospect reason properties
        "future_prospect_reasons", "hot_prospect_reason", 
        "neutral_prospect_reasons", "not_connected_reasons",
        "not_interested_reasons", "prospect_reasons",
        "other_enquiry_reasons", "lead_status",
        
        # Course/Program related properties
        "course", "program", "product", "service", "offering",
        "course_name", "program_name", "product_name",
        "enquired_course", "interested_course", "course_interested",
        "program_of_interest", "course_of_interest", "product_of_interest",
        "service_of_interest", "training_program", "educational_program",
        "learning_program", "certification_program",
        
        # Additional reason fields
        "contact_reason", "reason_for_contact", "enquiry_reason",
        "disqualification_reason", "conversion_reason",
        
        # Standard contact properties
        "firstname", "lastname", "email", "phone", 
        "createdate", "lastmodifieddate", "hs_object_id",
        "company", "jobtitle", "country", "state", "city",
        "industry", "annualrevenue", "numemployees",
        "website", "mobilephone", "address"
    ]
    
    try:
        while True:  # Infinite loop - will break when no more pages
            # Prepare request body
            body = {
                "filterGroups": filter_groups,
                "properties": all_properties,
                "limit": 100,  # Max per API call
                "sorts": [{
                    "propertyName": "createdate" if date_field == "Created Date" else "lastmodifieddate",
                    "direction": "ASCENDING"
                }]
            }
            
            if after:
                body["after"] = after
            
            response = requests.post(url, headers=headers, json=body, timeout=30)
            
            # Check for rate limiting
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
                
                # Update progress and status
                if page_count <= 10:
                    progress = page_count / 10
                else:
                    progress = 0.9 + (page_count / 100)
                
                if progress > 0.99:
                    progress = 0.99
                
                progress_bar.progress(progress)
                status_text.text(f"📥 Fetched {len(all_contacts)} contacts (Page {page_count})...")
                
                # Check for next page
                paging_info = data.get("paging", {})
                after = paging_info.get("next", {}).get("after")
                
                # CRITICAL: Only break if no more pages
                if not after:
                    status_text.text(f"✅ No more pages. Total: {len(all_contacts)} contacts")
                    break  # No more pages
                
                # Small delay to avoid rate limiting
                time.sleep(0.2)
            else:
                status_text.text(f"✅ No more results. Total: {len(all_contacts)} contacts")
                break  # No results
        
        progress_bar.progress(1.0)
        status_text.text(f"✅ Fetch complete! Total: {len(all_contacts)} contacts")
        
        return all_contacts, len(all_contacts)
        
    except requests.exceptions.RequestException as e:
        progress_bar.empty()
        status_text.empty()
        
        st.error(f"❌ Error fetching data: {e}")
        return [], 0
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Unexpected error: {e}")
        return [], 0

def normalize_lead_status(raw_status):
    """
    🔥 AGGRESSIVELY normalize lead status - ensures consistent grouping
    This is the KEY FUNCTION that fixes your count issue
    """
    if not raw_status:
        return "Unknown"
    
    status = str(raw_status).strip().lower()
    
    # 🔥 FORCE MERGE OLD VALUES (THIS IS THE FIX!)
    # Group all prospect types to new categories
    if "prospect" in status:
        if "hot" in status or "urgent" in status:
            return "Hot"
        elif "warm" in status or "interested" in status:
            return "Warm"
        elif "neutral" in status or "cold" in status or "future" in status:
            return "Cold"
        else:
            return "Warm"  # Default prospect to Warm
    
    # Group all not-connected variations
    if "not_connect" in status or "nc" in status.lower() or "no_connect" in status:
        return "Not Connected (NC)"
    
    # Group all not-interested variations
    if "not_interest" in status or "no_interest" in status or "disinterest" in status:
        return "Not Interested"
    
    # Group all not-qualified variations
    if "not_qualif" in status or "unqualif" in status or "disqualif" in status:
        return "Not Qualified"
    
    # Group all duplicate variations
    if "duplicate" in status or "junk" in status or "spam" in status:
        return "Duplicate"
    
    # Group all customer variations
    if "customer" in status or "client" in status or "converted" in status:
        return "Customer"
    
    # Group all new lead variations
    if "new" in status or "open" in status or "fresh" in status:
        return "New Lead"
    
    # Direct mapping
    if status in LEAD_STATUS_MAP:
        return LEAD_STATUS_MAP[status]
    
    # Final fallback with title case
    return status.replace("_", " ").title()

def map_prospect_reason(reason):
    """Map prospect reason with aggressive cleaning"""
    if not reason:
        return ""
    
    reason_str = str(reason).strip().lower()
    
    # First, check exact match
    if reason_str in PROSPECT_REASON_MAP:
        return PROSPECT_REASON_MAP[reason_str]
    
    # Check for partial matches
    for key, value in PROSPECT_REASON_MAP.items():
        if key in reason_str:
            return value
    
    # Clean up special characters and format
    cleaned = reason_str.replace("_", " ").replace("-", " ").title()
    return cleaned

def process_contacts_data(contacts):
    """Process raw contacts data into a clean DataFrame with correct normalization."""
    if not contacts:
        return pd.DataFrame()
    
    processed_data = []
    
    for contact in contacts:
        properties = contact.get("properties", {})
        
        # Format dates if they exist
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
        
        # Parse revenue if exists
        annual_revenue = properties.get("annualrevenue", "")
        if annual_revenue:
            try:
                annual_revenue = str(annual_revenue).replace('$', '').replace(',', '')
                annual_revenue = float(annual_revenue)
            except:
                annual_revenue = None
        
        # Parse employee count
        employee_count = properties.get("numemployees", "")
        if employee_count:
            try:
                employee_count = int(employee_count)
            except:
                employee_count = None
        
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
        
        # 🔥 ULTIMATE FIX: Normalize lead status
        raw_lead_status = properties.get("hs_lead_status", "") or properties.get("lead_status", "")
        display_lead_status = normalize_lead_status(raw_lead_status)
        
        # Process each contact
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
            
            # 🔥 NORMALIZED LEAD STATUS (CORRECT!)
            "Lead Status": display_lead_status,
            "Lifecycle Stage": properties.get("lifecyclestage", ""),
            
            # 🔥 NORMALIZED PROSPECT REASONS (CORRECT!)
            "Future Prospect Reasons": map_prospect_reason(properties.get("future_prospect_reasons", "") or properties.get("future_prospect_reason", "")),
            "Hot Prospect Reason": map_prospect_reason(properties.get("hot_prospect_reason", "")),
            "Neutral Prospect Reasons": map_prospect_reason(properties.get("neutral_prospect_reasons", "")),
            "Not Connected Reasons": map_prospect_reason(properties.get("not_connected_reasons", "")),
            "Not Interested Reasons": map_prospect_reason(properties.get("not_interested_reasons", "")),
            "Other Enquiry Reasons": map_prospect_reason(properties.get("other_enquiry_reasons", "")),
            "Prospect Reasons": map_prospect_reason(properties.get("prospect_reasons", "")),
            
            # Additional reason fields
            "Contact Reason": map_prospect_reason(properties.get("contact_reason", "")),
            "Reason for Contact": map_prospect_reason(properties.get("reason_for_contact", "")),
            "Enquiry Reason": map_prospect_reason(properties.get("enquiry_reason", "")),
            "Disqualification Reason": map_prospect_reason(properties.get("disqualification_reason", "")),
            "Conversion Reason": map_prospect_reason(properties.get("conversion_reason", "")),
            
            # Other contact info
            "Country": properties.get("country", ""),
            "State": properties.get("state", ""),
            "City": properties.get("city", ""),
            "Industry": properties.get("industry", ""),
            "Annual Revenue": annual_revenue,
            "Employee Count": employee_count,
            "Website": properties.get("website", ""),
            "Owner ID": properties.get("hubspot_owner_id", ""),
            "Created Date": created_date,
            "Last Modified Date": last_modified,
            "Has Email": 1 if properties.get("email") else 0,
            "Has Phone": 1 if properties.get("phone") else 0,
            "Has Course": 1 if course_info else 0,
            
            # 🔥 STORE RAW VALUE FOR DEBUGGING
            "Lead Status Raw": raw_lead_status
        })
    
    df = pd.DataFrame(processed_data)
    return df

def build_course_quality_table(df):
    """
    🎯 BUILD COURSE QUALITY TABLE (PIVOT STYLE)
    Creates a matrix showing course-wise lead status distribution with quality metrics
    """
    # Keep only records with course info
    df_with_course = df[df['Course/Program'].notna() & (df['Course/Program'] != '')].copy()
    
    if df_with_course.empty:
        return pd.DataFrame()
    
    # Clean course names
    df_with_course['Course_Clean'] = df_with_course['Course/Program'].str.strip()
    
    # Create pivot table: Course × Lead Status
    pivot = pd.pivot_table(
        df_with_course,
        index='Course_Clean',
        columns='Lead Status',
        values='ID',
        aggfunc='count',
        fill_value=0
    )
    
    # Reset index to make Course_Clean a column
    pivot = pivot.reset_index()
    
    # Rename columns for consistency
    pivot = pivot.rename(columns={'Course_Clean': 'Course/Program'})
    
    # Define required columns in specific order
    required_columns = [
        'Course/Program',
        'Not Connected (NC)', 
        'Not Interested', 
        'Not Qualified',
        'Cold', 
        'Duplicate', 
        'Warm', 
        'Hot', 
        'Future Prospect',
        'Customer',
        'New Lead'
    ]
    
    # Add missing columns with 0 values
    for col in required_columns:
        if col not in pivot.columns:
            pivot[col] = 0
    
    # Reorder columns
    pivot = pivot[required_columns]
    
    # Calculate Quality Metrics
    pivot['Low Quality Leads'] = pivot['Not Interested'] + pivot['Not Qualified']
    pivot['Good Quality Leads'] = pivot['Cold'] + pivot['Warm'] + pivot['Hot']
    
    # Calculate Grand Total (sum of all lead status columns)
    status_columns = [col for col in required_columns if col != 'Course/Program']
    pivot['Grand Total'] = pivot[status_columns].sum(axis=1)
    
    # Calculate percentages
    pivot['Low Quality %'] = (pivot['Low Quality Leads'] / pivot['Grand Total'] * 100).round(1)
    pivot['Good Quality %'] = (pivot['Good Quality Leads'] / pivot['Grand Total'] * 100).round(1)
    
    # Sort by Grand Total descending
    pivot = pivot.sort_values('Grand Total', ascending=False)
    
    return pivot

def analyze_lead_status_distribution(df):
    """Analyze lead status distribution - with CORRECT normalization."""
    if 'Lead Status' not in df.columns:
        return pd.DataFrame()
    
    # 🔥 Use normalized lead status (already cleaned)
    lead_status_dist = df['Lead Status'].value_counts().reset_index()
    lead_status_dist.columns = ['Lead Status', 'Count']
    
    # Sort by count (descending)
    lead_status_dist = lead_status_dist.sort_values('Count', ascending=False)
    
    # Add "Grand Total" row at the end
    grand_total = lead_status_dist['Count'].sum()
    total_row = pd.DataFrame({'Lead Status': ['Grand Total'], 'Count': [grand_total]})
    lead_status_dist = pd.concat([lead_status_dist, total_row], ignore_index=True)
    
    return lead_status_dist

def analyze_course_distribution(df):
    """Analyze course/program distribution with count."""
    if 'Course/Program' not in df.columns:
        return pd.DataFrame()
    
    # Clean course data
    df['Course_Clean'] = df['Course/Program'].fillna('').astype(str).str.strip()
    
    # Remove empty values
    courses_with_data = df[df['Course_Clean'] != '']
    
    if courses_with_data.empty:
        return pd.DataFrame()
    
    # Count distribution
    course_dist = courses_with_data['Course_Clean'].value_counts().reset_index()
    course_dist.columns = ['Course', 'Count']
    
    # Sort by count (descending)
    course_dist = course_dist.sort_values('Count', ascending=False)
    
    return course_dist

def analyze_prospect_reasons(df):
    """Analyze all prospect reasons - with CORRECT mapping."""
    # Define all prospect reason columns
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
    
    # Find which columns actually exist in the dataframe
    available_columns = [col for col in prospect_columns if col in df.columns]
    
    results = {}
    
    for column in available_columns:
        # Clean the data
        df[column] = df[column].fillna('').astype(str).str.strip()
        
        # Remove empty values
        non_empty = df[df[column] != ''][column]
        
        if not non_empty.empty:
            # Count distribution
            reason_dist = non_empty.value_counts().reset_index()
            reason_dist.columns = ['Reason', 'Count']
            reason_dist = reason_dist.sort_values('Count', ascending=False)
            
            results[column] = reason_dist
    
    return results

def analyze_contact_data(df):
    """Perform comprehensive analysis on contacts data."""
    analysis = {}
    
    if df.empty:
        return analysis
    
    # 1. Lead Status Distribution - WITH CORRECT NORMALIZATION
    lead_status_dist = analyze_lead_status_distribution(df)
    if not lead_status_dist.empty:
        analysis['lead_status_distribution'] = lead_status_dist
    
    # 2. Course Distribution
    course_dist = analyze_course_distribution(df)
    if not course_dist.empty:
        analysis['course_distribution'] = course_dist
    
    # 3. Prospect Reasons Analysis
    prospect_reasons = analyze_prospect_reasons(df)
    if prospect_reasons:
        analysis['prospect_reasons'] = prospect_reasons
    
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
    
    # 6. Lifecycle Stage Analysis
    if 'Lifecycle Stage' in df.columns:
        stage_dist = df['Lifecycle Stage'].value_counts().reset_index()
        stage_dist.columns = ['Lifecycle Stage', 'Count']
        analysis['stage_distribution'] = stage_dist
    
    # 7. Creation Date Trend (Monthly)
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
        'Field': ['Email', 'Phone', 'Lead Status', 'Course/Program', 'Country', 'Industry'],
        'Count': [
            df['Email'].notna().sum(),
            df['Phone'].notna().sum(),
            df['Lead Status'].notna().sum(),
            df['Has Course'].sum(),
            df['Country'].notna().sum(),
            df['Industry'].notna().sum()
        ],
        'Percentage': [
            (df['Email'].notna().sum() / len(df)) * 100,
            (df['Phone'].notna().sum() / len(df)) * 100,
            (df['Lead Status'].notna().sum() / len(df)) * 100,
            (df['Has Course'].sum() / len(df)) * 100,
            (df['Country'].notna().sum() / len(df)) * 100,
            (df['Industry'].notna().sum() / len(df)) * 100
        ]
    }
    analysis['completeness'] = pd.DataFrame(completeness_data)
    
    # 9. Phone Number Country Analysis
    if 'Phone' in df.columns:
        phone_analysis = analyze_phone_numbers(df)
        analysis['phone_country_analysis'] = phone_analysis
    
    # 10. 🔥 NEW: Course Quality Analysis
    course_quality = build_course_quality_table(df)
    if not course_quality.empty:
        analysis['course_quality'] = course_quality
    
    # 11. DEBUG: Raw vs Normalized mapping
    if 'Lead Status Raw' in df.columns:
        debug_data = df[['Lead Status', 'Lead Status Raw']].copy()
        debug_data = debug_data.groupby(['Lead Status', 'Lead Status Raw']).size().reset_index(name='Count')
        debug_data = debug_data.sort_values('Count', ascending=False)
        analysis['debug_mapping'] = debug_data.head(20)
    
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

def create_visualizations(analysis, df):
    """Create Plotly visualizations."""
    visualizations = {}
    
    # 1. Lead Status Bar Chart (Top 10 - Excluding Grand Total)
    if 'lead_status_distribution' in analysis:
        lead_status_data = analysis['lead_status_distribution']
        # Exclude "Grand Total" from chart
        lead_status_chart_data = lead_status_data[lead_status_data['Lead Status'] != 'Grand Total'].head(10)
        if not lead_status_chart_data.empty:
            fig1 = px.bar(
                lead_status_chart_data,
                x='Lead Status',
                y='Count',
                title='Top 10 Lead Statuses',
                color='Count',
                color_continuous_scale='Viridis'
            )
            fig1.update_layout(xaxis_tickangle=-45)
            visualizations['lead_status_bar'] = fig1
    
    # 2. Course Distribution Bar Chart (Top 10)
    if 'course_distribution' in analysis:
        course_data = analysis['course_distribution'].head(10)
        if not course_data.empty:
            fig2 = px.bar(
                course_data,
                x='Course',
                y='Count',
                title='Top 10 Courses/Programs',
                color='Count',
                color_continuous_scale='Blues'
            )
            fig2.update_layout(xaxis_tickangle=-45)
            visualizations['course_bar'] = fig2
    
    # 3. Country Bar Chart (Top 15)
    if 'country_distribution' in analysis:
        country_data = analysis['country_distribution'].head(15)
        if not country_data.empty:
            fig3 = px.bar(
                country_data,
                x='Country',
                y='Count',
                title='Top 15 Countries',
                color='Count',
                color_continuous_scale='Greens'
            )
            fig3.update_layout(xaxis_tickangle=-45)
            visualizations['country_bar'] = fig3
    
    # 4. Monthly Trend Line Chart
    if 'monthly_trend' in analysis:
        trend_data = analysis['monthly_trend']
        if len(trend_data) > 1:
            fig4 = px.line(
                trend_data,
                x='Month',
                y='Count',
                title='Monthly Contact Creation Trend',
                markers=True
            )
            fig4.update_traces(line=dict(width=3))
            visualizations['monthly_trend'] = fig4
    
    # 5. Lead Status Pie Chart
    if 'lead_status_distribution' in analysis:
        lead_status_data = analysis['lead_status_distribution']
        # Exclude "Grand Total" from pie chart
        lead_status_pie_data = lead_status_data[lead_status_data['Lead Status'] != 'Grand Total'].head(8)
        if not lead_status_pie_data.empty:
            fig5 = px.pie(
                lead_status_pie_data,
                values='Count',
                names='Lead Status',
                title='Lead Status Distribution',
                hole=0.3,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig5.update_traces(textposition='inside', textinfo='percent+label')
            visualizations['lead_status_pie'] = fig5
    
    # 6. Course Pie Chart
    if 'course_distribution' in analysis:
        course_data = analysis['course_distribution'].head(8)
        if not course_data.empty:
            fig6 = px.pie(
                course_data,
                values='Count',
                names='Course',
                title='Top Course Distribution',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig6.update_traces(textposition='inside', textinfo='percent+label')
            visualizations['course_pie'] = fig6
    
    return visualizations

def main():
    # Header with gradient
    st.markdown(
        """
        <div class="header-container">
            <h1 style="margin: 0; font-size: 2.5rem;">📊 HubSpot Contacts Analytics Dashboard</h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem; opacity: 0.9;">Advanced Analytics & Insights for Your HubSpot Contacts</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Initialize session state
    if 'contacts_df' not in st.session_state:
        st.session_state.contacts_df = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'visualizations' not in st.session_state:
        st.session_state.visualizations = None
    if 'email_validation' not in st.session_state:
        st.session_state.email_validation = None
    
    # Create two columns for main layout
    col1, col2 = st.columns([3, 1])
    
    with col2:  # Sidebar-like configuration
        st.markdown("## 🔧 Configuration")
        
        # Test connection button - uses hidden API key
        if st.button("🔗 Test API Connection", use_container_width=True):
            is_valid, message = test_hubspot_connection(HUBSPOT_API_KEY)
            if is_valid:
                st.success(message)
            else:
                st.error(message)
        
        st.divider()
        
        # Date Filter Section
        st.markdown("## 📅 Date Range Filter")
        
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
        st.info(f"📅 Will fetch ALL contacts from {days_diff} day(s)")
        
        st.markdown(
            """
            <div class="warning-box">
                ⚠️ <strong>Note:</strong> This fetches ALL data including:<br>
                • Lead Status & Prospect Reasons<br>
                • Course/Program Information<br>
                • Contact details & Analytics<br>
                • <strong>NEW:</strong> Course Quality Analysis
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.divider()
        
        # Quick Actions
        st.markdown("## ⚡ Quick Actions")
        
        fetch_col1, fetch_col2 = st.columns(2)
        
        with fetch_col1:
            if st.button("🚀 Fetch ALL Contacts", type="primary", use_container_width=True):
                if start_date > end_date:
                    st.error("Start date must be before end date.")
                else:
                    with st.spinner("Fetching ALL contacts with prospect reasons..."):
                        # Test connection first
                        success, message = test_hubspot_connection(HUBSPOT_API_KEY)
                        
                        if success:
                            contacts, total_fetched = fetch_hubspot_contacts_with_date_filter(
                                HUBSPOT_API_KEY, date_field, start_date, end_date
                            )
                            
                            if contacts:
                                df = process_contacts_data(contacts)
                                st.session_state.contacts_df = df
                                
                                # Perform analysis
                                analysis_results = analyze_contact_data(df)
                                st.session_state.analysis_results = analysis_results
                                
                                # Create visualizations
                                visualizations = create_visualizations(analysis_results, df)
                                st.session_state.visualizations = visualizations
                                
                                # Email validation
                                email_validation = analyze_email_validation(df)
                                st.session_state.email_validation = email_validation
                                
                                st.success(f"✅ Successfully loaded ALL {len(contacts)} contacts!")
                                st.rerun()
                            else:
                                st.warning("No contacts found for the selected date range.")
                        else:
                            st.error(f"Connection failed: {message}")
        
        with fetch_col2:
            if st.button("🔄 Refresh Analysis", use_container_width=True):
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
        
        if st.button("🗑️ Clear All Data", use_container_width=True):
            st.session_state.clear()
            st.rerun()
    
    with col1:  # Main content area
        # Display dashboard if data exists
        if st.session_state.contacts_df is not None and not st.session_state.contacts_df.empty:
            df = st.session_state.contacts_df
            
            # Show filter info at the top
            st.markdown(
                f"""
                <div style="background-color: #e8f4fd; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                    <strong>📊 Showing ALL {len(df):,} contacts</strong><br>
                    <small>Filtered by: {date_field} from {start_date} to {end_date}</small>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Key Metrics at the top
            st.markdown("## 📈 Key Performance Indicators")
            
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                total_contacts = len(df)
                st.metric("Total Contacts", f"{total_contacts:,}")
            
            with metric_col2:
                email_count = df['Has Email'].sum()
                email_percent = (email_count / len(df)) * 100 if len(df) > 0 else 0
                st.metric("With Email", f"{email_count:,} ({email_percent:.1f}%)")
            
            with metric_col3:
                phone_count = df['Has Phone'].sum()
                phone_percent = (phone_count / len(df)) * 100 if len(df) > 0 else 0
                st.metric("With Phone", f"{phone_count:,} ({phone_percent:.1f}%)")
            
            with metric_col4:
                course_count = df['Has Course'].sum()
                course_percent = (course_count / len(df)) * 100 if len(df) > 0 else 0
                st.metric("With Course", f"{course_count:,} ({course_percent:.1f}%)")
            
            st.divider()
            
            # Create tabs for different sections - REMOVED Prospect Reasons tab
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "📈 Lead Status Distribution", 
                "📚 Course Distribution",
                "🎯 Course Quality Analysis",  # MOVED to position 3
                "🔍 Analytics Dashboard", 
                "🌍 Geographic Analysis", 
                "📧 Email Validation",
                "📥 Export Data"
            ])
            
            with tab1:  # LEAD STATUS DISTRIBUTION
                st.markdown("### 📊 Lead Status Distribution")
                
                if st.session_state.analysis_results and 'lead_status_distribution' in st.session_state.analysis_results:
                    lead_status_data = st.session_state.analysis_results['lead_status_distribution']
                    
                    if not lead_status_data.empty:
                        col_b1, col_b2 = st.columns([2, 1])
                        
                        with col_b1:
                            # Display the table EXACTLY like your example
                            st.markdown("#### Lead Status Counts")
                            st.dataframe(
                                lead_status_data,
                                use_container_width=True,
                                height=400,
                                column_config={
                                    "Lead Status": st.column_config.TextColumn("Lead Status", width="medium"),
                                    "Count": st.column_config.NumberColumn("Count", format="%d", width="small")
                                }
                            )
                        
                        with col_b2:
                            # Download button
                            csv_lead = lead_status_data.to_csv(index=False)
                            st.download_button(
                                "📥 Download Lead Status",
                                csv_lead,
                                "lead_status_distribution.csv",
                                "text/csv",
                                use_container_width=True
                            )
                            
                            # Quick stats
                            # Exclude Grand Total for metrics
                            data_for_metrics = lead_status_data[lead_status_data['Lead Status'] != 'Grand Total']
                            total_leads = data_for_metrics['Count'].sum() if not data_for_metrics.empty else 0
                            top_status = data_for_metrics.iloc[0]['Lead Status'] if len(data_for_metrics) > 0 else "N/A"
                            top_count = data_for_metrics.iloc[0]['Count'] if len(data_for_metrics) > 0 else 0
                            
                            st.metric("Total Records", total_leads)
                            st.metric("Top Status", top_status, delta=f"{top_count} records")
                            
                            # 🔍 DEBUG VIEW: Show raw vs normalized mapping
                            with st.expander("🔍 View Data Normalization", expanded=False):
                                if 'debug_mapping' in st.session_state.analysis_results:
                                    debug_df = st.session_state.analysis_results['debug_mapping']
                                    
                                    st.markdown("**Raw vs Normalized Values**")
                                    st.dataframe(debug_df, use_container_width=True, height=300)
                                    
                                    # Check for old values
                                    old_values = ['neutral_prospect', 'prospect', 'hot_prospect']
                                    has_old_values = any(debug_df['Lead Status Raw'].astype(str).str.lower().str.contains(val).any() for val in old_values)
                                    
                                    if has_old_values:
                                        st.success("✅ Old values detected and successfully normalized!")
                                        st.info("Old values (neutral_prospect, prospect, hot_prospect) are now merged into Cold, Warm, and Hot categories.")
                            
                            # Pie chart
                            if len(data_for_metrics) > 0:
                                fig = px.pie(
                                    data_for_metrics.head(8),
                                    values='Count',
                                    names='Lead Status',
                                    title="Lead Status Distribution",
                                    hole=0.3
                                )
                                fig.update_traces(textposition='inside', textinfo='percent+label')
                                st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No lead status data available")
                else:
                    st.info("No lead status analysis available")
            
            with tab2:  # COURSE DISTRIBUTION
                st.markdown("### 📚 Course/Program Distribution")
                
                if st.session_state.analysis_results and 'course_distribution' in st.session_state.analysis_results:
                    course_data = st.session_state.analysis_results['course_distribution']
                    
                    if not course_data.empty:
                        col_c1, col_c2 = st.columns([2, 1])
                        
                        with col_c1:
                            # Display the table with Course and Count
                            st.markdown("#### Course Counts")
                            st.dataframe(
                                course_data,
                                use_container_width=True,
                                height=400,
                                column_config={
                                    "Course": st.column_config.TextColumn("Course/Program", width="medium"),
                                    "Count": st.column_config.NumberColumn("Count", format="%d", width="small")
                                }
                            )
                        
                        with col_c2:
                            # Download button
                            csv_course = course_data.to_csv(index=False)
                            st.download_button(
                                "📥 Download Courses",
                                csv_course,
                                "course_distribution.csv",
                                "text/csv",
                                use_container_width=True
                            )
                            
                            # Quick stats
                            total_courses = course_data['Count'].sum()
                            top_course = course_data.iloc[0]['Course'] if len(course_data) > 0 else "N/A"
                            top_course_count = course_data.iloc[0]['Count'] if len(course_data) > 0 else 0
                            
                            st.metric("Total Course Records", total_courses)
                            st.metric("Top Course", top_course[:15], delta=f"{top_course_count} records")
                            
                            # Show course badges for top courses
                            if len(course_data) > 0:
                                st.markdown("#### Top Courses")
                                top_courses = course_data.head(5)
                                for _, row in top_courses.iterrows():
                                    st.markdown(
                                        f'<span class="course-badge">{row["Course"]}: {row["Count"]}</span>',
                                        unsafe_allow_html=True
                                    )
                            
                            # Pie chart
                            if len(course_data) > 0:
                                fig = px.pie(
                                    course_data.head(8),
                                    values='Count',
                                    names='Course',
                                    title="Top Course Distribution",
                                    hole=0.4
                                )
                                fig.update_traces(textposition='inside', textinfo='percent+label')
                                st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No course/program data available")
                        
                        # Show how many contacts have course info
                        course_count = df['Has Course'].sum()
                        if course_count > 0:
                            st.info(f"Found {course_count} contacts with course/program information")
                        else:
                            st.warning("No course/program information found in the contacts data")
                else:
                    st.info("No course distribution analysis available")
            
            with tab3:  # 🎯 FIXED: COURSE QUALITY ANALYSIS - PROPER UI
                st.markdown("### 🎯 Course-wise Lead Quality Analysis")
                st.markdown("*Pivot table showing lead status distribution by course/program with quality metrics*")
                
                if st.session_state.analysis_results and 'course_quality' in st.session_state.analysis_results:
                    quality_df = st.session_state.analysis_results['course_quality']
                    
                    if not quality_df.empty:
                        # Display metrics summary
                        col_q1, col_q2, col_q3 = st.columns(3)
                        
                        with col_q1:
                            total_courses = len(quality_df)
                            st.metric("Total Courses", total_courses)
                        
                        with col_q2:
                            avg_low_quality = quality_df['Low Quality %'].mean()
                            st.metric("Avg Low Quality %", f"{avg_low_quality:.1f}%")
                        
                        with col_q3:
                            avg_good_quality = quality_df['Good Quality %'].mean()
                            st.metric("Avg Good Quality %", f"{avg_good_quality:.1f}%")
                        
                        st.divider()
                        
                        # Display the main course quality table using Streamlit dataframe
                        st.markdown("#### Course Quality Matrix")
                        
                        # Create a copy for display with formatting
                        display_df = quality_df.copy()
                        
                        # Store original numeric values for comparison
                        low_quality_values = display_df['Low Quality %'].copy()
                        good_quality_values = display_df['Good Quality %'].copy()
                        
                        # Format numeric columns for better display
                        format_columns = [
                            'Not Connected (NC)', 'Not Interested', 'Not Qualified',
                            'Cold', 'Duplicate', 'Warm', 'Hot', 'Future Prospect',
                            'Customer', 'New Lead', 'Low Quality Leads', 'Good Quality Leads',
                            'Grand Total'
                        ]
                        
                        # Apply formatting to integer columns
                        for col in format_columns:
                            if col in display_df.columns:
                                display_df[col] = display_df[col].apply(lambda x: f"{int(x):,}" if pd.notnull(x) else "0")
                        
                        # Format percentage columns
                        display_df['Low Quality %'] = display_df['Low Quality %'].apply(lambda x: f"{x:.1f}%")
                        display_df['Good Quality %'] = display_df['Good Quality %'].apply(lambda x: f"{x:.1f}%")
                        
                        # Display the dataframe with proper scrolling
                        st.dataframe(
                            display_df,
                            use_container_width=True,
                            height=500,
                            column_config={
                                "Course/Program": st.column_config.TextColumn("Course/Program", width="large"),
                                "Low Quality %": st.column_config.TextColumn("Low Quality %", width="small"),
                                "Good Quality %": st.column_config.TextColumn("Good Quality %", width="small"),
                                "Grand Total": st.column_config.TextColumn("Total Leads", width="small")
                            }
                        )
                        
                        # Legend
                        st.markdown("""
                        <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin-top: 1rem;">
                            <strong>🎯 Quality Metrics Legend:</strong>
                            <ul style="margin-bottom: 0;">
                                <li><strong>Low Quality</strong> = Not Interested + Not Qualified</li>
                                <li><strong>Good Quality</strong> = Cold + Warm + Hot</li>
                                <li><strong>Low Quality %</strong> = Percentage of low quality leads</li>
                                <li><strong>Good Quality %</strong> = Percentage of good quality leads</li>
                            </ul>
                            <p style="margin-top: 0.5rem; margin-bottom: 0; font-size: 0.9rem;">
                                <span style="background-color: #f8d7da; color: #721c24; padding: 0.2rem 0.5rem; border-radius: 0.2rem; font-weight: bold;">🔴</span> 
                                Low Quality % > 40% indicates high number of disqualified leads<br>
                                <span style="background-color: #d4edda; color: #155724; padding: 0.2rem 0.5rem; border-radius: 0.2rem; font-weight: bold;">🟢</span> 
                                Good Quality % > 50% indicates strong lead pipeline
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Download and additional options
                        st.divider()
                        col_dl1, col_dl2, col_dl3 = st.columns(3)
                        
                        with col_dl1:
                            csv_quality = quality_df.to_csv(index=False)
                            st.download_button(
                                "📥 Download Course Quality Data",
                                csv_quality,
                                "course_quality_analysis.csv",
                                "text/csv",
                                use_container_width=True
                            )
                        
                        with col_dl2:
                            # Show raw numeric data
                            if st.button("📊 View Raw Numeric Data", use_container_width=True):
                                st.dataframe(quality_df, use_container_width=True, height=400)
                        
                        with col_dl3:
                            # Show top 5 courses by quality
                            if st.button("🏆 Show Top 5 Quality Courses", use_container_width=True):
                                top_courses = quality_df.sort_values('Good Quality %', ascending=False).head(5)
                                st.dataframe(top_courses[['Course/Program', 'Good Quality %', 'Low Quality %', 'Grand Total']], 
                                           use_container_width=True)
                        
                        # Additional insights
                        with st.expander("📈 Quality Insights", expanded=False):
                            # Find best and worst courses
                            best_course = quality_df.loc[quality_df['Good Quality %'].idxmax()]
                            worst_course = quality_df.loc[quality_df['Low Quality %'].idxmax()]
                            
                            col_ins1, col_ins2 = st.columns(2)
                            
                            with col_ins1:
                                st.markdown("**🏆 Best Quality Course**")
                                st.metric(
                                    label=best_course['Course/Program'],
                                    value=f"{best_course['Good Quality %']:.1f}% Good Quality",
                                    delta=f"{best_course['Grand Total']} total leads"
                                )
                            
                            with col_ins2:
                                st.markdown("**⚠️ Highest Low Quality Course**")
                                st.metric(
                                    label=worst_course['Course/Program'],
                                    value=f"{worst_course['Low Quality %']:.1f}% Low Quality",
                                    delta=f"{worst_course['Grand Total']} total leads"
                                )
                            
                            # Quality distribution
                            st.markdown("**📊 Quality Distribution**")
                            high_quality = (quality_df['Good Quality %'] > 50).sum()
                            medium_quality = ((quality_df['Good Quality %'] >= 30) & (quality_df['Good Quality %'] <= 50)).sum()
                            low_quality = (quality_df['Good Quality %'] < 30).sum()
                            
                            quality_dist = pd.DataFrame({
                                'Quality Level': ['High (>50%)', 'Medium (30-50%)', 'Low (<30%)'],
                                'Number of Courses': [high_quality, medium_quality, low_quality]
                            })
                            st.dataframe(quality_dist, use_container_width=True)
                            
                    else:
                        st.info("No course quality data available (no contacts with course information)")
                else:
                    st.info("No course quality analysis available")
            
            with tab4:  # Analytics Dashboard
                st.markdown("### 📈 Comprehensive Analytics")
                
                if st.session_state.analysis_results and st.session_state.visualizations:
                    analysis = st.session_state.analysis_results
                    visuals = st.session_state.visualizations
                    
                    # Row 1: Lead Status and Course Distribution
                    col_d1, col_d2 = st.columns(2)
                    
                    with col_d1:
                        if 'lead_status_bar' in visuals:
                            st.plotly_chart(visuals['lead_status_bar'], use_container_width=True)
                    
                    with col_d2:
                        if 'course_bar' in visuals:
                            st.plotly_chart(visuals['course_bar'], use_container_width=True)
                    
                    # Row 2: Pie Charts
                    col_e1, col_e2 = st.columns(2)
                    
                    with col_e1:
                        if 'lead_status_pie' in visuals:
                            st.plotly_chart(visuals['lead_status_pie'], use_container_width=True)
                    
                    with col_e2:
                        if 'course_pie' in visuals:
                            st.plotly_chart(visuals['course_pie'], use_container_width=True)
                    
                    # Row 3: Country and Trend
                    col_f1, col_f2 = st.columns(2)
                    
                    with col_f1:
                        if 'country_bar' in visuals:
                            st.plotly_chart(visuals['country_bar'], use_container_width=True)
                    
                    with col_f2:
                        if 'monthly_trend' in visuals:
                            st.plotly_chart(visuals['monthly_trend'], use_container_width=True)
                    
                    # Data Tables
                    st.markdown("### 📋 Detailed Statistics")
                    
                    analysis_tabs = st.tabs(["Courses", "Countries", "Industries", "Lifecycle", "Completeness"])
                    
                    with analysis_tabs[0]:
                        if 'course_distribution' in analysis:
                            st.dataframe(analysis['course_distribution'], use_container_width=True, height=300)
                    
                    with analysis_tabs[1]:
                        if 'country_distribution' in analysis:
                            st.dataframe(analysis['country_distribution'], use_container_width=True, height=300)
                    
                    with analysis_tabs[2]:
                        if 'industry_distribution' in analysis:
                            st.dataframe(analysis['industry_distribution'], use_container_width=True, height=300)
                    
                    with analysis_tabs[3]:
                        if 'stage_distribution' in analysis:
                            st.dataframe(analysis['stage_distribution'], use_container_width=True, height=300)
                    
                    with analysis_tabs[4]:
                        if 'completeness' in analysis:
                            st.dataframe(analysis['completeness'], use_container_width=True, height=300)
            
            with tab5:  # Geographic Analysis
                st.markdown("### 🌍 Geographic Distribution")
                
                if st.session_state.analysis_results:
                    analysis = st.session_state.analysis_results
                    
                    if 'country_distribution' in analysis:
                        country_data = analysis['country_distribution']
                        
                        # Create choropleth map
                        fig = px.choropleth(
                            country_data,
                            locations='Country',
                            locationmode='country names',
                            color='Count',
                            hover_name='Country',
                            title='Contact Distribution by Country',
                            color_continuous_scale='Viridis'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Country data table
                        st.dataframe(country_data, use_container_width=True, height=400)
            
            with tab6:  # Email Validation
                st.markdown("### 📧 Email Validation")
                
                if st.session_state.email_validation is not None:
                    email_issues = st.session_state.email_validation
                    
                    if not email_issues.empty:
                        col_g1, col_g2 = st.columns([3, 1])
                        
                        with col_g1:
                            st.warning(f"Found {len(email_issues)} email issues")
                            st.dataframe(email_issues, use_container_width=True, height=250)
                        
                        with col_g2:
                            st.metric("Total Issues", len(email_issues))
                            
                            gmal_count = (email_issues['Issue'] == 'Incorrect domain: gmal.com').sum()
                            st.metric("gmal.com issues", gmal_count)
                            
                            # Download email issues
                            csv_email = email_issues.to_csv(index=False)
                            st.download_button(
                                "📥 Download Email Issues",
                                csv_email,
                                "email_issues.csv",
                                "text/csv",
                                use_container_width=True
                            )
                    else:
                        st.success("✅ All emails appear valid!")
            
            with tab7:  # Export Data
                st.markdown("### 📥 Export Options")
                
                # First row of export buttons
                export_row1 = st.columns(3)
                
                with export_row1[0]:
                    # Export Full CSV
                    csv_data = df.to_csv(index=False)
                    st.download_button(
                        "📄 Download Full CSV",
                        csv_data,
                        f"hubspot_contacts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        "text/csv",
                        use_container_width=True
                    )
                
                with export_row1[1]:
                    # Export Excel with multiple sheets
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
                        use_container_width=True
                    )
                
                with export_row1[2]:
                    # View raw data
                    if st.button("👁️ View Raw Data", use_container_width=True):
                        st.dataframe(df, use_container_width=True, height=400)
                
                # Export individual analyses
                st.markdown("---")
                st.markdown("#### Export Individual Analyses")
                
                if st.session_state.analysis_results:
                    export_row2 = st.columns(4)
                    
                    with export_row2[0]:
                        if 'lead_status_distribution' in st.session_state.analysis_results:
                            csv = st.session_state.analysis_results['lead_status_distribution'].to_csv(index=False)
                            st.download_button(
                                "📊 Lead Status",
                                csv,
                                "lead_status_distribution.csv",
                                "text/csv",
                                use_container_width=True
                            )
                    
                    with export_row2[1]:
                        if 'course_distribution' in st.session_state.analysis_results:
                            csv = st.session_state.analysis_results['course_distribution'].to_csv(index=False)
                            st.download_button(
                                "📚 Courses",
                                csv,
                                "course_distribution.csv",
                                "text/csv",
                                use_container_width=True
                            )
                    
                    with export_row2[2]:
                        if 'course_quality' in st.session_state.analysis_results:
                            csv = st.session_state.analysis_results['course_quality'].to_csv(index=False)
                            st.download_button(
                                "🎯 Course Quality",
                                csv,
                                "course_quality_analysis.csv",
                                "text/csv",
                                use_container_width=True
                            )
                    
                    with export_row2[3]:
                        # Other exports if needed
                        st.download_button(
                            "📋 All Analysis",
                            "",
                            disabled=True,
                            help="Combine all analyses in Excel download above",
                            use_container_width=True
                        )
            
            # Footer
            st.divider()
            st.markdown(
                f"""
                <div style='text-align: center; color: #666; font-size: 0.8rem; padding: 1rem;'>
                <strong>HubSpot Contacts Analytics Dashboard</strong> • Built with Streamlit • 
                Data last fetched: {datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")} IST • 
                <span style='color: #00a86b; font-weight: bold;'>✅ LEAD STATUS NORMALIZATION ACTIVE</span> • 
                <span style='color: #1a73e8; font-weight: bold;'>🎯 COURSE QUALITY ANALYSIS ENABLED</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        else:
            # Welcome screen when no data is loaded
            st.markdown(
                """
                <div style='text-align: center; padding: 3rem;'>
                    <h2>👋 Welcome to HubSpot Contacts Dashboard</h2>
                    <p style='font-size: 1.1rem; color: #666; margin: 1rem 0;'>
                        Configure date filters and click "Fetch ALL Contacts" to start analysis
                    </p>
                    <div style='margin-top: 2rem;'>
                        <p>🎯 <strong>Key Features (FIXED & ENHANCED):</strong></p>
                        <ul style='text-align: left; margin-left: 30%;'>
                            <li>✅ <strong>Course Quality Analysis</strong> - NEW Pivot Table</li>
                            <li>✅ <strong>Correct Lead Status Counts</strong> - Old values merged</li>
                            <li>✅ <strong>Course Distribution</strong> with counts</li>
                            <li>✅ <strong>UNLIMITED fetching</strong> - Gets ALL records</li>
                        </ul>
                        <p style='margin-top: 2rem;'>📊 <strong>New Course Quality Analysis Includes:</strong></p>
                        <ul style='text-align: left; margin-left: 30%;'>
                            <li>🎯 <strong>Pivot Table</strong> - Course × Lead Status matrix</li>
                            <li>🔴 <strong>Low Quality Leads</strong> = Not Interested + Not Qualified</li>
                            <li>🟢 <strong>Good Quality Leads</strong> = Cold + Warm + Hot</li>
                            <li>📈 <strong>Quality Metrics</strong> - Percentage calculations</li>
                            <li>📥 <strong>Export Ready</strong> - Download complete analysis</li>
                        </ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

if __name__ == "__main__":
    main()
