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
        html_file_path = os.path.abspath("mobility.html")
        url = QUrl.fromLocalFile(html_file_path)
        self.web_view.setUrl(url)
        layout.addWidget(self.web_view)

        # CSV 및 XML 파일 로드
        self.load_csv_files()
        self.xml_data = self.parse_xml_to_json(os.path.abspath("data/network_jeju_canvas_adjusted.xml"))

        # 페이지 로드 완료 시 JavaScript에 데이터 전달
        self.web_view.loadFinished.connect(self.on_load_finished)

    def load_csv_files(self):
        try:
            csv_file_path1 = os.path.abspath("data/Jeju_V5_30_Output_data_with_leader_speed_acceleration_distance_adjusted.csv")
            with open(csv_file_path1, 'r') as file:
                self.csv_data1 = file.read()

            csv_file_path2 = os.path.abspath("data/Jeju_V5_60_Output_data_with_leader_speed_acceleration_distance_adjusted.csv")
            with open(csv_file_path2, 'r') as file:
                self.csv_data2 = file.read()

            csv_file_path3 = os.path.abspath("data/Combined_Jeju_V5_Output_data_Macro.csv")
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

            min_x, min_y = float("inf"), float("inf")
            max_x, max_y = float("-inf"), float("-inf")

            for edge in root.findall('edge'):
                for lane in edge.findall('lane'):
                    shape = lane.get('shape')
                    points = shape.split(' ')
                    for i in range(len(points) - 1):
                        x1, y1 = map(float, points[i].split(','))
                        x2, y2 = map(float, points[i + 1].split(','))
                        network_data['nodes'].append({"x": x1, "y": y1})
                        network_data['nodes'].append({"x": x2, "y": y2})
                        network_data['edges'].append({"source": {"x": x1, "y": y1}, "target": {"x": x2, "y": y2}})
                        
                        # Update min and max values for width and height calculation
                        min_x, min_y = min(min_x, x1, x2), min(min_y, y1, y2)
                        max_x, max_y = max(max_x, x1, x2), max(max_y, y1, y2)

            network_data['nodes'] = [dict(t) for t in {tuple(d.items()) for d in network_data['nodes']}]

            # Calculate width and height
            self.network_width = max_x - min_x
            self.network_height = max_y - min_y

            return json.dumps(network_data)
        except Exception as e:
            print(f"Error parsing XML: {e}")
            return {}

    def on_load_finished(self):
        print("Page load finished, executing JavaScript...")
        
        # 네트워크 비율과 스케일 계산
        network_rate = self.network_height / self.network_width
        
        # height를 window_height의 40%로 설정
        canvas_width = self.window_width
        canvas_height = canvas_width * network_rate
        
        # 스케일 계산
        scale_x = canvas_width / self.network_width
        scale_y = canvas_height / self.network_height

        # JavaScript로 네트워크 크기 및 계산된 값을 전달
        self.web_view.page().runJavaScript(f"networkWidth = {self.network_width};")
        self.web_view.page().runJavaScript(f"networkHeight = {self.network_height};")
        self.web_view.page().runJavaScript(f"networkRate = {network_rate};")
        self.web_view.page().runJavaScript(f"height = {canvas_height};")
        self.web_view.page().runJavaScript(f"width = {canvas_width};")
        self.web_view.page().runJavaScript(f"scaleX = {scale_x};")
        self.web_view.page().runJavaScript(f"scaleY = {scale_y};")
        
        # XML 데이터를 직접 JavaScript 함수로 전달
        self.web_view.page().runJavaScript(f"drawNetwork('content-03-01-01', {self.xml_data});")
        self.web_view.page().runJavaScript(f"drawNetwork('content-03-02-01', {self.xml_data});")

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