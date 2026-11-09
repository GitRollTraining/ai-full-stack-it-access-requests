"""Strict supplied-schema validation plus policy-level semantic findings."""
import copy
import datetime as dt
import re
from .config import SCHEMA

SCALARS = tuple(k for k in SCHEMA['required'] if k not in ('issues', 'supporting_quotes'))
REQUIRED = tuple(k for k in SCALARS if k != 'kind')


class ValidationError(ValueError):
    pass


def validate(extraction, message, document_id):
    if not isinstance(extraction, dict) or set(extraction) != set(SCHEMA['required']):
        raise ValidationError('schema keys differ from snapshot.schema.json')
    value = copy.deepcopy(extraction)
    for key, spec in SCHEMA['properties'].items():
        item = value[key]
        if spec['type'] == 'array':
            if not isinstance(item, list) or any(not isinstance(x, str) for x in item):
                raise ValidationError(f'{key} must be an array of strings')
        elif item is not None and (not isinstance(item, str) or not item.strip()):
            raise ValidationError(f'{key} must be a nonempty string or null')
        if 'enum' in spec and item not in spec['enum']:
            raise ValidationError(f'{key} has an invalid enum value')
    if not value['supporting_quotes'] or any(not q or q not in message for q in value['supporting_quotes']):
        raise ValidationError('supporting_quotes must be nonempty literal message substrings')
    findings = set()

    def issue(text):
        if text not in value['issues']:
            value['issues'].append(text)

    for key in SCALARS:
        if value[key] is None:
            issue(f'{key}: missing or unresolved explicit fact.')
            findings.add('missing')
    for key in ('request_date', 'start_date', 'end_date'):
        date = value[key]
        if date is not None:
            try:
                if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', date):
                    raise ValueError()
                dt.date.fromisoformat(date)
                if date not in message:
                    raise ValueError()
            except ValueError:
                value[key] = None
                issue(f'{key}: invalid or unsupported absolute date; see source evidence.')
                findings.add('missing')
    request_id = value['request_id']
    if request_id is not None and request_id != document_id.rsplit('.', 1)[0]:
        issue('request_id: identifier mismatch with document filename.')
        findings.add('mismatch')
    # LLM classification handles semantic attempts; these patterns also catch explicit
    # bypass instructions even when the model neglects to flag them.
    if re.search(r'system\s+override|ignore\b.{0,60}\b(instructions|rules)|'
                 r'bypass\b.{0,60}\b(approval|rules)|display\b.{0,40}\bapi key|'
                 r'mark\b.{0,40}\bas approved', message, re.I | re.S):
        findings.add('override')
        issue('override: attempted instruction override in source; inspect-message.')
        if message not in value['supporting_quotes']:
            value['supporting_quotes'].append(message)
    for item in value['issues']:
        if re.search(r'\boverride\b|instruction.attempt', item, re.I):
            findings.add('override')
        if re.search(r'\bconflict\w*\b|contradict\w*|unresolved', item, re.I):
            # Generated null issues are expected and still imply clarification.
            findings.add('conflict')
    if value['start_date'] and value['end_date'] and value['start_date'] > value['end_date']:
        findings.add('reversed')
        issue('start_date is after end_date: reversed access interval.')
    return value, findings
