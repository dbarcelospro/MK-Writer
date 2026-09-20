import logging
import os

from PyQt5.QtCore import QPoint, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import (
    QCloseEvent,
    QColor,
    QImage,
    QKeySequence,
    QPainter,
    QPixmap,
)
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
import pymupdf


class DetachedPDFWindow(QMainWindow):
    """
    Janela flutuante separada para exibir o PDF em um segundo monitor ou área de trabalho.
    """
    closed_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MK-Writer - Visualizador de PDF (Janela Separada / 2º Monitor)")
        self.resize(800, 950)

    def closeEvent(self, event: QCloseEvent):
        """Ao fechar a janela separada, avisa a janela principal para acoplar de volta."""
        self.closed_signal.emit()
        event.accept()


class PDFPageWidget(QWidget):
    """
    Widget interativo para exibir uma página de PDF renderizada com suporte a:
    - Seleção contínua de texto com arraste do mouse
    - Seleção de palavra por duplo clique
    - Seleção de linha por triplo clique
    - Realce visual translúcido sobre o texto selecionado
    - Alteração dinâmica do cursor para I-beam sobre texto
    - Cópia com atalho Ctrl+C e seleção total com Ctrl+A
    - Menu de contexto (botão direito) com opções 'Copiar' e 'Selecionar Tudo'
    """
    selection_started = pyqtSignal(object)

    def __init__(self, page_num: int, pixmap: QPixmap, words: list, zoom_factor: float, parent=None):
        super().__init__(parent)
        self.page_num = page_num
        self.pixmap = pixmap
        # words: lista de tuplas (x0, y0, x1, y1, text, block_no, line_no, word_no)
        self.words = words or []
        self.zoom_factor = zoom_factor

        self.selected_indices = set()
        self.is_selecting = False
        self.drag_start_idx = None

        self.setFixedSize(pixmap.width(), pixmap.height())
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        # Mapeamento de linhas para navegação e hit-testing
        self._lines_dict = {}
        for i, w in enumerate(self.words):
            key = (w[5], w[6])
            if key not in self._lines_dict:
                self._lines_dict[key] = []
            self._lines_dict[key].append(i)

    def _to_pdf_coords(self, pos: QPoint):
        """Converte coordenadas em pixels do widget para pontos do PDF."""
        return pos.x() / self.zoom_factor, pos.y() / self.zoom_factor

    def find_word_index_at(self, pdf_x: float, pdf_y: float):
        """
        Localiza o índice da palavra mais próxima do ponto clicado ou arrastado,
        respeitando a ordem de leitura.
        """
        if not self.words:
            return None

        # 1. Verifica colisão exata (com pequena margem de tolerância)
        for i, w in enumerate(self.words):
            if (w[0] - 3) <= pdf_x <= (w[2] + 3) and (w[1] - 3) <= pdf_y <= (w[3] + 3):
                return i

        # 2. Localiza a linha mais próxima no eixo Y
        best_line_key = None
        min_y_dist = float("inf")
        for key, indices in self._lines_dict.items():
            y0 = min(self.words[idx][1] for idx in indices)
            y1 = max(self.words[idx][3] for idx in indices)
            if y0 <= pdf_y <= y1:
                best_line_key = key
                min_y_dist = 0
                break
            y_dist = min(abs(pdf_y - y0), abs(pdf_y - y1))
            if y_dist < min_y_dist:
                min_y_dist = y_dist
                best_line_key = key

        if best_line_key is None:
            return None

        # 3. Na linha encontrada, busca a palavra mais próxima no eixo X
        best_idx = None
        min_x_dist = float("inf")
        for idx in self._lines_dict[best_line_key]:
            w = self.words[idx]
            if w[0] <= pdf_x <= w[2]:
                return idx
            x_dist = min(abs(pdf_x - w[0]), abs(pdf_x - w[2]))
            if x_dist < min_x_dist:
                min_x_dist = x_dist
                best_idx = idx

        return best_idx

    def _is_over_text(self, pdf_x: float, pdf_y: float) -> bool:
        """Verifica se as coordenadas estão sobre uma palavra de texto."""
        for w in self.words:
            if (w[0] - 2) <= pdf_x <= (w[2] + 2) and (w[1] - 2) <= pdf_y <= (w[3] + 2):
                return True
        return False

    def clear_selection(self):
        """Limpa a seleção atual nesta página."""
        if self.selected_indices:
            self.selected_indices.clear()
            self.update()

    def has_selection(self) -> bool:
        """Indica se há texto selecionado."""
        return bool(self.selected_indices)

    def select_all(self):
        """Seleciona todo o texto desta página."""
        if self.words:
            self.selection_started.emit(self)
            self.selected_indices = set(range(len(self.words)))
            self.update()

    def get_selected_text(self) -> str:
        """
        Reconstitui o texto selecionado preservando espaços e quebras de linha/parágrafo.
        """
        if not self.selected_indices:
            return ""

        sorted_idx = sorted(self.selected_indices)
        lines = []
        curr_line = []
        last_block = None
        last_line = None

        for idx in sorted_idx:
            w = self.words[idx]
            b_no, l_no, text = w[5], w[6], w[4]
            if last_line is not None and (b_no != last_block or l_no != last_line):
                lines.append(" ".join(curr_line))
                curr_line = []
                if b_no != last_block:
                    lines.append("")  # Espaçamento entre parágrafos
            curr_line.append(text)
            last_block = b_no
            last_line = l_no

        if curr_line:
            lines.append(" ".join(curr_line))

        return "\n".join(lines)

    def copy_selected_text(self):
        """Copia o texto selecionado para a área de transferência do sistema."""
        text = self.get_selected_text()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            logging.info(f"Texto copiado do PDF ({len(text)} caracteres).")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setFocus()
            self.selection_started.emit(self)
            pdf_x, pdf_y = self._to_pdf_coords(event.pos())
            idx = self.find_word_index_at(pdf_x, pdf_y)
            if idx is not None:
                self.drag_start_idx = idx
                self.selected_indices = {idx}
                self.is_selecting = True
            else:
                self.clear_selection()
                self.is_selecting = False
            self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pdf_x, pdf_y = self._to_pdf_coords(event.pos())

        if self.is_selecting and self.drag_start_idx is not None:
            curr_idx = self.find_word_index_at(pdf_x, pdf_y)
            if curr_idx is not None:
                start = min(self.drag_start_idx, curr_idx)
                end = max(self.drag_start_idx, curr_idx)
                self.selected_indices = set(range(start, end + 1))
                self.update()
        else:
            if self._is_over_text(pdf_x, pdf_y):
                self.setCursor(Qt.IBeamCursor)
            else:
                self.setCursor(Qt.ArrowCursor)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_selecting = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            pdf_x, pdf_y = self._to_pdf_coords(event.pos())
            idx = self.find_word_index_at(pdf_x, pdf_y)
            if idx is not None:
                self.selection_started.emit(self)
                self.selected_indices = {idx}
                self.update()
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_C and (event.modifiers() & Qt.ControlModifier):
            self.copy_selected_text()
            event.accept()
        elif event.key() == Qt.Key_A and (event.modifiers() & Qt.ControlModifier):
            self.select_all()
            event.accept()
        else:
            super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        copy_action = menu.addAction("📋 Copiar")
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.setEnabled(self.has_selection())
        copy_action.triggered.connect(self.copy_selected_text)

        select_all_action = menu.addAction("🔍 Selecionar Tudo")
        select_all_action.setShortcut(QKeySequence.SelectAll)
        select_all_action.setEnabled(bool(self.words))
        select_all_action.triggered.connect(self.select_all)

        menu.exec_(event.globalPos())

    def paintEvent(self, event):
        painter = QPainter(self)
        # 1. Desenha a página renderizada
        if self.pixmap and not self.pixmap.isNull():
            painter.drawPixmap(0, 0, self.pixmap)

        # 2. Desenha a camada de realce de texto selecionado
        if self.selected_indices:
            # Cor azul translúcida para seleção suave
            highlight_color = QColor(33, 150, 243, 85)
            painter.setBrush(highlight_color)
            painter.setPen(Qt.NoPen)

            for idx in self.selected_indices:
                if 0 <= idx < len(self.words):
                    w = self.words[idx]
                    rx = w[0] * self.zoom_factor
                    ry = w[1] * self.zoom_factor
                    rw = (w[2] - w[0]) * self.zoom_factor
                    rh = (w[3] - w[1]) * self.zoom_factor
                    painter.drawRect(QRectF(rx, ry, rw, rh))


class PDFViewer(QWidget):
    """
    Componente visualizador de PDF ultra-estável e de alto desempenho baseado em PyMuPDF (fitz).
    Livre de dependências do Chromium/QtWebEngine para evitar travamentos de GPU/Wayland no Linux.
    Suporta seleção nativa e cópia de texto com alto desempenho.
    """
    detach_requested = pyqtSignal()
    reattach_requested = pyqtSignal()
    save_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pdf_file_path = None
        self.is_detached = False
        self.zoom_factor = 1.25  # Fator de escala inicial
        self.doc = None
        self.page_widgets = []

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Barra superior do Visualizador PDF
        self.header_widget = QWidget(self)
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(8, 4, 8, 4)
        self.header_layout.setSpacing(6)

        self.title_label = QLabel("📄 Visualização do PDF", self)
        self.title_label.setStyleSheet("font-weight: bold; color: #334155; font-size: 9.5pt;")

        # Controles de Zoom
        self.btn_zoom_out = QPushButton("🔍 -", self)
        self.btn_zoom_out.setToolTip("Reduzir Zoom")
        self.btn_zoom_out.setCursor(Qt.PointingHandCursor)
        self.btn_zoom_out.clicked.connect(self.zoom_out)

        self.lbl_zoom = QLabel("125%", self)
        self.lbl_zoom.setStyleSheet("font-weight: bold; color: #475569; font-size: 8.5pt;")

        self.btn_zoom_in = QPushButton("🔍 +", self)
        self.btn_zoom_in.setToolTip("Aumentar Zoom")
        self.btn_zoom_in.setCursor(Qt.PointingHandCursor)
        self.btn_zoom_in.clicked.connect(self.zoom_in)

        button_style = """
            QPushButton {
                background-color: #F1F5F9;
                color: #1E293B;
                border: 1px solid #CBD5E1;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 8.5pt;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
                color: #0F172A;
            }
        """
        self.btn_zoom_out.setStyleSheet(button_style)
        self.btn_zoom_in.setStyleSheet(button_style)

        # Botão Salvar PDF
        self.btn_save = QPushButton("📥 Salvar PDF", self)
        self.btn_save.setToolTip("Salvar/Exportar o PDF compilado em qualquer pasta")
        self.btn_save.setCursor(Qt.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: white;
                border: 1px solid #059669;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 8.5pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.btn_save.clicked.connect(self.save_requested.emit)

        self.btn_detach = QPushButton("↗️ Destacar Janela (2º Monitor)", self)
        self.btn_detach.setToolTip("Destacar o visualizador de PDF para usar em outro monitor ou janela")
        self.btn_detach.setCursor(Qt.PointingHandCursor)
        self.btn_detach.setStyleSheet(button_style)
        self.btn_detach.clicked.connect(self.toggle_detach)

        self.header_layout.addWidget(self.title_label)
        self.header_layout.addSpacing(10)
        self.header_layout.addWidget(self.btn_zoom_out)
        self.header_layout.addWidget(self.lbl_zoom)
        self.header_layout.addWidget(self.btn_zoom_in)
        self.header_layout.addStretch(1)
        self.header_layout.addWidget(self.btn_save)
        self.header_layout.addWidget(self.btn_detach)

        self.header_widget.setStyleSheet("background-color: #F8FAFC; border-bottom: 1px solid #CBD5E1;")
        self.layout.addWidget(self.header_widget)

        # Área de Rolagem do PDF
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: #525659; border: none; }")

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: #525659;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(16, 16, 16, 16)
        self.scroll_layout.setSpacing(16)
        self.scroll_layout.setAlignment(Qt.AlignHCenter)

        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area, 1)

    def _on_page_selection_started(self, active_page_widget):
        """Desmarca o texto de outras páginas ao iniciar uma seleção."""
        for pw in self.page_widgets:
            if pw is not active_page_widget:
                pw.clear_selection()

    def copy_selection(self):
        """Copia a seleção da página ativa para a área de transferência."""
        for pw in self.page_widgets:
            if pw.has_selection():
                pw.copy_selected_text()
                break

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_C and (event.modifiers() & Qt.ControlModifier):
            self.copy_selection()
            event.accept()
        else:
            super().keyPressEvent(event)

    def load_pdf(self, pdf_file_path: str):
        """Carrega e renderiza todas as páginas do PDF usando PyMuPDF (fitz) com suporte a seleção de texto."""
        if not os.path.exists(pdf_file_path):
            return

        self.pdf_file_path = os.path.abspath(pdf_file_path)

        # Preserva a posição atual do scrollbar para recompilação contínua
        v_scroll = self.scroll_area.verticalScrollBar().value()

        try:
            if self.doc:
                self.doc.close()
            self.doc = pymupdf.open(self.pdf_file_path)

            # Limpa o layout das páginas anteriores
            self.page_widgets.clear()
            while self.scroll_layout.count():
                child = self.scroll_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            # Renderiza cada página do PDF
            for page_num in range(len(self.doc)):
                page = self.doc.load_page(page_num)

                # Extrai palavras e coordenadas do texto
                words = page.get_text("words")

                # Renderiza em alta resolução com a matriz de zoom
                matrix = pymupdf.Matrix(self.zoom_factor, self.zoom_factor)
                pix = page.get_pixmap(matrix=matrix, alpha=False)

                # Converte os pixels de PyMuPDF para QImage e depois QPixmap
                qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)

                # Cria o widget interativo da página
                page_widget = PDFPageWidget(
                    page_num=page_num,
                    pixmap=pixmap,
                    words=words,
                    zoom_factor=self.zoom_factor,
                    parent=self.scroll_content,
                )
                page_widget.setStyleSheet("background-color: white; border: 1px solid #CCCCCC;")

                # Sombra na página
                shadow = QGraphicsDropShadowEffect(page_widget)
                shadow.setBlurRadius(15)
                shadow.setColor(QColor(0, 0, 0, 80))
                shadow.setOffset(0, 4)
                page_widget.setGraphicsEffect(shadow)

                # Conecta evento de seleção para coordenar páginas
                page_widget.selection_started.connect(self._on_page_selection_started)

                self.page_widgets.append(page_widget)
                self.scroll_layout.addWidget(page_widget)

            # Restaura a posição da barra de rolagem
            self.scroll_area.verticalScrollBar().setValue(v_scroll)
            logging.info(f"PDF carregado e renderizado com sucesso: {len(self.doc)} página(s).")

        except Exception as e:
            logging.error(f"Erro ao renderizar PDF com PyMuPDF: {e}", exc_info=True)

    def zoom_in(self):
        if self.zoom_factor < 3.0:
            self.zoom_factor += 0.25
            self.lbl_zoom.setText(f"{int(self.zoom_factor * 100)}%")
            if self.pdf_file_path:
                self.load_pdf(self.pdf_file_path)

    def zoom_out(self):
        if self.zoom_factor > 0.5:
            self.zoom_factor -= 0.25
            self.lbl_zoom.setText(f"{int(self.zoom_factor * 100)}%")
            if self.pdf_file_path:
                self.load_pdf(self.pdf_file_path)

    def toggle_detach(self):
        """Alterna entre modo acoplado e janela destacada."""
        if self.is_detached:
            self.reattach_requested.emit()
        else:
            self.detach_requested.emit()

    def set_detached_state(self, detached: bool):
        """Atualiza o estado visual do botão."""
        self.is_detached = detached
        if detached:
            self.btn_detach.setText("🔗 Acoplar de Volta")
            self.btn_detach.setToolTip("Retornar o visualizador de PDF para dentro da janela principal")
        else:
            self.btn_detach.setText("↗️ Destacar Janela (2º Monitor)")
            self.btn_detach.setToolTip("Destacar o visualizador de PDF para usar em outro monitor ou janela")
