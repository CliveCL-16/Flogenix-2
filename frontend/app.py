import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

from utils.api_client import get_api_client, format_currency, format_datetime, get_status_color

# Page configuration
st.set_page_config(
    page_title="Flowgenix - Healthcare Claims Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b6b;
    }
    .success-card {
        border-left-color: #51cf66;
    }
    .warning-card {
        border-left-color: #ffd43b;
    }
    .danger-card {
        border-left-color: #ff6b6b;
    }
    .info-card {
        border-left-color: #339af0;
    }
    
    .stAlert > div {
        padding: 0.5rem 1rem;
    }
    
    .claim-status {
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-weight: bold;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Initialize API client
api = get_api_client()

# Sidebar navigation
st.sidebar.title("🏥 Flowgenix")
st.sidebar.markdown("*Intelligent Healthcare Claims Processing*")

# Check API health
if api.health_check():
    st.sidebar.success("✅ API Connected")
else:
    st.sidebar.error("❌ API Disconnected")
    st.error("Unable to connect to Flowgenix API. Please ensure the backend is running on http://localhost:8000")
    st.stop()

# Navigation
page = st.sidebar.selectbox(
    "Navigate to:",
    ["📊 Dashboard", "📝 Submit Claim", "📋 View Claims", "🤖 Agent Processing", "🔍 Claim Details"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Actions")

if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

# Main content based on navigation
if page == "📊 Dashboard":
    st.title("📊 Flowgenix Dashboard")
    st.markdown("### Real-time Healthcare Claims Processing Overview")
    
    # Get dashboard metrics
    metrics = api.get_dashboard_metrics()
    
    if metrics:
        # Key metrics row
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="Total Claims",
                value=metrics["total_claims"],
                delta=None
            )
        
        with col2:
            st.metric(
                label="Approval Rate",
                value=f"{metrics['approval_rate']:.1f}%",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Avg Processing Time",
                value=f"{metrics['avg_processing_time_seconds']:.1f}s",
                delta=None
            )
        
        with col4:
            st.metric(
                label="Approved Claims",
                value=metrics["approved_count"],
                delta=None
            )
        
        with col5:
            st.metric(
                label="Fraud Flagged",
                value=metrics["fraud_flagged_count"],
                delta=None
            )
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            # Claims by Status pie chart
            status_data = {
                "Status": ["Approved", "Denied", "Pending Review", "Fraud Flagged", "Pending"],
                "Count": [
                    metrics["approved_count"],
                    metrics["denied_count"], 
                    metrics["pending_review_count"],
                    metrics["fraud_flagged_count"],
                    metrics["total_claims"] - (metrics["approved_count"] + metrics["denied_count"] + 
                                               metrics["pending_review_count"] + metrics["fraud_flagged_count"])
                ]
            }
            
            fig_pie = px.pie(
                values=status_data["Count"],
                names=status_data["Status"],
                title="Claims Distribution by Status",
                color_discrete_map={
                    "Approved": "#51cf66",
                    "Denied": "#ff6b6b", 
                    "Pending Review": "#ffd43b",
                    "Fraud Flagged": "#e64980",
                    "Pending": "#339af0"
                }
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Processing efficiency gauge
            approval_rate = metrics["approval_rate"]
            
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=approval_rate,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Approval Rate"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#51cf66"},
                    'steps': [
                        {'range': [0, 50], 'color': "#ffe066"},
                        {'range': [50, 80], 'color': "#74c0fc"},
                        {'range': [80, 100], 'color': "#d0f4de"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            
            fig_gauge.update_layout(height=400)
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Recent claims
        st.markdown("### Recent Claims")
        claims = api.get_claims()
        
        if claims:
            # Convert to DataFrame
            df = pd.DataFrame(claims)
            df = df.head(10)  # Show last 10 claims
            
            # Format for display
            display_df = pd.DataFrame({
                "Claim ID": df["claim_id"],
                "Patient": df["patient_name"],
                "Amount": df["claim_amount"].apply(format_currency),
                "Status": df["status"].apply(lambda x: f"{get_status_color(x)} {x}"),
                "Created": df["created_at"].apply(format_datetime)
            })
            
            st.dataframe(display_df, use_container_width=True)
        else:
            st.info("No claims data available")
    
    else:
        st.error("Unable to load dashboard metrics")

elif page == "📝 Submit Claim":
    st.title("📝 Submit New Claim")
    st.markdown("### Enter claim information below")
    
    with st.form("claim_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Patient Information")
            patient_name = st.text_input("Patient Name*", placeholder="John Doe")
            patient_id = st.text_input("Patient ID*", placeholder="PAT-12345")
            insurance_provider = st.text_input("Insurance Provider*", placeholder="Blue Cross Blue Shield")
            policy_number = st.text_input("Policy Number*", placeholder="POL-67890")
        
        with col2:
            st.subheader("Medical Information")
            diagnosis_code = st.selectbox("Diagnosis Code (ICD-10)*", [
                "Z00.00 - General adult medical examination",
                "S52.501A - Unspecified fracture of lower end of right radius",
                "M25.511 - Pain in right shoulder",
                "E11.9 - Type 2 diabetes mellitus without complications",
                "J06.9 - Acute upper respiratory infection",
                "K21.9 - Gastro-esophageal reflux disease",
                "M79.3 - Panniculitis, unspecified",
                "I10 - Essential hypertension"
            ])
            
            procedure_code = st.selectbox("Procedure Code (CPT)*", [
                "99213 - Office visit, established patient, low complexity",
                "99214 - Office visit, established patient, moderate complexity", 
                "99215 - Office visit, established patient, high complexity",
                "92004 - Ophthalmological examination",
                "27447 - Knee arthroplasty",
                "73721 - MRI lower extremity",
                "36415 - Blood collection",
                "85025 - Complete blood count"
            ])
            
            claim_amount = st.number_input("Claim Amount ($)*", min_value=0.01, value=150.00, step=0.01)
            service_date = st.date_input("Service Date*", value=date.today())
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("Provider Information")
            provider_name = st.text_input("Provider Name*", placeholder="Dr. Jane Smith")
            provider_npi = st.text_input("Provider NPI", placeholder="1234567890", max_chars=10)
        
        with col4:
            st.subheader("Additional Information")
            notes = st.text_area("Notes", placeholder="Additional claim details...", height=100)
        
        # Submit button
        submitted = st.form_submit_button("Submit Claim", type="primary")
        
        if submitted:
            # Validation
            required_fields = [patient_name, patient_id, insurance_provider, policy_number, provider_name]
            if not all(required_fields):
                st.error("Please fill in all required fields (marked with *)")
            else:
                # Extract codes from dropdown selections
                diagnosis_code_clean = diagnosis_code.split(" - ")[0]
                procedure_code_clean = procedure_code.split(" - ")[0]
                
                # Prepare claim data
                claim_data = {
                    "patient_name": patient_name,
                    "patient_id": patient_id,
                    "insurance_provider": insurance_provider,
                    "policy_number": policy_number,
                    "diagnosis_code": diagnosis_code_clean,
                    "procedure_code": procedure_code_clean,
                    "claim_amount": claim_amount,
                    "service_date": service_date,
                    "provider_name": provider_name,
                    "provider_npi": provider_npi if provider_npi else None,
                    "notes": notes if notes else None
                }
                
                # Submit claim
                result = api.submit_claim(claim_data)
                
                if result:
                    st.success(f"✅ Claim submitted successfully! Claim ID: {result['claim_id']}")
                    st.info("You can now process this claim or view it in the Claims list.")
                    
                    # Option to process immediately
                    if st.button("Process Claim Now"):
                        with st.spinner("Processing claim..."):
                            process_result = api.process_claim(result['claim_id'])
                            if process_result:
                                st.success(f"Claim processed: {process_result['status']}")
                                st.json(process_result)

elif page == "📋 View Claims":
    st.title("📋 Claims Management")
    
    # Filters
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        status_filter = st.selectbox("Filter by Status", [
            "All", "PENDING", "APPROVED", "DENIED", "PENDING_REVIEW", "FRAUD_FLAGGED"
        ])
    
    with col2:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    with col3:
        show_details = st.checkbox("Show Details")
    
    # Get claims
    filter_value = None if status_filter == "All" else status_filter
    claims = api.get_claims(status_filter=filter_value)
    
    if claims:
        st.markdown(f"### {len(claims)} Claims Found")
        
        for claim in claims:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 1.5, 1, 1])
                
                with col1:
                    st.markdown(f"**{claim['claim_id']}**")
                    st.text(f"Patient: {claim['patient_name']}")
                
                with col2:
                    st.text(f"Amount: {format_currency(claim['claim_amount'])}")
                    st.text(f"Created: {format_datetime(claim['created_at'])}")
                
                with col3:
                    status_color = get_status_color(claim['status'])
                    st.markdown(f"{status_color} **{claim['status']}**")
                
                with col4:
                    if claim['status'] == 'PENDING':
                        if st.button("Process", key=f"process_{claim['claim_id']}"):
                            with st.spinner("Processing..."):
                                result = api.process_claim(claim['claim_id'])
                                if result:
                                    st.success("Processed!")
                                    st.rerun()
                
                with col5:
                    if st.button("View", key=f"view_{claim['claim_id']}"):
                        st.session_state['selected_claim_id'] = claim['claim_id']
                        st.switch_page("pages/claim_details.py")
                
                if show_details:
                    st.markdown(f"**Provider:** {claim['provider_name']}")
                    st.markdown(f"**Diagnosis:** {claim['diagnosis_code']} | **Procedure:** {claim['procedure_code']}")
                    if claim.get('notes'):
                        st.markdown(f"**Notes:** {claim['notes']}")
                
                st.divider()
    else:
        st.info("No claims found matching the selected criteria.")

elif page == "🤖 Agent Processing":
    st.title("🤖 Multi-Agent Processing View")
    st.markdown("### Watch AI Agents Collaborate to Process Claims")
    
    # Claim ID input
    col1, col2 = st.columns([3, 1])
    with col1:
        claim_id = st.text_input("Enter Claim ID to analyze agent processing", placeholder="CLM-12345678")
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
        process_button = st.button("🚀 Process Claim", type="primary", use_container_width=True)
    
    if process_button and claim_id:
        with st.spinner("Processing claim through multi-agent system..."):
            # Process the claim
            result = api.process_claim(claim_id)
            
            if result:
                st.success(f"✅ Claim processed: {result['status']}")
                
                # Section 1: Agent Timeline
                st.markdown("---")
                st.subheader("🤖 Agent Processing Timeline")
                
                timeline_data = api.get_agent_timeline(claim_id)
                if timeline_data:
                    agents = timeline_data.get("agents", [])
                    
                    for i, agent in enumerate(agents):
                        col1, col2, col3, col4 = st.columns([3, 1.5, 1, 2])
                        
                        with col1:
                            if agent["status"] == "completed":
                                st.success(f"✅ {agent['agent']}")
                            elif agent["status"] == "in_progress":
                                st.info(f"⏳ {agent['agent']}")
                            elif agent["status"] == "failed":
                                st.error(f"❌ {agent['agent']}")
                            else:
                                st.text(f"⏸️ {agent['agent']}")
                        
                        with col2:
                            st.text(f"{agent['duration']:.1f}s")
                        
                        with col3:
                            st.text(agent["status"])
                        
                        with col4:
                            confidence = agent.get("confidence", 0)
                            if confidence > 80:
                                st.success(f"🎯 {agent['result']} ({confidence}%)")
                            elif confidence > 60:
                                st.warning(f"⚠️ {agent['result']} ({confidence}%)")
                            else:
                                st.error(f"❌ {agent['result']} ({confidence}%)")
                
                # Section 2: Agent Communication Graph
                st.markdown("---")
                st.subheader("🔗 Agent Communication Flow")
                
                # Create agent flow visualization
                import plotly.graph_objects as go
                
                # Define agent nodes
                node_x = [1, 0, 2, 1, 1]
                node_y = [2, 1, 1, 0, -1]
                node_labels = ["Intake", "Eligibility", "Clinical", "Fraud", "Adjudication"]
                node_colors = ["#2E86C1", "#28B463", "#8E44AD", "#E67E22", "#E74C3C"]
                
                # Define edges (agent handoffs)
                edge_x = []
                edge_y = []
                edges = [(0,1), (0,2), (0,3), (1,4), (2,4), (3,4)]
                
                for edge in edges:
                    edge_x.extend([node_x[edge[0]], node_x[edge[1]], None])
                    edge_y.extend([node_y[edge[0]], node_y[edge[1]], None])
                
                # Create figure
                fig = go.Figure()
                
                # Add edges
                fig.add_trace(go.Scatter(
                    x=edge_x, y=edge_y,
                    mode='lines',
                    line=dict(width=3, color='#BDC3C7'),
                    hoverinfo='none',
                    showlegend=False
                ))
                
                # Add nodes
                fig.add_trace(go.Scatter(
                    x=node_x, y=node_y,
                    mode='markers+text',
                    marker=dict(size=40, color=node_colors, line=dict(width=2, color='white')),
                    text=node_labels,
                    textposition="middle center",
                    textfont=dict(color="white", size=10, family="Arial Black"),
                    hoverinfo='text',
                    showlegend=False
                ))
                
                fig.update_layout(
                    title="Multi-Agent Collaboration Network",
                    showlegend=False,
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    height=300,
                    margin=dict(l=20, r=20, t=40, b=20),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Section 3: Agent Reasoning Logs
                st.markdown("---")
                st.subheader("🧠 Agent Reasoning Logs (ReAct Pattern)")
                
                reasoning_data = api.get_agent_reasoning(claim_id)
                if reasoning_data:
                    agent_reasoning = reasoning_data.get("agent_reasoning", {})
                    
                    for agent_name, steps in agent_reasoning.items():
                        with st.expander(f"🤖 {agent_name} - Reasoning Steps", expanded=False):
                            for step in steps:
                                step_type = step.get("type", "INFO")
                                step_text = step.get("text", "")
                                step_num = step.get("step", 0)
                                
                                if step_type == "REASON":
                                    st.info(f"**Step {step_num} - 💭 REASON:** {step_text}")
                                elif step_type == "ACT":
                                    st.warning(f"**Step {step_num} - 🔧 ACT:** {step_text}")
                                elif step_type == "OBSERVE":
                                    st.success(f"**Step {step_num} - 👁️ OBSERVE:** {step_text}")
                                elif step_type == "COMPLETE":
                                    st.markdown(f"**Step {step_num} - ✅ COMPLETE:** {step_text}")
                                else:
                                    st.write(f"**Step {step_num} - {step_type}:** {step_text}")
                
                # Section 4: Tool Usage Summary
                st.markdown("---")
                st.subheader("🔧 Agent Tool Usage")
                
                tool_data = api.get_tool_usage(claim_id)
                if tool_data:
                    tools = tool_data.get("tool_usage", [])
                    
                    if tools:
                        df_tools = pd.DataFrame(tools)
                        
                        # Add success indicators
                        df_tools['Status'] = df_tools['success'].apply(
                            lambda x: "✅ Success" if x else "❌ Failed"
                        )
                        
                        # Reorder columns
                        display_columns = ['agent', 'tool', 'result', 'Status']
                        df_display = df_tools[display_columns].copy()
                        df_display.columns = ['Agent', 'Tool', 'Result', 'Status']
                        
                        st.dataframe(df_display, use_container_width=True, hide_index=True)
                    else:
                        st.info("No tool usage data available")
                
                # Section 5: Final Decision Summary
                st.markdown("---")
                st.subheader("⚖️ Final Adjudication Summary")
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    decision = result.get('decision', 'UNKNOWN')
                    confidence = result.get('confidence_score', 0)
                    
                    if decision == 'APPROVE':
                        st.success(f"**Decision:** ✅ {decision}")
                    elif decision == 'DENY':
                        st.error(f"**Decision:** ❌ {decision}")
                    else:
                        st.warning(f"**Decision:** ⚠️ {decision}")
                    
                    st.metric("Confidence Score", f"{confidence:.1f}%")
                    st.metric("Processing Time", f"{result.get('processing_time_seconds', 0):.1f}s")
                
                with col2:
                    st.markdown("**🤖 Multi-Agent Collaboration Summary:**")
                    reasoning = result.get('reasoning_text', 'No reasoning provided')
                    st.write(reasoning)
                    
                    st.markdown("**🏆 Agentic AI Benefits Demonstrated:**")
                    st.write("✅ **Autonomous Decision Making:** Agents independently chose tools and actions")
                    st.write("✅ **Collaborative Intelligence:** Multiple specialized agents worked together") 
                    st.write("✅ **Explainable Reasoning:** Complete transparency into agent thought processes")
                    st.write("✅ **Tool Integration:** Agents autonomously invoked external APIs and databases")
                    st.write("✅ **Adaptive Processing:** Agents adapted strategy based on findings")
            else:
                st.error("Failed to process claim")
    
    elif claim_id and not process_button:
        st.info("👆 Click 'Process Claim' to see the multi-agent system in action")
    
    # Demo instructions
    if not claim_id:
        st.markdown("---")
        st.markdown("### 🎯 Demo Instructions")
        st.info("""
        **How to use this Multi-Agent Processing View:**
        
        1. **Enter a Claim ID** from the Claims list (e.g., CLM-12345678)
        2. **Click 'Process Claim'** to watch the agents work
        3. **Observe the Timeline** showing each agent's processing steps
        4. **Expand Reasoning Logs** to see the ReAct pattern (Reason → Act → Observe)
        5. **Review Tool Usage** to see which APIs/databases agents accessed
        6. **View Final Decision** with confidence scores and reasoning
        
        **What makes this "Agentic AI":**
        - 🤖 **Autonomous Agents:** Each agent makes independent decisions
        - 🔗 **Multi-Agent Collaboration:** Agents hand off work and share information  
        - 🧠 **Reasoning Transparency:** See exactly how agents think and act
        - 🔧 **Tool Usage:** Agents choose and execute appropriate tools
        - 📊 **State Management:** Agents maintain context across processing steps
        """)

elif page == "🔍 Claim Details":
    st.title("🔍 Claim Details")
    
    # Claim ID input
    claim_id = st.text_input("Enter Claim ID", placeholder="CLM-12345678")
    
    if st.button("Load Claim") or claim_id:
        if claim_id:
            with st.spinner("Loading claim details..."):
                claim_details = api.get_claim_details(claim_id)
                
                if claim_details:
                    # Claim header
                    col1, col2, col3 = st.columns([2, 1, 1])
                    
                    with col1:
                        st.markdown(f"## Claim {claim_details['claim_id']}")
                        st.markdown(f"**Patient:** {claim_details['patient_name']}")
                    
                    with col2:
                        status_color = get_status_color(claim_details['status'])
                        st.markdown(f"**Status:** {status_color} {claim_details['status']}")
                    
                    with col3:
                        st.markdown(f"**Amount:** {format_currency(claim_details['claim_amount'])}")
                    
                    # Tabs for different sections
                    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Basic Info", "🤖 Agent Reports", "🧠 AI Decision", "🔍 Fraud Analysis", "⚠️ Exceptions"])
                    
                    with tab1:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Patient Information")
                            st.text(f"Name: {claim_details['patient_name']}")
                            st.text(f"ID: {claim_details['patient_id']}")
                            st.text(f"Insurance: {claim_details['insurance_provider']}")
                            st.text(f"Policy: {claim_details['policy_number']}")
                        
                        with col2:
                            st.subheader("Medical Information")
                            st.text(f"Diagnosis: {claim_details['diagnosis_code']}")
                            st.text(f"Procedure: {claim_details['procedure_code']}")
                            st.text(f"Service Date: {claim_details['service_date']}")
                            st.text(f"Provider: {claim_details['provider_name']}")
                    
                    with tab2:
                        st.subheader("🤖 Multi-Agent Processing Reports")
                        
                        # Get agent timeline
                        timeline_data = api.get_agent_timeline(claim_id)
                        if timeline_data and timeline_data.get("agents"):
                            agents = timeline_data["agents"]
                            
                            for agent in agents:
                                with st.expander(f"🤖 {agent['agent']} Report", expanded=False):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.metric("Status", agent["status"])
                                        st.metric("Duration", f"{agent['duration']:.1f}s")
                                    
                                    with col2:
                                        st.metric("Result", agent["result"])
                                        if agent.get("confidence"):
                                            st.metric("Confidence", f"{agent['confidence']}%")
                            
                            # Link to full agent processing view
                            if st.button("🚀 View Full Multi-Agent Analysis"):
                                st.session_state.selected_claim_id = claim_id
                                st.switch_page("🤖 Agent Processing")
                        else:
                            st.info("No agent processing data available. Process the claim to see agent collaboration.")
                    
                    with tab3:
                        if claim_details.get('decision_log'):
                            decision = claim_details['decision_log']
                            st.subheader("AI Decision Analysis")
                            
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                st.metric("Decision", decision['decision'])
                                st.metric("Confidence", f"{decision['confidence_score']:.1f}%")
                            
                            with col2:
                                st.markdown("**Reasoning:**")
                                st.write(decision['reasoning_text'])
                        else:
                            st.info("Claim has not been processed yet.")
                            
                            if claim_details['status'] == 'PENDING':
                                if st.button("Process Claim Now"):
                                    with st.spinner("Processing..."):
                                        result = api.process_claim(claim_id)
                                        if result:
                                            st.success("Claim processed!")
                                            st.rerun()
                    
                    with tab4:
                        fraud_analysis = api.get_fraud_analysis(claim_id)
                        if fraud_analysis:
                            st.subheader("Fraud Risk Analysis")
                            
                            col1, col2 = st.columns([1, 2])
                            
                            with col1:
                                fraud_score = fraud_analysis['fraud_score']
                                if fraud_score > 70:
                                    st.error(f"🚨 High Risk: {fraud_score:.1f}/100")
                                elif fraud_score > 30:
                                    st.warning(f"⚠️ Medium Risk: {fraud_score:.1f}/100")
                                else:
                                    st.success(f"✅ Low Risk: {fraud_score:.1f}/100")
                            
                            with col2:
                                if fraud_analysis['risk_factors']:
                                    st.markdown("**Risk Factors:**")
                                    for factor in fraud_analysis['risk_factors']:
                                        st.write(f"• {factor}")
                                else:
                                    st.write("No risk factors detected.")
                    
                    with tab5:
                        if claim_details.get('exception_logs'):
                            st.subheader("Exception History")
                            for exception in claim_details['exception_logs']:
                                with st.expander(f"Exception: {exception['exception_type']}"):
                                    st.write(f"**Resolution:** {exception['resolution_action']}")
                                    if exception.get('learned_from_case_id'):
                                        st.info(f"🧠 Learned from case: {exception['learned_from_case_id']}")
                                    st.write(f"**Date:** {format_datetime(exception['created_at'])}")
                        else:
                            st.info("No exceptions recorded for this claim.")
        else:
            st.warning("Please enter a Claim ID")