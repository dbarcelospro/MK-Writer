"""
Módulo da Barra de Ferramentas de Formatação e Escrita Acadêmica (Formatting Toolbar).
Fornece automação de escrita para Markdown, tags HTML (como <strong> e <br>),
seções não numeradas {-}, blocos de código Bash, tabelas e normas ABNT.
"""

from typing import Callable, Optional
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QComboBox,
    QMenu,
    QShortcut,
    QToolBar,
    QToolButton,
    QWidget,
)

from app.editor import MarkdownEditor


class FormattingToolbar(QToolBar):
    """
    Barra de ferramentas de formatação rápida estilo processador de texto (Word / Google Docs),
    mas focada em produtividade acadêmica em Markdown + ABNT.
    """

    def __init__(
        self,
        editor_provider: Callable[[], Optional[MarkdownEditor]],
        image_importer: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None
    ):
        super().__init__("Barra de Formatação", parent)
        self.editor_provider = editor_provider
        self.image_importer = image_importer
        self.setMovable(False)
        self.setObjectName("FormattingToolbar")
        self.init_style()
        self.build_tools()

    def get_editor(self) -> Optional[MarkdownEditor]:
        """Retorna a instância do editor atualmente ativo na aba em foco."""
        if callable(self.editor_provider):
            return self.editor_provider()
        return None

    def init_style(self):
        """Estilo visual limpo, moderno e harmônico com o tema do MK Writer."""
        self.setStyleSheet("""
            QToolBar#FormattingToolbar {
                background-color: #F8FAFC;
                border-top: 1px solid #E2E8F0;
                border-bottom: 1px solid #CBD5E1;
                spacing: 1px;
                padding: 2px 4px;
            }
            QToolButton {
                background-color: transparent;
                color: #334155;
                font-weight: 600;
                font-size: 8.5pt;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 2px 4px;
                margin: 0px 1px;
            }
            QToolButton:hover {
                background-color: #E2E8F0;
                color: #0F172A;
                border: 1px solid #CBD5E1;
            }
            QToolButton:pressed {
                background-color: #CBD5E1;
            }
            QToolButton::menu-button {
                border: none;
                border-top-right-radius: 4px;
                border-bottom-right-radius: 4px;
                width: 10px;
                background-color: transparent;
            }
            QToolButton::menu-button:hover {
                background-color: rgba(0, 0, 0, 0.08);
            }
            QToolButton::menu-arrow {
                width: 0px;
                height: 0px;
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 4px solid #475569;
                margin-top: 1px;
            }
            QComboBox {
                background-color: #FFFFFF;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 8.5pt;
                font-weight: 500;
                min-width: 100px;
                max-width: 125px;
            }
            QComboBox:hover {
                border-color: #3B82F6;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #1E293B;
                selection-background-color: #EFF6FF;
                selection-color: #1D4ED8;
                border: 1px solid #CBD5E1;
            }
        """)

    def build_tools(self):
        """Cria e organiza todos os botões e seletores da barra de ferramentas."""

        # ── 1. Histórico: Desfazer / Refazer ──
        act_undo = self.addAction("↩️")
        act_undo.setToolTip("Desfazer (Ctrl+Z)")
        act_undo.triggered.connect(lambda: self._call_editor("undo"))

        act_redo = self.addAction("↪️")
        act_redo.setToolTip("Refazer (Ctrl+Y)")
        act_redo.triggered.connect(lambda: self._call_editor("redo"))

        self.addSeparator()

        # ── 2. Nível de Título / Estilo (Dropdown) ──
        self.combo_heading = QComboBox(self)
        self.combo_heading.setToolTip("Nível do Título / Cabeçalho")
        self.combo_heading.addItems([
            "Texto Normal",
            "Título 1 (#)",
            "Título 2 (##)",
            "Título 3 (###)",
            "Título 4 (####)",
        ])
        self.combo_heading.activated.connect(self._on_heading_changed)
        self.addWidget(self.combo_heading)

        self.addSeparator()

        # ── 3. Formatação em Linha: Negrito, Itálico, Sublinhado, Tachado ──
        # Negrito Markdown (**)
        self.btn_bold = QToolButton(self)
        self.btn_bold.setText("B")
        font_bold = self.btn_bold.font()
        font_bold.setBold(True)
        self.btn_bold.setFont(font_bold)
        self.btn_bold.setToolTip("Negrito Markdown (**texto**)")
        self.btn_bold.clicked.connect(self._apply_bold)
        self.addWidget(self.btn_bold)

        # Negrito HTML (<strong>)
        self.btn_strong = QToolButton(self)
        self.btn_strong.setText("<strong>")
        self.btn_strong.setToolTip("Negrito HTML (<strong>texto</strong>)")
        self.btn_strong.setStyleSheet("font-size: 8pt; font-weight: bold; color: #0F766E;")
        self.btn_strong.clicked.connect(lambda: self._wrap_active("<strong>", "</strong>", "texto"))
        self.addWidget(self.btn_strong)


        # Itálico (*)
        self.btn_italic = QToolButton(self)
        self.btn_italic.setText("I")
        font_italic = self.btn_italic.font()
        font_italic.setItalic(True)
        self.btn_italic.setFont(font_italic)
        self.btn_italic.setToolTip("Itálico (*texto*)")
        self.btn_italic.clicked.connect(lambda: self._wrap_active("*", "*", "texto"))
        self.addWidget(self.btn_italic)

        # Sublinhado (<u>texto</u>)
        self.btn_underline = QToolButton(self)
        self.btn_underline.setText("U")
        font_underline = self.btn_underline.font()
        font_underline.setUnderline(True)
        self.btn_underline.setFont(font_underline)
        self.btn_underline.setToolTip("Sublinhado (<u>texto</u>) [Ctrl+U]")
        self.btn_underline.clicked.connect(lambda: self._wrap_active("<u>", "</u>", "texto"))
        self.addWidget(self.btn_underline)

        # Tachado (~~texto~~)
        self.btn_strike = QToolButton(self)
        self.btn_strike.setText("S")
        font_strike = self.btn_strike.font()
        font_strike.setStrikeOut(True)
        self.btn_strike.setFont(font_strike)
        self.btn_strike.setToolTip("Tachado (~~texto~~)")
        self.btn_strike.clicked.connect(lambda: self._wrap_active("~~", "~~", "texto"))
        self.addWidget(self.btn_strike)

        self.addSeparator()

        # ── 4. Seção Sem Numeração: {-} ──
        self.btn_unnumbered = QToolButton(self)
        self.btn_unnumbered.setText("{-}")
        self.btn_unnumbered.setToolTip("Alternar Título Sem Numeração {-} (Evita '1. INTRODUÇÃO' no PDF)")
        self.btn_unnumbered.setStyleSheet("color: #D97706; font-weight: bold;")
        self.btn_unnumbered.clicked.connect(self._toggle_unnumbered)
        self.addWidget(self.btn_unnumbered)

        # ── 5. Quebra de Página, Espaços e Tabulação ──
        self.btn_br = QToolButton(self)
        self.btn_br.setText("<br>")
        self.btn_br.setToolTip("Inserir Quebra de Linha Manual (<br>)")
        self.btn_br.setStyleSheet("color: #2563EB; font-weight: bold;")
        self.btn_br.clicked.connect(self._insert_line_break)
        self.addWidget(self.btn_br)

        act_pagebreak = self.addAction("Quebra")
        act_pagebreak.setToolTip("Inserir Quebra de Página ABNT (<div class='page-break'></div>)")
        act_pagebreak.triggered.connect(self._insert_page_break)

        # ── Botão Espaço com Dropdown ──
        self.btn_space = QToolButton(self)
        self.btn_space.setText("␣ Espaço")
        self.btn_space.setToolTip("Inserir Espaço Fixo (&nbsp;)")
        self.btn_space.setPopupMode(QToolButton.MenuButtonPopup)
        self.btn_space.setStyleSheet("color: #0284C7; font-weight: bold;")
        self.btn_space.clicked.connect(lambda: self._insert_space("nbsp"))

        menu_space = QMenu(self)
        menu_space.addAction("Espaço Fixo Normal (&nbsp;)").triggered.connect(lambda: self._insert_space("nbsp"))
        menu_space.addAction("Espaço Largo M-Space (&emsp;)").triggered.connect(lambda: self._insert_space("emsp"))
        menu_space.addAction("Espaço Quádruplo (4 espaços)").triggered.connect(lambda: self._insert_space("quad"))
        self.btn_space.setMenu(menu_space)
        self.addWidget(self.btn_space)

        # ── Botão Tab com Dropdown ──
        self.btn_tab = QToolButton(self)
        self.btn_tab.setText("⇥ Tab")
        self.btn_tab.setToolTip("Inserir Tabulação / Indentar (Tab)")
        self.btn_tab.setPopupMode(QToolButton.MenuButtonPopup)
        self.btn_tab.setStyleSheet("color: #6366F1; font-weight: bold;")
        self.btn_tab.clicked.connect(lambda: self._insert_tab())

        menu_tab = QMenu(self)
        menu_tab.addAction("Indentar 4 Espaços (Padrão)").triggered.connect(self._insert_tab)
        menu_tab.addAction("Desindentar Seleção (Shift+Tab)").triggered.connect(self._unindent)
        menu_tab.addAction("Tabulação HTML (&emsp;)").triggered.connect(lambda: self._insert_space("emsp"))
        self.btn_tab.setMenu(menu_tab)
        self.addWidget(self.btn_tab)

        self.addSeparator()

        # ── 6. Código: Inline e Terminal Bash ──
        self.btn_code_inline = QToolButton(self)
        self.btn_code_inline.setText("`code`")
        self.btn_code_inline.setToolTip("Código Inline (`comando`)")
        self.btn_code_inline.setStyleSheet("font-family: monospace; color: #059669;")
        self.btn_code_inline.clicked.connect(lambda: self._wrap_active("`", "`", "comando"))
        self.addWidget(self.btn_code_inline)

        self.btn_bash = QToolButton(self)
        self.btn_bash.setText("Bash")
        self.btn_bash.setToolTip("Inserir Bloco de Código Terminal Bash (```bash ... ```)")
        self.btn_bash.setStyleSheet("font-family: monospace; font-weight: bold; color: #0F172A;")
        self.btn_bash.clicked.connect(lambda: self._insert_code_block("bash"))
        self.addWidget(self.btn_bash)

        self.addSeparator()

        # ── 7. Listas e Citações ──
        act_bullet = self.addAction("•≡")
        act_bullet.setToolTip("Lista com Marcadores (- item)")
        act_bullet.triggered.connect(lambda: self._format_list("bullet"))

        # Lista Numerada 1≡ com menu para 1. e 1)
        self.btn_numbered = QToolButton(self)
        self.btn_numbered.setText("1≡")
        self.btn_numbered.setToolTip("Lista Numerada (1. item / 1) item)")
        self.btn_numbered.clicked.connect(lambda: self._format_list("numbered"))
        menu_num = QMenu(self)
        menu_num.addAction("Numeração com ponto (1. item)").triggered.connect(lambda: self._format_list("numbered"))
        menu_num.addAction("Numeração com parêntese (1) item)").triggered.connect(lambda: self._format_list("numbered_paren"))
        self.btn_numbered.setMenu(menu_num)
        self.btn_numbered.setPopupMode(QToolButton.MenuButtonPopup)
        self.addWidget(self.btn_numbered)

        # Marcador Alfabético / Alíneas a≡ (a. item, b. item)
        self.btn_alpha = QToolButton(self)
        self.btn_alpha.setText("a≡")
        self.btn_alpha.setToolTip("Lista Alfabética / Alíneas (a. item, b. item)")
        self.btn_alpha.setStyleSheet("font-weight: bold; color: #4338CA;")
        self.btn_alpha.clicked.connect(lambda: self._format_list("alpha"))
        menu_alpha = QMenu(self)
        menu_alpha.addAction("Alíneas com ponto (a. item)").triggered.connect(lambda: self._format_list("alpha"))
        menu_alpha.addAction("Alíneas com parêntese (a) item)").triggered.connect(lambda: self._format_list("alpha_paren"))
        self.btn_alpha.setMenu(menu_alpha)
        self.btn_alpha.setPopupMode(QToolButton.MenuButtonPopup)
        self.addWidget(self.btn_alpha)

        act_quote = self.addAction("❝ Citação")
        act_quote.setToolTip("Citação Longa ABNT (> 3 linhas, recuo 4cm)")
        act_quote.triggered.connect(self._insert_citation)

        self.addSeparator()

        # ── 8. Tabelas, Links, Figuras e Fórmulas ──
        act_table = self.addAction("⊞ Tabela")
        act_table.setToolTip("Inserir Modelo de Tabela Markdown Formatada")
        act_table.triggered.connect(self._insert_table)

        act_link = self.addAction("🔗 Link")
        act_link.setToolTip("Inserir Link ([texto](url))")
        act_link.triggered.connect(self._insert_link)

        btn_fig = QToolButton(self)
        btn_fig.setText("🖼️ Imagem")
        btn_fig.setToolTip("Inserir ou Importar Imagem com Legenda e Fonte ABNT")
        btn_fig.setPopupMode(QToolButton.MenuButtonPopup)

        fig_menu = QMenu(btn_fig)
        act_import_fig = fig_menu.addAction("📤  Escolher Imagem do Computador...")
        act_import_fig.triggered.connect(self._import_or_insert_figure)
        act_template_fig = fig_menu.addAction("📋  Inserir Modelo Genérico ABNT")
        act_template_fig.triggered.connect(self._insert_figure)

        btn_fig.setMenu(fig_menu)
        btn_fig.clicked.connect(self._import_or_insert_figure)
        self.addWidget(btn_fig)

        act_math = self.addAction(r"$\Sigma$")
        act_math.setToolTip("Inserir Equação Matemática LaTeX ($x=...$)")
        act_math.triggered.connect(self._insert_math)

        act_cite = self.addAction("[@]")
        act_cite.setToolTip("Inserir Citação Bibliográfica BibTeX ([@chave])")
        act_cite.triggered.connect(self._insert_bib)

    # ── HANDLERS INTERNOS ──

    def _call_editor(self, method_name: str, *args, **kwargs):
        """Executa um método no editor ativo se estiver disponível."""
        ed = self.get_editor()
        if ed and hasattr(ed, method_name):
            func = getattr(ed, method_name)
            if callable(func):
                func(*args, **kwargs)
                ed.setFocus()

    def _wrap_active(self, prefix: str, suffix: str, default_text: str = ""):
        ed = self.get_editor()
        if ed:
            ed.wrap_selection(prefix, suffix, default_text)
            ed.setFocus()

    def _apply_bold(self):
        """Aplica negrito na seleção atual."""
        self._wrap_active("**", "**", "texto")

    def _on_heading_changed(self, index: int):
        """Aplica o nível de cabeçalho selecionado."""
        ed = self.get_editor()
        if ed:
            ed.set_heading_level(index)
            ed.setFocus()

    def _toggle_unnumbered(self):
        ed = self.get_editor()
        if ed:
            ed.toggle_unnumbered()
            ed.setFocus()

    def _insert_line_break(self):
        ed = self.get_editor()
        if ed:
            ed.insert_line_break()
            ed.setFocus()

    def _insert_page_break(self):
        ed = self.get_editor()
        if ed:
            ed.insert_page_break()
            ed.setFocus()

    def _insert_space(self, space_type: str = "nbsp"):
        ed = self.get_editor()
        if ed and hasattr(ed, "insert_space"):
            ed.insert_space(space_type)
            ed.setFocus()

    def _insert_tab(self):
        ed = self.get_editor()
        if ed and hasattr(ed, "insert_tab"):
            ed.insert_tab()
            ed.setFocus()

    def _unindent(self):
        ed = self.get_editor()
        if ed and hasattr(ed, "unindent"):
            ed.unindent()
            ed.setFocus()

    def _format_list(self, list_type: str = "bullet", numbered: bool = None):
        ed = self.get_editor()
        if ed:
            ed.format_list(list_type=list_type, numbered=numbered)
            ed.setFocus()

    def _insert_code_block(self, lang: str = "bash"):
        ed = self.get_editor()
        if ed:
            ed.insert_code_block(lang)
            ed.setFocus()

    def _insert_citation(self):
        ed = self.get_editor()
        if ed:
            ed.insert_citation_block()
            ed.setFocus()

    def _insert_table(self):
        ed = self.get_editor()
        if ed:
            ed.insert_table_template(rows=3, cols=3)
            ed.setFocus()

    def _insert_link(self):
        ed = self.get_editor()
        if ed:
            ed.insert_link_template()
            ed.setFocus()

    def _import_or_insert_figure(self):
        if callable(self.image_importer):
            self.image_importer()
        else:
            self._insert_figure()

    def _insert_figure(self):
        ed = self.get_editor()
        if ed:
            ed.insert_figure_template()
            ed.setFocus()

    def _insert_math(self):
        ed = self.get_editor()
        if ed:
            ed.insert_math_formula(block=False)
            ed.setFocus()

    def _insert_bib(self):
        ed = self.get_editor()
        if ed:
            ed.insert_bib_citation_template()
            ed.setFocus()
