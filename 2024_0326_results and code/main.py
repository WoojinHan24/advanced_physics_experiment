import pyvisa
import numpy as np
import time
import pandas as pd
import matplotlib.pyplot as plt
from os import mkdir
from os.path import exists

rm = pyvisa.ResourceManager()


    
try:
    with open("cache.txt", "r") as f:
        resource_name=f.readline()
        instrument = rm.open_resource(resource_name,write_termination= '\n', read_termination='\n')
except FileNotFoundError:
    while True:
        try:
            input("input the index of resource to access : ")
            resources_list = rm.list_resources()
            for idx, resource in enumerate(resources_list):  
                print(f"{idx} : {resource}")
                
            instrument = rm.open_resource(resources_list[idx],write_termination= '\n', read_termination='\n')
            with open("cache.txt", "w") as f:
                f.write(resources_list[idx])
            break
        except IndexError:
            continue
instrument.write("OUTX 0") #set the output channel to GPIB

instrument.write("S1AM 1 mVpk") #set to the small value, avoid the overloads
instrument.write("S1FR 10 kHz") #set the frequency of a source
instrument.write("STYP 0") #set the source as sine
instrument.write("SRCO 1") #turn on the source
time.sleep(0.5)
Number_of_data = int(instrument.query("DSPN? 0")) #get number of data
time.sleep(0.5)

voltages = range(0,500,10)
result_dicts = []

for voltage in voltages:
    print(f"set voltage to {voltage}")
    time.sleep(0.5)
    instrument.write(f"S1AM {voltage} mVpk") # set Voltage
    time.sleep(1)
    result_y=list(map(lambda x: float(x),instrument.query("DSPY? 0").split(','))) # get result
    
    if len(result_y) != Number_of_data:
        raise ValueError(f"Number of data assertion issue, data stream check required. {len(result_y)} != {Number_of_data}")
    # print(result_y)
    result_x = []

    for idx in range(Number_of_data):
        result_x.append(float(instrument.query(f"DBIN? 0,{idx}"))) # get time data
    
    result_dicts.append({'voltage [mVpk]' : voltage, 'result [V]' : result_y, 'time [s]': result_x})
    # print(result_x)

if exists("figs") is False:
    mkdir("figs")

with pd.ExcelWriter("result.xlsx") as f:
    for result_dict in result_dicts:
        voltage = result_dict["voltage [mVpk]"]
        y = result_dict["result [V]"]
        x = result_dict["time [s]"]
        
        figsize = (8,4)
        fig = plt.figure(figsize = figsize)
        ax = fig.add_subplot(1,1,1)
        
        ax.plot(x,y, 'k.')
        ax.set_xlabel("time [s]")
        ax.set_ylabel("result [V]")
        
        fig.savefig(f"figs/V-t plot sine {voltage}.png")
        
        
        df = pd.DataFrame({"result [V]": y, "time [s]" : x})

        df.to_excel(f, sheet_name = f"{voltage}")

    
# instrument.write("*IDN?")
# print(instrument.read())
# time.sleep(1)
# instrument.write("APHS\n")
# time.sleep(2)
# instrument.write("OUTP? 1.\n")
# results.append(instrument.read())


# with open("result.csv", 'w') as f:
#     for v, result in zip(V, results):
#         f.write(f"{v}, {result}\n")
        

instrument.close()