import os
import shutil
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from PyQt5.QtWidgets import QApplication
from app.main_window import MainWindow
from app.package_manager import create_new_package

app = QApplication.instance()
if not app:
    app = QApplication([])


class TestImageImport(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pkg_path = os.path.join(self.temp_dir.name, "test_pkg.mkw")
        create_new_package(self.pkg_path, "Projeto de Teste Imagem", "Autor Teste")

        # Cria uma imagem dummy para teste
        self.dummy_img = os.path.join(self.temp_dir.name, "grafico_teste.png")
        with open(self.dummy_img, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4")

        self.win = MainWindow(initial_path=self.pkg_path)
        self.win.show()

    def tearDown(self):
        if self.win.compiler_thread and self.win.compiler_thread.isRunning():
            self.win.compiler_thread.wait(3000)
        self.win.close()
        self.temp_dir.cleanup()

    def test_file_tree_has_import_image_button(self):
        self.assertTrue(hasattr(self.win.file_tree, "btn_import_image"))
        self.assertEqual(self.win.file_tree.btn_import_image.text(), "🖼️+")

    @patch("PyQt5.QtWidgets.QInputDialog.getText")
    @patch("PyQt5.QtWidgets.QFileDialog.getOpenFileName")
    def test_import_and_insert_image_into_editor(self, mock_get_open, mock_get_text):
        mock_get_open.return_value = (self.dummy_img, "Imagens (*.png)")
        mock_get_text.side_effect = [
            ("Figura 1 — Gráfico de Dispersão", True),  # Legenda
            ("Dados da pesquisa (2026).", True),         # Fonte
        ]

        # Garante que há um arquivo aberto no editor (ex: 01_introducao.md)
        intro_file = os.path.join(self.win.project_root_dir, "02_Textual", "01_introducao.md")
        self.win.open_file_in_tab(intro_file)
        self.assertIsNotNone(self.win.editor)

        # Executa importação e inserção
        self.win.import_and_insert_image()

        # Verifica se a imagem foi copiada para Imagens/
        img_dest = os.path.join(self.win.project_root_dir, "Imagens", "grafico_teste.png")
        self.assertTrue(os.path.exists(img_dest))

        # Verifica conteúdo no editor
        editor_text = self.win.editor.toPlainText()
        self.assertIn('<div class="figura">', editor_text)
        self.assertIn("**Figura 1 — Gráfico de Dispersão**", editor_text)
        self.assertIn("grafico_teste.png)", editor_text)
        self.assertIn("<small>Fonte: Dados da pesquisa (2026).</small>", editor_text)

        # Salva para sincronizar com o pacote .mkw
        self.win.save_file()

        # Verifica se a imagem foi compactada dentro do arquivo .mkw
        with zipfile.ZipFile(self.pkg_path, "r") as zf:
            names = zf.namelist()
            self.assertTrue(any("grafico_teste.png" in name for name in names), f"Imagem não encontrada no .mkw: {names}")


if __name__ == "__main__":
    unittest.main()
