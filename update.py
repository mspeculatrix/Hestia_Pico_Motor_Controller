import hashlib
import json
import pathlib

FILES: list[str] = [
	'config.py',
	'hestia.py',
	'ws_server.py',
	'sensors.py',
	'L298_motor_controller.py',
	'ota.py',
	'ssd1306.py',
]
manifest: dict[str, str] = {
	f: hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()
	for f in FILES
	if pathlib.Path(f).exists()
}
pathlib.Path('manifest.json').write_text(json.dumps(manifest, indent=2))  # pyright: ignore[reportCallIssue]
print('Generated manifest.json:', manifest)
