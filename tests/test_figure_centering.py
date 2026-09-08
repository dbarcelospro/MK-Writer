import unittest
from unittest.mock import patch, MagicMock
import tempfile
from app.compiler import compile_markdown_to_pdf
from app.editor import MarkdownEditor

class TestFigureCentering(unittest.TestCase):
    @patch("subprocess.run")
    def test_compiler_injects_figure_css(self, mock_run):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_run.return_value = mock_proc

        written_md = []
        orig_ntf = tempfile.NamedTemporaryFile

        def mock_ntf(*args, **kwargs):
            handle = orig_ntf(*args, **kwargs)
            if kwargs.get("suffix") == ".md":
                orig_write = handle.write
                def recording_write(s):
                    written_md.append(s)
                    return orig_write(s)
                handle.write = recording_write
            return handle

        with patch("tempfile.NamedTemporaryFile", side_effect=mock_ntf):
            try:
                compile_markdown_to_pdf("# Teste\n\n![Grafico](img.png)\n", custom_output_path="/tmp/test_out.pdf")
            except Exception:
                pass

        full_md = "".join(written_md)
        self.assertIn("figure, div.figure, div.figura", full_md)
        self.assertIn("figure img, p img, img, .figura img", full_md)
        self.assertIn("margin-left: auto !important", full_md)
        self.assertIn("margin-right: auto !important", full_md)
        self.assertIn("figcaption, .figura-titulo, .caption-titulo", full_md)
        self.assertIn("p:has(img)", full_md)
        self.assertIn(".capa img, .capa-topo img", full_md)
        # Verifica regras de listas e continuidade de numeração
        self.assertIn("li > p, li p", full_md)
        self.assertIn("text-indent: 0 !important", full_md)
        self.assertIn('ol[start="6"] { counter-reset: list-item 5 !important; }', full_md)
        self.assertIn('ol[start="2"] { counter-reset: list-item 1 !important; }', full_md)

    def test_editor_insert_figure_template(self):
        editor = MarkdownEditor()
        editor.insert_figure_template()
        text = editor.toPlainText()
        self.assertIn('<div class="figura">', text)
        self.assertIn("**Figura 1**", text)
        self.assertIn("![](Imagens/figura.png)", text)
        self.assertIn("<small>Fonte: Elaborado pelos autores (2026).</small>", text)
        self.assertIn("</div>", text)

if __name__ == "__main__":
    unittest.main()
