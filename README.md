<div align="center">

# 📘 MK Writer
### Editor & Compilador Acadêmico Modular de Markdown para PDF

<p align="center">
  Uma ferramenta integrada para escrita científica, dissertações e relatórios técnicos em Markdown com compilação direta para PDF nas normas ABNT e modelos institucionais.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/GUI-PyQt5%20%26%20WebEngine-green?logo=qt&logoColor=white" alt="PyQt5">
  <img src="https://img.shields.io/badge/Compiler-Pandoc%20%2B%20WeasyPrint-purple" alt="Pandoc and WeasyPrint">
  <img src="https://img.shields.io/badge/Normas-ABNT%20%2F%20IFF-red" alt="ABNT">
  <img src="https://img.shields.io/badge/Platform-Linux%20%7C%20Windows-blue?logo=linux&logoColor=white" alt="Platform: Linux and Windows">
  <img src="https://img.shields.io/badge/License-MIT-teal" alt="License MIT">
</p>

</div>

---

## 🌟 Visão Geral

O **MK Writer** foi desenvolvido para preencher a lacuna entre a simplicidade do Markdown e o rigor de diagramação exigido por normas acadêmicas como a **ABNT** e universidades/instituições de pós-graduação.

Em vez de lidar com a curva de aprendizado íngreme e configurações complexas do LaTeX clássico ou as instabilidades de formatação do Microsoft Word/LibreOffice, o pesquisador escreve em Markdown puro e o **MK Writer** cuida da estruturação, numeração, referências bibliográficas e compilação do PDF final.

---

## 🚀 Principais Funcionalidades

### 1. ✍️ Editor Markdown Modular & Focado
* **Estrutura Acadêmica**: Organização automática em seções **Pré-Textuais** (Capa, Folha de Rosto, Resumo), **Textuais** (Introdução, Metodologia, Resultados) e **Pós-Textuais** (Referências, Anexos).
* **Pacotes de Projeto (`.mkw`)**: Formato exclusivo que encapsula todos os capítulos, imagens, estilos e base bibliográfica em um único arquivo portátil.

### 2. 📄 Compilação Acadêmica ABNT
* **Citações e Referências Automáticas**: Integração nativa com arquivos BibTeX (`.bib`) e regras da ABNT (`abnt.csl`).
* **Sumário Inteligente**: Geração automática de sumário dinâmico e paginação conforme as normas institucionais.
* **Centralização de Elementos**: Ajuste automático de figuras, tabelas, equações matemáticas e fontes.

### 3. 👁️ Pré-Visualizador PDF em Tempo Real
* Renderização direta na tela lado a lado com o editor através do motor **PyQtWebEngine**.
* Suporte a navegação rápida por páginas, ajuste de zoom e recarregamento automático após compilação.

### 4. 🧰 Barra de Ferramentas Acadêmica
* Atalhos de inserção com um clique para:
  * Equações matemáticas em formato LaTeX/MathJax.
  * Inserção e importação de figuras com legenda e fonte obrigatória da ABNT.
  * Tabelas formatadas e notas de rodapé.
  * Citações diretas e indiretas.

### 5. 🤖 Assistente de IA Integrado
* Módulo de apoio à escrita acadêmica para revisão gramatical, aprimoramento de estilo científico e sugestões de transição textual.

---

## 🛠️ Instalação e Execução

### Opção 1: Executável Portátil para Windows (.exe)

O **MK Writer** pode ser executado diretamente no **Windows 10 ou 11** sem necessidade de instalar Python:

1. Acesse a aba [Releases](https://github.com/dbarcelospro/MK-Writer/releases) (ou [Actions](https://github.com/dbarcelospro/MK-Writer/actions)) e baixe o arquivo:
   ```text
   MK-Writer-Windows.zip
   ```
2. Clique com o botão direito no arquivo baixado e escolha **"Extrair Tudo..."**.
3. Abra a pasta extraída e dê um duplo clique em **`MK-Writer.exe`**.

---

### Opção 2: Instalação Automática no Linux (Recomendado)

O repositório inclui um instalador completo com suporte a temas de ícones e registro no menu do sistema:

```bash
git clone https://github.com/dbarcelospro/MK-Writer.git
cd MK-Writer
./instalar_atalho.sh
```

Isso registrará o **MK Writer** no seu menu de aplicativos (Dash/GNOME/KDE) e associará automaticamente os arquivos de extensão **`.mkw`** ao programa.

---

### Opção 3: Execução pelo Código-Fonte (Python no Linux ou Windows)

#### 1. Pré-requisitos de Sistema
Para compilação de PDFs via Pandoc e WeasyPrint:
```bash
sudo apt update
sudo apt install -y pandoc weasyprint
```

#### 2. Configurar o Ambiente Virtual
```bash
git clone https://github.com/dbarcelospro/MK-Writer.git
cd MK-Writer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 3. Iniciar o Aplicativo
```bash
python main.py
```

---

## 📁 Estrutura do Projeto

```text
MK-Writer/
├── main.py                     # Ponto de entrada e inicialização da aplicação
├── app/                        # Módulos centrais do editor e visualizador
│   ├── main_window.py          # Janela principal e coordenação da interface
│   ├── editor.py               # Editor com realce de sintaxe e numeração
│   ├── compiler.py             # Motor de compilação Pandoc/WeasyPrint/ABNT
│   ├── pdf_viewer.py           # Visualizador de PDF integrado via WebEngine
│   ├── formatting_toolbar.py   # Barra de ferramentas e atalhos rápidos
│   ├── file_tree.py            # Árvore de navegação e arquivos de projeto
│   ├── package_manager.py      # Gerenciamento de pacotes .mkw
│   └── ai_assistant.py         # Módulo do assistente de inteligência artificial
├── resources/                  # Estilos, ícones, regras ABNT e modelos
│   ├── abnt.csl                # Estilo oficial de citação ABNT
│   ├── style.md                # Folha de estilo de diagramação CSS/Markdown
│   ├── template.md             # Modelo estrutural de artigo/monografia
│   └── toc.lua                 # Filtro Lua para geração de sumário ABNT
├── Imagens/                    # Ativos gráficos institucionais (SVG)
├── tests/                      # Bateria de testes automatizados do sistema
├── requirements.txt            # Dependências em Python
├── MANUAL_DE_INSTALACAO.md     # Guia completo offline de uso e configuração
├── CONTRIBUTING.md              # Guia para novos colaboradores
└── LICENSE                     # Licença de código aberto MIT
```

---

## 🤝 Como Contribuir

Contribuições para o **MK Writer** são muito bem-vindas! Consulte o arquivo [CONTRIBUTING.md](CONTRIBUTING.md) para diretrizes sobre como relatar problemas, propor melhorias em regras de formatação e enviar *Pull Requests*.

---

## 👤 Autor

* **Danilo Barcelos** — *Idealizador e Desenvolvedor Principal*  
  Concepção do ambiente de escrita modular, modelagem das regras ABNT e desenvolvimento da arquitetura do software.

---

## 📄 Licença

Este projeto está licenciado sob a **MIT License** — consulte o arquivo [LICENSE](LICENSE) para mais detalhes. Livre para utilização pessoal, acadêmica e profissional.
