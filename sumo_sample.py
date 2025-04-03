import os
import sys
import subprocess
from datetime import datetime

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
import traci    # 반드시 sys.path.append로 패키지 경로를 추가한 뒤에 import 해야함

network_file_name = 'Deajeon_V6.net.xml'
taz_file_name = 'Deajeon_V6.taz.xml'
od_file_name = 'Deajeon_v6_2.od'

network_path = os.path.join(DATA_ROOT, network_file_name)
taz_path = os.path.join(DATA_ROOT, taz_file_name)
od_path = os.path.join(DATA_ROOT, od_file_name)

print("traci 경로:", os.path.abspath(traci.__file__))

# 시뮬레이션 매개변수
sim_begin = 0
sim_end = 60 * 2

if __name__ == "__main__":
    temp_file_name = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    # odtrips.xml 파일 생성
    odtrips_file_name = temp_file_name + '.odtrips.xml'
    odtrips_file_path = os.path.join(TEMP_ROOT, odtrips_file_name)
    subprocess.run([od2trips_path, "-n", taz_path, "-d", od_path, "-o", odtrips_file_path])

    # rou.xml 파일 생성
    rou_file_name = temp_file_name + '.rou.xml'
    rou_file_path = os.path.join(TEMP_ROOT, rou_file_name)
    subprocess.run([duarouter_path, "-n", network_path, "-r", odtrips_file_path, "-o", rou_file_path])

    # sumo 시뮬레이션 시작
    cmd_arg_list = [sumo_path, "-n", network_path, "-r", rou_file_path,
                    "-b", str(sim_begin), "-e", str(sim_end)]
    traci.start(cmd_arg_list)

    while True:
        curr_time = traci.simulation.getTime()

        if curr_time > sim_end:
            break

        traci.simulationStep()

        avg_speed = 0
        vehicle_ids = traci.vehicle.getIDList()
        for veh_id in vehicle_ids:
            route_id = traci.vehicle.getRouteID(veh_id)
            speed = traci.vehicle.getSpeed(veh_id)
            pos = traci.vehicle.getPosition(veh_id)
            lane_id = traci.vehicle.getLaneID(veh_id)
            acceleration = traci.vehicle.getAcceleration(veh_id)
            Decel = traci.vehicle.getDecel(veh_id)
            angle = traci.vehicle.getAngle(veh_id)
            departdelay = traci.vehicle.getDepartDelay(veh_id)
            departure = traci.vehicle.getDeparture(veh_id)
            distance = traci.vehicle.getDistance(veh_id)
            avg_speed += speed
            # print(route_id, speed, pos, lane_id, acceleration, Decel, angle, departdelay, departure, distance)

        if len(vehicle_ids) > 0:
            avg_speed = avg_speed / len(vehicle_ids)
        print('Curr Time : {} / num vehicles : {} / avg speed : {}'.format(curr_time, len(vehicle_ids), avg_speed))

    traci.close()
    print('Simulation ended.')
