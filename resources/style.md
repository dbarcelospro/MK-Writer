<style>
/* ========================================== */
/* FOLHA E MARGENS (2 cm UNIFORMES)           */
/* ========================================== */
@page {
    size: A4 portrait;
    margin: 2cm;
}

*, *::before, *::after {
    box-sizing: border-box;
}

html {
    background-color: #ffffff;
}

body {
    margin: 0;
    padding: 0;
    max-width: none;
    font-family: "Times New Roman", Times, serif;
    font-size: 12pt;
    line-height: 1.15;
    text-align: justify;
    color: #000000;
}

/* ========================================== */
/* PARÁGRAFOS E TEXTO CORRENTE                */
/* ========================================== */
p {
    line-height: 1.15;
    text-align: justify;
    text-indent: 1.25cm;
    margin-top: 0;
    margin-bottom: 0;
    orphans: 2;
    widows: 2;
}

blockquote {
    margin-left: 4cm;
    margin-right: 0;
    margin-top: 1.2em;
    margin-bottom: 1.2em;
    font-size: 10pt;
    line-height: 1.0;
    text-align: justify;
}

blockquote p {
    text-indent: 0 !important;
    line-height: 1.0;
}

/* ========================================== */
/* CABEÇALHOS E SEÇÕES                        */
/* ========================================== */
h1, h2, h3, h4 {
    font-family: "Times New Roman", Times, serif;
    color: #000000;
    margin-bottom: 0.5em;
    break-after: avoid;
    page-break-after: avoid;
}

h1 {
    font-size: 14pt;
    text-transform: uppercase;
    margin-top: 1.5em;
}

h2 {
    font-size: 12pt;
    margin-top: 1.2em;
}

h3, h4 {
    font-size: 12pt;
    margin-top: 1em;
}

/* ========================================== */
/* CAPA NO MODELO EXATO DO PROFESSOR (ACADÊMICO)    */
/* ========================================== */
.capa {
    width: 100%;
    height: 25.5cm;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-sizing: border-box;
}

.capa p {
    text-indent: 0 !important;
    margin: 0 !important;
    text-align: inherit !important;
}

/* Topo sem imagem: texto à esquerda e linha verde */
.capa-topo {
    text-align: left;
    border-bottom: 2px solid #009640;
    padding-bottom: 8px;
    margin-bottom: 0.8cm;
}

.capa-iff-texto {
    font-size: 11pt;
    font-weight: bold;
    text-transform: uppercase;
    line-height: 1.25;
    color: #000000;
}

.capa-iff-campus {
    font-size: 10pt;
    font-weight: normal;
    color: #333333;
}

/* Subcabeçalho Institucional */
.capa-subcabecalho,
.capa-subcabecalho p {
    text-align: center !important;
    font-weight: bold;
    font-size: 11pt;
    line-height: 1.4;
    text-transform: uppercase;
}

/* Título */
.capa-titulo,
.capa-titulo p {
    text-align: center !important;
    font-weight: bold;
    font-size: 12.5pt;
    text-transform: uppercase;
    line-height: 1.45;
    padding: 0 1cm;
}

/* Autor */
.capa-autor,
.capa-autor p {
    text-align: center !important;
    font-weight: bold;
    font-size: 12pt;
    text-transform: uppercase;
}

/* Bloco de Orientadores alinhado à direita */
.capa-bloco-nota {
    display: flex;
    justify-content: flex-end;
    width: 100%;
}

.capa-nota {
    width: 52%;
    font-size: 10pt;
    line-height: 1.35;
}

.capa-nota,
.capa-nota p {
    text-align: justify !important;
}

/* Rodapé: Cidade e Ano */
.capa-rodape,
.capa-rodape p {
    text-align: center !important;
    font-size: 11pt;
    line-height: 1.3;
}

/* ========================================== */
/* QUEBRA DE PÁGINA E TABELAS                 */
/* ========================================== */
.page-break {
    display: block;
    clear: both;
    page-break-after: always;
    break-after: page;
    height: 0;
    margin: 0;
    padding: 0;
}

.page-break:first-child {
    display: none !important;
    page-break-after: auto !important;
    break-after: auto !important;
}

table {
    display: table !important;
    margin-left: auto !important;
    margin-right: auto !important;
    margin-top: 1.5em !important;
    margin-bottom: 1.5em !important;
    border-collapse: collapse;
    page-break-inside: auto !important;
    break-inside: auto !important;
}

tr {
    page-break-inside: avoid !important;
    break-inside: avoid !important;
}

thead {
    display: table-header-group !important;
}

tfoot {
    display: table-footer-group !important;
}

th, td {
    border: 1px solid #000000;
    padding: 6px 10px;
    text-align: left;
    font-size: 11pt;
}

th {
    background-color: #f2f2f2;
    font-weight: bold;
}

/* ========================================== */
/* FIGURAS, IMAGENS E LEGENDAS (ABNT NBR 14724) */
/* ========================================== */
figure, div.figure, div.figura {
    display: block !important;
    text-align: center !important;
    margin-left: auto !important;
    margin-right: auto !important;
    margin-top: 1.5em !important;
    margin-bottom: 1.5em !important;
    page-break-inside: avoid !important;
    break-inside: avoid !important;
}

figure img, p img, img, .figura img {
    display: block !important;
    margin-left: auto !important;
    margin-right: auto !important;
    max-width: 90% !important;
    height: auto !important;
    page-break-inside: avoid !important;
    break-inside: avoid !important;
}

.capa img, .capa-topo img {
    display: inline-block !important;
    margin: 0 !important;
}

figcaption, .figura-titulo, .caption-titulo {
    text-align: center !important;
    font-size: 10.5pt !important;
    font-weight: bold !important;
    margin-top: 0.5em !important;
    margin-bottom: 0.5em !important;
    text-indent: 0 !important;
}

p:has(img) {
    text-align: center !important;
    text-indent: 0 !important;
    margin-top: 1.5em !important;
    margin-bottom: 0.5em !important;
}

p:has(img) small,
small,
.fonte,
p.fonte {
    display: block !important;
    text-align: center !important;
    text-indent: 0 !important;
    font-size: 10pt !important;
    margin-top: 0.3em !important;
    margin-bottom: 1.5em !important;
}

.figura p, div.figura p {
    text-indent: 0 !important;
    text-align: center !important;
    margin: 0.3em auto !important;
}

/* ========================================== */
/* REFERÊNCIAS BIBLIOGRÁFICAS (ABNT NBR 14724)*/
/* ========================================== */
/* Título REFERÊNCIAS: Centralizado, sem número, fonte 12pt, caixa alta, negrito com espaço 1,5 */
h1.unnumbered, h1.centralizado, #referências, #referencias {
    text-align: center !important;
    font-size: 12pt !important;
    font-weight: bold !important;
    text-transform: uppercase !important;
    margin-top: 0 !important;
    margin-bottom: 1.5em !important;
    page-break-before: always;
}

/* Lista de obras: Alinhada à esquerda, espaçamento simples, linha em branco entre elas */
#refs, .references {
    margin-top: 1.5em;
    text-align: left !important;
}

.csl-entry {
    margin-bottom: 12pt !important;
    text-align: left !important;
    text-indent: 0 !important;
    line-height: 1.0 !important;
}

.csl-entry a {
    color: #000000;
    text-decoration: underline;
    word-break: break-all;
}
/* ========================================== */
/* REFERÊNCIAS BIBLIOGRÁFICAS (ABNT NBR 14724)*/
/* ========================================== */

/* 1. Título REFERÊNCIAS: Centralizado no topo, sem indicativo numérico, caixa alta, fonte 12pt, negrito, espaço 1.5 abaixo */
h1.unnumbered, h1.centralizado, #referências, #referencias {
    text-align: center !important;       /* Centralizado no topo da página */
    font-size: 12pt !important;          /* Tamanho 12pt */
    font-weight: bold !important;        /* Negrito */
    text-transform: uppercase !important;/* Caixa alta (MAIÚSCULAS) */
    margin-top: 0 !important;
    margin-bottom: 1.5em !important;     /* Espaçamento 1,5 até a primeira obra */
    page-break-before: always;
}

/* 2. Lista de Obras: Alinhada à esquerda, espaçamento simples (1.0), separadas por uma linha em branco (12pt) */
#refs, .references {
    margin-top: 1.5em;
    text-align: left !important;
}

.csl-entry {
    margin-bottom: 12pt !important;     /* Linha em branco entre cada obra */
    text-align: left !important;        /* Alinhamento estrito à esquerda */
    text-indent: 0 !important;          /* Sem recuo na primeira linha */
    line-height: 1.0 !important;        /* Espaçamento simples dentro da mesma citação */
}

/* ========================================== */
/* SUMÁRIO ABNT (NBR 6027)                     */
/* ========================================== */
#TOC, nav#TOC {
    page-break-after: always;
    margin-top: 1.5em;
}

#TOC h2, #TOC h1 {
    text-align: center !important;
    font-size: 12pt !important;
    font-weight: bold !important;
    text-transform: uppercase !important;
    margin-top: 0 !important;
    margin-bottom: 2em !important;
}

#TOC ul {
    list-style: none !important;
    padding-left: 0 !important;
    margin: 0 !important;
}

#TOC li {
    margin-bottom: 0.4em !important;
    font-family: "Times New Roman", Times, serif;
    font-size: 12pt !important;
}

#TOC a {
    text-decoration: none !important;
    color: #000000 !important;
}

#TOC a::after {
    content: leader('. ') target-counter(attr(href), page);
}

#TOC > ul > li > a {
    font-weight: bold !important;
    text-transform: uppercase !important;
}

#TOC > ul > li > ul > li {
    padding-left: 1.2em;
}

#TOC > ul > li > ul > li > a {
    font-weight: bold !important;
    text-transform: none !important;
}

#TOC > ul > li > ul > li > ul > li {
    padding-left: 2.4em;
}

#TOC > ul > li > ul > li > ul > li > a {
    font-weight: normal !important;
    text-transform: none !important;
}

/* Reseta os contadores no corpo do documento */
body {
    counter-reset: cap-count subcap-count;
}

/* Numeração de Capítulos Principais (# Título -> 1 TÍTULO) */
h1:not(.unnumbered) {
    counter-reset: subcap-count;
    counter-increment: cap-count;
}
h1:not(.unnumbered)::before {
    /* content: counter(cap-count) " "; desativado pelo Pandoc --number-sections */
}

/* Numeração de Subseções (## Título -> 1.1 Título) */
/* ========================================== */
/* BLOCOS DE CÓDIGO E TERMINAL (BASH / CODE)   */
/* ========================================== */
pre, div.sourceCode {
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
}

pre code, div.sourceCode code {
    background-color: transparent !important;
    color: #1F2328 !important;
    padding: 0 !important;
    border: none !important;
    font-family: inherit !important;
    font-size: inherit !important;
}

/* Realce de sintaxe em fundo claro */
.sourceCode .co { color: #57606A !important; font-style: italic !important; }
.sourceCode .st { color: #0A3069 !important; font-weight: 500 !important; }
.sourceCode .dv, .sourceCode .fl { color: #0550AE !important; }
.sourceCode .kw { color: #CF222E !important; font-weight: bold !important; }
.sourceCode .fu { color: #8250DF !important; }
.sourceCode .op { color: #0550AE !important; }

/* Código Inline (`comando`) */
p code, li code {
    background-color: #F1F5F9 !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 4px !important;
    padding: 1px 5px !important;
    font-family: "Consolas", "Courier New", monospace !important;
    font-size: 9.5pt !important;
}

/* ========================================== */
/* LISTAS E ALÍNEAS ABNT                      */
/* ========================================== */
ul, ol {
    margin-top: 0.5em !important;
    margin-bottom: 0.5em !important;
    padding-left: 2em !important;
}

li {
    text-indent: 0 !important;
    margin-top: 0.25em !important;
    margin-bottom: 0.25em !important;
    line-height: 1.15 !important;
    text-align: justify !important;
}

li > p, li p {
    text-indent: 0 !important;
    margin: 0 !important;
    display: inline !important;
    line-height: inherit !important;
}

/* Alíneas ABNT: listas ordenadas aninhadas ou com letras usam estilo alfabético (a, b, c) */
ol ol, ol[type="a"], ol.alineas {
    list-style-type: lower-alpha !important;
}
ol ol ol {
    list-style-type: lower-roman !important;
}
</style>


