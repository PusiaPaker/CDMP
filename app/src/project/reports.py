from io import BytesIO
import datetime

from reportlab.lib.units import inch
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

#
# Functions related to generating PDF reports
# refer to the following links for explanations on the reportlab library:
# - https://realpython.com/creating-modifying-pdf/#creating-pdf-files-with-python-and-reportlab
# - https://docs.reportlab.com/reportlab/userguide/ch2_graphics/
#

def generate_report_pdf(project):
    '''
    project: Project row from db
    '''
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    styles = getSampleStyleSheet()

    story = [
        Paragraph(project.title or '', styles['Title']),
        Spacer(1, 0.25 * inch),
        Paragraph(project.description or 'No description provided.', styles['BodyText']),
    ]

    doc.build(story)
    buffer.seek(0)
    return buffer

def get_report_file_name(project_title):
    '''
    Builds filename for a report
    '''
    current = datetime.datetime.now()
    return f'report-{project_title}-{current.date()}.pdf'