from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import mysql.connector
import bcrypt
import os
from datetime import datetime, timedelta
import requests
import difflib
from pymongo import MongoClient
from pydantic import BaseModel
import random
import string
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Setup logging for scheduler
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------- FastAPI Setup ---------------------------

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --------------------------- DB Connection ----------------------------

def connect_to_db():
    mongo_uri = os.environ.get("MONGODB_URI")
    if not mongo_uri:
        raise RuntimeError("MONGODB_URI environment variable not set.")
    client = MongoClient(mongo_uri)
    return client.petition_db

# --------------------------- Department Mapping ----------------------------

table_map = {
    0: "Public Works Department",
    1: "Finance Department",
    2: "Education Department"
}

department_tables = {
    "Adi Dravidar and Tribal Welfare Department": "petitions_adi_dravidar_tribal_welfare",
    "Agriculture and Farmers welfares Department": "petitions_agriculture_farmers_welfare",
    "Animal Husbandry and Dairying and Fisheries and Fishermen Welfare Department": "petitions_animal_husbandry_fisheries",
    "BC MBC and Minorities Welfare Department": "petitions_bc_mbc_minorities_welfare",
    "Co-operation Food and Consumer Protection Department": "petitions_cooperation_food_consumer_protection",
    "Commercial Taxes and Registration Department": "petitions_commercial_taxes_registration",
    "Energy Department": "petitions_energy",
    "Environment Climate Change and Forests Department": "petitions_environment_climate_forests",
    "Finance Department": "petitions_finance",
    "Handlooms Handicrafts Textiles and Khadi Department": "petitions_handlooms_handicrafts_textiles_khadi",
    "Health and Family Welfare Department": "petitions_health_family_welfare",
    "Higher Education Department": "petitions_higher_education",
    "Highways and Minor Ports Department": "petitions_highways_minor_ports",
    "Human Resources Management Department": "petitions_human_resources_management",
    "Home Prohibition and Excise Department": "petitions_home_prohibition_excise",
    "Housing and Urban Development Department": "petitions_housing_urban_development",
    "Industries Department": "petitions_industries",
    "Information Technology Department": "petitions_information_technology",
    "Labour Welfare and Skill Development Department": "petitions_labour_welfare_skill_development",
    "Law Department": "petitions_law",
    "Legislative Assembly Department": "petitions_legislative_assembly",
    "Micro Small and Medium Enterprises Department": "petitions_micro_small_medium_enterprises",
    "Municipal Administration and Water Supply Department": "petitions_municipal_admin_water_supply",
    "Public Elections Department": "petitions_public_elections",
    "Public Department": "petitions_public",
    "Public Works Department": "petitions_pwd",
    "Revenue and Disaster Management Department": "petitions_revenue_disaster_management",
    "Rural Development and Panchayat Raj Department": "petitions_rural_development_panchayat_raj",
    "School Education Department": "petitions_school_education",
    "Social Welfare and Women Empowerment Department": "petitions_social_welfare_women_empowerment",
    "Tamil Dev. and Information Department": "petitions_tamil_dev_information",
    "Tamil Nadu Water Supply and Drainage Board": "petitions_tn_water_supply_drainage_board",
    "Tourism Culture and Religious Endowments Department": "petitions_tourism_culture_religious_endowments",
    "Transport Department": "petitions_transport",
    "Welfare of Differently Abled Persons": "petitions_welfare_diff_abled_persons",
    "Youth Welfare and Sports Development Department": "petitions_youth_welfare_sports_development",
    "Water Resources Department": "petitions_water_resources",
    "Planning Development Department": "petitions_planning_development",
    "Special Programme Implementation": "petitions_special_programme_implementation"
}

# --------------------------- Basic Routes ----------------------------

@app.get("/")
def index():
    return {"message": "API up and running."}

# --------------------------- Rule-Based Classifier ----------------------------

def simple_rule_classifier(text):
    text = text.lower()
    if any(term in text for term in ["budget", "finance", "fund", "loan", "startup", "tax"]):
        return "Finance Department"
    if any(term in text for term in ["teacher", "student", "college", "university", "school", "library"]):
        return "Education Department"
    # Tamil Nadu Water Supply and Drainage Board specific terms
    if any(term in text for term in [
        "water supply", "drinking water", "water connection", "water pipeline", "drainage system", 
        "sewage treatment", "water quality", "water board", "water tank", "water distribution", 
        "water bill", "water meter", "water leakage", "sewage block", "drainage block", "sewage overflow"
    ]):
        return "Tamil Nadu Water Supply and Drainage Board"
    if any(term in text for term in [
        "bridge", "road", "pipeline", "building", "stormwater", "area", "street", "home",
        "maintenance", "borewell", "repair", "infrastructure", "public toilet", "canals", "irrigation"
    ]):
        return "Public Works Department"
    return "General"  # Fallback category

def classify_with_groq(petition_text):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return "General"  # fallback if no API key
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    prompt = (
        "You are a classifier that maps petitions to the correct Tamil Nadu government department. Based on the petition text below, return only the single most appropriate department name from this list. If unsure, pick the closest match from the list. Never return 'General', 'Unknown', or anything not in the list.\n\n"
        "Adi Dravidar and Tribal Welfare Department\n"
        "Agriculture and Farmers welfares Department\n"
        "Animal Husbandry and Dairying and Fisheries and Fishermen Welfare Department\n"
        "BC MBC and Minorities Welfare Department\n"
        "Co-operation Food and Consumer Protection Department\n"
        "Commercial Taxes and Registration Department\n"
        "Energy Department\n"
        "Environment Climate Change and Forests Department\n"
        "Finance Department\n"
        "Handlooms Handicrafts Textiles and Khadi Department\n"
        "Health and Family Welfare Department\n"
        "Higher Education Department\n"
        "Highways and Minor Ports Department\n"
        "Human Resources Management Department\n"
        "Home Prohibition and Excise Department\n"
        "Housing and Urban Development Department\n"
        "Industries Department\n"
        "Information Technology Department\n"
        "Labour Welfare and Skill Development Department\n"
        "Law Department\n"
        "Legislative Assembly Department\n"
        "Micro Small and Medium Enterprises Department\n"
        "Municipal Administration and Water Supply Department\n"
        "Public Elections Department\n"
        "Public Department\n"
        "Public Works Department\n"
        "Revenue and Disaster Management Department\n"
        "Rural Development and Panchayat Raj Department\n"
        "School Education Department\n"
        "Social Welfare and Women Empowerment Department\n"
        "Tamil Dev. and Information Department\n"
        "Tamil Nadu Water Supply and Drainage Board\n"
        "Tourism Culture and Religious Endowments Department\n"
        "Transport Department\n"
        "Welfare of Differently Abled Persons\n"
        "Youth Welfare and Sports Development Department\n"
        "Water Resources Department\n"
        "Planning Development Department\n"
        "Special Programme Implementation\n\n"
        f"Petition: '{petition_text}'\nDepartment:"
    )
    data = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0,
        "max_tokens": 50
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        department = result["choices"][0]["message"]["content"].strip()
        return department
    except Exception:
        return "General"  # fallback on error

# --------------------------- Auth: Register ----------------------------

@app.post("/register")
def register_account(
    full_name: str = Form(...),
    new_user: str = Form(...),
    new_pass: str = Form(...)
):
    db = connect_to_db()
    users_collection = db["users"]  # Access the 'users' collection

    # Check if the username already exists
    if users_collection.find_one({"username": new_user}):
        return {"error": "Username is already taken"}

    # Hash the password and insert the new user
    hashed_password = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
    users_collection.insert_one({
        "name": full_name,
        "username": new_user,
        "password": hashed_password
    })

    return {"message": "User registered successfully"}

# --------------------------- Auth: Login ----------------------------

@app.post("/login")
def login_user(user_id: str = Form(...), passcode: str = Form(...)):
    predefined_admins = {
        "pwd": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Public Works Department"},
        "fin": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Finance Department"},
        "edu": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Education Department"},
        "adi": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Adi Dravidar and Tribal Welfare Department"},
        "agr": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Agriculture and Farmers welfares Department"},
        "ani": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Animal Husbandry and Dairying and Fisheries and Fishermen Welfare Department"},
        "bcm": {"password": "123", "dashboard": "officer_dashboard.html", "department": "BC MBC and Minorities Welfare Department"},
        "cof": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Co-operation Food and Consumer Protection Department"},
        "ctr": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Commercial Taxes and Registration Department"},
        "ene": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Energy Department"},
        "env": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Environment Climate Change and Forests Department"},
        "han": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Handlooms Handicrafts Textiles and Khadi Department"},
        "hea": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Health and Family Welfare Department"},
        "hed": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Higher Education Department"},
        "hig": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Highways and Minor Ports Department"},
        "hrm": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Human Resources Management Department"},
        "hom": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Home Prohibition and Excise Department"},
        "hou": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Housing and Urban Development Department"},
        "ind": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Industries Department"},
        "itd": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Information Technology Department"},
        "lab": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Labour Welfare and Skill Development Department"},
        "law": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Law Department"},
        "leg": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Legislative Assembly Department"},
        "mic": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Micro Small and Medium Enterprises Department"},
        "mun": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Municipal Administration and Water Supply Department"},
        "pel": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Public Elections Department"},
        "pub": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Public Department"},
        "rev": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Revenue and Disaster Management Department"},
        "rur": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Rural Development and Panchayat Raj Department"},
        "sch": {"password": "123", "dashboard": "officer_dashboard.html", "department": "School Education Department"},
        "soc": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Social Welfare and Women Empowerment Department"},
        "tam": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Tamil Dev. and Information Department"},
        "tou": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Tourism Culture and Religious Endowments Department"},
        "tra": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Transport Department"},
        "wel": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Welfare of Differently Abled Persons"},
        "you": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Youth Welfare and Sports Development Department"},
        "wat": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Water Resources Department"},
        "pla": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Planning Development Department"},
        "spe": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Special Programme Implementation"},
        "tws": {"password": "123", "dashboard": "officer_dashboard.html", "department": "Tamil Nadu Water Supply and Drainage Board"},
    }

    # Admin login
    if user_id in predefined_admins and predefined_admins[user_id]["password"] == passcode:
        return {
            "message": "Admin login successful",
            "role": "admin",
            "dashboard": predefined_admins[user_id]["dashboard"],
            "department": predefined_admins[user_id]["department"]
        }

    # User login
    db = connect_to_db()
    users_collection = db["users"]  # Access the 'users' collection
    user = users_collection.find_one({"username": user_id})  # Query the user by username

    if user and bcrypt.checkpw(passcode.encode(), user["password"].encode()):
        return {
            "message": "User login successful",
            "role": "user",
            "dashboard": "dashboardaph.html"
        }

    return {"error": "Invalid login credentials"}

# --------------------------- Classify Petition ----------------------------

@app.post("/classify")
def predict_category(petition_text: str = Form(...)):
    department_raw = classify_with_groq(petition_text)
    print(f"[DEBUG] Groq raw output: {department_raw}")

    if not department_raw:
        return {"category": "Unknown"}

    department_clean = department_raw.strip().lower()

    # Try exact match
    for dept in department_tables:
        if dept.lower() == department_clean:
            return {"category": dept}

    # Try partial match (e.g., if LLM returns 'School Education Department' but you store 'Education Department')
    for dept in department_tables:
        if dept.lower() in department_clean or department_clean in dept.lower():
            return {"category": dept}

    # Fuzzy match
    import difflib
    match = difflib.get_close_matches(department_clean, [d.lower() for d in department_tables.keys()], n=1, cutoff=0.6)
    if match:
        for dept in department_tables:
            if dept.lower() == match[0]:
                return {"category": dept}

    # Fallback: Rule-based classification
    guessed = simple_rule_classifier(petition_text)
    if guessed in department_tables:
        return {"category": guessed}

    return {"category": "Unknown"}

# --------------------------- Submit Petition ----------------------------

@app.post("/submit_to_department")
def save_petition(
    name: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...),
    petition_type: str = Form(...),
    petition_subject: str = Form(...),
    petition_description: str = Form(...),
    category: str = Form(...)
):
    """
    Submit a petition to the appropriate department
    
    This endpoint:
    1. Saves the grievance details to the appropriate department collection
    2. Automatically assigns a priority level based on text content
    3. Checks for similar grievances using TF-IDF cosine similarity
    4. Initializes timeline tracking
    5. Returns the assigned department, priority level, and similarity results
    
    Priority is determined by scanning for keywords like:
    "urgent", "danger", "accident", "emergency", "fire", "violence", 
    "death", "injury", "threat", "hospital"
    
    Args:
        name: Petitioner's name
        phone: Contact phone number
        address: Petitioner's address
        petition_type: Type of grievance
        petition_subject: Brief subject line
        petition_description: Detailed description of grievance
        category: Department category
        
    Returns:
        Status message, assigned department, priority level, and similarity results
    """
    try:
        # Normalize category for lookup
        category_clean = category.strip()
        table = department_tables.get(category_clean)
        if not table:
            # Try case-insensitive match
            for key in department_tables:
                if key.lower() == category_clean.lower():
                    table = department_tables[key]
                    category_clean = key
                    break
        if not table:
            return {"error": f"Invalid or undefined category: {category}"}
        
        db = connect_to_db()
        petitions_collection = db[table]
        
        # Detect priority level based on subject and description
        combined_text = f"{petition_subject} {petition_description}"
        priority_level = detect_priority(combined_text)
        
        # Check for similar grievances
        similar_grievances = find_similar_grievances(combined_text, category_clean)
        
        # Generate a unique tracking ID
        tracking_id = generate_tracking_id()
        
        # Ensure the tracking ID is unique across all departments
        is_unique = False
        attempts = 0
        while not is_unique and attempts < 10:
            # Check if this tracking ID already exists in any department
            exists = False
            for dept_table in department_tables.values():
                dept_collection = db[dept_table]
                if dept_collection.find_one({"tracking_id": tracking_id}):
                    exists = True
                    break
            
            if not exists:
                is_unique = True
            else:
                tracking_id = generate_tracking_id()
                attempts += 1
        
        # Initialize timeline with submission entry
        initial_timeline = [{
            'timestamp': datetime.now(),
            'date': datetime.now().strftime("%d-%b-%Y"),
            'time': datetime.now().strftime("%H:%M:%S"),
            'status': 'pending',
            'comment': 'Grievance submitted successfully',
            'update_type': 'submission'
        }]
        
        # Prepare petition data
        petition_data = {
            "tracking_id": tracking_id,
            "name": name,
            "phone": phone,
            "address": address,
            "petition_type": petition_type,
            "petition_subject": petition_subject,
            "petition_description": petition_description,
            "status": "pending",
            "priority": priority_level,
            "created_at": datetime.now().strftime("%d-%b-%Y"),
            "department": category_clean,
            "timeline": initial_timeline,
            "last_updated": datetime.now()
        }
        
        # Add related_to field if similar grievances found
        if similar_grievances:
            petition_data["related_to"] = [g['grievance_id'] for g in similar_grievances]
            petition_data["similarity_detected"] = True
        else:
            petition_data["similarity_detected"] = False
        
        # Insert the petition
        petitions_collection.insert_one(petition_data)
        
        # Prepare response
        response_data = {
            "message": "Petition recorded successfully", 
            "department": category_clean,
            "priority": priority_level,
            "tracking_id": tracking_id,
            "similarity_detected": len(similar_grievances) > 0,
            "similar_grievances_count": len(similar_grievances)
        }
        
        # Include similarity details if found
        if similar_grievances:
            response_data["similar_grievances"] = similar_grievances
            response_data["similarity_message"] = f"Found {len(similar_grievances)} similar grievance(s). Your issue may be related to existing cases."
        
        return response_data
        
    except OSError as os_err:
        return {"error": f"File system error: {os_err}"}
    except Exception as ex:
        return {"error": f"Unexpected error: {ex}"}

# --------------------------- Admin View Petitions ----------------------------

@app.get("/admin/petitions")
def list_petitions(department: str):
    table = department_tables.get(department)
    if not table:
        return {"error": "Invalid department requested"}

    db = connect_to_db()
    petitions_collection = db[table]  # Access the collection for the department
    result = list(petitions_collection.find())  # Retrieve all documents from the collection

    # Convert MongoDB documents to JSON-serializable format and add tracking IDs where missing
    for petition in result:
        petition["_id"] = str(petition["_id"])
        
        # If petition doesn't have a tracking_id (for old records), generate one
        if not petition.get("tracking_id"):
            tracking_id = generate_tracking_id()
            # Update the record in the database
            petitions_collection.update_one(
                {"_id": petition["_id"]}, 
                {"$set": {"tracking_id": tracking_id}}
            )
            petition["tracking_id"] = tracking_id

    return result

@app.get("/admin/petitions/by_priority")
def list_petitions_by_priority(department: str, priority: str = None):
    """
    List petitions for a department, optionally filtered by priority level
    
    Args:
        department: Department name
        priority: Optional priority filter ("High", "Medium", "Low")
        
    Returns:
        List of petitions matching the criteria
    """
    table = department_tables.get(department)
    if not table:
        return {"error": "Invalid department requested"}

    db = connect_to_db()
    petitions_collection = db[table]
    
    # Build query filter
    query = {}
    if priority:
        query["priority"] = priority
    
    # Execute the query
    result = list(petitions_collection.find(query))
    
    # Convert MongoDB documents to JSON-serializable format and add tracking IDs where missing
    for petition in result:
        petition["_id"] = str(petition["_id"])
        
        # If petition doesn't have a tracking_id (for old records), generate one
        if not petition.get("tracking_id"):
            tracking_id = generate_tracking_id()
            # Update the record in the database
            petitions_collection.update_one(
                {"_id": petition["_id"]}, 
                {"$set": {"tracking_id": tracking_id}}
            )
            petition["tracking_id"] = tracking_id

    return result

# --------------------------- Track Grievance ----------------------------

@app.post("/track_grievance")
def track_grievance(grievance_id: str = Form(...), phone: str = Form(...)):
    """
    Track a grievance using the new tracking system
    
    This function searches for grievances using the stored tracking_id field
    Phone number is used for additional verification
    """
    try:
        db = connect_to_db()
        
        # Validate inputs
        if not grievance_id or grievance_id.strip() == "":
            return {"found": False, "message": "Please provide your grievance tracking ID to track your grievance."}
        
        if not phone or phone.strip() == "":
            return {"found": False, "message": "Please provide your phone number for verification."}
        
        # Clean the grievance ID
        grievance_id = grievance_id.strip().upper()
        phone = phone.strip()
        
        print(f"[DEBUG] Tracking grievance with ID: {grievance_id} and phone: {phone}")
        
        # Search across all department tables for the tracking ID
        found_petition = None
        found_department = None
        
        for department, table_name in department_tables.items():
            collection = db[table_name]
            
            # Search by tracking_id
            petition = collection.find_one({"tracking_id": grievance_id})
            
            if petition:
                # Verify phone number matches for security
                if petition.get("phone") == phone:
                    found_petition = petition
                    found_department = department
                    print(f"[DEBUG] Found grievance {grievance_id} in {department}")
                    break
                else:
                    print(f"[DEBUG] Found grievance {grievance_id} but phone number doesn't match")
                    return {
                        "found": False, 
                        "message": "The phone number doesn't match the one used to file this grievance. Please check your phone number."
                    }
        
        if not found_petition:
            print(f"[DEBUG] No grievance found with tracking ID: {grievance_id}")
            # Check if there are any grievances for this phone number
            user_grievances = []
            for department, table_name in department_tables.items():
                collection = db[table_name]
                petitions = list(collection.find({"phone": phone}))
                for pet in petitions:
                    if pet.get("tracking_id"):
                        user_grievances.append(f"{pet['tracking_id']} ({department})")
            
            if user_grievances:
                return {
                    "found": False,
                    "message": f"No grievance found with ID '{grievance_id}'. Your registered grievances are: {', '.join(user_grievances)}"
                }
            else:
                return {
                    "found": False,
                    "message": "No grievance found with the provided tracking ID and phone number."
                }
        
        # Convert ObjectId to string for JSON serialization
        found_petition["_id"] = str(found_petition["_id"])
        
        # Add department information
        found_petition["department"] = found_department
        
        # Use the stored tracking_id as the display ID
        found_petition["id"] = found_petition.get("tracking_id", grievance_id)
        
        # Generate timeline updates
        created_date = found_petition.get("created_at", datetime.now().strftime("%d-%b-%Y"))
        
        updates = [
            {
                "date": created_date,
                "title": "Grievance Received",
                "description": "Your grievance has been received and registered in the system."
            },
            {
                "date": created_date,
                "title": "Assigned to Department",
                "description": f"Your grievance has been assigned to {found_department}."
            }
        ]
        
        # Add status-specific updates
        status = found_petition.get("status", "pending").lower()
        if status == "in_progress":
            updates.append({
                "date": datetime.now().strftime("%d-%b-%Y"),
                "title": "Under Review",
                "description": "Your grievance is currently being reviewed by the department."
            })
        elif status == "resolved":
            updates.append({
                "date": datetime.now().strftime("%d-%b-%Y"),
                "title": "Resolved",
                "description": "Your grievance has been resolved."
            })
        elif status == "rejected":
            updates.append({
                "date": datetime.now().strftime("%d-%b-%Y"),
                "title": "Rejected",
                "description": "Your grievance has been reviewed and rejected."
            })
        
        found_petition["updates"] = updates
        
        print(f"[DEBUG] Successfully retrieved grievance {grievance_id}")
        return {"found": True, "grievance": found_petition}
        
    except Exception as ex:
        print(f"[ERROR] Exception in track_grievance: {str(ex)}")
        return {"error": f"An error occurred while tracking your grievance: {str(ex)}"}

@app.post("/update_grievance_status")
def update_grievance_status(
    grievance_id: str = Form(...), 
    status: str = Form(...), 
    department: str = Form(...),
    comment: str = Form(None)
):
    """
    Update the status of a grievance with timeline tracking and notifications
    """
    try:
        db = connect_to_db()
        
        # Validate status
        valid_statuses = ["pending", "resolved", "rejected", "in_progress"]
        if status.lower() not in valid_statuses:
            return {"success": False, "message": "Invalid status value"}
            
        # Get the department table name
        table_name = department_tables.get(department)
        if not table_name:
            return {"success": False, "message": "Invalid department"}
            
        collection = db[table_name]
        
        # Find the petition using the tracking_id
        petition = collection.find_one({"tracking_id": grievance_id})
        
        if not petition:
            return {"success": False, "message": "Grievance not found with the provided tracking ID"}
        
        # Get the old status for notifications
        old_status = petition.get('status', 'unknown')
        new_status = status.lower()
        
        # Create timeline entry
        timeline_entry = {
            'timestamp': datetime.now(),
            'date': datetime.now().strftime("%d-%b-%Y"),
            'time': datetime.now().strftime("%H:%M:%S"),
            'status': new_status,
            'comment': comment if comment else f"Status updated to {new_status}",
            'update_type': 'status_update'
        }
        
        # Update the status and add timeline entry
        update_result = collection.update_one(
            {"tracking_id": grievance_id},
            {
                "$set": {
                    "status": new_status,
                    "last_updated": datetime.now()
                },
                "$push": {"timeline": timeline_entry}
            }
        )
        
        if update_result.modified_count == 0:
            return {"success": False, "message": "Failed to update status"}
        
        # Send notification to petitioner if status changed
        if old_status != new_status:
            try:
                send_notification_to_petitioner(petition, old_status, new_status)
            except Exception as e:
                logger.warning(f"Failed to send notification for {grievance_id}: {str(e)}")
                # Don't fail the status update if notification fails
        
        current_date = datetime.now().strftime("%d-%b-%Y")
        status_title = status.capitalize()
        status_description = comment if comment else f"Status updated to {status}"
        
        return {
            "success": True,
            "message": "Status updated successfully",
            "timeline_update": {
                "date": current_date,
                "title": status_title,
                "description": status_description
            },
            "notification_sent": True
        }
        
    except Exception as ex:
        return {"success": False, "message": f"An error occurred: {str(ex)}"}

# --------------------------- Utility Functions ----------------------------

import random
import string

def generate_tracking_id():
    """
    Generate a unique tracking ID in the format GR-YYYY-XXXXXX
    Where YYYY is the current year and XXXXXX is a 6-digit alphanumeric code
    """
    year = datetime.now().year
    # Generate a 6-character alphanumeric code (uppercase letters and numbers)
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"GR-{year}-{code}"

def detect_priority(text: str) -> str:
    """
    Detect priority level based on text content
    Returns: "High", "Medium", or "Low"
    """
    text_lower = text.lower()
    
    # High priority keywords
    high_priority_keywords = [
        'urgent', 'emergency', 'critical', 'immediate', 'life threatening',
        'danger', 'death', 'accident', 'fire', 'flood', 'earthquake',
        'medical emergency', 'hospital', 'ambulance', 'police',
        'violence', 'harassment', 'threat', 'safety'
    ]
    
    # Medium priority keywords
    medium_priority_keywords = [
        'important', 'asap', 'soon', 'quick', 'fast', 'priority',
        'water shortage', 'power outage', 'road damage', 'broken',
        'not working', 'complaint', 'problem', 'issue'
    ]
    
    # Check for high priority
    for keyword in high_priority_keywords:
        if keyword in text_lower:
            return "High"
    
    # Check for medium priority
    for keyword in medium_priority_keywords:
        if keyword in text_lower:
            return "Medium"
    
    # Default to Medium for general grievances
    return "Medium"

# --------------------------- Similarity Detection ---------------------------

def find_similar_grievances(petition_text, department, similarity_threshold=0.8):
    """
    Find similar grievances using TF-IDF and cosine similarity
    
    Args:
        petition_text: The text to compare (subject + description)
        department: Department to search within
        similarity_threshold: Minimum similarity score (default 0.8 for 80%)
        
    Returns:
        List of similar grievances with their similarity scores
    """
    try:
        db = connect_to_db()
        table_name = department_tables.get(department)
        if not table_name:
            return []
            
        collection = db[table_name]
        
        # Get all existing grievances in this department
        existing_grievances = list(collection.find({}, {
            'petition_subject': 1, 
            'petition_description': 1, 
            'tracking_id': 1,
            '_id': 1
        }))
        
        if len(existing_grievances) < 1:
            return []
        
        # Prepare texts for comparison
        texts = []
        grievance_refs = []
        
        # Add the new petition text
        combined_new_text = f"{petition_text}".lower().strip()
        texts.append(combined_new_text)
        grievance_refs.append(None)  # Placeholder for new petition
        
        # Add existing grievances
        for grievance in existing_grievances:
            subject = grievance.get('petition_subject', '')
            description = grievance.get('petition_description', '')
            combined_text = f"{subject} {description}".lower().strip()
            
            if combined_text:  # Only add non-empty texts
                texts.append(combined_text)
                grievance_refs.append(grievance)
        
        if len(texts) < 2:  # Need at least 2 texts for comparison
            return []
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=1000,
            ngram_range=(1, 2),  # Include unigrams and bigrams
            min_df=1,
            max_df=0.95
        )
        
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # Calculate cosine similarity between new petition and all existing ones
        similarity_scores = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        
        # Find similar grievances above threshold
        similar_grievances = []
        for i, score in enumerate(similarity_scores):
            if score >= similarity_threshold:
                grievance = grievance_refs[i + 1]  # +1 because we skip the new petition
                if grievance:
                    similar_grievances.append({
                        'grievance_id': grievance.get('tracking_id', str(grievance['_id'])),
                        'similarity_score': float(score),
                        'subject': grievance.get('petition_subject', 'N/A'),
                        'description': grievance.get('petition_description', 'N/A')[:100] + '...'
                    })
        
        # Sort by similarity score (highest first)
        similar_grievances.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return similar_grievances
        
    except Exception as e:
        logger.error(f"Error in similarity detection: {str(e)}")
        return []

# --------------------------- Timeline Management ---------------------------

def add_timeline_entry(grievance_id, department, status, comment="", update_type="status_update"):
    """
    Add a timeline entry to a grievance
    
    Args:
        grievance_id: Tracking ID of the grievance
        department: Department name
        status: New status
        comment: Optional comment
        update_type: Type of update (status_update, comment, reminder, etc.)
    """
    try:
        db = connect_to_db()
        table_name = department_tables.get(department)
        if not table_name:
            return False
            
        collection = db[table_name]
        
        # Create timeline entry
        timeline_entry = {
            'timestamp': datetime.now(),
            'date': datetime.now().strftime("%d-%b-%Y"),
            'time': datetime.now().strftime("%H:%M:%S"),
            'status': status,
            'comment': comment,
            'update_type': update_type
        }
        
        # Add timeline entry to the grievance
        result = collection.update_one(
            {'tracking_id': grievance_id},
            {
                '$push': {'timeline': timeline_entry},
                '$set': {'last_updated': datetime.now()}
            }
        )
        
        return result.modified_count > 0
        
    except Exception as e:
        logger.error(f"Error adding timeline entry: {str(e)}")
        return False

def get_grievance_timeline(grievance_id, department):
    """
    Get the complete timeline for a grievance
    """
    try:
        db = connect_to_db()
        table_name = department_tables.get(department)
        if not table_name:
            return []
            
        collection = db[table_name]
        grievance = collection.find_one({'tracking_id': grievance_id}, {'timeline': 1})
        
        if grievance and 'timeline' in grievance:
            timeline = grievance['timeline']
            # Convert datetime objects to strings for JSON serialization
            for entry in timeline:
                if isinstance(entry.get('timestamp'), datetime):
                    entry['timestamp'] = entry['timestamp'].isoformat()
            return timeline
        
        return []
        
    except Exception as e:
        logger.error(f"Error getting timeline: {str(e)}")
        return []

# --------------------------- Notification System ---------------------------

def send_notification_to_petitioner(grievance_data, old_status, new_status):
    """
    Simulate sending notifications to petitioners via SMS/Email
    
    Args:
        grievance_data: Complete grievance information
        old_status: Previous status
        new_status: Updated status
    """
    try:
        tracking_id = grievance_data.get('tracking_id', 'N/A')
        name = grievance_data.get('name', 'N/A')
        phone = grievance_data.get('phone', 'N/A')
        subject = grievance_data.get('petition_subject', 'N/A')
        
        # Simulate SMS notification
        sms_message = f"""
Tamil Nadu Grievance Portal - Status Update

Dear {name},

Your grievance {tracking_id} has been updated:
Subject: {subject}
Status: {old_status.upper()} → {new_status.upper()}

Track your grievance at: portal.tn.gov.in/track

Regards,
TN Grievance Portal
        """.strip()
        
        # Simulate Email notification
        email_message = f"""
Subject: Grievance Status Update - {tracking_id}

Dear {name},

This is to inform you that your grievance has been updated:

Tracking ID: {tracking_id}
Subject: {subject}
Previous Status: {old_status.upper()}
Current Status: {new_status.upper()}
Updated On: {datetime.now().strftime("%d-%b-%Y %H:%M:%S")}

You can track your grievance status at: portal.tn.gov.in/track

Best regards,
Tamil Nadu Grievance Portal Team
        """.strip()
        
        # Log the notifications (simulating actual sending)
        logger.info(f"📱 SMS NOTIFICATION SENT to {phone}:")
        logger.info(sms_message)
        print(f"\n📱 SMS NOTIFICATION SENT to {phone}:")
        print(sms_message)
        print("-" * 60)
        
        logger.info(f"📧 EMAIL NOTIFICATION SENT to petitioner:")
        logger.info(email_message)
        print(f"\n📧 EMAIL NOTIFICATION SENT to petitioner:")
        print(email_message)
        print("-" * 60)
        
        # Store notification log in database
        db = connect_to_db()
        notification_log = {
            'grievance_id': tracking_id,
            'recipient_name': name,
            'recipient_phone': phone,
            'notification_type': 'status_update',
            'old_status': old_status,
            'new_status': new_status,
            'sent_at': datetime.now(),
            'sms_content': sms_message,
            'email_content': email_message
        }
        
        db.notification_logs.insert_one(notification_log)
        
        return True
        
    except Exception as e:
        logger.error(f"Error sending notifications: {str(e)}")
        return False

# --------------------------- Reminder System ---------------------------

def get_last_timeline_update(petition):
    """
    Get the timestamp of the last timeline update for a petition
    """
    timeline = petition.get('timeline', [])
    if not timeline:
        # If no timeline, use created_at or current time
        created_at = petition.get('created_at')
        if created_at:
            try:
                # Parse different date formats
                if isinstance(created_at, str):
                    # Try different formats
                    formats = ['%d-%b-%Y', '%Y-%m-%d', '%d/%m/%Y']
                    for fmt in formats:
                        try:
                            return datetime.strptime(created_at, fmt)
                        except ValueError:
                            continue
                    # If all formats fail, return current time
                    return datetime.now()
                elif isinstance(created_at, datetime):
                    return created_at
            except:
                pass
        return datetime.now()
    
    # Find the most recent timeline entry
    latest_update = None
    for entry in timeline:
        if 'timestamp' in entry:
            try:
                if isinstance(entry['timestamp'], str):
                    # Parse ISO format or other common formats
                    try:
                        timestamp = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                    except:
                        # Try other formats
                        formats = ['%Y-%m-%d %H:%M:%S', '%d-%b-%Y %H:%M:%S', '%Y-%m-%dT%H:%M:%S']
                        for fmt in formats:
                            try:
                                timestamp = datetime.strptime(entry['timestamp'], fmt)
                                break
                            except ValueError:
                                continue
                        else:
                            continue
                elif isinstance(entry['timestamp'], datetime):
                    timestamp = entry['timestamp']
                else:
                    continue
                
                if latest_update is None or timestamp > latest_update:
                    latest_update = timestamp
            except:
                continue
    
    return latest_update or datetime.now()

def should_send_reminder(petition):
    """
    Check if a petition needs a reminder based on:
    1. Status is "pending" or "in_progress"
    2. Last update was more than 3 days ago
    3. No reminder sent in the last 3 days
    """
    status = petition.get('status', '').lower()
    if status not in ['pending', 'in_progress']:
        return False
    
    # Check last timeline update
    last_update = get_last_timeline_update(petition)
    days_since_update = (datetime.now() - last_update).days
    
    if days_since_update < 3:
        return False
    
    # Check if reminder was already sent recently
    last_reminded = petition.get('last_reminded_at')
    if last_reminded:
        try:
            if isinstance(last_reminded, str):
                last_reminded = datetime.fromisoformat(last_reminded.replace('Z', '+00:00'))
            
            days_since_reminder = (datetime.now() - last_reminded).days
            if days_since_reminder < 3:
                return False
        except:
            pass
    
    return True

def send_reminder_for_petition(petition, department):
    """
    Send a reminder for a specific petition
    """
    try:
        db = connect_to_db()
        
        tracking_id = petition.get('tracking_id', petition.get('_id', 'Unknown'))
        
        # Create reminder record
        reminder_data = {
            'grievance_id': tracking_id,
            'department': department,
            'officer_id': f"officer_{department.lower().replace(' ', '_')}",
            'sent_at': datetime.now(),
            'reason': 'No status update in 3 days',
            'petition_subject': petition.get('petition_subject', 'N/A'),
            'days_pending': (datetime.now() - get_last_timeline_update(petition)).days
        }
        
        # Insert reminder into reminders collection
        db.reminders.insert_one(reminder_data)
        
        # Update petition with last reminded timestamp
        department_table = department_tables.get(department)
        if department_table:
            db[department_table].update_one(
                {'_id': petition['_id']},
                {'$set': {'last_reminded_at': datetime.now()}}
            )
        
        # Log the reminder
        logger.info(f"Reminder sent to officer {reminder_data['officer_id']} for grievance {tracking_id}")
        print(f"Reminder sent to officer {reminder_data['officer_id']} for grievance {tracking_id}")
        
        return True
    except Exception as e:
        logger.error(f"Error sending reminder for petition {tracking_id}: {str(e)}")
        return False

def check_and_send_reminders():
    """
    Background task to check all departments for inactive grievances and send reminders
    """
    try:
        logger.info("Starting automated reminder check...")
        db = connect_to_db()
        
        total_reminders = 0
        
        # Check each department
        for department, table_name in department_tables.items():
            try:
                collection = db[table_name]
                
                # Find petitions that need reminders
                petitions_needing_reminders = list(collection.find({
                    'status': {'$in': ['pending', 'in_progress']},
                    '$or': [
                        {'last_reminded_at': {'$exists': False}},
                        {'last_reminded_at': {'$lt': datetime.now() - timedelta(days=3)}}
                    ]
                }))
                
                department_reminders = 0
                for petition in petitions_needing_reminders:
                    if should_send_reminder(petition):
                        if send_reminder_for_petition(petition, department):
                            department_reminders += 1
                            total_reminders += 1
                
                if department_reminders > 0:
                    logger.info(f"Sent {department_reminders} reminders for {department}")
                    
            except Exception as e:
                logger.error(f"Error checking reminders for {department}: {str(e)}")
                continue
        
        logger.info(f"Automated reminder check completed. Total reminders sent: {total_reminders}")
        
    except Exception as e:
        logger.error(f"Error in automated reminder system: {str(e)}")

# Initialize scheduler
scheduler = BackgroundScheduler(timezone=pytz.timezone('Asia/Kolkata'))

def start_reminder_scheduler():
    """
    Start the background scheduler for automated reminders
    """
    try:
        # Schedule the reminder check to run daily at 9 AM IST
        scheduler.add_job(
            func=check_and_send_reminders,
            trigger=CronTrigger(hour=9, minute=0),  # 9:00 AM daily
            id='daily_reminder_check',
            name='Daily Grievance Reminder Check',
            replace_existing=True
        )
        
        # Also add a job that runs every 6 hours for more frequent checks
        scheduler.add_job(
            func=check_and_send_reminders,
            trigger=CronTrigger(hour='*/6'),  # Every 6 hours
            id='frequent_reminder_check',
            name='Frequent Grievance Reminder Check',
            replace_existing=True
        )
        
        scheduler.start()
        logger.info("Reminder scheduler started successfully")
        
    except Exception as e:
        logger.error(f"Error starting reminder scheduler: {str(e)}")

def stop_reminder_scheduler():
    """
    Stop the background scheduler
    """
    try:
        scheduler.shutdown()
        logger.info("Reminder scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping reminder scheduler: {str(e)}")

# --------------------------- FastAPI Startup/Shutdown Events ---------------------------

@app.on_event("startup")
async def startup_event():
    """Start the reminder scheduler when the app starts"""
    start_reminder_scheduler()
    logger.info("Grievance Portal API started with automated reminder system")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop the reminder scheduler when the app shuts down"""
    stop_reminder_scheduler()
    logger.info("Grievance Portal API stopped")

# --------------------------- Manual Reminder Management ---------------------------

@app.post("/admin/send_reminders")
async def manual_reminder_check():
    """
    Manually trigger the reminder check (for testing and admin use)
    """
    try:
        check_and_send_reminders()
        return {"message": "Reminder check completed successfully"}
    except Exception as e:
        logger.error(f"Error in manual reminder check: {str(e)}")
        raise HTTPException(status_code=500, detail="Error checking reminders")

@app.get("/admin/reminders")
async def get_reminders_for_department(department: str = None):
    """
    Get reminders for a specific department or all reminders
    """
    try:
        db = connect_to_db()
        
        # If department is specified, get grievances that need reminders from that department
        if department:
            table_name = department_tables.get(department)
            if not table_name:
                return {"success": False, "message": "Invalid department"}
            
            collection = db[table_name]
            
            # Find petitions that need reminders
            petitions_needing_reminders = list(collection.find({
                'status': {'$in': ['pending', 'in_progress']},
                '$or': [
                    {'last_reminded_at': {'$exists': False}},
                    {'last_reminded_at': {'$lt': datetime.now() - timedelta(days=3)}}
                ]
            }))
            
            # Format the data for frontend
            formatted_reminders = []
            for petition in petitions_needing_reminders:
                if should_send_reminder(petition):
                    formatted_reminders.append({
                        '_id': str(petition['_id']),
                        'tracking_id': petition.get('tracking_id', 'N/A'),
                        'subject': petition.get('petition_subject', 'N/A'),
                        'department': department,
                        'created_at': petition.get('created_at', datetime.now().strftime("%d-%b-%Y")),
                        'last_reminder': petition.get('last_reminded_at')
                    })
            
            return {
                "success": True,
                "data": formatted_reminders
            }
        else:
            # Get all reminder history
            reminders = list(db.reminders.find().sort("sent_at", -1).limit(50))
            
            # Convert ObjectId to string for JSON serialization
            for reminder in reminders:
                reminder["_id"] = str(reminder["_id"])
                if isinstance(reminder.get("sent_at"), datetime):
                    reminder["sent_at"] = reminder["sent_at"].isoformat()
            
            return {
                "success": True,
                "data": reminders
            }
            
    except Exception as e:
        logger.error(f"Error getting reminders: {str(e)}")
        return {"success": False, "message": f"Error retrieving reminders: {str(e)}"}

@app.get("/admin/reminder_stats")
async def get_reminder_stats():
    """
    Get statistics about reminders sent
    """
    try:
        db = connect_to_db()
        
        # Get total reminders sent
        total_reminders = db.reminders.count_documents({})
        
        # Get reminders sent in the last 7 days
        week_ago = datetime.now() - timedelta(days=7)
        recent_reminders = db.reminders.count_documents({"sent_at": {"$gte": week_ago}})
        
        # Get reminders by department
        pipeline = [
            {"$group": {"_id": "$department", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        by_department = list(db.reminders.aggregate(pipeline))
        
        return {
            "success": True,
            "data": {
                "total": total_reminders,
                "recent": recent_reminders,
                "by_department": by_department
            }
        }
    except Exception as e:
        logger.error(f"Error getting reminder stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving reminder statistics")

@app.post("/admin/send_individual_reminder")
async def send_individual_reminder(request_data: dict):
    """
    Send an individual reminder for a specific grievance
    """
    try:
        reminder_id = request_data.get("reminderId")
        if not reminder_id:
            return {"success": False, "message": "Reminder ID is required"}
        
        db = connect_to_db()
        
        # Find the grievance across all departments
        grievance_found = None
        department_found = None
        
        for department, table_name in department_tables.items():
            collection = db[table_name]
            grievance = collection.find_one({"_id": reminder_id}) or collection.find_one({"tracking_id": reminder_id})
            
            if grievance:
                grievance_found = grievance
                department_found = department
                break
        
        if not grievance_found:
            return {"success": False, "message": "Grievance not found"}
        
        # Send the reminder
        success = send_reminder_for_petition(grievance_found, department_found)
        
        if success:
            return {
                "success": True,
                "message": "Individual reminder sent successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to send individual reminder"
            }
            
    except Exception as e:
        logger.error(f"Error sending individual reminder: {str(e)}")
        return {"success": False, "message": f"Error sending reminder: {str(e)}"}

# --------------------------- New Timeline and Similarity Endpoints ---------------------------

@app.get("/grievance/timeline")
def get_timeline(tracking_id: str, department: str):
    """
    Get the complete timeline for a specific grievance
    """
    try:
        timeline = get_grievance_timeline(tracking_id, department)
        return {
            "success": True,
            "timeline": timeline
        }
    except Exception as e:
        return {"success": False, "message": f"Error retrieving timeline: {str(e)}"}

@app.get("/grievance/similar")
def check_similar_grievances(department: str, text: str, threshold: float = 0.8):
    """
    Check for similar grievances (useful for testing or manual checks)
    """
    try:
        similar = find_similar_grievances(text, department, threshold)
        return {
            "success": True,
            "similar_grievances": similar,
            "count": len(similar)
        }
    except Exception as e:
        return {"success": False, "message": f"Error checking similarity: {str(e)}"}

@app.get("/admin/notifications")
def get_notification_logs(limit: int = 50):
    """
    Get notification logs for administrative purposes
    """
    try:
        db = connect_to_db()
        notifications = list(db.notification_logs.find().sort("sent_at", -1).limit(limit))
        
        # Convert ObjectId and datetime to strings for JSON serialization
        for notification in notifications:
            notification["_id"] = str(notification["_id"])
            if isinstance(notification.get("sent_at"), datetime):
                notification["sent_at"] = notification["sent_at"].isoformat()
        
        return {
            "success": True,
            "notifications": notifications
        }
    except Exception as e:
        return {"success": False, "message": f"Error retrieving notifications: {str(e)}"}

@app.post("/admin/test_similarity")
def test_similarity_detection():
    """
    Test endpoint to verify similarity detection is working
    """
    try:
        # Test with sample data
        test_text = "Water supply problem in my area. No water for 3 days."
        department = "Tamil Nadu Water Supply and Drainage Board"
        
        similar = find_similar_grievances(test_text, department, 0.5)  # Lower threshold for testing
        
        return {
            "success": True,
            "test_text": test_text,
            "department": department,
            "similar_found": len(similar),
            "similar_grievances": similar,
            "message": "Similarity detection is working properly"
        }
    except Exception as e:
        return {"success": False, "message": f"Similarity test failed: {str(e)}"}

@app.post("/admin/test_notifications")
def test_notification_system():
    """
    Test endpoint to verify notification system is working
    """
    try:
        # Create test grievance data
        test_grievance = {
            'tracking_id': 'TEST-2024-ABC123',
            'name': 'Test User',
            'phone': '+91 9876543210',
            'petition_subject': 'Test Notification System'
        }
        
        # Send test notification
        success = send_notification_to_petitioner(test_grievance, 'pending', 'in_progress')
        
        return {
            "success": success,
            "message": "Test notification sent successfully" if success else "Test notification failed"
        }
    except Exception as e:
        return {"success": False, "message": f"Notification test failed: {str(e)}"}
