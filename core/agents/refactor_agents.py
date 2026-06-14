import glob, os

for path in glob.glob('d:/Japan/backend/agents/*.py'):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    old_target = 'state_snapshot = ledger.get_projection("full_state")'
    if old_target in content:
        print('Modifying:', os.path.basename(path))
        new_content = content.replace(old_target, 'state_snapshot = ledger.get_projection("full_state")')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
