-- SLA breach rate by department
SELECT
    department,
    COUNT(*) AS total_tickets,
    SUM(CASE WHEN closed_at > sla_due_at THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS sla_breach_rate
FROM support_tickets
GROUP BY department
ORDER BY sla_breach_rate DESC;

-- Ticket volume by issue type
SELECT
    issue_type,
    COUNT(*) AS total_tickets
FROM support_tickets
GROUP BY issue_type
ORDER BY total_tickets DESC;

-- Agent workload
SELECT
    agent,
    COUNT(*) AS total_tickets,
    AVG(resolution_hours) AS avg_resolution_hours
FROM support_tickets
GROUP BY agent
ORDER BY total_tickets DESC;
