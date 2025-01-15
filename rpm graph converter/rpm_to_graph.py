# from scipy.interpolate import UnivariateSpline
from scipy.ndimage import gaussian_filter1d
import matplotlib.pyplot as plt
import numpy as np
import math
import time
import os


encoder_cpr = 2400
screw_pitch_mm = 5.
screw_len_mm = 50
gear_ratio = 6.

M_PI = 3.14159265358979323846



def ticks_to_rot(encoder_ticks):
  return encoder_ticks / encoder_cpr

def rot_to_ticks(rot):
  return rot * encoder_cpr

def motor_rpm_to_ticks(rpm, delta_time):
    rot = rpm / 60 * delta_time
    return rot_to_ticks(rot)

def ticks_to_motor_rpm(ticks, delta_time):
    rot = ticks_to_rot(ticks)
    return rot / delta_time * 60


# -- Motor verileri --
no_load_speed = 5310.0       # rpm (tork=0)
stall_torque = 2420.395      # mNm (rpm=0)
no_load_current = 2.5        # A   (tork=0)
stall_current = 131.227      # A   (tork=stall_torque)
motor_voltage = 12.0

# -- Hesap katsayıları --
motor_reg = no_load_speed / stall_torque  # rpm/mNm
current_slope = (stall_current - no_load_current) / stall_torque  # A/mNm


def get_motor_torque(current):
    """
    Calculates motor torque [Nm] from current [A].
    Based on the linear relationship:
        I = no_load_current + current_slope * torque
    =>  torque = (I - no_load_current) / current_slope
    """
    torque = (current - no_load_current) / current_slope
    return torque


def get_motor_power(current):
    return current * motor_voltage


def get_motor_power_output(rpm, torque_mnm):
    torque_nm = torque_mnm / 1000
    omega_rad_s = 2.0 * math.pi * (rpm / 60.0)
    return torque_nm * omega_rad_s


def get_motor_efficiency(current, rpm, torque_mnm):
    return get_motor_power_output(rpm, torque_mnm) / get_motor_power(current) * 100


# -- Mekanizma hesapları --

# leg parametreleri (bunların güncellenmesi lazım)
leg_l1 = 75
leg_l2 = 30
leg_y = 10
leg_dmax = 40

def calculate_leg_angle(screw_position):
  d1 = leg_dmax - screw_position
  l3 = math.sqrt(pow(d1, 2) + pow(leg_y, 2));

  beta = math.tan(d1/leg_y)
  alpha = math.acos( (pow(leg_l2, 2) + pow(l3, 2) - pow(leg_l1, 2)) / (2 * leg_l2 * l3))
  return M_PI/2 - alpha + beta


def get_screw_pos(ticks):
  return ticks_to_rot(ticks) / gear_ratio * screw_pitch_mm


def get_screw_speed(rpm):
    # return mm/s
    return rpm / 60 * screw_pitch_mm / gear_ratio


def get_screw_force(torque):
    torque_nm = torque / 1000
    screw_torque_Nm = torque_nm * gear_ratio
    pitch_m = screw_pitch_mm * 0.001                     # mm → m
    force_N = (2 * math.pi * screw_torque_Nm) / pitch_m  # F = 2πT / p
    return force_N



# -- Test ve data toplama --

def _read_data(filename):
    try:
        with open(filename, "r") as file:
            data = [float(i) for i in file.read().split("\n") if i != ""]
    except:
        raise Exception(f"Error reading the data: {filename}")
    return data


def read_datas(amps_filename="amps.txt", rpm_filename="rpms.txt"):
    rpms = _read_data(rpm_filename)
    amps = _read_data(amps_filename)

    if len(rpms) != len(amps):
        raise Exception("rpm and amp data length should be the same")
    
    return rpms, amps


def create_and_save_graph(x, y, filename, title="Graph", xlabel="X-axis", ylabel="Y-axis"):
    """
    Verilen x ve y veri dizilerinden bir grafik oluşturur, grafiği
    belirtilen dosya adıyla kaydeder (örn: 'graph.png') ve aynı zamanda
    veri noktalarını bir txt dosyasına yazar (örn: 'graph.txt').
    
    Opsiyonel olarak çizgiyi spline interpolasyonu ile yumuşatır.
    
    Parametreler:
      x            : X ekseni veri dizisi (list, numpy array, vb.)
      y            : Y ekseni veri dizisi (list, numpy array, vb.)
      filename     : Kaydedilecek grafik dosyasının adı (örn: "graph.png").
      title        : Grafik başlığı (varsayılan "Graph")
      xlabel       : X eksen etiketi (varsayılan "X-axis")
      ylabel       : Y eksen etiketi (varsayılan "Y-axis")
    """

    output_folder = "graphs and data"
    os.makedirs(output_folder, exist_ok=True)
    filename = os.path.join(output_folder, filename)

    x = np.array(x.copy())
    y = np.array(y.copy())

    sorted_indices = np.argsort(x)  # x'in sıralı indekslerini alın
    x = x[sorted_indices]           # x sıralı hale getirildi
    y = y[sorted_indices]           # y aynı sıraya göre düzenlendi

    plt.figure()

    # Orijinal veri noktalarını göster
    # plt.plot(x, y, 'o', color='blue', label="Data Points")  # Noktalar (mavi)
    plt.plot(x, y, marker='o', linestyle='-', color='blue', label="Data")

    # Eksen ve başlık
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    plt.legend()
    
    # Grafik kaydetme
    plt.savefig(filename, bbox_inches="tight")
    plt.close()
    print(f"Grafik '{filename}' olarak kaydedildi.")

    # Txt dosyası oluşturma
    base_name, _ = os.path.splitext(filename)
    data_filename = base_name + ".txt"
    with open(data_filename, "w") as file:
        file.write("x\ty\n")
        for xi, yi in zip(x, y):
            file.write(f"{xi}\t{yi}\n")
    print(f"Veri noktaları '{data_filename}' dosyasına yazıldı.")



def main():
    rpms, amps = read_datas()
    powers = [get_motor_power(I) for I in amps]
    torques = [get_motor_torque(I) for I in amps]
    screw_speeds = [get_screw_speed(rpm) for rpm in rpms] 
    screw_forces = [get_screw_force(torque) for torque in torques]

    print("RPM vs Torque")
    print(*zip(rpms, torques), sep="\n")
    create_and_save_graph(torques, rpms, "rpm_vs_torque.png", "RPM vs Torque", "Torque (mNm)", "RPM")

    print("Power vs Torque")
    print(*zip(powers, torques), sep="\n")
    create_and_save_graph(torques, powers, "power_vs_torque.png", "Power vs Torque", "Torque (mNm)", "Power (W)")

    print("Power vs Screw Speed")
    print(*zip(powers, screw_speeds), sep="\n")
    create_and_save_graph(screw_speeds, powers, "power_vs_screw_speed.png", "Power vs Screw Speed", "Screw Speed (mm/s)", "Power (W)")

    print("RPM vs Screw Speed")
    print(*zip(rpms, screw_speeds), sep="\n")
    create_and_save_graph(screw_speeds, rpms, "rpm_vs_screw_speed.png", "RPM vs Screw Speed", "Screw Speed (mm/s)", "RPM")

    print("RPM vs Screw Force")
    print(*zip(rpms, screw_forces), sep="\n")
    create_and_save_graph(screw_forces, rpms, "rpm_vs_screw_force.png", "RPM vs Screw Force", "RPM", "Screw Force (N)")

    print("Torque vs Screw Force")
    print(*zip(torques, screw_forces), sep="\n")
    create_and_save_graph(screw_forces, torques, "torque_vs_screw_force.png", "Torque vs Screw Force", "Torque (mNm)", "Screw Force (N)")

    print("Screw Force vs Screw Speed")
    print(*zip(screw_forces, screw_speeds), sep="\n")
    create_and_save_graph(screw_speeds, screw_forces, "screw_force_vs_screw_speed.png", "Screw Force vs Screw Speed", "Screw Speed (mm/s)", "Screw Force (N)")


if __name__ == "__main__":
    main()