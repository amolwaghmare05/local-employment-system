from models.mongodb import (
    find_one, find_many, insert_one, update_one, delete_one,
    to_object_id, serialize_doc, aggregate
)
from bson import ObjectId
from datetime import datetime

def create_application(job_id, worker_id):
    """Create a new job application"""
    if isinstance(job_id, str):
        job_id = to_object_id(job_id)
    if isinstance(worker_id, str):
        worker_id = to_object_id(worker_id)
    
    # Check if application already exists
    existing = find_one("applications", {
        "job_id": job_id,
        "worker_id": worker_id
    })
    
    if existing:
        raise ValueError("Application already exists for this job")
    
    application_doc = {
        "job_id": job_id,
        "worker_id": worker_id,
        "application_status": "pending",
        "applied_at": datetime.utcnow(),
        "created_at": datetime.utcnow()
    }
    result = insert_one("applications", application_doc)
    return result.inserted_id

def employer_applicants(employer_id):
    """Get all applicants for jobs posted by an employer"""
    if isinstance(employer_id, str):
        employer_id = to_object_id(employer_id)
    
    # Import partition-aware functions
    from models.job_model_mongo import get_jobs_by_employer
    from models.user_model_mongo import get_worker_by_id
    
    # Get all jobs by this employer (searches across all year partitions)
    employer_jobs = get_jobs_by_employer(employer_id)
    if not employer_jobs:
        return []
    
    # Get job IDs
    job_ids = [to_object_id(job["job_id"]) for job in employer_jobs]
    
    # Find all applications for these jobs
    applications = find_many("applications", {"job_id": {"$in": job_ids}})
    applications_list = list(applications)
    
    # Build job lookup map
    jobs_map = {to_object_id(job["job_id"]): job for job in employer_jobs}
    
    # Enrich applications with job and worker data
    results = []
    for app in applications_list:
        job = jobs_map.get(app["job_id"])
        if not job:
            continue
        
        # Get worker data from partitioned collections
        worker = get_worker_by_id(str(app["worker_id"]))
        if not worker:
            continue
        
        results.append({
            "application_id": str(app["_id"]),
            "application_status": app.get("application_status", "pending"),
            "applied_at": app.get("applied_at"),
            "worker_id": str(app["worker_id"]),
            "full_name": worker.get("full_name", "N/A"),
            "phone": worker.get("phone", "N/A"),
            "location": worker.get("location", "N/A"),
            "skills": worker.get("skills", []),
            "job_id": str(app["job_id"]),
            "title": job.get("title", "N/A")
        })
    
    # Sort by applied_at descending
    results.sort(key=lambda x: x.get("applied_at") or datetime.min, reverse=True)
    return results

def update_application_status(application_id, status):
    """Update application status"""
    if isinstance(application_id, str):
        application_id = to_object_id(application_id)
    
    if status not in ["pending", "approved", "rejected"]:
        raise ValueError("Invalid status. Must be 'pending', 'approved', or 'rejected'")
    
    update_data = {
        "$set": {
            "application_status": status,
            "updated_at": datetime.utcnow()
        }
    }
    return update_one("applications", {"_id": application_id}, update_data)

def admin_list_applications():
    """Get all applications for admin dashboard"""
    applications = find_many("applications", sort=[("applied_at", -1)])
    result = []
    for app in applications:
        app = serialize_doc(app)
        app["application_id"] = app["id"]  # Add application_id for compatibility
        result.append(app)
    return result

def worker_applied_jobs(worker_id):
    """Get all jobs applied by a worker with application status"""
    if isinstance(worker_id, str):
        worker_id = to_object_id(worker_id)
    
    pipeline = [
        {
            "$match": {"worker_id": worker_id}
        },
        {
            "$lookup": {
                "from": "jobs",
                "localField": "job_id",
                "foreignField": "_id",
                "as": "job"
            }
        },
        {
            "$unwind": "$job"
        },
        {
            "$lookup": {
                "from": "employers",
                "localField": "job.employer_id",
                "foreignField": "_id",
                "as": "employer"
            }
        },
        {
            "$unwind": "$employer"
        },
        {
            "$project": {
                "application_id": {"$toString": "$_id"},
                "application_status": 1,
                "applied_at": 1,
                "job_id": {"$toString": "$job_id"},
                "title": "$job.title",
                "description": "$job.description",
                "location": "$job.location",
                "required_skills": "$job.required_skills",
                "salary_range": {
                    "$cond": {
                        "if": {
                            "$and": [
                                {"$ne": ["$job.salary_min", None]},
                                {"$ne": ["$job.salary_max", None]}
                            ]
                        },
                        "then": {
                            "$concat": [
                                "₹", {"$toString": "$job.salary_min"},
                                " - ₹", {"$toString": "$job.salary_max"}
                            ]
                        },
                        "else": "Salary not specified"
                    }
                },
                "posted_at": "$job.posted_at",
                "company_name": "$employer.company_name"
            }
        },
        {
            "$sort": {"applied_at": -1}
        }
    ]
    
    results = aggregate("applications", pipeline)
    return [serialize_doc(doc) for doc in results]

def worker_pending_applications(worker_id):
    """Get pending job applications for a worker"""
    if isinstance(worker_id, str):
        worker_id = to_object_id(worker_id)
    
    # Import partition-aware functions
    from models.job_model_mongo import get_job_by_id
    
    # Find pending applications for this worker
    applications = find_many("applications", {
        "worker_id": worker_id,
        "application_status": "pending"
    })
    
    results = []
    for app in applications:
        # Get job data from partitioned collections
        job = get_job_by_id(str(app["job_id"]))
        if not job:
            continue
        
        # Get employer data
        employer = find_one("employers", {"_id": to_object_id(job.get("employer_id"))})
        if not employer:
            continue
        
        # Build salary range string
        salary_range = "Salary not specified"
        if job.get("salary_min") and job.get("salary_max"):
            salary_range = f"₹{job['salary_min']} - ₹{job['salary_max']}"
        
        results.append({
            "application_id": str(app["_id"]),
            "application_status": app.get("application_status", "pending"),
            "applied_at": app.get("applied_at"),
            "job_id": str(app["job_id"]),
            "title": job.get("title", "N/A"),
            "description": job.get("description", ""),
            "location": job.get("location", "N/A"),
            "required_skills": job.get("required_skills", []),
            "salary_range": salary_range,
            "posted_at": job.get("posted_at"),
            "company_name": employer.get("company_name", "N/A")
        })
    
    # Sort by applied_at descending
    results.sort(key=lambda x: x.get("applied_at") or datetime.min, reverse=True)
    return results

def worker_approved_applications(worker_id):
    """Get approved job applications for a worker"""
    if isinstance(worker_id, str):
        worker_id = to_object_id(worker_id)
    
    # Import partition-aware functions
    from models.job_model_mongo import get_job_by_id
    
    # Find approved applications for this worker
    applications = find_many("applications", {
        "worker_id": worker_id,
        "application_status": "approved"
    })
    
    results = []
    for app in applications:
        # Get job data from partitioned collections
        job = get_job_by_id(str(app["job_id"]))
        if not job:
            continue
        
        # Get employer data
        employer = find_one("employers", {"_id": to_object_id(job.get("employer_id"))})
        if not employer:
            continue
        
        # Get employer user data for email
        employer_user = find_one("users", {"_id": employer.get("user_id")})
        
        # Build salary range string
        salary_range = "Salary not specified"
        if job.get("salary_min") and job.get("salary_max"):
            salary_range = f"₹{job['salary_min']} - ₹{job['salary_max']}"
        
        results.append({
            "application_id": str(app["_id"]),
            "application_status": app.get("application_status", "approved"),
            "applied_at": app.get("applied_at"),
            "job_id": str(app["job_id"]),
            "title": job.get("title", "N/A"),
            "description": job.get("description", ""),
            "location": job.get("location", "N/A"),
            "required_skills": job.get("required_skills", []),
            "salary_range": salary_range,
            "posted_at": job.get("posted_at"),
            "company_name": employer.get("company_name", "N/A"),
            "company_phone": employer.get("phone", "N/A"),
            "company_location": employer.get("location", "N/A"),
            "employer_name": employer.get("employer_name", "N/A"),
            "employer_email": employer_user.get("email", "N/A") if employer_user else "N/A"
        })
    
    # Sort by applied_at descending
    results.sort(key=lambda x: x.get("applied_at") or datetime.min, reverse=True)
    return results

def get_application_by_id(application_id):
    """Get application by ID"""
    if isinstance(application_id, str):
        application_id = to_object_id(application_id)
    
    app = find_one("applications", {"_id": application_id})
    if app:
        app = serialize_doc(app)
        app["application_id"] = app["id"]  # Add application_id for compatibility
    return app

def get_worker_applications(worker_id):
    """Get all applications by a worker (simplified version)"""
    if isinstance(worker_id, str):
        worker_id = to_object_id(worker_id)
    
    applications = find_many("applications", {"worker_id": worker_id}, sort=[("applied_at", -1)])
    result = []
    for app in applications:
        app = serialize_doc(app)
        app["application_id"] = app["id"]  # Add application_id for compatibility
        result.append(app)
    return result

def delete_application(application_id):
    """Delete an application"""
    if isinstance(application_id, str):
        application_id = to_object_id(application_id)
    
    return delete_one("applications", {"_id": application_id})

def get_application_stats():
    """Get application statistics"""
    pipeline = [
        {
            "$group": {
                "_id": "$application_status",
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "status": "$_id",
                "count": 1,
                "_id": 0
            }
        }
    ]
    
    results = aggregate("applications", pipeline)
    return [serialize_doc(doc) for doc in results]