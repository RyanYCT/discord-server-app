import datetime
import logging
import os
from datetime import datetime as dt
from datetime import timedelta
from logging.config import dictConfig

import psycopg2
from flask import Flask, jsonify, request
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from werkzeug.middleware.proxy_fix import ProxyFix

from common import api_settings
from etl import analyzer

from . import config


def create_app(config_object=None):
    """Application factory function."""
    app = Flask(__name__)

    # Configure the application
    configure_app(app, config_object)
    configure_logging(app)

    # Register components
    register_error_handlers(app)
    register_basic_routes(app)
    register_report_routes(app)

    # Apply WSGI middleware
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    return app


def configure_logging(app):
    """Configure logging."""
    dictConfig(api_settings.API_LOGGING_CONFIG)
    app.logger = logging.getLogger(__name__)


def configure_app(app, config_object=None):
    """Configure the Flask application."""
    # Load configuration from object if provided
    if config_object:
        app.config.from_object(config_object)

    # Load default configuration
    app.config.from_object("common.api_settings")
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "your-secret-key-here")
    app.config["DEBUG"] = os.environ.get("FLASK_DEBUG", False)

    # Security configurations
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=60),
    )


def register_error_handlers(app):
    """Register error handlers."""

    @app.errorhandler(401)
    def unauthorized_error(error):
        return jsonify({"error": "Unauthorized - No API key provided"}), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        return jsonify({"error": "Forbidden - Invalid API key"}), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500


def register_basic_routes(app):
    """Register basic routes."""

    @app.route("/")
    def index():
        app.logger.info(
            f"Request received at endpoint: '/', method: '{request.method}', timestamp: '{dt.now(datetime.timezone.utc).isoformat()}'"
        )
        return jsonify({"message": "Welcome!"})

    @app.route("/health")
    def health_check():
        app.logger.info(
            f"Request received at endpoint: '/health', method: '{request.method}', timestamp: '{dt.now(datetime.timezone.utc).isoformat()}'"
        )
        try:
            return jsonify({"status": "healthy", "timestamp": dt.now(datetime.timezone.utc).isoformat()}), 200
        except Exception as e:
            return (
                jsonify(
                    {"status": "unhealthy", "timestamp": dt.now(datetime.timezone.utc).isoformat(), "error": str(e)}
                ),
                500,
            )


def register_report_routes(app):
    """Register report routes."""

    @app.route("/report/trends", methods=["GET"])
    def trends_report():
        """
        Generate trading volume trends report.
        """
        app.logger.info(
            f"Request received at endpoint: '/report/trends', method: '{request.method}', timestamp: '{dt.now(datetime.timezone.utc).isoformat()}'"
        )
        try:
            # Get period parameter from query string, default to 7 if not provided
            period = int(request.args.get("period", 7))

            if period < 1:
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": "Period parameter must be greater than 0",
                            "timestamp": dt.now(datetime.timezone.utc).isoformat(),
                        }
                    ),
                    400,
                )

            app.logger.info(f"Analyzing trends for the past '{period}' days")
            trends_df = analyzer.analyzer.trends_analyzer(period=period)

            if trends_df.empty:
                return (
                    jsonify(
                        {
                            "status": "success",
                            "message": "No trends data available for the specified period",
                            "data": [],
                            "count": 0,
                            "timestamp": dt.now(datetime.timezone.utc).isoformat(),
                        }
                    ),
                    200,
                )

            # Convert DataFrame to list of dictionaries
            trends_data = trends_df.to_dict(orient="records")

            return (
                jsonify(
                    {
                        "status": "success",
                        "message": f"Generated trends report for the past '{period}' days",
                        "data": trends_data,
                        "count": len(trends_data),
                        "timestamp": dt.now(datetime.timezone.utc).isoformat(),
                    }
                ),
                200,
            )

        except Exception as e:
            app.logger.error(f"Error generating trends report: {e}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Error generating trends report",
                        "timestamp": dt.now(datetime.timezone.utc).isoformat(),
                    }
                ),
                500,
            )

    @app.route("/report/profit", methods=["GET"])
    def profit_report():
        """
        Retrieve the latest profit report generated by the analyzer.

        Returns
        -------
        flask.Response
            JSON response containing:
            - status: str
                Success or error status
            - message: str
                Description of the operation result
            - data: list
                Report data if available
            - count: int
                Number of records (only if data exists)
            - timestamp: str
                ISO format UTC timestamp
        """
        app.logger.info(
            f"Request received at endpoint: '/report/profit', method: '{request.method}', timestamp: '{dt.now(datetime.timezone.utc).isoformat()}'"
        )
        try:
            app.logger.info(f"Attempting to connect to database with config: {api_settings.DATABASE_CONFIG}")
            with psycopg2.connect(**api_settings.DATABASE_CONFIG) as conn:
                try:
                    with conn.cursor(cursor_factory=RealDictCursor) as cur:
                        report_type = "profit"
                        report_table_name = api_settings.ALLOWED_REPORTS.get(report_type)

                        # Get current hour start time
                        current_datetime = dt.now()
                        current_hour = current_datetime.replace(minute=0, second=0, microsecond=0)

                        # Get the most recent report time with data
                        max_hours_back = 24
                        report_time = get_latest_report_time(cur, report_table_name, current_hour, max_hours_back)

                        if not report_time:
                            return (
                                jsonify(
                                    {
                                        "status": "success",
                                        "message": f"No data available within '{max_hours_back}' hours",
                                        "timestamp": dt.now(datetime.timezone.utc).isoformat(),
                                    }
                                ),
                                200,
                            )

                        # Get the latest report data
                        results = get_report_data(cur, report_table_name, report_time)

                        if not results:
                            return (
                                jsonify(
                                    {
                                        "status": "success",
                                        "message": "No results found",
                                        "data": [],
                                        "count": 0,
                                        "timestamp": dt.now(datetime.timezone.utc).isoformat(),
                                    }
                                ),
                                200,
                            )

                        return (
                            jsonify(
                                {
                                    "status": "success",
                                    "message": "Report retrieved successfully",
                                    "data": results,
                                    "count": len(results),
                                    "timestamp": dt.now(datetime.timezone.utc).isoformat(),
                                },
                            ),
                            200,
                        )

                except psycopg2.Error as dbe:
                    app.logger.error(f"Database operation error: {dbe}")
                    app.logger.error(f"Connection params: host={api_settings.DATABASE_CONFIG['host']}")
                    app.logger.error(f"port={api_settings.DATABASE_CONFIG['port']}")
                    app.logger.error(f"dbname={api_settings.DATABASE_CONFIG['dbname']}")
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "Database operation failed",
                                "timestamp": dt.now(datetime.timezone.utc).isoformat(),
                            }
                        ),
                        500,
                    )

        except psycopg2.Error as dbe:
            app.logger.error(f"Database connection error: {dbe}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Database connection error",
                        "timestamp": dt.now(datetime.timezone.utc).isoformat(),
                    }
                ),
                500,
            )

    def get_latest_report_time(cur, table_name: str, start_time: dt, max_hours_back: int = 24) -> dt:
        """
        Find the most recent report time that has data.

        Parameters
        ----------
        cur : psycopg2.extensions.cursor
            Database cursor
        table_name : str
            Name of the table to query
        start_time : datetime
            Starting time to search from
        max_hours_back : int
            Maximum number of hours to look back

        Returns
        -------
        datetime
            Most recent report time with data
        """
        app.logger.debug(f"Finding latest report time in table '{table_name}'")
        start_time = start_time.replace(minute=0, second=0, microsecond=0)
        end_time = start_time - timedelta(hours=max_hours_back)

        params = []
        query = sql.SQL(
            """
            SELECT DISTINCT analyzetime FROM {table_name}
            WHERE analyzetime >= %s AND analyzetime <= %s
            ORDER BY analyzetime DESC LIMIT 1
            """
        ).format(table_name=sql.Identifier(table_name))
        params.extend([end_time, start_time])

        cur.execute(query, params)
        result = cur.fetchone()

        if result:
            latest_time = result["analyzetime"]
        else:
            latest_time = None

        return latest_time

    def get_report_data(cur, table_name: str, report_time: dt) -> list:
        """
        Get report data for a specific time.

        Parameters
        ----------
        cur : psycopg2.extensions.cursor
            Database cursor
        table_name : str
            Name of the table to query
        report_time : datetime
            Time of the report to retrieve

        Returns
        -------
        list
            List of report records
        """
        app.logger.debug(f"Retrieving report data from table '{table_name}' for time '{report_time}'")
        params = []
        query = sql.SQL(
            """
            SELECT DISTINCT * FROM {table_name}
            WHERE analyzetime = %s ORDER BY rate DESC
            """
        ).format(table_name=sql.Identifier(table_name))
        params.append(report_time)

        cur.execute(query, params)
        result = cur.fetchall()
        return result


if __name__ == "__main__":
    env = os.environ.get("FLASK_ENV", "development")

    if env == "production":
        app = create_app(config.ProductionConfig)

    elif env == "testing":
        app = create_app(config.TestingConfig)

    else:
        app = create_app(config.DevelopmentConfig)
