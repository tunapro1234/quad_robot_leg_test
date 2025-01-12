import numpy as np
import matplotlib.pyplot as plt
import math
import time
import os


encoder_cpr = 2400
screw_pitch_mm = 5.
screw_len_mm = 50
gear_ratio = 6.

# simülasyon döngü süresi (ms)
update_interval_ms_g = 1000
# simülasyonun gerçek hayattan kaç kat hızlı çalışacağı
loop_time_multiplier_g = 1

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
motor_current_g = 0
encoder_reading_g = 0

no_load_speed = 5310.0       # rpm (tork=0)
stall_torque = 2420.395      # mNm (rpm=0)
no_load_current = 2.5        # A   (tork=0)
stall_current = 131.227      # A   (tork=stall_torque)
motor_voltage = 12.0

# -- Hesap katsayıları --
motor_reg = no_load_speed / stall_torque  # rpm/mNm
current_slope = (stall_current - no_load_current) / stall_torque  # A/mNm


def get_motor_current():
    return motor_current_g


def get_motor_torque(current):
    """
    Calculates motor torque [mNm] from current [A].
    Based on the linear relationship:
        I = no_load_current + current_slope * torque
    =>  torque = (I - no_load_current) / current_slope
    """
    torque = (current - no_load_current) / current_slope
    return apply_jitter(torque, 0.1)


def get_motor_rpm(current):
    """
    Calculates motor speed [rpm] from current [A].
    First find the torque from the current,
    then apply the linear RPM-Torque equation:
        rpm = no_load_speed - motor_reg * torque
    """
    torque = get_motor_torque(current)
    rpm = no_load_speed - motor_reg * torque
    return apply_jitter(rpm, 0.1)


def get_motor_power(current):
    return current * motor_voltage


def get_motor_power_dt(current, delta_time):
    power_watts = get_motor_power(current)
    energy_joules = power_watts * delta_time
    return energy_joules


def get_motor_power_output(current):
    torque_nm = get_motor_torque(current)
    rpm = get_motor_rpm(current)
    omega_rad_s = 2.0 * math.pi * (rpm / 60.0)
    return torque_nm * omega_rad_s / 1000


def get_motor_power_output_dt(current, delta_time):
    power_watts = get_motor_power_output(current)
    energy_joules = power_watts * delta_time
    return energy_joules


def get_motor_efficiency(current):
    return get_motor_power_output(current) / get_motor_power(current) * 100


def set_motor_current(current):
    global motor_current_g
    motor_current_g = current

    if -40 > motor_current_g or motor_current_g > 40:
        raise ValueError("Motor current out of range")


def update_motor(delta_time):
    # bu tamamen simülasyona özel bir fonksiyon
    global motor_current_g
    global encoder_reading_g

    rpm = get_motor_rpm(motor_current_g)
    encoder_reading_g += motor_rpm_to_ticks(rpm, delta_time)

# -- Motor Son --



# -- Mekanizma hesapları --

# leg parametreleri
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
    return rpm / 60 * screw_pitch_mm / gear_ratio


def get_screw_force(torque):
    screw_torque_mNm = torque * gear_ratio
    screw_torque_Nm = screw_torque_mNm * 0.001           # mNm → N·m
    pitch_m = screw_pitch_mm * 0.001                     # mm → m
    force_N = (2 * math.pi * screw_torque_Nm) / pitch_m  # F = 2πT / p
    return force_N



# -- Test ve data toplama --

def create_and_save_graph(x, y, filename, title="Graph", xlabel="X-axis", ylabel="Y-axis"):
    """
    Verilen x ve y veri dizilerinden bir grafik oluşturur, grafiği
    belirtilen dosya adıyla kaydeder (örn: 'graph.png') ve aynı zamanda
    veri noktalarını bir txt dosyasına yazar (örn: 'graph.txt').
    
    Parametreler:
      x        : X ekseni veri dizisi (list, numpy array, vb.)
      y        : Y ekseni veri dizisi (list, numpy array, vb.)
      filename : Kaydedilecek grafik dosyasının adı (örn. "graph.png").
      title    : Grafik başlığı (varsayılan "Graph")
      xlabel   : X eksen etiketi (varsayılan "X-axis")
      ylabel   : Y eksen etiketi (varsayılan "Y-axis")
    """
    # Grafik oluşturma ve kaydetme
    plt.figure()
    plt.plot(x, y, marker='o', linestyle='-', color='blue', label="Data")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    plt.legend()
    
    plt.savefig(filename, bbox_inches="tight")
    plt.close()
    print(f"Grafik '{filename}' olarak kaydedildi.")

    # Dosya ismini bölerek .txt uzantılı dosya adı oluşturma
    base_name, _ = os.path.splitext(filename)
    data_filename = base_name + ".txt"
    
    # Veri noktalarını txt dosyasına yazma
    with open(data_filename, "w") as file:
        file.write("x\ty\n")  # Başlık satırı
        for xi, yi in zip(x, y):
            file.write(f"{xi}\t{yi}\n")
    print(f"Veri noktaları '{data_filename}' dosyasına yazıldı.")


def main_test(update_interval_ms, loop_time_multiplier):
    last_time = time.time()
    while True:
        # interval dolana kadar bekle
        elapsed = time.time() - last_time
        while elapsed * 1000 < update_interval_ms:
            elapsed = time.time() - last_time

        sim_elapsed = (time.time() - last_time) * loop_time_multiplier
        last_time = time.time()
        # interval işleri son

        ### MERT BURAYA BAK MOTORA BURDAN AKIM VREİYOSUN, 
        ### 40 AMPERDEN FAZLA VERİRSEN MOTORUN KALBİNİ KIRARSIN
        set_motor_current(30)
        update_motor(sim_elapsed)
        
        # dt = sim_elapsed
        encr = encoder_reading_g
        current = get_motor_current()
        rpm = get_motor_rpm(current)
        torque = get_motor_torque(current)
        eff = get_motor_efficiency(current)

        screw_pos = get_screw_pos(encr)
        screw_speed = get_screw_speed(rpm)
        
        print(f" ------------------- ")
        print(f"Encoder: {encr}, ")
        print(f"Screw: {screw_pos}, ")
        print(f"Screw speed: {screw_speed}, ")

        print(f"Current: {current}, ")
        print(f"Motor RPM: {rpm}, ")
        print(f"Motor Torque: {torque}, ")
        print(f"Input: {get_motor_power(current)}, ")
        print(f"Output: {get_motor_power_output(current)}, ")
        print(f"Efficiency: {eff}, ")


def apply_jitter(value, percent):
    """
    Verilen value sayısını, ± percent aralığında rastgele oynar.
    
    Örnek: value = 100, percent = 0.1 ise, değer 90 ile 110 arasında bir
    değere rastgele ayarlanır.
    
    Parametreler:
      value   : Orijinal sayı
      percent : Maksimum oynama oranı (örn. %10 için 0.1)
    
    Return:
      Rastgele oynanmış değer.
    """
    # -percent ile +percent arasında rastgele bir oran belirlenir.
    delta = np.random.uniform(-percent, percent)
    return value * (1 + delta)


def collect_data(update_interval_ms, loop_time_multiplier, current_step_per_sec):
    total_power_consumption = 0
    powers = []
    torques = []
    power_consumptions = []
    times = []
    rpms = []

    # başlangıç akımımız 3 amper
    set_motor_current(3)

    last_time = time.time()
    while motor_current_g < 40:
        # interval dolana kadar bekle
        elapsed = time.time() - last_time
        while elapsed * 1000 < update_interval_ms:
            elapsed = time.time() - last_time

        sim_elapsed = (time.time() - last_time) * loop_time_multiplier
        last_time = time.time()
        # interval işleri son

        # akımı zamanla arttır
        try:
            set_motor_current(motor_current_g + apply_jitter(current_step_per_sec*sim_elapsed, 0.5))
        except ValueError:
            break
        update_motor(sim_elapsed)

        powers.append(get_motor_power(motor_current_g))
        torques.append(get_motor_torque(motor_current_g))
        rpms.append(get_motor_rpm(motor_current_g))

        times.append(sim_elapsed)
        total_power_consumption += powers[-1] * sim_elapsed
        power_consumptions.append(total_power_consumption)

    return powers, torques, rpms, times, power_consumptions


def main():
    powers, torques, rpms, _, power_consumptions = collect_data(10, 10, 10)
    print("Power vs Torque")
    print(*zip(powers, torques), sep="\n")
    create_and_save_graph(torques, powers, "power_vs_torque.png", "Power vs Torque", "Torque (mNm)", "Power (W)")

    print("Power Cons vs Torque")
    print(*zip(power_consumptions, torques), sep="\n")
    create_and_save_graph(torques, power_consumptions, "power_cons_vs_torque.png", "Power Consumption vs Torque", "Torque (mNm)", "Power Consumption (J)")

    print("Power Cons vs Screw Speed")
    screw_speeds = [get_screw_speed(rpm) for rpm in rpms] 
    print(*zip(power_consumptions, screw_speeds), sep="\n")
    create_and_save_graph(screw_speeds, power_consumptions, "power_cons_vs_screw_speed.png", "Power Consumption vs Screw Speed", "Screw Speed (mm/s)", "Power Consumption (J)")

    print("Screw Force vs Screw Speed")
    screw_forces = [get_screw_force(torque) for torque in torques]
    print(*zip(screw_forces, screw_speeds), sep="\n")
    create_and_save_graph(screw_speeds, screw_forces, "screw_force_vs_screw_speed.png", "Screw Force vs Screw Speed", "Screw Speed (mm/s)", "Screw Force (N)")



if __name__ == "__main__":
#    main_test(10, 10, 10)
#    power_vs_torque(10, 10, 10)
    main()