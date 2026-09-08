import datetime
import hashlib
import json
import logging
import os
import shutil
import tempfile
import zipfile


PACKAGE_EXTENSIONS = (".mkw", ".mkdoc")
DEFAULT_CACHE_DIR = os.path.expanduser("~/.cache/mk-writer/workspaces")

IGNORE_PATTERNS = {
    ".git",
    "__pycache__",
    ".DS_Store",
    "Thumbs.db",
    ".pytest_cache",
    ".mypy_cache",
}

IGNORE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".tmp",
    ".swp",
    ".bak",
}


def is_package_file(path: str) -> bool:
    """Verifica se o caminho aponta para um pacote de projeto MK Writer (.mkw / .mkdoc)."""
    if not path or not isinstance(path, str):
        return False
    lower = path.lower()
    if not any(lower.endswith(ext) for ext in PACKAGE_EXTENSIONS):
        return False
    return os.path.isfile(path) and zipfile.is_zipfile(path)


def get_workspace_dir_for_package(package_path: str, base_cache_dir: str = None) -> str:
    """
    Gera um diretório de trabalho dedicado e estável para um pacote específico.
    Utiliza hash SHA256 do caminho canônico para evitar colisões entre arquivos com nomes iguais.
    """
    cache_base = base_cache_dir or DEFAULT_CACHE_DIR
    os.makedirs(cache_base, exist_ok=True)

    abs_path = os.path.abspath(package_path)
    path_hash = hashlib.sha256(abs_path.encode("utf-8")).hexdigest()[:12]
    base_name = os.path.splitext(os.path.basename(package_path))[0]
    # Remove caracteres especiais para nome seguro de pasta
    safe_name = "".join(c for c in base_name if c.isalnum() or c in ("-", "_")).strip() or "projeto"

    workspace_dir = os.path.join(cache_base, f"{safe_name}_{path_hash}")
    os.makedirs(workspace_dir, exist_ok=True)
    return workspace_dir


def unpack_package(package_path: str, dest_dir: str = None) -> tuple[str, dict]:
    """
    Descompacta com segurança o pacote .mkw para o diretório de trabalho especificado.
    Protege contra ataques de zip-slip (path traversal).
    Retorna (caminho_workspace, metadados_dict).
    """
    abs_package = os.path.abspath(package_path)
    if not is_package_file(abs_package):
        raise ValueError(f"O arquivo fornecido não é um pacote válido do MK Writer: {package_path}")

    target_dir = dest_dir or get_workspace_dir_for_package(abs_package)
    os.makedirs(target_dir, exist_ok=True)

    with zipfile.ZipFile(abs_package, "r") as zf:
        # Validação de segurança contra path traversal
        for member in zf.infolist():
            member_path = member.filename
            if os.path.isabs(member_path) or ".." in os.path.normpath(member_path).split(os.path.sep):
                raise ValueError(f"Pacote potencialmente inseguro detectado: caminho relativo inválido '{member_path}'")

        zf.extractall(target_dir)

    # Lê metadados de project.json se existirem
    meta_path = os.path.join(target_dir, "project.json")
    metadata = {}
    if os.path.isfile(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as e:
            logging.warning(f"Não foi possível ler project.json do pacote {package_path}: {e}")

    logging.info(f"Pacote {abs_package} descompactado com sucesso em {target_dir}")
    return target_dir, metadata


def pack_project(source_dir: str, target_package_path: str, metadata: dict = None) -> str:
    """
    Compacta uma pasta de projeto em um arquivo .mkw único.
    Utiliza escrita atômica para evitar corrupção em caso de encerramento inesperado.
    """
    abs_source = os.path.abspath(source_dir)
    abs_target = os.path.abspath(target_package_path)

    # Garante a extensão .mkw caso não tenha extensão compatível
    if not any(abs_target.lower().endswith(ext) for ext in PACKAGE_EXTENSIONS):
        abs_target += ".mkw"

    os.makedirs(os.path.dirname(abs_target), exist_ok=True)

    # Atualiza ou cria project.json no workspace antes de compactar
    meta_file = os.path.join(abs_source, "project.json")
    current_meta = {}
    if os.path.isfile(meta_file):
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                current_meta = json.load(f)
        except Exception:
            current_meta = {}

    if metadata:
        current_meta.update(metadata)

    base_name = os.path.splitext(os.path.basename(abs_target))[0]
    current_meta.setdefault("format", "mkw")
    current_meta.setdefault("version", "1.0")
    current_meta.setdefault("title", base_name)
    current_meta.setdefault("main", "main.md")
    current_meta.setdefault("created_at", datetime.datetime.now().isoformat())
    current_meta["updated_at"] = datetime.datetime.now().isoformat()

    try:
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(current_meta, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.warning(f"Erro ao salvar project.json no diretório temporário: {e}")

    # Criação atômica via arquivo temporário
    target_dir = os.path.dirname(abs_target)
    with tempfile.NamedTemporaryFile(suffix=".tmp.mkw", dir=target_dir, delete=False) as tmp_file:
        tmp_name = tmp_file.name

    try:
        with zipfile.ZipFile(tmp_name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for root, dirs, files in os.walk(abs_source):
                # Ignora diretórios indesejados
                dirs[:] = [d for d in dirs if d not in IGNORE_PATTERNS and not d.startswith(".")]

                for file in sorted(files):
                    if file in IGNORE_PATTERNS or any(file.endswith(ext) for ext in IGNORE_EXTENSIONS):
                        continue
                    # Não empacota o próprio arquivo de destino se estiver dentro da pasta
                    full_path = os.path.join(root, file)
                    if full_path == abs_target:
                        continue

                    rel_path = os.path.relpath(full_path, abs_source)
                    zf.write(full_path, arcname=rel_path)

        # Substituição atômica
        os.replace(tmp_name, abs_target)
        logging.info(f"Projeto {abs_source} empacotado com sucesso em {abs_target}")
        return abs_target

    except Exception as e:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass
        raise e


def sync_workspace_to_package(workspace_dir: str, package_path: str) -> None:
    """Sincroniza o conteúdo do workspace de volta para o pacote .mkw."""
    if not workspace_dir or not package_path:
        return
    pack_project(workspace_dir, package_path)


def create_new_package(target_package_path: str, title: str = "Novo Documento Acadêmico", author: str = "") -> str:
    """
    Cria um novo pacote .mkw populado com a estrutura padrão ABNT completa:
    - project.json
    - main.md
    - style.md
    - referencias.bib
    - 01_Pre_Textual/ (01_capa.md, 02_resumo.md, 03_abstract.md, 04_sumario.md)
    - 02_Textual/ (01_introducao.md, 02_desenvolvimento.md, 03_conclusao.md)
    - 03_Pos_Textual/ (02_referencias.md)
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copia o style.md e abnt.csl se existirem no projeto, ou usa templates padrão
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        source_style = os.path.join(project_root, "resources", "style.md")

        target_style = os.path.join(temp_dir, "style.md")

        if os.path.isfile(source_style):
            shutil.copy2(source_style, target_style)
        else:
            with open(target_style, "w", encoding="utf-8") as f:
                f.write("/* Estilo ABNT Padrão */\n")

        # Cria estrutura de pastas
        pre_dir = os.path.join(temp_dir, "01_Pre_Textual")
        text_dir = os.path.join(temp_dir, "02_Textual")
        pos_dir = os.path.join(temp_dir, "03_Pos_Textual")
        img_dir = os.path.join(temp_dir, "imagens")

        os.makedirs(pre_dir, exist_ok=True)
        os.makedirs(text_dir, exist_ok=True)
        os.makedirs(pos_dir, exist_ok=True)
        os.makedirs(img_dir, exist_ok=True)

        source_logo = os.path.join(project_root, "resources", "logo.svg")
        if os.path.isfile(source_logo):
            shutil.copy2(source_logo, os.path.join(img_dir, "logo.svg"))

        # 1. main.md
        main_content = """<!-- ========================================== -->
<!-- ESTILO                                     -->
<!-- ========================================== -->
!include style.md

<!-- ========================================== -->
<!-- PRÉ-TEXTUAL                                -->
<!-- ========================================== -->
!include 01_Pre_Textual/01_capa.md
!include 01_Pre_Textual/02_resumo.md
!include 01_Pre_Textual/03_abstract.md
!include 01_Pre_Textual/04_sumario.md

<!-- ========================================== -->
<!-- TEXTUAL                                    -->
<!-- ========================================== -->
!include 02_Textual/01_introducao.md
!include 02_Textual/02_desenvolvimento.md
!include 02_Textual/03_conclusao.md

<!-- ========================================== -->
<!-- PÓS-TEXTUAL                                -->
<!-- ========================================== -->
!include 03_Pos_Textual/02_referencias.md
"""
        with open(os.path.join(temp_dir, "main.md"), "w", encoding="utf-8") as f:
            f.write(main_content)

        # 2. 01_capa.md
        capa_content = f"""!include ../style.md
<div class="capa">
<div>
<div class="capa-topo">
<img src="imagens/logo.svg" height="42" alt="Logotipo Institucional">
</div>

<div class="capa-subcabecalho">
PROGRAMA DE PÓS-GRADUAÇÃO<br>
MESTRADO PROFISSIONAL
</div>
</div>

<div class="capa-centro">
<div class="capa-titulo">{title.upper()}</div>
<div class="capa-autor">{author.upper() if author else "NOME DO AUTOR"}</div>
</div>

<div class="capa-rodape">
<div class="capa-natureza">
Trabalho acadêmico apresentado à Instituição de Ensino Superior.
</div>

<div class="capa-local-ano">
Cidade/UF<br>
{datetime.date.today().year}
</div>
</div>
</div>
<div class="page-break"></div>
"""
        with open(os.path.join(pre_dir, "01_capa.md"), "w", encoding="utf-8") as f:
            f.write(capa_content)

        # 3. 02_resumo.md
        resumo_content = """# RESUMO {-}

Insira aqui o resumo do trabalho em português (de 150 a 500 palavras). O texto deve ser redigido em parágrafo único, apresentando objetivo, método, resultados e conclusões.

**Palavras-chave**: Termo 1. Termo 2. Termo 3.

<div class="page-break"></div>
"""
        with open(os.path.join(pre_dir, "02_resumo.md"), "w", encoding="utf-8") as f:
            f.write(resumo_content)

        # 4. 03_abstract.md
        abstract_content = """# ABSTRACT {-}

Insert here the English translation of the abstract. It must faithfully reflect the Portuguese version.

**Keywords**: Term 1. Term 2. Term 3.

<div class="page-break"></div>
"""
        with open(os.path.join(pre_dir, "03_abstract.md"), "w", encoding="utf-8") as f:
            f.write(abstract_content)

        # 5. 04_sumario.md
        sumario_content = """!include ../style.md

# SUMÁRIO {.unnumbered .centralizado}

<!-- sumario -->
"""
        with open(os.path.join(pre_dir, "04_sumario.md"), "w", encoding="utf-8") as f:
            f.write(sumario_content)

        # 6. 01_introducao.md
        intro_content = """!include ../style.md
# INTRODUÇÃO

Inicie aqui a introdução do seu trabalho. Apresente o tema, a contextualização, a problemática de pesquisa e a relevância do estudo.

Segundo @exemplo2024, a pesquisa científica fundamenta o desenvolvimento sustentável.

<div class="page-break"></div>
"""
        with open(os.path.join(text_dir, "01_introducao.md"), "w", encoding="utf-8") as f:
            f.write(intro_content)

        # 7. 02_desenvolvimento.md
        desenvolvimento_content = """!include ../style.md
# DESENVOLVIMENTO

Apresente aqui a fundamentação teórica, materiais e métodos utilizados e a discussão dos resultados obtidos.

## Metodologia

Descreva as etapas, procedimentos, amostragem e técnicas analíticas empregadas.

<div class="page-break"></div>
"""
        with open(os.path.join(text_dir, "02_desenvolvimento.md"), "w", encoding="utf-8") as f:
            f.write(desenvolvimento_content)

        # 8. 03_conclusao.md
        conclusao_content = """!include ../style.md
# CONCLUSÃO

Sintetize as principais contribuições da pesquisa, limitações encontradas e sugestões para trabalhos futuros.

<div class="page-break"></div>
"""
        with open(os.path.join(text_dir, "03_conclusao.md"), "w", encoding="utf-8") as f:
            f.write(conclusao_content)

        # 9. 02_referencias.md
        refs_content = """!include ../style.md

# REFERÊNCIAS {.unnumbered .centralizado}

::: {#refs}
:::
"""
        with open(os.path.join(pos_dir, "02_referencias.md"), "w", encoding="utf-8") as f:
            f.write(refs_content)

        # 10. referencias.bib
        bib_content = """@article{exemplo2024,
  author  = {Sobrenome, Nome},
  title   = {Título do Artigo Científico de Exemplo},
  journal = {Revista Brasileira de Engenharia},
  volume  = {10},
  number  = {2},
  pages   = {100--115},
  year    = {2024}
}
"""
        with open(os.path.join(temp_dir, "referencias.bib"), "w", encoding="utf-8") as f:
            f.write(bib_content)

        meta = {
            "format": "mkw",
            "version": "1.0",
            "title": title,
            "author": author,
            "main": "main.md",
        }

        # Compacta para o destino
        return pack_project(temp_dir, target_package_path, metadata=meta)
