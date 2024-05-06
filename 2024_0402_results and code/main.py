import pyvisa
import numpy as np
import time
import pandas as pd
import matplotlib.pyplot as plt
from os import mkdir
from os.path import exists


def get_instrument(
    rm,
    cache_file,
    cache_code,
    write_termination= '\n', read_termination='\n'
):
    try:
        with open(cache_file, "r") as f:
            for line in f.readlines():
                code, resource_name = line.strip('\n').split(" ")
                if code == cache_code:
                    instrument = rm.open_resource(resource_name,write_termination= write_termination, read_termination=read_termination)
                    return instrument
            raise FileNotFoundError
    except FileNotFoundError:
        while True:
            try:
                print(f"get instrument for {cache_code}")
                resources_list = rm.list_resources()
                for idx, resource in enumerate(resources_list):  
                    print(f"{idx} : {resource}")
                    
                idx= int(input("input the index of resource to access : "))
                instrument = rm.open_resource(resources_list[idx],write_termination= write_termination, read_termination= read_termination)
                
                with open("cache.txt", "a") as f:
                    f.write(f"{cache_code} {resources_list[idx]}\n")
                break                
            except IndexError:
                continue
        
        return instrument
        
        
rm = pyvisa.ResourceManager()
oscilloscope =  get_instrument(rm, "cache.txt", "Oscilloscope")
signal_analyzer = get_instrument(rm, "cache.txt", "Signal_analyzer")

oscilloscope.write("*IDN?")
print(f"oscilloscope id : {oscilloscope.read()}")
signal_analyzer.write("*IDN?")
print(f"Signal_analyzer id : {signal_analyzer.read()}")


signal_analyzer.write("OUTX 0") #set the output channel to GPIB

signal_analyzer.write("S1AM 1 mVpk") #set to the small value, avoid the overloads
signal_analyzer.write("S1FR 10 kHz") #set the frequency of a source
signal_analyzer.write("STYP 0") #set the source as sine
signal_analyzer.write("SRCO 1") #turn on the source
# time.sleep(0.5)
# Number_of_data = int(signal_analyzer.query("DSPN? 0")) #get number of data
# time.sleep(0.5)

voltages = np.arange(10,10 + 5 * 40, 5)
frequencies = np.arange(1,1 + 1*20,1)

result_dicts = []
oscilloscope.write("SYSTem:AUToscale 1") #Enable AUToset action


if exists("figs") is False:
    mkdir("figs")
    
with pd.ExcelWriter("result.xlsx", mode = 'w') as f:
    for frequency in frequencies:
        for voltage in voltages:
            print(f"set to {voltage} [mV], {frequency} [kHz]")
            time.sleep(0.5)
            signal_analyzer.write(f"S1FR {frequency} kHz")
            signal_analyzer.write(f"S1AM {voltage} mVpk") # set Voltage
            
            oscilloscope.write("AUToset") #Autoset
            time.sleep(0.5)
            
            oscilloscope.write(":WAVeform:SOURce CHANnel1") # set channel to 1
            oscilloscope.write(":WAVeform:MODE NORMal") #Read the data on the screen
            oscilloscope.write(":WAVeform:FORMat ASCii") #Format into csv
            oscilloscope.write(":WAVeform:POINts 1000") #Grab 1000 points, which are maximum number
            oscilloscope.write("WAVeform:DATA?") #Get data
            amplified_data = list(map(lambda x: float(x),oscilloscope.read().split(','))) #Get data from amplified signal
            oscilloscope.write(":WAVeform:XINCrement?")
            amplified_time_increment = float(oscilloscope.read()) #Get time difference between points of amplified data
            
            oscilloscope.write(":WAVeform:SOURce CHANnel2") # set channel to 2
            oscilloscope.write(":WAVeform:MODE NORMal") #Read the data on the screen
            oscilloscope.write(":WAVeform:FORMat ASCii") #Format into csv
            oscilloscope.write(":WAVeform:POINts 1000") #Grab 1000 points, which are maximum number
            oscilloscope.write("WAVeform:DATA?") #Get data
            reference_data = list(map(lambda x: float(x),oscilloscope.read().split(','))) #Get data from reference signal
            oscilloscope.write(":WAVeform:XINCrement?")
            reference_time_increment = float(oscilloscope.read()) #Get time difference between points of reference data
            
            result_dict = {
                'frequency' : frequency,
                'voltage' : voltage,
                'amplified_data' : amplified_data,
                'amplified_time_increment' : amplified_time_increment,
                'reference_data' : reference_data,
                'reference_time_incerment' : reference_time_increment
                }
            result_dicts.append(result_dict) #build a result list

            voltage = result_dict["voltage"]
            frequency = result_dict["frequency"]
            y1 = result_dict["amplified_data"]
            step1 = result_dict["amplified_time_increment"]
            x1 = np.array(range(1000))*step1
            
            y2 = result_dict["reference_data"]
            step2 = result_dict["reference_time_incerment"]
            x2 = np.array(range(1000))*step2
            
            figsize = (32,4)
            fig = plt.figure(figsize = figsize)
            ax = fig.add_subplot(1,1,1)
            
            ax.plot(x1,y1, 'k.')
            ax.plot(x2,y2, 'b.')
            ax.set_xlabel("time [s]")
            ax.set_ylabel("result [V]")
            
            fig.savefig(f"figs/V-t plot sine {voltage} [mV] {frequency} [kHz].png")
            plt.close(fig)
            del fig
            
            df = pd.DataFrame({"result [V]": y1, "result time [s]" : x1, "reference [V]" : y2, "reference time [s]" : x2})
                
            df.to_excel(f, sheet_name = f"{voltage} mV, {frequency} kHz")


