"""
File-based mailbox: reads governance emails that an Outlook VBA macro on
DB's Windows laptop has dropped into bridge/inbound/, as plain .txt files
(one email body per file), and pushed to the company repo.

Same function signature as the old graph_mailbox.fetch_new_governance_emails
so run_cycle.py barely changes. Each file is moved to bridge/inbound/processed/
as soon as it's read, so a crash mid-cycle doesn't silently reprocess the
same email forever, and so nothing needs a separate "mark as read" call.
"""
import logging
import os
import shutil

from . import config

log = logging.getLogger("model_monitoring_workflow")


def fetch_new_governance_emails(since_minutes: int) -> list[str]:
    """
    Returns the plain-text bodies of every .txt file currently sitting in
    bridge/inbound/. `since_minutes` is unused here (kept for signature
    compatibility with the old Graph-based version) -- the VBA side only
    ever writes files for genuinely new emails, so everything present is new.
    """
    os.makedirs(config.BRIDGE_INBOUND_DIR, exist_ok=True)
    os.makedirs(config.BRIDGE_INBOUND_PROCESSED_DIR, exist_ok=True)

    bodies = []
    for filename in sorted(os.listdir(config.BRIDGE_INBOUND_DIR)):
        if not filename.endswith(".txt"):
            continue
        filepath = os.path.join(config.BRIDGE_INBOUND_DIR, filename)
        if not os.path.isfile(filepath):
            continue
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                bodies.append(f.read())
        except Exception:
            log.exception(f"Could not read inbound file {filename}")
            continue
        finally:
            # Move out of inbound/ immediately so it's never processed twice,
            # even if parsing this email fails downstream.
            shutil.move(filepath, os.path.join(config.BRIDGE_INBOUND_PROCESSED_DIR, filename))

    return bodies
