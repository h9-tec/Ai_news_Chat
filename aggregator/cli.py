import argparse, time
from apscheduler.schedulers.background import BackgroundScheduler
from .scraper import run as scrape_run
from .ui import launch


def main():
    p = argparse.ArgumentParser("AI News Aggregator")
    p.add_argument("--scrape", action="store_true")
    p.add_argument("--serve", action="store_true")
    p.add_argument("--auto",  action="store_true", help="schedule scraping every 24h")
    args = p.parse_args()

    if args.scrape:
        scrape_run()

    if args.auto:
        sched = BackgroundScheduler(daemon=True)
        sched.add_job(scrape_run, "interval", hours=24, next_run_time=time.time())
        sched.start()
        print("[Scheduler] scraping every 24h …")

    if args.serve:
        launch()

if __name__ == "__main__":
    main() 