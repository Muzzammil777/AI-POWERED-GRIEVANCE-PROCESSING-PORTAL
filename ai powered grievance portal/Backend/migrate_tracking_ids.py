"""
Migration script to add tracking IDs to existing grievances
This should be run once to update all existing grievances with proper tracking IDs
"""

import os
from dotenv import load_dotenv
load_dotenv()

from pymongo import MongoClient
import random
import string
from datetime import datetime

def generate_tracking_id():
    """Generate a unique tracking ID in the format GR-YYYY-XXXXXX"""
    year = datetime.now().year
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"GR-{year}-{code}"

def connect_to_db():
    mongo_uri = os.environ.get("MONGODB_URI")
    if not mongo_uri:
        raise RuntimeError("MONGODB_URI environment variable not set.")
    client = MongoClient(mongo_uri)
    return client.petition_db

def migrate_tracking_ids():
    """Add tracking IDs to all existing grievances that don't have them"""
    
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
    
    db = connect_to_db()
    used_tracking_ids = set()
    total_updated = 0
    
    print("Starting migration of tracking IDs...")
    
    for department, table_name in department_tables.items():
        collection = db[table_name]
        
        # Find petitions without tracking_id
        petitions_without_id = list(collection.find({"tracking_id": {"$exists": False}}))
        
        if petitions_without_id:
            print(f"Found {len(petitions_without_id)} petitions without tracking ID in {department}")
            
            for petition in petitions_without_id:
                # Generate a unique tracking ID
                tracking_id = generate_tracking_id()
                while tracking_id in used_tracking_ids:
                    tracking_id = generate_tracking_id()
                
                used_tracking_ids.add(tracking_id)
                
                # Update the petition with the tracking ID and ensure other fields are set
                update_data = {
                    "tracking_id": tracking_id,
                    "department": department
                }
                
                # Add created_at if missing
                if not petition.get("created_at"):
                    update_data["created_at"] = datetime.now().strftime("%d-%b-%Y")
                
                # Normalize status
                if petition.get("status"):
                    update_data["status"] = petition["status"].lower()
                else:
                    update_data["status"] = "pending"
                
                # Add priority if missing
                if not petition.get("priority"):
                    update_data["priority"] = "Medium"
                
                collection.update_one(
                    {"_id": petition["_id"]},
                    {"$set": update_data}
                )
                
                total_updated += 1
                print(f"  Updated petition {petition['_id']} with tracking ID: {tracking_id}")
        else:
            print(f"No petitions need updating in {department}")
    
    print(f"\nMigration complete! Updated {total_updated} petitions with tracking IDs.")

if __name__ == "__main__":
    migrate_tracking_ids()
