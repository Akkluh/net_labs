import sys
import subprocess
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, 
                               QPushButton, QLineEdit, QHBoxLayout, QTextEdit, QFormLayout, QSpinBox, 
                               QTableWidget, QHeaderView, QTableWidgetItem, QCheckBox, QComboBox, QSplitter,
                               QFrame)
from PySide6.QtCore import Qt
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

        # кнопки
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

        # функции для интерфейса
        def group_param(checkbox, spinbox): # группировка чекбоксов и счётчиков
            group = QWidget()
            group_layout = QHBoxLayout(group)
            group_layout.setContentsMargins(0, 0, 0, 0)
            group_layout.setSpacing(6)
            spinbox.setFixedWidth(90)
            group_layout.addWidget(checkbox, 1)
            group_layout.addWidget(spinbox)
            return group
        def make_row(c1, s1, c2, s2): # создание строки из двух параметров
            row = QHBoxLayout()
            row.setSpacing(16)
            row.addWidget(group_param(c1, s1), 1)
            row.addWidget(group_param(c2, s2), 1)
            return row

        # интерфейс
        params_layout.addLayout(make_row(self.ping_count_check, self.ping_count, self.ping_size_check, self.ping_size))
        params_layout.addLayout(make_row(self.ping_timeout_check, self.ping_timeout, self.ping_ttl_check, self.ping_ttl))
        params_layout.addLayout(make_row(self.ping_s, self.ping_s_count, self.ping_r, self.ping_r_count))
        flags_row = QHBoxLayout()
        flags_row.addWidget(self.ping_dont_fragment, 1)
        flags_row.addWidget(self.ping_get_name, 1)
        flags_row.addWidget(self.ping_t, 1)
        params_layout.addLayout(flags_row)
        route_row = QHBoxLayout()
        route_label = QLabel("Маршрут через узлы (-j/-k)")
        route_row.addWidget(route_label)
        route_row.addWidget(self.ping_route_type, 1)
        route_row.addWidget(self.ping_line_for_route, 1)
        params_layout.addLayout(route_row)
        layout.addLayout(params_layout)
        button_row = QHBoxLayout()
        button_row.addWidget(self.button, 1)
        button_row.addWidget(self.stop_button, 1)
        layout.addLayout(button_row)

        # таблица
        self.ping_table = QTableWidget()
        self.ping_table.setColumnCount(6)
        self.ping_table.setHorizontalHeaderLabels(["№", "IP-адрес", "Байты", "Время (мс)", "TTL", "Результат"])
        self.ping_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ping_table.verticalHeader().setVisible(False)
        self.ping_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # дополнительное поле вывода
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFrameShape(QFrame.Shape.Box)
        self.result_text.setLineWidth(1)

        # разделитель между таблицей и полем вывода
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.ping_table)
        splitter.addWidget(self.result_text)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter, 1)

        self.ping_tab.setLayout(layout)
# Метод для обработки одной строки вывода ping
    def process_ping_result(self, result):
        ip_result = re.search(r"Ответ от (.+?): (.*)", result)
        if not ip_result:
            return None
        bytes_result = re.search(r"байт=(\d+)", result)
        time_result = re.search(r"время([=<])(\d+)", result)
        ttl_result = re.search(r"TTL=(\d+)", result)
        # Успешный ответ: есть и байты, и время, и TTL
        if bytes_result and time_result and ttl_result:
            time_value = int(time_result.group(2))
            if time_result.group(1) == "<":
                time_value = 0
                time_display = "<1"
            else:
                time_display = str(time_value)
            return {
                "ip": ip_result.group(1),
                "bytes": int(bytes_result.group(1)),
                "time": time_value,
                "time_display": time_display,
                "ttl": int(ttl_result.group(1)),
                "status": "Успешно"
            }
        return {
            "ip": ip_result.group(1),
            "bytes": None,
            "time": None,
            "time_display": "---",
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
        self.ping_table.setItem(row, 3, QTableWidgetItem(result.get("time_display", str(result["time"]) if result["time"] is not None else "---")))
        self.ping_table.setItem(row, 4, QTableWidgetItem(str(result["ttl"]) if result["ttl"] is not None else "---"))
        self.ping_table.setItem(row, 5, QTableWidgetItem(result["status"]))
    # Метод для выполнения команды ping
    def ping_run(self):
        sent_count = 0
        receive_count = 0
        total_time = 0
        min_time = None
        max_time = None
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
        self.ping_table.setRowCount(0)  # Очистка таблицы перед новым запуском
        # Формирование команды ping с указанными параметрами
        command = ["ping"]
        # -n
        if self.ping_count_check.isChecked() and not self.ping_t.isChecked():
            command.extend(["-n", str(self.ping_count.value())])
        # -l
        if self.ping_size_check.isChecked():
            command.extend(["-l", str(self.ping_size.value())])
        # -w
        if self.ping_timeout_check.isChecked():
            command.extend(["-w", str(self.ping_timeout.value())])
        # -i
        if self.ping_ttl_check.isChecked():
            command.extend(["-i", str(self.ping_ttl.value())])
        # -t
        if self.ping_t.isChecked():
            command.append("-t")
        # -f
        if self.ping_dont_fragment.isChecked():
            command.append("-f")
        # -a
        if self.ping_get_name.isChecked():
            command.append("-a")
        # -r
        if self.ping_r.isChecked():
            command.extend(["-r", str(self.ping_r_count.value())])
        # -s
        if self.ping_s.isChecked():
            command.extend(["-s", str(self.ping_s_count.value())])
        # -j/-k
        if route_type == 1:
            command.extend(["-j", *route_hosts.split()])
        if route_type == 2:
            command.extend(["-k", *route_hosts.split()])
        # добавление адреса
        command.append(ip)
        print("Команда: ", subprocess.list2cmdline(command))
        self.button.setEnabled(False)
        self.stop_button.setEnabled(True)
        all_output = ""
        try:
            self.ping_command = subprocess.Popen(command, stdout=subprocess.PIPE, text=True, encoding='cp866', errors='replace')
            route_lines = []
            time_lines = []
            block_name = ""
            get_name = None
            get_ip = None
            for output in self.ping_command.stdout:
                QApplication.processEvents()
                all_output += output
                print("Полученная строка:", repr(output))
                name_match = re.search(r"Обмен пакетами с\s+(.+?)\s+\[(.+?)\]", output)
                if name_match:
                    get_name = name_match.group(1).strip()
                    get_ip = name_match.group(2).strip()
                self.ping_table.scrollToBottom()
                if "Маршрут:" in output and not route_lines:
                    block_name = "route"
                    route_lines = []
                elif "Отметка времени:" in output and not time_lines:
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

                # обработка результата ping
                ping_result = self.process_ping_result(output)
                if ping_result:
                    sent_count += 1
                    if get_name and ping_result["ip"] == get_ip:
                        ping_result["ip"] = f"{get_name} ({get_ip})"
                    self.add_ping_result(ping_result)
                    if ping_result["status"] == "Успешно":
                        receive_count += 1
                        paket_time = ping_result["time"]
                        total_time += paket_time
                        if min_time is None or paket_time < min_time:
                            min_time = paket_time
                        if max_time is None or paket_time > max_time:
                            max_time = paket_time
                elif "Превышен интервал ожидания" in output:
                    sent_count += 1
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
            lost_count = sent_count - receive_count
            if sent_count > 0:
                loss_percentage = (lost_count/sent_count)*100
            else:
                loss_percentage = 0
            if receive_count > 0:
                average_time = total_time/receive_count
            else:
                average_time = 0
            statistic = (f"Отправлено: {sent_count}\n"
                         f"Получено: {receive_count}\n"
                         f"Потеряно: {lost_count}\n"
                         f"Процент потерь: {loss_percentage:.2f}%\n"
                         f"Минимальное время: {min_time if min_time is not None else '---'} мс\n"
                         f"Максимальное время: {max_time if max_time is not None else '---'} мс\n"
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

        # выбор параметра
        layout.addWidget(QLabel("Режим работы: "))
        self.ipconfig_mode = QComboBox()
        self.ipconfig_mode.addItem("Основная информация", "default")
        self.ipconfig_mode.addItem("Полная информация (/all)", "/all")
        self.ipconfig_mode.addItem("Кэш DNS (/displaydns)", "/displaydns")
        self.ipconfig_mode.addItem("Очистка DNS-кэша (/flushdns)", "/flushdns")
        self.ipconfig_mode.addItem("Регистрация DNS (/registerdns)", "/registerdns")
        self.ipconfig_mode.addItem("Освобождение IP-адреса (/release)", "/release")
        self.ipconfig_mode.addItem("Обновление IP-адреса (/renew)", "/renew")
        self.ipconfig_mode.addItem("Просмотр класса DHCP (/showclassid)", "/showclassid")
        self.ipconfig_mode.addItem("Установка класса DHCP (/setclassid)", "/setclassid")
        layout.addWidget(self.ipconfig_mode)

        # поле для указания адаптера
        self.ipconfig_label = QLabel("Имя сетевого адаптера:")
        self.ipconfig_adapter_input = QLineEdit()
        self.ipconfig_adapter_input.setPlaceholderText("Например, Ethernet")
        layout.addWidget(self.ipconfig_label)
        layout.addWidget(self.ipconfig_adapter_input)

        # поле для указания DHCP class ID
        self.ipconfig_label2 = QLabel("Индетификатор класса DHCP:")
        self.ipconfig_classid_input = QLineEdit()
        self.ipconfig_classid_input.setPlaceholderText("Введите Class ID")
        layout.addWidget(self.ipconfig_label2)
        layout.addWidget(self.ipconfig_classid_input)

        # отслеживание изменения режима
        self.ipconfig_mode.currentIndexChanged.connect(self.update_ipconfig_fields)
        # первоначальное настройка видимости
        self.update_ipconfig_fields()

        # кнопка
        button = QPushButton("Получить информацию о сети")
        button.clicked.connect(self.ipconfig_run)
        layout.addWidget(button)

        # вкладки
        self.adapter_tabs = QTabWidget()
        # вкладка общего вывода
        self.result_text_ipconfig = QTextEdit()
        self.result_text_ipconfig.setReadOnly(True)
        # self.adapter_tabs.addTab(self.result_text_ipconfig, "Полный вывод")
        # размещение вкладок
        layout.addWidget(self.adapter_tabs)

        self.ipconfig_tab.setLayout(layout)
    # функция для обновления видимости полей ввода
    def update_ipconfig_fields(self):
        parametr = self.ipconfig_mode.currentData()
        adapter_mods = ["/release", "/renew", "/showclassid", "/setclassid"]
        self.ipconfig_label.setVisible(parametr in adapter_mods)
        self.ipconfig_adapter_input.setVisible(parametr in adapter_mods)
        self.ipconfig_label2.setVisible(parametr == adapter_mods[-1])
        self.ipconfig_classid_input.setVisible(parametr == adapter_mods[-1])

    # Метод для обработки результата ipconfig
    def process_ipconfig_result(self, result):
        adapters = [] # список всех адаптеров
        current_adapter = {} # словарь с информацией об адаптере
        last_key = None # последний параметр
        parametr_space = None
        for adapter in result.splitlines():
            line = adapter.strip()
            spaces = len(adapter) - len(adapter.lstrip()) # подсчёт пробелов
            if (line.lower().startswith("адаптер ") or line.lower().startswith("неизвестный адаптер ")) and line.endswith(":"):
                # найден адаптер
                name = line[:-1]
                current_adapter = {"name": name}
                adapters.append(current_adapter)
                last_key = None
                parametr_space = None
            else:
                if parametr_space is None and ":" in line:
                    parametr_space = spaces
                # обработка параметров
                if spaces == parametr_space and current_adapter:
                    key, value = line.split(":", 1)
                    key = key.replace(".", "").strip()
                    current_adapter[key.strip()] = value.strip()
                    last_key = key.strip()
                # обработка параметров на следующей строке
                elif parametr_space is not None and spaces > parametr_space and current_adapter and last_key:
                    current_adapter[last_key] += ", " + line.strip()
                elif not line:
                    continue
        return adapters
    # Метод для отображения результатов ipconfig
    def display_ipconfig_result(self, adapters, result):
        self.adapter_tabs.clear() # очистка вкладок
        # вкладка полного вывода
        self.result_text_ipconfig.setPlainText(result)
        self.adapter_tabs.addTab(self.result_text_ipconfig, "Полный вывод")
        # создание вкладок для каждого адаптера
        for adapter in adapters:
            tab = QWidget()
            layout = QVBoxLayout()
            # прижимаем к верху
            layout.setAlignment(Qt.AlignmentFlag.AlignTop)
            # вывод параметров адаптера
            for key, value in adapter.items():
                if key != "name":
                    label = QLabel(f"{key}: {value}")
                    layout.addWidget(label)
            tab.setLayout(layout)
            self.adapter_tabs.addTab(tab, adapter["name"])
    # Метод для выполнения команды ipconfig
    def ipconfig_run(self):
        try:
            if self.adapter_tabs.indexOf(self.result_text_ipconfig) == -1:
                self.adapter_tabs.addTab(self.result_text_ipconfig, "Полный вывод")
            # формирование команды
            command_ipconfig = ["ipconfig"]
            parametr = self.ipconfig_mode.currentData() # получаем параметр
            # проверяем нужно ли добавлять параметр
            if parametr != "default":
                command_ipconfig.append(parametr)
            adapter = self.ipconfig_adapter_input.text().strip()
            classid = self.ipconfig_classid_input.text().strip()
            # проверяем обязателен ли ввод адаптера
            if parametr in ["/showclassid", "/setclassid"] and not adapter:
                self.result_text_ipconfig.setText("Необходимо указать имя сетевого адаптера")
                return
            # добавлеям адаптер если он есть
            if parametr in ["/release", "/renew", "/showclassid", "/setclassid"]:
                if adapter:
                    command_ipconfig.append(adapter)
            # добавляем class id если он есть
            if parametr == "/setclassid" and classid:
                command_ipconfig.append(classid)
            # запускаем команду   
            result = subprocess.run(command_ipconfig, capture_output=True, text=True, timeout=15, encoding='cp866', errors='replace')
            output = result.stdout + result.stderr
            # проверяем нужно ли создавать вкладки для адаптеров
            if parametr == "default" or parametr == "/all":
                adapters = self.process_ipconfig_result(output)
            else:
                adapters = []
            self.display_ipconfig_result(adapters, output)
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