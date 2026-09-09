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


def get_app_search_paths():
    """
    Retorna lista de diretórios onde ferramentas portáteis estáticas (pandoc, weasyprint, etc)
    podem estar localizadas dentro do pacote da aplicação ou do ambiente.
    """
    paths = []
    # 1. Diretório do executável compilado (dist/MK-Writer)
    if sys.executable:
        app_dir = os.path.dirname(os.path.abspath(sys.executable))
        paths.extend([
            app_dir,
            os.path.join(app_dir, "_internal"),
            os.path.join(app_dir, "bin"),
            os.path.join(app_dir, "_internal", "bin"),
        ])

    # 2. Diretório temporário PyInstaller (se aplicável)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass and os.path.exists(meipass):
        paths.extend([meipass, os.path.join(meipass, "bin")])

    # 3. Diretório raiz do projeto
    proj_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths.extend([
        proj_dir,
        os.path.join(proj_dir, "bin"),
        os.path.join(proj_dir, "resources", "bin"),
    ])

    # 4. venv bin/Scripts
    if sys.prefix:
        paths.extend([
            os.path.join(sys.prefix, "bin"),
            os.path.join(sys.prefix, "Scripts"),
        ])

    seen = set()
    result = []
    for p in paths:
        if p and os.path.isdir(p):
            norm = os.path.normpath(p)
            if norm not in seen:
                seen.add(norm)
                result.append(norm)
    return result


def find_pandoc_executable():
    """
    Tenta encontrar o executável do Pandoc:
    1. No pacote portátil/estático local da aplicação
    2. No PATH do sistema
    3. Via pypandoc / pypandoc_binary se disponível
    """
    search_dirs = get_app_search_paths()
    names = ["pandoc.exe", "pandoc"] if sys.platform.startswith("win") else ["pandoc", "pandoc.exe"]

    # 1. Tenta encontrar dentro da pasta da aplicação (pacote estático)
    for sdir in search_dirs:
        for name in names:
            full_path = os.path.join(sdir, name)
            if os.path.isfile(full_path):
                if sys.platform.startswith("win") or os.access(full_path, os.X_OK):
                    return full_path

    # 2. Tenta encontrar no PATH do sistema
    pandoc_path = shutil.which("pandoc")
    if pandoc_path:
        return pandoc_path

    # 3. Tenta obter via pypandoc / pypandoc_binary se disponível
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
    Procura por uma engine de PDF compatível com Pandoc:
    1. No pacote portátil/estático local da aplicação (weasyprint.exe, typst.exe, etc)
    2. No PATH do sistema
    Retorna (engine_name, engine_path_or_command) ou (None, None).
    """
    engines = ["weasyprint", "typst", "xelatex", "pdflatex", "lualatex", "wkhtmltopdf"]
    exts = [".exe", ".bat", ".cmd", ""] if sys.platform.startswith("win") else ["", ".sh"]

    search_dirs = get_app_search_paths()

    # 1. Procura na pasta da aplicação (pacote estático)
    for eng in engines:
        for sdir in search_dirs:
            for ext in exts:
                cand = os.path.join(sdir, eng + ext)
                if os.path.isfile(cand):
                    if sys.platform.startswith("win") or os.access(cand, os.X_OK):
                        return eng, cand

    # 2. Procura no PATH do sistema (adicionando search_dirs como fallback)
    env_path = os.environ.get("PATH", "")
    for sdir in search_dirs:
        if sdir not in env_path:
            env_path = sdir + os.path.pathsep + env_path

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
