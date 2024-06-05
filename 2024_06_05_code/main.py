import pyvisa
import numpy as np
from os import mkdir
import spinapi
from os.path import exists
import json


def get_instrument(
    rm, cache_file, cache_code, write_termination="\n", read_termination="\n"
):
    try:
        with open(cache_file, "r") as f:
            for line in f.readlines():
                code, resource_name = line.strip("\n").split(" ")
                if code == cache_code:
                    instrument = rm.open_resource(
                        resource_name,
                        write_termination=write_termination,
                        read_termination=read_termination,
                    )
                    return instrument
            raise FileNotFoundError
    except FileNotFoundError:
        while True:
            try:
                print(f"get instrument for {cache_code}")
                resources_list = rm.list_resources()
                for idx, resource in enumerate(resources_list):
                    print(f"{idx} : {resource}")

                idx = int(input("input the index of resource to access : "))
                instrument = rm.open_resource(
                    resources_list[idx],
                    write_termination=write_termination,
                    read_termination=read_termination,
                )

                with open("cache.txt", "a") as f:
                    f.write(f"{cache_code} {resources_list[idx]}\n")
                break
            except IndexError:
                continue

        return instrument


rm = pyvisa.ResourceManager()
oscilloscope = get_instrument(rm, "cache.txt", "Oscilloscope")
photon_counter = get_instrument(rm, "cache.txt", "Photon_Counter")
# pulse_blaster = get_instrument(rm, "cache.txt", "Pulse_Blaster")
signal_generator = get_instrument(rm, "cache.txt", "Signal_Generator")


oscilloscope.write("*IDN?")
print(f"oscilloscope id : {oscilloscope.read()}")
photon_counter.write("*IDN?")
print(f"photon_counter id : {photon_counter.read()}")
# pulse_blaster.write("*IDN?")
# print(f"pulse_blaster id : {pulse_blaster.read()}")
spinapi.pb_start()
spinapi.pb_init()
spinapi.pb_set_freq(500000000)
PULSE_PROGRAM = 0
ms = 0.001
spinapi.pb_start_programming(PULSE_PROGRAM)
LOOP = 2
start = spinapi.pb_inst_pbonly(0x1, LOOP, 50, 250.0 * ms)
CONTINUE = 0
spinapi.pb_inst_pbonly(0x3, CONTINUE, 0, 250.0 * ms)
spinapi.pb_inst_pbonly(0x2, CONTINUE, 0, 250.0 * ms)
END_LOOP = 3
spinapi.pb_inst_pbonly(0x0, END_LOOP, start, 250.0 * ms)
STOP = 1
spinapi.pb_inst_pbonly(0x0, STOP, 0, 1.0 * ms)
spinapi.pb_stop_programming()
spinapi.pb_stop()

signal_generator.write("*IDN?")
print(f"signal_generator id : {signal_generator.read()}")
signal_generator.write(
    f"TYPE 7; PFNC 5; MODL 0; ENBR 0; ENBL 0; AMPL 0; AMPR 0;"
)  # preset signal generator

parameters = [(1)]
data = []
repetition = 100
T = 5e-6
t = 3e-7
d = 3e-7


for parameter in parameters:
    duty_factor = 10  # 10% of duty)factor
    frequency = 2875  # 2875 MHz of microwave frequency
    amplitude = 0  # 0dBm of the signal generator

    if amplitude > 0.5 or False:
        continue
    # set photon counter gate
    photon_counter.write("CM 0")
    # set photon counter count mode to 0, i.e. A,B both counting mode

    photon_counter.write("CP 2 , 1E0")
    photon_counter.write(f"NP {repetition}")
    photon_counter.write(f"DT {T-2*t-d}")
    photon_counter.write("GM 0, 1")
    photon_counter.write("GM 1, 1")
    photon_counter.write(f"GD 0, {t}")
    photon_counter.write(f"GD 1, {T-t-d}")
    photon_counter.write(f"GW 0, {d}")
    photon_counter.write(f"GW 1, {d}")
    photon_counter.write("DS 0 0")
    photon_counter.write("DS 1 0")
    photon_counter.write("DL 0 0.15")
    photon_counter.write("DL 1 0.15")

    # set pulse blaster
    spinapi.pb_start()

    # set signal_generator
    signal_generator.write("PFNC 3")  # Pulse modulation function square set
    signal_generator.write(f"PDTY {duty_factor}")  # set duty factor of the wave
    signal_generator.write(f"FREQ {frequency} MHz")  # set freguency of the microwave
    signal_generator.write(f"AMPL {amplitude}")  # set the amplitude

    data.append(1)

    spinapi.pb_stop()


with open("data.json", "w") as json_file:
    json.dump(data, json_file, indent=4)
