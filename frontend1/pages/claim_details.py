import streamlit as st
from utils.api_client import get_api_client, format_currency, format_datetime, get_status_color

st.set_page_config(page_title="Claim Details", layout="wide")

api = get_api_client()

def display_claim_details(claim):
    st.title(f"Claim Details: {claim['claim_id']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Patient Information")
        st.write(f"**Name:** {claim['patient_name']}")
        st.write(f"**Patient ID:** {claim['patient_id']}")
        st.write(f"**Insurance Provider:** {claim['insurance_provider']}")
        st.write(f"**Policy Number:** {claim['policy_number']}")
    
    with col2:
        st.subheader("Medical Information")
        st.write(f"**Diagnosis Code:** {claim['diagnosis_code']}")
        st.write(f"**Procedure Code:** {claim['procedure_code']}")
        st.write(f"**Claim Amount:** {format_currency(claim['claim_amount'])}")
        st.write(f"**Service Date:** {claim['service_date']}")
    
    st.subheader("Provider Information")
    st.write(f"**Name:** {claim['provider_name']}")
    st.write(f"**NPI:** {claim.get('provider_npi', 'N/A')}")
    
    st.subheader("Status")
    status_color = get_status_color(claim['status'])
    st.markdown(f"<div class='claim-status' style='color:{status_color}'>{claim['status']}</div>", unsafe_allow_html=True)
    st.write(f"**Created At:** {format_datetime(claim['created_at'])}")
    st.write(f"**Last Updated:** {format_datetime(claim.get('updated_at', ''))}")
    
    st.subheader("Notes")
    notes = claim.get('notes', '')
    if notes:
        st.write(notes)
    else:
        st.write("No additional notes provided.")

def main():
    if "selected_claim_id" not in st.session_state:
        st.info("No claim selected. Return to the dashboard to pick one.")
        return
    
    claim_id = st.session_state.selected_claim_id
    
    with st.spinner(f"Loading details for claim {claim_id}..."):
        claim = api.get_claim_details(claim_id)
    
    if claim:
        display_claim_details(claim)
    else:
        st.error(f"Failed to load claim details for ID: {claim_id}")


if __name__ == "__main__":
    main()
