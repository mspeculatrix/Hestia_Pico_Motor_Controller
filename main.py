import gc
import time

import machine
import network

from config import LED, Config


def run_ota_boot() -> None:
	wlan = network.WLAN(network.STA_IF)
	try:
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
			# Wait up to 15s for wifi
			timeout = 15
			while timeout > 0 and wlan.status() not in (
				network.STAT_GOT_IP,
				-1,
				-2,
				-3,
			):
				LED.off()
				time.sleep(1)
				timeout -= 1
				LED.on()
			LED.off()

		if wlan.isconnected():
			print('OTA:CONNECTED')
			Config.wlan = wlan  # Hand off active interface
			import ota

			if ota.check_and_update():
				print('OTA:UPDATED_REBOOTING')
				time.sleep_ms(200)
				machine.reset()
			print('OTA:FIRMWARE_OK')
			Config.ota_status = 'OK'
		else:  # if offline, skip OTA and boot normally
			print(f'OTA:WARNING:UPDATE_SKIPPED:WIFI_STATUS_{wlan.status()}')

	except Exception as e:
		print(f'OTA:ERR:UPDATE_CHECK_FAILED:{e}')
		Config.ota_status = 'FAILED'
		# Keep wlan attached if it is still connected so hestia.py can use it
		if wlan.isconnected():
			Config.wlan = wlan
	finally:
		# Cleanly tear down radio so hestia.py starts from a known state
		# try:
		# 	wlan.disconnect()
		# 	wlan.active(False)
		# 	time.sleep_ms(500)
		# except Exception as e:
		# 	print(f'OTA:ERR:DISCONNECT_ISSUE:{e}')
		gc.collect()


run_ota_boot()


# Hand over control to the main application (runs asyncio.run() on import)
import hestia  # noqa: E402, F401
