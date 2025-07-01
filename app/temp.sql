-- Processed events table for idempotency
CREATE TABLE IF NOT EXISTS processed_events (
    id SERIAL PRIMARY KEY,
    event_hash VARCHAR(64) UNIQUE NOT NULL,
    event_id VARCHAR(255) NOT NULL,
    source VARCHAR(100) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    data JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Integration health monitoring
CREATE TABLE IF NOT EXISTS integration_health (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    response_time_ms FLOAT NOT NULL,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);



-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_processed_events_hash ON processed_events(event_hash);
CREATE INDEX IF NOT EXISTS idx_processed_events_source_type ON processed_events(source, event_type);
CREATE INDEX IF NOT EXISTS idx_processed_events_processed_at ON processed_events(processed_at);
CREATE INDEX IF NOT EXISTS idx_integration_health_service ON integration_health(service_name);
CREATE INDEX IF NOT EXISTS idx_integration_health_checked_at ON integration_health(checked_at);
