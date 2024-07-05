import customtkinter as ctk
import subprocess
import tkinter as tk 
import os
import sys

def resource_path(relative_path):
    """Obtenha o caminho absoluto para o recurso, seja ele executado no modo de desenvolvimento ou como executável."""
    try:
        # PyInstaller cria um diretório temporário e armazena o caminho nele
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

def check_device_connection(ip_address, port):
    try:
        result = subprocess.run([ADB_PATH, "connect", f"{ip_address}:{port}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

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
                            # Aplicativo desinstalado com sucesso
                            result_label.configure(text=f"Aplicativo com endereço: {app} deletado com sucesso!", text_color="green")
                        else:
                            # Mostra a saída do comando ADB para o aplicativo não excluído
                            result_label.configure(text=f"Erro ao excluir o aplicativo {app}: {result.stdout.strip()}", text_color="red")
                    except subprocess.CalledProcessError as e:
                        # Mostra a saída do comando ADB para o aplicativo não excluído
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

# Tema escuro do Ctk
ctk.set_appearance_mode("dark")  
ctk.set_default_color_theme("blue")  

# Janela principal
window = ctk.CTk()
window.title("Alterar DPI e Excluir Aplicativos via ADB")
window.geometry("500x600")

# Layout
title_label = ctk.CTkLabel(window, text="Mini PCS", font=("Arial", 20, "bold"))
title_label.pack(pady=20)

ip_label = ctk.CTkLabel(window, text="Endereço IP do dispositivo:")
ip_label.pack()

ip_entry = ctk.CTkEntry(window, width=300)
ip_entry.pack(pady=5)

app_label = ctk.CTkLabel(window, text="Adicionar aplicativo à lista de exclusão:")
app_label.pack()

app_entry = ctk.CTkEntry(window, width=300)
app_entry.pack(pady=5)

add_button = ctk.CTkButton(window, text="Adicionar à lista", command=add_app_to_list)
add_button.pack(pady=5)

app_listbox_label = ctk.CTkLabel(window, text="Lista de aplicativos para excluir:")
app_listbox_label.pack()

# Configura a Listbox com fundo escuro
app_listbox = tk.Listbox(window, width=50, height=10, bg="#2E2E2E", fg="white", selectbackground="#4A4A4A", selectforeground="white")
app_listbox.pack(pady=5)

# Cria o rodapé com duas partes de texto
footer_frame = ctk.CTkFrame(window)
footer_frame.pack(side="bottom", pady=10)

footer_label_normal = ctk.CTkLabel(footer_frame, text="v3.0 | Desenvolvido por", font=("Arial", 10), text_color="gray")
footer_label_normal.pack(side="left")

footer_label_bold = ctk.CTkLabel(footer_frame, text=" Ruã Fernandes", font=("Arial", 10, "bold"), text_color="gray")
footer_label_bold.pack(side="left")

# Adiciona os aplicativos existentes na lista
for app in app_list:
    app_listbox.insert(tk.END, app)

change_button = ctk.CTkButton(window, text="Alterar DPI e Excluir Aplicativos", command=change_dpi)
change_button.pack(pady=10)

result_label = ctk.CTkLabel(window, text="", font=("Helvetica", 12))
result_label.pack(pady=20)

window.mainloop()
