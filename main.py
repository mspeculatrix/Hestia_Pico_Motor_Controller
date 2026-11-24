"""
Bootstrap program.

Makes the wifi connection (which is passed on to other modules) and runs a
check to see if Over The Air (OTA) updates are available for any of the program
files (except this one). Then hands control to hestia.py.
"""

import gc
import sys
import time

import machine
import network

from config import LED, Config


def run_ota_boot() -> None:
	"""
	Make wifi connection and check for OTA updates.
	"""
	wlan = network.WLAN(network.STA_IF)
	try:
		# Certain routines in oita.py will raise exceptions if the OTA update
		# process fails in awkward ways.

		# network.country('FR')
		# Clear any lingering CYW43 / lwIP state from a previous soft-reset
		if wlan.active():
			wlan.disconnect()
			wlan.active(False)
			time.sleep_ms(300)

		wlan.active(True)
		time.sleep_ms(500)

		tries: int = 0
		print('OTA:CONNECTING')
		while not wlan.isconnected() and tries < Config.MAX_CONN_TRIES:
			tries += 1
			LED.on()
			wlan.connect(Config.WIFI_SSID, Config.WIFI_PASS)
			# Wait for up to a certain period (set by Config.WIFI_CONN_WAIT)
			# for wifi to connect
			timeout: int = Config.WIFI_CONN_WAIT
			while timeout > 0 and wlan.status() not in (
				# If we're not connected and haven't failed in some way, wait
				# for a second before next try.
				network.STAT_GOT_IP,
				network.STAT_CONNECT_FAIL,
				network.STAT_NO_AP_FOUND,
				network.STAT_WRONG_PASSWORD,
			):
				LED.off()
				time.sleep(1)
				timeout -= 1
				LED.on()
			LED.off()

		if wlan.isconnected():
			print('OTA:CONNECTED')
			Config.wlan = wlan  # Hand off active interface to Config
			import ota

			if ota.check_and_update():
				print('OTA:UPDATED_REBOOTING')
				time.sleep_ms(200)
				machine.reset()
			print('OTA:FIRMWARE_OK')
			Config.ota_status = 'OK'
		else:  # if offline, skip OTA and boot normally
			print(f'OTA:WARNING:UPDATE_SKIPPED:WIFI_STATUS_{wlan.status()}')
			Config.ota_status = 'SKIPPED'

	except Exception as e:
		print(f'OTA:ERR:UPDATE_CHECK_FAILED:{e}')
		Config.ota_status = 'FAILED'
		# Keep wlan attached if it is still connected so hestia.py can use it
		if wlan.isconnected():
			Config.wlan = wlan
	finally:
		# Unload modules no longer needed to save memory
		for mod in ('ota', 'urequests', 'requests'):
			sys.modules.pop(mod, None)
		gc.collect()


run_ota_boot()


# Hand over control to the main application (runs asyncio.run() on import)
import app  # noqa: E402, F401
