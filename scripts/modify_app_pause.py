import sys

fn = r"d:\Games\Mystery-Dungeon\game\app.py"
with open(fn, 'r', encoding='utf-8') as f:
    data = f.read()

# Pass on_debug=self._input_debug to PauseMenu
if 'on_debug=self._input_debug' not in data:
    data = data.replace(
        'on_quit=self._on_pause_quit,',
        'on_quit=self._on_pause_quit,\n            on_debug=self._input_debug,'
    )

with open(fn, 'w', encoding='utf-8', newline='\n') as f:
    f.write(data)

print("PauseMenu modification successful!")
