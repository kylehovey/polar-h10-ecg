import asyncio
import math
import signal
import sys
import time

import numpy as np
from bleak import BleakClient
from bleak.uuids import uuid16_dict

""" Predefined UUID (Universal Unique Identifier) mapping are based on Heart Rate GATT service Protocol that most
Fitness/Heart Rate device manufacturer follow (Polar H10 in this case) to obtain a specific response input from
the device acting as an API """

uuid16_dict = {v: k for k, v in uuid16_dict.items()}

## This is the device MAC ID, please update with your device ID
ADDRESS = str(np.load("./address.npy"))

## UUID for model number ##
MODEL_NBR_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
    uuid16_dict.get("Model Number String")
)

## UUID for manufacturer name ##
MANUFACTURER_NAME_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
    uuid16_dict.get("Manufacturer Name String")
)

## UUID for battery level ##
BATTERY_LEVEL_UUID = "0000{0:x}-0000-1000-8000-00805f9b34fb".format(
    uuid16_dict.get("Battery Level")
)

## UUID for Request of ECG Stream ##
ECG_WRITE = bytearray([0x02, 0x00, 0x00, 0x01, 0x82, 0x00, 0x01, 0x01, 0x0E, 0x00])

PMD_SERVICE = "FB005C80-02E7-F387-1CAD-8ACD2D8DF0C8" ## UUID for connection establsihment with device ##
PMD_CONTROL = "FB005C81-02E7-F387-1CAD-8ACD2D8DF0C8" ## UUID for Request of stream settings ##
PMD_DATA = "FB005C82-02E7-F387-1CAD-8ACD2D8DF0C8" ## UUID for Request of start stream ##
ECG_SAMPLING_FREQ = 130 ## For Plolar H10  sampling frequency ##

ecg_session_data = []
ecg_session_time = []

## Keyboard Interrupt Handler
def keyboardInterrupt_handler(signum, frame):
    print("  key board interrupt received...")
    print("----------------Recording stopped------------------------")

def data_conv(sender, data):
    print("Data recieved")
    if data[0] == 0x00:
        timestamp = convert_to_unsigned_long(data, 1, 8)
        step = 3
        samples = data[10:]
        offset = 0
        while offset < len(samples):
            ecg = convert_array_to_signed_int(samples, offset, step)
            offset += step
            ecg_session_data.extend([ecg])
            ecg_session_time.extend([timestamp])

def convert_array_to_signed_int(data, offset, length):
    return int.from_bytes(
        bytearray(data[offset : offset + length]), byteorder="little", signed=True,
    )

def convert_to_unsigned_long(data, offset, length):
    return int.from_bytes(
        bytearray(data[offset : offset + length]), byteorder="little", signed=False,
    )

## Aynchronous task to start the data stream for ECG ##
async def run(client, debug=False):
    await client.is_connected()
    print("---------Device connected--------------")

    model_number = await client.read_gatt_char(MODEL_NBR_UUID)
    manufacturer_name = await client.read_gatt_char(MANUFACTURER_NAME_UUID)
    battery_level = await client.read_gatt_char(BATTERY_LEVEL_UUID)

    print("Model Number: {0}".format("".join(map(chr, model_number))))
    print("Manufacturer Name: {0}".format("".join(map(chr, manufacturer_name))))
    print("Battery Level: {0}%".format(int(battery_level[0])))

    await client.write_gatt_char(PMD_CONTROL, ECG_WRITE)
    await client.start_notify(PMD_DATA, data_conv)

    n = ECG_SAMPLING_FREQ
    i = 0

    while i < 10:
        ## Collecting ECG data for 1 second
        await asyncio.sleep(1)
        n = n + 130
        i += 1

    np.save("H10_ecg_time", ecg_session_time)
    np.save("H10_ecg_data", ecg_session_data)

    print("Stopping ECG data...")
    await client.stop_notify(PMD_DATA)
    print("[CLOSED] application closed.")

    sys.exit(0)

async def main():
    async with BleakClient(ADDRESS) as client:
        signal.signal(signal.SIGINT, keyboardInterrupt_handler)
        tasks = [asyncio.ensure_future(run(client, True))]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
