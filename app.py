import os
import pathlib
import sys
from datetime import datetime
from logging.config import dictConfig

from flask import Flask, jsonify, redirect

from scheduler import init_scheduler

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Configure logging
dictConfig({
    "version": 1,
    "formatters": {"default": {
        "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
    }},
    "handlers": {"wsgi": {
        "class": "logging.StreamHandler",
        "stream": "ext://flask.logging.wsgi_errors_stream",
        "formatter": "default"
    }},
    "root": {
        "level": "INFO",
        "handlers": ["wsgi"]
    }
})

app = Flask(__name__)

# Configure scheduler
app.config["SCHEDULER_API_ENABLED"] = True
app.config["SCHEDULER_TIMEZONE"] = "Asia/Hong_Kong"
init_scheduler(app)

# endpoints
@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/report")
@app.route("/report/<report_type>", methods=["GET"])
def get_report(report_type="overall"):
    """
    Response the latest report generated by the analyzer.

    Parameters
    ----------
    report_type : str
        The type of report to retrieve, e.g., `overall` from the `report/` folder.

    Returns
    -------
    str
        A report in string format.
    """
    report_dir = pathlib.Path(__file__).parent / "report" / report_type
    latest_time = None
    latest_file = None

    # Loop through the report directory and find the latest report file
    for year_dir in report_dir.iterdir():
        if year_dir.is_dir():
            for month_dir in year_dir.iterdir():
                if month_dir.is_dir():
                    for day_dir in month_dir.iterdir():
                        if day_dir.is_dir():
                            for file_name in day_dir.iterdir():
                                if file_name.is_file():
                                    # Get the modification time of the file
                                    file_time = datetime.fromtimestamp(file_name.stat().st_mtime)
                                    if latest_time is None or file_time > latest_time:
                                        # Update the latest time and file name
                                        latest_time = file_time
                                        latest_file = file_name

    # If no report file is found, return an error
    if not latest_file:
        return jsonify({"error": "Report not found"}), 404
    else:
        # Read the report file and return it as a JSON response
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                report = f.read()
            return jsonify({"report_time": latest_time.isoformat(), "report": report})

        except Exception as e:
            return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run()
