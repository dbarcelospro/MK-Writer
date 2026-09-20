import os
import sys
import tempfile
import unittest

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication
import pymupdf

from app.pdf_viewer import PDFPageWidget, PDFViewer

# Garante que existe uma instância única de QApplication para os testes de GUI
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)


class TestPDFViewerSelection(unittest.TestCase):
    def setUp(self):
        # Cria um PDF temporário em memória com texto estruturado
        self.doc = pymupdf.open()
        self.page = self.doc.new_page(width=595, height=842)  # A4
        self.page.insert_text((50, 70), "Primeira linha do texto acadêmico.", fontsize=12)
        self.page.insert_text((50, 95), "Segunda linha com fórmulas e palavras.", fontsize=12)
        self.page.insert_text((50, 120), "Terceira linha final.", fontsize=12)

        # Segunda página para teste de coordenação multipágina
        self.page2 = self.doc.new_page(width=595, height=842)
        self.page2.insert_text((50, 70), "Página dois com outro conteúdo.", fontsize=12)

        self.temp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.temp_pdf_path = self.temp_pdf.name
        self.temp_pdf.close()
        self.doc.save(self.temp_pdf_path)
        self.doc.close()

    def tearDown(self):
        if os.path.exists(self.temp_pdf_path):
            os.remove(self.temp_pdf_path)

    def test_page_widget_creation_and_text_extraction(self):
        """Verifica se o PDFPageWidget inicializa corretamente com as palavras extraídas."""
        doc = pymupdf.open(self.temp_pdf_path)
        page = doc[0]
        words = page.get_text("words")
        doc.close()

        self.assertTrue(len(words) > 0)

        pixmap = QPixmap(100, 100)
        widget = PDFPageWidget(page_num=0, pixmap=pixmap, words=words, zoom_factor=1.0)

        self.assertEqual(widget.page_num, 0)
        self.assertEqual(len(widget.words), len(words))
        self.assertFalse(widget.has_selection())

    def test_find_word_index_and_hit_testing(self):
        """Verifica o algoritmo de identificação de palavras por coordenadas."""
        doc = pymupdf.open(self.temp_pdf_path)
        page = doc[0]
        words = page.get_text("words")
        doc.close()

        pixmap = QPixmap(100, 100)
        widget = PDFPageWidget(page_num=0, pixmap=pixmap, words=words, zoom_factor=1.0)

        # w[0] é "Primeira"
        first_word = words[0]
        cx = (first_word[0] + first_word[2]) / 2
        cy = (first_word[1] + first_word[3]) / 2

        idx = widget.find_word_index_at(cx, cy)
        self.assertEqual(idx, 0)
        self.assertEqual(words[idx][4], "Primeira")
        self.assertTrue(widget._is_over_text(cx, cy))

    def test_selection_and_text_reconstruction(self):
        """Verifica a seleção de intervalo de palavras e reconstituição do texto com quebras de linha."""
        doc = pymupdf.open(self.temp_pdf_path)
        page = doc[0]
        words = page.get_text("words")
        doc.close()

        pixmap = QPixmap(100, 100)
        widget = PDFPageWidget(page_num=0, pixmap=pixmap, words=words, zoom_factor=1.0)

        # Seleciona as três primeiras palavras: "Primeira", "linha", "do"
        widget.selected_indices = {0, 1, 2}
        self.assertTrue(widget.has_selection())

        text = widget.get_selected_text()
        self.assertIn("Primeira linha do", text)

        # Teste de cópia para o clipboard
        widget.copy_selected_text()
        clipboard_text = QApplication.clipboard().text()
        self.assertEqual(clipboard_text, text)

    def test_select_all_and_clear(self):
        """Verifica o método select_all e clear_selection."""
        doc = pymupdf.open(self.temp_pdf_path)
        page = doc[0]
        words = page.get_text("words")
        doc.close()

        pixmap = QPixmap(100, 100)
        widget = PDFPageWidget(page_num=0, pixmap=pixmap, words=words, zoom_factor=1.0)

        widget.select_all()
        self.assertEqual(len(widget.selected_indices), len(words))

        widget.clear_selection()
        self.assertEqual(len(widget.selected_indices), 0)
        self.assertFalse(widget.has_selection())

    def test_pdf_viewer_load_pdf_and_coordination(self):
        """Verifica o carregamento do PDF no viewer e a coordenação de seleção entre páginas."""
        viewer = PDFViewer()
        viewer.load_pdf(self.temp_pdf_path)

        self.assertEqual(len(viewer.page_widgets), 2)
        page1 = viewer.page_widgets[0]
        page2 = viewer.page_widgets[1]

        self.assertIsInstance(page1, PDFPageWidget)
        self.assertIsInstance(page2, PDFPageWidget)

        # Seleciona algo na página 1
        page1.selected_indices = {0}
        self.assertTrue(page1.has_selection())

        # Ao iniciar seleção na página 2, página 1 deve ser desmarcada
        page2.selection_started.emit(page2)
        self.assertFalse(page1.has_selection())


if __name__ == "__main__":
    unittest.main()
