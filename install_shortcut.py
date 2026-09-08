#!/usr/bin/env python3
import os
import subprocess
import sys
from PyQt5.QtCore import QRectF, Qt
from PyQt5.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PyQt5.QtWidgets import QApplication

_app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()


def create_app_icon(size: int = 512) -> QPixmap:
    """
    Gera o ícone oficial da mão com a caneta sobre o fundo azul real arredondado.
    Este ícone é utilizado tanto para o aplicativo MK Writer quanto para os arquivos .mkw / .mkdoc.
    """
    global _app

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Fundo Quadrado Arredondado com Gradiente Azul Real
    path = QPainterPath()
    path.addRoundedRect(QRectF(16, 16, size - 32, size - 32), 96, 96)

    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, QColor("#1E3A8A"))  # Dark Blue
    gradient.setColorAt(0.5, QColor("#2563EB"))  # Royal Blue
    gradient.setColorAt(1.0, QColor("#3B82F6"))  # Light Blue

    painter.fillPath(path, gradient)

    # Borda sutil de destaque
    pen = QPen(QColor(255, 255, 255, 70))
    pen.setWidth(6)
    painter.setPen(pen)
    painter.drawPath(path)

    # Desenha a mão com a caneta ✍️
    font = QFont("Sans Serif", int(size * 0.42), QFont.Bold)
    painter.setFont(font)
    painter.setPen(QColor("#FFFFFF"))
    painter.drawText(QRectF(0, 0, size, size - 20), Qt.AlignCenter, "✍️")

    painter.end()
    return pixmap


def install_theme_icons(project_dir: str):
    """
    Instala o ícone da mão com a caneta azul em todas as resoluções (16x16 até 512x512)
    tanto para o aplicativo (apps) quanto para os arquivos .mkw (mimetypes).
    Instala em hicolor, Yaru e nos temas ativos do usuário para compatibilidade máxima com GNOME/Nautilus.
    """
    sizes = [16, 24, 32, 48, 64, 128, 256, 512]

    # Gera pixmap mestre
    app_pixmap = create_app_icon(512)

    # Salva cópia local em resources/
    res_dir = os.path.join(project_dir, "resources")
    os.makedirs(res_dir, exist_ok=True)
    app_pixmap.save(os.path.join(res_dir, "icon.png"), "PNG")
    app_pixmap.save(os.path.join(res_dir, "document_icon.png"), "PNG")

    theme_roots = [
        os.path.expanduser("~/.local/share/icons/hicolor"),
        os.path.expanduser("~/.local/share/icons/Yaru"),
        os.path.expanduser("~/.local/share/icons/Yaru-prussiangreen-dark"),
    ]

    for root in theme_roots:
        for sz in sizes:
            app_sz_dir = os.path.join(root, f"{sz}x{sz}", "apps")
            mime_sz_dir = os.path.join(root, f"{sz}x{sz}", "mimetypes")
            os.makedirs(app_sz_dir, exist_ok=True)
            os.makedirs(mime_sz_dir, exist_ok=True)

            scaled = app_pixmap.scaled(sz, sz, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Ícone do lançador
            scaled.save(os.path.join(app_sz_dir, "mk-writer.png"), "PNG")

            # Ícone do tipo de arquivo (.mkw)
            scaled.save(os.path.join(mime_sz_dir, "application-x-mk-writer.png"), "PNG")
            scaled.save(os.path.join(mime_sz_dir, "mk-writer.png"), "PNG")
            scaled.save(os.path.join(mime_sz_dir, "x-mk-writer.png"), "PNG")

    print("✅ Ícone da caneta azul instalado para arquivos .mkw e aplicativo em todas as resoluções!")

    # Atualiza caches do GTK
    for root in theme_roots:
        if os.path.isdir(root):
            for cmd in ["gtk-update-icon-cache", "gtk4-update-icon-cache"]:
                try:
                    subprocess.run([cmd, "-f", "-t", root], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    break
                except Exception:
                    pass


def register_mime_type():
    """Registra a associação de arquivos .mkw e .mkdoc para o MK Writer no sistema Linux."""
    mime_packages_dir = os.path.expanduser("~/.local/share/mime/packages")
    os.makedirs(mime_packages_dir, exist_ok=True)
    xml_path = os.path.join(mime_packages_dir, "mk-writer.xml")

    # IMPORTANTE: Sem generic-icon para não sofrer sobrescrita de temas com x-office-document genérico
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/x-mk-writer">
    <comment>Documento MK Writer</comment>
    <comment xml:lang="pt_BR">Documento MK Writer</comment>
    <glob pattern="*.mkw"/>
    <glob pattern="*.mkdoc"/>
    <icon name="application-x-mk-writer"/>
  </mime-type>
</mime-info>
"""
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    try:
        subprocess.run(
            ["update-mime-database", os.path.expanduser("~/.local/share/mime")],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("✅ Base de tipos MIME atualizada com sucesso")
    except Exception:
        pass


def install_desktop_shortcut():
    project_dir = os.path.abspath(os.path.dirname(__file__))
    main_py_path = os.path.join(project_dir, "main.py")
    python_venv = os.path.join(project_dir, "venv", "bin", "python3")

    # 1. Instala ícones
    install_theme_icons(project_dir)

    # 2. Registra tipo MIME
    register_mime_type()

    # 3. Conteúdo do arquivo .desktop
    desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=MK Writer
GenericName=Editor & Compilador Acadêmico Markdown
Comment=Editor Markdown com compilação PDF ABNT em tempo real
Exec={python_venv} {main_py_path} %f
Path={project_dir}
Icon=mk-writer
Terminal=false
Categories=Office;Development;Documentation;
StartupWMClass=MK Writer
MimeType=application/x-mk-writer;text/markdown;
Keywords=markdown;pdf;latex;abnt;editor;writer;mkw;mkdoc;
"""

    # Locais de instalação
    applications_dir = os.path.expanduser("~/.local/share/applications")
    os.makedirs(applications_dir, exist_ok=True)
    
    desktop_file_path = os.path.join(applications_dir, "mk-writer.desktop")

    with open(desktop_file_path, "w", encoding="utf-8") as f:
        f.write(desktop_content)

    os.chmod(desktop_file_path, 0o755)
    print(f"✅ Atalho instalado com sucesso em: {desktop_file_path}")

    # Define o MK Writer como o aplicativo padrão para abrir arquivos .mkw e .mkdoc
    for cmd in [
        ["gio", "mime", "application/x-mk-writer", "mk-writer.desktop"],
        ["xdg-mime", "default", "mk-writer.desktop", "application/x-mk-writer"],
    ]:
        try:
            subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    print("✅ MK Writer configurado como aplicativo padrão para arquivos .mkw")

    # Copia para Área de Trabalho se existir
    desktop_folder = os.path.expanduser("~/Área de Trabalho")
    if not os.path.exists(desktop_folder):
        desktop_folder = os.path.expanduser("~/Desktop")

    if os.path.exists(desktop_folder):
        target_desktop = os.path.join(desktop_folder, "MK-Writer.desktop")
        with open(target_desktop, "w", encoding="utf-8") as f:
            f.write(desktop_content)
        os.chmod(target_desktop, 0o755)
        print(f"✅ Atalho criado na Área de Trabalho: {target_desktop}")

    # Reinicia o Nautilus para limpar o cache de ícones em memória
    try:
        subprocess.run(["nautilus", "-q"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


if __name__ == "__main__":
    install_desktop_shortcut()
