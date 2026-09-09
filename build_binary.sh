#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "🔨 Iniciando compilação do MK Writer para Linux..."

# 1. Ativa ou cria o venv se necessário
if [ ! -d "venv" ]; then
    echo "📦 Criando ambiente virtual venv..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "📦 Instalando dependências..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo "🚀 Compilando binário com PyInstaller..."
pyinstaller --noconfirm MK-Writer.spec

# Inclui script de instalação de atalho dentro da pasta distribuível
if [ -f "instalar_atalho.sh" ]; then
    cp instalar_atalho.sh dist/MK-Writer/
    chmod +x dist/MK-Writer/instalar_atalho.sh
fi

echo "📦 Compactando em MK-Writer-Linux.tar.gz..."
tar -czvf MK-Writer-Linux.tar.gz -C dist MK-Writer

echo ""
echo "✅ Compilação concluída com sucesso!"
echo "📁 Executável gerado em: dist/MK-Writer/MK-Writer"
echo "📦 Pacote compactado gerado em: MK-Writer-Linux.tar.gz"
