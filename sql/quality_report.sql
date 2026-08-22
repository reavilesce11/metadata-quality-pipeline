SELECT
    status,
    COUNT(*) AS record_count
FROM processed_records
GROUP BY status
ORDER BY status;

SELECT
    severity,
    issue_code,
    COUNT(*) AS issue_count
FROM quality_issues
GROUP BY severity, issue_code
ORDER BY severity, issue_count DESC, issue_code;

