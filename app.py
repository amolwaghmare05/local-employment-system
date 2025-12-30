from flask import Flask, request, jsonify, render_template, redirect
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    get_jwt, jwt_required, get_jwt_identity
)
from flask_jwt_extended.exceptions import JWTExtendedException
from datetime import timedelta
import bcrypt
from config import SECRET_KEY, JWT_SECRET_KEY
from models.user_model_mongo import (
    create_user, get_user_by_email,
    create_employer_profile, get_employer_by_user,
    ensure_worker_row, get_worker_by_user, upsert_worker_profile,
    create_admin_profile, get_admin_by_user, upsert_admin_profile,
    admin_list_users, delete_user
)
from models.job_model_mongo import post_job, worker_matched_jobs, admin_list_jobs
from models.application_model_mongo import create_application, employer_applicants, update_application_status, admin_list_applications, worker_pending_applications, worker_approved_applications

# Page blueprints
from routes.worker_routes import worker_bp
from routes.employer_routes import employer_bp
from routes.admin_routes import admin_bp

app = Flask(__name__, template_folder="templates")
app.config["SECRET_KEY"] = SECRET_KEY
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)

jwt = JWTManager(app)

def role_required(*roles):
    """Decorator to require specific roles"""
    def wrapper(fn):
        @jwt_required()
        def decorated(*args, **kwargs):
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify({"msg": "Insufficient permissions"}), 403
            return fn(*args, **kwargs)
        decorated.__name__ = fn.__name__
        return decorated
    return wrapper

# ---------- Pages ----------
@app.get("/")
def index():
    return render_template("index.html")

@app.get("/login")
def login_page():
    return render_template("login.html")

@app.get("/register")
def register_page():
    return render_template("register.html")

# Register page blueprints for dashboards
app.register_blueprint(worker_bp)
app.register_blueprint(employer_bp)
app.register_blueprint(admin_bp)

# ---------- Auth API ----------
@app.post("/auth/register")
def register():
    data = request.json
    email = data["email"].strip().lower()
    password = data["password"]
    role = data["role"]  # worker | employer | admin
    
    # Hash password using bcrypt directly
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    pw_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    # create user
    create_user(email, pw_hash, role)
    user = get_user_by_email(email)
    user_id = user["user_id"]

    if role == "employer":
        create_employer_profile(user_id, data.get("company_name",""), data.get("employer_name",""))
    elif role == "worker":
        ensure_worker_row(user_id, data.get("full_name",""), data.get("skills",""))
    elif role == "admin":
        create_admin_profile(user_id, data.get("admin_name",""), data.get("department"))

    return jsonify({"msg":"registered","user_id":user_id})

@app.post("/auth/login")
def login():
    data = request.json
    email = data["email"].strip().lower()
    password = data["password"]
    
    user = get_user_by_email(email)
    if not user:
        return jsonify({"msg": "Bad credentials"}), 401
    
    # Verify password using bcrypt directly
    password_bytes = password.encode('utf-8')
    stored_hash = user["password_hash"].encode('utf-8')
    
    if not bcrypt.checkpw(password_bytes, stored_hash):
        return jsonify({"msg": "Bad credentials"}), 401
    
    access_token = create_access_token(identity=str(user["user_id"]), additional_claims={"role": user["role"]})
    refresh_token = create_refresh_token(identity=str(user["user_id"]), additional_claims={"role": user["role"]})
    
    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "role": user["role"],
        "user_id": user["user_id"]
    })

@app.post("/auth/refresh")
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    identity = get_jwt_identity()
    claims = get_jwt()
    access_token = create_access_token(
        identity=identity,
        additional_claims={"role": claims.get("role")}
    )
    return jsonify({"access_token": access_token})

# ---------- Worker API ----------
@app.get("/api/worker/profile")
@role_required("worker")
def api_worker_get_profile():
    user_id = get_jwt()["sub"]
    w = get_worker_by_user(user_id)
    if not w:
        return jsonify({"hasProfile": False})
    # Check if profile is filled
    has_profile = bool(w["full_name"] and w["skills"])
    w["hasProfile"] = has_profile
    return jsonify(w)

@app.get("/api/worker/applications") 
@role_required("worker")
def api_worker_applications():
    user_id = get_jwt()["sub"]
    w = get_worker_by_user(user_id)
    if not w:
        return jsonify([])
    from models.application_model_mongo import get_worker_applications
    applications = get_worker_applications(w["worker_id"])
    return jsonify(applications)

@app.put("/api/worker/profile")
@role_required("worker")
def api_worker_update_profile():
    payload = request.json
    user_id = get_jwt()["sub"]
    w = get_worker_by_user(user_id)
    if not w:
        ensure_worker_row(user_id, payload.get("full_name",""), payload.get("skills",""))
        w = get_worker_by_user(user_id)
    upsert_worker_profile(w["worker_id"], payload)
    return jsonify({"msg":"worker profile saved"})

@app.get("/api/worker/matched_jobs")
@role_required("worker")
def api_worker_matched_jobs():
    user_id = get_jwt()["sub"]
    w = get_worker_by_user(user_id)
    if not w:
        return jsonify([])
    rows = worker_matched_jobs(w["worker_id"], w["skills"], w["location"])
    return jsonify(rows)

@app.post("/api/worker/apply")
@role_required("worker")
def api_worker_apply():
    user_id = get_jwt()["sub"]
    job_id = request.json["job_id"]
    w = get_worker_by_user(user_id)
    if not w:
        return jsonify({"msg":"worker profile missing"}), 400
    # validate job exists using partitioned collection
    from models.job_model_mongo import get_job_by_id
    if not get_job_by_id(job_id):
        return jsonify({"msg":"job not found"}), 404
    create_application(job_id, w["worker_id"])
    return jsonify({"msg":"applied"})

@app.get("/api/worker/pending_jobs")
@role_required("worker")
def api_worker_pending_jobs():
    user_id = get_jwt()["sub"]
    w = get_worker_by_user(user_id)
    if not w:
        return jsonify([])
    jobs = worker_pending_applications(w["worker_id"])
    return jsonify(jobs)

@app.get("/api/worker/approved_jobs")
@role_required("worker")
def api_worker_approved_jobs():
    user_id = get_jwt()["sub"]
    w = get_worker_by_user(user_id)
    if not w:
        return jsonify([])
    jobs = worker_approved_applications(w["worker_id"])
    return jsonify(jobs)

# ---------- Employer API ----------
@app.get("/api/employer/jobs")
@role_required("employer")
def api_employer_get_jobs():
    user_id = get_jwt()["sub"]
    emp = get_employer_by_user(user_id)
    if not emp:
        return jsonify([])
    from models.job_model_mongo import get_jobs_by_employer
    jobs = get_jobs_by_employer(emp["employer_id"])
    return jsonify(jobs)

@app.post("/api/employer/jobs")
@role_required("employer")
def api_employer_post_job():
    user_id = get_jwt()["sub"]
    emp = get_employer_by_user(user_id)
    if not emp:
        return jsonify({"msg":"employer profile missing"}), 400
    post_job(emp["employer_id"], request.json)
    return jsonify({"msg":"job posted"})

@app.get("/api/employer/applicants")
@role_required("employer")
def api_employer_applicants():
    user_id = get_jwt()["sub"]
    emp = get_employer_by_user(user_id)
    if not emp:
        return jsonify([])
    rows = employer_applicants(emp["employer_id"])
    return jsonify(rows)

@app.put("/api/employer/applications/<application_id>/status")
@role_required("employer")
def api_employer_update_application(application_id):
    new_status = request.json.get("status")
    if new_status not in ("approved","rejected"):
        return jsonify({"msg":"invalid status"}), 400

    # authorization: ensure app belongs to this employer (partition-aware)
    from models.mongodb import find_one, to_object_id
    from models.job_model_mongo import get_job_by_id
    
    # Get the application
    application = find_one("applications", {"_id": to_object_id(application_id)})
    if not application:
        return jsonify({"msg":"application not found"}), 404
    
    # Get the job using partition-aware function
    job = get_job_by_id(str(application["job_id"]))
    if not job:
        return jsonify({"msg":"job not found"}), 404
    
    # Check if current user is the job owner
    emp = get_employer_by_user(get_jwt()["sub"])
    if not emp:
        return jsonify({"msg":"forbidden"}), 403
    
    # Convert both to strings for comparison
    job_employer_id = str(job.get("employer_id"))
    current_employer_id = str(emp["employer_id"])
    
    if job_employer_id != current_employer_id:
        return jsonify({"msg":"forbidden"}), 403

    update_application_status(application_id, new_status)
    return jsonify({"msg":"updated"})

@app.get("/api/employer/profile")
@role_required("employer")
def api_employer_get_profile():
    user_id = get_jwt()["sub"]
    emp = get_employer_by_user(user_id)
    if not emp:
        return jsonify({"hasProfile": False})
    # Check if profile is filled
    has_profile = bool(emp["company_name"])
    emp["hasProfile"] = has_profile
    return jsonify(emp)

@app.put("/api/employer/profile")
@role_required("employer")
def api_employer_update_profile():
    user_id = get_jwt()["sub"]
    emp = get_employer_by_user(user_id)
    if not emp:
        return jsonify({"msg": "employer profile missing"}), 400
    
    data = request.json
    from models.mongodb import update_one, to_object_id
    update_one("employers", 
        {"_id": to_object_id(emp["employer_id"])},
        {"$set": {
            "employer_name": data.get("employer_name", ""),
            "company_name": data.get("company_name", ""),
            "location": data.get("location"),
            "phone": data.get("phone")
        }}
    )
    return jsonify({"msg": "profile updated"})

# ---------- Admin API ----------
@app.get("/api/admin/users")
@role_required("admin")
def api_admin_users():
    try:
        users = admin_list_users()
        return jsonify(users)
    except Exception as e:
        print("Error fetching users:", str(e))
        return jsonify({"msg": "Error fetching users"}), 500

@app.get("/api/admin/jobs")
@role_required("admin")
def api_admin_jobs():
    try:
        jobs = admin_list_jobs()
        return jsonify(jobs)
    except Exception as e:
        print("Error fetching jobs:", str(e))
        return jsonify({"msg": "Error fetching jobs"}), 500

@app.get("/api/admin/jobs/<job_id>")
@role_required("admin")
def api_admin_get_job(job_id):
    try:
        from models.mongodb import find_one, to_object_id, serialize_doc
        job = find_one("jobs", {"_id": to_object_id(job_id)})
        if not job:
            return jsonify({"msg": "Job not found"}), 404
        
        job = serialize_doc(job)
        job["job_id"] = job["id"]  # Add job_id for compatibility
        return jsonify(job)
    except Exception as e:
        print("Error fetching job:", str(e))
        return jsonify({"msg": "Error fetching job"}), 500

@app.get("/api/admin/applications")
@role_required("admin")
def api_admin_apps():
    try:
        apps = admin_list_applications()
        return jsonify(apps)
    except Exception as e:
        print("Error fetching applications:", str(e))
        return jsonify({"msg": "Error fetching applications"}), 500

# Add admin profile endpoints
@app.get("/api/admin/profile")
@role_required("admin")
def api_admin_get_profile():
    user_id = get_jwt()["sub"]
    admin = get_admin_by_user(user_id)
    if not admin:
        return jsonify({"hasProfile": False})
    # Check if profile is filled
    has_profile = bool(admin["admin_name"])
    admin["hasProfile"] = has_profile
    return jsonify(admin)

@app.put("/api/admin/profile")
@role_required("admin")
def api_admin_update_profile():
    user_id = get_jwt()["sub"]
    admin = get_admin_by_user(user_id)
    if not admin:
        return jsonify({"msg": "admin profile missing"}), 400
    
    data = request.json
    upsert_admin_profile(admin["admin_id"], data)
    return jsonify({"msg": "profile updated"})

# ---------- Admin CRUD Operations ----------
@app.delete("/api/admin/users/<user_id>")
@role_required("admin")
def api_admin_delete_user(user_id):
    """Delete a user (admin only)"""
    try:
        from models.mongodb import delete_one, find_one, to_object_id
        
        # Prevent admin from deleting themselves
        current_user_id = get_jwt()["sub"]
        if user_id == current_user_id:
            return jsonify({"msg": "Cannot delete your own account"}), 400
        
        # Check if user exists
        user_obj_id = to_object_id(user_id)
        user = find_one("users", {"_id": user_obj_id})
        if not user:
            return jsonify({"msg": "User not found"}), 404
        
        # Delete from related collections first
        delete_one("workers", {"user_id": user_obj_id})
        delete_one("employers", {"user_id": user_obj_id})
        delete_one("admins", {"user_id": user_obj_id})
        
        # Delete user
        result = delete_one("users", {"_id": user_obj_id})
        
        if result > 0:
            return jsonify({"msg": "User deleted successfully"})
        else:
            return jsonify({"msg": "User not found"}), 404
            
    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({"msg": "Error deleting user"}), 500

@app.post("/api/admin/users")
@role_required("admin")
def api_admin_create_user():
    """Create a new user (admin only)"""
    try:
        from passlib.hash import bcrypt_sha256 as bcrypt
        from datetime import datetime
        
        data = request.json
        
        # Validate required fields
        required_fields = ["email", "password", "role"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"msg": f"Missing required field: {field}"}), 400
        
        email = data["email"].strip().lower()
        password = data["password"]
        role = data["role"]
        
        # Validate role
        if role not in ["worker", "employer", "admin"]:
            return jsonify({"msg": "Invalid role. Must be worker, employer, or admin"}), 400
        
        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            return jsonify({"msg": "User with this email already exists"}), 400
        
        # Validate password length
        if len(password.encode('utf-8')) > 72:
            return jsonify({"msg": "Password is too long. Please use a shorter password."}), 400
        
        # Create user
        pw_hash = bcrypt.hash(password)
        create_user(email, pw_hash, role)
        
        # Get the created user
        user = get_user_by_email(email)
        user_id = user["user_id"]
        
        # Create role-specific profile
        if role == "employer":
            create_employer_profile(user_id, data.get("company_name", ""))
        elif role == "worker":
            ensure_worker_row(user_id, data.get("full_name", ""), data.get("skills", ""))
        elif role == "admin":
            create_admin_profile(user_id, data.get("admin_name", ""), data.get("department", ""))
        
        return jsonify({"msg": "User created successfully", "user_id": user_id})
        
    except Exception as e:
        print(f"Error creating user: {e}")
        return jsonify({"msg": "Error creating user"}), 500

@app.get("/api/admin/activity-logs")
@role_required("admin")
def api_admin_activity_logs():
    """Get activity logs (admin only)"""
    try:
        # For now, return mock data since we don't have activity logging implemented
        # In a real system, you would log admin actions to a separate collection
        mock_logs = [
            {
                "created_at": "2025-10-12T10:30:00Z",
                "admin_email": "admin@example.com",
                "action_type": "delete",
                "target_table": "users",
                "target_id": "user123",
                "note": "Deleted inactive user account"
            },
            {
                "created_at": "2025-10-12T09:15:00Z", 
                "admin_email": "admin@example.com",
                "action_type": "update",
                "target_table": "jobs",
                "target_id": "job456",
                "note": "Updated job status to closed"
            },
            {
                "created_at": "2025-10-12T08:45:00Z",
                "admin_email": "admin@example.com", 
                "action_type": "create",
                "target_table": "users",
                "target_id": "user789",
                "note": "Created new employer account"
            }
        ]
        return jsonify(mock_logs)
    except Exception as e:
        print("Error fetching activity logs:", str(e))
        return jsonify({"msg": "Error fetching activity logs"}), 500

@app.put("/api/admin/users/<user_id>")
@role_required("admin")
def api_admin_update_user(user_id):
    """Update user details (admin only)"""
    try:
        from models.mongodb import update_one, find_one, to_object_id
        
        data = request.json
        user_obj_id = to_object_id(user_id)
        
        # Check if user exists
        user = find_one("users", {"_id": user_obj_id})
        if not user:
            return jsonify({"msg": "User not found"}), 404
        
        # Update user data
        update_data = {"$set": {}}
        
        if "email" in data:
            update_data["$set"]["email"] = data["email"].strip().lower()
        if "role" in data and data["role"] in ["worker", "employer", "admin"]:
            update_data["$set"]["role"] = data["role"]
        
        if update_data["$set"]:
            update_one("users", {"_id": user_obj_id}, update_data)
            return jsonify({"msg": "User updated successfully"})
        else:
            return jsonify({"msg": "No valid fields to update"}), 400
            
    except Exception as e:
        print(f"Error updating user: {e}")
        return jsonify({"msg": "Error updating user"}), 500

@app.post("/api/admin/jobs")
@role_required("admin")
def api_admin_create_job():
    """Create a new job (admin only)"""
    try:
        from models.mongodb import insert_one, find_one, to_object_id
        from datetime import datetime
        
        data = request.json
        
        # Validate required fields
        required_fields = ["title", "required_skills", "employer_id"]
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"msg": f"Missing required field: {field}"}), 400
        
        # Check if employer exists
        employer_obj_id = to_object_id(data["employer_id"])
        employer = find_one("employers", {"_id": employer_obj_id})
        if not employer:
            return jsonify({"msg": "Employer not found"}), 404
        
        # Create job document
        job_doc = {
            "employer_id": employer_obj_id,
            "title": data["title"],
            "required_skills": data["required_skills"],
            "description": data.get("description", ""),
            "salary_min": float(data["salary_min"]) if data.get("salary_min") else None,
            "salary_max": float(data["salary_max"]) if data.get("salary_max") else None,
            "location": data.get("location", ""),
            "status": data.get("status", "open"),
            "posted_at": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        
        result = insert_one("jobs", job_doc)
        return jsonify({"msg": "Job created successfully", "job_id": str(result.inserted_id)})
        
    except Exception as e:
        print(f"Error creating job: {e}")
        return jsonify({"msg": "Error creating job"}), 500

@app.put("/api/admin/jobs/<job_id>")
@role_required("admin")
def api_admin_update_job(job_id):
    """Update a job (admin only)"""
    try:
        from models.mongodb import update_one, find_one, to_object_id
        from datetime import datetime
        
        data = request.json
        job_obj_id = to_object_id(job_id)
        
        # Check if job exists
        job = find_one("jobs", {"_id": job_obj_id})
        if not job:
            return jsonify({"msg": "Job not found"}), 404
        
        # Update job data
        update_data = {"$set": {"updated_at": datetime.utcnow()}}
        
        if "title" in data:
            update_data["$set"]["title"] = data["title"]
        if "required_skills" in data:
            update_data["$set"]["required_skills"] = data["required_skills"]
        if "description" in data:
            update_data["$set"]["description"] = data["description"]
        if "salary_min" in data:
            update_data["$set"]["salary_min"] = float(data["salary_min"]) if data["salary_min"] else None
        if "salary_max" in data:
            update_data["$set"]["salary_max"] = float(data["salary_max"]) if data["salary_max"] else None
        if "location" in data:
            update_data["$set"]["location"] = data["location"]
        if "status" in data and data["status"] in ["open", "closed"]:
            update_data["$set"]["status"] = data["status"]
        
        result = update_one("jobs", {"_id": job_obj_id}, update_data)
        
        if result > 0:
            return jsonify({"msg": "Job updated successfully"})
        else:
            return jsonify({"msg": "No changes made"}), 400
            
    except Exception as e:
        print(f"Error updating job: {e}")
        return jsonify({"msg": "Error updating job"}), 500

@app.delete("/api/admin/jobs/<job_id>")
@role_required("admin")
def api_admin_delete_job(job_id):
    """Delete a job (admin only)"""
    try:
        from models.mongodb import delete_one, find_one, to_object_id
        
        job_obj_id = to_object_id(job_id)
        
        # Check if job exists
        job = find_one("jobs", {"_id": job_obj_id})
        if not job:
            return jsonify({"msg": "Job not found"}), 404
        
        # Delete related applications first
        delete_one("applications", {"job_id": job_obj_id})
        
        # Delete job
        result = delete_one("jobs", {"_id": job_obj_id})
        
        if result > 0:
            return jsonify({"msg": "Job deleted successfully"})
        else:
            return jsonify({"msg": "Job not found"}), 404
            
    except Exception as e:
        print(f"Error deleting job: {e}")
        return jsonify({"msg": "Error deleting job"}), 500

@app.put("/api/admin/applications/<application_id>")
@role_required("admin")
def api_admin_update_application(application_id):
    """Update application status (admin only)"""
    try:
        from models.mongodb import update_one, find_one, to_object_id
        from datetime import datetime
        
        data = request.json
        app_obj_id = to_object_id(application_id)
        
        # Check if application exists
        application = find_one("applications", {"_id": app_obj_id})
        if not application:
            return jsonify({"msg": "Application not found"}), 404
        
        # Update application status
        if "status" in data and data["status"] in ["pending", "approved", "rejected"]:
            update_data = {
                "$set": {
                    "application_status": data["status"],
                    "updated_at": datetime.utcnow()
                }
            }
            
            result = update_one("applications", {"_id": app_obj_id}, update_data)
            
            if result > 0:
                return jsonify({"msg": "Application status updated successfully"})
            else:
                return jsonify({"msg": "No changes made"}), 400
        else:
            return jsonify({"msg": "Invalid status. Must be pending, approved, or rejected"}), 400
            
    except Exception as e:
        print(f"Error updating application: {e}")
        return jsonify({"msg": "Error updating application"}), 500

@app.delete("/api/admin/applications/<application_id>")
@role_required("admin")
def api_admin_delete_application(application_id):
    """Delete an application (admin only)"""
    try:
        from models.mongodb import delete_one, find_one, to_object_id
        
        app_obj_id = to_object_id(application_id)
        
        # Check if application exists
        application = find_one("applications", {"_id": app_obj_id})
        if not application:
            return jsonify({"msg": "Application not found"}), 404
        
        # Delete application
        result = delete_one("applications", {"_id": app_obj_id})
        
        if result > 0:
            return jsonify({"msg": "Application deleted successfully"})
        else:
            return jsonify({"msg": "Application not found"}), 404
            
    except Exception as e:
        print(f"Error deleting application: {e}")
        return jsonify({"msg": "Error deleting application"}), 500

# ---------- MongoDB debug API (visible in dashboards) ----------
@app.get("/api/debug/jobs/stats")
@role_required("worker")
def api_debug_jobs_stats():
    try:
        from models.mongodb import aggregate
        pipeline = [{"$group": {"_id": None, "total_jobs": {"$sum": 1}}}]
        stats = list(aggregate("jobs", pipeline))
        return jsonify({"total_jobs": stats[0]["total_jobs"] if stats else 0})
    except Exception as e:
        return jsonify({"msg": "Error fetching job stats"}), 500

@app.get("/api/debug/jobs/partitions")
@role_required("employer")
def api_debug_jobs_partitions():
    """Get job partition statistics by year"""
    try:
        from models.mongodb import get_jobs_partition_stats
        stats = get_jobs_partition_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"msg": f"Error fetching partition stats: {str(e)}"}), 500

@app.get("/api/debug/workers/hash_partition/<worker_id>")
@role_required("worker")
def api_debug_worker_partition(worker_id):
    """Get worker's hash partition information"""
    try:
        from models.mongodb import hash_partition, get_worker_partition_collection, to_object_id
        worker_obj_id = to_object_id(worker_id)
        partition_num = hash_partition(worker_obj_id, 8)
        partition_coll = get_worker_partition_collection(worker_obj_id)
        
        return jsonify({
            "worker_id": worker_id,
            "partition_number": partition_num,
            "partition_collection": partition_coll,
            "hash_function": "hash(worker_id) % 8"
        })
    except Exception as e:
        return jsonify({"msg": f"Error: {str(e)}"}), 500

@app.get("/api/debug/workers/info/<worker_id>")
@role_required("worker")
def api_debug_worker_info(worker_id):
    try:
        from models.user_model_mongo import get_worker_by_id
        worker = get_worker_by_id(worker_id)
        if worker:
            return jsonify(worker)
        else:
            return jsonify({"msg": "Worker not found"}), 404
    except Exception as e:
        return jsonify({"msg": "Error fetching worker info"}), 500

# ---------- Error Handlers ----------
@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

@app.errorhandler(Exception)
def handle_error(error):
    print("Error:", str(error))  # Log the error
    if isinstance(error, JWTExtendedException):
        return jsonify({"msg": "Invalid or expired token. Please log in again."}), 401
    return jsonify({"msg": "An error occurred. Please try again."}), 500

if __name__ == "__main__":
    app.run(debug=True)