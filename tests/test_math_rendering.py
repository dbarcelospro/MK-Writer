import os
import sys
import unittest
from PyQt5.QtWidgets import QApplication
from app.compiler import compile_markdown_to_pdf
from app.editor import MarkdownEditor

app = QApplication.instance() or QApplication(sys.argv)


class TestMathRendering(unittest.TestCase):
    def test_editor_math_highlighting(self):
        """Verifica se o editor aplica formatação de realce a fórmulas em bloco e inline."""
        editor = MarkdownEditor()
        editor.setPlainText("Equação $x = 1$ e bloco:\n$$n_0 = \\frac{Z^2 \\cdot p \\cdot q}{e^2}$$")

        doc = editor.document()
        # Linha 0 tem fórmula inline
        block0 = doc.findBlockByNumber(0)
        self.assertTrue(len(block0.layout().formats()) >= 1)

        # Linha 1 tem fórmula em bloco
        block1 = doc.findBlockByNumber(1)
        self.assertTrue(len(block1.layout().formats()) >= 1)

    def test_compiler_math_to_pdf(self):
        """Verifica se o compilador gera o PDF com sucesso para documentos com fórmulas matemáticas."""
        md_content = """# Teste Matemática

Fórmula em bloco:

$$n_0 = \\frac{Z^2 \\cdot p \\cdot q}{e^2}$$

Fórmula inline: $E = mc^2$.
"""
        pdf_path, err, elapsed = compile_markdown_to_pdf(md_content)
        self.assertIsNotNone(pdf_path)
        self.assertTrue(os.path.exists(pdf_path))
        self.assertEqual(err, "")
        if os.path.exists(pdf_path):
            os.remove(pdf_path)


if __name__ == "__main__":
    unittest.main()
