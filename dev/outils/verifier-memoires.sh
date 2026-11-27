#!/bin/bash
# Mémoire de Claude Code du projet : contrôle mécanique, premier geste du tamis de chaque clôture (skill passation, décision
# du 13/10/2026). Repris d'un autre harnais de l'utilisateur (où le tamis a corrigé 4 mémoires sur 42, dont deux affirmaient l'inverse du fait) :
# index complet, liens qui mènent quelque part, chemins écrits en toutes lettres qui existent encore. Le fond ne se contrôle
# pas ici : relire ensuite chaque mémoire que le lot touche.
#   verifier-memoires.sh [--depot RACINE] [--memoire DOSSIER] [--depuis ÉTIQUETTE]
#     --depot    racine du projet (défaut : le dépôt git qui contient ce script, sinon celui du dossier courant, sinon lui)
#     --memoire  dossier de la mémoire, quand Claude Code a été lancé ailleurs qu'à la racine
#     --depuis   étiquette dont la date borne la liste des mémoires modifiées (défaut : la dernière étiquette du dépôt, ou
#                celle d'avant quand la dernière est posée sur HEAD : le tamis suit le commit étiqueté du lot)
# Où vit la mémoire (lu dans Claude Code 2.1.302, non documenté en entier : peut changer) : autoMemoryDirectory des réglages
# (.claude/settings.local.json du projet, puis settings.json de la configuration), sinon <configuration>/projects/<nom>/memory/,
# <configuration> valant CLAUDE_CONFIG_DIR ou ~/.claude, <nom> le chemin absolu du dossier de lancement, chaque caractère hors
# [A-Za-z0-9] changé en « - » (coupé à 200 caractères, suivi d'une empreinte, au-delà) ; l'index MEMORY.md n'est chargé que
# sur ses 200 premières lignes. Hors de la machine de Claude Code, rien à lire : le script le dit et rend 0.
# Code 0 : rien à reprendre, ou aucune mémoire (dit en toutes lettres). Code 1 : index ou lien à reprendre. Code 2 : usage.
# Un chemin introuvable est signalé (« ! ») sans échec : une mémoire peut citer un chemin retiré pour le dire retiré.
set -u
DEPOT=""; MEMOIRE=""; DEPUIS=""
while [ $# -gt 0 ]; do case "$1" in
  --depot|--memoire|--depuis) [ -n "${2:-}" ] || { echo "$1 : valeur manquante"; exit 2; }
    case "$1" in --depot) DEPOT="$2";; --memoire) MEMOIRE="$2";; *) DEPUIS="$2";; esac; shift;;
  *) echo "option inconnue : $1 (verifier-memoires.sh [--depot RACINE] [--memoire DOSSIER] [--depuis ÉTIQUETTE])"; exit 2;; esac; shift; done
command -v python3 >/dev/null || { echo "✗ python3 absent : mémoires non contrôlées"; exit 1; }
if [ -z "$DEPOT" ]; then
  DEPOT="$(git -C "$(dirname "$0")" rev-parse --show-toplevel 2>/dev/null || git rev-parse --show-toplevel 2>/dev/null || pwd -P)"
fi
[ -d "$DEPOT" ] || { echo "--depot : dossier introuvable ($DEPOT)"; exit 2; }
DEPOT="$(cd "$DEPOT" && pwd -P)"
if [ -z "$DEPUIS" ]; then
  # le tamis tourne après le commit étiqueté du lot (passation, Clôture) : une étiquette posée sur HEAD est celle du lot
  # lui-même, et toute mémoire écrite pendant le lot lui est antérieure ; la liste se borne alors à l'étiquette d'avant
  DEPUIS="$(git -C "$DEPOT" describe --tags --abbrev=0 2>/dev/null || true)"
  if [ -n "$DEPUIS" ] && [ "$(git -C "$DEPOT" rev-parse "$DEPUIS^{commit}" 2>/dev/null)" = "$(git -C "$DEPOT" rev-parse HEAD 2>/dev/null)" ]; then
    DEPUIS="$(git -C "$DEPOT" describe --tags --abbrev=0 HEAD^ 2>/dev/null || true)"
  fi
fi
QUAND=""
if [ -n "$DEPUIS" ]; then
  QUAND="$(git -C "$DEPOT" log -1 --format=%ct "$DEPUIS" 2>/dev/null)" || { echo "--depuis : étiquette inconnue dans $DEPOT ($DEPUIS)"; exit 2; }
fi
DEPOT="$DEPOT" MEMOIRE="$MEMOIRE" DEPUIS="$DEPUIS" QUAND="$QUAND" python3 - <<'PY'
import glob, json, os, re, sys, time, unicodedata
depot, E = os.environ["DEPOT"], os.environ.get
config = os.path.expanduser(E("CLAUDE_CONFIG_DIR") or "~/.claude")

def dossiers(projets, chemin):              # dossier de projet, nommé comme Claude Code le forme (unités UTF-16)
    n = "".join(c if re.fullmatch(r"[A-Za-z0-9]", c) else ("--" if ord(c) > 0xFFFF else "-") for c in chemin)
    if len(n) <= 200:
        return [os.path.join(projets, n)]
    return sorted(glob.glob(os.path.join(projets, glob.escape(n[:200]) + "-*")))   # coupé, suivi d'une empreinte

def reglage():                              # autoMemoryDirectory : réglages locaux du projet, puis de l'utilisateur
    for f in (os.path.join(depot, ".claude", "settings.local.json"), os.path.join(config, "settings.json")):
        try:
            v = json.load(open(f, encoding="utf-8")).get("autoMemoryDirectory")
        except (OSError, ValueError, AttributeError):
            continue
        if v:
            return os.path.expanduser(v), f
    return None, None

d, source = E("MEMOIRE"), "--memoire"
if not d:
    d, source = reglage()
if d:
    if not os.path.isdir(d):
        print(f"✗ dossier de mémoire introuvable : {d} ({source})"); sys.exit(1)
else:
    projets = os.path.join(config, "projects")
    if not os.path.isdir(projets):
        print(f"· pas de mémoire de Claude Code sur cette machine ({projets} absent) : rien à contrôler ; le tamis se fait dans Claude Code")
        sys.exit(0)
    vus = []
    for forme in dict.fromkeys(unicodedata.normalize(f, depot) for f in ("NFC", "NFD")):   # accents : deux écritures possibles
        vus += dossiers(projets, forme)
    vus = [x for x in dict.fromkeys(vus) if os.path.isdir(os.path.join(x, "memory"))]
    if not vus:
        print(f"· aucune mémoire de Claude Code pour {depot} (aucun dossier memory/ à son nom dans {projets}) : rien à contrôler"
              " ; --memoire DOSSIER si Claude Code a été lancé ailleurs qu'à la racine")
        sys.exit(0)
    d, source = os.path.join(vus[0], "memory"), "dossier du projet"

memoires = sorted(f for f in os.listdir(d) if f.endswith(".md") and f != "MEMORY.md" and os.path.isfile(os.path.join(d, f)))
index_p = os.path.join(d, "MEMORY.md")
print(f"· mémoire lue : {d}")
if not os.path.isfile(index_p):
    if memoires:
        print(f"✗ {len(memoires)} mémoire(s) sans index MEMORY.md : aucune n'est rappelée"); sys.exit(1)
    print("· dossier de mémoire vide : rien à contrôler"); sys.exit(0)
index = open(index_p, encoding="utf-8").read()
textes = {f: open(os.path.join(d, f), encoding="utf-8", errors="replace").read() for f in memoires}
bas = {f.lower() for f in memoires}         # macOS : un nom de fichier se retrouve sans tenir compte de la casse
ko, signal = [], []

# 1. chaque mémoire figure dans l'index : absente, elle n'est jamais rappelée
for f in memoires:
    if f"({f})" not in index:
        ko.append(f"{f} absente de l'index MEMORY.md : jamais rappelée")
# 2. chaque fichier que l'index nomme existe
for t in sorted(set(re.findall(r"\]\(([^)\s/#]+\.md)\)", index))):
    if t.lower() not in bas:
        ko.append(f"MEMORY.md renvoie à {t}, qui n'existe pas")
# 3. chaque lien [[nom]] d'une mémoire mène à une mémoire
for f, t in [("MEMORY.md", index)] + list(textes.items()):
    for lien in sorted(set(re.findall(r"\[\[([^\]\n|#]+)", t))):
        if (lien.strip() + ".md").lower() not in bas and lien.strip().lower() not in bas:
            ko.append(f"{f} : lien [[{lien.strip()}]] vers une mémoire qui n'existe pas")
# 4. index chargé en entier : au-delà de 200 lignes (ou 25000 caractères), Claude Code n'en lit pas la fin
lignes = index.strip().count("\n") + 1
if lignes > 200 or len(index.strip()) > 25000:
    signal.append(f"MEMORY.md : {lignes} lignes, {len(index.strip())} caractères : au-delà de 200 lignes ou 25000 caractères, la fin n'est pas chargée")
# 5. chemins écrits en toutes lettres, entre accents graves : « ~/… » partout, « dossier/… » quand le premier dossier existe à la
#    racine du projet ; un modèle (<…>, …, *, {…}) ou un « fichier:ligne » n'est pas un chemin
chemins, perdus = 0, 0
for f, t in [("MEMORY.md", index)] + list(textes.items()):
    for j in sorted(set(re.findall(r"`([^`\n]+)`", t))):
        j = j.strip().rstrip(".,;:)")
        if re.search(r"[…<>*{}$]|:\d+$|://|\s-", j) or j.startswith(("/", "@", "-")):
            continue
        if j.startswith("~/"):
            cible = os.path.expanduser(j)
        elif "/" in j and " " not in j and os.path.isdir(os.path.join(depot, j.split("/", 1)[0])):
            cible = os.path.join(depot, j)
        else:
            continue
        chemins += 1
        if not os.path.exists(cible):
            perdus += 1
            signal.append(f"{f} cite {j}, introuvable : chemin à corriger, ou à dire retiré")
# 6. aide au tamis : mémoires modifiées depuis l'étiquette d'avant le lot
if E("QUAND"):
    q = int(E("QUAND"))
    neuves = [f for f in ["MEMORY.md"] + memoires if os.path.getmtime(os.path.join(d, f)) >= q]
    quand = time.strftime("%d/%m/%Y %H:%M", time.localtime(q))
    print(f"· modifiées depuis {E('DEPUIS')} ({quand}) : " + (", ".join(neuves) if neuves else "aucune"))
else:
    print("· aucune étiquette avant ce lot : mémoires modifiées non listées, relire chacune de celles que le lot touche"
          " (--depuis ÉTIQUETTE pour borner la liste)")

for x in ko:
    print(f"✗ {x}")
for x in signal:
    print(f"! {x}")
if ko:
    print(f"✗ mémoires à reprendre : {len(ko)} écart(s) sur {len(memoires)} mémoire(s)"); sys.exit(1)
print(f"✓ {len(memoires)} mémoire(s) indexée(s), liens résolus, {chemins - perdus} chemin(s) trouvé(s) sur {chemins}"
      + (" ; signalements ci-dessus à relire" if signal else ""))
PY
