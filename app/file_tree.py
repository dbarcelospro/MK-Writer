import os
import shutil
from PyQt5.QtCore import QDir, QModelIndex, Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QFileSystemModel,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QShortcut,
    QTreeView,
    QVBoxLayout,
    QWidget,
)


class ProjectFileTree(QWidget):
    """
    Painel lateral de navegação de arquivos do projeto em estrutura de árvore (File Tree).
    Suporta alteração dinâmica da pasta raiz e botão para selecionar qualquer pasta de projeto.
    """
    file_selected = pyqtSignal(str)
    root_changed = pyqtSignal(str)
    item_renamed = pyqtSignal(str, str)  # (old_path, new_path)
    images_imported = pyqtSignal(list)  # Lista de caminhos completos das imagens importadas

    def __init__(self, root_path: str = None, parent=None):
        super().__init__(parent)
        self.root_path = os.path.abspath(root_path or os.getcwd())

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Cabeçalho do Painel com Título e Botão de Abrir Pasta
        self.header_widget = QWidget(self)
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(8, 6, 8, 6)
        self.header_layout.setSpacing(6)

        self.header_label = QLabel(f"📁 {os.path.basename(self.root_path)}", self)
        self.header_label.setStyleSheet("font-weight: bold; color: #334155; font-size: 9.5pt;")

        btn_style = """
            QPushButton {
                background-color: #E2E8F0;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 3px 6px;
                font-size: 8.5pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #CBD5E1;
                color: #0F172A;
            }
        """

        self.btn_new_file = QPushButton("📄+", self)
        self.btn_new_file.setToolTip("Criar Novo Arquivo")
        self.btn_new_file.setCursor(Qt.PointingHandCursor)
        self.btn_new_file.setStyleSheet(btn_style)
        self.btn_new_file.clicked.connect(lambda: self.create_new_file())

        self.btn_new_folder = QPushButton("📁+", self)
        self.btn_new_folder.setToolTip("Criar Nova Pasta")
        self.btn_new_folder.setCursor(Qt.PointingHandCursor)
        self.btn_new_folder.setStyleSheet(btn_style)
        self.btn_new_folder.clicked.connect(lambda: self.create_new_folder())

        self.btn_rename = QPushButton("✏️", self)
        self.btn_rename.setToolTip("Renomear Arquivo ou Pasta (F2)")
        self.btn_rename.setCursor(Qt.PointingHandCursor)
        self.btn_rename.setStyleSheet(btn_style)
        self.btn_rename.clicked.connect(lambda: self.rename_selected_item())

        self.btn_import_image = QPushButton("🖼️+", self)
        self.btn_import_image.setToolTip("Importar Imagens do Computador para o Projeto...")
        self.btn_import_image.setCursor(Qt.PointingHandCursor)
        self.btn_import_image.setStyleSheet(btn_style)
        self.btn_import_image.clicked.connect(lambda: self.import_images())

        self.btn_open_folder = QPushButton("📂", self)
        self.btn_open_folder.setToolTip("Selecionar uma nova pasta de projeto como raiz")
        self.btn_open_folder.setCursor(Qt.PointingHandCursor)
        self.btn_open_folder.setStyleSheet(btn_style)
        self.btn_open_folder.clicked.connect(self.select_new_root_folder)

        self.header_layout.addWidget(self.header_label, 1)
        self.header_layout.addWidget(self.btn_new_file)
        self.header_layout.addWidget(self.btn_new_folder)
        self.header_layout.addWidget(self.btn_import_image)
        self.header_layout.addWidget(self.btn_rename)
        self.header_layout.addWidget(self.btn_open_folder)

        self.header_widget.setStyleSheet("background-color: #F1F5F9; border-bottom: 1px solid #CBD5E1;")
        self.main_layout.addWidget(self.header_widget)

        # QFileSystemModel
        self.model = QFileSystemModel(self)
        self.model.setRootPath(self.root_path)

        # Filtro de arquivos exibidos
        self.model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self.model.setNameFilters([
            "*.md", "*.markdown", "*.bib", "*.txt", "*.json", "*.yaml", "*.yml", "*.css",
            "*.png", "*.jpg", "*.jpeg", "*.svg", "*.webp", "*.bmp", "*.gif"
        ])
        self.model.setNameFilterDisables(False)

        # QTreeView
        self.tree_view = QTreeView(self)
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(self.root_path))

        # Atalho F2 diretamente na árvore de arquivos
        self.shortcut_f2 = QShortcut(QKeySequence(Qt.Key_F2), self.tree_view)
        self.shortcut_f2.activated.connect(lambda: self.rename_selected_item())

        # Oculta colunas desnecessárias
        self.tree_view.setColumnHidden(1, True)
        self.tree_view.setColumnHidden(2, True)
        self.tree_view.setColumnHidden(3, True)
        self.tree_view.setHeaderHidden(True)
        self.tree_view.setAnimated(True)
        self.tree_view.setIndentation(16)
        self.tree_view.setSortingEnabled(True)
        self.tree_view.sortByColumn(0, Qt.AscendingOrder)

        # Habilita menu de contexto (clique direito)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)

        self.tree_view.setStyleSheet("""
            QTreeView {
                background-color: #F8FAFC;
                color: #1E293B;
                border: none;
                font-size: 9.5pt;
            }
            QTreeView::item {
                padding: 4px 6px;
                border-radius: 4px;
            }
            QTreeView::item:hover {
                background-color: #E2E8F0;
                color: #0F172A;
            }
            QTreeView::item:selected {
                background-color: #DBEAFE;
                color: #1E40AF;
                font-weight: bold;
            }
        """)

        self.tree_view.clicked.connect(self._on_item_clicked)
        self.tree_view.doubleClicked.connect(self._on_item_clicked)

        self.main_layout.addWidget(self.tree_view)

        self._expand_initial_dirs()

    def select_new_root_folder(self):
        """Abre uma caixa de diálogo para escolher uma nova pasta de projeto."""
        folder_path = QFileDialog.getExistingDirectory(self, "Selecionar Pasta do Projeto", self.root_path)
        if folder_path:
            self.set_root_path(folder_path)

    def set_header_title(self, title: str):
        """Atualiza o título do cabeçalho da árvore manualmente (ex: nome de pacote .mkw)."""
        self.header_label.setText(title)

    def set_root_path(self, path: str, display_name: str = None):
        """Atualiza a pasta raiz exibida na árvore."""
        self.root_path = os.path.abspath(path)
        if display_name:
            self.header_label.setText(display_name)
        else:
            self.header_label.setText(f"📁 {os.path.basename(self.root_path)}")
        self.model.setRootPath(self.root_path)
        self.tree_view.setRootIndex(self.model.index(self.root_path))
        self.tree_view.sortByColumn(0, Qt.AscendingOrder)
        self._expand_initial_dirs()
        self.root_changed.emit(self.root_path)

    def _expand_dir_recursive(self, parent_index: QModelIndex, current_depth: int, max_depth: int):
        if current_depth > max_depth:
            return
        self.tree_view.expand(parent_index)
        for i in range(self.model.rowCount(parent_index)):
            child_index = self.model.index(i, 0, parent_index)
            if self.model.isDir(child_index):
                self._expand_dir_recursive(child_index, current_depth + 1, max_depth)

    def _expand_initial_dirs(self):
        root_index = self.model.index(self.root_path)
        self._expand_dir_recursive(root_index, 0, 3)

    def _on_item_clicked(self, index: QModelIndex):
        file_path = self.model.filePath(index)
        if not self.model.isDir(index) and os.path.isfile(file_path):
            self.file_selected.emit(file_path)

    def _get_target_dir(self, index: QModelIndex = None) -> str:
        """Retorna o diretório alvo para criação de arquivos/pastas com base no item selecionado."""
        if index is None or not index.isValid():
            index = self.tree_view.currentIndex()

        if index.isValid():
            path = self.model.filePath(index)
            if self.model.isDir(index):
                return path
            else:
                return os.path.dirname(path)
        return self.root_path

    def show_context_menu(self, position):
        """Exibe menu de contexto de clique direito na árvore de arquivos."""
        index = self.tree_view.indexAt(position)
        menu = QMenu(self)

        act_new_file = menu.addAction("📄  Novo Arquivo...")
        act_new_file.triggered.connect(lambda: self.create_new_file(index))

        act_new_folder = menu.addAction("📁  Nova Pasta...")
        act_new_folder.triggered.connect(lambda: self.create_new_folder(index))

        act_import_img = menu.addAction("🖼️  Importar Imagens...")
        act_import_img.triggered.connect(lambda: self.import_images(index))

        menu.addSeparator()

        if index.isValid():
            act_rename = menu.addAction("✏️  Renomear...")
            act_rename.triggered.connect(lambda: self.rename_selected_item(index))

            act_delete = menu.addAction("🗑️  Excluir")
            act_delete.triggered.connect(lambda: self.delete_selected_item(index))
            menu.addSeparator()

        act_open_sys = menu.addAction("📂  Abrir Pasta no Gerenciador...")
        act_open_sys.triggered.connect(lambda: self.open_in_system_explorer(index))

        menu.exec_(self.tree_view.viewport().mapToGlobal(position))

    def create_new_file(self, index: QModelIndex = None):
        """Cria um novo arquivo no diretório selecionado ou na raiz."""
        target_dir = self._get_target_dir(index)
        file_name, ok = QInputDialog.getText(
            self, "Novo Arquivo", "Nome do arquivo (ex: 03_capitulo.md):"
        )
        if not ok or not file_name.strip():
            return

        file_name = file_name.strip()
        if not os.path.extsep in file_name:
            file_name += ".md"

        full_path = os.path.join(target_dir, file_name)

        if os.path.exists(full_path):
            QMessageBox.warning(self, "Arquivo Já Existe", f"O arquivo '{file_name}' já existe neste diretório.")
            return

        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(f"# {os.path.splitext(file_name)[0].replace('_', ' ').title()}\n\n")
            
            self.file_selected.emit(full_path)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Criar Arquivo", f"Não foi possível criar o arquivo:\n{str(e)}")

    def create_new_folder(self, index: QModelIndex = None):
        """Cria uma nova pasta no diretório selecionado ou na raiz."""
        target_dir = self._get_target_dir(index)
        folder_name, ok = QInputDialog.getText(
            self, "Nova Pasta", "Nome da pasta (ex: Imagens):"
        )
        if not ok or not folder_name.strip():
            return

        folder_name = folder_name.strip()
        full_path = os.path.join(target_dir, folder_name)

        if os.path.exists(full_path):
            QMessageBox.warning(self, "Pasta Já Existe", f"A pasta '{folder_name}' já existe neste diretório.")
            return

        try:
            os.makedirs(full_path, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Erro ao Criar Pasta", f"Não foi possível criar a pasta:\n{str(e)}")

    def import_images(self, index: QModelIndex = None) -> list:
        """Permite selecionar uma ou mais imagens do computador e copiá-las para a pasta do projeto."""
        target_dir = self._get_target_dir(index)

        # Se o item selecionado for a raiz, tenta usar ou criar a pasta 'Imagens' por padrão
        if target_dir == self.root_path:
            for candidate in ["Imagens", "imagens", "images", "img"]:
                candidate_path = os.path.join(self.root_path, candidate)
                if os.path.isdir(candidate_path):
                    target_dir = candidate_path
                    break
            else:
                target_dir = os.path.join(self.root_path, "Imagens")
                os.makedirs(target_dir, exist_ok=True)

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Importar Imagens para o Projeto",
            "",
            "Imagens (*.png *.jpg *.jpeg *.svg *.webp *.bmp *.gif);;Todos os Arquivos (*)"
        )
        if not files:
            return []

        imported_paths = []
        for src in files:
            filename = os.path.basename(src)
            dest = os.path.join(target_dir, filename)
            if os.path.abspath(src) == os.path.abspath(dest):
                imported_paths.append(dest)
                continue
            try:
                shutil.copy2(src, dest)
                imported_paths.append(dest)
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Importar Imagem", f"Não foi possível copiar '{filename}':\n{str(e)}")

        if imported_paths:
            self.images_imported.emit(imported_paths)
            rel_folder = os.path.relpath(target_dir, self.root_path)
            QMessageBox.information(
                self,
                "Imagens Importadas",
                f"{len(imported_paths)} imagem(ns) importada(s) com sucesso para:\n📁 {rel_folder}"
            )

        return imported_paths

    def open_in_system_explorer(self, index: QModelIndex = None):
        """Abre a pasta do projeto no gerenciador de arquivos padrão do sistema (Nautilus, Dolphin, Explorer)."""
        target_dir = self._get_target_dir(index)
        if not os.path.exists(target_dir):
            target_dir = self.root_path

        import subprocess
        import platform
        try:
            sys_name = platform.system()
            if sys_name == "Windows":
                os.startfile(target_dir)
            elif sys_name == "Darwin":
                subprocess.Popen(["open", target_dir])
            else:
                # Linux / Unix
                subprocess.Popen(["xdg-open", target_dir])
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"Não foi possível abrir o gerenciador de arquivos:\n{e}")

    def delete_selected_item(self, index: QModelIndex = None):
        """Exclui o arquivo ou pasta selecionado após confirmação."""
        if index is None or not index.isValid():
            index = self.tree_view.currentIndex()

        if not index.isValid():
            return

        file_path = self.model.filePath(index)
        item_name = os.path.basename(file_path)
        is_dir = self.model.isDir(index)

        item_type = "a pasta e todo o seu conteúdo" if is_dir else "o arquivo"
        reply = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Tem certeza de que deseja excluir {item_type} '\n{item_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                if is_dir:
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
            except Exception as e:
                QMessageBox.critical(self, "Erro ao Excluir", f"Não foi possível excluir '{item_name}':\n{str(e)}")

    def rename_selected_item(self, index: QModelIndex = None):
        """Renomeia o arquivo ou pasta selecionado após confirmação."""
        if index is None or not index.isValid():
            index = self.tree_view.currentIndex()

        if not index.isValid():
            QMessageBox.information(
                self,
                "Renomear",
                "Selecione um arquivo ou pasta na árvore para renomear."
            )
            return

        old_path = self.model.filePath(index)
        if not os.path.exists(old_path):
            return

        old_name = os.path.basename(old_path)
        is_dir = self.model.isDir(index)
        item_type = "Pasta" if is_dir else "Arquivo"

        new_name, ok = QInputDialog.getText(
            self,
            f"Renomear {item_type}",
            f"Novo nome para '{old_name}':",
            text=old_name
        )

        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return

        new_name = new_name.strip()
        dir_path = os.path.dirname(old_path)
        new_path = os.path.join(dir_path, new_name)

        if os.path.exists(new_path):
            QMessageBox.warning(
                self,
                "Item Já Existe",
                f"Já existe um {item_type.lower()} com o nome '{new_name}' neste local."
            )
            return

        try:
            os.rename(old_path, new_path)
            self.item_renamed.emit(old_path, new_path)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao Renomear",
                f"Não foi possível renomear '{old_name}':\n{str(e)}"
            )

