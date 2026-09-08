import logging
import os

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QColor, QImage, QPixmap
from PyQt5.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
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
        self.setWindowTitle("LatexMDown - Visualizador de PDF (Janela Separada / 2º Monitor)")
        self.resize(800, 950)

    def closeEvent(self, event: QCloseEvent):
        """Ao fechar a janela separada, avisa a janela principal para acoplar de volta."""
        self.closed_signal.emit()
        event.accept()


class PDFViewer(QWidget):
    """
    Componente visualizador de PDF ultra-estável e de alto desempenho baseado em PyMuPDF (fitz).
    Livre de dependências do Chromium/QtWebEngine para evitar travamentos de GPU/Wayland no Linux.
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

    def load_pdf(self, pdf_file_path: str):
        """Carrega e renderiza todas as páginas do PDF usando PyMuPDF (fitz)."""
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
            while self.scroll_layout.count():
                child = self.scroll_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            # Renderiza cada página do PDF
            for page_num in range(len(self.doc)):
                page = self.doc.load_page(page_num)

                # Renderiza em alta resolução com a matriz de zoom
                matrix = pymupdf.Matrix(self.zoom_factor, self.zoom_factor)
                pix = page.get_pixmap(matrix=matrix, alpha=False)

                # Converte os pixels de PyMuPDF para QImage e depois QPixmap
                qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)

                # Label da Página com sombra
                page_label = QLabel()
                page_label.setPixmap(pixmap)
                page_label.setFixedSize(pix.width, pix.height)
                page_label.setStyleSheet("background-color: white; border: 1px solid #CCCCCC;")

                # Sombra na página
                shadow = QGraphicsDropShadowEffect(self)
                shadow.setBlurRadius(15)
                shadow.setColor(QColor(0, 0, 0, 80))
                shadow.setOffset(0, 4)
                page_label.setGraphicsEffect(shadow)

                self.scroll_layout.addWidget(page_label)

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
