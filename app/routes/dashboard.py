from flask import Blueprint, render_template

DashBP= Blueprint('user', __name__)

@DashBP.route('/')
def get_dashboard():
    return render_template("dashboard/dashboard_index.html"), 200

