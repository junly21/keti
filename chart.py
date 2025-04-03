import sys
import os
import subprocess
import csv
from datetime import datetime
import xml.etree.ElementTree as ET
import traci

# 경로 설정
dirname = os.path.dirname
SITE_ROOT = os.path.realpath(dirname(__file__))
SUMO_ROOT = os.path.join(SITE_ROOT, 'sumo-1.19.0')
DATA_ROOT = os.path.join(SITE_ROOT, 'data')
TEMP_ROOT = os.path.join(SITE_ROOT, 'temp')

sumo_bin_path = os.path.join(SUMO_ROOT, 'bin')
sumo_tools_path = os.path.join(SUMO_ROOT, 'tools')
sumo_path = os.path.join(sumo_bin_path, 'sumo')
od2trips_path = os.path.join(sumo_bin_path, 'od2trips')
duarouter_path = os.path.join(sumo_bin_path, 'duarouter')

sys.path.append(sumo_tools_path)

network_file = 'Deajeon_V6.net.xml'
taz_file = 'Deajeon_V6.taz.xml'
od_file = 'Deajeon_v6_2.od'

network_path = os.path.join(DATA_ROOT, network_file)
taz_path = os.path.join(DATA_ROOT, taz_file)
od_path = os.path.join(DATA_ROOT, od_file)

sim_begin = 0
sim_end = 120

timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
odtrips_file = os.path.join(TEMP_ROOT, timestamp + ".odtrips.xml")
rou_file = os.path.join(TEMP_ROOT, timestamp + ".rou.xml")

# 1. 파일 생성
print("Running od2trips...")
subprocess.run([od2trips_path, "-n", taz_path, "-d", od_path, "-o", odtrips_file])
print("Running duarouter...")
subprocess.run([duarouter_path, "-n", network_path, "-r", odtrips_file, "-o", rou_file])

# 2. SUMO 시뮬레이션 실행
cmd = [sumo_path, "-n", network_path, "-r", rou_file, "-b", str(sim_begin), "-e", str(sim_end)]
print("Starting SUMO simulation for macro data generation...")
traci.start(cmd)

macro_data = []

while True:
    current_time = traci.simulation.getTime()
    if current_time > sim_end:
        break

    vehicle_ids = traci.vehicle.getIDList()
    num_vehicles = len(vehicle_ids)
    total_speed = 0.0
    total_acceleration = 0.0
    total_depart_delay = 0.0
    total_travel_time = 0.0

    for vid in vehicle_ids:
        speed = traci.vehicle.getSpeed(vid)
        acceleration = traci.vehicle.getAcceleration(vid)
        depart_delay = traci.vehicle.getDepartDelay(vid)
        departure = traci.vehicle.getDeparture(vid)
        travel_time = current_time - departure

        total_speed += speed
        total_acceleration += acceleration
        total_depart_delay += depart_delay
        total_travel_time += travel_time

    if num_vehicles > 0:
        avg_speed = total_speed / num_vehicles
        avg_acceleration = total_acceleration / num_vehicles
        avg_depart_delay = total_depart_delay / num_vehicles
        avg_travel_time = total_travel_time / num_vehicles
    else:
        avg_speed = 0
        avg_acceleration = 0
        avg_depart_delay = 0
        avg_travel_time = 0

    macro_data.append({
        'Time': current_time,
        'AverageSpeed': avg_speed,
        'AverageAcceleration': avg_acceleration,
        'AverageTravelTime': avg_travel_time,
        'AverageDepartDelay': avg_depart_delay
    })

    traci.simulationStep()

traci.close()
print("Simulation ended.")

# 3. CSV 파일로 저장
output_csv = os.path.join(TEMP_ROOT, timestamp + "_macro.csv")
with open(output_csv, 'w', newline='') as csvfile:
    fieldnames = ['Time', 'AverageSpeed', 'AverageAcceleration', 'AverageTravelTime', 'AverageDepartDelay']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in macro_data:
        writer.writerow(row)

print(f"Macro data written to {output_csv}")
