import sys
import subprocess
import os
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
                             QPushButton, QCheckBox, QTextEdit, QGroupBox,
                             QFrame, QScrollArea, QSizePolicy, QDialog,
                             QListWidget, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon

def resource_path(relative_path):
    """Obtenha o caminho absoluto para o recurso"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ADBManager:
    def __init__(self):
        self.adb_path = resource_path("adb.exe")
        self.port = "5555"

    def connect(self, ip_address):
        try:
            result = subprocess.run(
                [self.adb_path, "connect", f"{ip_address}:{self.port}"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True
            )
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False

    def get_device_info(self, ip_address):
        try:
            model = subprocess.run(
                [self.adb_path, "-s", f"{ip_address}:{self.port}", "shell", "getprop", "ro.product.model"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True
            ).stdout.strip()

            android_version = subprocess.run(
                [self.adb_path, "-s", f"{ip_address}:{self.port}", "shell", "getprop", "ro.build.version.release"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True
            ).stdout.strip()

            current_dpi = subprocess.run(
                [self.adb_path, "-s", f"{ip_address}:{self.port}", "shell", "wm", "density"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True
            ).stdout.strip()

            return {
                "model": model,
                "android_version": android_version,
                "current_dpi": current_dpi
            }
        except:
            return None

    def uninstall_app(self, ip_address, app_package):
        try:
            result = subprocess.run(
                [self.adb_path, "-s", f"{ip_address}:{self.port}", "uninstall", app_package],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0, result.stdout.strip() + result.stderr.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()
        except Exception as e:
            return False, str(e)

    def change_dpi(self, ip_address, dpi):
        try:
            result = subprocess.run(
                [self.adb_path, "-s", f"{ip_address}:{self.port}", "shell", "wm", "density", str(dpi)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0, result.stdout.strip() + result.stderr.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()
        except Exception as e:
            return False, str(e)

    def reboot_device(self, ip_address):
        try:
            result = subprocess.run(
                [self.adb_path, "-s", f"{ip_address}:{self.port}", "shell", "reboot"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0, result.stdout.strip() + result.stderr.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()
        except Exception as e:
            return False, str(e)

class AppManager:
    def __init__(self):
        self.default_apps = {
            "com.netflix.mediaclient": True,
            "com.globo.globotv": True,
            "tv.pluto.android": True,
            "com.spotify.tv.android": True,
            "com.facebook.katana": True
        }
        self.app_list = [app for app, enabled in self.default_apps.items() if enabled]

    def toggle_app(self, app_name):
        if app_name in self.default_apps:
            if self.default_apps[app_name]:
                self.default_apps[app_name] = False
                if app_name in self.app_list:
                    self.app_list.remove(app_name)
            else:
                self.default_apps[app_name] = True
                self.app_list.append(app_name)
            return True
        return False

class WorkerThread(QThread):
    finished = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, adb_manager, app_manager, devices_to_process):
        super().__init__()
        self.adb_manager = adb_manager
        self.app_manager = app_manager
        self.devices_to_process = devices_to_process

    def run(self):
        results = []
        for ip, dpi, device_num in self.devices_to_process:
            result = self.process_device(ip, dpi, device_num)
            results.append(result)
            self.progress.emit(f"Processando dispositivo {device_num}...")

        if len(results) == 1:
            self.finished.emit(results[0])
        else:
            success_count = sum(1 for r in results if "sucesso" in r.lower())
            if success_count == len(results):
                self.finished.emit("Todos os dispositivos configurados com sucesso!")
            elif success_count > 0:
                self.finished.emit(f"{success_count}/{len(results)} dispositivos configurados com sucesso.")
            else:
                self.finished.emit("Erro ao configurar dispositivos.")

    def process_device(self, ip_address, dpi, device_num):
        try:
            self.progress.emit(f"Dispositivo {device_num}: Conectando...")
            if not self.adb_manager.connect(ip_address):
                return f"Dispositivo {device_num}: Erro de conexão"
            
            self.progress.emit(f"Dispositivo {device_num}: Removendo aplicativos...")
            # Remove aplicativos
            for app in self.app_manager.app_list:
                try:
                    self.progress.emit(f"Dispositivo {device_num}: Removendo {app}...")
                    success, message = self.adb_manager.uninstall_app(ip_address, app)
                    if not success:
                        if "DELETE_FAILED_DEVICE_POLICY_MANAGER" in message or "DELETE_FAILED_INTERNAL_ERROR" in message:
                            self.progress.emit(f"Dispositivo {device_num}: {app} não pode ser removido (app do sistema)")
                        else:
                            self.progress.emit(f"Dispositivo {device_num}: Erro ao remover {app}: {message}")
                            return f"Dispositivo {device_num}: Erro ao remover {app}"
                    else:
                        self.progress.emit(f"Dispositivo {device_num}: {app} removido com sucesso")
                except Exception as e:
                    self.progress.emit(f"Dispositivo {device_num}: Exceção ao remover {app}: {str(e)}")
                    return f"Dispositivo {device_num}: Erro ao tentar remover {app}"
            
            self.progress.emit(f"Dispositivo {device_num}: Alterando DPI para {dpi}...")
            # Altera DPI
            success, message = self.adb_manager.change_dpi(ip_address, dpi)
            if not success:
                self.progress.emit(f"Dispositivo {device_num}: Erro ao alterar DPI: {message}")
                return f"Dispositivo {device_num}: Erro ao alterar DPI - {message}"
            else:
                self.progress.emit(f"Dispositivo {device_num}: DPI alterado com sucesso")
            
            self.progress.emit(f"Dispositivo {device_num}: Reiniciando...")
            # Reinicia dispositivo
            try:
                success, message = self.adb_manager.reboot_device(ip_address)
                if success:
                    self.progress.emit(f"Dispositivo {device_num}: Reiniciado com sucesso")
                else:
                    self.progress.emit(f"Dispositivo {device_num}: Erro ao reiniciar: {message}")
            except Exception as e:
                self.progress.emit(f"Dispositivo {device_num}: Exceção ao reiniciar: {str(e)}")
            
            return f"Dispositivo {device_num}: Configurado com sucesso!"
            
        except Exception as e:
            self.progress.emit(f"Dispositivo {device_num}: Exceção geral: {str(e)}")
            return f"Dispositivo {device_num}: Erro - {str(e)}"

class AppListDialog(QDialog):
    def __init__(self, parent, adb_manager, ip_address):
        super().__init__(parent)
        self.adb_manager = adb_manager
        self.ip_address = ip_address
        self.selected_apps = set()
        self.init_ui()
        self.load_apps()

    def init_ui(self):
        self.setWindowTitle("Aplicativos Instalados")
        self.setGeometry(200, 200, 600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3c3c3c;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #363636;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
            }
            QListWidget {
                background-color: #404040;
                border: 2px solid #555555;
                border-radius: 5px;
                color: white;
                font-size: 11px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #555555;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton#select_all {
                background-color: #28a745;
            }
            QPushButton#select_all:hover {
                background-color: #218838;
            }
            QPushButton#deselect_all {
                background-color: #dc3545;
            }
            QPushButton#deselect_all:hover {
                background-color: #c82333;
            }
            QLabel {
                color: white;
                font-size: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title_label = QLabel("Aplicativos Instalados no Dispositivo")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Lista de aplicativos
        self.app_list = QListWidget()
        self.app_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.app_list)

        # Botões
        buttons_layout = QHBoxLayout()
        
        select_all_button = QPushButton("Selecionar Todos")
        select_all_button.setObjectName("select_all")
        select_all_button.clicked.connect(self.select_all)
        buttons_layout.addWidget(select_all_button)
        
        deselect_all_button = QPushButton("Desselecionar Todos")
        deselect_all_button.setObjectName("deselect_all")
        deselect_all_button.clicked.connect(self.deselect_all)
        buttons_layout.addWidget(deselect_all_button)
        
        buttons_layout.addStretch()
        
        add_selected_button = QPushButton("Adicionar Selecionados")
        add_selected_button.clicked.connect(self.add_selected_to_list)
        buttons_layout.addWidget(add_selected_button)
        
        layout.addLayout(buttons_layout)

    def load_apps(self):
        try:
            # Conectar ao dispositivo
            if not self.adb_manager.connect(self.ip_address):
                QMessageBox.warning(self, "Erro", "Não foi possível conectar ao dispositivo.")
                return

            # Obter lista de aplicativos instalados
            result = subprocess.run(
                [self.adb_manager.adb_path, "-s", f"{self.ip_address}:{self.adb_manager.port}", 
                 "shell", "pm", "list", "packages", "-f"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            apps = result.stdout.strip().split('\n')
            for app in apps:
                if app.startswith('package:'):
                    package_name = app.split('=')[1]
                    self.app_list.addItem(package_name)

        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Erro", f"Erro ao carregar aplicativos: {e.stderr.decode()}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro inesperado: {str(e)}")

    def select_all(self):
        for i in range(self.app_list.count()):
            self.app_list.item(i).setSelected(True)

    def deselect_all(self):
        self.app_list.clearSelection()

    def add_selected_to_list(self):
        selected_items = self.app_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Informação", "Nenhum aplicativo selecionado.")
            return

        # Adicionar aplicativos selecionados à lista principal
        added_count = 0
        for item in selected_items:
            app_name = item.text()
            if app_name not in self.parent().app_manager.default_apps:
                self.parent().app_manager.default_apps[app_name] = True
                self.parent().app_manager.app_list.append(app_name)
                
                # Adicionar checkbox na interface principal
                self.parent().add_app_checkbox(app_name, True)
                added_count += 1

        if added_count > 0:
            QMessageBox.information(self, "Sucesso", f"{added_count} aplicativo(s) adicionado(s) à lista.")
        else:
            QMessageBox.information(self, "Informação", "Todos os aplicativos selecionados já estão na lista.")
        
        self.accept()

class ConfiguradorDPI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.adb_manager = ADBManager()
        self.app_manager = AppManager()
        self.load_settings()
        self.init_ui()

    def load_settings(self):
        try:
            if os.path.exists('settings.txt'):
                with open('settings.txt', 'r') as f:
                    lines = f.readlines()
                    self.last_ip = lines[0].strip() if len(lines) > 0 else "10.0.0."
                    self.last_dpi = lines[1].strip() if len(lines) > 1 else "160"
                    self.last_ip2 = lines[2].strip() if len(lines) > 2 else "10.0.0."
                    self.last_dpi2 = lines[3].strip() if len(lines) > 3 else "160"
            else:
                self.last_ip = "10.0.0."
                self.last_dpi = "160"
                self.last_ip2 = "10.0.0."
                self.last_dpi2 = "160"
        except:
            self.last_ip = "10.0.0."
            self.last_dpi = "160"
            self.last_ip2 = "10.0.0."
            self.last_dpi2 = "160"

    def save_settings(self):
        try:
            with open('settings.txt', 'w') as f:
                f.write(f"{self.ip_entry1.text()}\n")
                f.write(f"{self.dpi_entry1.text()}\n")
                f.write(f"{self.ip_entry2.text()}\n")
                f.write(f"{self.dpi_entry2.text()}\n")
        except:
            pass

    def init_ui(self):
        self.setWindowTitle("Configurador DPI - Mini PCS")
        self.setGeometry(100, 100, 800, 700)
        
        # Definir ícone da aplicação
        try:
            icon_path = resource_path("logoAI_preto.ico")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                print(f"Ícone carregado: {icon_path}")
            else:
                # Tentar caminho alternativo
                alt_icon_path = r"C:\Users\RuaF\Downloads\logoAI_preto.ico"
                if os.path.exists(alt_icon_path):
                    self.setWindowIcon(QIcon(alt_icon_path))
                    print(f"Ícone carregado (caminho alternativo): {alt_icon_path}")
                else:
                    print("Ícone não encontrado")
        except Exception as e:
            print(f"Erro ao carregar ícone: {e}")
        
        # Configurar estilo
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: white;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3c3c3c;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: #363636;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #555555;
                border-radius: 5px;
                background-color: #404040;
                color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
            QPushButton {
                background-color: #0078d4;
                border: none;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton#usb {
                background-color: #ff6b35;
            }
            QPushButton#usb:hover {
                background-color: #e55a2b;
            }
            QPushButton#main {
                background-color: #28a745;
                font-size: 14px;
                padding: 12px 24px;
            }
            QPushButton#main:hover {
                background-color: #218838;
            }
            QCheckBox {
                color: white;
                font-size: 11px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #555555;
                background-color: #404040;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #0078d4;
                background-color: #0078d4;
                border-radius: 3px;
            }
            QLabel {
                color: white;
                font-size: 12px;
            }
            QLabel#title {
                font-size: 24px;
                font-weight: bold;
                color: #ffffff;
            }
            QLabel#status {
                font-size: 10px;
                padding: 5px;
                border-radius: 3px;
            }
            QTextEdit {
                background-color: #404040;
                border: 2px solid #555555;
                border-radius: 5px;
                color: white;
                font-size: 11px;
            }
        """)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title_label = QLabel("Configurador DPI")
        title_label.setObjectName("title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Seção de dispositivos
        self.create_devices_section(main_layout)
        
        # Seção de aplicativos
        self.create_apps_section(main_layout)
        
        # Botão principal
        self.create_main_button(main_layout)
        
        # Área de resultado
        self.create_result_area(main_layout)
        
        # Rodapé
        self.create_footer(main_layout)

    def create_devices_section(self, parent_layout):
        devices_group = QGroupBox("Configuração de Dispositivos")
        devices_layout = QVBoxLayout(devices_group)
        
        # Container para os dois dispositivos
        devices_container = QHBoxLayout()
        
        # Dispositivo 1
        device1_group = QGroupBox("Dispositivo 1")
        device1_layout = QVBoxLayout(device1_group)
        
        # IP do dispositivo 1
        ip_layout1 = QVBoxLayout()
        ip_label1 = QLabel("Endereço IP:")
        self.ip_entry1 = QLineEdit()
        self.ip_entry1.setText(self.last_ip)
        ip_layout1.addWidget(ip_label1)
        ip_layout1.addWidget(self.ip_entry1)
        device1_layout.addLayout(ip_layout1)
        
        # DPI do dispositivo 1
        dpi_layout1 = QVBoxLayout()
        dpi_label1 = QLabel("DPI:")
        self.dpi_entry1 = QLineEdit()
        self.dpi_entry1.setText(self.last_dpi)
        self.dpi_entry1.setMaximumWidth(100)
        dpi_layout1.addWidget(dpi_label1)
        dpi_layout1.addWidget(self.dpi_entry1)
        device1_layout.addLayout(dpi_layout1)
        
        # Status do dispositivo 1
        self.status_label1 = QLabel("Dispositivo não conectado")
        self.status_label1.setObjectName("status")
        self.status_label1.setStyleSheet("color: #ff6b6b; background-color: #2d2d2d;")
        device1_layout.addWidget(self.status_label1)
        
        devices_container.addWidget(device1_group)
        
        # Dispositivo 2
        device2_group = QGroupBox("Dispositivo 2")
        device2_layout = QVBoxLayout(device2_group)
        
        # IP do dispositivo 2
        ip_layout2 = QVBoxLayout()
        ip_label2 = QLabel("Endereço IP:")
        self.ip_entry2 = QLineEdit()
        self.ip_entry2.setText(self.last_ip2)
        ip_layout2.addWidget(ip_label2)
        ip_layout2.addWidget(self.ip_entry2)
        device2_layout.addLayout(ip_layout2)
        
        # DPI do dispositivo 2
        dpi_layout2 = QVBoxLayout()
        dpi_label2 = QLabel("DPI:")
        self.dpi_entry2 = QLineEdit()
        self.dpi_entry2.setText(self.last_dpi2)
        self.dpi_entry2.setMaximumWidth(100)
        dpi_layout2.addWidget(dpi_label2)
        dpi_layout2.addWidget(self.dpi_entry2)
        device2_layout.addLayout(dpi_layout2)
        
        # Status do dispositivo 2
        self.status_label2 = QLabel("Dispositivo não conectado")
        self.status_label2.setObjectName("status")
        self.status_label2.setStyleSheet("color: #ff6b6b; background-color: #2d2d2d;")
        device2_layout.addWidget(self.status_label2)
        
        devices_container.addWidget(device2_group)
        
        devices_layout.addLayout(devices_container)
        
        # Botões de conexão
        buttons_layout = QHBoxLayout()
        
        connect_button = QPushButton("Conectar aos Dispositivos")
        connect_button.clicked.connect(self.connect_all_devices)
        buttons_layout.addWidget(connect_button)
        
        usb_button = QPushButton("USB")
        usb_button.setObjectName("usb")
        usb_button.clicked.connect(self.connect_usb_device)
        buttons_layout.addWidget(usb_button)
        
        devices_layout.addLayout(buttons_layout)
        
        parent_layout.addWidget(devices_group)

    def create_apps_section(self, parent_layout):
        apps_group = QGroupBox("Aplicativos para Remover")
        apps_layout = QVBoxLayout(apps_group)
        
        # Header
        header_layout = QHBoxLayout()
        apps_label = QLabel("Aplicativos Selecionados:")
        header_layout.addWidget(apps_label)
        
        list_apps_button = QPushButton("Listar Instalados")
        list_apps_button.clicked.connect(self.show_app_list)
        header_layout.addWidget(list_apps_button)
        
        apps_layout.addLayout(header_layout)
        
        # Container para os checkboxes
        self.apps_container = QVBoxLayout()
        apps_layout.addLayout(self.apps_container)
        
        # Checkboxes dos aplicativos padrão
        self.app_checkboxes = {}
        for app_name in self.app_manager.default_apps.keys():
            self.add_app_checkbox(app_name, self.app_manager.default_apps[app_name])
        
        parent_layout.addWidget(apps_group)

    def add_app_checkbox(self, app_name, checked=True):
        """Adiciona um checkbox para um aplicativo"""
        checkbox = QCheckBox(app_name)
        checkbox.setChecked(checked)
        checkbox.toggled.connect(lambda checked, app=app_name: self.toggle_app(app, checked))
        self.app_checkboxes[app_name] = checkbox
        self.apps_container.addWidget(checkbox)

    def create_main_button(self, parent_layout):
        self.main_button = QPushButton("Alterar DPI e Remover Apps")
        self.main_button.setObjectName("main")
        self.main_button.clicked.connect(self.change_dpi)
        parent_layout.addWidget(self.main_button)

    def create_result_area(self, parent_layout):
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(100)
        self.result_text.setPlaceholderText("Resultado das operações aparecerá aqui...")
        parent_layout.addWidget(self.result_text)

    def create_footer(self, parent_layout):
        footer_layout = QHBoxLayout()
        
        dev_label = QLabel("Desenvolvido por")
        dev_label.setStyleSheet("color: #888888; font-size: 10px;")
        footer_layout.addWidget(dev_label)
        
        name_button = QPushButton("Ruã Fernandes")
        name_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: none;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        name_button.clicked.connect(lambda: self.open_url("https://www.linkedin.com/in/ruã-fernandes-araújo-4617a8282/"))
        footer_layout.addWidget(name_button)
        
        footer_layout.addStretch()
        
        # Botões de redes sociais
        linkedin_button = QPushButton("in")
        linkedin_button.setStyleSheet("""
            QPushButton {
                background-color: #0077B5;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 12px;
                padding: 5px 8px;
            }
            QPushButton:hover {
                background-color: #006399;
            }
        """)
        linkedin_button.clicked.connect(lambda: self.open_url("https://www.linkedin.com/in/ruã-fernandes-araújo-4617a8282/"))
        footer_layout.addWidget(linkedin_button)
        
        github_button = QPushButton("Git")
        github_button.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
                padding: 5px 8px;
            }
            QPushButton:hover {
                background-color: #24292e;
            }
        """)
        github_button.clicked.connect(lambda: self.open_url("https://github.com/ruafernd/"))
        footer_layout.addWidget(github_button)
        
        version_label = QLabel("v5.0")
        version_label.setStyleSheet("color: #888888; font-size: 10px;")
        footer_layout.addWidget(version_label)
        
        parent_layout.addLayout(footer_layout)

    def open_url(self, url):
        import webbrowser
        webbrowser.open(url)

    def toggle_app(self, app_name, checked):
        self.app_manager.default_apps[app_name] = checked
        if checked and app_name not in self.app_manager.app_list:
            self.app_manager.app_list.append(app_name)
        elif not checked and app_name in self.app_manager.app_list:
            self.app_manager.app_list.remove(app_name)

    def connect_all_devices(self):
        # Testar dispositivo 1
        ip_address1 = self.ip_entry1.text()
        device1_connected = False
        if ip_address1:
            if self.adb_manager.connect(ip_address1):
                info1 = self.adb_manager.get_device_info(ip_address1)
                if info1:
                    self.status_label1.setText(f"Conectado: {info1['model']}")
                    self.status_label1.setStyleSheet("color: #4caf50; background-color: #2d2d2d;")
                    device1_connected = True
                else:
                    self.status_label1.setText("Erro ao obter informações")
                    self.status_label1.setStyleSheet("color: #ff6b6b; background-color: #2d2d2d;")
            else:
                self.status_label1.setText("Dispositivo não conectado")
                self.status_label1.setStyleSheet("color: #ff6b6b; background-color: #2d2d2d;")
        else:
            self.status_label1.setText("IP não informado")
            self.status_label1.setStyleSheet("color: #ffa726; background-color: #2d2d2d;")

        # Testar dispositivo 2
        ip_address2 = self.ip_entry2.text()
        device2_connected = False
        if ip_address2:
            if self.adb_manager.connect(ip_address2):
                info2 = self.adb_manager.get_device_info(ip_address2)
                if info2:
                    self.status_label2.setText(f"Conectado: {info2['model']}")
                    self.status_label2.setStyleSheet("color: #4caf50; background-color: #2d2d2d;")
                    device2_connected = True
                else:
                    self.status_label2.setText("Erro ao obter informações")
                    self.status_label2.setStyleSheet("color: #ff6b6b; background-color: #2d2d2d;")
            else:
                self.status_label2.setText("Dispositivo não conectado")
                self.status_label2.setStyleSheet("color: #ff6b6b; background-color: #2d2d2d;")
        else:
            self.status_label2.setText("IP não informado")
            self.status_label2.setStyleSheet("color: #ffa726; background-color: #2d2d2d;")

        # Mostrar resultado geral baseado no status real
        connected_count = 0
        if device1_connected:
            connected_count += 1
        if device2_connected:
            connected_count += 1
        
        if connected_count == 0:
            self.result_text.append("Nenhum dispositivo conectado")
        elif connected_count == 1:
            self.result_text.append("1 dispositivo conectado")
        else:
            self.result_text.append("2 dispositivos conectados")

    def connect_usb_device(self):
        try:
            self.result_text.append("Verificando dispositivos USB...")
            # Verificar dispositivos USB conectados
            result = subprocess.run(
                [self.adb_manager.adb_path, "devices"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode != 0:
                self.result_text.append(f"Erro ao executar 'adb devices': {result.stderr}")
                return
            
            devices_output = result.stdout.strip()
            self.result_text.append(f"Saída do comando 'adb devices':\n{devices_output}")
            
            # Verificar se há dispositivos conectados
            connected_devices = []
            for line in devices_output.split('\n'):
                if line.strip() and not line.startswith('List of devices') and '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    connected_devices.append(device_id)
            
            if not connected_devices:
                self.result_text.append("Nenhum dispositivo USB encontrado. Conecte um dispositivo via USB.")
                return
            
            # Se encontrou dispositivos, executar o comando
            self.result_text.append(f"Dispositivo USB encontrado: {connected_devices[0]}. Executando comando...")
            
            # Executar o comando de alteração de DPI
            self.result_text.append("Alterando DPI para 160...")
            dpi_result = subprocess.run(
                [self.adb_manager.adb_path, "shell", "wm", "density", "160"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if dpi_result.returncode != 0:
                self.result_text.append(f"Erro ao alterar DPI: {dpi_result.stderr}")
                return
            else:
                self.result_text.append("DPI alterado com sucesso!")
            
            # Executar reboot
            self.result_text.append("Reiniciando dispositivo...")
            reboot_result = subprocess.run(
                [self.adb_manager.adb_path, "shell", "reboot"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if reboot_result.returncode == 0:
                self.result_text.append("Dispositivo reiniciado com sucesso!")
            else:
                self.result_text.append(f"Erro ao reiniciar: {reboot_result.stderr}")
                
        except subprocess.CalledProcessError as e:
            self.result_text.append(f"Erro ao verificar dispositivos USB: {e.stderr.decode()}")
        except Exception as e:
            self.result_text.append(f"Erro inesperado: {str(e)}")

    def show_app_list(self):
        # Verificar qual dispositivo está conectado
        ip_address1 = self.ip_entry1.text()
        ip_address2 = self.ip_entry2.text()
        
        # Priorizar dispositivo 1 se ambos estiverem preenchidos
        target_ip = None
        if ip_address1:
            target_ip = ip_address1
        elif ip_address2:
            target_ip = ip_address2
        else:
            QMessageBox.warning(self, "Aviso", "Por favor, preencha pelo menos um endereço IP de dispositivo.")
            return
        
        # Verificar conexão
        if not self.adb_manager.connect(target_ip):
            QMessageBox.warning(self, "Erro", "Não foi possível conectar ao dispositivo. Verifique o IP e a conexão.")
            return
        
        # Abrir janela de aplicativos instalados
        dialog = AppListDialog(self, self.adb_manager, target_ip)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Os aplicativos já foram adicionados pelo dialog
            self.result_text.append("Aplicativos adicionados com sucesso!")
        else:
            self.result_text.append("Operação cancelada.")

    def change_dpi(self):
        ip_address1 = self.ip_entry1.text()
        dpi1 = self.dpi_entry1.text()
        ip_address2 = self.ip_entry2.text()
        dpi2 = self.dpi_entry2.text()

        # Validar entradas
        devices_to_process = []
        
        if ip_address1 and dpi1.isdigit():
            devices_to_process.append((ip_address1, dpi1, 1))
        
        if ip_address2 and dpi2.isdigit():
            devices_to_process.append((ip_address2, dpi2, 2))
        
        if not devices_to_process:
            self.result_text.append("Por favor, preencha pelo menos um IP válido e DPI válido.")
            return

        # Salvar configurações
        self.save_settings()

        # Desabilitar botão durante a operação
        self.main_button.setEnabled(False)
        self.main_button.setText("Processando...")

        # Criar e iniciar thread de trabalho
        self.worker = WorkerThread(self.adb_manager, self.app_manager, devices_to_process)
        self.worker.progress.connect(self.result_text.append)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def on_worker_finished(self, result):
        self.result_text.append(result)
        self.main_button.setEnabled(True)
        self.main_button.setText("Alterar DPI e Remover Apps")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConfiguradorDPI()
    window.show()
    sys.exit(app.exec()) 