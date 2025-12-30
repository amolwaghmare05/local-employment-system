from models.mongodb import (
    find_one, find_many, insert_one, update_one, delete_one,
    to_object_id, serialize_doc, get_worker_partition_collection,
    get_all_worker_partitions, get_collection
)
from bson import ObjectId
import bcrypt
from datetime import datetime

# ==================== USER FUNCTIONS ====================

def create_user(email, password_hash, role):
    """Create a new user"""
    user_doc = {
        "email": email,
        "password_hash": password_hash,
        "role": role,
        "created_at": datetime.utcnow()
    }
    result = insert_one("users", user_doc)
    return result.inserted_id

def get_user_by_email(email):
    """Get user by email"""
    user = find_one("users", {"email": email})
    if user:
        user = serialize_doc(user)
        user["user_id"] = user["id"]  # Add user_id for compatibility
    return user

def get_user_by_id(user_id):
    """Get user by ID"""
    if isinstance(user_id, str):
        user_id = to_object_id(user_id)
    user = find_one("users", {"_id": user_id})
    if user:
        user = serialize_doc(user)
        user["user_id"] = user["id"]  # Add user_id for compatibility
    return user

# ==================== WORKER FUNCTIONS (HASH PARTITIONED) ====================

def ensure_worker_row(user_id, full_name="", skills=""):
    """Ensure worker profile exists (uses hash partitioning)"""
    if isinstance(user_id, str):
        user_id = to_object_id(user_id)
    
    # Check all partitions for existing worker
    worker = _find_worker_in_partitions({"user_id": user_id})
    
    if not worker:
        worker_doc = {
            "user_id": user_id,
            "full_name": full_name,
            "skills": skills,
            "phone": "",
            "location": "",
            "experience": "",
            "created_at": datetime.utcnow()
        }
        # Insert into a temporary collection first to get the ID
        result = insert_one("workers", worker_doc)
        worker_id = result.inserted_id
        
        # Now move to the correct partition based on worker_id hash
        partition_coll = get_worker_partition_collection(worker_id)
        worker_doc["_id"] = worker_id
        get_collection(partition_coll).insert_one(worker_doc)
        
        # Delete from temporary collection
        delete_one("workers", {"_id": worker_id})
        
        return {"worker_id": str(worker_id), "user_id": str(user_id)}
    else:
        worker = serialize_doc(worker)
        worker["worker_id"] = worker["id"]
        return worker

def get_worker_by_user(user_id):
    """Get worker by user_id (searches across partitions)"""
    if isinstance(user_id, str):
        user_id = to_object_id(user_id)
    
    worker = _find_worker_in_partitions({"user_id": user_id})
    if worker:
        worker = serialize_doc(worker)
        worker["worker_id"] = worker["id"]  # Add worker_id for compatibility
        worker["user_id"] = str(worker["user_id"])  # Convert ObjectId to string
    return worker

def get_worker_by_id(worker_id):
    """Get worker by worker_id (uses hash to find correct partition)"""
    if isinstance(worker_id, str):
        worker_id = to_object_id(worker_id)
    
    partition_coll = get_worker_partition_collection(worker_id)
    worker = get_collection(partition_coll).find_one({"_id": worker_id})
    
    if worker:
        worker = serialize_doc(worker)
        worker["worker_id"] = worker["id"]
        worker["user_id"] = str(worker["user_id"])
    else:
        # Try searching all partitions as fallback (for workers created before partitioning)
        worker = _find_worker_in_partitions({"_id": worker_id})
        if worker:
            # _find_worker_in_partitions already serializes, just add worker_id
            worker["worker_id"] = worker["id"]
    
    return worker

def upsert_worker_profile(worker_id, data):
    """Update worker profile (uses hash partitioning)"""
    if isinstance(worker_id, str):
        worker_id = to_object_id(worker_id)
    
    # Handle experience field (can be 'experience' or 'experience_years')
    experience_value = data.get("experience_years") or data.get("experience", "")
    
    update_data = {
        "$set": {
            "full_name": data.get("full_name", ""),
            "skills": data.get("skills", ""),
            "phone": data.get("phone", ""),
            "location": data.get("location", ""),
            "experience": experience_value,
            "experience_years": experience_value,
            "age": data.get("age", ""),
            "gender": data.get("gender", ""),
            "updated_at": datetime.utcnow()
        }
    }
    
    # Update in the correct partition
    partition_coll = get_worker_partition_collection(worker_id)
    result = get_collection(partition_coll).update_one(
        {"_id": worker_id},
        update_data
    )
    return result.modified_count

def _find_worker_in_partitions(query):
    """Helper function to search for worker across all partitions"""
    for partition_name in get_all_worker_partitions():
        worker = get_collection(partition_name).find_one(query)
        if worker:
            return serialize_doc(worker)
    return None

# ==================== EMPLOYER FUNCTIONS ====================

def create_employer_profile(user_id, company_name="", employer_name=""):
    """Create employer profile"""
    if isinstance(user_id, str):
        user_id = to_object_id(user_id)
    
    employer_doc = {
        "user_id": user_id,
        "employer_name": employer_name,
        "company_name": company_name,
        "location": "",
        "phone": "",
        "created_at": datetime.utcnow()
    }
    result = insert_one("employers", employer_doc)
    return result.inserted_id

def get_employer_by_user(user_id):
    """Get employer by user_id"""
    if isinstance(user_id, str):
        user_id = to_object_id(user_id)
    
    employer = find_one("employers", {"user_id": user_id})
    if employer:
        employer = serialize_doc(employer)
        employer["employer_id"] = employer["id"]  # Add employer_id for compatibility
        employer["user_id"] = str(employer["user_id"])  # Convert ObjectId to string
    return employer

# ==================== ADMIN FUNCTIONS ====================

def create_admin_profile(user_id, admin_name="", department=""):
    """Create admin profile"""
    if isinstance(user_id, str):
        user_id = to_object_id(user_id)
    
    admin_doc = {
        "user_id": user_id,
        "admin_name": admin_name,
        "department": department,
        "created_at": datetime.utcnow()
    }
    result = insert_one("admins", admin_doc)
    return result.inserted_id

def get_admin_by_user(user_id):
    """Get admin by user_id"""
    if isinstance(user_id, str):
        user_id = to_object_id(user_id)
    
    admin = find_one("admins", {"user_id": user_id})
    if admin:
        admin = serialize_doc(admin)
        admin["admin_id"] = admin["id"]  # Add admin_id for compatibility
        admin["user_id"] = str(admin["user_id"])  # Convert ObjectId to string
    return admin

def upsert_admin_profile(admin_id, data):
    """Update admin profile"""
    if isinstance(admin_id, str):
        admin_id = to_object_id(admin_id)
    
    update_data = {
        "$set": {
            "admin_name": data.get("admin_name", ""),
            "department": data.get("department", ""),
            "updated_at": datetime.utcnow()
        }
    }
    return update_one("admins", {"_id": admin_id}, update_data)

def admin_list_users():
    """Get all users for admin dashboard"""
    users = find_many("users", sort=[("created_at", -1)])
    result = []
    for user in users:
        user_data = serialize_doc(user)
        user_data["user_id"] = user_data["id"]  # Add user_id for compatibility
        result.append(user_data)
    return result

def delete_user(user_id):
    """Delete a user (admin function)"""
    if isinstance(user_id, str):
        user_id = to_object_id(user_id)
    
    # Delete from all related collections
    user = find_one("users", {"_id": user_id})
    if user:
        # Delete from workers, employers, admins collections
        delete_one("workers", {"user_id": user_id})
        delete_one("employers", {"user_id": user_id})
        delete_one("admins", {"user_id": user_id})
        
        # Delete the user
        return delete_one("users", {"_id": user_id})
    return 0

def log_admin_action(admin_id, action, details=""):
    """Log admin actions (placeholder for future implementation)"""
    # This can be implemented later with an admin_logs collection
    pass

def get_admin_actions():
    """Get admin action logs (placeholder for future implementation)"""
    # This can be implemented later with an admin_logs collection
    return []