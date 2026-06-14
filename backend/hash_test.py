import json
import hashlib
from core.ledger.execution_artifact_manager import CANONICAL_SERIALIZE

line = '''{"event_id": 0, "timestamp": "2026-06-14T17:11:58.290244", "payload": "{\\"artifact\\": \\"issue\\", \\"data\\": {\\"description\\": \\"Desc\\", \\"issue_id\\": \\"ISSUE-123\\", \\"repo_path\\": \\"dummy_repo\\", \\"title\\": \\"Title\\"}}", "previous_hash": "d68f4eb0505b5fa393b31405cdb7925ceaae56480bd8548d710b941e27f63dc1", "current_hash": "dc9bf35c00b2e7a1b581f66334696400cf40643f3540106fda1d6f0c76f92b6a"}'''

env = json.loads(line)
payload_dict = env.get('payload')
last_hash = env.get('previous_hash')

canonical_bytes = CANONICAL_SERIALIZE(payload_dict, 'run_id')
expected_curr = hashlib.sha256(canonical_bytes + last_hash.encode('utf-8')).hexdigest()

print('Expected:', expected_curr)
print('Actual:  ', env.get('current_hash'))
print('Matches?', expected_curr == env.get('current_hash'))
