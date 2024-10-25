from datetime import datetime, timedelta

from apscheduler.triggers.cron import CronTrigger
from flask_apscheduler import APScheduler

from Analyzer.analyzer import analyze_helper
from Scraper.scraper import scrape_helper

scheduler = APScheduler()

def scheduled_scrape(endpoint):
    scrape_helper(endpoint)
    # Schedule the analysis job after scraping is done
    scheduler.add_job(
        func=scheduled_analyze, 
        kwargs={"endpoint": endpoint}, 
        trigger="date", 
        run_date=datetime.now() + timedelta(seconds=10), 
        id="Analyze WorldMarketSubList",
        replace_existing=True
    )

def scheduled_analyze(endpoint):
    analyze_helper(endpoint)

def init_scheduler(app):
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job(
        func=scheduled_scrape, 
        kwargs={"endpoint": "sub"}, 
        trigger=CronTrigger(minute=0, timezone="Asia/Hong_Kong"), 
        id="Scrape WorldMarketSubList"
    )
