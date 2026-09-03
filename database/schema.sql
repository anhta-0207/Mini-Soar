CREATE TABLE IF NOT EXISTS remediation_history (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,

    event_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL,

    host VARCHAR(255) NOT NULL,
    service VARCHAR(255) NOT NULL,

    action VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,

    duration_seconds DECIMAL(10,3) NOT NULL DEFAULT 0,

    message TEXT NULL,

    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    PRIMARY KEY (id),

    INDEX idx_event_id (event_id),
    INDEX idx_event_type (event_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);
