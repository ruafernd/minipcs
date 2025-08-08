import sys
import subprocess
import os
import threading
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
                             QPushButton, QCheckBox, QTextEdit, QGroupBox,
                             QFrame, QScrollArea, QSizePolicy, QDialog,
                             QListWidget, QMessageBox, QComboBox)
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
                "Painel Amor Saúde": ["amor", "painel", "amorpainel", "love", "health", "roosevelt", "senha"],
                "Painel Geral": ["geral", "painel", "general", "main", "roosevelt", "senha"],
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
                "Painel Amor Saúde": "com.example.roosevelt.painel_senha_digital",
                "Painel Geral": "com.example.roosevelt.painel_senha_digital", 
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
            "Painel Amor Saúde": [
                os.path.join(self.base_path, "Painel_Amor_Saude", "amor_painel.apk"),
                os.path.join(self.base_path, "Painel_Amor_Saude", "adb.apk"),
                os.path.join(self.base_path, "Painel_Amor_Saude", "sintese.apk")
            ],
            "Painel Geral": [
                os.path.join(self.base_path, "Painel_Geral", "geral_painel.apk"),
                os.path.join(self.base_path, "Painel_Geral", "adb.apk"),
                os.path.join(self.base_path, "Painel_Geral", "sintese.apk")
            ],
            "Totem": [
                os.path.join(self.base_path, "Totem", "totem_ai.apk"),
                os.path.join(self.base_path, "Totem", "adb.apk")
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
            folders = ["Painel_Amor_Saude", "Painel_Geral", "Totem"]
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
                
                folders = ["Painel_Amor_Saude", "Painel_Geral", "Totem"]
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
                if folder_name == "Painel_Amor_Saude":
                    content = """TEMPLATE - Painel Amor Saúde
=====================================

Coloque os seguintes arquivos APK nesta pasta:

✓ amor_painel.apk
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
                
                elif folder_name == "Painel_Geral":
                    content = """TEMPLATE - Painel Geral
=======================

Coloque os seguintes arquivos APK nesta pasta:

✓ geral_painel.apk
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
            "Painel Amor Saúde": [
                os.path.join(self.base_path, "Painel_Amor_Saude", "amor_painel.apk"),
                os.path.join(self.base_path, "Painel_Amor_Saude", "adb.apk"),
                os.path.join(self.base_path, "Painel_Amor_Saude", "sintese.apk")
            ],
            "Painel Geral": [
                os.path.join(self.base_path, "Painel_Geral", "geral_painel.apk"),
                os.path.join(self.base_path, "Painel_Geral", "adb.apk"),
                os.path.join(self.base_path, "Painel_Geral", "sintese.apk")
            ],
            "Totem": [
                os.path.join(self.base_path, "Totem", "totem_ai.apk"),
                os.path.join(self.base_path, "Totem", "adb.apk")
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
                if "Painel" in self.panel_type:
                    self.progress.emit("🗣️ Configurando síntese de voz para português brasileiro...")
                    
                    # Usar versão simplificada para evitar problemas de conexão
                    tts_success, tts_message = self.adb_manager.configure_tts_portuguese_brazil_simple(device_id)
                    if tts_success:
                        self.progress.emit(f"✅ {tts_message}")
                        self.progress.emit("ℹ️ TTS configurado: Google TTS, pt-BR, voz 5, velocidade normal")
                    else:
                        self.progress.emit(f"⚠️ Problema na configuração TTS: {tts_message}")
                        self.progress.emit("ℹ️ Você pode configurar manualmente: Configurações → Acessibilidade → TTS")
                
                # Configurar auto-start do aplicativo principal (para painéis e totem)
                if self.panel_type in ["Painel Amor Saúde", "Painel Geral", "Totem"]:
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
            QDialog {
                background-color: #2b2b2b;
                color: white;
            }
            QWidget {
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
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
            }
            QCheckBox {
                color: white;
                font-size: 11px;
                spacing: 8px;
                padding: 3px;
                background-color: transparent;
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
            QPushButton {
                background-color: #0078d4;
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                min-width: 80px;
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
                background-color: transparent;
            }
            QScrollArea {
                border: 1px solid #555555;
                border-radius: 5px;
                background-color: #404040;
            }
            QScrollArea QWidget {
                background-color: #404040;
                color: white;
            }
            QScrollArea QScrollBar:vertical {
                background-color: #555555;
                width: 12px;
                border-radius: 6px;
            }
            QScrollArea QScrollBar::handle:vertical {
                background-color: #888888;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollArea QScrollBar::handle:vertical:hover {
                background-color: #aaaaaa;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title_label = QLabel("Aplicativos que serão removidos automaticamente:")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
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
        self.setGeometry(100, 100, 800, 750)
        
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
            QComboBox {
                padding: 8px;
                border: 2px solid #555555;
                border-radius: 5px;
                background-color: #404040;
                color: white;
                font-size: 12px;
                min-width: 150px;
            }
            QComboBox:focus {
                border: 2px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #555555;
                border-radius: 3px;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
                width: 0px;
                height: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #404040;
                color: white;
                selection-background-color: #0078d4;
                border: 1px solid #555555;
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
            QMessageBox {
                background-color: #2b2b2b;
                color: white;
            }
            QMessageBox QLabel {
                color: white;
                background-color: transparent;
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

        # Seção USB
        self.create_usb_section(main_layout)
        
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
        devices_group = QGroupBox("Configuração de Dispositivos por Wi-Fi")
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
        
        # Layout horizontal compacto
        apps_info_layout = QHBoxLayout()
        
        # Info sobre quantos apps serão removidos
        apps_count = len([app for app, enabled in self.app_manager.default_apps.items() if enabled])
        info_label = QLabel(f"Apps selecionados para remoção: {apps_count}")
        info_label.setStyleSheet("color: #888888; font-size: 11px;")
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

    def create_usb_section(self, parent_layout):
        usb_group = QGroupBox("Configuração USB - Instalação Automática")
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
        info_label.setStyleSheet("color: #888888; font-size: 10px; font-style: italic;")
        right_layout.addWidget(info_label)
        
        # Botões na horizontal
        buttons_layout = QHBoxLayout()
        
        # Botão para abrir pasta
        open_folder_button = QPushButton("Abrir Pasta")
        open_folder_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                font-size: 10px;
                padding: 5px 10px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        open_folder_button.clicked.connect(self.open_apk_folder)
        buttons_layout.addWidget(open_folder_button)
        
        # Botão USB
        usb_button = QPushButton("Configurar Rápido")
        usb_button.setObjectName("usb")
        usb_button.setStyleSheet("""
            QPushButton#usb {
                background-color: #ff6b35;
                min-width: 100px;
            }
            QPushButton#usb:hover {
                background-color: #e55a2b;
            }
        """)
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConfiguradorDPI()
    window.show()
    sys.exit(app.exec()) 