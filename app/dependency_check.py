import os
import shutil
import sys


def check_python_dependencies():
    """
    Verifica se as bibliotecas Python necessárias (PyQt5, PyQtWebEngine) estão instaladas.
    Retorna (sucesso, lista_de_faltantes, mensagem_formatada).
    """
    missing = []
    try:
        import PyQt5
    except ImportError:
        missing.append("PyQt5 (pip install PyQt5)")

    try:
        import PyQt5.QtWebEngineWidgets
    except ImportError:
        missing.append("PyQtWebEngine (pip install PyQtWebEngine)")

    try:
        import pymupdf
    except ImportError:
        missing.append("PyMuPDF (pip install pymupdf)")

    if missing:
        msg = "As seguintes dependências do Python não foram encontradas:\n\n"
        for item in missing:
            msg += f" • {item}\n"
        msg += "\nPor favor, instale-as para executar a aplicação."
        return False, missing, msg
    
    return True, [], "Todas as dependências Python estão instaladas."


def find_pandoc_executable():
    """
    Tenta encontrar o executável do Pandoc via PATH do sistema ou via pypandoc.
    Retorna o caminho do executável ou None se não for encontrado.
    """
    # 1. Tenta encontrar no PATH
    pandoc_path = shutil.which("pandoc")
    if pandoc_path:
        return pandoc_path

    # 2. Tenta obter via pypandoc / pypandoc_binary se disponível
    try:
        import pypandoc
        path = pypandoc.get_pandoc_path()
        if os.path.exists(path):
            return path
    except Exception:
        pass

    return None


def find_pdf_engine():
    """
    Procura por uma engine de PDF compatível com Pandoc (weasyprint, typst, pdflatex, xelatex, lualatex, typst, etc).
    Retorna (engine_name, engine_path_or_command) ou (None, None).
    """
    # Ordem de preferência para engines leves e eficientes
    engines = ["weasyprint", "typst", "xelatex", "pdflatex", "lualatex", "wkhtmltopdf"]

    # Adiciona diretório bin do venv atual ao PATH caso esteja rodando em venv
    env_path = os.environ.get("PATH", "")
    sys_venv_bin = os.path.join(sys.prefix, "bin")
    if os.path.exists(sys_venv_bin) and sys_venv_bin not in env_path:
        env_path = sys_venv_bin + os.path.pathsep + env_path

    for eng in engines:
        cmd = shutil.which(eng, path=env_path)
        if cmd:
            return eng, cmd

    return None, None


def check_external_dependencies():
    """
    Verifica se o Pandoc e uma engine de PDF estão instalados.
    Retorna (sucesso, dict_com_informacoes).
    """
    pandoc_bin = find_pandoc_executable()
    pdf_engine, engine_path = find_pdf_engine()

    missing = []
    if not pandoc_bin:
        missing.append("Pandoc não encontrado. Instale via repositório de pacotes (ex: 'sudo apt install pandoc') ou via 'pip install pypandoc_binary'.")
    if not pdf_engine:
        missing.append("Engine de renderização de PDF não encontrada. Recomenda-se instalar 'weasyprint' ('pip install weasyprint') ou 'typst' ('pip install typst').")

    if missing:
        msg = "Algumas ferramentas externas necessárias estão ausentes:\n\n"
        for item in missing:
            msg += f" • {item}\n"
        return False, {
            "pandoc": pandoc_bin,
            "engine": pdf_engine,
            "engine_path": engine_path,
            "missing": missing,
            "message": msg
        }

    return True, {
        "pandoc": pandoc_bin,
        "engine": pdf_engine,
        "engine_path": engine_path,
        "missing": [],
        "message": f"Pandoc ({pandoc_bin}) e Engine ({pdf_engine}) encontrados com sucesso."
    }
