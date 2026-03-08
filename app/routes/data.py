from flask import Blueprint, render_template, session, redirect, request, url_for, jsonify, abort
import pandas as pd

from app.core import db
from app.tables import Project, Person, File

from app.src.project.files import path_to_file_from_disk

DataBP = Blueprint('data', __name__)

# @DataBP.route('/importpeople/<project_id>', methods=['POST'])
# def import_people(project_id):
#     file_id = request.form['selected_xlsx_file_id']

#     f = db.session.get(File, file_id)
#     file_name = f.file_name_disk

#     data = pd.read_excel(path_to_file_from_disk(file_name))

#     columns = data.columns

#     new_people = []
#     for ind, row in data.iterrows():
#         new_people.append(
#             Person(name=row[columns[0]], title=row[columns[2]], project_id=project_id)
#         )

#     db.session.add_all(new_people)
#     db.session.commit()

#     return redirect(url_for())


# The plan here is that this endpoint will take care of
# 
#
@DataBP.route('/columnselector', methods=['POST'])
def column_selector():
    '''
    Requires the following query params:
    - project_id 
    - file_id
    '''
    project_id = request.args.get('project_id')
    file_id = request.args.get('file_id')

    if (project_id is None) or (file_id is None):
        # return error pop up here later when that's implemented
        return abort(404)

    f = db.session.get(File, file_id)
    file_name = f.file_name_disk

    data = pd.read_excel(path_to_file_from_disk(file_name))

    columns = data.columns

    required_columns = ['Name', 'Job Title']
    optional_columns = ['Role']

    preview_data = {}
    for colname in columns:
        preview_data[colname] = data[colname].tolist()[:5]

    return render_template("project/table_column_selector.html", 
                           active_project_id=project_id,
                           required_columns=required_columns,
                           optional_columns=optional_columns,
                           preview_data=preview_data), 200
