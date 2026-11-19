import streamlit as st
import main

st.set_page_config(page_title="Take A Tour", page_icon="✈️")

st.title("✈️ Take A Tour: Personal Trip Planner")
st.write("Plan your trip based on your interests and budget!")

# Initialize session state variables
if "itinerary" not in st.session_state:
    st.session_state.itinerary = []
if "budget" not in st.session_state:
    st.session_state.budget = 0

# --- USER PREFERENCE FORM ---
with st.form("preferences_form"):
    st.subheader("1. Set your trip preferences")
    destination = st.text_input("Destination:", "Accra")
    days = st.number_input("Number of days:", min_value=1, max_value=7, value=2)
    interests = st.text_input("Interests (comma separated):", "history, local food")
    
    # Slider for budget. Added a "0" option to demonstrate infeasible requests
    budget = st.number_input("Activities budget per person (GHS):", min_value=0, max_value=5000, value=600)
    
    submit_button = st.form_submit_button("Generate Itinerary")

if submit_button:
    with st.spinner("Searching the web and building your plan..."):
        # Save budget to session state for revision checks
        st.session_state.budget = budget
        
        # 1. Fetch web data using Tavily
        search_results = main.fetch_activities(destination, interests)
        
        # 2. Ask OpenAI to build the plan
        itinerary = main.generate_itinerary(destination, days, interests, budget, search_results)
        st.session_state.itinerary = itinerary

# --- DISPLAY ITINERARY ---
if st.session_state.itinerary:
    st.divider()
    st.subheader("2. Your Day-by-Day Itinerary")
    
    # Display estimated labels
    st.info("ℹ️ **Note:** Estimated prices are fictional per-person estimates. Transport, meals outside listed experiences, and accommodation are excluded. Please verify details before visiting.")
    
    # Group by day for display
    for item in st.session_state.itinerary:
        st.markdown(f"### Day {item['day']}: {item['name']}")
        st.write(f"**Estimated Cost:** {item['price_ghs']} GHS")
        st.write(f"**Duration:** {item['duration_hours']} hours")
        st.write(f"*Why this fits you:* {item['explanation']}")
        st.write("---")

    # --- PYTHON CALCULATIONS & CHECKS ---
    st.subheader("3. Budget & Duration Check")
    is_valid, messages, total_cost, daily_hours = main.check_plan_feasibility(st.session_state.itinerary, st.session_state.budget)
    
    st.write(f"**Total Calculated Cost:** {total_cost} GHS (Budget: {st.session_state.budget} GHS)")
    st.write(f"**Daily Activity Hours:** {daily_hours}")
    
    if is_valid:
        st.success("✅ Plan is feasible and within your limits!")
    else:
        st.error("❌ Infeasible Request! Here is why:")
        for msg in messages:
            st.write(f"- {msg}")

    # --- DOWNLOAD BUTTON ---
    st.download_button(
        label="📥 Download Itinerary",
        data=main.format_itinerary_for_download(st.session_state.itinerary),
        file_name="my_trip_plan.txt",
        mime="text/plain"
    )

    # --- REVISION FLOW ---
    st.divider()
    st.subheader("4. Refine your plan")
    revision_request = st.text_input("How would you like to change the plan? (e.g., 'Make it cheaper', 'Add more food activities')")
    
    if st.button("Apply Revision"):
        if revision_request:
            with st.spinner("Updating your plan..."):
                updated_itinerary = main.revise_itinerary(
                    st.session_state.itinerary, 
                    revision_request, 
                    destination, 
                    st.session_state.budget
                )
                st.session_state.itinerary = updated_itinerary
                st.rerun() # Rerun the app to show the new plan
        else:
            st.warning("Please enter a revision request first.")

# --- INFEASIBLE REQUEST DEMO ---
st.divider()
st.subheader("🧪 Demonstration: Infeasible Request")
st.write("Click the button below to see what happens when you request 2 days in Accra with only 10 GHS for activities.")
if st.button("Try Infeasible Request (Low Budget)"):
    with st.spinner("Searching..."):
        # Force a very low budget
        st.session_state.budget = 10
        search_results = main.fetch_activities("Accra", "history, local food")
        st.session_state.itinerary = main.generate_itinerary("Accra", 2, "history, local food", 10, search_results)
    st.rerun()