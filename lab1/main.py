import sys
import math
import subprocess
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, 
                               QPushButton, QLineEdit, QHBoxLayout, QTextEdit, QFormLayout, QSpinBox, 
                               QTableWidget, QHeaderView, QTableWidgetItem, QCheckBox, QComboBox, QSplitter,
                               QFrame, QMessageBox, QGridLayout, QGraphicsView, QGraphicsScene)
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF, QProcess  # QProcess для интервального netstat
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QTextCursor  # Курсор для добавления вывода netstat
import re

# Класс для рисования графа
class GraphView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.gscene = QGraphicsScene(self)   # сцена
        self.setScene(self.gscene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)  # сглаживание линий
        self.points = []     # координаты узлов
        self.packet = None   # пакет
        self.progress = 0.0  # положение пакета внутри текущего отрезка
        self.segment = 0     # номер текущего отрезка маршрута
        self.route = []      # путь пакета
        self.timer = QTimer(self) #таймер
        self.timer.timeout.connect(self.move_packet)

    # Очистка графа
    def clear_graph(self):
        self.timer.stop() # отсановка анимации
        self.gscene.clear() # очистка графа
        self.points = [] # очистка списка координат
        self.packet = None # очищаем объект пакета

    # Добавление узла
    def add_node(self, pos, label, color, tip=""):
        # Отрисовка круга
        node = self.gscene.addEllipse(-22, -22, 44, 44, QPen(Qt.GlobalColor.black), QBrush(QColor(color)))
        node.setPos(pos) # устанавливаем объект на позицию
        node.setToolTip(tip)   # подсказка при наведении
        node.setZValue(1)      # узлы рисуются поверх линий
        text = self.gscene.addSimpleText(label) # создлание подписи
        text.setBrush(self.palette().text())  # цвет текста берётся из темы системы
        text.setPos(pos.x() - text.boundingRect().width() / 2, pos.y() + 26) # установка подписи на позицию

    # Добавление ребра между двумя точками
    def add_edge(self, a, b, color="#9e9e9e", label=""):
        self.gscene.addLine(a.x(), a.y(), b.x(), b.y(), QPen(QColor(color), 2)) # создание линии
        # Размещение подписи
        if label:
            text = self.gscene.addSimpleText(label)
            text.setBrush(self.palette().text())
            text.setPos((a.x() + b.x()) / 2, (a.y() + b.y()) / 2)

    # Подгонка масштаба
    def fit(self):
        rect = self.gscene.itemsBoundingRect().adjusted(-60, -60, 60, 60) # получаем прямоугольник который захватывает все элементы и расширяем его
        # Минимальный размер
        rect = rect.united(QRectF(rect.center().x() - 300, rect.center().y() - 150, 600, 300))
        self.setSceneRect(rect)
        #  Изменяет размер и сохраняет пропорции
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    # При изменении размера окна заново подгоняем масштаб
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    # Граф-цепочка для pathping
    def draw_path(self, nodes):
        self.clear_graph()
        for i in range(len(nodes)):
            row, col = divmod(i, 6) # по 6 узлов в строке
            # "змейка": нечётные строки идут справа налево
            if row % 2 == 1:
                col = 5 - col
            self.points.append(QPointF(col * 150, row * 120)) # расчёт координат
        # Соединение соседних узлов
        for i in range(len(self.points) - 1):
            self.add_edge(self.points[i], self.points[i + 1])
        for point, (label, color, tip) in zip(self.points, nodes): # одновременно перебираем несколько последовательностьей с помощью zip
            self.add_node(point, label, color, tip)
        self.fit()

    # Граф для netstat
    def draw_star(self, center_label, groups):
        self.clear_graph()
        if not groups:
            self.gscene.addText("Нет соединений для отображения.\nПопробуйте включить только параметр -a или параметр -a и -n.")
            self.fit()
            return
        # Сортировка узлов
        hosts = sorted(groups, key=lambda h: len(groups[h]), reverse=True)[:25]
        center = QPointF(0, 0)
        radius = 150 + 8 * len(hosts)
        for i, host in enumerate(hosts):
            angle = 2 * math.pi * i / len(hosts) # вычисление угла
            pos = QPointF(radius * math.cos(angle), radius * math.sin(angle)) # вычиление позиции
            lines = groups[host]
            # зелёное ребро, если есть установленное соединение
            color = "#4caf50" if any("ESTABLISHED" in l for l in lines) else "#9e9e9e"
            count = f"x{len(lines)}" if len(lines) > 1 else ""
            self.add_edge(center, pos, color, count)
            self.add_node(pos, host[:22], "#90a4ae", "\n".join(lines))
        self.add_node(center, center_label, "#2196f3")
        self.fit()

    # Запуск анимации
    def play(self):
        # Анимация невозможна если узлов меньше 2
        if len(self.points) < 2:
            return
        # Остановка и отчистка перед новым запуском
        self.timer.stop()
        if self.packet is not None:
            self.gscene.removeItem(self.packet)
        self.packet = self.gscene.addEllipse(-7, -7, 14, 14, QPen(Qt.GlobalColor.black), QBrush(QColor("#ffeb3b")))
        self.packet.setZValue(2)
        self.route = self.points + self.points[-2::-1] # туда и обратно
        # Установка начального состояния
        self.segment = 0
        self.progress = 0.0
        self.packet.setPos(self.route[0])
        self.timer.start(20) # шаг анимации каждые 20 мс

    # Один шаг анимации
    def move_packet(self):
        self.progress += 0.04
        if self.progress >= 1:
            self.progress = 0.0
            self.segment += 1
            if self.segment >= len(self.route) - 1:   # маршрут закончился
                self.packet.setPos(self.route[-1])
                self.timer.stop()
                return
        a = self.route[self.segment]
        b = self.route[self.segment + 1]
        self.packet.setPos(a + (b - a) * self.progress)

# Класс главного окна приложения
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.tabs = QTabWidget() # виджет вкладок
        self.setCentralWidget(self.tabs)
        # создание вкладок
        self.ping_tab = QWidget()
        self.ipconfig_tab = QWidget()
        self.pathping_tab = QWidget()
        self.netstat_tab = QWidget()
        self.tabs.addTab(self.ping_tab, "Ping")
        self.tabs.addTab(self.ipconfig_tab, "IPConfig")
        self.tabs.addTab(self.pathping_tab, "PathPing")
        self.tabs.addTab(self.netstat_tab, "NetStat")
        # вызов методов создания интерфейса вкладки
        self.create_ping_tab()
        self.create_ipconfig_tab()
        self.create_pathping_tab()
        self.create_netstat_tab()
# PING
# Метод для создания вкладки Ping
    def create_ping_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10) # отступы
        layout.setSpacing(10) # расстояние между элементами
        input_layout = QHBoxLayout()
        params_layout = QVBoxLayout()
        params_layout.setSpacing(8)
        # поле ввода
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
        # взаимоисключение параметров -t и -n
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
            # Объединяем чекбоксы и поля ввода в один виджет
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
        self.ping_table.verticalHeader().setVisible(False) # скрывает стандартную номерацию
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

        # установка компоновки на вкладку ping
        self.ping_tab.setLayout(layout)
# Метод для обработки одной строки вывода ping
    def process_ping_result(self, result):
        # извлечение ip
        ip_result = re.search(r"Ответ от (.+?): (.*)", result)
        if not ip_result:
            return None
        bytes_result = re.search(r"байт=(\d+)", result) # количество байтов
        time_result = re.search(r"время([=<])(\d+)", result) # время
        ttl_result = re.search(r"TTL=(\d+)", result) # TTL
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
        # неуспешный ответ
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
        row = self.ping_table.rowCount() # текущее количество строк
        self.ping_table.insertRow(row) # добавление строки по индексу
        self.ping_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        self.ping_table.setItem(row, 1, QTableWidgetItem(result["ip"]))
        self.ping_table.setItem(row, 2, QTableWidgetItem(str(result["bytes"]) if result["bytes"] is not None else "---"))
        self.ping_table.setItem(row, 3, QTableWidgetItem(result.get("time_display", str(result["time"]) if result["time"] is not None else "---")))
        self.ping_table.setItem(row, 4, QTableWidgetItem(str(result["ttl"]) if result["ttl"] is not None else "---"))
        self.ping_table.setItem(row, 5, QTableWidgetItem(result["status"]))
    # Метод для выполнения команды ping
    def ping_run(self):
        sent_count = 0 # количество отправленных запросов
        receive_count = 0 # количество успешных ответов
        total_time = 0 # сумма времени всех успешных ответов
        min_time = None # минимальное время
        max_time = None # максимальное время
        # Получение введенных пользователем данных
        ip = self.ip_input.text().strip()
        # проверка на пустую строку
        if not ip:
            self.result_text.setText("Пожалуйста, введите IP-адрес или домен.")
            return
        # провекра для маршрутизации для -j и -k
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
        # вывод комнады в консоль
        print("Команда: ", subprocess.list2cmdline(command))
        # изменения состояний кнопок
        self.button.setEnabled(False)
        self.stop_button.setEnabled(True)
        # полный вывод
        all_output = ""
        try:
            # выполнение команды
            self.ping_command = subprocess.Popen(command, stdout=subprocess.PIPE, text=True, encoding='cp866', errors='replace')
            route_lines = []
            time_lines = []
            block_name = ""
            get_name = None
            get_ip = None
            for output in self.ping_command.stdout:
                QApplication.processEvents() # обработка ожидающих событий
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
            # Среднее время рассчитывается по ответам и отсутствует при полной потере пакетов.
            average_time = f"{total_time / receive_count:.2f} мс" if receive_count else "---"
            statistic = (f"Отправлено: {sent_count}\n"
                         f"Получено: {receive_count}\n"
                         f"Потеряно: {lost_count}\n"
                         f"Процент потерь: {loss_percentage:.2f}%\n"
                         f"Минимальное время: {min_time if min_time is not None else '---'} мс\n"
                         f"Максимальное время: {max_time if max_time is not None else '---'} мс\n"
                         f"Среднее время: {average_time}")  # Единица измерения есть только у рассчитанного среднего.
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
        parametr_space = None # количество пробелов
        # разделяем текст на строки
        for adapter in result.splitlines():
            line = adapter.strip()
            spaces = len(adapter) - len(adapter.lstrip()) # подсчёт пробелов
            # проверяем является ли строка адаптером
            if (line.lower().startswith("адаптер ") or line.lower().startswith("неизвестный адаптер ")) and line.endswith(":"):
                # найден адаптер
                name = line[:-1] # имя адаптера
                current_adapter = {"name": name}
                adapters.append(current_adapter)
                last_key = None
                parametr_space = None
            # обработка остальных строк
            else:
                if parametr_space is None and ":" in line:
                    parametr_space = spaces # сохраняем пробелы
                # обработка параметров
                if spaces == parametr_space and current_adapter and ":" in line:
                    key, value = line.split(":", 1)
                    key = key.replace(".", "").strip()
                    current_adapter[key.strip()] = value.strip()
                    last_key = key.strip() # сохраняем параметр
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
            # создание вкладки полного вывода если её нет
            if self.adapter_tabs.indexOf(self.result_text_ipconfig) == -1:
                self.adapter_tabs.addTab(self.result_text_ipconfig, "Полный вывод")
            # формирование команды
            command_ipconfig = ["ipconfig"]
            parametr = self.ipconfig_mode.currentData() # получаем параметр
            # проверяем нужно ли добавлять параметр
            if parametr != "default":
                command_ipconfig.append(parametr)
            adapter = self.ipconfig_adapter_input.text().strip() # получаем имя адаптера
            classid = self.ipconfig_classid_input.text().strip() # получаем индетификатор класса DHCP
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
            # сообщение об опасности
            dunger = ["/flushdns", "/registerdns", "/release", "/renew", "/setclassid"]
            if parametr in dunger:
                answer = QMessageBox.question(self, "Подтверждение действия", 
                                              "Эта команда изменит сетевое состояние или настройки компьютера.\n"
                                              "Вы действительно хотите продолжить?", 
                                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                                              QMessageBox.StandardButton.No)
                if answer != QMessageBox.StandardButton.Yes:
                    return
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
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        input_layout = QHBoxLayout()
        params_layout = QVBoxLayout()
        params_layout.setSpacing(8)
        # строка ввода
        label = QLabel("IP-адрес или домен:")
        self.pathping_input = QLineEdit()
        self.pathping_input.setPlaceholderText("Введите IP-адрес или домен:")

        input_layout.addWidget(label)
        input_layout.addWidget(self.pathping_input)
        layout.addLayout(input_layout)

        # Максимальное число прыжков (-h)
        self.pathping_h = QSpinBox()
        self.pathping_h.setRange(1, 255)
        self.pathping_h.setValue(30)
        self.pathping_h_check = QCheckBox("Максимум прыжков (-h)")
        self.pathping_h.setEnabled(False)
        self.pathping_h_check.toggled.connect(self.pathping_h.setEnabled)

        # Число запросов на каждый узел (-q)
        self.pathping_q = QSpinBox()
        self.pathping_q.setRange(1, 1000)
        self.pathping_q.setValue(10)
        self.pathping_q_check = QCheckBox("Запросов на узел (-q)")
        self.pathping_q.setEnabled(False)
        self.pathping_q_check.toggled.connect(self.pathping_q.setEnabled)

        # Пауза между запросами (-p)
        self.pathping_p = QSpinBox()
        self.pathping_p.setRange(1, 10000)
        self.pathping_p.setValue(250)
        self.pathping_p_check = QCheckBox("Пауза между запросами (-p)")
        self.pathping_p.setEnabled(False)
        self.pathping_p_check.toggled.connect(self.pathping_p.setEnabled)

        # Время ожидания ответа (-w)
        self.pathping_timeout = QSpinBox()
        self.pathping_timeout.setRange(1, 10000)
        self.pathping_timeout.setValue(3000)
        self.pathping_timeout_check = QCheckBox("Таймаут (-w)")
        self.pathping_timeout.setEnabled(False)
        self.pathping_timeout_check.toggled.connect(self.pathping_timeout.setEnabled)

        # Свободный выбор маршрута (-g)
        self.pathping_g = QLineEdit()
        self.pathping_g.setPlaceholderText("IP-адреса узлов через пробел")
        self.pathping_g_check = QCheckBox("Свободный маршрут (-g)")
        self.pathping_g.setEnabled(False)
        self.pathping_g_check.toggled.connect(self.pathping_g.setEnabled)

        # Адрес исходного интерфейса (-i)
        self.pathping_i = QLineEdit()
        self.pathping_i.setPlaceholderText("Исходный IP-адрес")
        self.pathping_i_check = QCheckBox("Исходный адрес (-i)")
        self.pathping_i.setEnabled(False)
        self.pathping_i_check.toggled.connect(self.pathping_i.setEnabled)

        # Не определять имена узлов (-n)
        self.pathping_n = QCheckBox("Не определять имена узлов (-n)")

        # Использовать IPv4 (-4)
        self.pathping_4 = QCheckBox("Использовать IPv4 (-4)")

        # Использовать IPv6 (-6)
        self.pathping_6 = QCheckBox("Использовать IPv6 (-6)")

        # Взаимоисключение IPv4 и IPv6
        def toggle_pathping_ipv4(checked):
            self.pathping_6.setEnabled(not checked)
            if checked:
                self.pathping_6.setChecked(False)
        def toggle_pathping_ipv6(checked):
            self.pathping_4.setEnabled(not checked)
            if checked:
                self.pathping_4.setChecked(False)

        self.pathping_4.toggled.connect(toggle_pathping_ipv4)
        self.pathping_6.toggled.connect(toggle_pathping_ipv6)

        # Группировка чекбокса и поля ввода
        def group_param(checkbox, field):
            group = QWidget()
            group_layout = QHBoxLayout(group)
            group_layout.setContentsMargins(0, 0, 0, 0)
            group_layout.setSpacing(6)
            field.setFixedWidth(110)
            group_layout.addWidget(checkbox, 1)
            group_layout.addWidget(field)
            return group

        # Строка из двух параметров
        def make_row(c1, s1, c2, s2):
            row = QHBoxLayout()
            row.setSpacing(16)
            row.addWidget(group_param(c1, s1), 1)
            row.addWidget(group_param(c2, s2), 1)
            return row

        # Расположение параметров
        params_layout.addLayout(make_row(self.pathping_h_check, self.pathping_h, self.pathping_q_check, self.pathping_q))
        params_layout.addLayout(make_row(self.pathping_p_check, self.pathping_p, self.pathping_timeout_check, self.pathping_timeout))
        params_layout.addLayout(make_row(self.pathping_g_check, self.pathping_g, self.pathping_i_check, self.pathping_i))

        # Расположение флагов
        flags_row = QHBoxLayout()
        flags_row.addWidget(self.pathping_n, 1)
        flags_row.addWidget(self.pathping_4, 1)
        flags_row.addWidget(self.pathping_6, 1)
        params_layout.addLayout(flags_row)

        layout.addLayout(params_layout)

        # Кнопка запуска
        self.pathping_button = QPushButton("Проверить")
        self.pathping_button.clicked.connect(self.pathping_run)
        layout.addWidget(self.pathping_button)

        # Таблица результатов
        self.pathping_table = QTableWidget()
        self.pathping_table.setColumnCount(6)
        self.pathping_table.setHorizontalHeaderLabels([
            "Прыжок",
            "IP-адрес",
            "Время (мс)",
            "Потери до узла",
            "Потери на узле",
            "Результат"
        ])
        self.pathping_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.pathping_table.verticalHeader().setVisible(False)
        self.pathping_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.pathping_table)

        # вкладки статистики и полного результата
        self.result_tabs_pathping = QTabWidget()
        # статистика
        self.pathping_summary = QTextEdit()
        self.pathping_summary.setReadOnly(True)
        self.pathping_summary.setPlaceholderText("Краткая статистика появится после проверки.")
        # полный вывод
        self.result_text_pathping = QTextEdit()
        self.result_text_pathping.setReadOnly(True)
        self.result_text_pathping.setPlaceholderText("Полный вывод команды pathping.")
        # расположенеи вкладок в интерфейсе
        self.result_tabs_pathping.addTab(self.pathping_summary, "Краткая статистика")
        self.result_tabs_pathping.addTab(self.result_text_pathping, "Полный вывод")

        # вкладка с графом маршрута
        self.pathping_graph = GraphView()
        self.pathping_graph.setMinimumHeight(250)
        graph_tab = self.make_graph_tab(
            self.pathping_graph,
            "Зелёный узел - норма, оранжевый - есть потери, красный - нет ответа, синий - этот компьютер. "
            "Жёлтая точка - пакет.",
            play_button=True)
        self.result_tabs_pathping.addTab(graph_tab, "Граф маршрута")
        layout.addWidget(self.result_tabs_pathping)

        self.pathping_tab.setLayout(layout)

    # Метод для обработки одной строки вывода pathping
    def process_pathping_result(self, result):
        stat_result = re.search(
            r"^\s*(\d+)\s+(?:(<\s*\d+|\d+)\s*мс|[-*]+)\s+"
            r"(\d+)\s*/\s*(\d+)\s*=\s*(\d+)%\s+"
            r"(\d+)\s*/\s*(\d+)\s*=\s*(\d+)%\s*(.*?)\s*$",
            result
        )

        if not stat_result:
            return None

        # Количество потерянных и отправленных пакетов от источника
        lost_source_count = int(stat_result.group(3))
        sent_source_count = int(stat_result.group(4))
        loss_source = int(stat_result.group(5))

        # Количество потерянных и отправленных пакетов на узле
        lost_node_count = int(stat_result.group(6))
        sent_node_count = int(stat_result.group(7))
        loss_node = int(stat_result.group(8))

        # Сохранение времени в исходном виде
        time_result = stat_result.group(2)
        if time_result:
            time_result = time_result.replace(" ", "")

        # Определение состояния узла
        if loss_node == 100:
            status = "Нет ответа"
        elif loss_node > 0 or loss_source > 0:
            status = "Есть потери"
        else:
            status = "Норма"
        # формирование словаря
        return {
            "hop": int(stat_result.group(1)),
            "ip": stat_result.group(9).strip() or f"Узел {stat_result.group(1)}",
            "time": time_result,
            "loss_source": loss_source,
            "loss_node": loss_node,
            "lost_source_count": lost_source_count,
            "sent_source_count": sent_source_count,
            "lost_node_count": lost_node_count,
            "sent_node_count": sent_node_count,
            "status": status
        }

    # Метод для добавления результата pathping в таблицу
    def add_pathping_result(self, result):
        row = self.pathping_table.rowCount()
        self.pathping_table.insertRow(row)

        # Формирование статистики потерь от источника
        if result["loss_source"] is not None:
            source_loss = (
                f'{result["lost_source_count"]}/'
                f'{result["sent_source_count"]} '
                f'({result["loss_source"]}%)'
            )
        else:
            source_loss = "---"

        # Формирование статистики потерь на узле
        if result["loss_node"] is not None:
            node_loss = (
                f'{result["lost_node_count"]}/'
                f'{result["sent_node_count"]} '
                f'({result["loss_node"]}%)'
            )
        else:
            node_loss = "---"
        # прыжок
        self.pathping_table.setItem(
            row, 0, QTableWidgetItem(str(result["hop"]))
        )
        # ip
        self.pathping_table.setItem(
            row, 1, QTableWidgetItem(result["ip"])
        )
        # время
        self.pathping_table.setItem(
            row, 2, QTableWidgetItem(
                result["time"] if result["time"] is not None else "---"
            )
        )
        # потери до узла
        self.pathping_table.setItem(
            row, 3, QTableWidgetItem(source_loss)
        )
        # потери на узле
        self.pathping_table.setItem(
            row, 4, QTableWidgetItem(node_loss)
        )
        # результат
        self.pathping_table.setItem(
            row, 5, QTableWidgetItem(result["status"])
        )

    # Метод для выполнения команды pathping
    def pathping_run(self):
        # получение введенных пользователем данных
        ip = self.pathping_input.text().strip()
        # проверка на ввод ip
        if not ip:
            self.result_text_pathping.setText("Пожалуйста, введите IP-адрес или домен.")
            return
        # формирование команды pathping с указанными параметрами
        command = ["pathping"]
        # (-h)
        if self.pathping_h_check.isChecked():
            command.extend(["-h", str(self.pathping_h.value())])
        # (-q)
        if self.pathping_q_check.isChecked():
            command.extend(["-q", str(self.pathping_q.value())])
        # (-p)
        if self.pathping_p_check.isChecked():
            command.extend(["-p", str(self.pathping_p.value())])
        # (-w)
        if self.pathping_timeout_check.isChecked():
            command.extend(["-w", str(self.pathping_timeout.value())])
        # (-g)
        if self.pathping_g_check.isChecked():
            route = self.pathping_g.text().strip()
            if not route:
                self.pathping_summary.setText("Укажите список промежуточных узлов для параметра -g")
                return
            command.extend(["-g", " ".join(route.split())])
        # (-i)
        if self.pathping_i_check.isChecked():
            source = self.pathping_i.text().strip()
            if not source:
                self.pathping_summary.setText("Укажите исходный IP-адрес для параметра (-i)")
                return
            command.extend(["-i", source])
        # (-n)
        if self.pathping_n.isChecked():
            command.append("-n")
        # (-4)
        if self.pathping_4.isChecked():
            command.append("-4")
        # (-6)
        if self.pathping_6.isChecked():
            command.append("-6")
        # ip
        command.append(ip)

        # подготовка интерфейса
        self.pathping_table.setRowCount(0)
        self.pathping_graph.clear_graph()
        self.pathping_summary.setText("Выполняется проверка, это может занять некоторое время...")
        self.result_text_pathping.clear()
        QApplication.processEvents()  # обновление окна, чтобы сообщение было видно

        try:
            # запуск команды
            result = subprocess.run(command, capture_output=True, text=True, encoding='cp866', errors='replace')
            # Словарь результатов, ключом является номер перехода
            hops = {}
            # Флаг первой фазы выполнения pathping
            tracing = True
            # Разделение вывода на строки
            for output in result.stdout.splitlines():
                # Определение завершения первой фазы
                if re.search(r"Подсч[её]т статистики", output, re.IGNORECASE):
                    tracing = False
                # Обработка итоговой статистики
                pathping_result = self.process_pathping_result(output)
                if pathping_result:
                    hop = pathping_result["hop"]
                    hops[hop] = pathping_result
                    tracing = False
                    continue
                # Обработка первой фазы — трассировки маршрута
                if tracing:
                    route_result = re.match(
                        r"^\s*(\d+)\s+(.+?)\s*$",
                        output
                    )
                    if route_result:
                        hop = int(route_result.group(1))
                        address = route_result.group(2).strip()
                        # Нулевой переход — текущий компьютер
                        if hop == 0:
                            continue
                        # Проверка отсутствия ответа от узла
                        if re.fullmatch(r"(?:\*\s*)+", address):
                            address = f"Узел {hop}"
                            status = "Нет ответа"
                        else:
                            status = "Нет статистики"
                        # Сохраняем обнаруженный переход
                        hops[hop] = {
                            "hop": hop,
                            "ip": address,
                            "time": None,
                            "loss_source": None,
                            "loss_node": None,
                            "lost_source_count": None,
                            "sent_source_count": None,
                            "lost_node_count": None,
                            "sent_node_count": None,
                            "status": status
                        }
            # Добавление результатов в порядке следования узлов
            for hop in sorted(hops):
                self.add_pathping_result(hops[hop])
            # сохранение полного вывода
            full_output = result.stdout
            if result.stderr:
                full_output += "\n\nОШИБКА:\n" + result.stderr
            self.result_text_pathping.setPlainText(full_output if full_output else "Команда не вернула текстовый вывод")
            # Вывод краткой статистики
            total_hops = self.pathping_table.rowCount()
            if total_hops == 0:
                self.pathping_summary.setText(
                    "Не удалось получить информацию о маршруте"
                )
            else:
                normal_hops = 0
                lost_hops = 0
                no_answer_hops = 0
                no_stat_hops = 0

                for row in range(total_hops):
                    status = self.pathping_table.item(row, 5).text()
                    if status == "Норма":
                        normal_hops += 1
                    elif status == "Есть потери":
                        lost_hops += 1
                    elif status == "Нет ответа":
                        no_answer_hops += 1
                    elif status == "Нет статистики":
                        no_stat_hops += 1
                summary = (
                    f"Всего переходов: {total_hops}\n"
                    f"Узлов без обнаруженных потерь: {normal_hops}\n"
                    f"Узлов с обнаруженными потерями: {lost_hops}\n"
                    f"Узлов без ответа: {no_answer_hops}\n"
                    f"Узлов без статистики: {no_stat_hops}"
                )
                # Проверка достижения конечного узла
                target_match = re.search(
                    r"Трассировка маршрута к\s+([^\r\n]+)",
                    result.stdout
                )
                target = target_match.group(1).strip() if target_match else ip
                def extract_address(address):
                    match = re.search(r"\[([^\]]+)\]", address)
                    if match:
                        return match.group(1).strip().lower()
                    return address.strip().lower()

                last_node = hops[max(hops)]

                if extract_address(last_node["ip"]) != extract_address(target):
                    summary += (
                        "\n\nМаршрут исследован не полностью."
                        "\nДостижение конечного узла не подтверждено."
                    )
                elif last_node["loss_source"] is None:
                    summary += (
                        "\n\nКонечный узел обнаружен,"
                        " но статистика для него не получена."
                    )

                self.pathping_summary.setText(summary)

            self.result_tabs_pathping.setCurrentIndex(0)
            self.draw_pathping_graph()
            # если в таблицу ничего не попало
            if self.pathping_table.rowCount() == 0:
                self.result_text_pathping.setText(result.stdout)
                return
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

        param_layout = QGridLayout() # размещение ввиде сетки

        # размещение параметров
        self.netstat_a = QCheckBox("-a (Все соединения)")
        self.netstat_e = QCheckBox("-e (Статистика Ethernet)")
        self.netstat_n = QCheckBox("-n (Числовой формат)")
        self.netstat_s = QCheckBox("-s (Статистика протоколов)")
        self.netstat_r = QCheckBox("-r (Таблица маршрутов)")
        self.netstat_o = QCheckBox("-o (PID процессов)")

        param_layout.addWidget(self.netstat_a, 0, 0)
        param_layout.addWidget(self.netstat_e, 0, 1)
        param_layout.addWidget(self.netstat_n, 1, 0)
        param_layout.addWidget(self.netstat_s, 1, 1)
        param_layout.addWidget(self.netstat_r, 2, 0)
        param_layout.addWidget(self.netstat_o, 2, 1)

        layout.addLayout(param_layout)

        # выбор протокола
        protocol_layout = QHBoxLayout()
        protocol_layout.addWidget(QLabel("Протокол (-p):"))  # «Все протоколы» оставляет команду без -p.
        self.netstat_protocol = QComboBox()
        self.netstat_protocol.addItems(["Все протоколы", "TCP", "UDP", "IP", "ICMP"])
        protocol_layout.addWidget(self.netstat_protocol)

        layout.addLayout(protocol_layout)

        # интервал
        # Нулевой интервал означает разовый вывод
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Интервал обновления (0 — один раз):"))
        self.netstat_interval = QSpinBox()
        self.netstat_interval.setRange(0, 3600)
        self.netstat_interval.setSuffix(" с") # добавление единицы измерения
        interval_layout.addWidget(self.netstat_interval)
        layout.addLayout(interval_layout)

        # Кнопки запуска и остановки
        button_layout = QHBoxLayout()
        self.netstat_button = QPushButton("Получить информацию")
        self.netstat_button.clicked.connect(self.netstat_run)
        self.netstat_stop_button = QPushButton("Остановить")
        button_layout.addWidget(self.netstat_button)
        button_layout.addWidget(self.netstat_stop_button)
        layout.addLayout(button_layout)

        self.result_text_netstat = QTextEdit()
        self.result_text_netstat.setReadOnly(True)
        self.netstat_graph = GraphView()
        self.netstat_tabs = QTabWidget()
        self.netstat_tabs.addTab(self.result_text_netstat, "Вывод")
        self.netstat_tabs.addTab(
            self.make_graph_tab(self.netstat_graph,
                                "Зелёная линия - есть соединение ESTABLISHED, серая - остальные состояния. "
                                "Наведите курсор на узел, чтобы увидеть порты и состояния."),
            "Граф соединений")
        layout.addWidget(self.netstat_tabs)

        self.netstat_tab.setLayout(layout)

        # С интервалом netstat работает до остановки, поэтому читаем его вывод через Qt
        # Создание QProcess
        self.netstat_process = QProcess(self)
        self.netstat_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels) # объединение потоков
        # Подключение трех обработчиков событий
        self.netstat_process.readyReadStandardOutput.connect(self.read_netstat_output) # при появление новых данных автоматически их читатет
        self.netstat_process.errorOccurred.connect(self.netstat_interval_error) # при поялвение ошибок
        self.netstat_process.stateChanged.connect(self.update_netstat_fields) # при изменение состояния
        self.netstat_stop_button.clicked.connect(self.netstat_process.kill) # остановка через kill
        self.netstat_s.toggled.connect(self.update_netstat_fields)  # обновляем допустимые протоколы при смене режима
        self.update_netstat_fields()
    # Обновление поля протокола и кнопок netstat.
    def update_netstat_fields(self):
        # IP и ICMP доступны только при запросе статистики, TCP и UDP доступны и без -s.
        statistics = self.netstat_s.isChecked()
        for index in (self.netstat_protocol.findText("IP"), self.netstat_protocol.findText("ICMP")):
            self.netstat_protocol.model().item(index).setEnabled(statistics)
        if not statistics and self.netstat_protocol.currentText() in ("IP", "ICMP"):
            self.netstat_protocol.setCurrentIndex(0)

        # Пока идёт обновление, можно остановить текущий запуск.
        running = self.netstat_process.state() != QProcess.ProcessState.NotRunning # получаем статус
        # Определяем доступность кнопок в зависимости от состояния
        self.netstat_button.setEnabled(not running)
        self.netstat_stop_button.setEnabled(running)
    # Метод для выполнения команды netstat
    def netstat_run(self):
        try:
            # формирование команды netstat
            command = ["netstat"]
            # -a
            if self.netstat_a.isChecked():
                command.append("-a")
            # -e
            if self.netstat_e.isChecked():
                command.append("-e")
            # -n
            if self.netstat_n.isChecked():
                command.append("-n")
            # -s
            if self.netstat_s.isChecked():
                command.append("-s")
            # -r
            if self.netstat_r.isChecked():
                command.append("-r")
            # -o
            if self.netstat_o.isChecked():
                command.append("-o")
            # -p фильтрует соединения без -s и статистику вместе с -s
            protocol = self.netstat_protocol.currentText()
            if protocol != "Все протоколы":
                command.extend(["-p", protocol])
            # Положительный интервал передаётся последним аргументом в секундах
            interval = self.netstat_interval.value() # получаем значение интервала
            if interval:
                self.result_text_netstat.clear() # очистка текстового поля
                self.draw_netstat_graph("")  # сбрасываем граф перед получением первого списка
                self.netstat_graph_output = ""  # текст текущего списка соединений для графа
                # Запуск команды через start
                self.netstat_process.start(command[0], command[1:] + [str(interval)])
                # Завершаем метод
                return
            # Разовый вызов
            result = subprocess.run(command, capture_output=True, text=True, timeout=360, encoding='cp866', errors='replace')
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
            if result.returncode != 0:
                self.result_text_netstat.setPlainText(f"Ошибка выполнения программы:\n{output}")
            else:
                self.result_text_netstat.setPlainText(output) # вывод
            self.draw_netstat_graph(output) # отрисовка графа
        except subprocess.TimeoutExpired:
            self.result_text_netstat.setText("Превышено время ожидания.")
        except Exception as error:
            self.result_text_netstat.setText(f"Ошибка: {error}")

    # Добавление интервального вывода и обновление графа по последнему списку соединений
    def read_netstat_output(self):
        output = bytes(self.netstat_process.readAllStandardOutput()).decode("cp866", errors="replace").replace("\r", "")
        # Записываем вывод в конец
        self.result_text_netstat.moveCursor(QTextCursor.MoveOperation.End)
        self.result_text_netstat.insertPlainText(output)
        # Новый заголовок начинает список заново. Сохраняем его на случай, если таблица придёт частями
        sections = re.split(
            r"(?m)(?=^[ \t]*Активные подключения[ \t]*\n)",
            self.netstat_graph_output + output
        )
        if len(sections) > 1:
            self.netstat_graph_output = sections[-1]
            self.draw_netstat_graph(self.netstat_graph_output)
        else:
            # Без таблицы сохраняем только незавершённую строку для поиска заголовка
            self.netstat_graph_output = sections[0].rsplit("\n", 1)[-1]

    # Ошибка запуска команды в интервальном режиме
    def netstat_interval_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.result_text_netstat.setPlainText(f"Ошибка запуска netstat: {self.netstat_process.errorString()}")
# ГРАФЫ
    # Вкладка с графом
    def make_graph_tab(self, graph, legend, play_button=False):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.addWidget(graph, 1)
        if play_button:
            button = QPushButton("Показать движение пакета")
            button.clicked.connect(graph.play)
            layout.addWidget(button)
        legend_label = QLabel(legend)
        legend_label.setWordWrap(True)
        layout.addWidget(legend_label)
        return tab

    # Построение графа маршрута по уже заполненной таблице pathping
    def draw_pathping_graph(self):
        if self.pathping_table.rowCount() == 0:
            return
        colors = {
            "Норма": "#4caf50",
            "Есть потери": "#ff9800",
            "Нет ответа": "#f44336",
            "Нет статистики": "#9e9e9e"
        }
        nodes = [("Этот компьютер", "#2196f3", "")]
        for row in range(self.pathping_table.rowCount()):
            ip = self.pathping_table.item(row, 1).text()
            # Если указано "имя [адрес]", показываем только адрес
            if "[" in ip and "]" in ip:
                ip = ip[ip.find("[") + 1: ip.find("]")]
            status = self.pathping_table.item(row, 5).text()
            tip = (
                f"Прыжок {self.pathping_table.item(row, 0).text()}\n"
                f"Время: {self.pathping_table.item(row, 2).text()} мс\n"
                f"Потери до узла: {self.pathping_table.item(row, 3).text()}\n"
                f"Потери на узле: {self.pathping_table.item(row, 4).text()}\n"
                f"Состояние: {status}"
            )
            nodes.append((ip, colors[status], tip))
        self.pathping_graph.draw_path(nodes)

    # Построение графа соединений из вывода netstat
    def draw_netstat_graph(self, output):
        groups = {}  # удалённый хост -> список соединений с ним
        for line in output.splitlines():
            # строка вида: TCP  192.168.1.5:50123  142.250.1.1:443  ESTABLISHED
            match = re.match(r"^\s*(TCP|UDP)\s+\S+:\S+\s+(\S+):(\S+)\s*(\S*)", line)
            if not match:
                continue
            protocol, host, port, state = match.groups()
            if host in ("0.0.0.0", "*", "[::]"):   # слушающие порты, удалённого узла нет
                continue
            groups.setdefault(host, []).append(f"{protocol} порт {port} {state}".strip())
        self.netstat_graph.draw_star("Этот компьютер", groups)
# Запуска приложения
app = QApplication(sys.argv)
window = MainWindow()
window.setWindowTitle("Network Analyzer")
window.resize(1200, 1000)
window.show()
# для теста
# window.pathping_graph.draw_path([
#     ("Этот компьютер", "#2196f3", ""),
#     ("192.168.1.1", "#4caf50", "Роутер"),
#     ("Узел 2", "#f44336", "Не отвечает"),
#     ("172.27.0.109", "#4caf50", ""),
#     ("172.27.0.85", "#4caf50", ""),
#     ("85.175.221.233", "#4caf50", ""),
#     ("Узел 6", "#f44336", "Не отвечает"),
#     ("173.194.121.4", "#ff9800", "Есть потери"),
#     ("142.250.236.117", "#4caf50", ""),
#     ("142.251.48.45", "#4caf50", ""),
#     ("dns.google", "#4caf50", "Цель 8.8.8.8"),
# ])
sys.exit(app.exec())