-- Kod bloğunun her satırını ayrı kod paragrafı yapar. Pandoc tek kod bloğunu tek paragrafa
-- çevirirse büyük API gövdelerinde Word/LibreOffice dosyayı açamıyor (bkz. CHANGELOG v0.9.4).
function CodeBlock(b)
  local cikti = {}
  for satir in (b.text .. "\n"):gmatch("(.-)\n") do
    cikti[#cikti + 1] = pandoc.CodeBlock(satir, b.attr)
  end
  return cikti
end
