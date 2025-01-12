import math
import time

encoder_cpr = 2400
screw_pitch_mm = 5.
screw_len_mm = 50
gear_ratio = 6.

# simülasyon döngü süresi (ms)
update_interval_ms = 1000
# simülasyonun gerçek hayattan kaç kat hızlı çalışacağı
loop_time_multiplier = 1

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
    return (current - no_load_current) / current_slope


def get_motor_rpm(current):
    """
    Calculates motor speed [rpm] from current [A].
    First find the torque from the current,
    then apply the linear RPM-Torque equation:
        rpm = no_load_speed - motor_reg * torque
    """
    torque = get_motor_torque(current)
    rpm = no_load_speed - motor_reg * torque
    return rpm


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

    if -30 > motor_current_g or motor_current_g > 30 :
        raise ValueError("Motor current out of range")


def update_motor(delta_time):
    # bu tamamen simülasyona özel bir fonksiyon
    global motor_current_g
    global encoder_reading_g

    rpm = get_motor_rpm(motor_current_g)
    encoder_reading_g += motor_rpm_to_ticks(rpm, delta_time)

# -- Motor Son --



# -- Leg kısmı --

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


def get_screw_displacement(ticks):
  return ticks_to_rot(ticks) / gear_ratio * screw_pitch_mm


def main():
    last_time = time.time()
    while True:
        # interval dolana kadar bekle
        elapsed = time.time() - last_time
        while elapsed * 1000 < update_interval_ms:
            elapsed = time.time() - last_time

        sim_elapsed = (time.time() - last_time) * loop_time_multiplier
        last_time = time.time()
        # interval işleri son

        set_motor_current(30)
        update_motor(sim_elapsed)
        
        dt = sim_elapsed
        encr = encoder_reading_g
        current = get_motor_current()
        rpm = get_motor_rpm(current)
        torque = get_motor_torque(current)
        eff = get_motor_efficiency(current)

        print(f" ------------------- ")
        print(f"Encoder: {encr}, ")
        print(f"Screw: {get_screw_displacement(encr)}, ")

        print(f"Current: {current}, ")
        print(f"Motor RPM: {rpm}, ")
        print(f"Motor Torque: {torque}, ")
        print(f"Input: {get_motor_power(current)}, ")
        print(f"Output: {get_motor_power_output(current)}, ")
        print(f"Efficiency: {eff}, ")




if __name__ == "__main__":
   main()
