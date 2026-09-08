import json
import os
import shutil
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.package_manager import (
    PACKAGE_EXTENSIONS,
    create_new_package,
    get_workspace_dir_for_package,
    is_package_file,
    pack_project,
    sync_workspace_to_package,
    unpack_package,
)
from app.compiler import compile_markdown_to_pdf


def test_create_and_unpack_package():
    with tempfile.TemporaryDirectory() as tmp_dir:
        pkg_path = os.path.join(tmp_dir, "Teste_Documento.mkw")
        created_path = create_new_package(pkg_path, title="Meu Trabalho de Mestrado", author="Danilo")

        assert os.path.exists(created_path)
        assert is_package_file(created_path)
        assert created_path.endswith(".mkw")

        # Verifica arquivos contidos dentro do zip
        with zipfile.ZipFile(created_path, "r") as zf:
            namelist = zf.namelist()
            assert "project.json" in namelist
            assert "main.md" in namelist
            assert "style.md" in namelist
            assert "referencias.bib" in namelist
            assert any("01_capa.md" in name for name in namelist)
            assert any("01_introducao.md" in name for name in namelist)
            assert any("02_referencias.md" in name for name in namelist)

        # Descompacta o pacote
        extract_dir = os.path.join(tmp_dir, "workspace")
        ws_dir, meta = unpack_package(created_path, dest_dir=extract_dir)

        assert ws_dir == extract_dir
        assert meta["title"] == "Meu Trabalho de Mestrado"
        assert meta["author"] == "Danilo"
        assert os.path.isfile(os.path.join(ws_dir, "main.md"))
        assert os.path.isfile(os.path.join(ws_dir, "style.md"))
        assert os.path.isfile(os.path.join(ws_dir, "referencias.bib"))


def test_sync_workspace_modification():
    with tempfile.TemporaryDirectory() as tmp_dir:
        pkg_path = os.path.join(tmp_dir, "Sincronizacao.mkw")
        create_new_package(pkg_path, title="Projeto Sinc", author="Autor")

        ws_dir, _ = unpack_package(pkg_path, dest_dir=os.path.join(tmp_dir, "ws1"))
        intro_file = os.path.join(ws_dir, "02_Textual", "01_introducao.md")

        # Modifica arquivo no workspace
        with open(intro_file, "a", encoding="utf-8") as f:
            f.write("\n\nTexto adicional inserido durante o teste de sincronizacao.")

        # Sincroniza de volta para o pacote
        sync_workspace_to_package(ws_dir, pkg_path)

        # Extrai em uma segunda pasta limpa para conferir persistência
        ws2_dir, _ = unpack_package(pkg_path, dest_dir=os.path.join(tmp_dir, "ws2"))
        intro2_file = os.path.join(ws2_dir, "02_Textual", "01_introducao.md")

        with open(intro2_file, "r", encoding="utf-8") as f:
            content2 = f.read()

        assert "Texto adicional inserido durante o teste de sincronizacao." in content2


def test_pack_existing_project():
    with tempfile.TemporaryDirectory() as tmp_dir:
        source_dir = os.path.join(tmp_dir, "projeto_origem")
        os.makedirs(os.path.join(source_dir, "01_Pre_Textual"), exist_ok=True)
        os.makedirs(os.path.join(source_dir, "02_Textual"), exist_ok=True)
        os.makedirs(os.path.join(source_dir, "03_Pos_Textual"), exist_ok=True)
        with open(os.path.join(source_dir, "01_Pre_Textual", "01_capa.md"), "w", encoding="utf-8") as f:
            f.write("# Capa\n")
        with open(os.path.join(source_dir, "02_Textual", "01_intro.md"), "w", encoding="utf-8") as f:
            f.write("# Intro\n")
        with open(os.path.join(source_dir, "03_Pos_Textual", "01_refs.md"), "w", encoding="utf-8") as f:
            f.write("# Refs\n")
        with open(os.path.join(source_dir, "main.md"), "w", encoding="utf-8") as f:
            f.write("# Projeto\n!include style.md\n")
        with open(os.path.join(source_dir, "style.md"), "w", encoding="utf-8") as f:
            f.write("/* Estilo */\n")
        with open(os.path.join(source_dir, "referencias.bib"), "w", encoding="utf-8") as f:
            f.write("@article{ref, author={Autor}, title={Titulo}, year={2024}}\n")

        target_pkg = os.path.join(tmp_dir, "Projeto_Teste.mkw")
        pack_project(source_dir, target_pkg, metadata={"title": "Projeto de Teste"})

        assert os.path.isfile(target_pkg)
        assert is_package_file(target_pkg)

        # Testa descompactação
        ws_dir, meta = unpack_package(target_pkg, dest_dir=os.path.join(tmp_dir, "ws_extraido"))
        assert os.path.isfile(os.path.join(ws_dir, "main.md"))
        assert os.path.isfile(os.path.join(ws_dir, "style.md"))
        assert os.path.isfile(os.path.join(ws_dir, "referencias.bib"))
        assert os.path.isdir(os.path.join(ws_dir, "01_Pre_Textual"))
        assert os.path.isdir(os.path.join(ws_dir, "02_Textual"))
        assert os.path.isdir(os.path.join(ws_dir, "03_Pos_Textual"))


def test_compile_package_to_pdf():
    """Testa se um projeto criado via pacote .mkw compila perfeitamente para PDF via Pandoc e WeasyPrint."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        pkg_path = os.path.join(tmp_dir, "Compilacao_Teste.mkw")
        create_new_package(pkg_path, title="Trabalho Completo", author="Danilo")

        ws_dir, _ = unpack_package(pkg_path, dest_dir=os.path.join(tmp_dir, "comp_ws"))
        main_md_path = os.path.join(ws_dir, "main.md")

        with open(main_md_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        pdf_path, err, elapsed = compile_markdown_to_pdf(raw_text, working_dir=ws_dir, main_file_path=main_md_path)

        assert pdf_path is not None, f"Falha na compilação do PDF: {err}"
        assert os.path.isfile(pdf_path)
        assert os.path.getsize(pdf_path) > 1000


def test_compile_subfolder_file_with_include_style():
    """Testa se um arquivo individual em uma subpasta (ex: 02_Textual/01_introducao.md)
    consegue incluir '!include style.md' da raiz com sucesso."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        pkg_path = os.path.join(tmp_dir, "Subfolder_Include.mkw")
        create_new_package(pkg_path, title="Subfolder Test", author="Danilo")

        ws_dir, _ = unpack_package(pkg_path, dest_dir=os.path.join(tmp_dir, "ws"))
        intro_path = os.path.join(ws_dir, "02_Textual", "01_introducao.md")

        # Escreve !include style.md diretamente (sem ../)
        intro_content = "!include style.md\n# TESTE INTRODUÇÃO\n\nTexto de teste com estilos ABNT."
        with open(intro_path, "w", encoding="utf-8") as f:
            f.write(intro_content)

        pdf_path, err, elapsed = compile_markdown_to_pdf(
            intro_content,
            working_dir=os.path.dirname(intro_path),
            main_file_path=intro_path,
            project_root=ws_dir
        )

        assert pdf_path is not None, f"Falha ao compilar arquivo individual com !include style.md: {err}"
        assert os.path.isfile(pdf_path)
        assert os.path.getsize(pdf_path) > 1000


if __name__ == "__main__":
    print("▶ Executando test_create_and_unpack_package...")
    test_create_and_unpack_package()
    print("✓ test_create_and_unpack_package: SUCESSO")

    print("▶ Executando test_sync_workspace_modification...")
    test_sync_workspace_modification()
    print("✓ test_sync_workspace_modification: SUCESSO")

    print("▶ Executando test_pack_existing_project...")
    test_pack_existing_project()
    print("✓ test_pack_existing_project: SUCESSO")

    print("▶ Executando test_compile_package_to_pdf...")
    test_compile_package_to_pdf()
    print("✓ test_compile_package_to_pdf: SUCESSO")

    print("▶ Executando test_compile_subfolder_file_with_include_style...")
    test_compile_subfolder_file_with_include_style()
    print("✓ test_compile_subfolder_file_with_include_style: SUCESSO")

    print("\n🎉 TODOS OS TESTES DO SISTEMA DE PACOTES (.mkw) PASSARAM COM SUCESSO!")

