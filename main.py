#!/usr/bin/env python3
import os
import sys

# Se executado diretamente pelo Python do sistema e existir o venv local do projeto,
# re-executa utilizando o interpretador do venv para garantir todas as dependências.
venv_python = os.path.abspath(os.path.join(os.path.dirname(__file__), "venv", "bin", "python3"))
if os.path.exists(venv_python) and sys.executable != venv_python and not os.environ.get("LATEXMDOWN_IN_VENV"):
    os.environ["LATEXMDOWN_IN_VENV"] = "1"
    os.execv(venv_python, [venv_python] + sys.argv)

# Configurações de ambiente do QtWebEngine/Chromium para evitar travamentos de GPU/Wayland no Linux
os.environ["QTWEBENGINE_DISABLE_SANDBOX"] = "1"
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer --no-sandbox"

import logging

log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "mk_writer.log"))
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filemode="a",
)
logging.info("=== Inicializando MK Writer ===")

def main():
    logging.info("Verificando dependências Python...")
    # 1. Verificação prévia de dependências do Python
    from app.dependency_check import check_python_dependencies
    py_ok, py_missing, py_msg = check_python_dependencies()

    if not py_ok:
        logging.error(f"Dependências Python ausentes: {py_msg}")
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            app = QApplication(sys.argv)
            QMessageBox.critical(None, "Dependências Python Ausentes", py_msg)
        except Exception:
            print("[ERRO CRÍTICO]", py_msg, file=sys.stderr)
        sys.exit(1)

    # 2. Inicialização da QApplication
    from PyQt5.QtWidgets import QApplication, QMessageBox
    from PyQt5.QtCore import Qt, QTimer

    # Habilita suporte a High DPI
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    from PyQt5.QtGui import QIcon
    app = QApplication(sys.argv)
    app.setApplicationName("MK Writer")
    app.setOrganizationName("MK Writer")

    icon_path = os.path.join(os.path.dirname(__file__), "resources", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    # 3. Exibe Splash Screen
    import time
    from app.splash import MKSplashScreen
    splash = MKSplashScreen()
    splash.show()

    splash.set_progress(15, "Verificando ambiente e dependências...")
    time.sleep(0.4)

    # 4. Verificação de binários e ferramentas externas (Pandoc / Engine PDF)
    from app.dependency_check import check_external_dependencies
    splash.set_progress(45, "Verificando Pandoc e WeasyPrint...")
    time.sleep(0.5)
    ext_ok, ext_info = check_external_dependencies()

    if not ext_ok:
        splash.hide()
        warning_box = QMessageBox()
        warning_box.setIcon(QMessageBox.Warning)
        warning_box.setWindowTitle("Aviso de Dependências Externas")
        warning_box.setText("Algumas ferramentas externas não foram encontradas:")
        warning_box.setInformativeText(ext_info["message"])
        warning_box.setStandardButtons(QMessageBox.Ok)
        warning_box.exec_()
        splash.show()

    # 5. Inicializa a Janela Principal
    splash.set_progress(75, "Carregando a interface do MK Writer...")
    time.sleep(0.5)
    logging.info("Inicializando janela principal...")

    initial_path = None
    if len(sys.argv) > 1 and sys.argv[1]:
        raw_arg = sys.argv[1].strip()
        if raw_arg.startswith("file://"):
            from urllib.parse import unquote, urlparse
            raw_arg = unquote(urlparse(raw_arg).path)

        arg_path = os.path.abspath(raw_arg)
        if os.path.exists(arg_path):
            initial_path = arg_path
            logging.info(f"Caminho inicial fornecido via argumento CLI: {initial_path}")

    from app.main_window import MainWindow
    window = MainWindow(external_info=ext_info, initial_path=initial_path)

    splash.set_progress(100, "Pronto!")
    logging.info("Aplicação iniciada com sucesso. Abrindo interface gráfica.")
    
    # Exibe a janela principal após 1.2s mantendo o splash na tela por ~2.5s no total
    QTimer.singleShot(1200, lambda: (splash.close(), window.show()))

    sys.exit(app.exec_())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.critical("Exceção não tratada ao executar a aplicação", exc_info=True)
        raise e

