import time
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath
from PyQt5.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class MKSplashScreen(QWidget):
    """
    Tela de Splash (SplashScreen) moderna e profissional para o MK Writer.
    Apresenta design em Dark Slate, barra de progresso personalizada e mensagens de inicialização.
    """
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SplashScreen)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(540, 350)

        self.init_ui()
        self.center_on_screen()

    def init_ui(self):
        # Container Principal com Borda Arredondada
        self.container = QWidget(self)
        self.container.setGeometry(10, 10, 520, 330)
        self.container.setStyleSheet("""
            QWidget#SplashContainer {
                background-color: #0F172A;
                border: 1px solid #334155;
                border-radius: 14px;
            }
        """)
        self.container.setObjectName("SplashContainer")

        # Sombra suave em volta do container
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(36, 28, 36, 24)

        # ── ÍCONE / BADGE ──
        badge_label = QLabel("✍️", self.container)
        badge_label.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2563EB, stop:1 #3B82F6);
            border-radius: 12px;
            font-size: 26pt;
            padding: 8px;
        """)
        badge_label.setFixedSize(56, 56)
        badge_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(badge_label, 0, Qt.AlignCenter)

        layout.addSpacing(10)

        # ── TÍTULO DA APLICAÇÃO ──
        title_label = QLabel("MK Writer", self.container)
        title_label.setStyleSheet("color: #F8FAFC; font-size: 22pt; font-weight: 800; letter-spacing: 1px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # ── SUBTÍTULO ──
        sub_label = QLabel("Editor & Compilador Acadêmico Markdown", self.container)
        sub_label.setStyleSheet("color: #94A3B8; font-size: 10pt; font-weight: 500;")
        sub_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(sub_label)

        # ── CRÉDITOS DE DESENVOLVIMENTO ──
        dev_label = QLabel("Desenvolvido por <b>Danilo</b> & <b>Antigravity AI</b>", self.container)
        dev_label.setStyleSheet("color: #38BDF8; font-size: 9pt; margin-top: 4px;")
        dev_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(dev_label)

        layout.addStretch()

        # ── BARRA DE PROGRESSO ──
        self.progress_bar = QProgressBar(self.container)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1E293B;
                border: none;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #60A5FA);
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)

        layout.addSpacing(8)

        # ── MENSAGEM DE STATUS & VERSÃO ──
        bottom_widget = QWidget(self.container)
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(2)

        self.status_label = QLabel("Iniciando MK Writer...", self.container)
        self.status_label.setStyleSheet("color: #64748B; font-size: 8.5pt; font-weight: 500;")
        self.status_label.setAlignment(Qt.AlignCenter)
        bottom_layout.addWidget(self.status_label)

        ver_label = QLabel("v1.0.0 • Padrão ABNT", self.container)
        ver_label.setStyleSheet("color: #475569; font-size: 7.5pt;")
        ver_label.setAlignment(Qt.AlignCenter)
        bottom_layout.addWidget(ver_label)

        layout.addWidget(bottom_widget)

    def set_progress(self, value: int, message: str = None):
        """Atualiza o progresso e a mensagem de status da inicialização."""
        self.progress_bar.setValue(value)
        if message:
            self.status_label.setText(message)
        QApplication.processEvents()

    def center_on_screen(self):
        """Centraliza a janela de splash no centro da tela principal."""
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            y = (geo.height() - self.height()) // 2
            self.move(x, y)
