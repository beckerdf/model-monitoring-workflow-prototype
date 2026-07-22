"""
Persistent background loop -- replaces cron, which isn't available on this
server. Run this once in the background and it keeps going on its own:

    nohup python -m automation.run_cycle_loop > /tmp/model_monitoring.log 2>&1 &

Each iteration:
  1. git pull  -- picks up new inbound emails and any outbound files the
     Outlook side has already sent (and deleted) since last time
  2. runs the full cycle -- process new emails, sync statuses, check
     reminders (writes new outbound notification files as needed)
  3. git push  -- publishes anything new for the Outlook side to pick up

Check it's actually running:
    ps aux | grep run_cycle_loop

Stop it:
    pkill -f run_cycle_loop

Watch it live:
    tail -f /tmp/model_monitoring.log
"""
import logging
import time
from datetime import datetime

from . import config, git_bridge, run_cycle

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("model_monitoring_workflow")


def main():
    log.info(f"Starting background loop, interval={config.RUN_INTERVAL_MINUTES} min")
    while True:
        try:
            if not git_bridge.pull():
                log.warning("git pull failed this cycle -- skipping to next interval")
            else:
                run_cycle.run_cycle()
                git_bridge.push(f"Automation cycle {datetime.now().isoformat()}")
        except Exception:
            log.exception("Cycle failed unexpectedly -- will retry next interval")

        time.sleep(config.RUN_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()
