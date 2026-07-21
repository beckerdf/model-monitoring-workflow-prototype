-- Review Inventory: the single system of record for every model monitoring
-- review. Written entirely by the automation job; never edited by hand.
--
-- NOTE: The real Archer notification email does not include an Archer
-- Model Number -- only Model Record Name. MODEL_NAME is therefore the
-- practical identifier for a review. ARCHER_MODEL_NUMBER is kept as an
-- optional column in case it becomes available later (e.g. via a future
-- Archer API/report integration), but is nullable.

CREATE TABLE IF NOT EXISTS MODEL_GOVERNANCE.MONITORING_WORKFLOW.REVIEW_INVENTORY (
    REVIEW_ID              STRING       DEFAULT UUID_STRING(),
    MODEL_NAME              STRING       NOT NULL,
    ARCHER_MODEL_NUMBER      STRING,                                    -- nullable, not present in current email
    ASSIGNED_DS_EMAIL       STRING       NOT NULL,
    ASSIGNED_DS_NAME         STRING       NOT NULL,
    START_DATE               DATE         NOT NULL,
    DUE_DATE                  DATE         NOT NULL,                    -- computed: start + cycle_days (see email_parser.py)
    STATUS                    STRING       NOT NULL DEFAULT 'Not Started', -- Not Started / In Progress / Complete
    COMPLETION_DATE            DATE,
    ASSIGNED_BY                STRING       NOT NULL DEFAULT 'Auto',        -- Auto / Manager Override
    REMINDER_7DAY_SENT_AT       TIMESTAMP_NTZ,
    REMINDER_2DAY_SENT_AT       TIMESTAMP_NTZ,
    OVERDUE_ESCALATED_AT        TIMESTAMP_NTZ,
    CREATED_AT                  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPDATED_AT                  TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (REVIEW_ID)
);

-- One row per status change, for audit trail purposes (who/what changed, when).
CREATE TABLE IF NOT EXISTS MODEL_GOVERNANCE.MONITORING_WORKFLOW.REVIEW_INVENTORY_AUDIT_LOG (
    LOG_ID       STRING    DEFAULT UUID_STRING(),
    REVIEW_ID    STRING    NOT NULL,
    EVENT_TYPE   STRING    NOT NULL, -- assigned / reassigned / status_changed / reminder_sent / escalated / closed
    DETAIL       STRING,
    LOGGED_AT    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    PRIMARY KEY (LOG_ID)
);
