"""Validate only the handoff kit, NOT the future application. Requires PyYAML."""
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import json
import yaml

ROOT = Path(__file__).resolve().parents[1]
api = yaml.safe_load((ROOT / 'contracts/openapi.yaml').read_text(encoding='utf-8'))
assert api['openapi'].startswith('3.0.')
components = api['components']['schemas']
assert '/api/v1/webhooks/mock' in api['paths']
assert '/api/v1/orders/{order_id}/confirm' in api['paths']
assert '/api/v1/demo/orders/{order_id}/simulate' in api['paths']


def validate_refs(value):
    if isinstance(value, dict):
        if '$ref' in value:
            ref = value['$ref']
            assert ref.startswith('#/components/schemas/'), ref
            assert ref.split('/')[-1] in components, ref
        for child in value.values():
            validate_refs(child)
    elif isinstance(value, list):
        for child in value:
            validate_refs(child)

validate_refs(api)

invoice = json.loads((ROOT / 'fixtures/demo_invoices.json').read_text(encoding='utf-8'))[0]
q = json.loads((ROOT / 'fixtures/expected_demo_quote.json').read_text(encoding='utf-8'))
assert invoice['amount'] == q['amount_cny']
principal = (Decimal(q['amount_cny']) * Decimal(q['vnd_per_cny'])).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
fee = (principal * Decimal(q['variable_fee_rate_percent']) / Decimal(100)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
total = principal + fee + Decimal(q['fixed_fee_vnd'])
assert str(principal) == q['converted_subtotal_vnd']
assert str(fee) == q['variable_fee_vnd']
assert str(total) == q['total_vnd']
assert all(s['id'] for s in json.loads((ROOT / 'fixtures/payment_scenarios.json').read_text(encoding='utf-8')))
assert 'CREATE TABLE' in (ROOT / 'database/schema.sql').read_text(encoding='utf-8')
assert (ROOT / 'reference/NC_Tham_Quyen_Shenzhen_2026_original.docx').is_file()
assert (ROOT / 'AGENTS.md').is_file()
print('HANDOFF VALID: YAML schema references, source, fixtures, Decimal money calculation, docs present.')
