CREATE TABLE support_tickets (
    ticket_id TEXT PRIMARY KEY,
    customer_id TEXT,
    department TEXT,
    issue_type TEXT,
    priority TEXT,
    agent TEXT,
    channel TEXT,
    created_at TIMESTAMP,
    sla_due_at TIMESTAMP,
    closed_at TIMESTAMP,
    status TEXT,
    resolution_hours REAL,
    previous_contacts INTEGER,
    customer_message TEXT,
    customer_rating INTEGER
);
