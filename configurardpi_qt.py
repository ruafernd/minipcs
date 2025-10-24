import sys
import subprocess
import os
import threading
import time
# Importações para sistema de atualização
import requests
import json
import zipfile
import shutil
from urllib.parse import urlparse
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
                             QPushButton, QCheckBox, QTextEdit, QGroupBox,
                             QFrame, QScrollArea, QSizePolicy, QDialog,
                             QListWidget, QMessageBox, QComboBox, QProgressBar,
                             QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QRect, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPainter, QPen, QBrush, QLinearGradient

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

    def uninstall_app_usb(self, device_id, app_package):
        """Desinstala um app via USB usando device_id"""
        try:
            result = subprocess.run(
                [self.adb_path, "-s", device_id, "uninstall", app_package],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0, result.stdout.strip() + result.stderr.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()
        except Exception as e:
            return False, str(e)

    def install_apk(self, apk_path, device_id=None):
        """Instala um APK no dispositivo"""
        try:
            cmd = [self.adb_path]
            if device_id:
                cmd.extend(["-s", device_id])
            cmd.extend(["install", "-r", apk_path])
            
            result = subprocess.run(
                cmd,
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

    def configure_tts_portuguese_brazil(self, device_id):
        """Configura síntese de voz para português brasileiro com voz 5"""
        try:
            commands_results = []
            
            # 1. Habilitar síntese de voz do Google
            result1 = subprocess.run(
                [self.adb_path, "-s", device_id, "shell", "settings", "put", "secure", 
                 "tts_default_synth", "com.google.android.tts"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            commands_results.append(("Definir Google TTS como padrão", result1))
            
            # 2. Definir idioma para português brasileiro
            result2 = subprocess.run(
                [self.adb_path, "-s", device_id, "shell", "settings", "put", "secure", 
                 "tts_default_locale", "pt-BR"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            commands_results.append(("Definir idioma pt-BR", result2))
            
            # 3. Configurar velocidade da fala (100 = normal)
            result3 = subprocess.run(
                [self.adb_path, "-s", device_id, "shell", "settings", "put", "secure", 
                 "tts_default_rate", "100"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            commands_results.append(("Configurar velocidade", result3))
            
            # 4. Configurar pitch da voz (100 = normal)
            result4 = subprocess.run(
                [self.adb_path, "-s", device_id, "shell", "settings", "put", "secure", 
                 "tts_default_pitch", "100"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            commands_results.append(("Configurar pitch", result4))
            
            # 5. Tentar configurar voz específica 5 - método 1
            result5 = subprocess.run(
                [self.adb_path, "-s", device_id, "shell", "settings", "put", "secure", 
                 "tts_default_variant", "5"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            commands_results.append(("Configurar variante de voz 5", result5))
            
            # 6. Configurar preferências específicas do Google TTS para voz 5
            result6 = subprocess.run(
                [self.adb_path, "-s", device_id, "shell", "settings", "put", "secure", 
                 "google_tts_voice_variant_pt_BR", "5"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            commands_results.append(("Configurar voz Google TTS pt-BR", result6))
            
            # 7. Tentar definir configuração de voz através de shared preferences (método alternativo)
            result7 = subprocess.run(
                [self.adb_path, "-s", device_id, "shell", "am", "broadcast", "-a", 
                 "android.speech.tts.engine.TTS_DATA_INSTALLED", "--es", "language", "pt-BR"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            commands_results.append(("Broadcast dados TTS instalados", result7))
            
            # 8. Configurar engine específico do Google TTS
            result8 = subprocess.run(
                [self.adb_path, "-s", device_id, "shell", "settings", "put", "secure", 
                 "tts_enabled_plugins", "com.google.android.tts/com.google.android.tts.service.GoogleTTSService"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            commands_results.append(("Habilitar plugin Google TTS", result8))
            
            # Contar sucessos e falhas
            successful_commands = sum(1 for _, result in commands_results if result.returncode == 0)
            total_commands = len(commands_results)
            
            # Preparar relatório detalhado
            success_details = []
            error_details = []
            
            for description, result in commands_results:
                if result.returncode == 0:
                    success_details.append(f"✓ {description}")
                else:
                    error_msg = result.stderr.strip() if result.stderr.strip() else "Erro desconhecido"
                    error_details.append(f"✗ {description}: {error_msg}")
            
            # Determinar se a configuração foi bem-sucedida
            critical_success = (
                commands_results[0][1].returncode == 0 and  # Google TTS como padrão
                commands_results[1][1].returncode == 0      # Idioma pt-BR
            )
            
            if critical_success:
                message = f"TTS configurado com sucesso ({successful_commands}/{total_commands} comandos)"
                if successful_commands == total_commands:
                    message += " - Configuração completa!"
                else:
                    message += f" - Alguns comandos opcionais falharam"
                return True, message
            else:
                message = f"Falha na configuração crítica do TTS ({successful_commands}/{total_commands} comandos)"
                if error_details:
                    message += f". Erros: {'; '.join(error_details[:3])}"  # Mostrar só os 3 primeiros erros
                return False, message
                
        except Exception as e:
            return False, f"Erro inesperado ao configurar TTS: {str(e)}"

    def install_tts_voice_data(self, device_id):
        """Instala dados de voz para português brasileiro"""
        try:
            # Tentar instalar dados de voz via comando de sistema
            result = subprocess.run(
                [self.adb_path, "-s", device_id, "shell", "am", "start", "-a", 
                 "android.speech.tts.engine.INSTALL_TTS_DATA", "-e", "language", "pt-BR"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                return True, "Comando de instalação de dados de voz enviado"
            else:
                return False, result.stderr.strip()
                
        except Exception as e:
            return False, str(e)

    def configure_tts_voice_5_advanced(self, device_id):
        """Configuração avançada para tentar definir especificamente a voz 5"""
        try:
            advanced_commands = []
            
            # Tentar diferentes métodos para configurar voz 5
            methods = [
                # Método 1: Configuração via settings específicos do Google TTS
                ([self.adb_path, "-s", device_id, "shell", "settings", "put", "secure", 
                  "com.google.android.tts.voice.pt_BR", "5"], "Google TTS voz pt-BR específica"),
                
                # Método 2: Configuração via sistema de preferências
                ([self.adb_path, "-s", device_id, "shell", "setprop", 
                  "persist.vendor.tts.voice.variant", "5"], "Propriedade sistema voz"),
                
                # Método 3: Broadcast para configurar voz
                ([self.adb_path, "-s", device_id, "shell", "am", "broadcast", "-a", 
                  "com.google.android.tts.SET_VOICE", "--es", "voice", "pt-BR-voice-5"], "Broadcast configurar voz"),
                
                # Método 4: Intent direto para configurações TTS
                ([self.adb_path, "-s", device_id, "shell", "am", "start", "-a", 
                  "android.intent.action.MAIN", "-n", "com.google.android.tts/.settings.TtsSettingsActivity"], "Abrir configurações TTS"),
                
                # Método 5: Configuração via content provider
                ([self.adb_path, "-s", device_id, "shell", "content", "insert", "--uri", 
                  "content://com.google.android.tts.settings", "--bind", "voice:s:5"], "Content provider TTS")
            ]
            
            results = []
            for command, description in methods:
                try:
                    result = subprocess.run(
                        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                        text=True, creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    results.append((description, result.returncode == 0, result.stderr.strip()))
                    advanced_commands.append(f"{'✓' if result.returncode == 0 else '✗'} {description}")
                except Exception as e:
                    results.append((description, False, str(e)))
                    advanced_commands.append(f"✗ {description}: {str(e)}")
            
            successful_methods = sum(1 for _, success, _ in results if success)
            total_methods = len(results)
            
            return successful_methods > 0, f"Métodos avançados: {successful_methods}/{total_methods} sucessos. {'; '.join(advanced_commands[:3])}"
            
        except Exception as e:
            return False, f"Erro nos métodos avançados: {str(e)}"

    def configure_tts_portuguese_brazil_simple(self, device_id):
        """Versão simplificada da configuração TTS para evitar erros de conexão"""
        try:
            # Verificar se o dispositivo ainda está conectado
            check_result = subprocess.run(
                [self.adb_path, "-s", device_id, "shell", "echo", "test"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if check_result.returncode != 0:
                return False, f"Dispositivo não encontrado: {device_id}"
            
            successful_commands = 0
            total_commands = 0
            
            # Comandos essenciais apenas
            essential_commands = [
                ("Definir Google TTS", ["settings", "put", "secure", "tts_default_synth", "com.google.android.tts"]),
                ("Definir idioma pt-BR", ["settings", "put", "secure", "tts_default_locale", "pt-BR"]),
                ("Configurar velocidade", ["settings", "put", "secure", "tts_default_rate", "100"]),
                ("Configurar voz 5", ["settings", "put", "secure", "tts_default_variant", "5"])
            ]
            
            for description, cmd_args in essential_commands:
                total_commands += 1
                try:
                    result = subprocess.run(
                        [self.adb_path, "-s", device_id, "shell"] + cmd_args,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW, timeout=10
                    )
                    
                    if result.returncode == 0:
                        successful_commands += 1
                    
                except subprocess.TimeoutExpired:
                    continue
                except Exception:
                    continue
            
            if successful_commands >= 2:  # Pelo menos TTS e idioma
                return True, f"TTS configurado ({successful_commands}/{total_commands} comandos)"
            else:
                return False, f"Falha na configuração TTS ({successful_commands}/{total_commands} comandos)"
                
        except Exception as e:
            return False, f"Erro ao configurar TTS: {str(e)}"

    def get_main_app_package(self, device_id, panel_type):
        """Detecta automaticamente o pacote principal instalado baseado no tipo de painel"""
        try:
            # Listar todos os pacotes instalados
            result = subprocess.run(
                [self.adb_path, "-s", device_id, "shell", "pm", "list", "packages"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=10
            )
            
            if result.returncode != 0:
                return None
            
            packages = result.stdout.strip().split('\n')
            
            # Padrões de busca baseados no tipo de painel
            search_patterns = {
                "Painel": ["painel", "panel", "roosevelt", "senha", "ai"],
                "Totem": ["totem", "ai", "kiosk", "display"]
            }
            
            patterns = search_patterns.get(panel_type, [])
            
            # Procurar por pacotes que contenham os padrões
            for package_line in packages:
                if package_line.startswith('package:'):
                    package_name = package_line.split(':')[1]
                    
                    # Verificar se o pacote contém algum dos padrões
                    for pattern in patterns:
                        if pattern.lower() in package_name.lower():
                            return package_name
            
            return None
            
        except Exception:
            return None

    def configure_app_autostart(self, device_id, panel_type):
        """Configura aplicativo para iniciar automaticamente no boot usando os comandos que funcionaram"""
        try:
            # Definir pacotes corretos para cada tipo
            main_app_packages = {
                "Painel": "com.example.roosevelt.painel_senha_digital",
                "Totem": "com.example.roosevelt.ai_autoatendimento"
            }
            
            main_package = main_app_packages.get(panel_type)
            if not main_package:
                return False, f"Tipo de painel não reconhecido: {panel_type}"
            
            # Verificar se o app está instalado
            check_result = subprocess.run(
                [self.adb_path, "-s", device_id, "shell", "pm", "list", "packages", main_package],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW, timeout=10
            )
            
            if main_package not in check_result.stdout:
                return False, f"App principal não encontrado: {main_package}"
            
            successful_commands = 0
            total_commands = 0
            results = []
            
            # Comandos que funcionaram no bash - adaptados para Python
            autostart_commands = [
                # 1. Desabilitar otimização de bateria
                (["dumpsys", "deviceidle", "whitelist", "+" + main_package], "Whitelist de bateria"),
                (["cmd", "appops", "set", main_package, "REQUEST_IGNORE_BATTERY_OPTIMIZATIONS", "allow"], "Ignorar otimização de bateria"),
                
                # 2. Permitir auto-start / background activity
                (["cmd", "appops", "set", main_package, "START_FOREGROUND", "allow"], "Permitir foreground"),
                (["cmd", "appops", "set", main_package, "SYSTEM_ALERT_WINDOW", "allow"], "Permitir janelas do sistema"),
                (["cmd", "appops", "set", main_package, "RUN_IN_BACKGROUND", "allow"], "Executar em background"),
                
                # 3. Desabilitar App Standby
                (["dumpsys", "usagestats", "set-standby-bucket", main_package, "10"], "Desabilitar App Standby"),
                
                # 4. Configurar como app crítico
                (["cmd", "deviceidle", "whitelist", "+" + main_package], "App crítico do sistema"),
                (["cmd", "appops", "set", main_package, "RUN_ANY_IN_BACKGROUND", "allow"], "Execução irrestrita"),
                
                # 5. Configurar Doze mode
                (["settings", "put", "global", "device_idle_constants", 
                  "inactive_to=7200000,sensing_to=0,locating_to=0,location_accuracy=20,motion_inactive_to=0,idle_after_inactive_to=0,idle_pending_to=300000,max_idle_pending_to=600000,idle_pending_factor=2.0,idle_to=3600000,max_idle_to=21600000,idle_factor=2.0,min_time_to_alarm=3600000,max_temp_app_whitelist_duration=300000,mms_temp_app_whitelist_duration=60000,sms_temp_app_whitelist_duration=20000"], 
                  "Configurar Doze mode"),
                
                # 6. Conceder permissões específicas
                (["pm", "grant", main_package, "android.permission.RECEIVE_BOOT_COMPLETED"], "Permissão BOOT_COMPLETED"),
                (["pm", "grant", main_package, "android.permission.SYSTEM_ALERT_WINDOW"], "Permissão janelas sistema"),
                (["pm", "grant", main_package, "android.permission.WAKE_LOCK"], "Permissão Wake Lock"),
                (["pm", "grant", main_package, "android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS"], "Permissão ignorar bateria")
            ]
            
            # Verificar versão do Android para comandos específicos
            try:
                android_version = subprocess.run(
                    [self.adb_path, "-s", device_id, "shell", "getprop", "ro.build.version.release"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW, timeout=5
                ).stdout.strip()
                
                # Comandos específicos por versão
                if android_version and int(android_version.split('.')[0]) >= 8:
                    autostart_commands.extend([
                        (["cmd", "appops", "set", main_package, "BOOT_COMPLETED", "allow"], "Permitir BOOT_COMPLETED"),
                        (["settings", "put", "global", "hidden_api_policy_pre_p_apps", "1"], "API Policy Pre-P"),
                        (["settings", "put", "global", "hidden_api_policy_p_apps", "1"], "API Policy P")
                    ])
                
                if android_version and int(android_version.split('.')[0]) >= 9:
                    autostart_commands.extend([
                        (["device_config", "put", "activity_manager", "default_background_activity_starts_enabled", "true"], "Background activity starts")
                    ])
                
                if android_version and int(android_version.split('.')[0]) >= 10:
                    autostart_commands.extend([
                        (["cmd", "appops", "set", main_package, "AUTO_START", "allow"], "Auto-start Android 10+")
                    ])
                    
            except Exception:
                # Se não conseguir detectar a versão, continuar sem os comandos específicos
                pass
            
            # Executar todos os comandos
            for cmd_args, description in autostart_commands:
                total_commands += 1
                try:
                    result = subprocess.run(
                        [self.adb_path, "-s", device_id, "shell"] + cmd_args,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                        creationflags=subprocess.CREATE_NO_WINDOW, timeout=15
                    )
                    
                    if result.returncode == 0:
                        successful_commands += 1
                        results.append(f"✓ {description}")
                    else:
                        # Alguns comandos podem falhar mas isso é OK para alguns casos
                        error_msg = result.stderr.strip().lower()
                        if any(x in error_msg for x in ["unknown command", "not found", "permission denied", "invalid"]):
                            results.append(f"⚠️ {description}: Comando não disponível (ignorando)")
                        else:
                            results.append(f"✗ {description}: {result.stderr.strip()[:50]}")
                    
                except subprocess.TimeoutExpired:
                    results.append(f"✗ {description}: Timeout")
                    continue
                except Exception as e:
                    results.append(f"✗ {description}: {str(e)[:50]}")
                    continue
            
            # Consideramos sucesso se pelo menos 60% dos comandos funcionaram
            success_rate = successful_commands / total_commands if total_commands > 0 else 0
            
            if success_rate >= 0.6:
                # Após configurar o auto-start, iniciar o painel uma vez
                try:
                    # Tentar diferentes formas de iniciar o app
                    start_commands = [
                        # Método 1: Via SplashActivity (mais comum)
                        (["am", "start", "-n", main_package + "/.SplashActivity"], "Iniciar via SplashActivity"),
                        # Método 2: Via MainActivity (fallback)
                        (["am", "start", "-n", main_package + "/.MainActivity"], "Iniciar via MainActivity"),
                        # Método 3: Via launcher (genérico)
                        (["monkey", "-p", main_package, "-c", "android.intent.category.LAUNCHER", "1"], "Iniciar via launcher")
                    ]
                    
                    app_started = False
                    for start_cmd, start_desc in start_commands:
                        try:
                            start_result = subprocess.run(
                                [self.adb_path, "-s", device_id, "shell"] + start_cmd,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                creationflags=subprocess.CREATE_NO_WINDOW, timeout=10
                            )
                            
                            if start_result.returncode == 0:
                                results.append(f"✓ {start_desc}")
                                app_started = True
                                break
                            else:
                                results.append(f"⚠️ {start_desc}: {start_result.stderr.strip()[:30]}")
                        except Exception:
                            continue
                    
                    if app_started:
                        results.append("✓ App iniciado com sucesso - configuração ativada")
                        
                        # Aguardar um pouco para o app carregar
                        import time
                        time.sleep(10)
                        
                        # Reiniciar o dispositivo para testar o auto-start
                        try:
                            reboot_result = subprocess.run(
                                [self.adb_path, "-s", device_id, "reboot"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                creationflags=subprocess.CREATE_NO_WINDOW, timeout=5
                            )
                            
                            if reboot_result.returncode == 0:
                                results.append("✓ Dispositivo reiniciado para testar auto-start")
                                summary = f"Auto-start configurado, testado e dispositivo reiniciado para {main_package}"
                            else:
                                results.append("⚠️ Configurado mas falha ao reiniciar - reinicie manualmente")
                                summary = f"Auto-start configurado para {main_package} - REINICIE MANUALMENTE para testar"
                        except Exception:
                            results.append("⚠️ Configurado mas falha ao reiniciar - reinicie manualmente")
                            summary = f"Auto-start configurado para {main_package} - REINICIE MANUALMENTE para testar"
                    else:
                        results.append("⚠️ Configurado mas falha ao iniciar app - inicie manualmente e reinicie")
                        summary = f"Auto-start configurado para {main_package} - INICIE O APP MANUALMENTE e depois reinicie"
                        
                except Exception as e:
                    results.append(f"⚠️ Configurado mas erro ao iniciar app: {str(e)[:50]}")
                    summary = f"Auto-start configurado para {main_package} - INICIE O APP MANUALMENTE e depois reinicie"
                
                detailed_results = "; ".join(results[:6])  # Mostrar mais resultados agora
                return True, f"{summary}. Detalhes: {detailed_results}"
            else:
                return False, f"Falha na configuração de auto-start para {main_package} ({successful_commands}/{total_commands} comandos). Resultados: {'; '.join(results[:3])}"
                
        except Exception as e:
            return False, f"Erro ao configurar auto-start: {str(e)}"

class AppManager:
    def __init__(self):
        self.default_apps = {
            # Apps básicos - igual ao arquivo original
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

class APKManager:
    def __init__(self):
        # Definir caminho base no Program Files
        self.base_path = r"C:\Program Files\MiniPcs"
        
        # Criar estrutura de pastas se não existir
        self.create_folder_structure()
        
        self.apk_lists = {
            "Painel": [
                os.path.join(self.base_path, "Painel", "painel_ai.apk"),
                os.path.join(self.base_path, "Painel", "adb.apk"),
                os.path.join(self.base_path, "Painel", "sintese.apk")
            ],
            "Totem": [
                os.path.join(self.base_path, "Totem", "totem_ai.apk"),
                os.path.join(self.base_path, "Totem", "adb.apk"),
                os.path.join(self.base_path, "Totem", "sintese.apk")
            ]
        }
    
    def create_folder_structure(self):
        """Cria a estrutura de pastas se não existir"""
        try:
            # Criar pasta principal
            if not os.path.exists(self.base_path):
                os.makedirs(self.base_path)
                print(f"Pasta criada: {self.base_path}")
            
            # Criar subpastas para cada configuração
            folders = ["Painel", "Totem"]
            for folder in folders:
                folder_path = os.path.join(self.base_path, folder)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                    print(f"Pasta criada: {folder_path}")
                
                # Criar arquivo de template se a pasta estiver vazia
                self.create_template_if_empty(folder_path, folder)
                    
        except PermissionError:
            # Se não tiver permissão no Program Files, usar pasta do usuário
            import getpass
            username = getpass.getuser()
            self.base_path = rf"C:\Users\{username}\AppData\Local\MiniPcs"
            print(f"Sem permissão no Program Files, usando: {self.base_path}")
            
            # Tentar criar na pasta do usuário
            try:
                if not os.path.exists(self.base_path):
                    os.makedirs(self.base_path)
                
                folders = ["Painel", "Totem"]
                for folder in folders:
                    folder_path = os.path.join(self.base_path, folder)
                    if not os.path.exists(folder_path):
                        os.makedirs(folder_path)
                    
                    # Criar arquivo de template se a pasta estiver vazia
                    self.create_template_if_empty(folder_path, folder)
                        
                # Atualizar caminhos dos APKs
                self.update_apk_paths()
                        
            except Exception as e:
                print(f"Erro ao criar pastas: {e}")
                # Usar pasta relativa como fallback
                self.base_path = "apps"
                if not os.path.exists(self.base_path):
                    os.makedirs(self.base_path)
        except Exception as e:
            print(f"Erro inesperado: {e}")
            # Usar pasta relativa como fallback
            self.base_path = "apps"
            if not os.path.exists(self.base_path):
                os.makedirs(self.base_path)
    
    def create_template_if_empty(self, folder_path, folder_name):
        """Cria arquivo de template se a pasta estiver vazia"""
        try:
            # Verificar se a pasta está vazia (ignorar arquivos de template)
            files = [f for f in os.listdir(folder_path) if not f.startswith('TEMPLATE_') and f.endswith('.apk')]
            
            if len(files) == 0:  # Pasta vazia de APKs
                template_file = os.path.join(folder_path, "TEMPLATE_Lista_de_APKs.txt")
                
                # Definir conteúdo do template baseado no tipo de painel
                if folder_name == "Painel":
                    content = """TEMPLATE - Painel
==================

Coloque os seguintes arquivos APK nesta pasta:

✓ painel_ai.apk
✓ adb.apk
✓ sintese.apk

INSTRUÇÕES:
1. Baixe os APKs necessários
2. Renomeie-os conforme a lista acima
3. Coloque-os nesta pasta
4. Delete este arquivo de template
5. Use a função "Configurar Rápido" no aplicativo

NOTA: A configuração de auto-start é feita automaticamente 
via comandos do sistema (não precisa mais do auto_start.apk)

Pasta: {folder_path}
""".format(folder_path=folder_path)
                
                elif folder_name == "Totem":
                    content = """TEMPLATE - Totem
=================

Coloque os seguintes arquivos APK nesta pasta:

✓ totem_ai.apk
✓ adb.apk

INSTRUÇÕES:
1. Baixe os APKs necessários
2. Renomeie-os conforme a lista acima
3. Coloque-os nesta pasta
4. Delete este arquivo de template
5. Use a função "Configurar Rápido" no aplicativo

NOTA: A configuração de auto-start é feita automaticamente 
via comandos do sistema (não precisa mais do auto_start.apk)

Pasta: {folder_path}
""".format(folder_path=folder_path)
                
                # Criar o arquivo de template
                with open(template_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Template criado: {template_file}")
                
        except Exception as e:
            print(f"Erro ao criar template para {folder_name}: {e}")
    
    def update_apk_paths(self):
        """Atualiza os caminhos dos APKs após mudança do base_path"""
        self.apk_lists = {
            "Painel": [
                os.path.join(self.base_path, "Painel", "painel_ai.apk"),
                os.path.join(self.base_path, "Painel", "adb.apk"),
                os.path.join(self.base_path, "Painel", "sintese.apk")
            ],
            "Totem": [
                os.path.join(self.base_path, "Totem", "totem_ai.apk"),
                os.path.join(self.base_path, "Totem", "adb.apk"),
                os.path.join(self.base_path, "Totem", "sintese.apk")
            ]
        }
    
    def get_apk_list(self, panel_type):
        """Retorna a lista de APKs para o tipo de painel especificado"""
        return self.apk_lists.get(panel_type, [])
    
    def get_panel_types(self):
        """Retorna os tipos de painéis disponíveis"""
        return list(self.apk_lists.keys())
    
    def get_base_path(self):
        """Retorna o caminho base onde estão as pastas dos APKs"""
        return self.base_path

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
                        # Melhor detecção de tipos de erro
                        message_lower = message.lower()
                        
                        if "DELETE_FAILED_DEVICE_POLICY_MANAGER" in message or "DELETE_FAILED_INTERNAL_ERROR" in message:
                            self.progress.emit(f"Dispositivo {device_num}: {app} não pode ser removido (app do sistema)")
                        elif "not installed" in message_lower or "not found" in message_lower or "unknown package" in message_lower:
                            self.progress.emit(f"Dispositivo {device_num}: {app} não está instalado (ignorando)")
                        elif message.strip() == "":
                            self.progress.emit(f"Dispositivo {device_num}: {app} não está instalado (sem resposta)")
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

class USBWorkerThread(QThread):
    finished = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, adb_manager, app_manager, apk_manager, panel_type):
        super().__init__()
        self.adb_manager = adb_manager
        self.app_manager = app_manager
        self.apk_manager = apk_manager
        self.panel_type = panel_type

    def run(self):
        try:
            self.progress.emit("🔍 Verificando dispositivos USB...")
            
            # Verificar dispositivos USB conectados
            result = subprocess.run(
                [self.adb_manager.adb_path, "devices"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode != 0:
                self.finished.emit(f"❌ Erro ao executar 'adb devices': {result.stderr}")
                return
            
            devices_output = result.stdout.strip()
            self.progress.emit(f"📱 Saída do comando 'adb devices':\n{devices_output}")
            
            # Verificar se há dispositivos conectados
            connected_devices = []
            for line in devices_output.split('\n'):
                if line.strip() and not line.startswith('List of devices') and '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    connected_devices.append(device_id)
            
            if not connected_devices:
                self.finished.emit("❌ Nenhum dispositivo USB encontrado. Conecte um dispositivo via USB.")
                return
            
            self.progress.emit(f"✅ Dispositivos encontrados: {len(connected_devices)}")
            
            # Processar todos os dispositivos conectados sequencialmente
            processed = 0
            for idx, device_id in enumerate(connected_devices, start=1):
                self.progress.emit(f"\n🔌 Dispositivo {idx}/{len(connected_devices)}: {device_id}")
                
                # CONFIGURAÇÃO RÁPIDA USB - Foco em instalação e configuração, não remoção
                self.progress.emit("⚡ Configuração Rápida: Foco em instalação de APKs e configuração")
                self.progress.emit("ℹ️ Para remoção de apps, use a configuração manual via Wi-Fi")
                
                # Instalar APKs do painel selecionado
                apk_list = self.apk_manager.get_apk_list(self.panel_type)
                if apk_list:
                    self.progress.emit(f"📦 Iniciando instalação de aplicativos do {self.panel_type}...")
                    self.progress.emit(f"📋 Total de APKs para instalar: {len(apk_list)}")
                    
                    installed_count = 0
                    failed_count = 0
                    
                    for i, apk_path in enumerate(apk_list, 1):
                        apk_name = os.path.basename(apk_path)
                        self.progress.emit(f"⬇️ [{i}/{len(apk_list)}] Instalando {apk_name}...")
                        
                        if os.path.exists(apk_path):
                            success, message = self.adb_manager.install_apk(apk_path, device_id)
                            if success:
                                self.progress.emit(f"✅ [{i}/{len(apk_list)}] {apk_name} instalado com sucesso!")
                                installed_count += 1
                            else:
                                self.progress.emit(f"❌ [{i}/{len(apk_list)}] Erro ao instalar {apk_name}: {message}")
                                failed_count += 1
                        else:
                            self.progress.emit(f"⚠️ [{i}/{len(apk_list)}] APK não encontrado: {apk_path}")
                            failed_count += 1
                    
                    # Resumo da instalação
                    self.progress.emit(f"📊 Resumo da instalação:")
                    self.progress.emit(f"   ✅ Instalados com sucesso: {installed_count}")
                    self.progress.emit(f"   ❌ Falharam: {failed_count}")
                    self.progress.emit(f"   📦 Total processado: {len(apk_list)}")
                else:
                    self.progress.emit(f"⚠️ Nenhum APK encontrado para {self.panel_type}")
                
                # Alterar DPI para 160
                self.progress.emit("🔧 Alterando DPI para 160...")
                dpi_result = subprocess.run(
                    [self.adb_manager.adb_path, "-s", device_id, "shell", "wm", "density", "160"],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                if dpi_result.returncode != 0:
                    self.progress.emit(f"❌ Erro ao alterar DPI: {dpi_result.stderr}")
                else:
                    self.progress.emit("✅ DPI alterado com sucesso para 160!")
                
                # Configurar TTS para português brasileiro (apenas para painéis)
                # DESABILITADO: Instalação automática da síntese de voz comentada
                # if "Painel" in self.panel_type:
                #     self.progress.emit("🗣️ Configurando síntese de voz para português brasileiro...")
                #     
                #     # Usar versão simplificada para evitar problemas de conexão
                #     tts_success, tts_message = self.adb_manager.configure_tts_portuguese_brazil_simple(device_id)
                #     if tts_success:
                #         self.progress.emit(f"✅ {tts_message}")
                #         self.progress.emit("ℹ️ TTS configurado: Google TTS, pt-BR, voz 5, velocidade normal")
                #     else:
                #         self.progress.emit(f"⚠️ Problema na configuração TTS: {tts_message}")
                #         self.progress.emit("ℹ️ Você pode configurar manualmente: Configurações → Acessibilidade → TTS")
                
                # Configurar auto-start do aplicativo principal (para painéis e totem)
                if self.panel_type in ["Painel", "Totem"]:
                    self.progress.emit("🚀 Configurando inicialização automática do aplicativo...")
                    
                    autostart_success, autostart_message = self.adb_manager.configure_app_autostart(device_id, self.panel_type)
                    if autostart_success:
                        self.progress.emit(f"✅ {autostart_message}")
                        self.progress.emit("ℹ️ App configurado para iniciar automaticamente no boot")
                    else:
                        self.progress.emit(f"⚠️ Problema na configuração de auto-start: {autostart_message}")
                        self.progress.emit("ℹ️ Você pode configurar manualmente nas configurações do dispositivo")
                
                processed += 1
            
            # Mensagem final sobre o reboot - agora é feito automaticamente pelo auto-start
            self.progress.emit("ℹ️ Configuração concluída!")
            if "Painel" in self.panel_type:
                self.progress.emit("💡 O dispositivo foi reiniciado automaticamente para testar o auto-start.")
                self.progress.emit("💡 Aguarde o boot completo e verifique se o painel inicia sozinho.")
            else:
                self.progress.emit("💡 O dispositivo foi reiniciado automaticamente para testar o auto-start.")
            
            self.finished.emit(f"🎉 Configuração do {self.panel_type} concluída para {processed} dispositivo(s)!")
                
        except Exception as e:
            self.finished.emit(f"❌ Erro inesperado: {str(e)}")

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
            QDialog { background-color: #0f1116; color: #e6e6e6; }
            QLabel { color: #e6e6e6; font-size: 12px; }
            QGroupBox { font-weight: bold; border: 1px solid #3a4056; border-radius: 10px; margin-top: 10px; padding-top: 10px; background-color: #121725; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #c8cbe0; }
            QListWidget { background-color: #0f121a; border: 1px solid #2b3040; border-radius: 10px; color: #e6e6e6; font-size: 12px; padding: 6px; }
            QListWidget::item { padding: 6px; border-bottom: 1px solid #262b3a; }
            QListWidget::item:selected { background-color: #4d58ff; }
            QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4d58ff, stop:1 #8a46ff); border: none; color: white; padding: 9px 16px; border-radius: 10px; font-weight: 700; }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5a63ff, stop:1 #9b52ff); }
            QPushButton#select_all { background: #19c37d; }
            QPushButton#select_all:hover { background: #17b67f; }
            QPushButton#deselect_all { background: #ff6b35; }
            QPushButton#deselect_all:hover { background: #e55a2b; }
            QScrollBar:vertical { background:#1a1d26; width:10px; border:none; }
            QScrollBar::handle:vertical { background:#3a4056; border-radius:5px; min-height:20px; }
            QScrollBar::handle:vertical:hover { background:#4b5270; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title_label = QLabel("Aplicativos Instalados no Dispositivo")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
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
                self.show_message_box("Erro", "Não foi possível conectar ao dispositivo.", "critical")
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
            self.show_message_box("Erro", f"Erro ao carregar aplicativos: {e.stderr.decode()}", "critical")
        except Exception as e:
            self.show_message_box("Erro", f"Erro inesperado: {str(e)}", "critical")

    def show_message_box(self, title, message, icon_type="information"):
        """Cria um QMessageBox com tema escuro"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        # Definir ícone
        if icon_type == "information":
            msg_box.setIcon(QMessageBox.Icon.Information)
        elif icon_type == "warning":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        elif icon_type == "critical":
            msg_box.setIcon(QMessageBox.Icon.Critical)
        
        # Aplicar estilo escuro
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
                color: white;
            }
            QMessageBox QLabel {
                color: white;
                background-color: transparent;
                font-size: 12px;
            }
            QMessageBox QPushButton {
                background-color: #0078d4;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        
        return msg_box.exec()

    def select_all(self):
        for i in range(self.app_list.count()):
            self.app_list.item(i).setSelected(True)

    def deselect_all(self):
        self.app_list.clearSelection()

    def add_selected_to_list(self):
        selected_items = self.app_list.selectedItems()
        if not selected_items:
            self.show_message_box("Informação", "Nenhum aplicativo selecionado.", "information")
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
            self.show_message_box("Sucesso", f"{added_count} aplicativo(s) adicionado(s) à lista.", "information")
        else:
            self.show_message_box("Informação", "Todos os aplicativos selecionados já estão na lista.", "information")
        
        self.accept()

class DefaultAppsDialog(QDialog):
    def __init__(self, parent, app_manager):
        super().__init__(parent)
        self.app_manager = app_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Aplicativos para Remoção")
        self.setGeometry(200, 200, 500, 600)
        self.setStyleSheet("""
            QDialog { background-color: #0f1116; color: #e6e6e6; }
            QWidget { background-color: #0f1116; color: #e6e6e6; }
            QGroupBox { font-weight: bold; border: 1px solid #3a4056; border-radius: 10px; margin-top: 10px; padding-top: 10px; background-color: #121725; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #c8cbe0; }
            QCheckBox { color: #e6e6e6; font-size: 12px; spacing: 8px; padding: 3px; background-color: transparent; }
            QCheckBox::indicator { width: 18px; height: 18px; }
            QCheckBox::indicator:unchecked { border: 2px solid #2b3040; background-color: #141822; border-radius: 4px; }
            QCheckBox::indicator:checked { border: 2px solid #4d58ff; background-color: #4d58ff; border-radius: 4px; }
            QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4d58ff, stop:1 #8a46ff); border: none; color: white; padding: 9px 16px; border-radius: 10px; font-weight: 700; }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5a63ff, stop:1 #9b52ff); }
            QPushButton#select_all { background: #19c37d; }
            QPushButton#select_all:hover { background: #17b67f; }
            QPushButton#deselect_all { background: #ff6b35; }
            QPushButton#deselect_all:hover { background: #e55a2b; }
            QLabel { color: #e6e6e6; font-size: 12px; background-color: transparent; }
            QScrollArea { border: 1px solid #2b3040; border-radius: 10px; background-color: #0f121a; }
            QScrollArea QWidget { background-color: #0f121a; color: #e6e6e6; }
            QScrollBar:vertical { background:#1a1d26; width:10px; border:none; }
            QScrollBar::handle:vertical { background:#3a4056; border-radius:5px; min-height:20px; }
            QScrollBar::handle:vertical:hover { background:#4b5270; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title_label = QLabel("Aplicativos que serão removidos automaticamente:")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title_label)

        # Área de scroll para os checkboxes
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Criar checkboxes para cada app
        self.app_checkboxes = {}
        for app_name in self.app_manager.default_apps.keys():
            checkbox = QCheckBox(app_name)
            checkbox.setChecked(self.app_manager.default_apps[app_name])
            checkbox.toggled.connect(lambda checked, app=app_name: self.toggle_app(app, checked))
            self.app_checkboxes[app_name] = checkbox
            scroll_layout.addWidget(checkbox)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(400)
        layout.addWidget(scroll_area)

        # Botões de controle
        buttons_layout = QHBoxLayout()
        
        select_all_button = QPushButton("Selecionar Todos")
        select_all_button.setObjectName("select_all")
        select_all_button.clicked.connect(self.select_all)
        buttons_layout.addWidget(select_all_button)
        
        deselect_all_button = QPushButton("Desmarcar Todos")
        deselect_all_button.setObjectName("deselect_all")
        deselect_all_button.clicked.connect(self.deselect_all)
        buttons_layout.addWidget(deselect_all_button)
        
        buttons_layout.addStretch()
        
        # Botões OK/Cancel
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        buttons_layout.addWidget(ok_button)
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(buttons_layout)

    def toggle_app(self, app_name, checked):
        """Alterna o status de um app"""
        self.app_manager.default_apps[app_name] = checked
        if checked and app_name not in self.app_manager.app_list:
            self.app_manager.app_list.append(app_name)
        elif not checked and app_name in self.app_manager.app_list:
            self.app_manager.app_list.remove(app_name)

    def select_all(self):
        """Seleciona todos os apps"""
        for checkbox in self.app_checkboxes.values():
            checkbox.setChecked(True)

    def deselect_all(self):
        """Desmarca todos os apps"""
        for checkbox in self.app_checkboxes.values():
            checkbox.setChecked(False)

class ConfiguradorDPI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.adb_manager = ADBManager()
        self.app_manager = AppManager()
        self.apk_manager = APKManager()
        self.update_manager = UpdateManager()  # Adicionar gerenciador de atualizações
        
        # Controles para evitar verificações múltiplas
        self.checking_updates = False
        self.update_dialog_open = False
        
        self.load_settings()
        self.init_ui()
        self.setup_auto_update_check()  # Configurar verificação automática

    def setup_auto_update_check(self):
        """Configura a verificação automática de atualizações"""
        # Timer para verificar atualizações na inicialização (após 5 segundos)
        self.startup_update_timer = QTimer()
        self.startup_update_timer.setSingleShot(True)
        self.startup_update_timer.timeout.connect(self.check_updates_silent)
        self.startup_update_timer.start(5000)  # 5 segundos após a inicialização
        
        # Timer para verificações periódicas (a cada 2 horas)
        self.periodic_update_timer = QTimer()
        self.periodic_update_timer.timeout.connect(self.check_updates_silent)
        self.periodic_update_timer.start(2 * 60 * 60 * 1000)  # 2 horas em milissegundos

    def check_updates_silent(self):
        """Verifica atualizações silenciosamente em segundo plano"""
        if self.checking_updates or self.update_dialog_open:
            return
        
        self.checking_updates = True
        self.update_worker = UpdateWorkerThread(self.update_manager)
        self.update_worker.update_available.connect(self.on_update_available)
        self.update_worker.error_occurred.connect(self.on_update_error)
        self.update_worker.finished.connect(lambda: setattr(self, 'checking_updates', False))
        self.update_worker.start()

    def check_updates_manual(self):
        """Verifica atualizações manualmente (acionado pelo botão)"""
        if self.checking_updates:
            self.result_text.append("⏳ Verificação já em andamento...")
            return
        
        # Mostrar feedback visual
        if hasattr(self, 'update_button'):
            self.update_button.setEnabled(False)
            self.update_button.setText("Verificando...")
        
        self.result_text.append("🔍 Verificando atualizações...")
        self.checking_updates = True
        
        self.manual_update_worker = UpdateWorkerThread(self.update_manager)
        self.manual_update_worker.update_available.connect(self.on_update_available)
        self.manual_update_worker.error_occurred.connect(self.on_manual_update_error)
        self.manual_update_worker.finished.connect(self.on_manual_check_finished)
        self.manual_update_worker.start()

    def on_update_available(self, update_info):
        """Chamado quando uma atualização está disponível"""
        if self.update_dialog_open:
            return
        
        self.update_dialog_open = True
        dialog = UpdateDialog(self, update_info)
        dialog.finished.connect(lambda: setattr(self, 'update_dialog_open', False))
        dialog.exec()

    def on_update_error(self, error_message):
        """Chamado quando há erro na verificação silenciosa (não mostra ao usuário)"""
        self.checking_updates = False
        # Log silencioso - pode ser usado para debug
        pass

    def on_manual_update_error(self, error_message):
        """Chamado quando há erro na verificação manual"""
        self.checking_updates = False
        self.result_text.append(f"❌ Erro ao verificar atualizações: {error_message}")

    def on_manual_check_finished(self):
        """Chamado quando a verificação manual termina"""
        self.checking_updates = False
        
        if hasattr(self, 'update_button'):
            self.update_button.setEnabled(True)
            self.update_button.setText("⟳ Buscar Atualizações")
        
        # Se chegou até aqui sem mostrar diálogo, não há atualizações
        if not self.update_dialog_open:
            self.result_text.append("✅ Você está usando a versão mais recente!")

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
        self.setWindowTitle("Configurador de Mini PCS")
        self.setGeometry(100, 100, 600, 720)
        
        # Definir ícone da aplicação (método robusto)
        self.apply_window_icon()
        
        # Configurar estilo (tema novo)
        self.setStyleSheet("""
            /* Paleta base */
            * { font-family: 'Segoe UI', 'Inter', 'Roboto', sans-serif; }
            QMainWindow { background-color: #0f1116; color: #e6e6e6; }
            QWidget   { color: #e6e6e6; }

            /* Hero (cabeçalho) - versão clean */
            QFrame#Hero {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                          stop:0 #141824, stop:1 #1a1f2d);
                border-radius: 16px;
                padding: 22px;
                border: 1px solid #262b3a;
            }
            QLabel#HeroTitle { font-size: 24px; font-weight: 800; color: #ffffff; }
            QLabel#HeroSubtitle { font-size: 12px; color: #b9bfd3; }

            /* Cards */
            QGroupBox#Card {
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 14px;
                margin-top: 18px; /* espaço para o título */
                padding-top: 14px;
            }
            QGroupBox#Card::title {
                subcontrol-origin: margin; left: 16px; top: 10px;
                color: #b9b9ff; font-weight: 700; padding: 0 6px;
                background-color: transparent;
            }

            /* Inputs */
            QLineEdit, QComboBox {
                min-height: 38px; padding: 6px 12px; border-radius: 10px; font-size: 13px;
                background-color: #1a1d26; color: #ffffff;
                border: 1px solid #3a4056;
            }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #6a6fff; }
            QComboBox { padding-right: 42px; }
            QComboBox::drop-down {
                subcontrol-origin: padding; subcontrol-position: center right;
                border-left: 1px solid #3a4056; background: #151824; width: 20px;
                border-top-right-radius: 10px; border-bottom-right-radius: 10px;
            }
            QComboBox::down-arrow {
                /* seta custom visível e mais grossa */
                image: url(:/qt-project.org/styles/commonstyle/images/arrowdown-16.png);
                width: 14px; height: 14px; margin-right: 10px; margin-top: 1px; margin-left: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1d26; color: #ffffff; selection-background-color: #4d58ff;
                border: 1px solid #2b3040; border-radius: 8px; }

            /* Botões */
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                          stop:0 #4d58ff, stop:1 #8a46ff);
                border: none; color: white; padding: 11px 20px; border-radius: 10px;
                font-weight: 700; letter-spacing: 0.3px; font-size: 13px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                          stop:0 #5a63ff, stop:1 #9b52ff);
            }
            QPushButton:pressed { background-color: #3b3fc9; }

            QPushButton#usb {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                          stop:0 #ff7a45, stop:1 #ff4c68);
            }
            QPushButton#usb:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                          stop:0 #ff8a5b, stop:1 #ff5e79);
            }
            QPushButton#main {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                          stop:0 #19c37d, stop:1 #13a06f);
                font-size: 15px; padding: 14px 24px; border-radius: 12px;
            }
            QPushButton#main:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                          stop:0 #22d28a, stop:1 #17b67f);
            }

            /* Checkboxes */
            QCheckBox { color: #e6e6e6; font-size: 12px; }
            QCheckBox::indicator { width: 20px; height: 20px; }
            QCheckBox::indicator:unchecked { border: 2px solid #2b3040; background: #141822; border-radius: 4px; }
            QCheckBox::indicator:checked   { border: 2px solid #4d58ff; background: #4d58ff; border-radius: 4px; }

            /* Labels de status */
            QLabel#status { font-size: 11px; padding: 6px 10px; border-radius: 8px; }

            /* TextEdit / Logs */
            QTextEdit {
                background-color: #0f121a; border: 1px solid #23283a;
                border-radius: 12px; color: #dcdcdc; font-size: 11px;
            }

            /* Dialogs */
            QMessageBox { background-color: #121521; color: white; }
            QMessageBox QLabel { color: white; background-color: transparent; font-size: 12px; }
            QMessageBox QPushButton { background-color: #4d58ff; border: none; color: white;
                padding: 8px 16px; border-radius: 8px; font-weight: 700; min-width: 90px; }
            QMessageBox QPushButton:hover { background-color: #5a63ff; }

            /* Barra de progresso */
            QProgressBar { border: 1px solid #2b3040; border-radius: 10px; text-align: center; background: #141822; color: #ddd; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4d58ff, stop:1 #8a46ff); border-radius: 8px; }
        """)

        # Widget central com layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(16, 14, 16, 14)

        # Cabeçalho hero
        self.create_header(main_layout)
        
        # Seção USB
        self.create_usb_section(main_layout)
        
        # Seção de dispositivos
        self.create_devices_section(main_layout)
        
        # Botão principal
        self.create_main_button(main_layout)
        
        # Área de resultado
        self.create_result_area(main_layout)
        
        # Rodapé
        self.create_footer(main_layout)

        # Garantir seta visível no QComboBox específico (panel_combo)
        try:
            arrow_svg = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'arrow_down_white.svg')
            if not os.path.exists(arrow_svg):
                svg_content = """
<svg width="12" height="12" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
  <path d="M6 9l6 6 6-6" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""
                with open(arrow_svg, 'w', encoding='utf-8') as f:
                    f.write(svg_content)
            svg_path = arrow_svg.replace('\\', '/')
            # aplica somente ao combo de painel
            self.panel_combo.setStyleSheet(self.panel_combo.styleSheet() + f" QComboBox::down-arrow {{ image: url({svg_path}); width: 12px; height: 12px; margin-right: 10px; }}")
        except Exception as e:
            print(f"Falha ao aplicar seta customizada: {e}")

    def create_header(self, parent_layout):
        hero = QFrame()
        hero.setObjectName("Hero")
        h_layout = QHBoxLayout(hero)
        h_layout.setContentsMargins(24, 18, 24, 18)
        h_layout.setSpacing(16)

        left = QVBoxLayout()
        title = QLabel("Configurador de Mini PCS")
        title.setObjectName("HeroTitle")
        subtitle = QLabel("Instalação rápida por USB, Wi‑Fi, remoção de apps, DPI, TTS e auto‑start.")
        subtitle.setWordWrap(True)
        subtitle.setObjectName("HeroSubtitle")
        left.addWidget(title)
        left.addWidget(subtitle)

        # Faixa decorativa vertical (animada)
        ribbon = AnimatedLineWidget()

        # Lado direito com badge e pequeno ícone 
        right_box = QVBoxLayout()
        right_box.setSpacing(6)
        badge = QLabel("v10.5")
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge.setStyleSheet("padding:6px 10px; border-radius:8px; background-color: rgba(106,111,255,0.18); font-weight:700;")
        right_box.addWidget(badge, alignment=Qt.AlignmentFlag.AlignRight)
        mark = QLabel("●")
        mark.setStyleSheet("color:#6a6fff; font-size:18px;")
        right_box.addWidget(mark, alignment=Qt.AlignmentFlag.AlignRight)
        right_box.addStretch()

        h_layout.addLayout(left, stretch=10)
        h_layout.addWidget(ribbon)
        h_layout.addLayout(right_box, stretch=1)

        # Sombra sutil no hero
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(26)
        effect.setColor(QColor(0, 0, 0, 160))
        effect.setOffset(0, 12)
        hero.setGraphicsEffect(effect)

        parent_layout.addWidget(hero)

    def _apply_card_effect(self, widget: QWidget):
        widget.setObjectName("Card")
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(24)
        effect.setColor(QColor(0, 0, 0, 140))
        effect.setOffset(0, 12)
        widget.setGraphicsEffect(effect)

    def create_devices_section(self, parent_layout):
        devices_group = QGroupBox("Configuração de Dispositivos por Wi-Fi")
        self._apply_card_effect(devices_group)
        devices_layout = QVBoxLayout(devices_group)
        
        # Container para os dois dispositivos
        devices_container = QHBoxLayout()
        
        # Dispositivo 1
        device1_group = QGroupBox("Dispositivo 1")
        device1_group.setStyleSheet(
            "QGroupBox{border:1px solid #3a4056; border-radius:8px; margin-top:6px; padding-top:2px;}"
            " QGroupBox::title{subcontrol-origin: margin; left:10px; top:-4px; color:#c8cbe0;}"
        )
        device1_layout = QVBoxLayout(device1_group)
        
        # Status do dispositivo 1 (em cima)
        self.status_label1 = QLabel("Dispositivo não conectado")
        self.status_label1.setMinimumHeight(32)
        self.status_label1.setObjectName("status")
        self.status_label1.setStyleSheet("color: #ff6b6b; background-color: #1a1d26; padding: 6px; border-radius: 4px; margin-bottom: 8px;")
        device1_layout.addWidget(self.status_label1)
        
        # Layout horizontal para IP e DPI do dispositivo 1
        device1_horizontal = QHBoxLayout()
        
        # IP do dispositivo 1
        ip_layout1 = QVBoxLayout()
        ip_label1 = QLabel("Endereço IP:")
        self.ip_entry1 = QLineEdit()
        self.ip_entry1.setMinimumWidth(200)
        self.ip_entry1.setMinimumHeight(38)
        self.ip_entry1.setText(self.last_ip)
        ip_layout1.addWidget(ip_label1)
        ip_layout1.addWidget(self.ip_entry1)
        device1_horizontal.addLayout(ip_layout1)
        
        # DPI do dispositivo 1
        dpi_layout1 = QVBoxLayout()
        dpi_label1 = QLabel("DPI:")
        self.dpi_entry1 = QLineEdit()
        self.dpi_entry1.setText(self.last_dpi)
        self.dpi_entry1.setMinimumHeight(38)
        self.dpi_entry1.setMaximumWidth(80)
        dpi_layout1.addWidget(dpi_label1)
        dpi_layout1.addWidget(self.dpi_entry1)
        device1_horizontal.addLayout(dpi_layout1)
        
        device1_layout.addLayout(device1_horizontal)
        devices_container.addWidget(device1_group)
        
        # Dispositivo 2
        device2_group = QGroupBox("Dispositivo 2")
        device2_group.setStyleSheet(
            "QGroupBox{border:1px solid #3a4056; border-radius:8px; margin-top:6px; padding-top:2px;}"
            " QGroupBox::title{subcontrol-origin: margin; left:10px; top:-4px; color:#c8cbe0;}"
        )
        device2_layout = QVBoxLayout(device2_group)
        
        # Status do dispositivo 2 (em cima)
        self.status_label2 = QLabel("Dispositivo não conectado")
        self.status_label2.setMinimumHeight(32)
        self.status_label2.setObjectName("status")
        self.status_label2.setStyleSheet("color: #ff6b6b; background-color: #1a1d26; padding: 6px; border-radius: 4px; margin-bottom: 8px;")
        device2_layout.addWidget(self.status_label2)
        
        # Layout horizontal para IP e DPI do dispositivo 2
        device2_horizontal = QHBoxLayout()
        
        # IP do dispositivo 2
        ip_layout2 = QVBoxLayout()
        ip_label2 = QLabel("Endereço IP:")
        self.ip_entry2 = QLineEdit()
        self.ip_entry2.setMinimumWidth(200)
        self.ip_entry2.setMinimumHeight(38)
        self.ip_entry2.setText(self.last_ip2)
        ip_layout2.addWidget(ip_label2)
        ip_layout2.addWidget(self.ip_entry2)
        device2_horizontal.addLayout(ip_layout2)
        
        # DPI do dispositivo 2
        dpi_layout2 = QVBoxLayout()
        dpi_label2 = QLabel("DPI:")
        self.dpi_entry2 = QLineEdit()
        self.dpi_entry2.setText(self.last_dpi2)
        self.dpi_entry2.setMinimumHeight(38)
        self.dpi_entry2.setMaximumWidth(80)
        dpi_layout2.addWidget(dpi_label2)
        dpi_layout2.addWidget(self.dpi_entry2)
        device2_horizontal.addLayout(dpi_layout2)
        
        device2_layout.addLayout(device2_horizontal)
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
        self._apply_card_effect(apps_group)
        apps_layout = QVBoxLayout(apps_group)
        
        # Layout horizontal compacto
        apps_info_layout = QHBoxLayout()
        
        # Info sobre quantos apps serão removidos
        apps_count = len([app for app, enabled in self.app_manager.default_apps.items() if enabled])
        info_label = QLabel(f"Apps selecionados para remoção: {apps_count}")
        info_label.setStyleSheet("color: #aeb2c0; font-size: 11px;")
        apps_info_layout.addWidget(info_label)
        
        apps_info_layout.addStretch()
        
        # Botão para gerenciar apps padrão
        manage_default_button = QPushButton("Gerenciar Apps Padrão")
        manage_default_button.clicked.connect(self.show_default_apps_dialog)
        apps_info_layout.addWidget(manage_default_button)
        
        # Botão para listar apps instalados
        list_apps_button = QPushButton("Listar Instalados")
        list_apps_button.clicked.connect(self.show_app_list)
        apps_info_layout.addWidget(list_apps_button)
        
        apps_layout.addLayout(apps_info_layout)
        
        # Container visual para exibir checkboxes adicionados dinamicamente
        self.app_checkboxes = getattr(self, 'app_checkboxes', {})
        self.apps_container = QVBoxLayout()
        self.apps_container.setSpacing(6)
        chips_hint = QLabel("Apps escolhidos serão listados abaixo. Use 'Listar Instalados' para adicionar mais.")
        chips_hint.setStyleSheet("color:#8f95a5; font-size:10px;")
        apps_layout.addWidget(chips_hint)
        apps_layout.addLayout(self.apps_container)
        
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
        
        # Ocultar temporariamente o botão principal (sem quebrar a lógica)
        self.main_button.setVisible(False)
        
        # Redução de altura: botão extra desativado temporariamente
        # extra_row = QHBoxLayout()
        # extra_row.addStretch()
        # extra_usb = QPushButton("USB (extra)")
        # extra_usb.setObjectName("usb")
        # extra_usb.clicked.connect(self.connect_usb_device)
        # extra_row.addWidget(extra_usb)
        # parent_layout.addLayout(extra_row)

    def create_result_area(self, parent_layout):
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(100)
        self.result_text.setPlaceholderText("Resultado das operações aparecerá aqui...")
        parent_layout.addWidget(self.result_text)

    def create_footer(self, parent_layout):
        footer_layout = QHBoxLayout()
        
        # Desenvolvido por - botão com efeito neon animado
        dev_button = NeonButton("Desenvolvido por Ruã Fernandes")
        dev_button.setStyleSheet("""
            NeonButton {
                background-color: transparent;
                color: #888888;
                border: 1px solid transparent;
                border-radius: 4px;
                font-size: 11px;
                padding: 6px 8px 8px 8px;
                text-align: left;
            }
            NeonButton:hover {
                color: #ffffff;
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            NeonButton:pressed {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        dev_button.clicked.connect(lambda: self.open_url("www.linkedin.com/in/ruafernandes"))
        footer_layout.addWidget(dev_button)
        
        footer_layout.addStretch()
        
        # Botão discreto de buscar atualizações
        self.update_button = QPushButton("⟳ Buscar Atualizações")
        self.update_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #666666;
                border: 1px solid #444444;
                border-radius: 3px;
                font-size: 9px;
                padding: 3px 8px;
                margin-right: 10px;
            }
            QPushButton:hover {
                color: #0078d4;
                border-color: #0078d4;
                background-color: rgba(0, 120, 212, 0.1);
            }
            QPushButton:disabled {
                color: #444444;
                border-color: #333333;
            }
        """)
        self.update_button.clicked.connect(self.check_updates_manual)
        footer_layout.addWidget(self.update_button)
        
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
        linkedin_button.clicked.connect(lambda: self.open_url("www.linkedin.com/in/ruafernandes"))
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
        
        version_label = QLabel("v10.5")
        version_label.setStyleSheet("color: #888888; font-size: 10px;")
        footer_layout.addWidget(version_label)
        
        parent_layout.addLayout(footer_layout)

    def create_usb_section(self, parent_layout):
        usb_group = QGroupBox("Configuração USB - Instalação Automática")
        self._apply_card_effect(usb_group)
        usb_layout = QVBoxLayout(usb_group)
        
        # Layout principal horizontal
        main_layout = QHBoxLayout()
        
        # Lado esquerdo - Seletor de painel
        left_layout = QVBoxLayout()
        panel_label = QLabel("Tipo de Painel:")
        self.panel_combo = QComboBox()
        self.panel_combo.addItems(self.apk_manager.get_panel_types())
        left_layout.addWidget(panel_label)
        left_layout.addWidget(self.panel_combo)
        
        # Lado direito - Info e botões
        right_layout = QVBoxLayout()
        
        # Info sobre localização dos APKs
        info_label = QLabel(f"Pasta: {self.apk_manager.get_base_path()}")
        info_label.setStyleSheet("color: #aeb2c0; font-size: 10px; font-style: italic;")
        right_layout.addWidget(info_label)
        
        # Botões na horizontal
        buttons_layout = QHBoxLayout()
        
        # Botão para abrir pasta
        open_folder_button = QPushButton("Abrir Pasta")
        open_folder_button.setStyleSheet("background: #32384a; font-size: 12px; padding: 8px 14px;")
        open_folder_button.clicked.connect(self.open_apk_folder)
        buttons_layout.addWidget(open_folder_button)
        
        # Botão USB
        usb_button = QPushButton("Configurar Rápido")
        usb_button.setObjectName("usb")
        usb_button.clicked.connect(self.configure_usb_device)
        buttons_layout.addWidget(usb_button)
        
        right_layout.addLayout(buttons_layout)
        
        # Adicionar ao layout principal
        main_layout.addLayout(left_layout)
        main_layout.addStretch()
        main_layout.addLayout(right_layout)
        
        usb_layout.addLayout(main_layout)
        parent_layout.addWidget(usb_group)

    def show_message_box(self, title, message, icon_type="information"):
        """Cria um QMessageBox com tema escuro"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        # Definir ícone
        if icon_type == "information":
            msg_box.setIcon(QMessageBox.Icon.Information)
        elif icon_type == "warning":
            msg_box.setIcon(QMessageBox.Icon.Warning)
        elif icon_type == "critical":
            msg_box.setIcon(QMessageBox.Icon.Critical)
        
        # Aplicar estilo escuro
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2b2b2b;
                color: white;
            }
            QMessageBox QLabel {
                color: white;
                background-color: transparent;
                font-size: 12px;
            }
            QMessageBox QPushButton {
                background-color: #0078d4;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #106ebe;
            }
        """)
        
        return msg_box.exec()

    def open_apk_folder(self):
        """Abre a pasta onde devem ser colocados os APKs"""
        import subprocess
        import os
        try:
            # Verificar se a pasta existe primeiro
            if not os.path.exists(self.apk_manager.get_base_path()):
                self.show_message_box("Erro", 
                                    f"A pasta não existe: {self.apk_manager.get_base_path()}", 
                                    "critical")
                return
            
            # Abrir a pasta no Windows Explorer
            # No Windows, o explorer pode retornar códigos de erro mesmo abrindo corretamente
            subprocess.run(['explorer', self.apk_manager.get_base_path()], 
                          creationflags=subprocess.CREATE_NO_WINDOW)
            
        except FileNotFoundError:
            self.show_message_box("Erro", 
                                "Comando 'explorer' não encontrado.", 
                                "critical")
        except Exception as e:
            self.show_message_box("Erro", 
                                f"Erro inesperado ao abrir pasta: {str(e)}", 
                                "critical")

    def open_url(self, url):
        import webbrowser
        webbrowser.open(url)

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

    def configure_usb_device(self):
        """Configura dispositivo USB com instalação automática de APKs"""
        panel_type = self.panel_combo.currentText()
        
        # Desabilitar botão durante a operação
        usb_button = self.sender()
        usb_button.setEnabled(False)
        usb_button.setText("Configurando...")
        
        # Criar e iniciar thread USB
        self.usb_worker = USBWorkerThread(self.adb_manager, self.app_manager, self.apk_manager, panel_type)
        self.usb_worker.progress.connect(self.result_text.append)
        self.usb_worker.finished.connect(lambda result: self.on_usb_worker_finished(result, usb_button))
        self.usb_worker.start()

    def on_usb_worker_finished(self, result, button):
        """Callback quando a configuração USB termina"""
        self.result_text.append(result)
        button.setEnabled(True)
        button.setText("Configurar Rápido")

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
            self.show_message_box("Aviso", "Por favor, preencha pelo menos um endereço IP de dispositivo.", "warning")
            return
        
        # Verificar conexão
        if not self.adb_manager.connect(target_ip):
            self.show_message_box("Erro", "Não foi possível conectar ao dispositivo. Verifique o IP e a conexão.", "critical")
            return
        
        # Abrir janela de aplicativos instalados
        dialog = AppListDialog(self, self.adb_manager, target_ip)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Os aplicativos já foram adicionados pelo dialog
            self.result_text.append("Aplicativos adicionados com sucesso!")
        else:
            self.result_text.append("Operação cancelada.")

    def show_default_apps_dialog(self):
        """Abre um diálogo para gerenciar os aplicativos padrão para remoção"""
        dialog = DefaultAppsDialog(self, self.app_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Atualizar a lista de apps para remover
            self.app_manager.app_list = [app for app, enabled in self.app_manager.default_apps.items() if enabled]
            
            # Atualizar o contador na interface
            self.update_apps_count()
            
            self.result_text.append("Aplicativos padrão para remoção atualizados!")
        else:
            self.result_text.append("Operação de gerenciamento de apps cancelada.")

    def update_apps_count(self):
        """Atualiza o contador de apps na interface"""
        # Encontrar o label de contagem e atualizar
        apps_count = len([app for app, enabled in self.app_manager.default_apps.items() if enabled])
        # Como não temos referência direta ao label, vamos recriar a seção de apps
        # Isso é uma solução simples para atualizar o contador
        pass  # Por enquanto, o usuário pode ver a mudança na próxima vez que abrir

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

    def apply_window_icon(self):
        """Aplica o ícone da janela priorizando o ícone embutido no executável.
        Fallback para arquivos .ico empacotados e, por fim, caminhos alternativos.
        """
        try:
            # 0) Se compilado, tentar um .ico ao lado do executável com o mesmo basename
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
                exe_dir = os.path.dirname(exe_path)
                exe_base = os.path.splitext(os.path.basename(exe_path))[0]
                side_candidates = [
                    os.path.join(exe_dir, exe_base + '.ico'),
                    os.path.join(exe_dir, 'app.ico'),
                ]
                # procurar qualquer .ico no diretório como último recurso local
                try:
                    for f in os.listdir(exe_dir):
                        if f.lower().endswith('.ico'):
                            side_candidates.append(os.path.join(exe_dir, f))
                except Exception:
                    pass
                for cand in side_candidates:
                    if os.path.exists(cand):
                        ic = QIcon(cand)
                        if not ic.isNull():
                            self.setWindowIcon(ic)
                            QApplication.setWindowIcon(ic)
                            print(f"Ícone aplicado via .ico ao lado do exe: {cand}")
                            return

            # 1) Tentar usar o ícone do executável (quando compilado) usando WinAPI
            if os.name == 'nt' and getattr(sys, 'frozen', False):
                exe_path = sys.executable
                try:
                    import ctypes
                    from ctypes import wintypes
                    # Tentar obter ícone grande via SHGetFileInfo
                    SHGFI_ICON = 0x000000100
                    SHGFI_LARGEICON = 0x000000000
                    shinfo = wintypes.SHFILEINFOW()
                    shell32 = ctypes.windll.shell32
                    res = shell32.SHGetFileInfoW(exe_path, 0, ctypes.byref(shinfo), ctypes.sizeof(shinfo), SHGFI_ICON | SHGFI_LARGEICON)
                    if res:
                        hicon = shinfo.hIcon
                        try:
                            try:
                                from PyQt6.QtWinExtras import QtWin  # type: ignore
                                pm = QtWin.fromHICON(hicon)
                                if pm and not pm.isNull():
                                    icon = QIcon(pm)
                                    self.setWindowIcon(icon)
                                    QApplication.setWindowIcon(icon)
                                    print("Ícone aplicado a partir do executável (WinAPI)")
                                    ctypes.windll.user32.DestroyIcon(hicon)
                                    return
                            except Exception:
                                pass
                        finally:
                            try:
                                ctypes.windll.user32.DestroyIcon(hicon)
                            except Exception:
                                pass
                except Exception as e:
                    print(f"Falha WinAPI ao obter ícone: {e}")

                exe_icon = QIcon(exe_path)
                if not exe_icon.isNull():
                    self.setWindowIcon(exe_icon)
                    QApplication.setWindowIcon(exe_icon)
                    print("Ícone aplicado a partir do executável (fallback QIcon)")
                    return

            # 2) Tentar ícones empacotados (PyInstaller --add-data)
            for name in ("app.ico", "logoAI_preto.ico", "logo.ico"):
                path = resource_path(name)
                if os.path.exists(path):
                    ic = QIcon(path)
                    if not ic.isNull():
                        self.setWindowIcon(ic)
                        QApplication.setWindowIcon(ic)
                        print(f"Ícone aplicado via recurso: {path}")
                        return

            # 3) Caminho alternativo conhecido
            alt_icon_path = r"C:\Users\RuaF\Downloads\logoAI_preto.ico"
            if os.path.exists(alt_icon_path):
                ic = QIcon(alt_icon_path)
                if not ic.isNull():
                    self.setWindowIcon(ic)
                    QApplication.setWindowIcon(ic)
                    print(f"Ícone aplicado via caminho alternativo: {alt_icon_path}")
                    return

            print("Não foi possível definir o ícone da janela")
        except Exception as e:
            print(f"Erro ao aplicar ícone da janela: {e}")

class UpdateManager:
    def __init__(self):
        # Configuração do Firebase Realtime Database (gratuito)
        self.firebase_url = "https://seu-projeto-firebase-default-rtdb.firebaseio.com/"
        self.current_version = "10.5"  # Versão atual do aplicativo
        self.app_name = "ConfiguradorDPI"
        
        # Alternativa gratuita: GitHub Releases
        self.github_repo = "ruafernd/minipcs-releases"  # Seu repositório para releases
        self.use_github = True  # True = usar GitHub, False = usar Firebase Storage
        
    def check_for_updates(self):
        """Verifica se há atualizações disponíveis"""
        try:
            if self.use_github:
                return self._check_github_releases()
            else:
                return self._check_firebase_updates()
                
        except Exception as e:
            return {'update_available': False, 'error': f'Erro inesperado: {str(e)}'}
    
    def _check_github_releases(self):
        """Verifica atualizações no GitHub Releases (GRATUITO)"""
        try:
            # API do GitHub para releases
            url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                latest_version = data.get('tag_name', '0.0').replace('v', '')  # Remove 'v' se houver
                changelog = data.get('body', 'Sem informações de mudanças.')
                
                # Debug: listar todos os assets disponíveis
                assets = data.get('assets', [])
                print(f"DEBUG: Assets encontrados: {len(assets)}")
                for asset in assets:
                    print(f"DEBUG: Asset: {asset['name']} - {asset['browser_download_url']}")
                
                # Procurar arquivo .exe ou .zip nos assets (busca mais flexível)
                download_url = None
                file_type = None
                
                # Prioridade: .exe primeiro, depois .zip
                for asset in assets:
                    asset_name = asset['name'].lower()
                    if asset_name.endswith('.exe'):
                        download_url = asset['browser_download_url']
                        file_type = 'exe'
                        print(f"DEBUG: Encontrado EXE: {asset['name']}")
                        break
                
                # Se não encontrou .exe, procurar .zip
                if not download_url:
                    for asset in assets:
                        asset_name = asset['name'].lower()
                        if asset_name.endswith('.zip'):
                            download_url = asset['browser_download_url']
                            file_type = 'zip'
                            print(f"DEBUG: Encontrado ZIP: {asset['name']}")
                            break
                
                # Se ainda não encontrou, procurar qualquer arquivo binário comum
                if not download_url:
                    for asset in assets:
                        asset_name = asset['name'].lower()
                        if any(ext in asset_name for ext in ['.msi', '.deb', '.rpm', '.dmg', '.pkg']):
                            download_url = asset['browser_download_url']
                            file_type = 'other'
                            print(f"DEBUG: Encontrado outro tipo: {asset['name']}")
                            break
                
                if not download_url:
                    error_msg = f'Nenhum arquivo executável encontrado. Assets disponíveis: {[asset["name"] for asset in assets]}'
                    print(f"DEBUG: {error_msg}")
                    return {'update_available': False, 'error': error_msg}
                
                # Verificar se é versão obrigatória (baseado em tag ou descrição)
                mandatory = 'OBRIGATÓRIA' in changelog.upper() or 'MANDATORY' in changelog.upper()
                
                # Comparar versões
                if self.is_newer_version(latest_version, self.current_version):
                    return {
                        'update_available': True,
                        'version': latest_version,
                        'download_url': download_url,
                        'file_type': file_type,
                        'changelog': changelog,
                        'mandatory': mandatory,
                        'current_version': self.current_version
                    }
                else:
                    return {'update_available': False}
            else:
                return {'update_available': False, 'error': f'Erro GitHub API: {response.status_code}'}
                
        except requests.RequestException as e:
            return {'update_available': False, 'error': f'Erro de conexão GitHub: {str(e)}'}
    
    def _check_firebase_updates(self):
        """Verifica atualizações no Firebase (método original)"""
        try:
            # URL para buscar informações da versão mais recente
            url = f"{self.firebase_url}/updates/{self.app_name}.json"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    latest_version = data.get('version', '0.0')
                    download_url = data.get('download_url', '')
                    changelog = data.get('changelog', 'Sem informações de mudanças.')
                    mandatory = data.get('mandatory', False)
                    file_type = data.get('file_type', 'zip')  # Padrão ZIP se não especificado
                    
                    # Comparar versões (versão simples)
                    if self.is_newer_version(latest_version, self.current_version):
                        return {
                            'update_available': True,
                            'version': latest_version,
                            'download_url': download_url,
                            'file_type': file_type,
                            'changelog': changelog,
                            'mandatory': mandatory,
                            'current_version': self.current_version
                        }
                    else:
                        return {'update_available': False}
                else:
                    return {'update_available': False, 'error': 'Dados não encontrados'}
            else:
                return {'update_available': False, 'error': f'Erro HTTP: {response.status_code}'}
                
        except requests.RequestException as e:
            return {'update_available': False, 'error': f'Erro de conexão: {str(e)}'}
    
    def is_newer_version(self, latest, current):
        """Compara duas versões no formato X.Y"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Preencher com zeros se necessário
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            
            return latest_parts > current_parts
        except:
            return False
    
    def download_update(self, download_url, file_type='zip', progress_callback=None):
        """Baixa a atualização (funciona com GitHub ou Firebase)"""
        try:
            # Criar pasta temporária para download
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp_update')
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            # Nome do arquivo baseado no asset original
            filename = os.path.basename(urlparse(download_url).path)
            if not filename:
                filename = 'update.bin'
            
            file_path = os.path.join(temp_dir, filename)
            
            # Download com progresso
            response = requests.get(download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if progress_callback and total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            progress_callback(progress)
            
            return file_path
            
        except Exception as e:
            return None, str(e)
    
    def install_update(self, file_path):
        """Instala a atualização baixada (ZIP ou EXE) sem reiniciar automaticamente.
        - Para EXE: substitui o executável atual pelo novo mantendo o mesmo nome (fechando o app e sem abrir novamente).
        - Para ZIP: extrai para uma subpasta de atualização e instrui o usuário a fechar o app e abrir o novo executável.
        """
        try:
            # Detectar o executável atual corretamente
            if getattr(sys, 'frozen', False):
                current_exe = sys.executable
            else:
                current_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'minipcs.exe')

            app_dir = os.path.dirname(current_exe)

            # EXE direto: substituir mantendo o mesmo nome do executável atual
            if file_path.lower().endswith('.exe'):
                try:
                    # Caminhos normalizados
                    target_exe = current_exe  # manter exatamente o mesmo nome
                    exe_name = os.path.basename(target_exe)

                    # Preparar pasta temporária segura no %TEMP%
                    temp_root = os.path.join(os.environ.get('TEMP', os.path.dirname(file_path)), 'MiniPcsUpdate')
                    if not os.path.exists(temp_root):
                        os.makedirs(temp_root, exist_ok=True)
                    staged_new_exe = os.path.join(temp_root, exe_name)

                    # Copiar o novo EXE para a área temporária com o mesmo nome do alvo
                    try:
                        if os.path.abspath(file_path) != os.path.abspath(staged_new_exe):
                            shutil.copy2(file_path, staged_new_exe)
                    except Exception as e:
                        return False, f"Erro ao preparar arquivo de atualização: {str(e)}"

                    # Criar script PowerShell que aguarda o app fechar e substitui o executável
                    ps_script = f'''
$ErrorActionPreference = 'SilentlyContinue'
$exePath = "{target_exe}"
$newExe = "{staged_new_exe}"
$procName = [System.IO.Path]::GetFileNameWithoutExtension($exePath)
$tempRoot = "{temp_root}"

# Esperar o processo finalizar
for ($i=0; $i -lt 240; $i++) {{
    $p = Get-Process -Name $procName -ErrorAction SilentlyContinue
    if (-not $p) {{ break }}
    Start-Sleep -Milliseconds 250
}}

    # Substituição simples e direta
    try {{
        # Fazer backup do arquivo atual (opcional)
        if (Test-Path ($exePath + '.old')) {{ 
            Remove-Item ($exePath + '.old') -Force -ErrorAction SilentlyContinue 
        }}
        
        # Fazer backup do arquivo atual
        if (Test-Path $exePath) {{ 
            Copy-Item $exePath ($exePath + '.old') -Force -ErrorAction SilentlyContinue 
        }}
        
        # Substituir pelo novo arquivo
        Copy-Item $newExe $exePath -Force -ErrorAction Stop
        
        # Verificar se a substituição foi bem-sucedida
        if (Test-Path $exePath) {{
            # Remover backup antigo após sucesso
            if (Test-Path ($exePath + '.old')) {{ 
                Remove-Item ($exePath + '.old') -Force -ErrorAction SilentlyContinue 
            }}
        }}
    }} catch {{
        # Se falhou, tentar restaurar backup
        if (Test-Path ($exePath + '.old')) {{
            Copy-Item ($exePath + '.old') $exePath -Force -ErrorAction SilentlyContinue
        }}
    }}

    # Limpeza dos arquivos temporários
    try {{ 
        if (Test-Path $tempRoot) {{ 
            Remove-Item $tempRoot -Recurse -Force -ErrorAction SilentlyContinue 
        }} 
    }} catch {{}}

    # Mostrar mensagem de conclusão
    try {{
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show(
            "Atualizacao concluida com sucesso!`n`nVoce pode abrir o aplicativo normalmente.",
            "MiniPCS - Atualizacao v10.5",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Information
        )
    }} catch {{}}

    # Remover o script
    Remove-Item $MyInvocation.MyCommand.Path -Force -ErrorAction SilentlyContinue
    '''
                    script_path = os.path.join(temp_root, 'apply_update.ps1')
                    with open(script_path, 'w', encoding='utf-8') as f:
                        f.write(ps_script)

                    # Executar o script em background e fechar o app em seguida
                    try:
                        subprocess.Popen([
                            'powershell.exe', '-WindowStyle', 'Hidden', '-ExecutionPolicy', 'Bypass',
                            '-File', script_path
                        ], creationflags=subprocess.CREATE_NO_WINDOW)
                    except Exception:
                        pass

                    # Fechar o app para permitir a substituição
                    QTimer.singleShot(300, QApplication.instance().quit)

                    message = (
                        "Atualização será aplicada!\n\n"
                        f"O aplicativo será fechado para substituir o arquivo.\n"
                        f"Após a conclusão, abra o aplicativo normalmente.\n\n"
                        f"Nova versão: v10.5"
                    )
                    return True, message
                except Exception as e:
                    return False, f"Erro ao preparar substituição do executável: {str(e)}"

            # ZIP: extrair e instruir o usuário
            extract_dir = os.path.join(os.path.dirname(file_path), 'Update_Extracted')
            try:
                if os.path.exists(extract_dir):
                    shutil.rmtree(extract_dir)
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            except Exception as e:
                return False, f"Erro ao extrair atualização: {str(e)}"

            # Procurar um executável dentro do ZIP extraído
            exe_files = []
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    if file.lower().endswith('.exe'):
                        exe_files.append(os.path.join(root, file))

            if exe_files:
                new_exe = exe_files[0]
                is_valid, msg = self.validate_executable(new_exe)
                if not is_valid:
                    return False, f"Executável inválido no pacote: {msg}"
                
                # Para arquivos ZIP, ainda requer intervenção manual, mas com melhor orientação
                message = (
                    "Atualização extraída com sucesso!\n\n"
                    f"Nova versão extraída em: {new_exe}\n\n"
                    "Para completar a atualização:\n"
                    "1. Feche este aplicativo\n"
                    "2. Substitua o executável atual pelo novo\n"
                    "3. Execute a nova versão\n\n"
                    "Nota: Atualizações em formato EXE são aplicadas automaticamente."
                )
                return True, message
            else:
                return False, "Nenhum executável encontrado no pacote de atualização."

        except Exception as e:
            return False, f"Erro ao instalar atualização: {str(e)}"

    def validate_executable(self, exe_path):
        """Valida se o executável é compatível"""
        try:
            # Verificar se o arquivo existe e não está corrompido
            if not os.path.exists(exe_path):
                return False, "Arquivo não encontrado"
            
            # Verificar tamanho mínimo (deve ter pelo menos 1MB)
            file_size = os.path.getsize(exe_path)
            if file_size < 1024 * 1024:  # 1MB
                return False, "Arquivo muito pequeno, pode estar corrompido"
            
            # Verificar se é um executável Windows válido
            with open(exe_path, 'rb') as f:
                # Ler os primeiros bytes para verificar assinatura PE
                header = f.read(2)
                if header != b'MZ':
                    return False, "Não é um executável Windows válido"
                
                # Pular para o offset do PE header
                f.seek(60)
                pe_offset_bytes = f.read(4)
                if len(pe_offset_bytes) < 4:
                    return False, "Arquivo corrompido"
                
                pe_offset = int.from_bytes(pe_offset_bytes, byteorder='little')
                f.seek(pe_offset)
                pe_signature = f.read(4)
                if pe_signature != b'PE\x00\x00':
                    return False, "Assinatura PE inválida"
            
            return True, "Executável válido"
            
        except Exception as e:
            return False, f"Erro na validação: {str(e)}"

class UpdateWorkerThread(QThread):
    """Thread para verificar atualizações em segundo plano"""
    update_available = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, update_manager):
        super().__init__()
        self.update_manager = update_manager
    
    def run(self):
        try:
            result = self.update_manager.check_for_updates()
            if result.get('update_available'):
                self.update_available.emit(result)
            elif result.get('error'):
                self.error_occurred.emit(result['error'])
        except Exception as e:
            self.error_occurred.emit(f"Erro ao verificar atualizações: {str(e)}")

class DownloadWorkerThread(QThread):
    """Thread para baixar atualizações"""
    progress_updated = pyqtSignal(int)
    download_finished = pyqtSignal(str)  # file_path
    download_failed = pyqtSignal(str)    # error_message
    
    def __init__(self, update_manager, download_url, file_type='zip'):
        super().__init__()
        self.update_manager = update_manager
        self.download_url = download_url
        self.file_type = file_type
    
    def run(self):
        try:
            result = self.update_manager.download_update(
                self.download_url, 
                self.file_type,
                progress_callback=self.progress_updated.emit
            )
            
            if isinstance(result, tuple):  # Erro retornado
                file_path, error = result
                if error:
                    self.download_failed.emit(error)
                    return
            
            self.download_finished.emit(result)
            
        except Exception as e:
            self.download_failed.emit(f"Erro no download: {str(e)}")

class UpdateDialog(QDialog):
    """Diálogo para mostrar informações de atualização"""
    
    def __init__(self, parent, update_info):
        super().__init__(parent)
        self.update_info = update_info
        self.update_manager = parent.update_manager
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Atualização Disponível")
        self.setFixedSize(500, 400)
        self.setModal(True)
        
        # Aplicar o mesmo tema escuro moderno
        self.setStyleSheet("""
            QDialog { background-color: #0f1116; color: #e6e6e6; }
            QLabel { color: #e6e6e6; background-color: transparent; }
            QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4d58ff, stop:1 #8a46ff); border: none; color: white; padding: 10px 20px; border-radius: 10px; font-weight: 700; }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5a63ff, stop:1 #9b52ff); }
            QPushButton#cancel { background: #32384a; }
            QPushButton#cancel:hover { background: #3b4257; }
            QTextEdit { background-color: #0f121a; border: 1px solid #2b3040; border-radius: 10px; color: #e6e6e6; padding: 10px; }
            QProgressBar { border: 1px solid #2b3040; border-radius: 10px; text-align: center; background-color: #141822; color: #e6e6e6; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4d58ff, stop:1 #8a46ff); border-radius: 8px; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title_label = QLabel("🚀 Nova Versão Disponível!")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Informações da versão
        version_info = QLabel(f"Versão Atual: {self.update_info['current_version']}\n"
                             f"Nova Versão: {self.update_info['version']}")
        version_info.setStyleSheet("font-size: 14px; padding: 10px; background-color: #121725; border: 1px solid #3a4056; border-radius: 10px;")
        version_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_info)
        
        # Changelog
        changelog_label = QLabel("📋 Novidades desta versão:")
        changelog_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(changelog_label)
        
        changelog_text = QTextEdit()
        changelog_text.setPlainText(self.update_info['changelog'])
        changelog_text.setMaximumHeight(150)
        changelog_text.setReadOnly(True)
        layout.addWidget(changelog_text)
        
        # Barra de progresso (inicialmente oculta)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #aeb2c0; font-style: italic;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Botões
        buttons_layout = QHBoxLayout()
        
        if not self.update_info.get('mandatory', False):
            cancel_button = QPushButton("Agora Não")
            cancel_button.setObjectName("cancel")
            cancel_button.clicked.connect(self.reject)
            buttons_layout.addWidget(cancel_button)
        
        self.update_button = QPushButton("Atualizar Agora")
        self.update_button.clicked.connect(self.start_update)
        buttons_layout.addWidget(self.update_button)
        
        layout.addLayout(buttons_layout)
        
        # Se for obrigatória, mostrar aviso
        if self.update_info.get('mandatory', False):
            mandatory_label = QLabel("⚠️ Esta atualização é obrigatória")
            mandatory_label.setStyleSheet("color: #ff6b35; font-weight: bold; text-align: center;")
            mandatory_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.insertWidget(1, mandatory_label)
    
    def start_update(self):
        """Inicia o processo de atualização"""
        self.update_button.setEnabled(False)
        self.update_button.setText("Baixando...")
        self.progress_bar.setVisible(True)
        self.status_label.setText("Baixando atualização...")
        
        # Iniciar download em thread separada
        self.download_thread = DownloadWorkerThread(
            self.update_manager, 
            self.update_info['download_url'],
            self.update_info['file_type']
        )
        self.download_thread.progress_updated.connect(self.update_progress)
        self.download_thread.download_finished.connect(self.on_download_finished)
        self.download_thread.download_failed.connect(self.on_download_failed)
        self.download_thread.start()
    
    def update_progress(self, progress):
        """Atualiza a barra de progresso"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"Baixando... {progress}%")
    
    def on_download_finished(self, file_path):
        """Chamado quando o download termina"""
        self.status_label.setText("Instalando atualização...")
        self.progress_bar.setVisible(False)
        
        # Instalar atualização
        success, message = self.update_manager.install_update(file_path)
        
        if success:
            self.status_label.setText("✅ " + message)
            # Fechar aplicativo após breve pausa
            QTimer.singleShot(2000, QApplication.instance().quit)
        else:
            self.status_label.setText("❌ " + message)
            self.update_button.setEnabled(True)
            self.update_button.setText("Tentar Novamente")
    
    def on_download_failed(self, error_message):
        """Chamado quando o download falha"""
        self.status_label.setText(f"❌ Erro: {error_message}")
        self.progress_bar.setVisible(False)
        self.update_button.setEnabled(True)
        self.update_button.setText("Tentar Novamente")

class NeonButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self._neon_position = 0.0
        self._animation = QPropertyAnimation(self, b"neon_position")
        self._animation.setDuration(800)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.setMouseTracking(True)
        
    @pyqtProperty(float)
    def neon_position(self):
        return self._neon_position
    
    @neon_position.setter
    def neon_position(self, value):
        self._neon_position = value
        self.update()
    
    def enterEvent(self, event):
        super().enterEvent(event)
        self._animation.setStartValue(0.0)
        self._animation.setEndValue(1.0)
        self._animation.start()
    
    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._animation.setStartValue(1.0)
        self._animation.setEndValue(0.0)
        self._animation.start()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Desenhar linha neon animada
        if self._neon_position > 0:
            rect = self.rect()
            line_width = 2
            line_height = 2
            
            # Posição da linha baseada na animação
            line_x = rect.width() * self._neon_position - 20
            line_y = rect.height() - 4
            
            # Criar gradiente neon
            gradient = QLinearGradient(line_x, line_y, line_x + 40, line_y)
            gradient.setColorAt(0.0, QColor(0, 200, 255, 0))
            gradient.setColorAt(0.3, QColor(0, 200, 255, 200))
            gradient.setColorAt(0.7, QColor(0, 200, 255, 200))
            gradient.setColorAt(1.0, QColor(0, 200, 255, 0))
            
            # Desenhar linha neon principal
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(int(line_x), int(line_y), 40, line_height)
            
            # Efeito de brilho adicional
            glow_gradient = QLinearGradient(line_x, line_y - 1, line_x + 40, line_y - 1)
            glow_gradient.setColorAt(0.0, QColor(0, 200, 255, 0))
            glow_gradient.setColorAt(0.5, QColor(0, 200, 255, 100))
            glow_gradient.setColorAt(1.0, QColor(0, 200, 255, 0))
            
            painter.setBrush(QBrush(glow_gradient))
            painter.drawRect(int(line_x), int(line_y - 1), 40, line_height + 2)

class AnimatedLineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(6, 64)
        self._phase = 0.0
        self._direction = 1
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(40)  # ~50fps

    def _tick(self):
        # Vai e volta entre 0 e 1
        step = 0.01 * self._direction
        self._phase += step
        if self._phase >= 1.0:
            self._phase = 1.0
            self._direction = -1
        elif self._phase <= 0.0:
            self._phase = 0.0
            self._direction = 1
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        # Fundo transparente
        painter.fillRect(self.rect(), Qt.GlobalColor.transparent)

        # Linha base com gradiente suave
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, QColor(120, 96, 255, 180))
        grad.setColorAt(1.0, QColor(120, 96, 255, 60))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawRoundedRect(2, 0, 2, h, 2, 2)

        # Glow que sobe/desce
        glow_y = int((1.0 - self._phase) * (h - 18))  # 18px de altura do glow
        glow_grad = QLinearGradient(0, glow_y, 0, glow_y + 18)
        glow_grad.setColorAt(0.0, QColor(160, 140, 255, 0))
        glow_grad.setColorAt(0.5, QColor(160, 140, 255, 220))
        glow_grad.setColorAt(1.0, QColor(160, 140, 255, 0))
        painter.setBrush(QBrush(glow_grad))
        painter.drawRoundedRect(1, glow_y, 4, 18, 4, 4)
        painter.end()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConfiguradorDPI()
    window.show()
    sys.exit(app.exec()) 