import logging
import os
import shutil
from datetime import datetime
from PyQt5.QtCore import QSettings, QTimer, Qt
from PyQt5.QtGui import QFont, QIcon, QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QCheckBox,
    QFileDialog,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QShortcut,
    QSplitter,
    QStatusBar,
    QStyle,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.ai_assistant import AIAssistantWidget, AISettingsDialog
from app.compiler import PDFCompilerThread
from app.editor import MarkdownEditor
from app.file_tree import ProjectFileTree
from app.formatting_toolbar import FormattingToolbar
from app.package_manager import (
    PACKAGE_EXTENSIONS,
    create_new_package,
    is_package_file,
    pack_project,
    sync_workspace_to_package,
    unpack_package,
)
from app.pdf_viewer import DetachedPDFWindow, PDFViewer


class MainWindow(QMainWindow):
    """
    Janela Principal do LatexMDown / MK Writer.
    Organiza o layout horizontal em QSplitter flexível (Árvore de Arquivos, Editor, Assistente IA, Visualizador PDF),
    com suporte a pacotes de arquivo único (.mkw), compilação ABNT em tempo real e destacamento de PDF.
    """
    def __init__(self, external_info=None, initial_path=None):
        super().__init__()
        self.external_info = external_info or {}
        self.current_file_path = None
        self.current_package_path = None
        self.compiler_thread = None
        self.is_compiling = False
        self.pending_recompile = False
        self.detached_pdf_window = None
        self.last_compiled_pdf_path = None
        self.formatting_toolbar = None

        self.setWindowTitle("MK Writer - Editor & Compilador Acadêmico Markdown")
        self.resize(1480, 880)

        # Configura armazenamento persistente de configurações e projetos recentes
        self.settings = QSettings("MKWriter", "LatexMDown")
        self.auto_save_enabled = self.settings.value("auto_save_enabled", True, type=bool)
        self._last_active_editor = None

        # Timer para salvamento automático inteligente após digitação
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setSingleShot(True)
        self.auto_save_timer.setInterval(1500)
        self.auto_save_timer.timeout.connect(self.auto_save_current_file)

        # Determina o projeto ou pacote inicial
        pkg_to_open = None
        folder_to_open = None
        file_to_open = None

        if initial_path:
            abs_init = os.path.abspath(initial_path)
            if is_package_file(abs_init):
                pkg_to_open = abs_init
            elif os.path.isdir(abs_init):
                folder_to_open = abs_init
            elif os.path.isfile(abs_init):
                file_to_open = abs_init
                folder_to_open = os.path.dirname(abs_init)

        if not pkg_to_open and not folder_to_open:
            recents = self.get_recent_projects()
            if recents and os.path.exists(recents[0]):
                if is_package_file(recents[0]):
                    pkg_to_open = recents[0]
                elif os.path.isdir(recents[0]):
                    folder_to_open = recents[0]

        if not pkg_to_open and not folder_to_open:
            default_root = os.path.abspath("Documentos/COLÓQUIO SEMINÁRIO I")
            if not os.path.exists(default_root):
                default_root = os.path.abspath("Documentos")
            if not os.path.exists(default_root):
                default_root = os.path.abspath(os.getcwd())
            folder_to_open = default_root

        self.project_root_dir = folder_to_open if folder_to_open else os.path.abspath(os.getcwd())
        if folder_to_open:
            self.add_recent_project(folder_to_open)

        # Configura Interface
        self.init_ui()
        self.init_menu_bar()
        self.init_toolbar()
        self.init_shortcuts()
        self.init_debounce_timer()

        # Abre o pacote inicial ou arquivos da pasta
        if pkg_to_open:
            self.open_package(pkg_to_open)
        elif file_to_open:
            self.load_file_to_editor(file_to_open)
        else:
            # Tenta carregar o arquivo main.md, Modelo_IFF.md ou template.md
            candidates = [
                os.path.join(self.project_root_dir, "main.md"),
                os.path.join(self.project_root_dir, "template.md"),
                os.path.join(self.project_root_dir, "resources", "template.md"),
                os.path.abspath("main.md"),
                os.path.abspath("template.md"),
            ]
            found = None
            for cand in candidates:
                if os.path.exists(cand):
                    found = cand
                    break

            if found:
                self.load_file_to_editor(found)
            else:
                if self.editor_tabs.count() == 0:
                    self.new_untitled_tab("# Novo Documento Markdown\n\nComece a digitar...")

    def get_current_editor(self):
        """Retorna o editor Markdown ativo na aba selecionada no momento."""
        if hasattr(self, "editor_tabs"):
            curr = self.editor_tabs.currentWidget()
            if isinstance(curr, MarkdownEditor):
                return curr
        return None

    @property
    def editor(self):
        """Propriedade que aponta dinamicamente para o editor da aba ativa."""
        return self.get_current_editor()

    @property
    def auto_compile_checkbox(self):
        """Compatibilidade para componentes ou testes que acessam auto_compile_checkbox."""
        return getattr(self, "act_auto_compile", None)

    def init_ui(self):
        """Inicializa a interface com barra lateral esquerda vertical (árvore + IA), editor em abas e PDF."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # QSplitter horizontal principal
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setChildrenCollapsible(False)

        # ── Barra Lateral Esquerda: Divisor Vertical (Árvore de Arquivos em cima, IA em baixo) ──
        self.left_splitter = QSplitter(Qt.Vertical)
        self.left_splitter.setChildrenCollapsible(False)

        # Painel Superior: Árvore de Arquivos
        self.file_tree = ProjectFileTree(root_path=self.project_root_dir, parent=self)
        self.file_tree.file_selected.connect(self.open_file_from_tree)
        self.file_tree.root_changed.connect(self.on_project_root_changed)
        self.file_tree.item_renamed.connect(self.on_item_renamed)
        self.file_tree.images_imported.connect(self.on_images_imported)

        # Painel Inferior: Assistente de Escrita e Edição com IA (Compacto)
        self.ai_assistant = AIAssistantWidget(editor_ref=lambda: self.editor, parent=self)
        self.ai_assistant.apply_action.connect(self.apply_ai_action_to_editor)
        self.ai_assistant.setVisible(True)

        self.left_splitter.addWidget(self.file_tree)
        self.left_splitter.addWidget(self.ai_assistant)
        self.left_splitter.setSizes([380, 420])

        # ── Painel Central: Editor Markdown Multi-Abas ──
        self.editor_tabs = QTabWidget(self)
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.setMovable(True)
        self.editor_tabs.setDocumentMode(True)
        self.editor_tabs.tabCloseRequested.connect(self.close_tab)
        self.editor_tabs.currentChanged.connect(self.on_tab_changed)

        # Menu de contexto com botão direito na barra de abas
        self.editor_tabs.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.editor_tabs.tabBar().customContextMenuRequested.connect(self.on_tab_context_menu)

        # ── Painel Direito: Visualizador de PDF ──
        self.pdf_viewer = PDFViewer(self)
        self.pdf_viewer.detach_requested.connect(self.detach_pdf_viewer)
        self.pdf_viewer.reattach_requested.connect(self.reattach_pdf_viewer)
        self.pdf_viewer.save_requested.connect(self.export_pdf_dialog)

        # Placeholder exibido quando o PDF for destacado para outra janela
        self.pdf_placeholder = QWidget(self)
        placeholder_layout = QVBoxLayout(self.pdf_placeholder)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        
        lbl_ph = QLabel("↗️ O visualizador de PDF está aberto em uma janela separada (2º Monitor).", self)
        lbl_ph.setStyleSheet("color: #64748B; font-weight: bold; font-size: 11pt;")
        lbl_ph.setAlignment(Qt.AlignCenter)
        
        btn_ph_reattach = QPushButton("🔗 Acoplar PDF de Volta à Janela Principal", self)
        btn_ph_reattach.setCursor(Qt.PointingHandCursor)
        btn_ph_reattach.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
        """)
        btn_ph_reattach.clicked.connect(self.reattach_pdf_viewer)
        
        placeholder_layout.addWidget(lbl_ph)
        placeholder_layout.addSpacing(12)
        placeholder_layout.addWidget(btn_ph_reattach, 0, Qt.AlignCenter)
        self.pdf_placeholder.setVisible(False)

        # Monta splitter principal: Esquerda (Árvore+IA), Centro (Abas), Direita (PDF)
        self.splitter.addWidget(self.left_splitter)
        self.splitter.addWidget(self.editor_tabs)
        self.splitter.addWidget(self.pdf_viewer)
        self.splitter.addWidget(self.pdf_placeholder)

        self.splitter.setSizes([260, 580, 560, 0])

        main_layout.addWidget(self.splitter)

        # Barra de Status inferior
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Pronto", self)
        self.status_bar.addWidget(self.status_label, 1)

        self.setStyleSheet("""
            QMainWindow { background-color: #F8FAFC; }
            QMenuBar {
                background-color: #1E293B;
                color: #CBD5E1;
                font-size: 10pt;
                padding: 2px 0;
                border-bottom: 2px solid #334155;
            }
            QMenuBar::item {
                padding: 6px 14px;
                border-radius: 4px;
                margin: 2px 1px;
            }
            QMenuBar::item:selected { background-color: #334155; color: #F1F5F9; }
            QMenuBar::item:pressed  { background-color: #3B82F6; color: white; }
            QMenu {
                background-color: #1E293B;
                color: #E2E8F0;
                border: 1px solid #475569;
                padding: 4px 0;
                font-size: 9.5pt;
            }
            QMenu::item { padding: 7px 30px 7px 20px; }
            QMenu::item:selected { background-color: #3B82F6; color: white; }
            QMenu::separator { height: 1px; background: #475569; margin: 4px 10px; }
            QToolBar {
                background-color: #F1F5F9;
                border-bottom: 1px solid #E2E8F0;
                spacing: 6px;
                padding: 4px 10px;
            }
            QToolButton {
                background-color: transparent;
                color: #334155;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: 500;
                font-size: 9pt;
            }
            QToolButton:hover { background-color: #E2E8F0; color: #0F172A; }
            QToolButton:pressed { background-color: #CBD5E1; }
            QCheckBox {
                font-weight: 500; color: #334155;
                spacing: 6px; padding: 4px 8px; font-size: 9pt;
            }
            QTabWidget::pane {
                border: 1px solid #CBD5E1;
                background-color: #FFFFFF;
                border-top: none;
            }
            QTabBar::tab {
                background-color: #E2E8F0;
                color: #475569;
                font-weight: 500;
                font-size: 9pt;
                padding: 6px 14px;
                border: 1px solid #CBD5E1;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #1E293B;
                font-weight: bold;
                border-top: 2px solid #2563EB;
            }
            QTabBar::tab:hover:!selected {
                background-color: #F1F5F9;
                color: #0F172A;
            }
            QTabBar::close-button {
                subcontrol-position: right;
                margin-left: 4px;
            }
            QStatusBar {
                background-color: #1E293B; color: #94A3B8;
                border-top: 1px solid #334155; font-size: 9pt; padding: 2px 8px;
            }
            QSplitter::handle { background-color: #CBD5E1; width: 4px; }
            QSplitter::handle:hover { background-color: #3B82F6; }
        """)

    def init_menu_bar(self):
        """Cria a barra de menus principal com dropdowns organizados."""
        menu_bar = self.menuBar()

        # ── Menu Arquivo ──
        file_menu = menu_bar.addMenu("Arquivo")

        act_new_pkg = file_menu.addAction("📦  Novo Pacote (.mkw)...")
        act_new_pkg.setShortcut("Ctrl+Shift+P")
        act_new_pkg.triggered.connect(self.create_new_package_dialog)

        act_open_pkg = file_menu.addAction("📦  Abrir Pacote (.mkw)...")
        act_open_pkg.setShortcut("Ctrl+Alt+O")
        act_open_pkg.triggered.connect(self.open_package_dialog)

        act_open_folder = file_menu.addAction("📁  Abrir Pasta do Projeto...")
        act_open_folder.triggered.connect(self.select_project_folder)

        # Submenu de Projetos Recentes
        self.recent_menu = file_menu.addMenu("🕒  Projetos Recentes")
        self.update_recent_projects_menu()

        file_menu.addSeparator()

        act_save = file_menu.addAction("💾  Salvar")
        act_save.setShortcut("Ctrl+S")
        act_save.triggered.connect(self.save_file)

        act_save_all = file_menu.addAction("💾  Salvar Todas as Abas")
        act_save_all.setShortcut("Ctrl+Shift+S")
        act_save_all.triggered.connect(self.save_all_files)

        act_save_as = file_menu.addAction("💾  Salvar Arquivo Como...")
        act_save_as.setShortcut("Ctrl+Alt+S")
        act_save_as.triggered.connect(self.save_file_as)

        act_save_as_pkg = file_menu.addAction("📦  Salvar Como Pacote (.mkw)...")
        act_save_as_pkg.triggered.connect(self.save_as_package_dialog)

        act_pack_folder = file_menu.addAction("📦  Empacotar Pasta Atual em (.mkw)...")
        act_pack_folder.triggered.connect(self.export_current_folder_as_package)

        file_menu.addSeparator()

        act_new_file = file_menu.addAction("📄  Novo Arquivo na Pasta...")
        act_new_file.setShortcut("Ctrl+N")
        act_new_file.triggered.connect(lambda: self.file_tree.create_new_file())

        act_new_folder = file_menu.addAction("📁  Nova Pasta...")
        act_new_folder.setShortcut("Ctrl+Shift+N")
        act_new_folder.triggered.connect(lambda: self.file_tree.create_new_folder())

        act_import_img = file_menu.addAction("🖼️  Importar Imagens para o Projeto...")
        act_import_img.setShortcut("Ctrl+Shift+I")
        act_import_img.triggered.connect(self.import_images_dialog)

        act_open_sys_folder = file_menu.addAction("📂  Abrir Pasta do Projeto no Gerenciador...")
        act_open_sys_folder.triggered.connect(self.open_project_in_system_explorer)

        act_open = file_menu.addAction("📂  Abrir Arquivo Avulso...")
        act_open.setShortcut("Ctrl+O")
        act_open.triggered.connect(self.open_file_dialog)

        file_menu.addSeparator()

        act_rename = file_menu.addAction("✏️  Renomear Item...")
        act_rename.setShortcut("F2")
        act_rename.triggered.connect(lambda: self.file_tree.rename_selected_item())

        act_delete = file_menu.addAction("🗑️  Excluir Item Selecionado")
        act_delete.setShortcut("Delete")
        act_delete.triggered.connect(lambda: self.file_tree.delete_selected_item())

        file_menu.addSeparator()

        act_export = file_menu.addAction("📥  Exportar PDF")
        act_export.setShortcut("Ctrl+E")
        act_export.triggered.connect(self.export_pdf_dialog)

        file_menu.addSeparator()

        act_quit = file_menu.addAction("❌  Sair")
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.quit_app)

        # ── Menu Editar ──
        edit_menu = menu_bar.addMenu("Editar")

        act_undo = edit_menu.addAction("↩️  Desfazer")
        act_undo.setShortcut("Ctrl+Z")
        act_undo.triggered.connect(lambda: self.editor.undo() if self.editor else None)

        act_redo = edit_menu.addAction("↪️  Refazer")
        act_redo.setShortcut("Ctrl+Y")
        act_redo.triggered.connect(lambda: self.editor.redo() if self.editor else None)

        edit_menu.addSeparator()

        act_cut = edit_menu.addAction("✂️  Recortar")
        act_cut.setShortcut("Ctrl+X")
        act_cut.triggered.connect(lambda: self.editor.cut() if self.editor else None)

        act_copy = edit_menu.addAction("📋  Copiar")
        act_copy.setShortcut("Ctrl+C")
        act_copy.triggered.connect(lambda: self.editor.copy() if self.editor else None)

        act_paste = edit_menu.addAction("📋  Colar")
        act_paste.setShortcut("Ctrl+V")
        act_paste.triggered.connect(lambda: self.editor.paste() if self.editor else None)

        edit_menu.addSeparator()

        act_tab = edit_menu.addAction("⇥  Inserir Tabulação / Indentar")
        act_tab.setShortcut("Tab")
        act_tab.triggered.connect(lambda: self.editor.insert_tab() if self.editor else None)

        act_unindent = edit_menu.addAction("⇤  Desindentar Seleção")
        act_unindent.setShortcut("Shift+Tab")
        act_unindent.triggered.connect(lambda: self.editor.unindent() if self.editor else None)

        act_space = edit_menu.addAction("␣  Inserir Espaço Fixo (&nbsp;)")
        act_space.setShortcut("Ctrl+Space")
        act_space.triggered.connect(lambda: self.editor.insert_space("nbsp") if self.editor else None)

        edit_menu.addSeparator()

        act_insert_img = edit_menu.addAction("🖼️  Inserir Imagem do Computador...")
        act_insert_img.setShortcut("Ctrl+Alt+I")
        act_insert_img.triggered.connect(self.import_and_insert_image)

        # ── Menu Visualização ──
        view_menu = menu_bar.addMenu("Visualização")

        act_tree = view_menu.addAction("🌲  Árvore de Arquivos")
        act_tree.setShortcut("Ctrl+B")
        act_tree.triggered.connect(self.toggle_file_tree)

        act_ai = view_menu.addAction("✨  Assistente IA")
        act_ai.setShortcut("Ctrl+I")
        act_ai.triggered.connect(self.toggle_ai_assistant)

        view_menu.addSeparator()

        self.act_formatting_toolbar = view_menu.addAction("🔤  Barra de Formatação")
        self.act_formatting_toolbar.setCheckable(True)
        self.act_formatting_toolbar.setChecked(True)
        self.act_formatting_toolbar.toggled.connect(
            lambda c: self.formatting_toolbar.setVisible(c) if getattr(self, "formatting_toolbar", None) else None
        )

        view_menu.addSeparator()

        self.detach_pdf_action = view_menu.addAction("↗️  Destacar PDF (2º Monitor)")
        self.detach_pdf_action.setShortcut("Ctrl+D")
        self.detach_pdf_action.triggered.connect(self.toggle_detach_pdf)

        # ── Menu Compilação ──
        compile_menu = menu_bar.addMenu("Compilação")

        act_compile = compile_menu.addAction("⚡  Compilar Agora")
        act_compile.setShortcut("Ctrl+R")
        act_compile.triggered.connect(self.trigger_compilation)

        # ── Menu Configurações ──
        settings_menu = menu_bar.addMenu("Configurações")

        act_ai_settings = settings_menu.addAction("⚙️  Configurações de IA & Chaves de API...")
        act_ai_settings.triggered.connect(self.open_ai_settings_dialog)

        settings_menu.addSeparator()

        self.act_auto_save = settings_menu.addAction("💾  Salvamento Automático (Auto-Save)")
        self.act_auto_save.setCheckable(True)
        self.act_auto_save.setChecked(self.auto_save_enabled)
        self.act_auto_save.toggled.connect(self.toggle_auto_save)

        settings_menu.addSeparator()

        self.act_auto_compile = settings_menu.addAction("⚡  Compilação Automática (1.5s)")
        self.act_auto_compile.setCheckable(True)
        self.act_auto_compile.setChecked(True)

        # ── Menu Ajuda ──
        help_menu = menu_bar.addMenu("Ajuda")
        act_about = help_menu.addAction("ℹ️  Sobre o MK Writer")
        act_about.triggered.connect(self.show_about)

        act_shortcuts = help_menu.addAction("⌨️  Atalhos de Teclado")
        act_shortcuts.triggered.connect(self.show_shortcuts_help)

    def init_toolbar(self):
        """Toolbar com as ações mais usadas e atalhos rápidos para pacotes."""
        toolbar = QToolBar("Ações Rápidas", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        act_new_pkg = QAction("📦 Novo Pacote", self)
        act_new_pkg.setToolTip("Criar Novo Pacote MK Writer (.mkw) [Ctrl+Shift+P]")
        act_new_pkg.triggered.connect(self.create_new_package_dialog)
        toolbar.addAction(act_new_pkg)

        act_open_pkg = QAction("📂 Abrir Pacote", self)
        act_open_pkg.setToolTip("Abrir Pacote (.mkw / .mkdoc) [Ctrl+Alt+O]")
        act_open_pkg.triggered.connect(self.open_package_dialog)
        toolbar.addAction(act_open_pkg)

        toolbar.addSeparator()

        act_save = QAction("💾 Salvar", self)
        act_save.setToolTip("Salvar (Ctrl+S)")
        act_save.triggered.connect(self.save_file)
        toolbar.addAction(act_save)

        toolbar.addSeparator()

        act_compile = QAction("⚡ Compilar", self)
        act_compile.setToolTip("Compilar PDF (Ctrl+R / F5)")
        act_compile.triggered.connect(self.trigger_compilation)
        toolbar.addAction(act_compile)

        act_export = QAction("📥 Exportar PDF", self)
        act_export.setToolTip("Exportar PDF (Ctrl+E)")
        act_export.triggered.connect(self.export_pdf_dialog)
        toolbar.addAction(act_export)

        # ── Linha 2: Barra de Ferramentas de Formatação e Escrita ──
        self.addToolBarBreak()
        self.formatting_toolbar = FormattingToolbar(
            editor_provider=lambda: self.editor,
            image_importer=self.import_and_insert_image,
            parent=self
        )
        self.addToolBar(self.formatting_toolbar)
        self.formatting_toolbar.visibilityChanged.connect(self.act_formatting_toolbar.setChecked)


    def init_shortcuts(self):
        """Configura os atalhos de teclado adicionais (F5 para compilar, Ctrl+U para sublinhado)."""
        shortcut_f5 = QShortcut(QKeySequence("F5"), self)
        shortcut_f5.activated.connect(self.trigger_compilation)

        shortcut_u = QShortcut(QKeySequence("Ctrl+U"), self)
        shortcut_u.activated.connect(lambda: self.editor.wrap_selection("<u>", "</u>", "texto") if self.editor else None)

    def init_debounce_timer(self):
        """Configura o timer de debounce de 1.5s para compilação automática."""
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.setInterval(1500)
        self.debounce_timer.timeout.connect(self.on_debounce_timeout)

    def _update_left_sidebar_visibility(self):
        """Atualiza a visibilidade do splitter lateral esquerdo se ambos estiverem ocultos."""
        tree_vis = self.file_tree.isVisible()
        ai_vis = self.ai_assistant.isVisible()
        self.left_splitter.setVisible(tree_vis or ai_vis)

    def toggle_file_tree(self):
        """Exibe ou oculta a árvore de arquivos na barra lateral esquerda."""
        self.file_tree.setVisible(not self.file_tree.isVisible())
        self._update_left_sidebar_visibility()

    def toggle_ai_assistant(self):
        """Exibe ou oculta o painel do assistente de IA na barra lateral esquerda."""
        self.ai_assistant.setVisible(not self.ai_assistant.isVisible())
        self._update_left_sidebar_visibility()

    def open_ai_settings_dialog(self):
        """Abre o diálogo de configurações da API e modelos de IA."""
        dlg = AISettingsDialog(self)
        dlg.exec_()

    def toggle_auto_save(self, enabled: bool):
        """Ativa ou desativa o salvamento automático contínuo."""
        self.auto_save_enabled = enabled
        self.settings.setValue("auto_save_enabled", enabled)
        state = "ativado" if enabled else "desativado"
        self.status_label.setText(f"Salvamento automático {state}.")

    def auto_save_current_file(self):
        """Chamado pelo timer após inatividade de digitação para salvar o arquivo em segundo plano."""
        if not self.auto_save_enabled:
            return
        ed = self.editor
        if ed and getattr(ed, "file_path", None) and ed.document().isModified():
            self.save_editor_file(ed)

    def toggle_detach_pdf(self):
        """Alterna entre destacar o PDF para outra janela e acoplá-lo de volta."""
        if self.detached_pdf_window and self.detached_pdf_window.isVisible():
            self.reattach_pdf_viewer()
        else:
            self.detach_pdf_viewer()

    def detach_pdf_viewer(self):
        """Move o widget visualizador de PDF para uma nova janela flutuante independente."""
        if self.detached_pdf_window is not None:
            return

        self.detached_pdf_window = DetachedPDFWindow(self)
        self.detached_pdf_window.closed_signal.connect(self.reattach_pdf_viewer)

        # Substitui no splitter: oculta pdf_viewer no splitter e mostra placeholder
        self.pdf_viewer.setParent(None)
        self.detached_pdf_window.setCentralWidget(self.pdf_viewer)

        self.pdf_placeholder.setVisible(True)
        self.pdf_viewer.set_detached_state(True)
        self.detach_pdf_action.setText("🔗 Acoplar PDF")

        self.detached_pdf_window.show()
        self.status_label.setText("↗️ Visualizador de PDF destacado para janela separada.")

    def reattach_pdf_viewer(self):
        """Retorna o visualizador de PDF para dentro do QSplitter da janela principal."""
        if self.detached_pdf_window is None and not self.pdf_placeholder.isVisible():
            return

        # Fecha a janela destacada sem gerar loop no sinal de fechamento
        if self.detached_pdf_window:
            window_to_close = self.detached_pdf_window
            self.detached_pdf_window = None
            window_to_close.close()

        # Reinsere o pdf_viewer no QSplitter no lugar do placeholder
        self.pdf_viewer.setParent(self)
        
        # Oculta placeholder
        self.pdf_placeholder.setVisible(False)
        
        # Re-adiciona pdf_viewer ao splitter se necessário
        index = self.splitter.indexOf(self.pdf_placeholder)
        if index != -1:
            self.splitter.insertWidget(index, self.pdf_viewer)

        self.pdf_viewer.setVisible(True)
        self.pdf_viewer.set_detached_state(False)
        self.detach_pdf_action.setText("↗️ Destacar PDF (2º Monitor)")
        self.status_label.setText("🔗 Visualizador de PDF acoplado de volta à janela principal.")

    def get_recent_projects(self) -> list:
        """Retorna lista de caminhos de projetos recentes salvos (pastas ou pacotes .mkw / .mkdoc)."""
        raw = self.settings.value("recent_projects", [])
        if not isinstance(raw, list):
            raw = []
        valid = []
        for p in raw:
            if not p or not isinstance(p, str):
                continue
            abs_p = os.path.abspath(p)
            if os.path.isdir(abs_p) or (os.path.isfile(abs_p) and is_package_file(abs_p)):
                valid.append(abs_p)
        return valid

    def add_recent_project(self, target_path: str):
        """Adiciona um projeto (pasta ou arquivo .mkw) recente ao topo da lista persistente."""
        if not target_path or not isinstance(target_path, str):
            return
        abs_path = os.path.abspath(target_path)
        if not (os.path.isdir(abs_path) or (os.path.isfile(abs_path) and is_package_file(abs_path))):
            return

        recents = self.get_recent_projects()
        if abs_path in recents:
            recents.remove(abs_path)
        recents.insert(0, abs_path)
        recents = recents[:10]  # Limite de até 10 projetos recentes

        self.settings.setValue("recent_projects", recents)
        self.update_recent_projects_menu()

    def clear_recent_projects(self):
        """Limpa o histórico de projetos recentes."""
        self.settings.setValue("recent_projects", [])
        self.update_recent_projects_menu()
        self.status_label.setText("Histórico de projetos recentes limpo.")

    def update_recent_projects_menu(self):
        """Reconstrói dinamicamente os itens do submenu 'Projetos Recentes' com suporte a pacotes 📦 e pastas 📁."""
        if not hasattr(self, "recent_menu") or self.recent_menu is None:
            return

        self.recent_menu.clear()
        recents = self.get_recent_projects()

        if not recents:
            act_empty = self.recent_menu.addAction("(Nenhum projeto recente)")
            act_empty.setEnabled(False)
            return

        for path in recents:
            base_name = os.path.basename(path) or path
            if is_package_file(path):
                act = self.recent_menu.addAction(f"📦  {base_name}")
                act.triggered.connect(lambda checked, p=path: self.open_package(p))
            else:
                act = self.recent_menu.addAction(f"📁  {base_name}")
                act.triggered.connect(lambda checked, p=path: self.open_project_folder(p))
            act.setToolTip(path)
            act.setStatusTip(path)

        self.recent_menu.addSeparator()
        act_clear = self.recent_menu.addAction("🗑️  Limpar Projetos Recentes")
        act_clear.triggered.connect(self.clear_recent_projects)

    def open_package(self, package_path: str) -> bool:
        """Abre um pacote .mkw / .mkdoc, descompacta no workspace de cache e carrega no editor."""
        abs_pkg = os.path.abspath(package_path)
        if not is_package_file(abs_pkg):
            QMessageBox.critical(self, "Pacote Inválido", f"O arquivo selecionado não é um pacote MK Writer válido:\n{abs_pkg}")
            recents = self.get_recent_projects()
            if abs_pkg in recents:
                recents.remove(abs_pkg)
                self.settings.setValue("recent_projects", recents)
                self.update_recent_projects_menu()
            return False

        try:
            workspace_dir, metadata = unpack_package(abs_pkg)
            self.current_package_path = abs_pkg
            self.project_root_dir = workspace_dir
            pkg_name = os.path.basename(abs_pkg)

            self.file_tree.set_root_path(workspace_dir, display_name=f"📦 {pkg_name}")
            self.add_recent_project(abs_pkg)
            self.setWindowTitle(f"MK Writer - [Pacote] {pkg_name}")
            self.status_label.setText(f"✓ Pacote aberto: {pkg_name}")
            self.status_label.setStyleSheet("color: #166534; font-weight: bold;")

            # Procura o arquivo mestre indicado pelos metadados ou candidatos padrão
            main_entry = metadata.get("main", "main.md") if metadata else "main.md"
            entry_path = os.path.join(workspace_dir, main_entry)
            if not os.path.exists(entry_path):
                candidates = [
                    os.path.join(workspace_dir, "main.md"),
                                        os.path.join(workspace_dir, "template.md"),
                ]
                entry_path = None
                for cand in candidates:
                    if os.path.exists(cand):
                        entry_path = cand
                        break

            self.close_all_tabs(save_modified=True)
            if entry_path and os.path.exists(entry_path):
                self.open_file_in_tab(entry_path)
            else:
                self.new_untitled_tab("# Novo Documento Acadêmico\n\nComece a editar...")

            return True
        except Exception as e:
            logging.error(f"Erro ao abrir pacote {abs_pkg}: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro ao Abrir Pacote", f"Não foi possível descompactar o pacote:\n{str(e)}")
            return False

    def open_package_dialog(self):
        """Abre caixa de diálogo para seleção de arquivo de pacote .mkw ou .mkdoc."""
        filter_str = "Pacotes MK Writer (*.mkw *.mkdoc);;Todos os Arquivos (*)"
        start_dir = os.path.dirname(self.current_package_path) if self.current_package_path else self.project_root_dir
        pkg_path, _ = QFileDialog.getOpenFileName(self, "Abrir Pacote MK Writer", start_dir, filter_str)
        if pkg_path:
            self.open_package(pkg_path)

    def create_new_package_dialog(self):
        """Cria um novo pacote .mkw com o template padrão ABNT completo."""
        start_dir = os.path.dirname(self.current_package_path) if self.current_package_path else os.path.expanduser("~")
        default_target = os.path.join(start_dir, "Novo_Trabalho.mkw")
        pkg_path, _ = QFileDialog.getSaveFileName(
            self,
            "Criar Novo Pacote MK Writer",
            default_target,
            "Pacotes MK Writer (*.mkw);;Todos os Arquivos (*)"
        )
        if not pkg_path:
            return

        if not any(pkg_path.lower().endswith(ext) for ext in PACKAGE_EXTENSIONS):
            pkg_path += ".mkw"

        base_title = os.path.splitext(os.path.basename(pkg_path))[0].replace("_", " ").title()
        try:
            create_new_package(pkg_path, title=base_title, author="")
            self.status_label.setText(f"✓ Pacote criado: {os.path.basename(pkg_path)}")
            self.open_package(pkg_path)
            QMessageBox.information(
                self,
                "Pacote Criado com Sucesso",
                f"O novo pacote <b>{os.path.basename(pkg_path)}</b> foi criado com a estrutura padrão ABNT e aberto para edição!"
            )
        except Exception as e:
            logging.error(f"Erro ao criar novo pacote {pkg_path}: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro ao Criar Pacote", f"Não foi possível criar o pacote:\n{str(e)}")

    def save_as_package_dialog(self):
        """Salva o projeto atual como um novo pacote .mkw."""
        if self.current_file_path:
            self.save_file()

        start_dir = os.path.dirname(self.current_package_path) if self.current_package_path else os.path.expanduser("~")
        default_name = os.path.basename(self.current_package_path) if self.current_package_path else (os.path.basename(self.project_root_dir) + ".mkw")
        target_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Como Pacote MK Writer",
            os.path.join(start_dir, default_name),
            "Pacotes MK Writer (*.mkw);;Todos os Arquivos (*)"
        )
        if not target_path:
            return

        if not any(target_path.lower().endswith(ext) for ext in PACKAGE_EXTENSIONS):
            target_path += ".mkw"

        try:
            pack_project(self.project_root_dir, target_path)
            self.open_package(target_path)
            QMessageBox.information(
                self,
                "Pacote Salvo",
                f"Projeto salvo com sucesso como pacote único em:\n\n{target_path}"
            )
        except Exception as e:
            logging.error(f"Erro ao salvar pacote como {target_path}: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro ao Salvar Pacote", f"Falha ao empacotar projeto:\n{str(e)}")

    def export_current_folder_as_package(self):
        """Empacota a pasta do projeto atual em um arquivo .mkw."""
        if self.current_file_path:
            self.save_file()

        default_name = os.path.basename(self.project_root_dir.rstrip(os.sep)) + ".mkw"
        suggested_dir = os.path.dirname(self.project_root_dir)
        target_path, _ = QFileDialog.getSaveFileName(
            self,
            "Empacotar Pasta Atual em (.mkw)",
            os.path.join(suggested_dir, default_name),
            "Pacotes MK Writer (*.mkw);;Todos os Arquivos (*)"
        )
        if not target_path:
            return

        if not any(target_path.lower().endswith(ext) for ext in PACKAGE_EXTENSIONS):
            target_path += ".mkw"

        try:
            pack_project(self.project_root_dir, target_path)
            ans = QMessageBox.question(
                self,
                "Empacotamento Concluído",
                f"Pasta empacotada com sucesso em:\n{target_path}\n\nDeseja abrir o novo pacote para edição contínua agora?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if ans == QMessageBox.Yes:
                self.open_package(target_path)
        except Exception as e:
            logging.error(f"Erro ao empacotar pasta atual: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro ao Empacotar", f"Falha ao criar pacote:\n{str(e)}")

    def open_project_folder(self, folder_path: str):
        """Abre uma pasta de projeto na árvore e carrega seu documento principal."""
        abs_path = os.path.abspath(folder_path)
        if not os.path.isdir(abs_path):
            QMessageBox.warning(self, "Pasta Não Encontrada", f"A pasta selecionada não existe:\n{abs_path}")
            recents = self.get_recent_projects()
            if abs_path in recents:
                recents.remove(abs_path)
                self.settings.setValue("recent_projects", recents)
                self.update_recent_projects_menu()
            return

        self.current_package_path = None
        self.project_root_dir = abs_path
        self.file_tree.set_root_path(abs_path, display_name=f"📁 {os.path.basename(abs_path)}")
        self.add_recent_project(abs_path)
        self.setWindowTitle(f"MK Writer - {os.path.basename(abs_path)}")
        self.status_label.setText(f"Projeto aberto: {abs_path}")

        self.close_all_tabs(save_modified=True)
        # Tenta carregar automaticamente o arquivo principal do projeto aberto
        candidates = [
            os.path.join(abs_path, "main.md"),
                        os.path.join(abs_path, "template.md"),
        ]
        found = None
        for cand in candidates:
            if os.path.exists(cand):
                found = cand
                break

        if found:
            self.open_file_in_tab(found)
        else:
            self.new_untitled_tab("# Novo Documento Acadêmico\n\nComece a editar...")

    def select_project_folder(self):
        """Abre a seleção de pasta para alterar a raiz da árvore de arquivos."""
        folder_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta do Projeto", self.project_root_dir)
        if folder_path:
            self.open_project_folder(folder_path)

    def on_project_root_changed(self, new_path: str):
        """Callback acionado quando a pasta raiz da árvore é alterada."""
        self.project_root_dir = new_path
        self.add_recent_project(new_path)
        self.status_label.setText(f"Pasta raiz do projeto alterada para: {new_path}")

    def update_window_title(self):
        """Atualiza o título da janela principal de acordo com o arquivo da aba ativa e pacote."""
        doc_name = os.path.basename(self.current_file_path) if self.current_file_path else "Sem título"
        if self.current_package_path:
            pkg_name = os.path.basename(self.current_package_path)
            self.setWindowTitle(f"MK Writer - [Pacote] {pkg_name} ({doc_name})")
        elif self.project_root_dir:
            proj_name = os.path.basename(self.project_root_dir)
            self.setWindowTitle(f"MK Writer - {proj_name} ({doc_name})")
        else:
            self.setWindowTitle(f"MK Writer - {doc_name}")

    def on_item_renamed(self, old_path: str, new_path: str):
        """Atualiza referências do arquivo em todas as abas abertas quando ele ou sua pasta for renomeado."""
        old_abs = os.path.abspath(old_path)
        new_abs = os.path.abspath(new_path)

        for i in range(self.editor_tabs.count()):
            ed = self.editor_tabs.widget(i)
            if isinstance(ed, MarkdownEditor) and getattr(ed, "file_path", None):
                curr_abs = os.path.abspath(ed.file_path)
                if curr_abs == old_abs:
                    ed.file_path = new_abs
                    self.update_tab_title(ed)
                    self.editor_tabs.setTabToolTip(i, new_abs)
                elif curr_abs.startswith(old_abs + os.sep):
                    rel = os.path.relpath(curr_abs, old_abs)
                    ed.file_path = os.path.join(new_abs, rel)
                    self.update_tab_title(ed)
                    self.editor_tabs.setTabToolTip(i, ed.file_path)

        if self.current_file_path:
            curr_main_abs = os.path.abspath(self.current_file_path)
            if curr_main_abs == old_abs:
                self.current_file_path = new_abs
            elif curr_main_abs.startswith(old_abs + os.sep):
                rel = os.path.relpath(curr_main_abs, old_abs)
                self.current_file_path = os.path.join(new_abs, rel)

        self.update_window_title()
        self.status_label.setText(f"✓ Renomeado para: {os.path.basename(new_abs)}")
        self.trigger_compilation()

    def apply_ai_action_to_editor(self, text: str, mode: str):
        """Aplica as edições da IA diretamente no editor da aba ativa conforme a opção escolhida."""
        ed = self.editor
        if not ed:
            return

        cursor = ed.textCursor()
        if mode == "cursor":
            cursor.insertText(text + "\n")
        elif mode == "replace_selection":
            if cursor.hasSelection():
                cursor.insertText(text)
            else:
                cursor.insertText(text + "\n")
        elif mode == "replace_document":
            ed.setPlainText(text)
            ed.document().setModified(True)
            self.update_tab_title(ed)

        ed.setFocus()
        self.status_label.setText("✓ Alterações aplicadas no arquivo .md com sucesso!")

    def open_file_from_tree(self, file_path: str):
        """Carrega um arquivo selecionado na árvore de arquivos para o editor em abas."""
        if file_path.endswith((".md", ".markdown", ".txt", ".bib", ".json", ".yaml", ".yml", ".css", ".lua")):
            # Salva automaticamente a aba ativa atual se tiver alterações antes de abrir/trocar
            if self.editor and getattr(self.editor, "file_path", None) and self.editor.document().isModified():
                self.save_editor_file(self.editor)
            self.open_file_in_tab(file_path)

    def open_file_dialog(self):
        """Abre uma caixa de diálogo para carregar um arquivo avulso em nova aba."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Arquivo Markdown", self.project_root_dir, "Arquivos Markdown (*.md *.markdown);;Todos os Arquivos (*)"
        )
        if file_path:
            self.open_file_in_tab(file_path)

    def import_images_dialog(self):
        """Abre o seletor para importar imagens do computador para o projeto."""
        self.file_tree.import_images()

    def open_project_in_system_explorer(self):
        """Abre o diretório do projeto no gerenciador de arquivos padrão do sistema."""
        self.file_tree.open_in_system_explorer()

    def import_and_insert_image(self):
        """Abre diálogo para escolher uma imagem do computador, copia para Imagens/ do projeto e insere a tag no editor."""
        if not self.editor:
            QMessageBox.warning(self, "Aviso", "Nenhum documento aberto no editor para inserir a imagem.")
            return

        target_dir = os.path.join(self.project_root_dir, "Imagens")
        for candidate in ["Imagens", "imagens", "images", "img"]:
            candidate_path = os.path.join(self.project_root_dir, candidate)
            if os.path.isdir(candidate_path):
                target_dir = candidate_path
                break
        os.makedirs(target_dir, exist_ok=True)

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Imagem do Computador",
            "",
            "Imagens (*.png *.jpg *.jpeg *.svg *.webp *.bmp *.gif);;Todos os Arquivos (*)"
        )
        if not file_path:
            return

        filename = os.path.basename(file_path)
        dest_path = os.path.join(target_dir, filename)

        if os.path.abspath(file_path) != os.path.abspath(dest_path):
            try:
                shutil.copy2(file_path, dest_path)
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Copiar Imagem", f"Não foi possível copiar a imagem para o projeto:\n{e}")
                return

        # Sincroniza imediatamente o pacote se for .mkw
        if self.current_package_path and self.project_root_dir:
            try:
                sync_workspace_to_package(self.project_root_dir, self.current_package_path)
            except Exception as e:
                logging.warning(f"Erro ao sincronizar pacote após importar imagem: {e}")

        # Solicita legenda e fonte ABNT ao usuário
        default_leg = f"Figura — {os.path.splitext(filename)[0].replace('_', ' ').capitalize()}"
        legenda, ok_leg = QInputDialog.getText(
            self,
            "Legenda da Imagem",
            "Digite o título / legenda da figura (ABNT):",
            text=default_leg
        )
        if not ok_leg or not legenda.strip():
            legenda = "Figura"

        fonte, ok_fonte = QInputDialog.getText(
            self,
            "Fonte da Imagem",
            "Digite a fonte da figura (ABNT):",
            text="Elaborado pelos autores (2026)."
        )
        if not ok_fonte or not fonte.strip():
            fonte = "Elaborado pelos autores (2026)."

        # Caminho relativo em relação ao arquivo markdown sendo editado ou à raiz
        curr_file = getattr(self.editor, "file_path", None)
        if curr_file:
            rel_img = os.path.relpath(dest_path, os.path.dirname(curr_file))
        else:
            rel_img = os.path.relpath(dest_path, self.project_root_dir)

        # Insere no editor ativo
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()
        tag = (
            f"\n<div class=\"figura\">\n\n"
            f"**{legenda.strip()}**\n\n"
            f"![]({rel_img})\n\n"
            f"<small>Fonte: {fonte.strip()}</small>\n\n"
            f"</div>\n\n"
        )
        cursor.insertText(tag)
        cursor.endEditBlock()
        self.editor.setFocus()

    def on_images_imported(self, imported_paths: list):
        """Callback acionado quando imagens são importadas pela árvore de arquivos."""
        if self.current_package_path and self.project_root_dir:
            try:
                sync_workspace_to_package(self.project_root_dir, self.current_package_path)
            except Exception as e:
                logging.warning(f"Erro ao sincronizar pacote: {e}")

        # Se apenas 1 imagem foi importada e o editor estiver com documento aberto, oferece inseri-la
        if len(imported_paths) == 1 and self.editor:
            img_path = imported_paths[0]
            filename = os.path.basename(img_path)
            resp = QMessageBox.question(
                self,
                "Inserir Imagem no Documento",
                f"A imagem '{filename}' foi adicionada com sucesso ao projeto.\n\nDeseja inseri-la na posição atual do documento aberto?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if resp == QMessageBox.Yes:
                default_leg = f"Figura — {os.path.splitext(filename)[0].replace('_', ' ').capitalize()}"
                legenda, ok_leg = QInputDialog.getText(
                    self,
                    "Legenda da Imagem",
                    "Digite o título / legenda da figura (ABNT):",
                    text=default_leg
                )
                if not ok_leg or not legenda.strip():
                    legenda = "Figura"

                fonte, ok_fonte = QInputDialog.getText(
                    self,
                    "Fonte da Imagem",
                    "Digite a fonte da figura (ABNT):",
                    text="Elaborado pelos autores (2026)."
                )
                if not ok_fonte or not fonte.strip():
                    fonte = "Elaborado pelos autores (2026)."

                curr_file = getattr(self.editor, "file_path", None)
                if curr_file:
                    rel_img = os.path.relpath(img_path, os.path.dirname(curr_file))
                else:
                    rel_img = os.path.relpath(img_path, self.project_root_dir)

                cursor = self.editor.textCursor()
                cursor.beginEditBlock()
                tag = (
                    f"\n<div class=\"figura\">\n\n"
                    f"**{legenda.strip()}**\n\n"
                    f"![]({rel_img})\n\n"
                    f"<small>Fonte: {fonte.strip()}</small>\n\n"
                    f"</div>\n\n"
                )
                cursor.insertText(tag)
                cursor.endEditBlock()
                self.editor.setFocus()

    def open_file_in_tab(self, file_path: str) -> MarkdownEditor:
        """Abre um arquivo em uma aba. Se já estiver aberto, apenas seleciona sua aba."""
        abs_path = os.path.abspath(file_path)

        # Verifica se já está aberto em uma das abas existentes
        for i in range(self.editor_tabs.count()):
            widget = self.editor_tabs.widget(i)
            if isinstance(widget, MarkdownEditor) and getattr(widget, "file_path", None):
                if os.path.abspath(widget.file_path) == abs_path:
                    self.editor_tabs.setCurrentIndex(i)
                    self.current_file_path = abs_path
                    self.update_window_title()
                    return widget

        # Lê conteúdo do arquivo
        try:
            with open(abs_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logging.error(f"Erro ao ler arquivo {abs_path}: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro ao Abrir Arquivo", f"Não foi possível abrir o arquivo:\n{str(e)}")
            return None

        # Se houver apenas uma aba e ela for vazia e sem arquivo ("Sem título"), reaproveita
        if self.editor_tabs.count() == 1:
            first_ed = self.editor_tabs.widget(0)
            if isinstance(first_ed, MarkdownEditor) and not getattr(first_ed, "file_path", None):
                if not first_ed.toPlainText().strip() or not first_ed.document().isModified():
                    first_ed.file_path = abs_path
                    first_ed.setPlainText(content)
                    first_ed.document().setModified(False)
                    self.editor_tabs.setTabText(0, os.path.basename(abs_path))
                    self.editor_tabs.setTabToolTip(0, abs_path)
                    self.current_file_path = abs_path
                    self.update_window_title()
                    self.trigger_compilation()
                    return first_ed

        # Cria novo editor para a nova aba
        ed = MarkdownEditor(self)
        ed.file_path = abs_path
        ed.setPlainText(content)
        ed.document().setModified(False)
        ed.textChanged.connect(self.on_text_changed)
        ed.document().modificationChanged.connect(lambda modified, e=ed: self.update_tab_title(e))

        idx = self.editor_tabs.addTab(ed, os.path.basename(abs_path))
        self.editor_tabs.setTabToolTip(idx, abs_path)
        self.editor_tabs.setCurrentIndex(idx)
        self.current_file_path = abs_path
        self.update_window_title()
        self.status_label.setText(f"✓ Aberto na aba {idx + 1}: {os.path.basename(abs_path)}")
        self.trigger_compilation()
        return ed

    def load_file_to_editor(self, file_path: str):
        """Retrocompatibilidade: carrega arquivo abrindo ou focando sua aba."""
        return self.open_file_in_tab(file_path)

    def new_untitled_tab(self, content: str = "") -> MarkdownEditor:
        """Cria uma nova aba vazia para documento sem título."""
        ed = MarkdownEditor(self)
        ed.file_path = None
        if content:
            ed.setPlainText(content)
        else:
            ed.setPlainText("# Novo Documento Markdown\n\nComece a digitar...")
        ed.document().setModified(False)
        ed.textChanged.connect(self.on_text_changed)
        ed.document().modificationChanged.connect(lambda modified, e=ed: self.update_tab_title(e))
        idx = self.editor_tabs.addTab(ed, "Sem título")
        self.editor_tabs.setCurrentIndex(idx)
        self.current_file_path = None
        self.update_window_title()
        return ed

    def update_tab_title(self, editor: MarkdownEditor):
        """Atualiza o título da aba adicionando indicador '●' se houver modificações não salvas."""
        idx = self.editor_tabs.indexOf(editor)
        if idx == -1:
            return
        name = os.path.basename(editor.file_path) if getattr(editor, "file_path", None) else "Sem título"
        if editor.document().isModified():
            self.editor_tabs.setTabText(idx, f"● {name}")
        else:
            self.editor_tabs.setTabText(idx, name)

    def on_tab_changed(self, index: int):
        """Acionado ao alternar entre abas. Salva automaticamente a aba anterior se estiver modificada."""
        if index < 0 or index >= self.editor_tabs.count():
            return

        # Se a aba anterior estava modificada, salva automaticamente para prevenir qualquer perda de dados
        if hasattr(self, "_last_active_editor") and self._last_active_editor:
            prev_ed = self._last_active_editor
            if prev_ed != self.editor_tabs.widget(index) and getattr(prev_ed, "file_path", None) and prev_ed.document().isModified():
                self.save_editor_file(prev_ed)

        current_ed = self.editor_tabs.widget(index)
        self._last_active_editor = current_ed

        if isinstance(current_ed, MarkdownEditor):
            self.current_file_path = getattr(current_ed, "file_path", None)
            self.update_window_title()
            if self.current_file_path:
                self.status_label.setText(f"Aba ativa: {os.path.basename(self.current_file_path)}")
            if hasattr(self, "auto_compile_checkbox") and self.auto_compile_checkbox.isChecked():
                self.trigger_compilation()

    def on_tab_context_menu(self, pos):
        """Menu de contexto ao clicar com o botão direito na barra de abas."""
        tab_idx = self.editor_tabs.tabBar().tabAt(pos)
        if tab_idx < 0:
            return

        menu = QMenu(self)
        act_save = menu.addAction("💾  Salvar Esta Aba")
        act_save_all = menu.addAction("💾  Salvar Todas as Abas")
        menu.addSeparator()
        act_close = menu.addAction("❌  Fechar Aba")
        act_close_others = menu.addAction("❌  Fechar Outras Abas")
        act_close_all = menu.addAction("❌  Fechar Todas")

        action = menu.exec_(self.editor_tabs.tabBar().mapToGlobal(pos))
        if action == act_save:
            ed = self.editor_tabs.widget(tab_idx)
            if isinstance(ed, MarkdownEditor):
                self.save_editor_file(ed)
        elif action == act_save_all:
            self.save_all_files()
        elif action == act_close:
            self.close_tab(tab_idx)
        elif action == act_close_others:
            for i in range(self.editor_tabs.count() - 1, -1, -1):
                if i != tab_idx:
                    self.close_tab(i)
        elif action == act_close_all:
            for i in range(self.editor_tabs.count() - 1, -1, -1):
                self.close_tab(i)

    def close_tab(self, index: int):
        """Fecha uma aba específica, salvando ou confirmando alterações se não salvas."""
        if index < 0 or index >= self.editor_tabs.count():
            return

        ed = self.editor_tabs.widget(index)
        if isinstance(ed, MarkdownEditor) and ed.document().isModified():
            if getattr(ed, "file_path", None):
                if self.auto_save_enabled:
                    self.save_editor_file(ed)
                else:
                    name = os.path.basename(ed.file_path)
                    res = QMessageBox.question(
                        self,
                        "Alterações Não Salvas",
                        f"O arquivo <b>{name}</b> possui alterações não salvas.<br>Deseja salvar antes de fechar?",
                        QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                        QMessageBox.Save
                    )
                    if res == QMessageBox.Save:
                        self.save_editor_file(ed)
                    elif res == QMessageBox.Cancel:
                        return
            else:
                res = QMessageBox.question(
                    self,
                    "Documento Não Salvo",
                    "O documento sem título possui alterações.<br>Deseja salvar antes de fechar?",
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                    QMessageBox.Save
                )
                if res == QMessageBox.Save:
                    self.save_file_as()
                elif res == QMessageBox.Cancel:
                    return

        self.editor_tabs.removeTab(index)

        # Se fechar todas as abas, garante que o editor não fique vazio criando aba inicial
        if self.editor_tabs.count() == 0:
            self.new_untitled_tab()

    def close_all_tabs(self, save_modified: bool = True):
        """Fecha todas as abas abertas."""
        for i in range(self.editor_tabs.count() - 1, -1, -1):
            ed = self.editor_tabs.widget(i)
            if isinstance(ed, MarkdownEditor) and save_modified and getattr(ed, "file_path", None):
                if ed.document().isModified():
                    self.save_editor_file(ed)
            self.editor_tabs.removeTab(i)

    def save_editor_file(self, editor: MarkdownEditor) -> bool:
        """Salva o documento de um editor específico para o disco e sincroniza com pacote se houver."""
        if not editor:
            return False

        file_path = getattr(editor, "file_path", None)
        if not file_path:
            if editor == self.editor:
                return self.save_file_as()
            return False

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(editor.toPlainText())

            editor.document().setModified(False)
            self.update_tab_title(editor)

            if self.current_package_path:
                sync_workspace_to_package(self.project_root_dir, self.current_package_path)
                pkg_name = os.path.basename(self.current_package_path)
                self.update_window_title()
                self.status_label.setText(f"✓ Salvo e sincronizado no pacote: {pkg_name}")
            else:
                self.update_window_title()
                self.status_label.setText(f"✓ Arquivo salvo: {os.path.basename(file_path)}")

            logging.info(f"Arquivo salvo com sucesso: {file_path}")
            return True
        except Exception as e:
            logging.error(f"Erro ao salvar arquivo {file_path}: {e}", exc_info=True)
            QMessageBox.critical(self, "Erro ao Salvar Arquivo", f"Não foi possível salvar o arquivo:\n{str(e)}")
            return False

    def save_file(self):
        """Salva a aba ativa no momento."""
        return self.save_editor_file(self.editor)

    def save_all_files(self):
        """Salva todas as abas abertas que possuem caminho de arquivo associado."""
        saved_count = 0
        for i in range(self.editor_tabs.count()):
            ed = self.editor_tabs.widget(i)
            if isinstance(ed, MarkdownEditor) and getattr(ed, "file_path", None):
                if ed.document().isModified():
                    if self.save_editor_file(ed):
                        saved_count += 1
        if saved_count > 0:
            self.status_label.setText(f"✓ Todas as abas foram salvas ({saved_count} arquivo(s)).")

    def save_file_as(self):
        """Salva o documento atual com um novo nome ou em outro diretório."""
        default_name = os.path.basename(self.current_file_path) if self.current_file_path else "novo_documento.md"
        suggested_path = os.path.join(self.project_root_dir, default_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Arquivo Como...",
            suggested_path,
            "Arquivos Markdown (*.md *.markdown);;Todos os Arquivos (*)"
        )
        if not file_path:
            return False

        ed = self.editor
        if ed:
            ed.file_path = file_path
            self.current_file_path = file_path
            self.save_editor_file(ed)
            self.update_tab_title(ed)
            idx = self.editor_tabs.indexOf(ed)
            if idx != -1:
                self.editor_tabs.setTabToolTip(idx, file_path)
            return True
        return False

    def quit_app(self):
        """Encerra a aplicação."""
        self.close()

    def show_about(self):
        """Exibe o diálogo 'Sobre o MK Writer'."""
        QMessageBox.about(
            self,
            "Sobre o MK Writer",
            "<h3>MK Writer</h3>"
            "<p>Editor e compilador modular de Markdown para PDF com padrões acadêmicos ABNT.</p>"
            "<p><b>Desenvolvido por:</b> Danilo Barcelos &amp; Antigravity (Google DeepMind)</p>"
            "<p><b>Recursos:</b></p>"
            "<ul>"
            "<li><b>Formato de Pacote Único (.mkw)</b>: armazena todo o projeto em um único arquivo compacto e portátil</li>"
            "<li>Visualização PDF em tempo real (1.5s debounce)</li>"
            "<li>Suporte à diretiva <code>!include</code> modular por capítulos</li>"
            "<li>Assistente de IA integrado</li>"
            "<li>Exportação PDF nativa com precisão milimétrica</li>"
            "</ul>"
        )

    def show_shortcuts_help(self):
        """Exibe os atalhos de teclado principais em uma caixa de mensagem."""
        shortcuts_text = (
            "<b>Atalhos de Teclado Principais:</b><br><br>"
            "• <b>Ctrl + Shift + P</b>: Criar Novo Pacote (.mkw)<br>"
            "• <b>Ctrl + Alt + O</b>: Abrir Pacote MK Writer (.mkw / .mkdoc)<br>"
            "• <b>Ctrl + O</b>: Abrir Arquivo em Nova Aba<br>"
            "• <b>Ctrl + S</b>: Salvar Aba Ativa / Sincronizar Pacote<br>"
            "• <b>Ctrl + Shift + S</b>: Salvar Todas as Abas<br>"
            "• <b>Ctrl + Alt + S</b>: Salvar Arquivo Como...<br>"
            "• <b>Ctrl + E</b>: Exportar PDF<br>"
            "• <b>Ctrl + R / F5</b>: Compilar PDF Manualmente<br>"
            "• <b>Ctrl + B</b>: Alternar Árvore de Arquivos<br>"
            "• <b>Ctrl + I</b>: Alternar Assistente de IA<br>"
            "• <b>Ctrl + D</b>: Destacar/Acoplar Visualizador PDF<br>"
            "• <b>F2</b>: Renomear Arquivo ou Pasta Selecionada<br>"
            "• <b>Delete</b>: Excluir Item Selecionado<br>"
            "• <b>Ctrl + Q</b>: Sair da Aplicação"
        )
        QMessageBox.information(self, "Atalhos de Teclado", shortcuts_text)

    def export_pdf_dialog(self):
        """Abre uma caixa de diálogo para o usuário salvar o PDF compilado em qualquer lugar do computador."""
        suggested_name = "documento.pdf"
        if self.current_file_path:
            base = os.path.splitext(os.path.basename(self.current_file_path))[0]
            suggested_name = f"{base}.pdf"

        default_dir = self.project_root_dir
        if self.current_file_path:
            default_dir = os.path.dirname(self.current_file_path)

        suggested_path = os.path.join(default_dir, suggested_name)

        target_pdf_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Documento PDF",
            suggested_path,
            "Arquivos PDF (*.pdf);;Todos os Arquivos (*)"
        )

        if not target_pdf_path:
            return

        if not target_pdf_path.endswith(".pdf"):
            target_pdf_path += ".pdf"

        if self.last_compiled_pdf_path and os.path.exists(self.last_compiled_pdf_path):
            try:
                import shutil
                shutil.copyfile(self.last_compiled_pdf_path, target_pdf_path)
                self.status_label.setText(f"✓ PDF salvo com sucesso em: {target_pdf_path}")
                self.status_label.setStyleSheet("color: #166534; font-weight: bold;")
                logging.info(f"PDF exportado para: {target_pdf_path}")
                QMessageBox.information(
                    self,
                    "PDF Salvo com Sucesso",
                    f"O documento PDF foi exportado com sucesso para:\n\n{target_pdf_path}"
                )
                return
            except Exception as e:
                logging.error(f"Erro ao salvar PDF: {e}", exc_info=True)
                QMessageBox.warning(self, "Erro ao Salvar PDF", f"Falha ao copiar o arquivo PDF:\n{str(e)}")

        # Se ainda não houver compilação pronta, dispara a compilação
        self.trigger_compilation()

    def on_text_changed(self):
        ed = self.sender()
        if not ed and hasattr(self, "editor"):
            ed = self.editor
        if ed and isinstance(ed, MarkdownEditor):
            ed.document().setModified(True)
            self.update_tab_title(ed)
            if self.auto_save_enabled and getattr(ed, "file_path", None):
                self.auto_save_timer.start(1500)

        if hasattr(self, "auto_compile_checkbox") and self.auto_compile_checkbox.isChecked():
            self.debounce_timer.start(1500)

    def on_debounce_timeout(self):
        if hasattr(self, "act_auto_compile") and self.act_auto_compile.isChecked():
            self.trigger_compilation()

    def trigger_compilation(self):
        if self.is_compiling:
            self.pending_recompile = True
            return

        ed = self.editor
        if not ed:
            return

        markdown_text = ed.toPlainText()
        if not markdown_text.strip():
            self.status_label.setText("O documento está vazio. Nenhuma compilação necessária.")
            return

        self.is_compiling = True
        self.status_label.setText("⏳ Compilando PDF em segundo plano...")
        self.status_label.setStyleSheet("color: #2563EB; font-weight: bold;")
        logging.info("Disparando nova compilação de PDF...")

        working_dir = self.project_root_dir
        if self.current_file_path:
            working_dir = os.path.dirname(self.current_file_path)

        self.compiler_thread = PDFCompilerThread(
            markdown_text,
            working_dir=working_dir,
            main_file_path=self.current_file_path,
            project_root=self.project_root_dir,
            parent=self
        )
        self.compiler_thread.compilation_finished.connect(self.on_compilation_finished)
        self.compiler_thread.start()

    def on_compilation_finished(self, success: bool, pdf_path: str, stderr_msg: str, elapsed_seconds: float):
        self.is_compiling = False

        if success:
            self.last_compiled_pdf_path = pdf_path
            time_str = datetime.now().strftime("%H:%M:%S")
            msg = f"✓ PDF compilado com sucesso ({elapsed_seconds:.2f}s) às {time_str}"
            self.status_label.setText(msg)
            self.status_label.setStyleSheet("color: #166534; font-weight: bold;")
            logging.info(f"Compilação de PDF concluída com sucesso em {elapsed_seconds:.2f}s.")
            self.pdf_viewer.load_pdf(pdf_path)
        else:
            clean_err = stderr_msg.replace("\n", " | ")
            if len(clean_err) > 180:
                clean_err = clean_err[:180] + "..."
            
            self.status_label.setText(f"⚠️ Erro de compilação: {clean_err}")
            self.status_label.setStyleSheet("color: #DC2626; font-weight: bold;")
            logging.error(f"Erro de compilação Pandoc/WeasyPrint: {stderr_msg}")

        if self.pending_recompile:
            self.pending_recompile = False
            self.trigger_compilation()

    def closeEvent(self, event):
        """Ao fechar a janela principal, salva abas modificadas, sincroniza pacote e encerra janelas filhas."""
        for i in range(self.editor_tabs.count()):
            ed = self.editor_tabs.widget(i)
            if isinstance(ed, MarkdownEditor) and ed.document().isModified():
                if getattr(ed, "file_path", None):
                    if self.auto_save_enabled:
                        self.save_editor_file(ed)
                    else:
                        name = os.path.basename(ed.file_path)
                        res = QMessageBox.question(
                            self,
                            "Salvar Alterações",
                            f"O arquivo <b>{name}</b> possui alterações não salvas.<br>Deseja salvar antes de fechar?",
                            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                            QMessageBox.Save
                        )
                        if res == QMessageBox.Save:
                            self.save_editor_file(ed)
                        elif res == QMessageBox.Cancel:
                            event.ignore()
                            return

        if self.current_package_path and self.project_root_dir:
            try:
                sync_workspace_to_package(self.project_root_dir, self.current_package_path)
                logging.info(f"Sincronização final do pacote concluída: {self.current_package_path}")
            except Exception as e:
                logging.warning(f"Erro na sincronização final do pacote: {e}")

        if self.detached_pdf_window:
            self.detached_pdf_window.close()
        event.accept()
