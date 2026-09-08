# 📘 Manual de Instalação e Uso — MK Writer

**MK Writer** é um editor e compilador acadêmico modular de Markdown para PDF com suporte nativo às normas **ABNT**, modelos acadêmicos estruturados, pré-visualização em tempo real e assistente de IA integrado.

---

## 📋 Requisitos de Sistema

- **Sistema Operacional**: Linux (Ubuntu 20.04+, Debian 11+, Fedora 34+, Arch Linux ou derivados)
- **Espaço em Disco**: 250 MB livres
- **Ferramenta de PDF (Opcional, porém recomendada)**: `pandoc` e `weasyprint` para geração de documentos PDF.

---

## ⚡ Método 1: Instalação Rápida (Executável Portátil — Recomendado)

Este método **não requer a instalação manual do Python** nem de bibliotecas adicionais na máquina de destino.

### 1. Obter o Pacote
Baixe ou copie o arquivo **`MK-Writer-Linux.tar.gz`** para o computador de destino.

### 2. Extrair o Arquivo
Abra o terminal no diretório onde o arquivo foi salvo e execute:

```bash
tar -xzvf MK-Writer-Linux.tar.gz
cd MK-Writer
```

### 3. Instalar o Atalho no Sistema (Automático)
Para criar o ícone no menu de aplicativos e na Área de Trabalho:

```bash
./instalar_atalho.sh
```

### 4. Executar o Programa
Você pode abrir o aplicativo de duas formas:
- **Pelo Menu do Sistema**: Pesquise por **MK Writer** no menu de aplicativos (ou tecla `Super`/`Windows`).
- **Pelo Terminal**:
  ```bash
  ./MK-Writer
  ```

---

## 📦 Método 2: Instalação a partir do Código Fonte (Desenvolvedores)

Se você deseja rodar a aplicação diretamente pelo código-fonte Python:

### 1. Clonar ou Baixar o Repositório
```bash
git clone https://github.com/seu-usuario/LatexMDown.git
cd LatexMDown
```

### 2. Criar e Ativar o Ambiente Virtual Python
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar as Dependências do Python
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Instalar Atalho no Sistema
```bash
python3 install_shortcut.py
```

### 5. Iniciar o Aplicativo
```bash
python3 main.py
```

---

## 📦 Formato de Pacote de Arquivo Único (.mkw)

O MK Writer introduz o formato de documento acadêmico **`.mkw`** (e suporte a `.mkdoc`), funcionando similarmente a arquivos `.odt` (LibreOffice) e `.docx` (Word). Em vez de manter dezenas de pastas e arquivos `.md`, referências `.bib`, regras de estilo e imagens soltas no computador:

- **Tudo em um só arquivo**: Capa, Resumo, Abstract, Sumário, Capítulos, Referências BibTeX, Imagens e Estilos ficam compactados de forma segura dentro do arquivo `.mkw`.
- **Abertura transparente**: Dê duplo clique em qualquer `.mkw` no gerenciador de arquivos (Nautilus/Dolphin) ou use `Arquivo -> Abrir Pacote (.mkw)...`. O MK Writer descompacta em cache local e recria toda a navegação modular na árvore de arquivos lateral.
- **Sincronização atômica ao salvar (`Ctrl+S`)**: Qualquer edição feita em qualquer arquivo do projeto é gravada e sincronizada instantaneamente para dentro do pacote `.mkw`, sem risco de perda ou corrupção de dados.
- **Atalhos Rápidos**:
  - `Ctrl + Shift + P`: Criar Novo Pacote ABNT (`.mkw`)
  - `Ctrl + Alt + O`: Abrir Pacote Existente (`.mkw` ou `.mkdoc`)
  - `Ctrl + S`: Salvar e Sincronizar Pacote
  - `Arquivo -> Empacotar Pasta Atual em (.mkw)...`: Converte qualquer pasta de trabalho existente em um pacote único com 1 clique.

---

## 📑 Instalação das Ferramentas Externas de PDF

Para gerar PDFs com formatação acadêmica perfeita (ABNT), é recomendado ter o **Pandoc** e/ou **WeasyPrint** instalados no sistema operacional.

### Ubuntu / Debian / Linux Mint
```bash
sudo apt update
sudo apt install -y pandoc weasyprint
```

### Fedora / RHEL
```bash
sudo dnf install -y pandoc weasyprint
```

### Arch Linux / Manjaro
```bash
sudo pacman -S pandoc weasyprint
```

---

## 🛠️ Solução de Problemas (Troubleshooting)

### 1. Permissão Negada ao Executar (`Permission Denied`)
Caso o sistema informe que não tem permissão para rodar o arquivo executável ou o script de instalação, execute no terminal:
```bash
chmod +x MK-Writer instalar_atalho.sh
```

### 2. O atalho não aparece na Área de Trabalho
Em algumas versões do GNOME (como no Ubuntu padrão), a Área de Trabalho não exibe ícones por padrão a menos que a extensão de ícones esteja ativada.
- O atalho estará sempre disponível no **Menu de Aplicativos** (pesquise por "MK Writer").

### 3. Aviso "Pandoc não encontrado" ao iniciar
O aplicativo abrirá normalmente mesmo sem o Pandoc, mas para compilar arquivos `.md` em `.pdf`, instale o Pandoc conforme a seção *Instalação das Ferramentas Externas de PDF*.

---

## 👥 Créditos & Desenvolvimento

- **Autor & Idealizador**: Danilo
- **Co-Desenvolvedor**: Antigravity AI (Google DeepMind)
- **Versão**: 1.0.0
- **Licença**: MIT
