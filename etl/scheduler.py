import logging
import signal
from logging.config import dictConfig

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from common import etl_settings
from etl.analyzer.analyzer import analyzer
from etl.scraper.scraper import scraper

load_dotenv()


# Configure logging
dictConfig(etl_settings.ETL_LOGGING_CONFIG)
logger = logging.getLogger(__name__)


def run_etl():
    try:
        # Run scraper for different endpoints
        endpoint_keys = etl_settings.ENDPOINTS.keys()
        item_name = "all"
        for endpoint_key in endpoint_keys:
            logger.info(f"Running scraper for '{endpoint_key}'")
            scraper(endpoint_key, item_name=item_name)

        # Run analyzer for different reports
        report_types = etl_settings.REPORT_TABLES.keys()
        for report_type in report_types:
            logger.info(f"Running analyzer for '{report_type}'")
            analyzer(report_type)

    except Exception as e:
        logger.error(f"ETL pipeline error: {e}", exc_info=True)


def main():
    scheduler = BackgroundScheduler()

    job_id = "data_pipeline"
    scheduler.add_job(
        func=run_etl,
        trigger=CronTrigger(minute=0, second=0),
        id=job_id,
        name="Scrape and analyze market data hourly",
        replace_existing=True,
    )

    try:
        scheduler.start()
        logger.info("Scheduler started")

        # For graceful shutdown
        def signal_handler(signum, frame):
            scheduler.shutdown()
            logger.info("Scheduler shutdown")
            exit(0)

        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Block the main thread indefinitely without consuming CPU
        signal.pause()

    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Scheduler shutdown")


if __name__ == "__main__":
    main()
