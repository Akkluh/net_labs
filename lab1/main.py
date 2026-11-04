import sys
import subprocess
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, 
                               QPushButton, QLineEdit, QHBoxLayout, QTextEdit, QFormLayout, QSpinBox, 
                               QTableWidget, QHeaderView, QTableWidgetItem)
import re
# Класс главного окна приложения
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.ping_tab = QWidget()
        self.ipconfig_tab = QWidget()
        self.pathping_tab = QWidget()
        self.netstat_tab = QWidget()
        
        self.tabs.addTab(self.ping_tab, "Ping")
        self.tabs.addTab(self.ipconfig_tab, "IPConfig")
        self.tabs.addTab(self.pathping_tab, "PathPing")
        self.tabs.addTab(self.netstat_tab, "NetStat")

        self.create_ping_tab()
        self.create_ipconfig_tab()
        self.create_pathping_tab()
        self.create_netstat_tab()
# PING
# Метод для создания вкладки Ping
    def create_ping_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        input_layout = QHBoxLayout()
        form_layout = QFormLayout()

        label = QLabel("IP-адрес или домен:")

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Введите IP-адрес или домен:")

        button = QPushButton("Проверить")
        button.clicked.connect(self.ping_run)

        input_layout.addWidget(label)
        input_layout.addWidget(self.ip_input)
        layout.addLayout(input_layout)

        self.ping_count = QSpinBox()
        self.ping_count.setRange(1, 1000)
        self.ping_count.setValue(4)

        self.ping_size = QSpinBox()
        self.ping_size.setRange(1, 65500)
        self.ping_size.setValue(32)

        self.ping_timeout = QSpinBox()
        self.ping_timeout.setRange(1, 10000)
        self.ping_timeout.setValue(1000)

        form_layout.addRow("Количество пакетов:", self.ping_count)
        form_layout.addRow("Размер пакета (байт):", self.ping_size)
        form_layout.addRow("Время ожидания (мс):", self.ping_timeout)
        layout.addLayout(form_layout)

        layout.addWidget(button)

        self.ping_table = QTableWidget()
        self.ping_table.setColumnCount(6)
        self.ping_table.setHorizontalHeaderLabels(["№", "IP-адрес", "Байты", "Время (мс)", "TTL", "Результат"])
        self.ping_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ping_table.verticalHeader().setVisible(False)
        self.ping_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.ping_table)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

        self.ping_tab.setLayout(layout)
    def process_ping_result(self, result):
        ip_result = re.search(r"Ответ от ([\d\.]+):", result)
        bytes_result = re.search(r"байт=(\d+)", result)
        time_result = re.search(r"время[=<](\d+)", result)
        ttl_result = re.search(r"TTL=(\d+)", result)
        if ip_result and bytes_result and time_result and ttl_result:
            return {
                "ip": ip_result.group(1),
                "bytes": int(bytes_result.group(1)),
                "time": int(time_result.group(1)),
                "ttl": int(ttl_result.group(1)),
                "status": "Успешно"
            }
        return None
    def add_ping_result(self, result):
        row = self.ping_table.rowCount()
        self.ping_table.insertRow(row)
        self.ping_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.ping_table.setItem(row, 1, QTableWidgetItem(result["ip"]))
        self.ping_table.setItem(row, 2, QTableWidgetItem(str(result["bytes"]) if result["bytes"] is not None else "---"))
        self.ping_table.setItem(row, 3, QTableWidgetItem(str(result["time"]) if result["time"] is not None else "---"))
        self.ping_table.setItem(row, 4, QTableWidgetItem(str(result["ttl"]) if result["ttl"] is not None else "---"))
        self.ping_table.setItem(row, 5, QTableWidgetItem(result["status"]))
    # Метод для выполнения команды ping
    def ping_run(self):
        receive_count = 0
        lost_count = 0
        total_time = 0
        # Получение введенных пользователем данных
        ip = self.ip_input.text().strip()
        if not ip:
            self.result_text.setText("Пожалуйста, введите IP-адрес или домен.")
            return
        count = self.ping_count.value()
        if count <= 0:
            self.result_text.setText("Количество пакетов должно быть больше нуля.")
            return
        size = self.ping_size.value()
        if size <= 0:
            self.result_text.setText("Размер пакета должен быть больше нуля.")
            return
        timeout = self.ping_timeout.value()
        if timeout <= 0:
            self.result_text.setText("Время ожидания должно быть больше нуля.")
            return
        self.ping_table.setRowCount(0)  # Очистка таблицы перед новым запуском
        try:
            # Выполнение команды ping с указанными параметрами
            result = subprocess.run(["ping", "-n", str(count), "-l", str(size), "-w", str(timeout), ip], capture_output=True, text=True, timeout=15, encoding='cp866', errors='replace')
            # Разделение вывода на строки и обработка каждой строки
            for output in result.stdout.splitlines():
                ping_result = self.process_ping_result(output)
                if ping_result:
                    self.add_ping_result(ping_result)
                    receive_count += 1
                    total_time += ping_result["time"]
                elif "Превышен интервал ожидания" in output:
                    self.add_ping_result({
                        "ip": ip,
                        "bytes": None,
                        "time": None,
                        "ttl": None,
                        "status": "Потеря пакета"
                    })
                    lost_count += 1
            # Вывод статистики по результатам ping
            loss_percentage = (lost_count / count) * 100
            if receive_count > 0:
                average_time = total_time / receive_count
            else:
                average_time = 0
            self.result_text.setText(f"Отправлено: {count}\n"
                                     f"Получено: {receive_count}\n"
                                     f"Потеряно: {lost_count}\n"
                                     f"Процент потерь: {loss_percentage:.2f}%\n"
                                     f"Среднее время: {average_time:.2f} мс")
        except subprocess.TimeoutExpired:
            self.result_text.setText("Превышено время ожидания.")
        except Exception as error:
            self.result_text.setText(f"Ошибка: {error}")
# IPCONFIG
    # Метод для создания вкладки IPConfig
    def create_ipconfig_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        button = QPushButton("Получить информацию о сети")
        button.clicked.connect(self.ipconfig_run)

        layout.addWidget(button)

        self.result_text_ipconfig = QTextEdit()
        self.result_text_ipconfig.setReadOnly(True)
        layout.addWidget(self.result_text_ipconfig)

        self.ipconfig_tab.setLayout(layout)
    # Метод для выполнения команды ipconfig
    def ipconfig_run(self):
        try:
            result = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, timeout=15, encoding='cp866', errors='replace')
            self.result_text_ipconfig.setPlainText(result.stdout)
        except subprocess.TimeoutExpired:
            self.result_text_ipconfig.setText("Превышено время ожидания.")
        except Exception as error:
            self.result_text_ipconfig.setText(f"Ошибка: {error}")
# PATHPING
    # Метод для создания вкладки PathPing
    def create_pathping_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        label = QLabel("IP-адрес или домен:")
        self.pathping_input = QLineEdit()
        self.pathping_input.setPlaceholderText("Введите IP-адрес или домен:")

        button = QPushButton("Проверить")
        button.clicked.connect(self.pathping_run)

        input_layout = QHBoxLayout()
        input_layout.addWidget(label)
        input_layout.addWidget(self.pathping_input)
        input_layout.addWidget(button)
        layout.addLayout(input_layout)

        self.result_text_pathping = QTextEdit()
        self.result_text_pathping.setReadOnly(True)
        layout.addWidget(self.result_text_pathping)

        self.pathping_tab.setLayout(layout)
    # Метод для выполнения команды pathping
    def pathping_run(self):
        ip = self.pathping_input.text().strip()
        if not ip:
            self.result_text_pathping.setText("Пожалуйста, введите IP-адрес или домен.")
            return
        try:
            result = subprocess.run(["pathping", "-n", ip], capture_output=True, text=True, timeout=60, encoding='cp866', errors='replace')
            self.result_text_pathping.setPlainText(result.stdout)
        except subprocess.TimeoutExpired:
            self.result_text_pathping.setText("Превышено время ожидания.")
        except Exception as error:
            self.result_text_pathping.setText(f"Ошибка: {error}")
# NETSTAT
    # Метод для создания вкладки NetStat
    def create_netstat_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        button = QPushButton("Получить информацию")
        button.clicked.connect(self.netstat_run)
        layout.addWidget(button)

        self.result_text_netstat = QTextEdit()
        self.result_text_netstat.setReadOnly(True)
        layout.addWidget(self.result_text_netstat)

        self.netstat_tab.setLayout(layout)
    # Метод для выполнения команды netstat
    def netstat_run(self):
        try:
            result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=30, encoding='cp866', errors='replace')
            self.result_text_netstat.setPlainText(result.stdout)
        except subprocess.TimeoutExpired:
            self.result_text_netstat.setText("Превышено время ожидания.")
        except Exception as error:
            self.result_text_netstat.setText(f"Ошибка: {error}")
# Запуска приложения
app = QApplication(sys.argv)
window = MainWindow()
window.setWindowTitle("Network Analyzer")
window.resize(1000, 650)
window.show()
sys.exit(app.exec())