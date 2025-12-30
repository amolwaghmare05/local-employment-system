from flask import Blueprint, render_template
employer_bp = Blueprint("employer_pages", __name__)

@employer_bp.get("/employer/dashboard")
def employer_dashboard():
    return render_template("employer_dashboard.html")
