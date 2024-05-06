import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from os import mkdir
from os.path import exists
import scipy.optimize as opt

def get_regression_result(
    x,y,fitting_function, p0, maxfev = 100000
):
    param, param_covariance=opt.curve_fit(
        fitting_function,
        x,
        y,
        p0,
        maxfev= maxfev
    )

    return param,param_covariance

def phys_plot(
    x_list,
    y_list,
    x_label,
    y_label,
    error_x = None,
    error_y = None,
    fitting_function = None,
    p0 = None,
    figsize = (8,8)
):
    figsize = (8,8)
    fig = plt.figure(figsize = figsize)
    ax = fig.add_subplot(1,1,1)
    
    ax.plot(x_list,y_list, 'k.')
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    
    x_list = np.array(x_list)
    y_list = np.array(y_list)
    
            
    if fitting_function is not None:
        param,param_cov = get_regression_result(x_list,y_list,fitting_function,p0)
        x_continuous = np.linspace(min(x_list),max(x_list),500)
        residuals = y_list - fitting_function(x_list,*param)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y_list-np.mean(y_list))**2)
        R_square= 1-ss_res/ss_tot

    if error_y is not None:
        ax.errorbar(x_list,y_list,fmt='k.',xerr = error_x,yerr = error_y)
    if fitting_function is not None:
        ax.plot(x_continuous,fitting_function(x_continuous,*param),'r-')
            

    fig.tight_layout()
    if fitting_function is not None:
        return fig, (param, param_cov, R_square)
    return fig


voltages = np.arange(10,10 + 5 * 40, 5)
frequencies = np.arange(1,1 + 1*20,1)

folders = ["100kOhm", "100MOhm"]

gains = [1e5, 1e8]
flag = 0


with open("figs//fitting_param.txt", 'w') as f:
    f.write("label, R [Ohm], intercept(V-I), R^2,\n")

if exists("figs") is False:
    mkdir("figs")

for folder,gain in zip(folders,gains):
    file_name = folder + "//result.xlsx"
    for frequency in frequencies:
        print(f"plotting {frequency} [kHz]")
        result_I = []
        result_V = []
        result_phi = []
        for voltage in voltages:
            print(f"calculating at {voltage} [mV]")
            sheet_name = f"{voltage} mV, {frequency} kHz"
            df = pd.read_excel(file_name, sheet_name = sheet_name)
            amplified_data = df['result [V]'].to_numpy()
            amplified_time = df['result time [s]'].to_numpy()
            reference_data = df['reference [V]'].to_numpy()
            reference_time = df['reference time [s]'].to_numpy()
            
            dt = amplified_time[1]-amplified_time[0]
            integral = 0
            for v1, t1, v2,t2 in zip(amplified_data, amplified_time, reference_data, reference_time):
                if t1 != t2:
                    print(t1,t2)
                    raise ValueError("time assertion broken")
                integral += v1*v2 *dt
            
            T = amplified_time[-1] - amplified_time[0]
            Vcosphi = integral*2/T/(voltage*1e-3)
            
            shift_index = int(1/(frequency*1000)/dt/2)
            
            shifted_integral = 0
            for v1,t1,v2,t2 in zip(amplified_data[:-shift_index],amplified_time[:-shift_index],reference_data[shift_index:], reference_time[shift_index:]):
                shifted_integral += v1*v2*dt
            
            shifted_T = amplified_time[-shift_index]-amplified_time[0]
            Vsinphi = shifted_integral*2/shifted_T/(voltage*1e-3)
            
            V_amplified = np.sqrt(Vcosphi**2 + Vsinphi**2)
            phi = np.arctan(Vsinphi/Vcosphi)
            
            I = V_amplified/gain
            result_I.append(I)
            result_V.append(voltage*1e-3)
            result_phi.append(phi)
        
        raw_fig = phys_plot(
            result_I,
            result_V,
            "lock in current [A]",
            "Source voltage [V]"
        )
        raw_fig.savefig(f"figs/V-I raw figure at {frequency}[kHz], {folder}.png")
        plt.close(raw_fig)
        
        phi_raw_fig = phys_plot(
            result_V,
            result_phi,
            "Source voltage [V]",
            "phase shift [rad]"
        )
        phi_raw_fig.savefig(f"figs/phi-V raw figure at {frequency}[kHz], {folder}.png")
        plt.close(phi_raw_fig)
        
        fitted_fig, (param, param_cov, R_square)= phys_plot(
            result_I,
            result_V,
            "lock in current [A]",
            "Source voltage [V]",
            None,
            None,
            lambda x,a,b : a*x+b,
            [0,0],
        )
        fitted_fig.savefig(f"figs/V-I fitted plot at {frequency}[kHz], {folder}.png")
        plt.close(fitted_fig)
        
        param_string = f"{frequency} [kHz] {folder}, {param[0]} \\pm {np.sqrt(param_cov[0][0])}, {param[1]} \\pm {np.sqrt(param_cov[1][1])}, {R_square},\n"
        with open("figs//fitting_param.txt", 'a') as f:
            f.write(param_string)
