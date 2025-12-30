# These blueprints only render HTML pages.
from flask import Blueprint, render_template

worker_bp = Blueprint("worker_pages", __name__)

@worker_bp.get("/worker/dashboard")
def worker_dashboard():
    return render_template("worker_dashboard.html")
