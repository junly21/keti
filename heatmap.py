import sys
import os
import subprocess
import csv
from datetime import datetime
import xml.etree.ElementTree as ET
import traci

# Pytraci import 및 경로 설정
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

# 1. 경로 파일 생성
print("Running od2trips...")
subprocess.run([od2trips_path, "-n", taz_path, "-d", od_path, "-o", odtrips_file])
print("Running duarouter...")
subprocess.run([duarouter_path, "-n", network_path, "-r", odtrips_file, "-o", rou_file])

# 2. SUMO 시뮬레이션 실행 (생성된 경로 파일 사용)
cmd = [sumo_path, "-n", network_path, "-r", rou_file, "-b", str(sim_begin), "-e", str(sim_end)]
print("Starting SUMO simulation for heatmap data generation...")
traci.start(cmd)

# 3. 시뮬레이션 동안 모든 차량의 위치, 속도 데이터를 메모리에 저장
rows = []
while True:
    current_time = traci.simulation.getTime()
    if current_time > sim_end:
        break

    vehicle_ids = traci.vehicle.getIDList()
    for vid in vehicle_ids:
        pos = traci.vehicle.getPosition(vid)  # (x, y)
        speed = traci.vehicle.getSpeed(vid)
        rows.append({
            'time': current_time,
            'vehicle_id': vid,
            'x': pos[0],
            'y': pos[1],
            'speed': speed
        })
    traci.simulationStep()

traci.close()

# 4. X, Y의 최소값을 찾아 보정
if rows:
    min_x = min(row['x'] for row in rows)
    min_y = min(row['y'] for row in rows)
    for row in rows:
        row['x'] = row['x'] - min_x
        row['y'] = row['y'] - min_y

# 5. CSV 파일로 저장
output_csv = os.path.join(TEMP_ROOT, timestamp + "_heatmap.csv")
with open(output_csv, 'w', newline='') as csvfile:
    fieldnames = ['Time', 'VehicleId', 'X', 'Y', 'Speed']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({
            'Time': row['time'],
            'VehicleId': row['vehicle_id'],
            'X': row['x'],
            'Y': row['y'],
            'Speed': row['speed']
        })

print(f"Heatmap data written to {output_csv}")
