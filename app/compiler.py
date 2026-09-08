import os
import subprocess
import sys
import tempfile
import time
from PyQt5.QtCore import QThread, pyqtSignal

from app.dependency_check import find_pandoc_executable, find_pdf_engine


def find_image_file(src: str, base_dir: str, project_root: str = None) -> str | None:
    """
    Localiza o caminho absoluto de um arquivo de imagem referenciado no Markdown/HTML.
    Busca no diretório base (base_dir), na raiz do projeto (project_root)
    e na pasta 'Imagens/' em ambas as localizações ou seus ancestrais.
    """
    if not src or src.startswith(("http://", "https://", "data:", "file://")):
        return None

    clean_src = src.split("?")[0].split("#")[0].strip("<>")
    if os.path.isabs(clean_src) and os.path.exists(clean_src):
        return clean_src

    candidates = []
    if base_dir:
        candidates.append(os.path.abspath(os.path.join(base_dir, clean_src)))
    if project_root:
        candidates.append(os.path.abspath(os.path.join(project_root, clean_src)))

    img_filename = os.path.basename(clean_src)
    if project_root:
        candidates.append(os.path.abspath(os.path.join(project_root, "Imagens", img_filename)))
    if base_dir:
        candidates.append(os.path.abspath(os.path.join(base_dir, "Imagens", img_filename)))
        curr = os.path.abspath(base_dir)
        for _ in range(5):
            parent = os.path.dirname(curr)
            if parent == curr:
                break
            candidates.append(os.path.abspath(os.path.join(parent, clean_src)))
            candidates.append(os.path.abspath(os.path.join(parent, "Imagens", img_filename)))
            curr = parent

    for cand in candidates:
        if os.path.isfile(cand):
            return cand

    return None


def resolve_image_paths(markdown_text: str, base_dir: str, project_root: str = None) -> str:
    """
    Substitui os caminhos relativos de imagem em Markdown e HTML por seus caminhos absolutos no disco,
    garantindo compilação sem falhas no WeasyPrint independente do diretório de execução.
    """
    import re

    def md_img_repl(match):
        alt = match.group(1)
        body = match.group(2).strip()
        parts = body.split(maxsplit=1)
        src = parts[0] if parts else ""
        rest = (" " + parts[1]) if len(parts) > 1 else ""
        found = find_image_file(src, base_dir, project_root)
        if found:
            return f"![{alt}]({found}{rest})"
        return match.group(0)

    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', md_img_repl, markdown_text)

    def html_img_repl(match):
        before = match.group(1)
        src = match.group(2)
        after = match.group(3)
        found = find_image_file(src, base_dir, project_root)
        if found:
            return f'<img {before}src="{found}"{after}>'
        return match.group(0)

    text = re.sub(r'<img\s+([^>]*?)src=["\']([^"\']+)["\']([^>]*?)>', html_img_repl, text, flags=re.IGNORECASE)
    return text


def resolve_includes(text: str, base_dir: str, depth: int = 0, visited: set = None, project_root: str = None) -> str:
    """
    Resolve recursivamente instruções de inclusão modular de arquivos Markdown:
    Exemplo: !include Pre_Textual/01_capa.md
             !include style.md
             <!-- include Textual/01_introducao.md -->
    Busca o arquivo relativo ao diretório atual (base_dir), ao diretório raiz do projeto (project_root)
    e aos diretórios ancestrais (subindo nas pastas pais), permitindo que arquivos em subpastas
    (como 02_Textual/01_introducao.md) incluam arquivos da raiz (como style.md) sem precisar de '../'.
    Evita loops de inclusão circular/duplicada rastreando os caminhos canônicos visitados.
    """
    if visited is None:
        visited = set()

    if depth > 10:
        return text

    lines = text.splitlines()
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("!include ") or (stripped.startswith("<!-- include ") and stripped.endswith("-->")):
            path_str = stripped.replace("!include ", "").replace("<!-- include ", "").replace("-->", "").strip()

            found_path = None
            # 1. Procura primeiro relativo ao diretório base (pasta do arquivo atual)
            direct_path = os.path.abspath(os.path.join(base_dir, path_str))
            if os.path.exists(direct_path):
                found_path = direct_path
            # 2. Se project_root foi fornecido, procura na raiz do projeto
            elif project_root:
                root_path = os.path.abspath(os.path.join(project_root, path_str))
                if os.path.exists(root_path):
                    found_path = root_path

            # 3. Se ainda não encontrou, busca subindo nos diretórios ancestrais de base_dir
            if not found_path:
                curr = os.path.abspath(base_dir)
                for _ in range(5):
                    parent = os.path.dirname(curr)
                    if parent == curr:
                        break
                    candidate = os.path.abspath(os.path.join(parent, path_str))
                    if os.path.exists(candidate):
                        found_path = candidate
                        break
                    curr = parent

            if found_path:
                inc_path = found_path
                if inc_path in visited:
                    new_lines.append(f"\n\n<!-- Ignorado include duplicado/circular: {path_str} -->\n\n")
                    continue

                try:
                    visited.add(inc_path)
                    with open(inc_path, "r", encoding="utf-8") as f_inc:
                        inc_content = f_inc.read()
                    inc_dir = os.path.dirname(inc_path)
                    inc_content = resolve_image_paths(inc_content, base_dir=inc_dir, project_root=project_root)
                    inc_content_resolved = resolve_includes(
                        inc_content,
                        inc_dir,
                        depth + 1,
                        visited,
                        project_root=project_root
                    )
                    # Garante isolamento estrito com quebras de linha duplas antes e depois
                    new_lines.append(f"\n\n{inc_content_resolved.strip()}\n\n")
                except Exception as e:
                    new_lines.append(f"\n\n<!-- Erro ao ler include {path_str}: {str(e)} -->\n\n")
            else:
                new_lines.append(f"\n\n<!-- Erro: Arquivo de include não encontrado: {path_str} -->\n\n")
        else:
            new_lines.append(line)

    return "\n".join(new_lines)


def find_bibliography_file(working_dir: str, markdown_text: str = "") -> str | None:
    """
    Localiza arquivo de referências (.bib) especificado no documento,
    no diretório de trabalho ou em seus diretórios ancestrais.
    """
    import re
    m = re.search(r'^bibliography:\s*["\']?([^"\'\r\n]+)["\']?', markdown_text, re.MULTILINE)
    if m:
        bib_rel = m.group(1).strip()
        candidate = os.path.abspath(os.path.join(working_dir, bib_rel))
        if os.path.isfile(candidate):
            return candidate

    curr = os.path.abspath(working_dir)
    for _ in range(4):
        for std in ["referencias.bib", "references.bib", "bibliografia.bib"]:
            p = os.path.join(curr, std)
            if os.path.isfile(p):
                return p
        try:
            for fname in os.listdir(curr):
                if fname.endswith(".bib"):
                    return os.path.join(curr, fname)
        except OSError:
            pass
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent

    return None


def find_csl_file(working_dir: str, markdown_text: str = "") -> str | None:
    """
    Localiza arquivo de estilo CSL (ex: ABNT) no documento, na pasta resources ou ancestrais.
    """
    import re
    m = re.search(r'^csl:\s*["\']?([^"\'\r\n]+)["\']?', markdown_text, re.MULTILINE)
    if m:
        csl_rel = m.group(1).strip()
        candidate = os.path.abspath(os.path.join(working_dir, csl_rel))
        if os.path.isfile(candidate):
            return candidate

    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    res_csl = os.path.join(base_path, "resources", "abnt.csl")
    if os.path.isfile(res_csl):
        return res_csl

    curr = os.path.abspath(working_dir)
    for _ in range(4):
        p = os.path.join(curr, "abnt.csl")
        if os.path.isfile(p):
            return p
        parent = os.path.dirname(curr)
        if parent == curr:
            break
        curr = parent

    return None


def find_toc_filter() -> str | None:
    """Localiza o filtro Lua do Sumário ABNT."""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    p = os.path.join(base_path, "resources", "toc.lua")
    return p if os.path.isfile(p) else None


def document_wants_bibliography(markdown_text: str) -> bool:
    """
    Verifica se o documento possui uma seção ou placeholder explícito para a bibliografia.
    Evita que páginas individuais (ex: capa, introdução) exibam a bibliografia no rodapé.
    """
    import re
    # 1. Placeholder do Pandoc ::: {#refs} ou <div id="refs">
    if re.search(r"\{#refs\}|id=[\"']refs[\"']", markdown_text, re.IGNORECASE):
        return True
    # 2. Cabeçalho de Referências ou Bibliografia
    if re.search(r"^#+\s+(REFERÊNCIAS|REFERENCIAS|BIBLIOGRAFIA)\b", markdown_text, re.IGNORECASE | re.MULTILINE):
        return True
    return False


def compile_markdown_to_pdf(
    markdown_text: str,
    custom_output_path: str = None,
    working_dir: str = None,
    main_file_path: str = None,
    project_root: str = None
) -> tuple[str | None, str, float]:
    """
    Função utilitária síncrona para compilação de Markdown para PDF com suporte a:
    - Inclusões modulares (!include)
    - Sumário ABNT via filtro Lua (toc.lua)
    - Citações e Bibliografia BibTeX (.bib) com estilos ABNT (abnt.csl)
    - Engine WeasyPrint com HTML e CSS milimétrico
    Retorna: (caminho_pdf_ou_None, mensagem_erro, tempo_segundos)
    """
    start_time = time.time()
    work_dir = working_dir or os.getcwd()

    pandoc_bin = find_pandoc_executable()
    pdf_engine, _ = find_pdf_engine()

    if not pandoc_bin:
        return None, "Erro: O executável do Pandoc não foi encontrado no sistema.", 0.0

    env = os.environ.copy()
    venv_bin = os.path.join(sys.prefix, "bin")
    if os.path.exists(venv_bin):
        env["PATH"] = venv_bin + os.path.pathsep + env.get("PATH", "")

    temp_md = None
    temp_pdf = None
    temp_meta = None

    try:
        initial_visited = set()
        if main_file_path:
            initial_visited.add(os.path.abspath(main_file_path))

        # Resolve arquivos inclusos (!include caminho/arquivo.md) antes de compilar
        processed_md = resolve_includes(
            markdown_text,
            work_dir,
            visited=initial_visited,
            project_root=project_root
        )

        # Normaliza caminhos de imagens em Markdown/HTML para absolutos
        processed_md = resolve_image_paths(
            processed_md,
            base_dir=work_dir,
            project_root=project_root
        )

        # Injeta regras de estilo universais (código, tabelas, figuras, listas e continuação de numeração)
        ol_start_rules = "\n".join(
            f"ol[start=\"{n}\"] {{ counter-reset: list-item {n-1} !important; }}\n"
            f"li[value=\"{n}\"] {{ counter-set: list-item {n} !important; }}"
            for n in range(1, 251)
        )

        code_css = f"""
<style>
/* Estilo retangular suave em cinza claro para blocos de código e terminal (text / code) */
pre, div.sourceCode {{
    background-color: #F6F8FA !important;
    color: #1F2328 !important;
    border-radius: 6px !important;
    padding: 10px 14px !important;
    margin: 1.2em 0 !important;
    font-family: "Consolas", "Courier New", "DejaVu Sans Mono", monospace !important;
    font-size: 9.5pt !important;
    line-height: 1.4 !important;
    border: 1px solid #D0D7DE !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    page-break-inside: avoid !important;
    break-inside: avoid !important;
    text-align: left !important;
    text-indent: 0 !important;
    white-space: pre-wrap !important;
    word-break: break-all !important;
}}
pre code, div.sourceCode code {{
    background-color: transparent !important;
    color: #1F2328 !important;
    padding: 0 !important;
    border: none !important;
    font-family: inherit !important;
    font-size: inherit !important;
}}
/* Realce de sintaxe em fundo claro */
.sourceCode .co {{ color: #57606A !important; font-style: italic !important; }}
.sourceCode .st {{ color: #0A3069 !important; font-weight: 500 !important; }}
.sourceCode .dv, .sourceCode .fl {{ color: #0550AE !important; }}
.sourceCode .kw {{ color: #CF222E !important; font-weight: bold !important; }}
.sourceCode .fu {{ color: #8250DF !important; }}
.sourceCode .op {{ color: #0550AE !important; }}
p code, li code {{
    background-color: #F1F5F9 !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 4px !important;
    padding: 1px 5px !important;
    font-family: "Consolas", "Courier New", monospace !important;
    font-size: 9.5pt !important;
}}
/* Alíneas ABNT: listas ordenadas aninhadas ou com letras usam estilo alfabético (a, b, c) */
ol ol, ol[type="a"], ol.alineas {{
    list-style-type: lower-alpha !important;
}}
/* Centralização automática e quebra fluida de tabelas entre páginas */
table {{
    display: table !important;
    margin-left: auto !important;
    margin-right: auto !important;
    margin-top: 1.5em !important;
    margin-bottom: 1.5em !important;
    border-collapse: collapse !important;
    page-break-inside: auto !important;
    break-inside: auto !important;
}}

tr {{
    page-break-inside: avoid !important;
    break-inside: avoid !important;
}}

thead {{
    display: table-header-group !important;
}}

tfoot {{
    display: table-footer-group !important;
}}

/* Centralização de Figuras, Imagens, Legendas e Fontes ABNT */
figure, div.figure, div.figura {{
    display: block !important;
    text-align: center !important;
    margin-left: auto !important;
    margin-right: auto !important;
    margin-top: 1.5em !important;
    margin-bottom: 1.5em !important;
    page-break-inside: avoid !important;
    break-inside: avoid !important;
}}

figure img, p img, img, .figura img {{
    display: block !important;
    margin-left: auto !important;
    margin-right: auto !important;
    max-width: 90% !important;
    height: auto !important;
    page-break-inside: avoid !important;
    break-inside: avoid !important;
}}

.capa img, .capa-topo img {{
    display: inline-block !important;
    margin: 0 !important;
}}

figcaption, .figura-titulo, .caption-titulo {{
    text-align: center !important;
    font-size: 10.5pt !important;
    font-weight: bold !important;
    margin-top: 0.5em !important;
    margin-bottom: 0.5em !important;
    text-indent: 0 !important;
}}

p:has(img) {{
    text-align: center !important;
    text-indent: 0 !important;
    margin-top: 1.5em !important;
    margin-bottom: 0.5em !important;
}}

p:has(img) small,
small,
.fonte,
p.fonte {{
    display: block !important;
    text-align: center !important;
    text-indent: 0 !important;
    font-size: 10pt !important;
    margin-top: 0.3em !important;
    margin-bottom: 1.5em !important;
}}

.figura p, div.figura p {{
    text-indent: 0 !important;
    text-align: center !important;
    margin: 0.3em auto !important;
}}

/* Listas com marcadores (ul) e numeradas (ol) ABNT: sem recuo indevido no texto do marcador */
ul, ol {{
    margin-top: 0.5em !important;
    margin-bottom: 0.5em !important;
    padding-left: 2em !important;
}}

li {{
    text-indent: 0 !important;
    margin-top: 0.25em !important;
    margin-bottom: 0.25em !important;
    line-height: 1.15 !important;
    text-align: justify !important;
}}

li > p, li p {{
    text-indent: 0 !important;
    margin: 0 !important;
    display: inline !important;
    line-height: inherit !important;
}}

/* Continuação automática de numeração para listas ordenadas interrompidas por parágrafos/questões */
{ol_start_rules}
</style>
"""
        processed_md = code_css + "\n" + processed_md

        # Salva o texto Markdown final em um arquivo temporário
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", encoding="utf-8", delete=False
        ) as f_md:
            f_md.write(processed_md)
            temp_md = f_md.name

        # Define o arquivo PDF de saída
        if custom_output_path:
            output_pdf = custom_output_path
        else:
            with tempfile.NamedTemporaryFile(
                suffix=".pdf", delete=False
            ) as f_pdf:
                temp_pdf = f_pdf.name
                output_pdf = temp_pdf

        # Monta caminhos de recursos para imagens e includes
        res_dirs = [".", work_dir]
        if project_root and os.path.isdir(project_root):
            res_dirs.append(project_root)
            img_cand = os.path.join(project_root, "Imagens")
            if os.path.isdir(img_cand):
                res_dirs.append(img_cand)

        curr_res = os.path.abspath(work_dir)
        for _ in range(5):
            parent_res = os.path.dirname(curr_res)
            if parent_res == curr_res:
                break
            res_dirs.append(parent_res)
            img_parent = os.path.join(parent_res, "Imagens")
            if os.path.isdir(img_parent):
                res_dirs.append(img_parent)
            curr_res = parent_res

        unique_res = []
        seen_res = set()
        for d in res_dirs:
            if d not in seen_res:
                seen_res.add(d)
                unique_res.append(d)

        cmd = [
            pandoc_bin,
            "-f", "markdown+raw_html+markdown_in_html_blocks",
            temp_md,
            "-o", output_pdf,
            f"--resource-path={':'.join(unique_res)}"
        ]

        # Suporte automático a Sumário (TOC) ABNT posicionado e numeração de seções
        toc_filter = find_toc_filter()
        if toc_filter and any(k in processed_md.lower() for k in ["sumario", "toc", "table-of-contents"]):
            cmd.append(f"--lua-filter={toc_filter}")
            cmd.append("--number-sections")
        elif any(k in processed_md.lower() for k in ["sumario", "toc", "table-of-contents"]):
            cmd.append("--toc")
            cmd.append("--toc-depth=3")
            cmd.append("--number-sections")

        # Suporte automático a citações e bibliografia (.bib)
        bib_path = find_bibliography_file(work_dir, processed_md)
        if bib_path:
            cmd.append("--citeproc")
            cmd.append(f"--bibliography={bib_path}")

            csl_path = find_csl_file(work_dir, processed_md)
            if csl_path:
                cmd.append(f"--csl={csl_path}")

            # Gerencia a exibição da bibliografia:
            wants_bib = document_wants_bibliography(processed_md)
            if wants_bib:
                if "nocite:" not in processed_md:
                    with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".yaml", encoding="utf-8", delete=False
                    ) as f_meta:
                        f_meta.write('nocite: "@*"\n')
                        temp_meta = f_meta.name
                    cmd.append(f"--metadata-file={temp_meta}")
            else:
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=".yaml", encoding="utf-8", delete=False
                ) as f_meta:
                    f_meta.write("suppress-bibliography: true\n")
                    temp_meta = f_meta.name
                cmd.append(f"--metadata-file={temp_meta}")

        # Se uma engine de PDF for encontrada (ex: weasyprint, typst, pdflatex), adiciona a flag
        if pdf_engine:
            cmd.append(f"--pdf-engine={pdf_engine}")

        # Executa a compilação garantindo o diretório de trabalho correto (CWD)
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            cwd=work_dir,
            timeout=30
        )

        elapsed_time = time.time() - start_time

        if process.returncode == 0 and os.path.exists(output_pdf):
            return output_pdf, "", elapsed_time
        else:
            stderr_msg = process.stderr.strip() or f"Pandoc encerrou com código de erro {process.returncode}."
            return None, stderr_msg, elapsed_time

    except subprocess.TimeoutExpired:
        return None, "Erro: O processo de compilação excedeu o tempo limite (timeout de 30s).", time.time() - start_time
    except Exception as e:
        return None, f"Exceção inesperada durante a compilação: {str(e)}", time.time() - start_time
    finally:
        # Limpa arquivos temporários
        if temp_md and os.path.exists(temp_md):
            try:
                os.remove(temp_md)
            except OSError:
                pass
        if temp_meta and os.path.exists(temp_meta):
            try:
                os.remove(temp_meta)
            except OSError:
                pass


class PDFCompilerThread(QThread):
    """
    Thread em segundo plano (QThread) para compilação assíncrona de Markdown para PDF.
    Garante o suporte a HTML bruto (raw_html), imagens relativas, bibliografia (citeproc) e engine WeasyPrint.
    """
    # Sinal emitido ao concluir a compilação: (sucesso: bool, caminho_pdf: str, stderr: str, duracao_seg: float)
    compilation_finished = pyqtSignal(bool, str, str, float)

    def __init__(self, markdown_text: str, custom_output_path: str = None, working_dir: str = None, main_file_path: str = None, project_root: str = None, parent=None):
        super().__init__(parent)
        self.markdown_text = markdown_text
        self.custom_output_path = custom_output_path
        self.working_dir = working_dir or os.getcwd()
        self.main_file_path = main_file_path
        self.project_root = project_root

    def run(self):
        pdf_path, err_msg, elapsed = compile_markdown_to_pdf(
            self.markdown_text,
            custom_output_path=self.custom_output_path,
            working_dir=self.working_dir,
            main_file_path=self.main_file_path,
            project_root=self.project_root
        )
        if pdf_path and os.path.exists(pdf_path):
            self.compilation_finished.emit(True, pdf_path, "", elapsed)
        else:
            self.compilation_finished.emit(False, "", err_msg, elapsed)
