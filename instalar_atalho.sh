#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPLICATIONS_DIR="$HOME/.local/share/applications"
MIME_PACKAGES="$HOME/.local/share/mime/packages"

mkdir -p "$APPLICATIONS_DIR" "$MIME_PACKAGES"

# 1. Encontra os executáveis e ícones
if [ -f "$DIR/MK-Writer" ]; then
    EXEC_PATH="$DIR/MK-Writer"
    ICON_SRC="$DIR/_internal/resources/icon.png"
elif [ -f "$DIR/venv/bin/python3" ]; then
    EXEC_PATH="$DIR/venv/bin/python3 $DIR/main.py"
    ICON_SRC="$DIR/resources/icon.png"
else
    EXEC_PATH="python3 $DIR/main.py"
    ICON_SRC="$DIR/resources/icon.png"
fi

# 2. Instala ícones no tema do sistema para o app e para os arquivos .mkw
THEME_ROOTS=(
    "$HOME/.local/share/icons/hicolor"
    "$HOME/.local/share/icons/Yaru"
    "$HOME/.local/share/icons/Yaru-prussiangreen-dark"
)

for ROOT in "${THEME_ROOTS[@]}"; do
    for SZ in 16 24 32 48 64 128 256 512; do
        mkdir -p "$ROOT/${SZ}x${SZ}/apps" "$ROOT/${SZ}x${SZ}/mimetypes"
        if [ -f "$ICON_SRC" ]; then
            cp "$ICON_SRC" "$ROOT/${SZ}x${SZ}/apps/mk-writer.png" 2>/dev/null || true
            cp "$ICON_SRC" "$ROOT/${SZ}x${SZ}/mimetypes/application-x-mk-writer.png" 2>/dev/null || true
            cp "$ICON_SRC" "$ROOT/${SZ}x${SZ}/mimetypes/mk-writer.png" 2>/dev/null || true
            cp "$ICON_SRC" "$ROOT/${SZ}x${SZ}/mimetypes/x-mk-writer.png" 2>/dev/null || true
        fi
    done

    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f -t "$ROOT" >/dev/null 2>&1 || true
    elif command -v gtk4-update-icon-cache >/dev/null 2>&1; then
        gtk4-update-icon-cache -f -t "$ROOT" >/dev/null 2>&1 || true
    fi
done

# 3. Registra tipo MIME para .mkw e .mkdoc sem generic-icon para não sofrer substituição
cat << 'EOF' > "$MIME_PACKAGES/mk-writer.xml"
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="application/x-mk-writer">
    <comment>Documento MK Writer</comment>
    <comment xml:lang="pt_BR">Documento MK Writer</comment>
    <glob pattern="*.mkw"/>
    <glob pattern="*.mkdoc"/>
    <icon name="application-x-mk-writer"/>
  </mime-type>
</mime-info>
EOF

if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database "$HOME/.local/share/mime" >/dev/null 2>&1 || true
fi

# 4. Cria arquivo .desktop
cat << EOF > "$APPLICATIONS_DIR/mk-writer.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=MK Writer
GenericName=Editor & Compilador Acadêmico Markdown
Comment=Editor Markdown com compilação PDF ABNT/IFF em tempo real
Exec=$EXEC_PATH %f
Path=$DIR
Icon=mk-writer
Terminal=false
Categories=Office;Development;Documentation;
StartupWMClass=MK Writer
MimeType=application/x-mk-writer;text/markdown;
Keywords=markdown;pdf;latex;abnt;editor;writer;mkw;mkdoc;
EOF

chmod +x "$APPLICATIONS_DIR/mk-writer.desktop"

# 5. Define como aplicativo padrão no sistema
if command -v gio >/dev/null 2>&1; then
    gio mime application/x-mk-writer mk-writer.desktop >/dev/null 2>&1 || true
fi
if command -v xdg-mime >/dev/null 2>&1; then
    xdg-mime default mk-writer.desktop application/x-mk-writer >/dev/null 2>&1 || true
fi

# Copia para Área de Trabalho se existir
DESKTOP_DIR="$HOME/Área de Trabalho"
[ ! -d "$DESKTOP_DIR" ] && DESKTOP_DIR="$HOME/Desktop"
if [ -d "$DESKTOP_DIR" ]; then
    cp "$APPLICATIONS_DIR/mk-writer.desktop" "$DESKTOP_DIR/MK-Writer.desktop"
    chmod +x "$DESKTOP_DIR/MK-Writer.desktop"
fi

# Reinicia Nautilus para atualizar os ícones
if command -v nautilus >/dev/null 2>&1; then
    nautilus -q >/dev/null 2>&1 || true
fi

echo "✅ Atalho do MK Writer e ícones de arquivo .mkw instalados com sucesso!"
