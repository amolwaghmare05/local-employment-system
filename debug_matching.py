#!/usr/bin/env python3
"""
Debug script to test job matching functionality
"""

import sys
import os
from pprint import pprint

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# MongoDB imports
from models.mongodb import find_one, find_many, aggregate
from models.job_model_mongo import worker_matched_jobs
from models.user_model_mongo import get_worker_by_user

def debug_job_matching():
    print("=== JOB MATCHING DEBUG ===")
    
    # Get worker1's details
    print("\n1. Worker1 Details:")
    worker_user_id = "68e737fa7cedddd24c3dda57"  # From the API response
    worker = get_worker_by_user(worker_user_id)
    print(f"Worker: {worker}")
    
    if not worker:
        print("ERROR: Worker not found!")
        return
    
    worker_skills = worker.get('skills', '')
    worker_location = worker.get('location', '')
    
    print(f"Skills: {worker_skills}")
    print(f"Location: {worker_location}")
    
    # Check available jobs
    print("\n2. Available Jobs:")
    jobs = find_many("jobs", {"status": "open"})
    print(f"Total open jobs: {len(jobs)}")
    
    for i, job in enumerate(jobs):
        print(f"\nJob {i+1}:")
        print(f"  Title: {job.get('title')}")
        print(f"  Required Skills: {job.get('required_skills')}")
        print(f"  Location: {job.get('location')}")
        print(f"  Status: {job.get('status')}")
    
    # Test the matching function
    print(f"\n3. Testing job matching for worker {worker['worker_id']}:")
    matched_jobs = worker_matched_jobs(worker['worker_id'], worker_skills, worker_location)
    print(f"Matched jobs count: {len(matched_jobs)}")
    
    if matched_jobs:
        for i, job in enumerate(matched_jobs):
            print(f"\nMatched Job {i+1}:")
            pprint(job)
    else:
        print("No matched jobs found!")
    
    # Manual skill matching test
    print(f"\n4. Manual Skill Matching Test:")
    worker_skill_list = [s.strip().lower() for s in worker_skills.split(',') if s.strip()]
    print(f"Worker skill list: {worker_skill_list}")
    
    for i, job in enumerate(jobs):
        job_skills = job.get('required_skills', '').lower()
        print(f"\nJob {i+1}: {job.get('title')}")
        print(f"  Job skills: {job_skills}")
        
        matches = []
        for skill in worker_skill_list:
            if skill in job_skills:
                matches.append(skill)
        
        print(f"  Matching skills: {matches}")
        print(f"  Should match: {len(matches) > 0}")

if __name__ == "__main__":
    debug_job_matching()