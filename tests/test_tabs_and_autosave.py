import os
import sys
import tempfile
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QSettings

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.package_manager import create_new_package
from app.main_window import MainWindow
from app.ai_assistant import AISettingsDialog

def test_tabs_and_autosave():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Cria pacote de teste
        pkg_path = os.path.join(tmp_dir, "TesteTabs.mkw")
        create_new_package(pkg_path, title="Teste Tabs", author="Danilo")

        window = MainWindow(initial_path=pkg_path)

        # 1. Verifica layout: left_splitter possui árvore de arquivos e IA
        assert hasattr(window, "left_splitter")
        assert window.left_splitter.count() == 2
        assert window.left_splitter.widget(0) == window.file_tree
        assert window.left_splitter.widget(1) == window.ai_assistant

        # 2. Verifica editor de abas
        assert hasattr(window, "editor_tabs")
        assert window.editor_tabs.count() >= 1

        # Abre capítulos adicionais em novas abas
        cap1 = os.path.join(window.project_root_dir, "02_Textual", "01_introducao.md")
        cap2 = os.path.join(window.project_root_dir, "02_Textual", "02_desenvolvimento.md")
        
        ed1 = window.open_file_in_tab(cap1)
        assert ed1 is not None
        assert window.editor == ed1
        assert window.editor_tabs.count() == 2
        assert os.path.basename(cap1) in window.editor_tabs.tabText(window.editor_tabs.currentIndex())

        ed2 = window.open_file_in_tab(cap2)
        assert ed2 is not None
        assert window.editor == ed2
        assert window.editor_tabs.count() == 3
        assert os.path.basename(cap2) in window.editor_tabs.tabText(window.editor_tabs.currentIndex())

        # 3. Testa salvamento automático ao alternar abas
        # Modifica o conteúdo da aba 2 (cap2)
        ed2.appendPlainText("\n<!-- Nova Linha Auto-Save -->")
        assert ed2.document().isModified()

        # Alterna para a aba 1 (cap1)
        tab1_idx = window.editor_tabs.indexOf(ed1)
        window.editor_tabs.setCurrentIndex(tab1_idx)

        # Verifica se o arquivo cap2 no disco foi automaticamente salvo
        updated_cap2_disk = open(cap2, "r", encoding="utf-8").read()
        assert "<!-- Nova Linha Auto-Save -->" in updated_cap2_disk, "O arquivo modificado deveria ter sido salvo automaticamente ao alternar abas!"
        assert not ed2.document().isModified(), "O estado de modificação da aba deveria ter sido limpo após auto-save."

        # 4. Testa salvamento automático ao abrir outro arquivo a partir da árvore
        ed1.appendPlainText("\n<!-- Alteracao em Introducao -->")
        assert ed1.document().isModified()
        
        cap3 = os.path.join(window.project_root_dir, "02_Textual", "03_conclusao.md")
        window.open_file_from_tree(cap3)

        updated_cap1_disk = open(cap1, "r", encoding="utf-8").read()
        assert "<!-- Alteracao em Introducao -->" in updated_cap1_disk, "O arquivo anterior deveria ter sido salvo automaticamente ao selecionar outro arquivo na árvore!"

        # 5. Testa fechamento de abas
        initial_count = window.editor_tabs.count()
        window.close_tab(window.editor_tabs.currentIndex())
        assert window.editor_tabs.count() == initial_count - 1

        # 6. Testa diálogo de configurações de IA
        ai_dialog = AISettingsDialog(parent=window)
        ai_dialog.combo_provider.setCurrentText("Gemini (Google)")
        ai_dialog.combo_model.setCurrentText("Gemini 2.5 Flash (Mais recente e rápido)")
        ai_dialog.input_key.setText("CHAVE_MOCK_TESTE_123")
        ai_dialog.save_and_accept()

        settings = QSettings("LatexMDown", "AIAssistant")
        assert settings.value("api_key") == "CHAVE_MOCK_TESTE_123"
        assert settings.value("provider") == "Gemini (Google)"

        if window.compiler_thread and window.compiler_thread.isRunning():
            window.compiler_thread.wait(3000)
        window.close()

    print("✓ test_tabs_and_autosave: TODOS OS TESTES PASSARAM COM SUCESSO!")

if __name__ == "__main__":
    test_tabs_and_autosave()
