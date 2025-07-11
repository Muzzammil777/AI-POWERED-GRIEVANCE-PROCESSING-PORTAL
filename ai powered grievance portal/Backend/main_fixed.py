from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import mysql.connector
import bcrypt
import os
from datetime import datetime
import requests
import difflib
from pymongo import MongoClient
from pydantic import BaseModel

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
        "pwd": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Public Works Department"},
        "fin": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Finance Department"},
        "edu": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Education Department"},
        "adi": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Adi Dravidar and Tribal Welfare Department"},
        "agr": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Agriculture and Farmers welfares Department"},
        "ani": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Animal Husbandry and Dairying and Fisheries and Fishermen Welfare Department"},
        "bcm": {"password": "123", "dashboard": "admindashboardaph.html", "department": "BC MBC and Minorities Welfare Department"},
        "cof": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Co-operation Food and Consumer Protection Department"},
        "ctr": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Commercial Taxes and Registration Department"},
        "ene": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Energy Department"},
        "env": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Environment Climate Change and Forests Department"},
        "han": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Handlooms Handicrafts Textiles and Khadi Department"},
        "hea": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Health and Family Welfare Department"},
        "hed": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Higher Education Department"},
        "hig": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Highways and Minor Ports Department"},
        "hrm": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Human Resources Management Department"},
        "hom": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Home Prohibition and Excise Department"},
        "hou": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Housing and Urban Development Department"},
        "ind": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Industries Department"},
        "itd": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Information Technology Department"},
        "lab": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Labour Welfare and Skill Development Department"},
        "law": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Law Department"},
        "leg": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Legislative Assembly Department"},
        "mic": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Micro Small and Medium Enterprises Department"},
        "mun": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Municipal Administration and Water Supply Department"},
        "pel": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Public Elections Department"},
        "pub": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Public Department"},
        "rev": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Revenue and Disaster Management Department"},
        "rur": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Rural Development and Panchayat Raj Department"},
        "sch": {"password": "123", "dashboard": "admindashboardaph.html", "department": "School Education Department"},
        "soc": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Social Welfare and Women Empowerment Department"},
        "tam": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Tamil Dev. and Information Department"},
        "tou": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Tourism Culture and Religious Endowments Department"},
        "tra": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Transport Department"},
        "wel": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Welfare of Differently Abled Persons"},
        "you": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Youth Welfare and Sports Development Department"},
        "wat": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Water Resources Department"},
        "pla": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Planning Development Department"},
        "spe": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Special Programme Implementation"},
        "tws": {"password": "123", "dashboard": "admindashboardaph.html", "department": "Tamil Nadu Water Supply and Drainage Board"},
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
    3. Returns the assigned department and priority level
    
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
        Status message, assigned department, and priority level
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
        
        petition_data = {
            "tracking_id": tracking_id,  # Add the tracking ID to the petition
            "name": name,
            "phone": phone,
            "address": address,
            "petition_type": petition_type,
            "petition_subject": petition_subject,
            "petition_description": petition_description,
            "status": "pending",
            "priority": priority_level,
            "created_at": datetime.now().strftime("%d-%b-%Y"),
            "department": category_clean
        }
        petitions_collection.insert_one(petition_data)
        return {
            "message": "Petition recorded successfully", 
            "department": category_clean,
            "priority": priority_level,
            "tracking_id": tracking_id
        }
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
    Update the status of a grievance using the new tracking system
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
            
        # Update the status
        update_result = collection.update_one(
            {"tracking_id": grievance_id},
            {"$set": {"status": status.lower()}}
        )
        
        if update_result.modified_count == 0:
            return {"success": False, "message": "Failed to update status"}
        
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
            }
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
    Detects priority level based on text content
    
    Args:
        text: The text to analyze (petition subject + description)
        
    Returns:
        Priority level: "High", "Medium", or "Low"
    """
    # Convert to lowercase for case-insensitive matching
    text = text.lower()
    
    # High-priority keywords
    high_priority_keywords = [
        "urgent", "danger", "accident", "emergency", "fire", "violence", 
        "death", "injury", "threat", "hospital"
    ]
    
    # Check if any high-priority keyword is in the text
    if any(keyword in text for keyword in high_priority_keywords):
        return "High"
    
    # Default to Medium priority
    return "Medium"

@app.post("/test_priority")
def test_priority_detection(text: str = Form(...)):
    """
    Test endpoint to check the priority detection logic
    
    Args:
        text: Text to analyze for priority keywords
        
    Returns:
        Detected priority level
    """
    priority = detect_priority(text)
    return {"text": text, "detected_priority": priority}

@app.post("/test_tracking")
def test_tracking_system():
    """
    Test endpoint to verify the new tracking system works
    """
    try:
        # Generate a test tracking ID
        test_id = generate_tracking_id()
        
        return {
            "message": "New tracking system is working!",
            "sample_tracking_id": test_id,
            "format": "GR-YYYY-XXXXXX where YYYY is year and XXXXXX is 6-digit alphanumeric code"
        }
    except Exception as ex:
        return {"error": f"Error in tracking system: {str(ex)}"}
