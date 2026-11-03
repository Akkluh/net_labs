import sys
import subprocess
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QHBoxLayout, QTextEdit
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
# Метод для создания вкладки Ping
    def create_ping_tab(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        input_layout = QHBoxLayout()

        label = QLabel("IP-адрес или домен:")

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Введите IP-адрес или домен:")

        button = QPushButton("Проверить")
        button.clicked.connect(self.ping_run)

        input_layout.addWidget(label)
        input_layout.addWidget(self.ip_input)
        input_layout.addWidget(button)
        layout.addLayout(input_layout)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

        self.ping_tab.setLayout(layout)
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
    # Метод для выполнения команды ping
    def ping_run(self):
        ip = self.ip_input.text().strip()
        if not ip:
            self.result_text.setText("Пожалуйста, введите IP-адрес или домен.")
            return
        try:
            result = subprocess.run(["ping", "-n", "4", ip], capture_output=True, text=True, timeout=15, encoding='cp866', errors='replace')
            self.result_text.setPlainText(result.stdout)
        except subprocess.TimeoutExpired:
            self.result_text.setText("Превышено время ожидания.")
        except Exception as error:
            self.result_text.setText(f"Ошибка: {error}")
    # Метод для выполнения команды ipconfig
    def ipconfig_run(self):
        try:
            result = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, timeout=15, encoding='cp866', errors='replace')
            self.result_text_ipconfig.setPlainText(result.stdout)
        except subprocess.TimeoutExpired:
            self.result_text_ipconfig.setText("Превышено время ожидания.")
        except Exception as error:
            self.result_text_ipconfig.setText(f"Ошибка: {error}")
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