import os
import json
from dotenv import load_dotenv
from tavily import TavilyClient
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize clients
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def fetch_activities(destination, interests):
    """Uses Tavily to search the web for activities."""
    query = f"Best activities, tours, and historical sites in {destination} for people interested in {interests}"
    response = tavily_client.search(query=query, max_results=5)
    
    # Combine search results into one text block
    search_text = ""
    for result in response['results']:
        search_text += result['content'] + "\n"
    return search_text

def generate_itinerary(destination, days, interests, budget, search_text):
    """Uses OpenAI to structure the plan into a strict JSON format."""
    prompt = f"""
    You are a helpful travel planner. Based on the following web search results about {destination}:
    
    {search_text}
    
    Create a {days}-day itinerary for a traveler interested in {interests} with a total activities budget of {budget} GHS.
    
    You MUST output ONLY a valid JSON list of dictionaries. Do not include any other text or markdown like ```json.
    Each dictionary must have exactly these keys:
    - "day": (integer, e.g., 1)
    - "activity_id": (integer, unique for each activity)
    - "name": (string, name of activity)
    - "price_ghs": (integer, estimated cost in GHS)
    - "duration_hours": (integer, estimated hours to complete)
    - "explanation": (string, why this fits the user's interests)
    
    Ensure the total price does not exceed {budget} GHS and each day does not exceed 6 hours of activities.
    """
    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    # Clean up the response and convert it to a Python list of dictionaries
    raw_text = response.choices[0].message.content.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:-3]
    
    try:
        itinerary = json.loads(raw_text)
    except:
        # Fallback if AI fails to format perfectly
        itinerary = []
        
    return itinerary

def calculate_totals(itinerary):
    """Pure Python: Calculates total cost and daily durations."""
    total_cost = 0
    daily_hours = {}
    
    for item in itinerary:
        total_cost += item["price_ghs"]
        day = item["day"]
        
        if day not in daily_hours:
            daily_hours[day] = 0
        daily_hours[day] += item["duration_hours"]
        
    return total_cost, daily_hours

def check_plan_feasibility(itinerary, budget):
    """Pure Python: Checks if the plan is valid based on budget and daily limits."""
    total_cost, daily_hours = calculate_totals(itinerary)
    
    is_valid = True
    messages = []
    
    if total_cost > budget:
        is_valid = False
        messages.append(f"Over budget: Total cost is {total_cost} GHS, which exceeds your budget of {budget} GHS.")
        
    for day, hours in daily_hours.items():
        if hours > 6:
            is_valid = False
            messages.append(f"Day {day} is too packed: {hours} hours of activities (max is 6 hours).")
            
    if not messages:
        messages.append("Plan is feasible! Total cost and daily hours are within limits.")
        
    return is_valid, messages, total_cost, daily_hours

def revise_itinerary(current_itinerary, revision_request, destination, budget):
    """Uses OpenAI to update the existing plan based on a new request."""
    prompt = f"""
    Here is the current itinerary for {destination}:
    {json.dumps(current_itinerary)}
    
    The user wants to make this change: "{revision_request}"
    
    Update the itinerary based on this request. Output ONLY a valid JSON list of dictionaries with the exact same keys as before ("day", "activity_id", "name", "price_ghs", "duration_hours", "explanation").
    Keep the total budget under {budget} GHS and daily hours under 6.
    """
    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    raw_text = response.choices[0].message.content.strip()
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:-3]
        
    try:
        return json.loads(raw_text)
    except:
        return current_itinerary # Return old one if parsing fails

def format_itinerary_for_download(itinerary):
    """Converts the list of dictionaries into a simple text string."""
    text = "Your Personal Trip Planner Itinerary\n"
    text += "===================================\n\n"
    for item in itinerary:
        text += f"Day {item['day']}: {item['name']}\n"
        text += f"Cost: {item['price_ghs']} GHS | Duration: {item['duration_hours']} hours\n"
        text += f"Why: {item['explanation']}\n\n"
    return text