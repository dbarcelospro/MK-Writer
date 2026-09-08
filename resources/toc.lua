-- Filtro Lua para Pandoc: Sumário ABNT (NBR 6027) posicionado no local exato do documento
-- Suporta <!-- sumario -->, <!-- toc --> ou <div id="sumario"> / <div id="sumario-placeholder">

local function Header(el)
    local text = pandoc.utils.stringify(el):upper():gsub("^%s*(.-)%s*$", "%1")
    -- Títulos pré-textuais e o próprio sumário não devem receber numeração nem constar no sumário
    if text == "SUMÁRIO" or text == "SUMARIO" or text == "RESUMO" or text == "ABSTRACT" 
       or text == "DEDICATÓRIA" or text == "DEDICATORIA" or text == "AGRADECIMENTOS" or text == "EPÍGRAFE" or text == "EPIGRAFE"
       or el.classes:includes("unlisted") then
        if not el.classes:includes("unlisted") then
            table.insert(el.classes, "unlisted")
        end
        if not el.classes:includes("unnumbered") then
            table.insert(el.classes, "unnumbered")
        end
    end
    return el
end

local function is_toc_placeholder(el)
    if el.t == "RawBlock" and el.format == "html" then
        local t = el.text:lower()
        if t:find("<%!%-%-%s*sumario%s*%-%->") or t:find("<%!%-%-%s*toc%s*%-%->") or (t:find("<div") and t:find("sumario")) then
            return true
        end
    elseif el.t == "Div" then
        if el.identifier == "sumario" or el.identifier == "sumario-placeholder" or el.identifier == "toc-placeholder" or el.classes:includes("sumario") then
            return true
        end
    end
    return false
end

local function Pandoc(doc)
    local opts = {toc_depth = 3, number_sections = true}
    local toc = pandoc.structure.table_of_contents(doc, opts)
    local toc_div = pandoc.Div({toc}, {id = "TOC", class = "toc"})
    local new_blocks = {}
    local inserted = false

    for i, el in ipairs(doc.blocks) do
        if is_toc_placeholder(el) then
            table.insert(new_blocks, toc_div)
            inserted = true
        else
            table.insert(new_blocks, el)
        end
    end

    -- Se não encontrou placeholder explícito, mas o documento possui o cabeçalho SUMÁRIO, insere logo após ele
    if not inserted then
        local final_blocks = {}
        for i, el in ipairs(new_blocks) do
            table.insert(final_blocks, el)
            if el.t == "Header" and (pandoc.utils.stringify(el):upper():find("SUMÁRIO") or pandoc.utils.stringify(el):upper():find("SUMARIO")) then
                table.insert(final_blocks, toc_div)
                table.insert(final_blocks, pandoc.RawBlock("html", '<div class="page-break"></div>'))
                inserted = true
            end
        end
        new_blocks = final_blocks
    end

    doc.blocks = new_blocks
    return doc
end

return {
    { Header = Header },
    { Pandoc = Pandoc }
}
