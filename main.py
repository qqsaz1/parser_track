import sys
import os
import shutil
import io

from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton,
                             QVBoxLayout, QHBoxLayout, QWidget, QFileDialog,
                             QLabel, QMessageBox, QDoubleSpinBox, QGroupBox)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QUrl

from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
import folium

# Импортируем твой класс из соседнего файла parser.py
from parser import Parser

class TrackParserApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Track Parser Tool with Map")
        self.resize(1100, 800)

        # Временный файл будет создаваться в рабочей директории
        self.temp_output_file = os.path.join(os.getcwd(), "temp_processed_track.txt")

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ==========================================
        # Левая панель управления
        # ==========================================
        control_panel = QWidget()
        control_panel.setFixedWidth(320)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setSpacing(15)
        control_layout.setContentsMargins(0, 0, 0, 0)

        # ---- Настройка шага ----
        settings_group = QGroupBox("Настройки")
        settings_layout = QVBoxLayout()
        
        lbl_step = QLabel("Шаг ресемплинга (в метрах):")
        lbl_step.setFont(QFont("Arial", 10))
        settings_layout.addWidget(lbl_step)

        self.spin_step = QDoubleSpinBox()
        self.spin_step.setValue(3.0)
        self.spin_step.setMinimum(0.1)
        self.spin_step.setMaximum(500.0)
        self.spin_step.setSingleStep(0.5)
        self.spin_step.setSuffix(" м")
        self.spin_step.setFont(QFont("Arial", 11))
        settings_layout.addWidget(self.spin_step)
        
        settings_group.setLayout(settings_layout)
        control_layout.addWidget(settings_group)

        # ---- Кнопка 1: Обработка ----
        self.btn_load = QPushButton("1. Выбрать и обработать")
        self.btn_load.setMinimumHeight(45)
        self.btn_load.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.btn_load.setStyleSheet("background-color: #2b5c8f; color: white; border-radius: 5px;")
        self.btn_load.clicked.connect(self.load_and_process)
        control_layout.addWidget(self.btn_load)

        # ---- Кнопка 2: Карта (НОВАЯ) ----
        self.btn_show_map = QPushButton("2. Показать трек на карте")
        self.btn_show_map.setMinimumHeight(45)
        self.btn_show_map.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.btn_show_map.setStyleSheet("background-color: #e67e22; color: white; border-radius: 5px;")
        self.btn_show_map.setEnabled(False) # Выключена до обработки
        self.btn_show_map.clicked.connect(self.show_map)
        control_layout.addWidget(self.btn_show_map)

        # ---- Кнопка 3: Сохранение ----
        self.btn_export = QPushButton("3. Выгрузить трек (.txt)")
        self.btn_export.setMinimumHeight(45)
        self.btn_export.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.btn_export.setStyleSheet("background-color: #2b8f44; color: white; border-radius: 5px;")
        self.btn_export.setEnabled(False) # Выключена до обработки
        self.btn_export.clicked.connect(self.export_track)
        control_layout.addWidget(self.btn_export)

        # Информационный блок
        self.label_status = QLabel("Готов к работе.\nЗагрузите трек (GeoJSON/TXT).")
        self.label_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_status.setWordWrap(True)
        self.label_status.setStyleSheet("color: gray; border: 1px solid #ccc; padding: 10px; border-radius: 5px;")
        control_layout.addWidget(self.label_status)

        control_layout.addStretch()
        main_layout.addWidget(control_panel)

        # ==========================================
        # Правая панель с картой
        # ==========================================
        map_group = QGroupBox("Предпросмотр трека")
        map_layout = QVBoxLayout()
        map_layout.setContentsMargins(5, 10, 5, 5)

        self.web_view = QWebEngineView()
        self.web_view.setStyleSheet("border: 1px solid #ccc;")
        
        web_settings = self.web_view.settings()
        web_settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        web_settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        
        self.show_empty_map()
        
        map_layout.addWidget(self.web_view)
        map_group.setLayout(map_layout)
        main_layout.addWidget(map_group)

        central_widget.setLayout(main_layout)

    def show_empty_map(self):
        m = folium.Map(location=[55.75, 37.62], zoom_start=5, tiles="OpenStreetMap") 
        self.load_folium_map_to_web_view(m)

    def load_folium_map_to_web_view(self, folium_map):
        try:
            data = io.BytesIO()
            folium_map.save(data, close_file=False)
            html_content = data.getvalue().decode('utf-8')
            
            # Загружаем через обходной путь (localhost) от белого экрана
            self.web_view.setHtml(html_content, QUrl("http://localhost"))
        except Exception as e:
            print(f"Ошибка загрузки карты: {e}")

    def parse_processed_coordinates(self, file_path):
        import json
        coords = []
        if not os.path.exists(file_path):
            return coords
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for feature in data.get("features", []):
                geom = feature.get("geometry", {})
                if geom.get("type") == "LineString":
                    original_coords = geom.get("coordinates", [])
                    for point in original_coords:
                        if len(point) >= 2:
                            coords.append([point[1], point[0]]) # [lat, lon]
        except Exception as e:
            print(f"Ошибка при чтении JSON для карты: {e}")
            
        return coords

    # ==========================================
    # ЛОГИКА КНОПОК
    # ==========================================

    def load_and_process(self):
        """Функция только для парсинга и расчетов (Кнопка 1)."""
        input_file, _ = QFileDialog.getOpenFileName(
            self, "Выберите файл трека", "", "GeoJSON/TXT Files (*.txt *.json);;All Files (*)"
        )

        if input_file:
            try:
                self.label_status.setText("Идет математическая обработка...\nПожалуйста, подождите.")
                self.btn_load.setEnabled(False)
                self.btn_show_map.setEnabled(False)
                self.btn_export.setEnabled(False)
                QApplication.processEvents()

                step_val = self.spin_step.value()
                
                # Запуск парсера
                parser = Parser(step_meters=step_val)
                parser.process_track_file(input_file, self.temp_output_file, step_meters=step_val)

                # Открываем доступ к следующим шагам
                self.btn_show_map.setEnabled(True)
                self.btn_export.setEnabled(True)
                self.btn_load.setEnabled(True)
                
                self.label_status.setText(f"Успех!\nТрек обработан (шаг {step_val} м).\nТеперь вы можете отрисовать его или выгрузить.")
                self.label_status.setStyleSheet("color: #2b5c8f; border: 1px solid #2b5c8f; padding: 10px; border-radius: 5px;")

            except Exception as e:
                self.btn_load.setEnabled(True)
                self.label_status.setText("Ошибка при обработке.")
                self.label_status.setStyleSheet("color: red; border: 1px solid red; padding: 10px; border-radius: 5px;")
                QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при обработке:\n\n{str(e)}")

    def show_map(self):
        """Функция только для отрисовки карты (Кнопка 2)."""
        try:
            self.label_status.setText("Генерация карты...\nЭто может занять время.")
            self.btn_show_map.setEnabled(False)
            QApplication.processEvents()

            coordinates = self.parse_processed_coordinates(self.temp_output_file)
            
            if not coordinates:
                raise Exception("Не найдено валидных координат в обработанном файле.")

            # Создаем карту Folium
            m = folium.Map(tiles="OpenStreetMap")

            # Линия
            folium.PolyLine(
                coordinates, 
                color="blue", 
                weight=5, 
                opacity=0.8
            ).add_to(m)

            # Маркеры
            folium.Marker(coordinates[0], popup="Старт", icon=folium.Icon(color='green', icon='play')).add_to(m)
            folium.Marker(coordinates[-1], popup="Финиш", icon=folium.Icon(color='red', icon='stop')).add_to(m)

            # Фокус камеры
            m.fit_bounds(coordinates)
            self.load_folium_map_to_web_view(m)

            self.btn_show_map.setEnabled(True)
            self.label_status.setText(f"Карта успешно загружена!\nОтрисовано точек: {len(coordinates)}")
            self.label_status.setStyleSheet("color: green; border: 1px solid green; padding: 10px; border-radius: 5px;")

        except Exception as e:
            self.btn_show_map.setEnabled(True)
            self.label_status.setText("Ошибка отрисовки карты.")
            self.label_status.setStyleSheet("color: red; border: 1px solid red; padding: 10px; border-radius: 5px;")
            self.show_empty_map()
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при отрисовке:\n\n{str(e)}")

    def export_track(self):
        """Функция для выгрузки файла (Кнопка 3)."""
        if not os.path.exists(self.temp_output_file):
            return

        save_file, _ = QFileDialog.getSaveFileName(
            self, "Сохранить измененный трек", "TRACK_processed.txt", "Text Files (*.txt);;JSON Files (*.json)"
        )

        if save_file:
            try:
                shutil.copy(self.temp_output_file, save_file)
                QMessageBox.information(self, "Готово", f"Трек успешно сохранен!")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл:\n{str(e)}")

    def closeEvent(self, event):
        if os.path.exists(self.temp_output_file):
            try:
                os.remove(self.temp_output_file)
            except:
                pass
        event.accept()

if __name__ == '__main__':
    # Оставляем костыли для стабильности на Windows
    os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1" 
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu"
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    window = TrackParserApp()
    window.show()
    sys.exit(app.exec())