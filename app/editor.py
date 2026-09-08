import re
from PyQt5.QtCore import QRect, QSize, Qt
from PyQt5.QtGui import (
    QColor,
    QCursor,
    QFont,
    QPainter,
    QPen,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
    QTextFormat,
)
from PyQt5.QtWidgets import QPlainTextEdit, QTextEdit, QWidget


class LineNumberArea(QWidget):
    """
    Widget auxiliar para desenhar os números das linhas na lateral esquerda do QPlainTextEdit.
    """
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


class MarkdownHighlighter(QSyntaxHighlighter):
    """
    Realçador de sintaxe (Syntax Highlighter) leve para elementos de Markdown e YAML frontmatter.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # Títulos (# ... ######)
        header_format = QTextCharFormat()
        header_format.setForeground(QColor("#2563EB"))  # Azul royal
        header_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((re.compile(r"^#{1,6}\s+.*$"), header_format))

        # Negrito (**texto** ou __texto__)
        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Bold)
        bold_format.setForeground(QColor("#0F766E"))  # Teal escuro
        self.highlighting_rules.append((re.compile(r"(\*\*|__)(.*?)\1"), bold_format))

        # Itálico (*texto* ou _texto_)
        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        italic_format.setForeground(QColor("#9D174D"))  # Magenta escuro
        self.highlighting_rules.append((re.compile(r"(\*|_)(.*?)\1"), italic_format))

        # Código inline (`code`)
        code_format = QTextCharFormat()
        code_format.setFontFamily("Consolas")
        code_format.setForeground(QColor("#D97706"))  # Âmbar
        code_format.setBackground(QColor("#FEF3C7"))  # Fundo levemente amarelado
        self.highlighting_rules.append((re.compile(r"`[^`]+`"), code_format))

        # Citações (> texto)
        quote_format = QTextCharFormat()
        quote_format.setForeground(QColor("#4B5563"))  # Cinza neutro
        quote_format.setFontItalic(True)
        self.highlighting_rules.append((re.compile(r"^\s*>.*$"), quote_format))

        # Links ([texto](url))
        link_format = QTextCharFormat()
        link_format.setForeground(QColor("#0284C7"))  # Azul claro
        link_format.setFontUnderline(True)
        self.highlighting_rules.append((re.compile(r"\[.*?\]\(.*?\)" ), link_format))

        # Listas (- ou * ou 1. ou 1) ou a. ou a))
        list_format = QTextCharFormat()
        list_format.setForeground(QColor("#DC2626"))  # Vermelho suave
        list_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((re.compile(r"^\s*([\*\-\+]|\d+[\.\)]|[a-zA-Z][\.\)])\s+"), list_format))

        # YAML Frontmatter chave: valor
        yaml_key_format = QTextCharFormat()
        yaml_key_format.setForeground(QColor("#7C3AED"))  # Roxo
        yaml_key_format.setFontWeight(QFont.Bold)
        self.highlighting_rules.append((re.compile(r"^\s*[\w\-]+:"), yaml_key_format))

        # Formatação para blocos de código multiline (```) com fundo retangular escuro
        self.code_block_format = QTextCharFormat()
        self.code_block_format.setFontFamily("Consolas")
        self.code_block_format.setBackground(QColor("#21252B"))  # Fundo escuro elegante
        self.code_block_format.setForeground(QColor("#ECEFF4"))  # Texto claro

        self.code_fence_format = QTextCharFormat()
        self.code_fence_format.setFontFamily("Consolas")
        self.code_fence_format.setFontWeight(QFont.Bold)
        self.code_fence_format.setBackground(QColor("#1E2227"))
        self.code_fence_format.setForeground(QColor("#61AFEF"))  # Azul suave

    def highlightBlock(self, text):
        # Verifica se estamos dentro de um bloco de código multiline (```)
        self.setCurrentBlockState(0)
        is_in_code = self.previousBlockState() == 1

        stripped = text.strip()
        if stripped.startswith("```"):
            if is_in_code:
                # Fim do bloco de código
                self.setFormat(0, len(text), self.code_fence_format)
                self.setCurrentBlockState(0)
            else:
                # Início do bloco de código
                self.setFormat(0, len(text), self.code_fence_format)
                self.setCurrentBlockState(1)
            return

        if is_in_code:
            # Linha interna do bloco de código
            self.setFormat(0, len(text), self.code_block_format)
            self.setCurrentBlockState(1)
            return

        # Para linhas normais fora do bloco de código, aplica as regras padrão
        for pattern, fmt in self.highlighting_rules:
            for match in pattern.finditer(text):
                start, end = match.span()
                self.setFormat(start, end - start, fmt)



class MarkdownEditor(QPlainTextEdit):
    """
    Editor avançado de texto com suporte a numeração de linhas, fonte monoespaçada e realce de Markdown.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)

        # Conecta sinais do editor à atualização da barra de números
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        # Configuração de fonte monoespaçada
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.Monospace)
        font.setFixedPitch(True)
        self.setFont(font)

        # Realçador de sintaxe
        self.highlighter = MarkdownHighlighter(self.document())

        # Configurações visuais do editor
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.setTabChangesFocus(False)
        self.update_line_number_area_width(0)
        self.highlight_current_line()

        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #FAFAFA;
                color: #1E293B;
                selection-background-color: #93C5FD;
                selection-color: #0F172A;
                border: none;
                font-family: 'Consolas', 'DejaVu Sans Mono', 'Monospace', monospace;
                font-size: 11pt;
            }
        """)

    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, newBlockCount):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#E2E8F0")  # Slate suave
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#F1F5F9"))  # Fundo levemente cinza

        # Borda lateral direita da área dos números
        painter.setPen(QColor("#CBD5E1"))
        painter.drawLine(
            event.rect().width() - 1, event.rect().top(),
            event.rect().width() - 1, event.rect().bottom()
        )

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        painter.setPen(QColor("#64748B"))
        painter.setFont(self.font())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0, top, self.line_number_area.width() - 8, self.fontMetrics().height(),
                    Qt.AlignRight, number
                )

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def keyPressEvent(self, event):
        # Suporte a Tab para indentar e Shift+Tab / Backtab para desindentar
        if event.key() == Qt.Key_Tab and not (event.modifiers() & Qt.ControlModifier):
            if event.modifiers() & Qt.ShiftModifier:
                self.unindent()
                return
            else:
                self.insert_tab()
                return
        elif event.key() == Qt.Key_Backtab:
            self.unindent()
            return

        super().keyPressEvent(event)

    def insert_tab(self, spaces: int = 4):
        """
        Insere tabulação ou indenta as linhas selecionadas com 4 espaços.
        Se houver seleção de múltiplas linhas, indenta todas as linhas selecionadas.
        """
        cursor = self.textCursor()
        cursor.beginEditBlock()
        if cursor.hasSelection():
            start = cursor.selectionStart()
            end = cursor.selectionEnd()

            cursor.setPosition(start)
            cursor.movePosition(QTextCursor.StartOfLine)
            start_pos = cursor.position()

            cursor.setPosition(end)
            cursor.movePosition(QTextCursor.EndOfLine)
            end_pos = cursor.position()

            cursor.setPosition(start_pos)
            cursor.setPosition(end_pos, QTextCursor.KeepAnchor)

            text = cursor.selectedText()
            lines = text.split("\u2029")
            indented = [(" " * spaces + line) if line else line for line in lines]
            new_text = "\u2029".join(indented)
            cursor.insertText(new_text)

            cursor.setPosition(start_pos)
            cursor.setPosition(start_pos + len(new_text), QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)
        else:
            cursor.insertText(" " * spaces)
        cursor.endEditBlock()

    def unindent(self, spaces: int = 4):
        """
        Desindenta as linhas selecionadas (ou linha atual) removendo até 4 espaços ou 1 tab.
        """
        cursor = self.textCursor()
        cursor.beginEditBlock()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.StartOfLine)
        start_pos = cursor.position()

        cursor.setPosition(end)
        cursor.movePosition(QTextCursor.EndOfLine)
        end_pos = cursor.position()

        cursor.setPosition(start_pos)
        cursor.setPosition(end_pos, QTextCursor.KeepAnchor)

        text = cursor.selectedText()
        lines = text.split("\u2029")
        unindented = []
        for line in lines:
            if line.startswith(" " * spaces):
                unindented.append(line[spaces:])
            elif line.startswith("\t"):
                unindented.append(line[1:])
            else:
                stripped_len = len(line) - len(line.lstrip(" "))
                to_remove = min(stripped_len, spaces)
                unindented.append(line[to_remove:])

        new_text = "\u2029".join(unindented)
        cursor.insertText(new_text)

        if start != end:
            cursor.setPosition(start_pos)
            cursor.setPosition(start_pos + len(new_text), QTextCursor.KeepAnchor)
            self.setTextCursor(cursor)
        cursor.endEditBlock()

    def insert_space(self, space_type: str = "nbsp"):
        """
        Insere espaço formatado:
        - "nbsp": &nbsp; (espaço inquebrável / não-separável)
        - "emsp": &emsp; (espaço largo / tabulação)
        - "quad": 4 espaços
        - "single": 1 espaço comum
        """
        cursor = self.textCursor()
        if space_type == "nbsp":
            cursor.insertText("&nbsp;")
        elif space_type == "emsp":
            cursor.insertText("&emsp;")
        elif space_type == "quad":
            cursor.insertText("    ")
        else:
            cursor.insertText(" ")

    # ── MÉTODOS DE FORMATAÇÃO E AUTOMAÇÃO DE ESCRITA ──

    def wrap_selection(self, prefix: str, suffix: str, default_text: str = ""):
        """Envolve o texto selecionado com prefix e suffix. Se não houver seleção, insere default_text."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        if cursor.hasSelection():
            selected = cursor.selectedText()
            cursor.insertText(f"{prefix}{selected}{suffix}")
        else:
            cursor.insertText(f"{prefix}{default_text}{suffix}")
            if default_text:
                pos = cursor.position() - len(suffix)
                cursor.setPosition(pos - len(default_text))
                cursor.setPosition(pos, QTextCursor.KeepAnchor)
                self.setTextCursor(cursor)
        cursor.endEditBlock()

    def set_heading_level(self, level: int):
        """Define o nível de cabeçalho (0 = normal, 1 = #, 2 = ##, etc.) na linha atual."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        line = cursor.selectedText()

        # Remove marcação existente de título (# ... ####)
        clean = re.sub(r"^#{1,6}\s+", "", line)
        
        if level > 0:
            new_line = f"{'#' * level} {clean}"
        else:
            new_line = clean
            
        cursor.insertText(new_line)
        cursor.endEditBlock()

    def toggle_unnumbered(self):
        """Alterna a tag {-} ou {.unnumbered} na linha do título atual."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.StartOfLine)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        line = cursor.selectedText()

        if "{-}" in line:
            new_line = line.replace(" {-}", "").replace("{-}", "")
        elif "{.unnumbered}" in line:
            new_line = line.replace(" {.unnumbered}", "").replace("{.unnumbered}", "")
        else:
            # Se já for título, adiciona {-}
            if line.startswith("#"):
                new_line = line.rstrip() + " {-}"
            else:
                new_line = f"# {line.rstrip()} {{-}}"

        cursor.insertText(new_line)
        cursor.endEditBlock()

    def insert_line_break(self):
        """Insere quebra de linha manual HTML <br>."""
        cursor = self.textCursor()
        cursor.insertText("<br>\n")

    def insert_page_break(self):
        """Insere quebra de página ABNT."""
        cursor = self.textCursor()
        cursor.insertText("\n<div class=\"page-break\"></div>\n\n")

    def format_list(self, list_type: str = "bullet", numbered: bool = None):
        """
        Formata as linhas selecionadas como lista ou alíneas:
        - "bullet": marcadores '- '
        - "numbered": numeração '1. ', '2. '...
        - "numbered_paren": numeração com parêntese '1) ', '2) '...
        - "alpha": alíneas alfabéticas 'a. ', 'b. ', 'c. '...
        - "alpha_paren": alíneas com parêntese 'a) ', 'b) '...
        """
        if numbered is not None:
            list_type = "numbered" if numbered else "bullet"

        cursor = self.textCursor()
        cursor.beginEditBlock()

        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        cursor.setPosition(start)
        cursor.movePosition(QTextCursor.StartOfLine)
        start_pos = cursor.position()

        cursor.setPosition(end)
        cursor.movePosition(QTextCursor.EndOfLine)
        end_pos = cursor.position()

        cursor.setPosition(start_pos)
        cursor.setPosition(end_pos, QTextCursor.KeepAnchor)

        text = cursor.selectedText()
        lines = text.split("\u2029")
        if len(lines) == 1 and not text:
            lines = [""]

        new_lines = []
        for i, line in enumerate(lines):
            stripped = line.lstrip()
            # Remove qualquer prefixo anterior (-, *, +, 1., 1), a., a))
            clean = re.sub(r"^([*\-+]|\d+[\.\)]|[a-zA-Z][\.\)])\s+", "", stripped)

            if list_type == "alpha":
                letter = chr(ord('a') + (i % 26))
                prefix = f"{letter}. "
            elif list_type == "alpha_paren":
                letter = chr(ord('a') + (i % 26))
                prefix = f"{letter}) "
            elif list_type == "numbered_paren":
                prefix = f"{i + 1}) "
            elif list_type == "numbered":
                prefix = f"{i + 1}. "
            else:
                prefix = "- "

            new_lines.append(prefix + (clean if clean else "Item"))

        cursor.insertText("\n".join(new_lines))
        cursor.endEditBlock()


    def insert_code_block(self, language: str = "bash"):
        """Insere bloco de código cercado por crases triplas."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        if cursor.hasSelection():
            selected = cursor.selectedText().replace("\u2029", "\n")
            cursor.insertText(f"\n```{language}\n{selected}\n```\n")
        else:
            cursor.insertText(f"\n```{language}\n# Comandos aqui\n```\n")
        cursor.endEditBlock()

    def insert_table_template(self, rows: int = 3, cols: int = 3):
        """Insere modelo de tabela Markdown formatada."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        header = "| " + " | ".join([f"Coluna {i+1}" for i in range(cols)]) + " |"
        sep = "| " + " | ".join([":---" for _ in range(cols)]) + " |"
        data_rows = ["| " + " | ".join([f"Dado {r+1}.{c+1}" for c in range(cols)]) + " |" for r in range(rows)]
        table_md = "\n" + "\n".join([header, sep] + data_rows) + "\n\n"
        cursor.insertText(table_md)
        cursor.endEditBlock()

    def insert_figure_template(self):
        """Insere modelo ABNT para figuras com legenda superior, imagem e fonte inferior centralizadas."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        template = (
            "\n<div class=\"figura\">\n\n"
            "**Figura 1** — Título ou Legenda da Figura\n\n"
            "![](Imagens/figura.png)\n\n"
            "<small>Fonte: Elaborado pelos autores (2026).</small>\n\n"
            "</div>\n\n"
        )
        cursor.insertText(template)
        cursor.endEditBlock()

    def insert_citation_block(self):
        """Insere bloco de citação direta longa ABNT (> 3 linhas, recuo 4cm)."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        if cursor.hasSelection():
            text = cursor.selectedText().replace("\u2029", "\n")
        else:
            text = "Texto da citação longa com mais de três linhas, recuo de 4cm da margem esquerda, fonte tamanho 10 e espaçamento simples (ABNT NBR 10520)."
        template = f"\n<div class=\"citacao\">\n{text}\n</div>\n\n"
        cursor.insertText(template)
        cursor.endEditBlock()

    def insert_math_formula(self, block: bool = False):
        """Insere fórmula matemática LaTeX."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        selected = cursor.selectedText()
        if block:
            formula = selected if selected else "E = mc^2"
            cursor.insertText(f"\n$$\n{formula}\n$$\n")
        else:
            formula = selected if selected else "x = \\frac{-b \\pm \\sqrt{\\Delta}}{2a}"
            cursor.insertText(f"${formula}$")
        cursor.endEditBlock()

    def insert_link_template(self):
        """Insere link em Markdown [texto](url)."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        if cursor.hasSelection():
            selected = cursor.selectedText()
            cursor.insertText(f"[{selected}](https://)")
        else:
            cursor.insertText("[Texto do Link](https://)")
        cursor.endEditBlock()

    def insert_footnote_template(self):
        """Insere nota de rodapé no formato Markdown."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        cursor.insertText("[^1]\n\n[^1]: Texto da nota de rodapé.\n")
        cursor.endEditBlock()

    def insert_bib_citation_template(self):
        """Insere citação bibliográfica no padrão Pandoc/BibTeX [@chave]."""
        cursor = self.textCursor()
        cursor.beginEditBlock()
        if cursor.hasSelection():
            selected = cursor.selectedText()
            cursor.insertText(f"[@{selected}]")
        else:
            cursor.insertText("[@chave_bib]")
        cursor.endEditBlock()

