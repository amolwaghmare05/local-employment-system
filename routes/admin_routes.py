from flask import Blueprint, render_template, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from models.user_model_mongo import admin_list_users, delete_user
from models.job_model_mongo import update_job, delete_job
from models.application_model_mongo import update_application_status

admin_bp = Blueprint("admin_pages", __name__)

@admin_bp.route("/admin/dashboard")
def admin_dashboard():
    """Remove JWT check from route - it will be handled client-side"""
    return render_template("admin_dashboard.html")

@admin_bp.delete("/api/admin/users/<int:user_id>")
@jwt_required()
def delete_user_route(user_id):
    try:
        claims = get_jwt()
        delete_user(user_id)
        log_admin_action(
            admin_user_id=int(claims["sub"]),
            action_type="delete",
            target_table="users",
            target_id=user_id,
            note=f"Deleted user ID {user_id}"
        )
        return jsonify({"msg": "User deleted successfully"})
    except Exception as e:
        print(f"Error deleting user {user_id}:", str(e))
        return jsonify({"msg": f"Error deleting user: {str(e)}"}), 500

@admin_bp.put("/api/admin/jobs/<int:job_id>")
@jwt_required()
def update_job_route(job_id):
    try:
        data = request.json
        claims = get_jwt()
        update_job(job_id, data)
        log_admin_action(
            admin_user_id=int(claims["sub"]),
            action_type="update",
            target_table="jobs",
            target_id=job_id,
            note=f"Updated job ID {job_id}: {data.get('title', 'No title')}"
        )
        return jsonify({"msg": "Job updated successfully"})
    except Exception as e:
        print(f"Error updating job {job_id}:", str(e))
        return jsonify({"msg": f"Error updating job: {str(e)}"}), 500

@admin_bp.delete("/api/admin/jobs/<int:job_id>")
@jwt_required()
def delete_job_route(job_id):
    try:
        claims = get_jwt()
        delete_job(job_id)
        log_admin_action(
            admin_user_id=int(claims["sub"]),
            action_type="delete",
            target_table="jobs",
            target_id=job_id,
            note=f"Deleted job ID {job_id}"
        )
        return jsonify({"msg": "Job deleted successfully"})
    except Exception as e:
        print(f"Error deleting job {job_id}:", str(e))
        return jsonify({"msg": f"Error deleting job: {str(e)}"}), 500

@admin_bp.put("/api/admin/applications/<int:application_id>")
@jwt_required()
def update_application_route(application_id):
    try:
        claims = get_jwt()
        status = request.json.get("status")
        if status not in ("pending", "approved", "rejected"):
            return jsonify({"msg": "Invalid status"}), 400
            
        update_application_status(application_id, status)
        log_admin_action(
            admin_user_id=int(claims["sub"]),
            action_type="update",
            target_table="applications",
            target_id=application_id,
            note=f"Updated application ID {application_id} status to {status}"
        )
        return jsonify({"msg": "Application status updated successfully"})
    except Exception as e:
        print(f"Error updating application {application_id}:", str(e))
        return jsonify({"msg": f"Error updating application: {str(e)}"}), 500

@admin_bp.get("/api/admin/activity-logs")
@jwt_required()
def get_activity_logs():
    try:
        logs = get_admin_actions()
        return jsonify(logs)
    except Exception as e:
        print("Error fetching activity logs:", str(e))
        return jsonify({"msg": "Error fetching activity logs"}), 500
