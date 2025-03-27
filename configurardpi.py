import customtkinter as ctk
import subprocess
import tkinter as tk
import os
import sys
from tkinter import ttk
from PIL import Image, ImageTk
import io

def resource_path(relative_path):
    """Obtenha o caminho absoluto para o recurso, seja ele executado no modo de desenvolvimento ou como executável."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Caminho completo para o executável ADB
ADB_PATH = resource_path("adb.exe")

# Lista de aplicativos a serem excluídos
app_list = [
    "com.netflix.mediaclient",
    "com.globo.globotv",
    "tv.pluto.android",
    "com.spotify.tv.android",
    "com.facebook.katana"
]

def get_device_info(ip_address, port):
    try:
        # Obtém informações do dispositivo
        model = subprocess.run(
            [ADB_PATH, "-s", f"{ip_address}:{port}", "shell", "getprop", "ro.product.model"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True
        ).stdout.strip()

        android_version = subprocess.run(
            [ADB_PATH, "-s", f"{ip_address}:{port}", "shell", "getprop", "ro.build.version.release"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True
        ).stdout.strip()

        current_dpi = subprocess.run(
            [ADB_PATH, "-s", f"{ip_address}:{port}", "shell", "wm", "density"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True
        ).stdout.strip()

        return {
            "model": model,
            "android_version": android_version,
            "current_dpi": current_dpi
        }
    except:
        return None

def check_device_connection(ip_address, port):
    try:
        result = subprocess.run([ADB_PATH, "connect", f"{ip_address}:{port}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def update_device_info():
    ip_address = ip_entry.get()
    port = "5555"

    if ip_address and check_device_connection(ip_address, port):
        info = get_device_info(ip_address, port)
        if info:
            device_info_label.configure(
                text=f"Modelo: {info['model']}\n"
                     f"Android: {info['android_version']}\n"
                     f"DPI Atual: {info['current_dpi']}",
                text_color="green"
            )
        else:
            device_info_label.configure(text="Não foi possível obter informações do dispositivo", text_color="red")
    else:
        device_info_label.configure(text="Dispositivo não conectado", text_color="red")

def change_dpi():
    ip_address = ip_entry.get()
    dpi = "160"
    port = "5555"

    if ip_address:
        if not check_device_connection(ip_address, port):
            result_label.configure(text="Erro: Verifique a conexão Wi-Fi ou a depuração USB desativada no Mini PC.", text_color="red")
            return

        try:
            result_label.configure(text="Conectando ao Mini PC...", text_color="green")

            # Conecta ao dispositivo Mini pc
            subprocess.run(
                [ADB_PATH, "connect", f"{ip_address}:{port}"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # Excluir os aplicativos da lista, se houver algum
            if app_list:
                for app in app_list:
                    try:
                        result = subprocess.run(
                            [ADB_PATH, "-s", f"{ip_address}:{port}", "uninstall", app],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        if result.returncode == 0:
                            result_label.configure(text=f"Aplicativo com endereço: {app} deletado com sucesso!", text_color="green")
                        else:
                            result_label.configure(text=f"Erro ao excluir o aplicativo {app}: {result.stdout.strip()}", text_color="red")
                    except subprocess.CalledProcessError as e:
                        result_label.configure(text=f"Erro ao excluir o aplicativo {app}: {e.stderr.strip()}", text_color="red")
                        continue

            # Altera a DPI no mini pc
            subprocess.run(
                [ADB_PATH, "-s", f"{ip_address}:{port}", "shell", "wm", "density", dpi],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            # Reinicia o dispositivo para testar o autostart
            subprocess.run(
                [ADB_PATH, "-s", f"{ip_address}:{port}", "shell", "reboot"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            result_label.configure(text="DPI alterado e aplicativos excluídos com sucesso!", text_color="green")
        except subprocess.CalledProcessError as e:
            result_label.configure(text=f"Erro ao alterar DPI ou excluir aplicativos: {e.stderr.strip()}", text_color="red")
        except Exception as e:
            result_label.configure(text=f"Erro ao alterar DPI ou excluir aplicativos: {str(e)}", text_color="red")
    else:
        result_label.configure(text="Por favor, preencha o campo Endereço IP do dispositivo.", text_color="red")

def add_app_to_list():
    app_name = app_entry.get()
    if app_name:
        app_list.append(app_name)
        app_listbox.insert(tk.END, app_name)
        app_entry.delete(0, tk.END)

class AppListWindow:
    def __init__(self, parent, adb_manager, ip_address):
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Aplicativos Instalados")
        self.window.geometry("600x500")
        self.window.resizable(False, False)

        self.adb_manager = adb_manager
        self.ip_address = ip_address
        self.selected_apps = set()

        self.setup_ui()
        self.load_apps()

    def setup_ui(self):
        # Frame principal
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Título
        title_label = ctk.CTkLabel(main_frame, text="Aplicativos Instalados", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))

        # Frame para lista de aplicativos
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Canvas e Scrollbar
        canvas = tk.Canvas(list_frame, bg="#2E2E2E", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ctk.CTkFrame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack dos elementos de scroll
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Botões
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(0, 5))

        select_all_button = ctk.CTkButton(
            button_frame,
            text="Selecionar Todos",
            command=self.select_all,
            width=120,
            height=30
        )
        select_all_button.pack(side="left", padx=5)

        deselect_all_button = ctk.CTkButton(
            button_frame,
            text="Desselecionar Todos",
            command=self.deselect_all,
            width=120,
            height=30
        )
        deselect_all_button.pack(side="left", padx=5)

        add_selected_button = ctk.CTkButton(
            button_frame,
            text="Adicionar Selecionados",
            command=self.add_selected_to_list,
            width=150,
            height=30
        )
        add_selected_button.pack(side="right", padx=5)

    def load_apps(self):
        try:
            # Obtém lista de aplicativos instalados
            result = subprocess.run(
                [self.adb_manager.adb_path, "-s", f"{self.ip_address}:{self.adb_manager.port}", "shell", "pm", "list", "packages", "-f"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
                text=True
            )

            apps = result.stdout.strip().split('\n')
            for app in apps:
                if app.startswith('package:'):
                    package_name = app.split('=')[1]
                    self.create_app_item(package_name)

        except Exception as e:
            error_label = ctk.CTkLabel(
                self.scrollable_frame,
                text=f"Erro ao carregar aplicativos: {str(e)}",
                text_color="red"
            )
            error_label.pack(pady=10)

    def create_app_item(self, package_name):
        frame = ctk.CTkFrame(self.scrollable_frame)
        frame.pack(fill="x", padx=5, pady=2)

        # Checkbox
        var = tk.BooleanVar()
        checkbox = ctk.CTkCheckBox(
            frame,
            text=package_name,
            variable=var,
            command=lambda: self.toggle_app(package_name, var.get())
        )
        checkbox.pack(side="left", padx=5)

    def toggle_app(self, package_name, selected):
        if selected:
            self.selected_apps.add(package_name)
        else:
            self.selected_apps.discard(package_name)

    def select_all(self):
        for widget in self.scrollable_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkCheckBox):
                        child.select()
                        self.selected_apps.add(child.cget("text"))

    def deselect_all(self):
        for widget in self.scrollable_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame):
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkCheckBox):
                        child.deselect()
        self.selected_apps.clear()

    def add_selected_to_list(self):
        for app in self.selected_apps:
            if app not in app_list:
                app_list.append(app)
                app_listbox.insert(tk.END, app)
        self.window.destroy()

class ADBManager:
    def __init__(self, adb_path):
        self.adb_path = adb_path
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
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()

    def change_dpi(self, ip_address, dpi):
        try:
            subprocess.run(
                [self.adb_path, "-s", f"{ip_address}:{self.port}", "shell", "wm", "density", str(dpi)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True, "DPI alterado com sucesso"
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()

    def reboot_device(self, ip_address):
        try:
            subprocess.run(
                [self.adb_path, "-s", f"{ip_address}:{self.port}", "shell", "reboot"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True, "Dispositivo reiniciado com sucesso"
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()

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

    def add_app(self, app_name):
        if app_name and app_name not in self.default_apps:
            self.default_apps[app_name] = True
            self.app_list.append(app_name)
            return True
        return False

    def remove_app(self, app_name):
        if app_name in self.default_apps:
            self.default_apps[app_name] = False
            if app_name in self.app_list:
                self.app_list.remove(app_name)
            return True
        return False

    def toggle_app(self, app_name):
        if app_name in self.default_apps:
            if self.default_apps[app_name]:
                self.remove_app(app_name)
            else:
                self.default_apps[app_name] = True
                self.app_list.append(app_name)
            return True
        return False

class ConfiguradorDPI:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("Configurador DPI - Mini PCS")

        # Ajustando o tamanho da janela para acomodar todo o conteúdo
        window_width = 590
        window_height = 650

        # Posicionar janela no centro da tela
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        # Calculando posição para centralizar
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        # Ajuste adicional para garantir que não fique muito próximo à barra de tarefas
        y = max(y - 50, 0)  # Subtrai 50 pixels da posição y para elevar a janela um pouco

        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.window.resizable(False, False)

        # Bind Enter key to change_dpi
        self.window.bind('<Return>', lambda event: self.change_dpi())

        self.adb_manager = ADBManager(resource_path("adb.exe"))
        self.app_manager = AppManager()

        # Carregar últimas configurações
        self.load_settings()

        self.setup_ui()
        self.load_apps()

    def load_settings(self):
        try:
            if os.path.exists('settings.txt'):
                with open('settings.txt', 'r') as f:
                    self.last_ip = f.readline().strip()
                    self.last_dpi = f.readline().strip()
            else:
                self.last_ip = "10.0.0."
                self.last_dpi = "160"
        except:
            self.last_ip = "10.0.0."
            self.last_dpi = "160"

    def save_settings(self):
        try:
            with open('settings.txt', 'w') as f:
                f.write(f"{self.ip_entry.get()}\n")
                f.write(f"{self.dpi_entry.get()}\n")
        except:
            pass

    def setup_ui(self):
        # Frame principal
        self.main_frame = ctk.CTkFrame(self.window)
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Título
        self.title_label = ctk.CTkLabel(self.main_frame, text="Configurador DPI", font=("Arial", 20, "bold"))
        self.title_label.pack(pady=(0, 10))

        # Frame para conexão
        self.setup_connection_frame()

        # Frame para aplicativos
        self.setup_apps_frame()

        # Botão principal
        self.change_button = ctk.CTkButton(
            self.main_frame,
            text="Alterar DPI e Remover Apps",
            command=self.change_dpi,
            width=300,
            height=35
        )
        self.change_button.pack(pady=(0, 5))

        # Label de resultado
        self.result_label = ctk.CTkLabel(self.main_frame, text="", font=("Helvetica", 10))
        self.result_label.pack(pady=(0, 5))

        # Rodapé
        self.setup_footer()

    def setup_connection_frame(self):
        connection_frame = ctk.CTkFrame(self.main_frame)
        connection_frame.pack(fill="x", pady=(0, 10))

        # Frame para IP e DPI
        settings_frame = ctk.CTkFrame(connection_frame)
        settings_frame.pack(fill="x", pady=(0, 5))

        # IP Frame
        ip_frame = ctk.CTkFrame(settings_frame)
        ip_frame.pack(side="left", fill="x", expand=True)

        ip_label = ctk.CTkLabel(ip_frame, text="IP do dispositivo:", font=("Arial", 12))
        ip_label.pack(side="left", padx=(0, 10))

        self.ip_entry = ctk.CTkEntry(ip_frame, width=200, height=30)
        self.ip_entry.pack(side="left", fill="x", expand=True)
        self.ip_entry.insert(0, self.last_ip)

        # DPI Frame
        dpi_frame = ctk.CTkFrame(settings_frame)
        dpi_frame.pack(side="right", padx=(10, 0))

        dpi_label = ctk.CTkLabel(dpi_frame, text="DPI:", font=("Arial", 12))
        dpi_label.pack(side="left", padx=(0, 5))

        self.dpi_entry = ctk.CTkEntry(dpi_frame, width=60, height=30)
        self.dpi_entry.pack(side="left")
        self.dpi_entry.insert(0, self.last_dpi)

        # Botão Conectar
        connect_button = ctk.CTkButton(
            settings_frame,
            text="Conectar",
            command=self.update_device_info,
            width=80,
            height=30
        )
        connect_button.pack(side="right", padx=(10, 0))

        # Informações do dispositivo
        self.device_info_label = ctk.CTkLabel(
            connection_frame,
            text="Dispositivo não conectado",
            font=("Arial", 10),
            text_color="red"
        )
        self.device_info_label.pack(pady=5)

    def setup_apps_frame(self):
        apps_frame = ctk.CTkFrame(self.main_frame)
        apps_frame.pack(fill="both", expand=True, pady=(0, 10))

        # Frame para título e botões
        header_frame = ctk.CTkFrame(apps_frame)
        header_frame.pack(fill="x", pady=(0, 5))

        apps_label = ctk.CTkLabel(header_frame, text="Aplicativos para Remover", font=("Arial", 12, "bold"))
        apps_label.pack(side="left")

        buttons_frame = ctk.CTkFrame(header_frame)
        buttons_frame.pack(side="right")

        list_apps_button = ctk.CTkButton(
            buttons_frame,
            text="Listar Instalados",
            command=self.show_app_list,
            width=120,
            height=30
        )
        list_apps_button.pack(side="left")

        # Lista de aplicativos padrão
        default_apps_frame = ctk.CTkFrame(apps_frame)
        default_apps_frame.pack(fill="x", pady=(5, 0))

        default_label = ctk.CTkLabel(default_apps_frame, text="Apps Padrão:", font=("Arial", 10, "bold"))
        default_label.pack(anchor="w", padx=5, pady=(5,0))

        for app_name in self.app_manager.default_apps.keys():
            self.create_default_app_item(default_apps_frame, app_name)

        # Lista de aplicativos adicionais
        listbox_frame = ctk.CTkFrame(apps_frame)
        listbox_frame.pack(fill="both", expand=True)

        # Estilo personalizado para a scrollbar
        style = ttk.Style()
        style.theme_use('default')  # Usar o tema padrão como base
        style.element_create("Custom.Vertical.TScrollbar.trough", "from", "default")
        style.element_create("Custom.Vertical.TScrollbar.thumb", "from", "default")
        style.layout("Custom.Vertical.TScrollbar",
                    [('Custom.Vertical.TScrollbar.trough',
                      {'children': [('Custom.Vertical.TScrollbar.thumb', {'expand': '1'})],
                       'sticky': 'ns'})])
        style.configure("Custom.Vertical.TScrollbar",
                      background="#1a1a1a",  # Cor do thumb (a parte que move)
                      troughcolor="#2E2E2E",  # Cor do canal da scrollbar
                      borderwidth=0,
                      arrowsize=0,  # Remove as setas
                      relief="flat")  # Remove o efeito 3D
        style.map("Custom.Vertical.TScrollbar",
                 background=[('pressed', '#0f0f0f'),  # Cor quando pressionado
                           ('active', '#262626')])  # Cor quando hover

        self.app_listbox = tk.Listbox(
            listbox_frame,
            width=40,
            height=8,
            bg="#2E2E2E",
            fg="white",
            selectbackground="#4A4A4A",
            selectforeground="white",
            font=("Arial", 10),
            borderwidth=0,
            highlightthickness=0
        )
        self.app_listbox.pack(side="left", fill="both", expand=True, pady=5)

        scrollbar = ttk.Scrollbar(
            listbox_frame,
            orient="vertical",
            command=self.app_listbox.yview,
            style="Custom.Vertical.TScrollbar"
        )
        scrollbar.pack(side="right", fill="y", pady=5)
        self.app_listbox.configure(yscrollcommand=scrollbar.set)

    def create_default_app_item(self, parent, app_name):
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", padx=5, pady=2)

        var = tk.BooleanVar(value=self.app_manager.default_apps[app_name])
        checkbox = ctk.CTkCheckBox(
            frame,
            text=app_name,
            variable=var,
            command=lambda: self.toggle_default_app(app_name, var)
        )
        checkbox.pack(side="left", padx=5)

    def toggle_default_app(self, app_name, var):
        if self.app_manager.toggle_app(app_name):
            self.refresh_app_list()

    def refresh_app_list(self):
        self.app_listbox.delete(0, tk.END)
        for app in self.app_manager.app_list:
            self.app_listbox.insert(tk.END, app)

    def setup_footer(self):
        # Frame principal do rodapé
        footer_frame = ctk.CTkFrame(self.window, height=30)
        footer_frame.pack(side="bottom", fill="x", padx=10, pady=5)
        footer_frame.pack_propagate(False)  # Impede que o frame encolha

        # Texto "Desenvolvido por"
        dev_label = ctk.CTkLabel(
            footer_frame,
            text="Desenvolvido por",
            font=("Arial", 9),
            text_color="gray"
        )
        dev_label.pack(side="left", padx=(10, 0))

        def open_linkedin():
            import webbrowser
            webbrowser.open("https://www.linkedin.com/in/ruã-fernandes-araújo-4617a8282/")

        def open_github():
            import webbrowser
            webbrowser.open("https://github.com/ruafernd/")

        # Nome clicável
        name_button = ctk.CTkButton(
            footer_frame,
            text="Ruã Fernandes",
            command=open_linkedin,
            font=("Arial", 9, "bold"),
            fg_color="transparent",
            hover_color="#2B2B2B",
            text_color="gray",
            width=80,
            height=20
        )
        name_button.pack(side="left", padx=(5, 0))

        # Botões de redes sociais
        social_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        social_frame.pack(side="right", padx=10)

        # Botão do LinkedIn com ícone
        linkedin_button = ctk.CTkButton(
            social_frame,
            text="in",  # Símbolo do LinkedIn
            command=open_linkedin,
            font=("Arial", 12, "bold"),
            fg_color="#0077B5",  # Cor de fundo do LinkedIn
            hover_color="#006399",  # Cor mais escura para hover
            text_color="white",  # Texto branco
            width=25,
            height=25,
            corner_radius=5
        )
        linkedin_button.pack(side="right", padx=5)

        # Botão do GitHub com ícone
        github_button = ctk.CTkButton(
            social_frame,
            text="Git",  # Texto Git para representar GitHub
            command=open_github,
            font=("Arial", 10, "bold"),
            fg_color="#333",  # Cor de fundo do GitHub
            hover_color="#24292e",  # Cor mais escura para hover (cor oficial do GitHub)
            text_color="white",
            width=35,  # Um pouco mais largo para acomodar o texto
            height=25,
            corner_radius=5
        )
        github_button.pack(side="right", padx=5)

        # Versão
        version_label = ctk.CTkLabel(
            social_frame,
            text="v4.0",
            font=("Arial", 9),
            text_color="gray"
        )
        version_label.pack(side="right", padx=(0, 10))

    def load_apps(self):
        for app in self.app_manager.app_list:
            self.app_listbox.insert(tk.END, app)

    def update_device_info(self):
        ip_address = self.ip_entry.get()
        if ip_address and self.adb_manager.connect(ip_address):
            info = self.adb_manager.get_device_info(ip_address)
            if info:
                self.device_info_label.configure(
                    text=f"Modelo: {info['model']}\n"
                         f"Android: {info['android_version']}\n"
                         f"DPI Atual: {info['current_dpi']}",
                    text_color="green"
                )
            else:
                self.device_info_label.configure(
                    text="Não foi possível obter informações do dispositivo",
                    text_color="red"
                )
        else:
            self.device_info_label.configure(
                text="Dispositivo não conectado",
                text_color="red"
            )

    def show_app_list(self):
        ip_address = self.ip_entry.get()
        if not ip_address:
            self.result_label.configure(
                text="Por favor, preencha o campo IP do dispositivo.",
                text_color="red"
            )
            return

        if not self.adb_manager.connect(ip_address):
            self.result_label.configure(
                text="Erro: Verifique a conexão Wi-Fi ou a depuração USB desativada no Mini PC.",
                text_color="red"
            )
            return

        AppListWindow(self.window, self.adb_manager, ip_address)

    def remove_selected_app(self):
        selection = self.app_listbox.curselection()
        if selection:
            app_name = self.app_listbox.get(selection[0])
            # Remove o app da lista do app_manager
            if app_name in self.app_manager.app_list:
                self.app_manager.app_list.remove(app_name)
            # Remove o app da listbox
            self.app_listbox.delete(selection[0])
            # Se for um app padrão, atualiza o estado no app_manager e desmarca o checkbox
            if app_name in self.app_manager.default_apps:
                self.app_manager.default_apps[app_name] = False
                # Procura e desmarca o checkbox correspondente
                for frame in self.main_frame.winfo_children():
                    if isinstance(frame, ctk.CTkFrame):
                        for apps_frame in frame.winfo_children():
                            if isinstance(apps_frame, ctk.CTkFrame):
                                for default_frame in apps_frame.winfo_children():
                                    if isinstance(default_frame, ctk.CTkFrame):
                                        for checkbox in default_frame.winfo_children():
                                            if isinstance(checkbox, ctk.CTkCheckBox) and checkbox.cget("text") == app_name:
                                                checkbox.deselect()
                                                return

    def change_dpi(self):
        ip_address = self.ip_entry.get()
        dpi = self.dpi_entry.get()

        if not ip_address:
            self.result_label.configure(
                text="Por favor, preencha o campo Endereço IP do dispositivo.",
                text_color="red"
            )
            return

        if not dpi.isdigit():
            self.result_label.configure(
                text="Por favor, insira um valor válido para DPI.",
                text_color="red"
            )
            return

        # Salvar configurações
        self.save_settings()

        # Desabilitar botões durante a operação
        self.change_button.configure(state="disabled")

        try:
            if not self.adb_manager.connect(ip_address):
                self.result_label.configure(
                    text="Erro: Verifique a conexão Wi-Fi ou a depuração USB desativada no Mini PC.",
                    text_color="red"
                )
                return

            self.result_label.configure(text="Conectando ao Mini PC...", text_color="green")

            # Remove aplicativos
            for app in self.app_manager.app_list:
                try:
                    success, message = self.adb_manager.uninstall_app(ip_address, app)
                    if success:
                        self.result_label.configure(
                            text=f"Aplicativo {app} removido com sucesso!",
                            text_color="green"
                        )
                    else:
                        if "DELETE_FAILED_DEVICE_POLICY_MANAGER" in message or "DELETE_FAILED_INTERNAL_ERROR" in message:
                            self.result_label.configure(
                                text=f"Aplicativo {app} não pode ser removido (aplicativo do sistema)",
                                text_color="orange"
                            )
                        else:
                            self.result_label.configure(
                                text=f"Erro ao remover {app}: {message}",
                                text_color="red"
                            )
                except Exception as e:
                    self.result_label.configure(
                        text=f"Erro ao tentar remover {app}: {str(e)}",
                        text_color="red"
                    )
                    continue

            # Altera DPI
            try:
                success, message = self.adb_manager.change_dpi(ip_address, dpi)
                if not success:
                    self.result_label.configure(text=f"Erro ao alterar DPI: {message}", text_color="red")
                    return
            except Exception as e:
                self.result_label.configure(text=f"Erro ao alterar DPI: {str(e)}", text_color="red")
                return

            # Reinicia dispositivo
            try:
                self.adb_manager.reboot_device(ip_address)
                self.result_label.configure(
                    text="DPI alterado e aplicativos removidos com sucesso! Reiniciando...",
                    text_color="green"
                )
            except:
                # Ignora erros de reinicialização pois o dispositivo já estará reiniciando
                pass

        except Exception as e:
            self.result_label.configure(
                text=f"Erro: {str(e)}",
                text_color="red"
            )
        finally:
            try:
                self.change_button.configure(state="normal")
            except:
                pass  # Ignora erros ao tentar reabilitar o botão

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = ConfiguradorDPI()
    app.run()
