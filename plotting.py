
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from PIL import ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True


def plot_loop_data(split_v_data, split_c_data, file_info, device_path, re_save_graph):
    """ Plot and save data for files with multiple sweeps. """
    # Add your looped data plotting code here
    pass

def plot_single_sweep_data(df, file_info, device_path, re_save_graph):
    """ Plot and save data for files with a single sweep. """
    # Add your single sweep plotting code here
    pass


def create_graph(file_info, save_path, voltage, current, abs_current, slope, loop=False, num_sweeps=0):
    plt.close('all')
    fig = plt.figure(figsize=(12, 8))
    plt.suptitle(f"{file_info['polymer']} - {file_info['sample_name']} - {file_info['section']} - {file_info['device_number']} - {file_info['file_name']}")

    plt.subplot(2, 2, 1)
    plt.title('Iv Graph')
    Plot_types.plot_iv(voltage, current)

    plt.subplot(2, 2, 2)
    plt.title('Log Iv')
    Plot_types.plot_logiv(voltage, abs_current)

    plt.subplot(2, 2, 3)
    plt.title('Iv Avg Showing Direction')
    if loop:
        split_v_data, split_c_data = split_loops(voltage, current, num_sweeps)
        Plot_types.plot_iv_avg(split_v_data[0], split_c_data[0])
    else:
        Plot_types.plot_iv_avg(voltage, current)

    plt.subplot(2, 2, 4)
    plt.title('Current vs Index')
    Plot_types.plot_current_count(current)

    fig.text(0.01, 0.01, f'Gradient between 0-0.1V = {slope}', ha='left', fontsize=8)
    plt.ioff()
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight', dpi=200)
    print(f"File saved successfully at {save_path}")

def multi_graph(df):
    voltage = df['voltage']
    current = df['current']
    abs_current = df['abs_current']
    current_voltage = df['inverse_resistance_ps']
    voltage_half = df['sqrt_Voltage_ps']
    current_density = df['current_Density_ps']

    # Create a 6x10 grid of subplots
    fig = plt.figure(figsize=(12, 10))
    gs = gridspec.GridSpec(6, 10, figure=fig)

    def plot_4x2_top_right(ax):
        ax.plot(np.random.rand(10))
        ax.set_title('4x2 Top Right')

    # Add plots using the imported functions
    ax1 = fig.add_subplot(gs[0:4, 0:4])
    Plot_types.plot_iv(voltage, current)
    ax1.set_title('Iv')

    ax2 = fig.add_subplot(gs[0:4, 4:8])
    Plot_types.plot_logiv(voltage, abs_current)
    ax2.set_title('Log Iv')

    ax3 = fig.add_subplot(gs[0:4, 8:10])
    plot_4x2_top_right(ax3)
    ax3.set_title('Spare')

    ax4 = fig.add_subplot(gs[4:6, 0:2])
    Plot_types.plot_iv_avg(voltage, current, 20)
    ax4.set_title('Iv Avg')

    ax5 = fig.add_subplot(gs[4:6, 2:4])
    Plot_types.sclc_ps(voltage, current_density)
    ax5.set_title('SCLC')

    ax6 = fig.add_subplot(gs[4:6, 4:6])
    Plot_types.poole_frenkel_ps(current_voltage, voltage_half)
    ax6.set_title('Poole-Frenkel')

    ax7 = fig.add_subplot(gs[4:6, 6:8])
    Plot_types.schottky_emission_ps(voltage_half, current)
    ax7.set_title('Schottky')

    ax8 = fig.add_subplot(gs[4:6, 8:10])
    Plot_types.plot_current_count(current)
    ax8.set_title('Current Count')

    plt.tight_layout()
    plt.show()

def main_plot(voltage, current, abs_current, save_loc, re_save, file_info, slope, loop=False, num_sweeps=0):
    # Main function to handle Plots and saving graphs
    short_filename = os.path.splitext(file_info['file_name'])[0]
    save_path = os.path.join(save_loc, f"{short_filename}.png")

    if os.path.exists(save_path) and not re_save:
        return  # Skip saving if the file exists and re_save is False

    create_graph(file_info, save_path, voltage, current, abs_current, slope, loop, num_sweeps)

def plot_filenames_vs_values(filenames, on_values, off_values):
    # Plot filenames vs resistance values
    plt.figure(figsize=(14, 6))
    x = range(len(filenames))
    plt.plot(x, on_values, 'bo-', label='On Values')
    plt.plot(x, off_values, 'ro-', label='Off Values')
    plt.xticks(x, filenames, rotation=90)
    plt.xlabel('Filename')
    plt.ylabel('Resistance Value')
    plt.yscale("log")
    plt.title('Filename vs Resistance Values')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def grid_spec(df, save_loc, file_info):
    short_filename = os.path.splitext(file_info['file_name'])[0]
    save_path = os.path.join(save_loc, f"{short_filename}.png")

    voltage = df['voltage']
    current = df['current']
    voltage_ng = df['voltage_ng']
    abs_current = df['abs_current']
    current_voltage = df['inverse_resistance_ps']
    current_voltage_ng = df['inverse_resistance_ng']
    voltage_half = df['sqrt_Voltage_ps']
    voltage_half_ng = df['sqrt_Voltage_ng']
    current_density = df['current_Density_ps']
    current_density_ng = df['current_Density_ng']
    resistance = df['resistance']

    fontsize = 5
    plt.figure(figsize=(15, 10))

    gs = gridspec.GridSpec(4, 5, wspace=0.3, hspace=0.3)

    # Row 1: IV, Log IV, SCLC
    ax1 = plt.subplot(gs[0:2, 0:2])
    ax1.text(0.05, 0.95, 'Iv', transform=ax1.transAxes, fontsize=8, va='top', ha='left', color="red")
    Plot_types.plot_iv(voltage, current, fontsize)

    ax2 = plt.subplot(gs[0:2, 2:4])
    ax2.text(0.05, 0.95, 'Log Iv', transform=ax2.transAxes, fontsize=8, va='top', ha='left', color="red")
    Plot_types.plot_logiv(voltage, abs_current, fontsize)

    ax3 = plt.subplot(gs[2, 0])
    ax3.text(0.05, 0.95, 'SCLC', transform=ax3.transAxes, fontsize=8, va='top', ha='left', color="red")
    Plot_types.sclc_ps(voltage, current_density, fontsize)

    # Row 2: SCLC (-ve), Schottky (+ve), Schottky (-ve)
    ax4 = plt.subplot(gs[2, 1])
    ax4.text(0.05, 0.95, 'SCLC -ve', transform=ax4.transAxes, fontsize=8, va='top', ha='left', color="red")
    Plot_types.sclc_ng(voltage_ng, current_density_ng, fontsize)

    ax5 = plt.subplot(gs[2, 2])
    ax5.text(0.05, 0.95, 'Schottky', transform=ax5.transAxes, fontsize=8, va='top', ha='left', color="red")
    Plot_types.schottky_emission_ps(voltage_half, current, fontsize)

    ax6 = plt.subplot(gs[2, 3])
    ax6.text(0.05, 0.95, 'Schottky -ve', transform=ax6.transAxes, fontsize=8, va='top', ha='left', color="red")
    Plot_types.schottky_emission_ng(voltage_half_ng, current, fontsize)

    # Row 3: Poole-Frenkel, Current Count, Resistance vs Voltage
    ax7 = plt.subplot(gs[0, 4])
    ax7.text(0.05, 0.95, 'Poole-Frenkel +ve', transform=ax7.transAxes, fontsize=8, va='top', ha='left', color="red")
    Plot_types.poole_frenkel_ps(current_voltage, voltage_half, fontsize)

    ax8 = plt.subplot(gs[1, 4])
    ax8.text(0.05, 0.95, 'Poole-Frenkel -ve', transform=ax8.transAxes, fontsize=8, va='top', ha='left', color="red")
    Plot_types.poole_frenkel_ng(current_voltage_ng, voltage_half_ng, fontsize)

    ax9 = plt.subplot(gs[3, 0:2])
    ax9.text(0.05, 0.95, 'Current Count', transform=ax9.transAxes, fontsize=8, va='top', ha='left', color="red")
    Plot_types.plot_current_count(current, fontsize)

    ax10 = plt.subplot(gs[3, 2:4])
    ax10.text(0.05, 0.95, 'Resistance', transform=ax10.transAxes, fontsize=8, va='top', ha='left', color="red")
    Plot_types.plot_resistance(voltage, resistance, fontsize)

    fig = plt.gcf()
    fig.tight_layout(pad=3.0)
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"File saved successfully at {save_path}")
