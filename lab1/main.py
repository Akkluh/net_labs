import sys
import subprocess
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, 
                               QPushButton, QLineEdit, QHBoxLayout, QTextEdit, QFormLayout, QSpinBox, 
                               QTableWidget, QHeaderView, QTableWidgetItem, QCheckBox, QComboBox, QGridLayout)
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
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        input_layout = QHBoxLayout()
        params_layout = QVBoxLayout()
        params_layout.setSpacing(8)

        label = QLabel("IP-адрес или домен:")

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Введите IP-адрес или домен:")

        self.button = QPushButton("Проверить")
        self.button.clicked.connect(self.ping_run)
        self.stop_button = QPushButton("Остановить")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.ping_stop)

        input_layout.addWidget(label)
        input_layout.addWidget(self.ip_input)
        layout.addLayout(input_layout)

        # количество пакетов (-n)
        self.ping_count = QSpinBox()
        self.ping_count.setRange(1, 1000)
        self.ping_count.setValue(4)
        self.ping_count_check = QCheckBox("Количество пакетов (-n)")
        self.ping_count.setEnabled(False)
        self.ping_count_check.toggled.connect(self.ping_count.setEnabled)

        # размер (-l)
        self.ping_size = QSpinBox()
        self.ping_size.setRange(1, 65500)
        self.ping_size.setValue(32)
        self.ping_size_check = QCheckBox("Размер (-l)")
        self.ping_size.setEnabled(False)
        self.ping_size_check.toggled.connect(self.ping_size.setEnabled)

        # задержка (-w)
        self.ping_timeout = QSpinBox()
        self.ping_timeout.setRange(1, 10000)
        self.ping_timeout.setValue(1000)
        self.ping_timeout_check = QCheckBox("Таймаут (-w)")
        self.ping_timeout.setEnabled(False)
        self.ping_timeout_check.toggled.connect(self.ping_timeout.setEnabled)

        # Время жизни пакета (параметр -i)
        self.ping_ttl = QSpinBox()
        self.ping_ttl.setRange(1, 255)
        self.ping_ttl.setValue(128)
        self.ping_ttl_check = QCheckBox("TTL (-i)")
        self.ping_ttl.setEnabled(False)
        self.ping_ttl_check.toggled.connect(self.ping_ttl.setEnabled)

        # Флаг "не фрагментировать" (параметр -f)
        self.ping_dont_fragment = QCheckBox("Не фрагментировать пакеты (-f)")

        # Определение имени узла по адресу (параметр -a)
        self.ping_get_name = QCheckBox("Определять имя узла (-a)")

        # Флаг постоянной проверки (параметр -t)
        self.ping_t = QCheckBox("Постоянная проверка (-t)")
        def toggle_ping_count(checked):
            self.ping_count_check.setEnabled(not checked)
            self.ping_count.setEnabled(not checked and self.ping_count_check.isChecked())
        self.ping_t.toggled.connect(toggle_ping_count)

        # Запись маршрута (параметр -r)
        self.ping_r = QCheckBox("Запись маршрута (-r), узлов: ")
        self.ping_r_count = QSpinBox()
        self.ping_r_count.setRange(1, 9)
        self.ping_r_count.setValue(4)
        self.ping_r_count.setEnabled(False)
        self.ping_r.toggled.connect(self.ping_r_count.setEnabled)

        # Метки времени (параметр -s)
        self.ping_s = QCheckBox("Метки времени (параметр -s), узлов: ")
        self.ping_s_count = QSpinBox()
        self.ping_s_count.setRange(1, 4)
        self.ping_s_count.setValue(4)
        self.ping_s_count.setEnabled(False)
        self.ping_s.toggled.connect(self.ping_s_count.setEnabled)

        # Маршрут по списку узлов (параметры -j/-k)
        self.ping_route_type = QComboBox()
        self.ping_route_type.addItems(["Нет", "Нестрогий маршрут (-j)", "Строгий маршрут (-k)"])
        self.ping_line_for_route = QLineEdit()
        self.ping_line_for_route.setPlaceholderText("IP-адресса через пробел")
        self.ping_line_for_route.setEnabled(False)
        self.ping_route_type.currentIndexChanged.connect(lambda i: self.ping_line_for_route.setEnabled(i != 0))
        def group_param(checkbox, spinbox):
            group = QWidget()
            group_layout = QHBoxLayout(group)
            group_layout.setContentsMargins(0, 0, 0, 0)
            group_layout.setSpacing(6)
            spinbox.setFixedWidth(90)
            group_layout.addWidget(checkbox, 1)
            group_layout.addWidget(spinbox)
            return group
        def make_row(c1, s1, c2, s2):
            row = QHBoxLayout()
            row.setSpacing(16)
            row.addWidget(group_param(c1, s1), 1)
            row.addWidget(group_param(c2, s2), 1)
            return row

        params_layout.addLayout(make_row(self.ping_count_check, self.ping_count, self.ping_size_check, self.ping_size))
        params_layout.addLayout(make_row(self.ping_timeout_check, self.ping_timeout, self.ping_ttl_check, self.ping_ttl))
        params_layout.addLayout(make_row(self.ping_s, self.ping_s_count, self.ping_r, self.ping_r_count))
        flags_row = QHBoxLayout()
        flags_row.addWidget(self.ping_dont_fragment, 1)
        flags_row.addWidget(self.ping_get_name, 1)
        flags_row.addWidget(self.ping_t, 1)
        params_layout.addLayout(flags_row)
        route_row = QHBoxLayout()
        route_row.addWidget(self.ping_route_type, 1)
        route_row.addWidget(self.ping_line_for_route, 1)
        params_layout.addLayout(route_row)
        layout.addLayout(params_layout)
        button_row = QHBoxLayout()
        button_row.addWidget(self.button, 1)
        button_row.addWidget(self.stop_button, 1)
        layout.addLayout(button_row)

        self.ping_table = QTableWidget()
        self.ping_table.setColumnCount(6)
        self.ping_table.setHorizontalHeaderLabels(["№", "IP-адрес", "Байты", "Время (мс)", "TTL", "Результат"])
        self.ping_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ping_table.verticalHeader().setVisible(False)
        self.ping_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.ping_table)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(150)
        layout.addWidget(self.result_text)

        self.ping_tab.setLayout(layout)
# Метод для обработки одной строки вывода ping
    def process_ping_result(self, result):
        ip_result = re.search(r"Ответ от (.+?): (.*)", result)
        if not ip_result:
            return None
        bytes_result = re.search(r"байт=(\d+)", result)
        time_result = re.search(r"время[=<](\d+)", result)
        ttl_result = re.search(r"TTL=(\d+)", result)
        # Успешный ответ: есть и байты, и время, и TTL
        if bytes_result and time_result and ttl_result:
            return {
                "ip": ip_result.group(1),
                "bytes": int(bytes_result.group(1)),
                "time": int(time_result.group(1)),
                "ttl": int(ttl_result.group(1)),
                "status": "Успешно"
            }
        return {
            "ip": ip_result.group(1),
            "bytes": None,
            "time": None,
            "ttl": None,
            "status": ip_result.group(2).strip().rstrip(".")
        }
    # Метод для добавления результата ping в таблицу
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
        total_time = 0
        # Получение введенных пользователем данных
        ip = self.ip_input.text().strip()
        if not ip:
            self.result_text.setText("Пожалуйста, введите IP-адрес или домен.")
            return
        route_hosts = self.ping_line_for_route.text().strip()
        route_type = self.ping_route_type.currentIndex()
        if route_type != 0 and not route_hosts:
            self.result_text.setText("Укажите IP-адреса для маршрута по списку узлов")
            return
        count = self.ping_count.value()
        size = self.ping_size.value()
        timeout = self.ping_timeout.value()
        ttl = self.ping_ttl.value()
        self.ping_table.setRowCount(0)  # Очистка таблицы перед новым запуском
        # Формирование команды ping с указанными параметрами
        command = ["ping", "-l", str(size), "-w", str(timeout), "-i", str(ttl)]
        if self.ping_t.isChecked():
            command.append("-t")
        else:
            command.extend(["-n", str(count)])
        if self.ping_dont_fragment.isChecked():
            command.append("-f")
        if self.ping_get_name.isChecked():
            command.append("-a")
        if self.ping_r.isChecked():
            command.extend(["-r", str(self.ping_r_count.value())])
        if self.ping_s.isChecked():
            command.extend(["-s", str(self.ping_s_count.value())])
        if route_type == 1:
            command.extend(["-j", *route_hosts.split()])
        if route_type == 2:
            command.extend(["-k", *route_hosts.split()])
        command.append(ip)
        self.button.setEnabled(False)
        self.stop_button.setEnabled(True)
        all_output = ""
        try:
            self.ping_command = subprocess.Popen(command, stdout=subprocess.PIPE, text=True, encoding='cp866', errors='replace')
            route_lines = []
            time_lines = []
            block_name = ""
            for output in self.ping_command.stdout:
                QApplication.processEvents()
                all_output += output
                self.ping_table.scrollToBottom()
                if "Маршрут:" in output:
                    block_name = "route"
                    route_lines = []
                elif "Отметка времени:" in output:
                    block_name = "time"
                    time_lines = []
                elif not output.startswith(" "):
                    block_name = ""
                if block_name == "route":
                    route_lines.append(output.strip())
                    continue
                if block_name == "time":
                    time_lines.append(output.strip())
                    continue
                ping_result = self.process_ping_result(output)
                if ping_result:
                    self.add_ping_result(ping_result)
                    if ping_result["status"] == "Успешно":
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
            if self.ping_table.rowCount() == 0:
                self.result_text.setText(all_output)
                return
            # Вывод статистики по результатам ping
            count = self.ping_table.rowCount()
            lost_count = count - receive_count
            loss_percentage = (lost_count / count) * 100
            if receive_count > 0:
                average_time = total_time / receive_count
            else:
                average_time = 0
            statistic = (f"Отправлено: {count}\n"
                         f"Получено: {receive_count}\n"
                         f"Потеряно: {lost_count}\n"
                         f"Процент потерь: {loss_percentage:.2f}%\n"
                         f"Среднее время: {average_time:.2f} мс")
            if route_lines:
                statistic += "\n\n"+ "\n".join(route_lines)
            if time_lines:
                statistic += "\n\n"+ "\n".join(time_lines)
            self.result_text.setText(statistic)
        except subprocess.TimeoutExpired:
            self.result_text.setText("Превышено время ожидания.")
        except Exception as error:
            self.result_text.setText(f"Ошибка: {error}")
        finally:
            self.button.setEnabled(True)
            self.stop_button.setEnabled(False)
        # Метод для остановки ping
    def ping_stop(self):
        self.ping_command.terminate()
# IPCONFIG
    # Метод для создания вкладки IPConfig
    def create_ipconfig_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        button = QPushButton("Получить информацию о сети")
        button.clicked.connect(self.ipconfig_run)

        layout.addWidget(button)

        self.adapter_tabs = QTabWidget()
        layout.addWidget(self.adapter_tabs)
        
        self.result_text_ipconfig = QTextEdit()
        self.result_text_ipconfig.setReadOnly(True)
        layout.addWidget(self.result_text_ipconfig)

        self.ipconfig_tab.setLayout(layout)
    # Метод для обработки результата ipconfig
    def process_ipconfig_result(self, result):
        adapters = []
        current_adapter = {}
        last_key = None
        for adapter in result.splitlines():
            line = adapter.strip()
            indent = len(adapter) - len(adapter.lstrip())
            if (line.lower().startswith("адаптер ") or line.lower().startswith("неизвестный адаптер ")) and line.endswith(":"):
                name = line[:-1]
                current_adapter = {"name": name}
                adapters.append(current_adapter)
                last_key = None
            else:
                if  indent == 3 and current_adapter:
                    key, value = line.split(":", 1)
                    key = key.replace(".", "").strip()
                    current_adapter[key.strip()] = value.strip()
                    last_key = key.strip()
                elif indent > 3 and current_adapter and last_key:
                    current_adapter[last_key] += ", " + line.strip()
                elif not line:
                    continue
        return adapters
    # Метод для отображения результатов ipconfig
    def display_ipconfig_result(self, adapters):
        self.adapter_tabs.clear()
        for adapter in adapters:
            tab = QWidget()
            layout = QVBoxLayout()
            for key, value in adapter.items():
                if key != "name":
                    label = QLabel(f"{key}: {value}")
                    layout.addWidget(label)
            tab.setLayout(layout)
            self.adapter_tabs.addTab(tab, adapter["name"])
    # Метод для выполнения команды ipconfig
    def ipconfig_run(self):
        try:
            result = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, timeout=15, encoding='cp866', errors='replace')
            adapters = self.process_ipconfig_result(result.stdout)
            self.display_ipconfig_result(adapters)
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
        input_layout = QHBoxLayout()
        form_layout = QFormLayout()

        label = QLabel("IP-адрес или домен:")
        self.pathping_input = QLineEdit()
        self.pathping_input.setPlaceholderText("Введите IP-адрес или домен:")

        button = QPushButton("Проверить")
        button.clicked.connect(self.pathping_run)

        input_layout.addWidget(label)
        input_layout.addWidget(self.pathping_input)
        layout.addLayout(input_layout)

        # Максимальное число прыжков (параметр -h)
        self.pathping_hops = QSpinBox()
        self.pathping_hops.setRange(1, 255)
        self.pathping_hops.setValue(30)

        # Число запросов на каждый узел (параметр -q)
        self.pathping_queries = QSpinBox()
        self.pathping_queries.setRange(1, 1000)
        self.pathping_queries.setValue(10)

        # Пауза между запросами в мс (параметр -p)
        self.pathping_period = QSpinBox()
        self.pathping_period.setRange(1, 10000)
        self.pathping_period.setValue(250)

        # Время ожидания ответа в мс (параметр -w)
        self.pathping_timeout = QSpinBox()
        self.pathping_timeout.setRange(1, 10000)
        self.pathping_timeout.setValue(3000)

        # Не определять имена узлов (параметр -n)
        self.pathping_no_resolve = QCheckBox("Не определять имена узлов (-n)")
        self.pathping_no_resolve.setChecked(True)

        form_layout.addRow("Максимум прыжков:", self.pathping_hops)
        form_layout.addRow("Число запросов на узел:", self.pathping_queries)
        form_layout.addRow("Пауза между запросами (мс):", self.pathping_period)
        form_layout.addRow("Время ожидания (мс):", self.pathping_timeout)
        form_layout.addRow(self.pathping_no_resolve)
        layout.addLayout(form_layout)

        layout.addWidget(button)

        self.pathping_table = QTableWidget()
        self.pathping_table.setColumnCount(6)
        self.pathping_table.setHorizontalHeaderLabels(["Прыжок", "IP-адрес", "Время (мс)", "Потери до узла (%)", "Потери на узле (%)", "Результат"])
        self.pathping_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.pathping_table.verticalHeader().setVisible(False)
        self.pathping_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.pathping_table)

        self.result_text_pathping = QTextEdit()
        self.result_text_pathping.setReadOnly(True)
        layout.addWidget(self.result_text_pathping)

        self.pathping_tab.setLayout(layout)
    # Метод для обработки одной строки вывода pathping
    def process_pathping_result(self, result):
        # Строка статистики: "  1    2мс     0/ 100 =  0%     0/ 100 =  0%  192.168.1.1"
        # Время может быть "---", если ответа не было
        stat_result = re.search(r"^\s*(\d+)\s+(?:<?(\d+)\s*мс|-)\s+\d+/\s*\d+\s*=\s*(\d+)%\s+\d+/\s*\d+\s*=\s*(\d+)%\s+(.+)$", result)
        if not stat_result:
            return None
        loss_source = int(stat_result.group(3))
        loss_node = int(stat_result.group(4))
        # Вывод о работе узла по потерям на самом узле
        if loss_node == 100:
            status = "Нет ответа"
        elif loss_node > 0:
            status = "Есть потери"
        else:
            status = "Норма"
        return {
            "hop": int(stat_result.group(1)),
            "ip": stat_result.group(5).strip(),
            "time": int(stat_result.group(2)) if stat_result.group(2) else None,
            "loss_source": loss_source,
            "loss_node": loss_node,
            "status": status
        }
    # Метод для добавления результата pathping в таблицу
    def add_pathping_result(self, result):
        row = self.pathping_table.rowCount()
        self.pathping_table.insertRow(row)
        self.pathping_table.setItem(row, 0, QTableWidgetItem(str(result["hop"])))
        self.pathping_table.setItem(row, 1, QTableWidgetItem(result["ip"]))
        self.pathping_table.setItem(row, 2, QTableWidgetItem(str(result["time"]) if result["time"] is not None else "---"))
        self.pathping_table.setItem(row, 3, QTableWidgetItem(str(result["loss_source"])))
        self.pathping_table.setItem(row, 4, QTableWidgetItem(str(result["loss_node"])))
        self.pathping_table.setItem(row, 5, QTableWidgetItem(result["status"]))
    # Метод для выполнения команды pathping
    def pathping_run(self):
        # Получение введенных пользователем данных
        ip = self.pathping_input.text().strip()
        if not ip:
            self.result_text_pathping.setText("Пожалуйста, введите IP-адрес или домен.")
            return
        hops = self.pathping_hops.value()
        queries = self.pathping_queries.value()
        period = self.pathping_period.value()
        timeout = self.pathping_timeout.value()
        self.pathping_table.setRowCount(0)  # Очистка таблицы перед новым запуском
        # Формирование команды pathping с указанными параметрами
        command = ["pathping", "-h", str(hops), "-q", str(queries), "-p", str(period), "-w", str(timeout)]
        if self.pathping_no_resolve.isChecked():
            command.append("-n")
        command.append(ip)
        # Максимальное время работы: трассировка (3 запроса на прыжок) + сбор статистики
        max_time = hops * (3 * timeout / 1000 + queries * period / 1000) + 30
        self.result_text_pathping.setText("Выполняется проверка, это может занять некоторое время...")
        QApplication.processEvents()  # Обновление окна, чтобы сообщение было видно
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=max_time, encoding='cp866', errors='replace')
            # Разделение вывода на строки и обработка каждой строки
            for output in result.stdout.splitlines():
                pathping_result = self.process_pathping_result(output)
                if pathping_result:
                    self.add_pathping_result(pathping_result)
            # Если в таблицу ничего не попало (например, узел не найден), показываем вывод pathping как есть
            if self.pathping_table.rowCount() == 0:
                self.result_text_pathping.setText(result.stdout)
                return
            # Вывод краткой статистики
            total_hops = self.pathping_table.rowCount()
            lost_hops = 0
            for row in range(total_hops):
                if self.pathping_table.item(row, 5).text() != "Норма":
                    lost_hops += 1
            self.result_text_pathping.setText(f"Всего узлов: {total_hops}\n"
                                              f"Узлов с потерями или без ответа: {lost_hops}")
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
window.resize(1200, 1000)
window.show()
sys.exit(app.exec())