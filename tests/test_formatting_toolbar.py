import sys
import unittest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QTextCursor

from app.editor import MarkdownEditor
from app.formatting_toolbar import FormattingToolbar
from app.main_window import MainWindow

app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)


class TestFormattingToolbar(unittest.TestCase):
    def setUp(self):
        self.editor = MarkdownEditor()

    def test_wrap_selection_bold_markdown(self):
        self.editor.setPlainText("Renda mínima registrada:")
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.Document)
        self.editor.setTextCursor(cursor)

        self.editor.wrap_selection("**", "**", "texto")
        self.assertEqual(self.editor.toPlainText(), "**Renda mínima registrada:**")

    def test_wrap_selection_bold_html(self):
        self.editor.setPlainText("Renda mínima registrada:")
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.Document)
        self.editor.setTextCursor(cursor)

        self.editor.wrap_selection("<strong>", "</strong>", "texto")
        self.assertEqual(self.editor.toPlainText(), "<strong>Renda mínima registrada:</strong>")

    def test_wrap_selection_italic_and_underline(self):
        self.editor.setPlainText("Importante")
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.Document)
        self.editor.setTextCursor(cursor)

        self.editor.wrap_selection("<u>", "</u>", "texto")
        self.assertEqual(self.editor.toPlainText(), "<u>Importante</u>")

    def test_toggle_unnumbered_heading(self):
        self.editor.setPlainText("# INTRODUÇÃO\nTexto do parágrafo.")
        cursor = self.editor.textCursor()
        cursor.setPosition(2)  # Dentro da linha do título
        self.editor.setTextCursor(cursor)

        # Adiciona {-}
        self.editor.toggle_unnumbered()
        self.assertTrue(self.editor.toPlainText().startswith("# INTRODUÇÃO {-}"))

        # Alterna de volta removendo {-}
        self.editor.toggle_unnumbered()
        self.assertTrue(self.editor.toPlainText().startswith("# INTRODUÇÃO"))
        self.assertNotIn("{-}", self.editor.toPlainText())

    def test_set_heading_level(self):
        self.editor.setPlainText("Objetivo Geral")
        cursor = self.editor.textCursor()
        cursor.setPosition(0)
        self.editor.setTextCursor(cursor)

        # Nível 1 (#)
        self.editor.set_heading_level(1)
        self.assertEqual(self.editor.toPlainText(), "# Objetivo Geral")

        # Nível 2 (##)
        self.editor.set_heading_level(2)
        self.assertEqual(self.editor.toPlainText(), "## Objetivo Geral")

        # Nível 0 (Normal)
        self.editor.set_heading_level(0)
        self.assertEqual(self.editor.toPlainText(), "Objetivo Geral")

    def test_insert_line_break_and_page_break(self):
        self.editor.setPlainText("Linha 1")
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.editor.setTextCursor(cursor)

        self.editor.insert_line_break()
        self.assertIn("<br>", self.editor.toPlainText())

        self.editor.insert_page_break()
        self.assertIn("<div class=\"page-break\"></div>", self.editor.toPlainText())

    def test_insert_bash_code_block(self):
        self.editor.setPlainText("echo 'Hello World'")
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.Document)
        self.editor.setTextCursor(cursor)

        self.editor.insert_code_block("bash")
        text = self.editor.toPlainText()
        self.assertIn("```bash", text)
        self.assertIn("echo 'Hello World'", text)
        self.assertIn("```", text)

    def test_format_lists(self):
        self.editor.setPlainText("Primeiro item\nSegundo item")
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.Document)
        self.editor.setTextCursor(cursor)

        # Lista com marcadores
        self.editor.format_list(numbered=False)
        text = self.editor.toPlainText()
        self.assertIn("- Primeiro item", text)
        self.assertIn("- Segundo item", text)

        # Lista numerada padrão (1. 2.)
        cursor.select(QTextCursor.Document)
        self.editor.setTextCursor(cursor)
        self.editor.format_list(numbered=True)
        text_num = self.editor.toPlainText()
        self.assertIn("1. Primeiro item", text_num)
        self.assertIn("2. Segundo item", text_num)

        # Lista com parênteses (1) 2))
        cursor.select(QTextCursor.Document)
        self.editor.setTextCursor(cursor)
        self.editor.format_list(list_type="numbered_paren")
        text_paren = self.editor.toPlainText()
        self.assertIn("1) Primeiro item", text_paren)
        self.assertIn("2)棒Segundo item" if "棒" in text_paren else "2) Segundo item", text_paren)

        # Lista alfabética / alíneas (a. b.)
        cursor.select(QTextCursor.Document)
        self.editor.setTextCursor(cursor)
        self.editor.format_list(list_type="alpha")
        text_alpha = self.editor.toPlainText()
        self.assertIn("a. Primeiro item", text_alpha)
        self.assertIn("b. Segundo item", text_alpha)

        # Lista alfabética com parêntese (a) b))
        cursor.select(QTextCursor.Document)
        self.editor.setTextCursor(cursor)
        self.editor.format_list(list_type="alpha_paren")
        text_alpha_p = self.editor.toPlainText()
        self.assertIn("a) Primeiro item", text_alpha_p)
        self.assertIn("b) Segundo item", text_alpha_p)


    def test_insert_table_and_citation_and_math(self):
        self.editor.setPlainText("")
        self.editor.insert_table_template(rows=2, cols=2)
        text = self.editor.toPlainText()
        self.assertIn("| Coluna 1 | Coluna 2 |", text)

        self.editor.insert_citation_block()
        self.assertIn("<div class=\"citacao\">", self.editor.toPlainText())

        self.editor.insert_math_formula(block=False)
        self.assertIn("$", self.editor.toPlainText())

    def test_insert_tab_and_unindent(self):
        # Inserção sem seleção
        self.editor.setPlainText("")
        self.editor.insert_tab(spaces=4)
        self.assertEqual(self.editor.toPlainText(), "    ")

        # Indentação de múltiplas linhas
        self.editor.setPlainText("Linha 1\nLinha 2")
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.Document)
        self.editor.setTextCursor(cursor)
        self.editor.insert_tab(spaces=4)
        self.assertEqual(self.editor.toPlainText(), "    Linha 1\n    Linha 2")

        # Desindentação de múltiplas linhas
        self.editor.unindent(spaces=4)
        self.assertEqual(self.editor.toPlainText(), "Linha 1\nLinha 2")

    def test_insert_space_types(self):
        self.editor.setPlainText("")
        self.editor.insert_space("nbsp")
        self.assertEqual(self.editor.toPlainText(), "&nbsp;")

        self.editor.setPlainText("")
        self.editor.insert_space("emsp")
        self.assertEqual(self.editor.toPlainText(), "&emsp;")

        self.editor.setPlainText("")
        self.editor.insert_space("quad")
        self.assertEqual(self.editor.toPlainText(), "    ")

    def test_toolbar_widget_actions(self):
        toolbar = FormattingToolbar(editor_provider=lambda: self.editor)
        self.editor.setPlainText("Texto Selecionado")
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.Document)
        self.editor.setTextCursor(cursor)

        # Dispara o botão negrito da toolbar
        toolbar._apply_bold()
        self.assertEqual(self.editor.toPlainText(), "**Texto Selecionado**")

        # Dispara toggle unnumbered
        self.editor.setPlainText("# CAPÍTULO")
        toolbar._toggle_unnumbered()
        self.assertIn("{-}", self.editor.toPlainText())

    def test_toolbar_integration_with_main_window(self):
        win = MainWindow()
        win.show()
        self.assertIsNotNone(win.formatting_toolbar)
        self.assertFalse(win.formatting_toolbar.isHidden())

        # Verifica ação no menu Visualização
        self.assertIsNotNone(win.act_formatting_toolbar)
        self.assertTrue(win.act_formatting_toolbar.isChecked())

        # Alterna visibilidade
        win.act_formatting_toolbar.setChecked(False)
        self.assertTrue(win.formatting_toolbar.isHidden())
        win.act_formatting_toolbar.setChecked(True)
        if win.compiler_thread and win.compiler_thread.isRunning():
            win.compiler_thread.wait(3000)
        win.close()


if __name__ == "__main__":
    unittest.main()
