from models.mongodb import (
    find_one, find_many, insert_one, update_one, delete_one,
    to_object_id, serialize_doc, aggregate, get_jobs_partition_collection,
    get_collection
)
from bson import ObjectId
from datetime import datetime, date
import re

def post_job(employer_id, data):
    """Create a new job posting (uses range partitioning by year)"""
    if isinstance(employer_id, str):
        employer_id = to_object_id(employer_id)
    
    posted_at = datetime.utcnow()
    job_doc = {
        "employer_id": employer_id,
        "title": data.get("title", ""),
        "required_skills": data.get("required_skills", ""),
        "description": data.get("description", ""),
        "salary_min": float(data.get("salary_min", 0)) if data.get("salary_min") else None,
        "salary_max": float(data.get("salary_max", 0)) if data.get("salary_max") else None,
        "location": data.get("location", ""),
        "status": "open",
        "posted_at": posted_at,
        "created_at": posted_at
    }
    
    # Insert into year-based partition
    year = posted_at.year
    partition_coll = get_jobs_partition_collection(year)
    result = get_collection(partition_coll).insert_one(job_doc)
    return result.inserted_id

def _get_all_job_partitions():
    """Get all job partition collections"""
    db_instance = get_collection("jobs").database
    collections = db_instance.list_collection_names()
    job_partitions = [c for c in collections if c.startswith("jobs_") and c != "jobs"]
    return job_partitions

def worker_matched_jobs(worker_id, skills, location=None):
    """Find jobs matching worker's skills and location (searches across year partitions)"""
    if isinstance(worker_id, str):
        worker_id = to_object_id(worker_id)
    
    # Split worker skills into a list and clean them
    worker_skills = [s.strip().lower() for s in skills.split(',') if s.strip()]
    
    # Create regex patterns for skill matching
    skill_patterns = [{"required_skills": {"$regex": skill, "$options": "i"}} for skill in worker_skills]
    
    # Build the aggregation pipeline
    pipeline = [
        {
            "$match": {
                "status": "open",
                "$or": skill_patterns
            }
        },
        {
            "$lookup": {
                "from": "employers",
                "localField": "employer_id",
                "foreignField": "_id",
                "as": "employer"
            }
        },
        {
            "$unwind": "$employer"
        },
        {
            "$lookup": {
                "from": "applications",
                "let": {"job_id": "$_id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$job_id", "$$job_id"]},
                                    {"$eq": ["$worker_id", worker_id]}
                                ]
                            }
                        }
                    }
                ],
                "as": "application"
            }
        },
        {
            "$addFields": {
                "application_status": {
                    "$cond": {
                        "if": {"$gt": [{"$size": "$application"}, 0]},
                        "then": {"$arrayElemAt": ["$application.application_status", 0]},
                        "else": None
                    }
                }
            }
        },
        {
            "$project": {
                "job_id": {"$toString": "$_id"},
                "title": 1,
                "location": 1,
                "posted_at": 1,
                "required_skills": 1,
                "description": 1,
                "salary_min": 1,
                "salary_max": 1,
                "application_status": 1,
                "company_name": "$employer.company_name",
                "company_phone": "$employer.phone",
                "company_location": "$employer.location"
            }
        },
        {
            "$sort": {"posted_at": -1}
        },
        {
            "$limit": 100
        }
    ]
    
    # Add location filter if specified
    if location:
        pipeline[0]["$match"]["$and"] = [
            {"$or": [
                {"location": location},
                {"location": {"$exists": False}},
                {"location": None},
                {"location": ""}
            ]}
        ]
    
    # Search across all year partitions
    all_results = []
    for partition_name in _get_all_job_partitions():
        try:
            partition_results = list(get_collection(partition_name).aggregate(pipeline))
            all_results.extend(partition_results)
        except Exception as e:
            print(f"Error querying partition {partition_name}: {e}")
            continue
    
    # Sort by posted_at and limit
    all_results.sort(key=lambda x: x.get("posted_at", datetime.min), reverse=True)
    all_results = all_results[:100]
    
    # Serialize the results to handle ObjectId fields
    return [serialize_doc(doc) for doc in all_results]

def admin_list_jobs():
    """Get all jobs with details for admin dashboard"""
    pipeline = [
        {
            "$lookup": {
                "from": "employers",
                "localField": "employer_id",
                "foreignField": "_id",
                "as": "employer"
            }
        },
        {
            "$unwind": "$employer"
        },
        {
            "$project": {
                "job_id": {"$toString": "$_id"},
                "title": 1,
                "employer_id": {"$toString": "$employer_id"},
                "required_skills": 1,
                "description": 1,
                "salary_min": 1,
                "salary_max": 1,
                "location": 1,
                "status": 1,
                "posted_at": 1,
                "company_name": "$employer.company_name"
            }
        },
        {
            "$sort": {"posted_at": -1}
        }
    ]
    
    # Search across all partitions
    all_results = []
    for partition_name in _get_all_job_partitions():
        try:
            partition_results = list(get_collection(partition_name).aggregate(pipeline))
            all_results.extend(partition_results)
        except Exception as e:
            print(f"Error querying partition {partition_name}: {e}")
            continue
    
    # Sort by posted_at
    all_results.sort(key=lambda x: x.get("posted_at", datetime.min), reverse=True)
    
    return [serialize_doc(doc) for doc in all_results]

def update_job(job_id, data):
    """Update job details"""
    if isinstance(job_id, str):
        job_id = to_object_id(job_id)
    
    # First verify the job exists
    job = find_one("jobs", {"_id": job_id})
    if not job:
        raise ValueError("Job not found")
    
    # Build update document with only non-None values
    update_fields = {}
    
    if "title" in data and data["title"] is not None:
        update_fields["title"] = data["title"]
    if "required_skills" in data and data["required_skills"] is not None:
        update_fields["required_skills"] = data["required_skills"]
    if "description" in data and data["description"] is not None:
        update_fields["description"] = data["description"]
    if "salary_min" in data and data["salary_min"] is not None:
        update_fields["salary_min"] = float(data["salary_min"])
    if "salary_max" in data and data["salary_max"] is not None:
        update_fields["salary_max"] = float(data["salary_max"])
    if "location" in data and data["location"] is not None:
        update_fields["location"] = data["location"]
    if "status" in data and data["status"] is not None:
        update_fields["status"] = data["status"]
    
    if update_fields:
        update_fields["updated_at"] = datetime.utcnow()
        return update_one("jobs", {"_id": job_id}, {"$set": update_fields})
    
    return 0

def delete_job(job_id):
    """Delete a job and its applications (searches across partitions)"""
    if isinstance(job_id, str):
        job_id = to_object_id(job_id)
    
    # Delete applications first
    get_collection("applications").delete_many({"job_id": job_id})
    
    # Delete from partitions
    deleted = False
    for partition_name in _get_all_job_partitions():
        result = get_collection(partition_name).delete_one({"_id": job_id})
        if result.deleted_count > 0:
            deleted = True
            break
    
    return 1 if deleted else 0

def get_job_by_id(job_id):
    """Get a job by its ID (searches across partitions)"""
    if isinstance(job_id, str):
        job_id = to_object_id(job_id)
    
    # Search across all partitions
    for partition_name in _get_all_job_partitions():
        job = get_collection(partition_name).find_one({"_id": job_id})
        if job:
            job = serialize_doc(job)
            job["job_id"] = job["id"]  # Add job_id for compatibility
            return job
    return None

def get_jobs_by_employer(employer_id):
    """Get all jobs posted by an employer (searches across partitions)"""
    if isinstance(employer_id, str):
        employer_id = to_object_id(employer_id)
    
    # Search across all partitions
    all_jobs = []
    for partition_name in _get_all_job_partitions():
        try:
            jobs = list(get_collection(partition_name).find({"employer_id": employer_id}))
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"Error querying partition {partition_name}: {e}")
            continue
    
    # Sort by posted_at descending
    all_jobs.sort(key=lambda x: x.get("posted_at", datetime.min), reverse=True)
    
    result = []
    for job in all_jobs:
        job = serialize_doc(job)
        job["job_id"] = job["id"]  # Add job_id for compatibility
        result.append(job)
    return result

# COLLECTION INSIGHTS (MongoDB collection statistics)
def jobs_partition_stats():
    """Get job collection statistics"""
    from models.mongodb import get_collection
    
    # Get collection statistics
    collection = get_collection("jobs")
    stats = collection.estimated_document_count()
    
    # Group jobs by year for analytical insights
    pipeline = [
        {
            "$group": {
                "_id": {"$year": "$posted_at"},
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "year": "$_id",
                "job_count": "$count",
                "_id": 0
            }
        },
        {
            "$sort": {"year": 1}
        }
    ]
    
    yearly_stats = aggregate("jobs", pipeline)
    
    # Format for analytics dashboard
    result = []
    for stat in yearly_stats:
        result.append({
            "COLLECTION_STATS": f"jobs_year_{stat['year']}",
            "year": stat["year"],
            "document_count": stat["job_count"]
        })
    
    return result

def search_jobs(query_text, location=None, skills=None):
    """Search jobs by text, location, and skills"""
    match_conditions = {"status": "open"}
    
    # Text search
    if query_text:
        match_conditions["$or"] = [
            {"title": {"$regex": query_text, "$options": "i"}},
            {"description": {"$regex": query_text, "$options": "i"}},
            {"required_skills": {"$regex": query_text, "$options": "i"}}
        ]
    
    # Location filter
    if location:
        match_conditions["$and"] = match_conditions.get("$and", [])
        match_conditions["$and"].append({
            "$or": [
                {"location": {"$regex": location, "$options": "i"}},
                {"location": {"$exists": False}},
                {"location": None}
            ]
        })
    
    # Skills filter
    if skills:
        skill_list = [s.strip() for s in skills.split(',') if s.strip()]
        skill_patterns = [{"required_skills": {"$regex": skill, "$options": "i"}} for skill in skill_list]
        if skill_patterns:
            match_conditions["$and"] = match_conditions.get("$and", [])
            match_conditions["$and"].append({"$or": skill_patterns})
    
    pipeline = [
        {"$match": match_conditions},
        {
            "$lookup": {
                "from": "employers",
                "localField": "employer_id",
                "foreignField": "_id",
                "as": "employer"
            }
        },
        {"$unwind": "$employer"},
        {
            "$project": {
                "job_id": {"$toString": "$_id"},
                "title": 1,
                "location": 1,
                "posted_at": 1,
                "required_skills": 1,
                "description": 1,
                "salary_min": 1,
                "salary_max": 1,
                "company_name": "$employer.company_name"
            }
        },
        {"$sort": {"posted_at": -1}},
        {"$limit": 50}
    ]
    
    results = aggregate("jobs", pipeline)
    return [serialize_doc(doc) for doc in results]