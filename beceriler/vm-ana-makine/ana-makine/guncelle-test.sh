#!/usr/bin/env bash
# guncelle.sh denemesi: sahte GitHub (bare repo) + onu çeken "ana makine" kopyası, geçici klasörde.
G="$(cd "$(dirname "$0")" && pwd)/guncelle.sh"
S="$(mktemp -d)"; trap 'pkill -f "$U"; rm -rf "$S"' EXIT; mkdir -p "$S/stub" && cd "$S"
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
printf '#!/bin/sh\necho "gsettings $*" >> %s/gs.log; [ "$1" = get ] && echo "[%sfirefox.desktop%s]"\n' "$S" "'" "'" > stub/gsettings; chmod +x stub/gsettings
export PATH=$S/stub:$PATH XDG_STATE_HOME=$S/state XDG_DATA_HOME=$S/data
U=deneme-uyg; U=$U-xyz   # desen bu betiğin metninde tek parça geçmesin
git init -q --bare -b main uzak.git; git clone -q uzak.git vm 2>/dev/null; cd vm; git checkout -q -b main; mkdir .ortam
cat > .ortam/guncelle <<EOF
AD="Deneme"
KUR="echo KUR >> ../kur.log; [ ! -f bozuk ]"
AC="exec -a $U sleep 60"
SUREC="$U"
EOF
git add -A; git commit -qm ilk; git push -q origin main; cd ..
git clone -q uzak.git ana; git -C ana checkout -q -b eski
ok() { if eval "$2"; then echo "✓ $1"; else echo "✗ $1"; HATA=1; fi; }
$G --kisayol ana origin/main >/dev/null 2>&1
ok "dal main'e geçti" '[ "$(git -C ana rev-parse --abbrev-ref @{u})" = origin/main ]'
ok "desktop dosyası" 'grep -q "Exec=.*guncelle.sh $S/ana$" data/applications/guncelle-ana.desktop'
ok "favoriye eklendi" 'grep -q "guncelle-ana.desktop" gs.log'
$G ana </dev/null >/dev/null 2>&1; sleep .3
ok "1. basış: kurdu ve açtı" '[ "$(wc -l < kur.log)" = 1 ] && pgrep -f "$U" >/dev/null'
$G ana </dev/null >/dev/null 2>&1
ok "2. basış: değişiklik yok, kurmadı, ikinci kopya açmadı" '[ "$(wc -l < kur.log)" = 1 ] && [ "$(pgrep -fc "$U")" = 1 ]'
(cd vm && touch yeni && git add yeni && git commit -qm yeni && git push -q)
$G ana </dev/null >/dev/null 2>&1; k=$?
ok "3. basış: yeni kod var ama uygulama açık → beklerken durdu" '[ $k -ne 0 ] && [ "$(wc -l < kur.log)" = 1 ]'
pkill -f "$U"; sleep .3
$G ana </dev/null >/dev/null 2>&1
ok "4. basış: kapatılınca kurdu" '[ -f ana/yeni ] && [ "$(wc -l < kur.log)" = 2 ]'
pkill -f "$U"; (cd vm && touch bozuk && git add bozuk && git commit -qm bozuk && git push -q)
$G ana </dev/null >/dev/null 2>&1; k=$?
ok "5. basış: kurulum hatası → hata kodu, açmadı" '[ $k -ne 0 ] && ! pgrep -f "$U" >/dev/null'
$G ana </dev/null >/dev/null 2>&1; k=$?
ok "6. basış: önceki kurulum başarısızdı → yeniden kurmayı dener" '[ $k -ne 0 ] && [ "$(wc -l < kur.log)" = 4 ]'
exit ${HATA:-0}
