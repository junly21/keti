## pip install PyQt5==5.15.11 PyQt5-Qt5==5.15.2 PyQt5_sip==12.15.0 PyQtWebEngine==5.15.7


import sys
import json
import csv
import xml.etree.ElementTree as ET
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import QUrl, Qt
import os

class CustomWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, line, source):
        print(f"console message: {message} (Source: {source}, Line: {line})")

class MainWindow(QMainWindow):
    def __init__(self, window_width=1920, window_height=1080):
        super().__init__()

        self.window_width = window_width
        self.window_height = window_height
        self.setWindowTitle("Test")
        self.setGeometry(100, 100, self.window_width, self.window_height)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        self.web_view = QWebEngineView()
        custom_page = CustomWebEnginePage(self.web_view)
        self.web_view.setPage(custom_page)

        # HTML 파일 로드
        html_file_path = os.path.abspath("mobility_traci.html")
        url = QUrl.fromLocalFile(html_file_path)
        self.web_view.setUrl(url)
        layout.addWidget(self.web_view)

        # CSV 및 XML 파일 로드
        self.load_csv_files()
        self.xml_data = self.parse_xml_to_json(os.path.abspath("data/Deajeon_V6.net.xml"))

        # 페이지 로드 완료 시 JavaScript에 데이터 전달
        self.web_view.loadFinished.connect(self.on_load_finished)

    def load_csv_files(self):
        try:
            csv_file_path1 = os.path.abspath("temp/2025-02-24-11-56-53_heatmap.csv")
            with open(csv_file_path1, 'r') as file:
                self.csv_data1 = file.read()

            csv_file_path2 = os.path.abspath("data/Deajeon_V6_Output2_data_with_leader_speed_acceleration_distance.csv")
            with open(csv_file_path2, 'r') as file:
                self.csv_data2 = file.read()

            csv_file_path3 = os.path.abspath("temp/2025-02-24-12-04-24_macro.csv")
            with open(csv_file_path3, 'r') as file:
                self.csv_data3 = file.read()

            def convert_type(value):
                try:
                    return int(value)
                except ValueError:
                    try:
                        return float(value)
                    except ValueError:
                        return value

            def csv_to_json(csv_data):
                reader = csv.DictReader(csv_data.splitlines())
                json_data = []
                for row in reader:
                    converted_row = {key: convert_type(value) for key, value in row.items()}
                    json_data.append(converted_row)
                return json_data

            # JSON 데이터로 변환
            self.csv_json_data1 = csv_to_json(self.csv_data1)
            self.csv_json_data2 = csv_to_json(self.csv_data2)
            self.csv_json_data3 = csv_to_json(self.csv_data3)

        except Exception as e:
            print(f"Error loading CSV files: {e}")

    def parse_xml_to_json(self, xml_file_path):
        try:
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            network_data = {"nodes": [], "edges": []}
            junction_coords = {}

            min_x, min_y = float("inf"), float("inf")
            max_x, max_y = float("-inf"), float("-inf")

            # Junction 좌표 추출 및 최소, 최대 좌표 계산
            for junction in root.findall('junction'):
                junc_id = junction.attrib['id']
                x, y = float(junction.attrib['x']), float(junction.attrib['y'])
                junction_coords[junc_id] = {'x': x, 'y': y}
                min_x, min_y = min(min_x, x), min(min_y, y)
                max_x, max_y = max(max_x, x), max(max_y, y)

            # lane의 좌표(shape) 추출 (중요한 수정사항)
            for edge in root.findall('edge'):
                for lane in edge.findall('lane'):
                    shape = lane.attrib.get('shape')
                    if shape:
                        points = shape.split(' ')
                        for i in range(len(points) - 1):
                            x1, y1 = map(float, points[i].split(','))
                            x2, y2 = map(float, points[i + 1].split(','))

                            network_data['edges'].append({
                                "source": {"x": x1, "y": y1},
                                "target": {"x": x2, "y": y2}
                            })

                            min_x, min_y = min(min_x, x1, x2), min(min_y, y1, y2)
                            max_x, max_y = max(max_x, x1, x2), max(max_y, y1, y2)

            # Junction 좌표 보정
            for jid, coord in junction_coords.items():
                corrected_x = coord['x'] - min_x
                corrected_y = coord['y'] - min_y
                network_data['nodes'].append({
                    "id": jid,
                    "x": corrected_x,
                    "y": corrected_y
                })

            # Edge 좌표 보정 및 노드 추가
            for edge in network_data['edges']:
                edge["source"]["x"] -= min_x
                edge["source"]["y"] -= min_y
                edge["target"]["x"] -= min_x
                edge["target"]["y"] -= min_y

                network_data['nodes'].append(edge["source"])
                network_data['nodes'].append(edge["target"])

            # 중복된 노드 제거
            unique_nodes = { (node['x'], node['y']) : node for node in network_data['nodes'] }
            network_data['nodes'] = list(unique_nodes.values())

            # 네트워크 크기 업데이트
            self.network_width = max_x - min_x
            self.network_height = max_y - min_y

            return network_data

        except Exception as e:
            print(f"Error parsing XML: {e}")
            return {}

    def load_xml(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                xml_data = file.read()
                
                # XML 파싱
                root = ET.fromstring(xml_data)
                
                # 도로(edge) 데이터 추출
                edges_data = []
                for edge in root.findall('.//edge'):
                    edge_info = {
                        'id': edge.get('id'),
                        'function': edge.get('function'),
                        'lanes': []
                    }
                    
                    # 차선(lane) 데이터 추출
                    for lane in edge.findall('lane'):
                        lane_info = {
                            'id': lane.get('id'),
                            'index': lane.get('index'),
                            'speed': lane.get('speed'),
                            'length': lane.get('length'),
                            'disallow': lane.get('disallow'),
                            'shape': lane.get('shape')
                        }
                        edge_info['lanes'].append(lane_info)
                    
                    edges_data.append(edge_info)
                
                # 교차로(junction) 데이터 추출
                junctions_data = []
                for junction in root.findall('.//junction'):
                    junction_info = {
                        'id': junction.get('id'),
                        'type': junction.get('type'),
                        'x': junction.get('x'),
                        'y': junction.get('y')
                    }
                    junctions_data.append(junction_info)
                
                # 모든 데이터를 하나의 객체로 합침
                network_data = {
                    'edges': edges_data,
                    'junctions': junctions_data
                }
                
                # JSON으로 변환
                json_data = json.dumps(network_data)
                
                # JavaScript로 데이터 전달
                self.web_view.page().runJavaScript(f'window.networkData = {json_data};')
                
                return xml_data
        except Exception as e:
            print(f"Error loading XML: {e}")
            return None

    def on_load_finished(self):
        print("Page load finished, executing JavaScript...")
       
        # 네트워크 비율, 스케일, 높이 계산
        network_rate = self.network_height / self.network_width
        height = self.window_width * network_rate
        scale_x = self.window_width / self.network_width
        scale_y = height / self.network_height

        # JavaScript로 네트워크 크기 및 계산된 값을 전달
        self.web_view.page().runJavaScript(f"networkWidth = {self.network_width};")
        self.web_view.page().runJavaScript(f"networkHeight = {self.network_height};")
        self.web_view.page().runJavaScript(f"networkRate = {network_rate};")
        self.web_view.page().runJavaScript(f"height = {height};")
        self.web_view.page().runJavaScript(f"scaleX = {scale_x};")
        self.web_view.page().runJavaScript(f"scaleY = {scale_y};")

        self.web_view.page().runJavaScript("console.log('networkWidth:', networkWidth);")
        self.web_view.page().runJavaScript("console.log('networkHeight:', networkHeight);")
        self.web_view.page().runJavaScript("console.log('networkRate:', networkRate);")
        
        # XML 데이터를 직접 JavaScript 함수로 전달
        self.web_view.page().runJavaScript(f"drawNetwork('content-03-01-01', {self.xml_data});")
        self.web_view.page().runJavaScript(f"drawNetwork('content-03-02-01', {self.xml_data});")

        # 도로 정보 로드
        self.load_xml(os.path.abspath("data/Deajeon_V6.net.xml"))

        # CSV 데이터를 분할하여 JavaScript로 전송
        self.send_large_data_in_chunks(self.csv_json_data1, "mprHeatmap", "content-03-01-01")
        self.send_large_data_in_chunks(self.csv_json_data2, "mprHeatmap", "content-03-02-01")
        self.send_large_data_in_chunks(self.csv_json_data3, "setChart")


    def send_large_data_in_chunks(self, data, function_name, element_id=None, chunk_size=1000):
        total_chunks = (len(data) + chunk_size - 1) // chunk_size
        for i in range(total_chunks):
            chunk = data[i * chunk_size: (i + 1) * chunk_size]
            json_chunk = json.dumps(chunk)
            
            # receiveDataChunk로 함수 이름을 문자열로 전달
            if element_id:
                self.web_view.page().runJavaScript(
                    f"receiveDataChunk('{function_name}', {json_chunk}, '{element_id}', {i + 1}, {total_chunks});"
                )
            else:
                self.web_view.page().runJavaScript(
                    f"receiveDataChunk('{function_name}', {json_chunk}, null, {i + 1}, {total_chunks});"
                )


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())