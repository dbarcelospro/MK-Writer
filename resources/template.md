<style>
@page {
    size: A4;
    margin: 2cm;
}
body {
    font-family: "Times New Roman", Times, serif;
    font-size: 12pt;
    line-height: 1.15;
    text-align: justify;
    color: #000000;
}
h1, h2, h3, h4 {
    font-family: "Times New Roman", Times, serif;
    color: #000000;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}
h1 {
    font-size: 14pt;
    text-transform: uppercase;
}
h2 {
    font-size: 12pt;
}

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

p code, li code {
    background-color: #F1F5F9 !important;
    color: #0F172A !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 4px !important;
    padding: 1px 5px !important;
    font-family: "Consolas", "Courier New", monospace !important;
    font-size: 9.5pt !important;
}

/* Alíneas ABNT: listas ordenadas aninhadas ou com letras usam estilo alfabético (a, b, c) */
ol ol, ol[type="a"], ol.alineas {
    list-style-type: lower-alpha !important;
}
ol ol ol {
    list-style-type: lower-roman !important;
}



/* ========================================== */
/* CAPA NO MODELO DO PROFESSOR (ACADÊMICO)    */
/* ========================================== */
.capa {
    position: relative;
    height: 25.5cm; /* Preenche a altura útil da folha A4 em 1 única folha */
    box-sizing: border-box;
}

/* Cabeçalho Superior com Logo e Linha Verde/Vermelha */
.capa-topo {
    border-bottom: 2px solid #009640;
    padding-bottom: 6px;
}

.capa p {
    text-indent: 0 !important;
    margin: 0 !important;
    text-align: inherit !important;
}

.capa-subcabecalho,
.capa-subcabecalho p {
    text-align: center !important;
    font-weight: bold;
    font-size: 11pt;
    line-height: 1.35;
    margin-top: 0.8cm;
}

/* Título (Proporcional ao modelo do professor) */
.capa-titulo,
.capa-titulo p {
    text-align: center !important;
    font-weight: bold;
    font-size: 13pt;
    text-transform: uppercase;
    margin-top: 1.5cm;
    line-height: 1.4;
}

/* Autor */
.capa-autor,
.capa-autor p {
    text-align: center !important;
    font-weight: bold;
    font-size: 11.5pt;
    text-transform: uppercase;
    margin-top: 1.5cm;
}

/* Nota de Apresentação e Orientadores (Alinhado a 48% da margem esquerda) */
.capa-nota {
    margin-left: 48%;
    font-size: 10pt;
    line-height: 1.3;
    margin-top: 1.2cm;
}

.capa-nota,
.capa-nota p {
    text-align: justify !important;
}

/* Rodapé (Centralizado na borda final da folha A4) */
.capa-rodape,
.capa-rodape p {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    width: 100%;
    text-align: center !important;
    font-size: 11pt;
    line-height: 1.3;
}

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
    border: 1px solid #000;
    padding: 6px 10px;
    text-align: left;
    font-size: 11pt;
}
th {
    background-color: #F2F2F2;
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

/* Alíneas ABNT */
ol ol, ol[type="a"], ol.alineas {
    list-style-type: lower-alpha !important;
}
ol ol ol {
    list-style-type: lower-roman !important;
}

/* ========================================== */
/* REFERÊNCIAS BIBLIOGRÁFICAS (ABNT)          */
/* ========================================== */
#refs, .references {
    margin-top: 1.5em;
    line-height: 1.15;
}

.csl-entry {
    margin-bottom: 1.2em !important;
    text-align: left !important;
    text-indent: 0 !important;
    line-height: 1.15 !important;
}

.csl-entry a {
    color: #000000;
    text-decoration: underline;
    word-break: break-all;
}
</style>

<!-- ========================================== -->
<!-- PRÉ-TEXTUAL                                -->
<!-- ========================================== -->

<!-- CAPA MODELO DO PROFESSOR -->
<div class="capa">

  <div class="capa-topo">
    <!-- Inserir logotipo institucional aqui caso desejado: <img src="Imagens/logo.svg" height="42" alt="Logotipo"> -->
  </div>

  <div class="capa-subcabecalho">
    PRÓ-REITORIA DE PESQUISA E INOVAÇÃO<br>
    PROGRAMA DE PÓS-GRADUAÇÃO EM ENGENHARIA AMBIENTAL<br>
    MESTRADO EM ENGENHARIA AMBIENTAL<br>
    MODALIDADE PROFISSIONAL
  </div>

  <div class="capa-titulo">
    TÍTULO DO PROJETO DE PESQUISA OU DISSERTAÇÃO
  </div>

  <div class="capa-autor">
    NOME COMPLETO DO AUTOR
  </div>

  <div class="capa-nota">
    Proposta de Projeto de Pesquisa da linha XXXXX, área de atuação WWWWW, apresentada para avaliação.<br><br>
    <b>Orientação:</b> Prof. Dr. YYYYY.<br>
    <b>Coorientação:</b> Prof. Dr. ZZZZZZ (opcional).
  </div>

  <div class="capa-rodape">
    Cidade/UF<br>
    2026
  </div>

</div>

<div class="page-break"></div>

<!-- RESUMO E ABSTRACT -->
# RESUMO

Insira aqui o resumo do trabalho em português (de 150 a 500 palavras). O resumo deve apresentar o objetivo, a justificativa, a metodologia simplificada e os principais resultados ou contribuições esperadas da pesquisa.

**Palavras-chave**: Engenharia Ambiental. Projeto de Pesquisa. Metodologia Científica.

<br>

---

# ABSTRACT

Insert the English version of the abstract here. It must accurately reflect the contents of the Portuguese version.

**Keywords**: Environmental Engineering. Research Project. Scientific Methodology.

<div class="page-break"></div>

<!-- ========================================== -->
<!-- TEXTUAL                                    -->
<!-- ========================================== -->

# 1. INTRODUÇÃO

Insira aqui a introdução do seu projeto de pesquisa. Apresente a contextualização do tema, a delimitação do problema e o estado da arte geral em que o estudo se insere.

# 2. JUSTIFICATIVA / RELEVÂNCIA

Apresente a justificativa teórica e prática da pesquisa, destacando a relevância científica, socioambiental e/ou tecnológica do trabalho para a região ou para a área de Engenharia Ambiental.

# 3. OBJETIVOS

## 3.1. Geral
Descreva de forma clara e direta o objetivo principal da pesquisa.

## 3.2. Específicos
1. Metas específicas do projeto:
   a. Detalhar a primeira meta específica necessária para alcançar o objetivo geral;
   b. Detalhar a segunda meta específica relacionada ao levantamento de dados ou experimentos;
   c. Detalhar a terceira meta referente à análise, modelagem ou validação dos resultados.

# 4. REVISÃO DE LITERATURA

Apresente a fundamentação teórica que dá suporte ao trabalho. Subdivida em tópicos se necessário para abordar os principais conceitos, técnicas e trabalhos correlatos.

# 5. MATERIAL E MÉTODOS

## 5.1. Material
Descreva os materiais, reagentes, equipamentos, softwares, bases de dados ou dados cartográficos utilizados.

## 5.2. Métodos
Descreva detalhadamente a metodologia adotada, os procedimentos experimentais, o plano de amostragem, o tratamento estatístico e os métodos de análise.

Exemplo de bloco de código ou rotina de comandos com fundo escuro:

```bash
# Exemplo de execução de pipeline de análise
python -m analise_descritiva --input dados_coleta.csv --output relatorio.pdf
```

Exemplo de tabela estatística com fórmulas LaTeX e centralização automática:

**Tabela 1** — Síntese das estatísticas descritivas por estado avaliado.

| Estatística | Estado A | Estado B |
| :--- | :--- | :--- |
| Média ($\bar{x}$) | 12,5 eventos | 12,8 eventos |
| Desvio-Padrão ($s$) | 2,1 eventos | 8,6 eventos |
| Mínimo | 8,0 eventos | 3,0 eventos |
| Primeiro Quartil ($Q_1$) | 11,0 eventos | 6,0 eventos |
| Mediana ($Q_2$) | 12,5 eventos | 9,5 eventos |
| Terceiro Quartil ($Q_3$) | 14,0 eventos | 15,0 eventos |
| Máximo | 17,0 eventos | 45,0 eventos |

Fonte: Elaborado pelo autor (2026).

# 6. PLANO DE TRABALHO E CRONOGRAMA DE EXECUÇÃO

## 6.1. Plano de Trabalho
Detalhamento das etapas operacionais de execução da pesquisa ao longo do período do mestrado.

## 6.2. Cronograma

| Etapas / Mês | M1 | M2 | M3 | M4 | M5 | M6 | M7 | M8 | M9 | M10 | M11 | M12 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1. Revisão Bibliográfica | X | X | X | X | X | X | X | X | X | X | X | X |
| 2. Coleta de Dados / Amostragem | | X | X | X | X | | | | | | | |
| 3. Processamento e Análise | | | | X | X | X | X | | | | | |
| 4. Redação da Dissertação | | | | | | | X | X | X | X | X | |
| 5. Defesa do Projeto | | | | | | | | | | | | X |

<!-- ========================================== -->
<!-- PÓS-TEXTUAL                                -->
<!-- ========================================== -->

# 7. ESTIMATIVA DE CUSTO (OPCIONAL)

| Item / Descrição | Qtd. | Valor Unitário (R\$) | Valor Total (R\$) |
| :--- | :---: | :---: | :---: |
| Material de Consumo e Reagentes | 1 | R\$ 1.500,00 | R\$ 1.500,00 |
| Serviços de Terceiros (Análises) | 1 | R\$ 2.000,00 | R\$ 2.000,00 |
| **Total Estimado** | | | **R\$ 3.500,00** |

# 8. REFERÊNCIAS

- ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. **ABNT NBR 6023**: Informação e documentação - Referências - Elaboração. Rio de Janeiro: ABNT, 2018.
- SOBRENOME, Nome. Título do artigo científico. **Nome da Revista**, v. 10, n. 2, p. 100-115, 2024.