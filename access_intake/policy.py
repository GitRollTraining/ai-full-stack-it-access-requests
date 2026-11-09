"""First-match review routing. Never approves or provisions access."""
from .validation import REQUIRED


def route(value, findings):
    if 'override' in findings:
        return 'review', 'IT Service Desk', 'inspect-message'
    if value['kind'] == 'withdrawal' and value['request_id'] and value['request_date']:
        return 'review', 'IT Service Desk', 'confirm-withdrawal'
    if (value['kind'] not in ('new', 'change') or
        findings.intersection({'conflict', 'mismatch', 'missing', 'reversed'}) or
            any(value[k] is None for k in REQUIRED)):
        return 'needs-information', 'IT Service Desk', 'clarify'
    if value['environment'] == 'production' or value['permission'] in ('write', 'admin'):
        return 'review', 'Security Review', 'review-risk-then-owner'
    return 'review', 'System Owner', 'review-request'
