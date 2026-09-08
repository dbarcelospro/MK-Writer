import os
import sys
import tempfile
from PyQt5.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.package_manager import create_new_package, is_package_file
from app.main_window import MainWindow

def test_main_window_package_loading():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    with tempfile.TemporaryDirectory() as tmp_dir:
        pkg_file = os.path.join(tmp_dir, "Trabalho_Danilo.mkw")
        create_new_package(pkg_file, title="Tese de Doutorado", author="Danilo")

        assert is_package_file(pkg_file)

        # Inicializa MainWindow passando o pacote como argumento
        window = MainWindow(initial_path=pkg_file)

        assert window.current_package_path == os.path.abspath(pkg_file)
        assert "[Pacote]" in window.windowTitle()
        assert "Trabalho_Danilo.mkw" in window.windowTitle()

        # Verifica árvore de arquivos
        assert "📦" in window.file_tree.header_label.text()
        assert "Trabalho_Danilo.mkw" in window.file_tree.header_label.text()

        # Verifica projetos recentes
        recents = window.get_recent_projects()
        assert os.path.abspath(pkg_file) in recents

        # Testa salvamento
        original_text = window.editor.toPlainText()
        window.editor.setPlainText(original_text + "\n\n<!-- Linha de teste de salvamento -->")
        window.save_file()

        if window.compiler_thread and window.compiler_thread.isRunning():
            window.compiler_thread.wait(3000)
        window.close()

    print("✓ test_main_window_package_loading: SUCESSO")

if __name__ == "__main__":
    test_main_window_package_loading()
