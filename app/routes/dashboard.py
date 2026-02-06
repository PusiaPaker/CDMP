from flask import Blueprint, render_template

DashBP= Blueprint('user', __name__)

@DashBP.route('/')
def get_dashboard():
    dashboard_title = 'All Projects View'

    return render_template("dashboard/dashboard_index.html", dashboard_title=dashboard_title), 200

