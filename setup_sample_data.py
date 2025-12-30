#!/usr/bin/env python3
"""
Data Setup Script: MongoDB Sample Data
====================================
This script creates sample data for the MongoDB database.
Use this if you don't have existing data to migrate.

Usage:
    python3 setup_sample_data.py
"""

import sys
import os
from datetime import datetime, timedelta
from bson import ObjectId

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# MongoDB imports
from models.mongodb import insert_one, insert_many, find_one, get_collection
from passlib.hash import bcrypt_sha256 as bcrypt

def create_sample_users():
    """Create sample users"""
    print("Creating sample users...")
    
    users = [
        {
            "email": "admin@example.com",
            "password_hash": bcrypt.hash("admin123"),
            "role": "admin",
            "created_at": datetime.utcnow()
        },
        {
            "email": "employer1@company.com", 
            "password_hash": bcrypt.hash("employer123"),
            "role": "employer",
            "created_at": datetime.utcnow()
        },
        {
            "email": "employer2@tech.com",
            "password_hash": bcrypt.hash("employer123"), 
            "role": "employer",
            "created_at": datetime.utcnow()
        },
        {
            "email": "worker1@email.com",
            "password_hash": bcrypt.hash("worker123"),
            "role": "worker", 
            "created_at": datetime.utcnow()
        },
        {
            "email": "worker2@email.com",
            "password_hash": bcrypt.hash("worker123"),
            "role": "worker",
            "created_at": datetime.utcnow()
        },
        {
            "email": "worker3@email.com",
            "password_hash": bcrypt.hash("worker123"),
            "role": "worker",
            "created_at": datetime.utcnow()
        }
    ]
    
    user_ids = []
    for user in users:
        # Check if user already exists
        existing = find_one("users", {"email": user["email"]})
        if existing:
            print(f"User {user['email']} already exists, skipping...")
            user_ids.append(existing["_id"])
        else:
            result = insert_one("users", user)
            user_ids.append(result.inserted_id)
            print(f"Created user: {user['email']}")
    
    return user_ids

def create_sample_profiles(user_ids):
    """Create sample profiles for users"""
    print("Creating sample profiles...")
    
    # Admin profile
    admin_profile = {
        "user_id": user_ids[0],
        "full_name": "System Administrator",
        "created_at": datetime.utcnow()
    }
    
    # Check if admin profile already exists
    existing_admin = find_one("admins", {"user_id": user_ids[0]})
    if not existing_admin:
        admin_result = insert_one("admins", admin_profile)
        print(f"Created admin profile: {admin_profile['full_name']}")
    else:
        admin_result = type('obj', (object,), {'inserted_id': existing_admin["_id"]})
    
    # Employer profiles
    employer_profiles = [
        {
            "user_id": user_ids[1],
            "company_name": "TechCorp Solutions",
            "location": "Mumbai",
            "phone": "+91-9876543210",
            "created_at": datetime.utcnow()
        },
        {
            "user_id": user_ids[2], 
            "company_name": "Digital Innovations Ltd",
            "location": "Pune",
            "phone": "+91-9876543211",
            "created_at": datetime.utcnow()
        }
    ]
    
    employer_ids = []
    for i, profile in enumerate(employer_profiles):
        existing_employer = find_one("employers", {"user_id": user_ids[i+1]})
        if not existing_employer:
            result = insert_one("employers", profile)
            employer_ids.append(result.inserted_id)
            print(f"Created employer profile: {profile['company_name']}")
        else:
            employer_ids.append(existing_employer["_id"])
    
    # Worker profiles
    worker_profiles = [
        {
            "user_id": user_ids[3],
            "full_name": "Rahul Sharma",
            "phone": "+91-9876543212",
            "location": "Mumbai",
            "skills": "Python, JavaScript, React, Node.js",
            "created_at": datetime.utcnow()
        },
        {
            "user_id": user_ids[4],
            "full_name": "Priya Patel", 
            "phone": "+91-9876543213",
            "location": "Pune",
            "skills": "Java, Spring Boot, MySQL, Angular",
            "created_at": datetime.utcnow()
        },
        {
            "user_id": user_ids[5],
            "full_name": "Amit Kumar",
            "phone": "+91-9876543214", 
            "location": "Delhi",
            "skills": "PHP, Laravel, Vue.js, PostgreSQL",
            "created_at": datetime.utcnow()
        }
    ]
    
    worker_ids = []
    for i, profile in enumerate(worker_profiles):
        existing_worker = find_one("workers", {"user_id": user_ids[i+3]})
        if not existing_worker:
            result = insert_one("workers", profile)
            worker_ids.append(result.inserted_id)
            print(f"Created worker profile: {profile['full_name']}")
        else:
            worker_ids.append(existing_worker["_id"])
    
    return admin_result.inserted_id, employer_ids, worker_ids

def create_sample_jobs(employer_ids):
    """Create sample job postings"""
    print("Creating sample jobs...")
    
    jobs = [
        {
            "employer_id": employer_ids[0],
            "title": "Full Stack Developer",
            "description": "We are looking for a skilled Full Stack Developer to join our team. Experience with Python, React, and MongoDB required.",
            "location": "Mumbai",
            "status": "open",
            "required_skills": "Python, React, MongoDB, Node.js",
            "salary_min": 800000,
            "salary_max": 1200000,
            "posted_at": datetime.utcnow() - timedelta(days=5),
            "created_at": datetime.utcnow() - timedelta(days=5)
        },
        {
            "employer_id": employer_ids[0],
            "title": "Frontend Developer",
            "description": "Join our frontend team to build amazing user interfaces. React and JavaScript expertise required.", 
            "location": "Mumbai",
            "status": "open",
            "required_skills": "JavaScript, React, CSS, HTML",
            "salary_min": 600000,
            "salary_max": 900000,
            "posted_at": datetime.utcnow() - timedelta(days=3),
            "created_at": datetime.utcnow() - timedelta(days=3)
        },
        {
            "employer_id": employer_ids[1],
            "title": "Backend Java Developer",
            "description": "Experienced Java developer needed for enterprise applications. Spring Boot and microservices experience preferred.",
            "location": "Pune", 
            "status": "open",
            "required_skills": "Java, Spring Boot, MySQL, Microservices",
            "salary_min": 700000,
            "salary_max": 1100000,
            "posted_at": datetime.utcnow() - timedelta(days=7),
            "created_at": datetime.utcnow() - timedelta(days=7)
        },
        {
            "employer_id": employer_ids[1],
            "title": "DevOps Engineer",
            "description": "Looking for DevOps engineer to manage our cloud infrastructure. AWS and Docker experience required.",
            "location": "Pune",
            "status": "open",
            "required_skills": "AWS, Docker, Kubernetes, Jenkins",
            "salary_min": 900000,
            "salary_max": 1400000,
            "posted_at": datetime.utcnow() - timedelta(days=2),
            "created_at": datetime.utcnow() - timedelta(days=2)
        },
        {
            "employer_id": employer_ids[0],
            "title": "PHP Developer",
            "description": "PHP developer needed for web application development. Laravel framework experience preferred.",
            "location": "Remote",
            "status": "open",
            "required_skills": "PHP, Laravel, MySQL, Vue.js",
            "salary_min": 500000,
            "salary_max": 800000,
            "posted_at": datetime.utcnow() - timedelta(days=1),
            "created_at": datetime.utcnow() - timedelta(days=1)
        }
    ]
    
    job_ids = []
    for job in jobs:
        # Check if similar job already exists
        existing = find_one("jobs", {"title": job["title"], "employer_id": job["employer_id"]})
        if not existing:
            result = insert_one("jobs", job)
            job_ids.append(result.inserted_id)
            print(f"Created job: {job['title']} at {job['location']}")
        else:
            job_ids.append(existing["_id"])
    
    return job_ids

def create_sample_applications(job_ids, worker_ids):
    """Create sample job applications"""
    print("Creating sample applications...")
    
    applications = [
        {
            "job_id": job_ids[0],  # Full Stack Developer
            "worker_id": worker_ids[0],  # Rahul Sharma
            "application_status": "pending",
            "applied_at": datetime.utcnow() - timedelta(days=2),
            "created_at": datetime.utcnow() - timedelta(days=2)
        },
        {
            "job_id": job_ids[1],  # Frontend Developer  
            "worker_id": worker_ids[0],  # Rahul Sharma
            "application_status": "approved",
            "applied_at": datetime.utcnow() - timedelta(days=1),
            "created_at": datetime.utcnow() - timedelta(days=1)
        },
        {
            "job_id": job_ids[2],  # Backend Java Developer
            "worker_id": worker_ids[1],  # Priya Patel
            "application_status": "approved", 
            "applied_at": datetime.utcnow() - timedelta(days=3),
            "created_at": datetime.utcnow() - timedelta(days=3)
        },
        {
            "job_id": job_ids[0],  # Full Stack Developer
            "worker_id": worker_ids[1],  # Priya Patel
            "application_status": "rejected",
            "applied_at": datetime.utcnow() - timedelta(days=4),
            "created_at": datetime.utcnow() - timedelta(days=4)
        },
        {
            "job_id": job_ids[4],  # PHP Developer
            "worker_id": worker_ids[2],  # Amit Kumar
            "application_status": "pending",
            "applied_at": datetime.utcnow() - timedelta(hours=6),
            "created_at": datetime.utcnow() - timedelta(hours=6)
        }
    ]
    
    for app in applications:
        # Check if application already exists
        existing = find_one("applications", {"job_id": app["job_id"], "worker_id": app["worker_id"]})
        if not existing:
            result = insert_one("applications", app)
            print(f"Created application: Worker {app['worker_id']} -> Job {app['job_id']} ({app['application_status']})")
        else:
            print(f"Application already exists: Worker {app['worker_id']} -> Job {app['job_id']}")

def verify_sample_data():
    """Verify the sample data was created"""
    print("\nVerifying sample data...")
    
    users_count = len(list(get_collection("users").find()))
    workers_count = len(list(get_collection("workers").find()))
    employers_count = len(list(get_collection("employers").find()))
    admins_count = len(list(get_collection("admins").find()))
    jobs_count = len(list(get_collection("jobs").find()))
    applications_count = len(list(get_collection("applications").find()))
    
    print(f"MongoDB document counts:")
    print(f"  Users: {users_count}")
    print(f"  Workers: {workers_count}")
    print(f"  Employers: {employers_count}")
    print(f"  Admins: {admins_count}")
    print(f"  Jobs: {jobs_count}")
    print(f"  Applications: {applications_count}")
    
    if all(count > 0 for count in [users_count, workers_count, employers_count, admins_count, jobs_count]):
        print("\n✅ Sample data verification successful!")
        return True
    else:
        print("\n❌ Sample data verification failed!")
        return False

def main():
    """Main function to create sample data"""
    print("Creating Sample Data for MongoDB")
    print("=" * 40)
    
    try:
        # Test MongoDB connection
        try:
            get_collection("users").find_one()
            print("✅ MongoDB connection successful")
        except Exception as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            return False
        
        print("\nCreating sample data...")
        print("-" * 25)
        
        # Create sample data
        user_ids = create_sample_users()
        admin_id, employer_ids, worker_ids = create_sample_profiles(user_ids)
        job_ids = create_sample_jobs(employer_ids)
        create_sample_applications(job_ids, worker_ids)
        
        # Verify sample data
        success = verify_sample_data()
        
        if success:
            print("\n🎉 Sample data created successfully!")
            print("\nSample Login Credentials:")
            print("=" * 30)
            print("Admin:")
            print("  Email: admin@example.com")
            print("  Password: admin123")
            print("\nEmployer:")
            print("  Email: employer1@company.com")
            print("  Password: employer123")
            print("\nWorker:")
            print("  Email: worker1@email.com")
            print("  Password: worker123")
            print("\nYou can now test the application at: http://127.0.0.1:5000")
        
        return success
        
    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)