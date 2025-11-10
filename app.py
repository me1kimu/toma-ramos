"""
Flask web application for class schedule finder.
"""
from flask import Flask, render_template, jsonify, request
from schedule_processor import ScheduleProcessor
import os
import json
import math

app = Flask(__name__)

# Initialize schedule processor
EXCEL_FILE = 'ING_CIVIL_EN_INFOR_Y_TEL.xlsx'
processor = ScheduleProcessor(EXCEL_FILE)


def clean_nan(obj):
    """Recursively replace NaN and None values with empty strings for JSON serialization."""
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(item) for item in obj]
    elif isinstance(obj, float) and (math.isnan(obj) or obj != obj):  # NaN check
        return ""
    elif obj is None:
        return ""
    else:
        return obj


@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')


@app.route('/api/courses')
def get_courses():
    """Get list of all courses."""
    courses = processor.get_courses_list()
    return jsonify(clean_nan(courses))


@app.route('/api/course/<course_code>')
def get_course_sections(course_code):
    """Get sections for a specific course."""
    sections = processor.get_course_sections(course_code)
    return jsonify(clean_nan(sections))


@app.route('/api/professors')
def get_professors():
    """Get list of all professors."""
    professors = processor.get_all_professors()
    return jsonify(professors)


@app.route('/api/generate-schedules', methods=['POST'])
def generate_schedules():
    """Generate valid schedule combinations."""
    data = request.get_json()
    selected_courses = data.get('courses', [])
    max_results = data.get('max_results', 50)
    optimization = data.get('optimization', None)  # 'morning', 'afternoon', 'gaps', or None
    exclude_professors = data.get('exclude_professors', None)  # Comma-separated string of professor names
    
    schedules = processor.generate_schedules(selected_courses, max_results, optimization, exclude_professors)
    
    return jsonify(clean_nan({
        'schedules': schedules,
        'count': len(schedules),
        'optimization': optimization
    }))


if __name__ == '__main__':
    # Note: Set debug=False in production environments
    # Use environment variable for configuration
    import os
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
