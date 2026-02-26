from flask import Blueprint, render_template, session, redirect, request, url_for, jsonify
from app.src.database import db
from app.tables.projects import Project
from app.tables.files import File
from app.src.util_functions import path_to_file_from_disk
import pandas as pd

DataBP = Blueprint('data', __name__)

@DataBP.route('/importpeople/<project_id>', methods=['POST'])
def import_people(project_id):
    file_id = request.form['selected_xlsx_file_id']

    f = db.session.get(File, file_id)
    file_name = f.file_name_disk

    data = pd.read_excel(path_to_file_from_disk(file_name))

    print(data)

    return file_id