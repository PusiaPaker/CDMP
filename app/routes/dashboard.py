from flask import Blueprint

DashBP= Blueprint('user', __name__)

@DashBP.route('/dashboard')
def get_dashboard():
    return {
        "message": "Hello, World!",
        "status": "success"
    }
