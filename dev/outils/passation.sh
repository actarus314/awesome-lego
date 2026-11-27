#!/bin/bash
# Clôture d'un lot et passation à une nouvelle conversation — générique, piloté par passation.conf
# à la racine du dépôt (voir l'exemple en fin de fichier).
#   passation.sh                       : contrôles
#   passation.sh --suivant LOT[,LOT…]  : à la clôture, chaque lot à lancer ensuite est dans la table des lots du registre
#                                        (AVANCEMENT), ouvert, avec son cahier (LOTS) suivi par git ; rend sa ligne de
#                                        lancement. Remplace --lot et le fichier de reprise (décision du 12/10/2026)
#   passation.sh --strict              : code de sortie 1 si un contrôle échoue (condition pour dire « livré »)
#   passation.sh --skills DIR          : dossier des skills à contrôler (fichiers cités présents, fichiers posés dans le
#                                        dépôt identiques à ceux des skills) ; défaut SKILLS_SOURCE, sinon ~/.claude/skills
#   passation.sh --projet FICHIER      : compare le doc de contexte à sa recopie (projet Claude), lue en entier
#   passation.sh --projet-tete LIGNE   : recopie écrite par project_write local_path (jamais lue en entier) : sa ligne
#                                        d'en-tête lue par project_search doit être celle du contexte, comparées
#                                        jusqu'à la dernière occurrence du motif de l'étiquette (CONTEXTE_MOTIF)
#   passation.sh --annexes [--depot RACINE] : seulement les contrôles --skills / --projet / --projet-tete (sans git, côté
#                                        Claude) ; avec CITES (passation.conf), aussi les fichiers du dépôt cités par les
#                                        skills ; avec --depot, sur un dépôt sans passation.sh ni passation.conf
#   passation.sh --references X [--skills DIR] : sans dépôt : écrit dans le dossier X, ou dans l'archive X si X finit par
#                                        .tgz, les fichiers que chaque skill déclare dans son assets/DEPLOIEMENT, ce script
#                                        et leur MANIFESTE ; affiche leur empreinte
#   passation.sh --maj-outils X [--depot RACINE] [--attendu EMPREINTE] : au début de chaque conversation, lancé depuis la
#                                        copie de référence extraite (X/passation.sh) : remplace dans le dépôt chaque fichier
#                                        posé par une skill qui diffère de sa référence ; passation.conf facultatif
#   passation.sh --voisines LOT        : à la reprise, sans échec : index des lignes du registre et de son archive hors du
#                                        lot qui citent un de ses items, un fichier qu'il possède seul ou un de ses prérequis
#                                        (une ligne par correspondance, jamais la ligne entière) ; « lire en entier » quand le
#                                        registre tient en une lecture ou n'a pas de table des lots (04/11/2026)
#   passation.sh --cibles              : juge la suite de cibles données par un autre outil (une veille, par exemple), une
#                                        par ligne sur l'entrée standard : « horodatage<TAB>lieu<TAB>cible[<TAB>classe] » ;
#                                        « ! » pour chaque cible sans suite, comme le contrôle de suite des constats, et
#                                        par classe le compte des cibles devenues un changement et leur délai (06/11/2026)
set -u
STRICT=0; SUIVANT=""; SKDIR=""; PROJ=""; PROJT=""; ANNEXES=0; REFS=""; MAJ=""; RACINE_OPT=""; ATTENDU=""; VOISINES=""; CIBLES=0
while [ $# -gt 0 ]; do case "$1" in
  --strict) STRICT=1;; --annexes) ANNEXES=1;; --cibles) CIBLES=1;;
  --voisines) [ -n "${2:-}" ] || { echo "$1 : valeur manquante (lot de la table des lots, ex. --voisines L3)"; exit 2; }
    VOISINES="$2"; shift;;
  --lot) echo "--lot est retiré : plus de fichier de reprise (décision du 12/10/2026 ; la reprise tient par le CLAUDE.md du dépôt,"
    echo "la ligne de lancement et le cahier du lot). À la clôture : passation.sh --strict --suivant <lot> vérifie que le lot"
    echo "suivant est dans la table des lots avec son cahier, et rend sa ligne de lancement."; exit 2;;
  --suivant) [ -n "${2:-}" ] || { echo "$1 : valeur manquante (lot de la table des lots, ex. --suivant L3)"; exit 2; }
    SUIVANT="$SUIVANT ${2//,/ }"; shift;;
  --skills) SKDIR="${2:-}"; shift;;
  --references|--maj-outils|--depot|--attendu) [ -n "${2:-}" ] || { echo "$1 : valeur manquante"; exit 2; }
    case "$1" in --references) REFS="$2";; --maj-outils) MAJ="$2";; --depot) RACINE_OPT="$2";; *) ATTENDU="$2";; esac; shift;;
  --projet|--projet-tete) [ -n "${2:-}" ] || { echo "$1 : valeur manquante"; exit 2; }   # vide : jamais un faux vert
    [ "$1" = --projet ] && PROJ="$2" || PROJT="$2"; shift;;
  *) echo "option inconnue : $1"; exit 2;; esac; shift; done
# chemins donnés en option : lus depuis le dossier d'appel, avant de se placer à la racine
abs(){ python3 -c 'import os,sys;print(os.path.abspath(os.path.expanduser(sys.argv[1])))' "$1"; }
[ -n "$SKDIR" ] && SKDIR="$(abs "$SKDIR")"; [ -n "$PROJ" ] && PROJ="$(abs "$PROJ")"
[ -n "$MAJ" ] && MAJ="$(abs "$MAJ")"; [ -n "$RACINE_OPT" ] && RACINE_OPT="$(abs "$RACINE_OPT")"
[ -z "$MAJ" ] && [ -n "$ATTENDU" ] && { echo "--attendu ne sert qu'avec --maj-outils"; exit 2; }
[ -z "$MAJ" ] && [ $ANNEXES -eq 0 ] && [ -n "$RACINE_OPT" ] && { echo "--depot ne sert qu'avec --maj-outils ou --annexes"; exit 2; }


# ---------- déploiement : les fichiers que les skills posent dans un dépôt, lus dans leur assets/DEPLOIEMENT ----------
# aucun nom de skill ici : une skill qui pose un fichier le déclare, et ce script la découvre
deploiement(){   # $1 : references | maj | annexes ; réglages par l'environnement
  MODE="$1" python3 - <<'PY'
import difflib, hashlib, io, os, re, shlex, subprocess, sys, tarfile
MODE, E = os.environ["MODE"], lambda k: os.environ.get(k, "")
FORMAT = 1                                  # grammaire de DEPLOIEMENT que ce script sait lire
class Ecart(Exception): pass

def skills_de(d):                           # nom -> dossiers des skills de d (une skill ne contient pas de skill)
    vus = {}
    for racine, dirs, fichiers in os.walk(d, followlinks=True):
        dirs[:] = sorted(x for x in dirs if not x.startswith("."))
        if "SKILL.md" in fichiers:
            vus.setdefault(os.path.basename(os.path.normpath(racine)), []).append(racine); dirs[:] = []
    return vus
def fichiers_de(r):                         # chemins relatifs des fichiers d'une skill
    out = []
    for racine, dirs, fichiers in os.walk(r):
        dirs[:] = sorted(x for x in dirs if not x.startswith("."))
        out += [os.path.relpath(os.path.join(racine, f), r) for f in sorted(fichiers) if f != ".DS_Store"]
    return out
def choisir(vus, nom):                      # deux copies différentes d'une skill : jamais un choix silencieux
    l = vus.get(nom, [])
    if len(l) > 1:
        emp = {hashlib.sha256(b"".join(f.encode() + open(os.path.join(r, f), "rb").read() for f in fichiers_de(r))).hexdigest() for r in l}
        if len(emp) > 1:
            raise Ecart(f"skill {nom} : {len(l)} copies différentes ({', '.join(l)}) : en désigner une par --skills")
    return l[0] if l else None
def porte(l):                               # une des copies déclare-t-elle des fichiers à poser ?
    return any(os.path.isfile(os.path.join(x, "assets", "DEPLOIEMENT")) for x in l)
def lire(texte, nom):                       # DEPLOIEMENT -> (version, [(source, destination, condition)], dossier de hooks git)
    fmt, ver, lignes, hooks = None, "", [], ""
    for n, l in enumerate(texte.splitlines(), 1):
        c = l.split()
        if not c or c[0].startswith("#"):
            continue
        if c[0] == "format" and len(c) == 2 and c[1].isdigit(): fmt = int(c[1])
        elif c[0] == "version" and len(c) == 2: ver = c[1]
        elif c[0] == "hooks" and len(c) == 2 and re.fullmatch(r"\{(OUTILS|RACINE)\}/\S+", c[1]): hooks = c[1]
        elif (len(c) == 3 and re.fullmatch(r"\{(OUTILS|DOCS|BLOCS|RACINE)\}/\S*", c[1]) and c[0].endswith("/") == c[1].endswith("/")
              and re.fullmatch(r"present|pose|requis(:[A-Z_]+)?", c[2])):
            lignes.append(tuple(c))
        else:
            raise Ecart(f"{nom}/assets/DEPLOIEMENT, ligne {n} illisible : « {l.strip()[:70]} »")
    if fmt is None:
        raise Ecart(f"{nom}/assets/DEPLOIEMENT sans ligne « format N »")
    if fmt > FORMAT:
        raise Ecart(f"{nom}/assets/DEPLOIEMENT au format {fmt}, ce passation.sh lit le format {FORMAT} : republier la skill qui porte passation.sh")
    return ver, lignes, hooks
def sources(lignes, dispo):                 # une ligne de dossier vaut pour chaque fichier du dossier
    out = []
    for s, d, c in lignes:
        if s.endswith("/"):
            out += [(f, d + f[len(s):], c) for f in dispo if f.startswith(s) and "/" not in f[len(s):]]
        else:
            out.append((s, d, c))
    return out
def memes_versions(versions):               # skills enregistrées une à une : une publication à moitié faite se voit ici
    if len({v for v in versions.values() if v}) > 1:
        raise Ecart("skills de versions différentes (" + ", ".join(f"{n} {v or '?'}" for n, v in sorted(versions.items()))
                    + ") : republier les plus anciennes avant de s'en servir")
def conf():                                 # clés renseignées de passation.conf, pour « requis:CLE »
    c = {}
    try:
        for l in open("passation.conf", encoding="utf-8").read().splitlines():
            m = re.match(r"^([A-Z_]+)=(.*)$", l.strip())
            if m:
                try: v = shlex.split(m.group(2))
                except ValueError: v = [m.group(2)]
                c[m.group(1)] = v[0] if v else ""
    except OSError:
        pass
    return c
def bases():                                # valeur de chaque variable de destination dans ce dépôt
    docs = [os.path.dirname(x) or "." for x in E("DOCS").split()]
    if not docs and E("SANS_CONF"):         # sans passation.conf : un journal détaché se reconnaît à ses deux fichiers
        for racine, dirs, fichiers in os.walk("."):
            dirs[:] = sorted(x for x in dirs if not x.startswith(".") and x not in ("node_modules", "_to_delete"))
            if "journal.html" in fichiers and "journal-data.js" in fichiers:
                docs.append(os.path.normpath(racine))
    return {"OUTILS": [E("OUTILS")] if E("OUTILS") else [], "DOCS": sorted(set(docs)),
            "BLOCS": [E("BLOCS")] if E("BLOCS") else [], "RACINE": ["."]}
def destinations(d, b):
    var, reste = re.fullmatch(r"\{(\w+)\}/(.*)", d).groups()
    return [os.path.normpath(os.path.join(x, reste)) for x in b[var]]
executable = lambda n: n.endswith((".sh", ".command")) or "/hooks/" in n
def git(*a):                                # (code, sortie) d'une commande git du dépôt, par l'enveloppe du projet
    r = subprocess.run(["bash", "-c", E("GITCMD") + ' "$@"', "_", *a], capture_output=True, text=True)
    return r.returncode, r.stdout.strip()

def references():
    d, cible = E("SKDIR"), E("REFS")
    vus, refs, versions, compte = skills_de(d), {}, {}, {}
    for nom in sorted(n for n in vus if porte(vus[n])):
        r = choisir(vus, nom); p = os.path.join(r, "assets", "DEPLOIEMENT")
        if not os.path.isfile(p):
            continue
        t = open(p, encoding="utf-8").read()
        versions[nom], lignes, _ = lire(t, nom)
        for s, _, _ in sources(lignes, fichiers_de(r)):
            if not os.path.isfile(os.path.join(r, s)):
                raise Ecart(f"skill {nom} : {s} déclaré dans assets/DEPLOIEMENT, absent de la skill")
            refs[f"{nom}/{s}"] = open(os.path.join(r, s), "rb").read(); compte[nom] = compte.get(nom, 0) + 1
        refs[f"{nom}/assets/DEPLOIEMENT"] = t.encode("utf-8")
    if not compte:                          # jamais « 0 fichier » en vert : la mise à jour ne remplacerait plus rien
        raise Ecart(f"aucun fichier à déployer dans {d} : aucune skill n'y porte assets/DEPLOIEMENT")
    memes_versions(versions)
    refs["passation.sh"] = open(E("SOI"), "rb").read()      # le script qui jouera --maj-outils, hors de tout dépôt
    man = "".join(f"{hashlib.sha256(c).hexdigest()}  {n}\n" for n, c in sorted(refs.items())).encode("utf-8")
    refs["MANIFESTE"] = man
    if cible.endswith((".tgz", ".tar.gz")):
        os.makedirs(os.path.dirname(cible), exist_ok=True)
        with tarfile.open(cible, "w:gz") as tf:
            for n, c in sorted(refs.items()):
                ti = tarfile.TarInfo(n); ti.size = len(c); ti.mode = 0o755 if executable(n) else 0o644
                tf.addfile(ti, io.BytesIO(c))
    else:
        for n, c in refs.items():
            p = os.path.join(cible, n); os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").write(c); os.chmod(p, 0o755 if executable(n) else 0o644)
    print(f"✓ références écrites dans {cible} : " + ", ".join(f"{n} {k} fichier(s)" for n, k in sorted(compte.items()))
          + f" ; empreinte {hashlib.sha256(man).hexdigest()[:16]}")
    return 0

def maj():
    src, att = E("MAJ"), E("ATTENDU")
    try:
        man = open(os.path.join(src, "MANIFESTE"), "rb").read()
    except OSError:
        raise Ecart(f"{src}/MANIFESTE absent : écrire les références par passation.sh --references")
    emp = hashlib.sha256(man).hexdigest()[:16]
    if att and att != emp:
        raise Ecart(f"références d'empreinte {emp}, {att} attendue : transfert périmé, le refaire sous un nom neuf")
    refs = {}
    for l in man.decode("utf-8").splitlines():
        h, n = l.split("  ", 1)
        try:
            c = open(os.path.join(src, n), "rb").read()
        except OSError:
            c = b""
        if hashlib.sha256(c).hexdigest() != h:
            raise Ecart(f"{n} : contenu différent du MANIFESTE (transfert abîmé)")
        refs[n] = c
    noms = sorted(n[:-len("/assets/DEPLOIEMENT")] for n in refs if n.endswith("/assets/DEPLOIEMENT"))
    if not noms:
        raise Ecart(f"{src} sans aucun DEPLOIEMENT (références d'un format ancien) : les réécrire par passation.sh --references")
    b, cibles, versions, armer = bases(), [], {}, []
    for nom in noms:
        versions[nom], lignes, hooks = lire(refs[f"{nom}/assets/DEPLOIEMENT"].decode("utf-8"), nom)
        for s, d, c in sources(lignes, [n[len(nom) + 1:] for n in refs if n.startswith(nom + "/")]):
            cibles += [(f"{nom}/{s}", p, c) for p in destinations(d, b)]
        armer += destinations(hooks, b) if hooks else []
    memes_versions(versions)
    suivi = git("rev-parse", "--git-dir")[0] == 0
    def au_commit(p):                       # contenu de p au dernier commit, None s'il n'y est pas
        r = subprocess.run(["bash", "-c", E("GITCMD") + " cat-file -p \"HEAD:$1\"", "_", p], capture_output=True)
        return r.stdout if r.returncode == 0 else None
    ko, faits, vus = 0, [], 0
    for n, p, cond in cibles:
        if n in refs and cond == "pose" and suivi and not os.path.exists(p):    # posé d'office dans un dépôt git
            os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
            open(p, "wb").write(refs[n]); os.chmod(p, 0o755 if executable(p) else 0o644)
            vus += 1; faits.append(p); print(f"＋ {p} posé"); continue
        if n not in refs or not os.path.isfile(p):
            continue                        # fichier que ce dépôt n'utilise pas
        vus += 1
        c = open(p, "rb").read()
        if c == refs[n]:
            continue
        if not suivi:
            print(f"✗ {p} diffère de sa référence, et ce dossier n'est pas un dépôt git : non remplacé (rien ne garderait l'ancien)")
            ko = 1; continue
        if au_commit(p) != c:
            print(f"✗ {p} modifié depuis le dernier commit, ou non suivi : non remplacé (commiter, ou reporter l'amélioration dans la skill)")
            ko = 1; continue
        x, y = c.decode("utf-8", "replace").splitlines(), refs[n].decode("utf-8", "replace").splitlines()
        plus = moins = 0
        for l in difflib.ndiff(x, y):
            plus += l.startswith("+ "); moins += l.startswith("- ")
        tmp = os.path.join(os.path.dirname(p) or ".", ".%s.maj-%d" % (os.path.basename(p), os.getpid()))
        try:
            with open(tmp, "wb") as f:
                f.write(refs[n])
            os.chmod(tmp, 0o755 if executable(p) else os.stat(p).st_mode & 0o777)
            os.replace(tmp, p)              # renommage : un script en cours d'exécution garde son ancien fichier
        except OSError as e:
            print(f"✗ {p} non remplacé ({e}) ; temporaire {tmp} à retirer s'il existe"); ko = 1; continue
        faits.append(p); print(f"↻ {p} remplacé par sa référence (+{plus} −{moins} lignes)")
    for h in armer if suivi else []:        # la configuration git est locale : un clone arrive désarmé
        if not os.path.isdir(h):
            continue
        actuel = git("config", "--local", "core.hooksPath")[1]
        if actuel == h: continue
        if actuel: print(f"✗ core.hooksPath vaut déjà « {actuel} » : hooks de {h} non armés (à trancher à la main)"); ko = 1
        elif git("config", "--local", "core.hooksPath", h)[0] == 0:
            print(f"↻ hooks git armés : core.hooksPath = {h}")
            gd = git("rev-parse", "--git-dir")[1]; anciens = os.path.join(gd, "hooks")
            vieux = sorted(f for f in (os.listdir(anciens) if os.path.isdir(anciens) else []) if not f.endswith(".sample") and os.access(os.path.join(anciens, f), os.X_OK))
            if vieux: print(f"! hooks de {anciens} qui ne tournent plus depuis cet armement : {', '.join(vieux)} (les reporter dans {h} s'ils servent)")
        else: print(f"✗ core.hooksPath non posé ({h})"); ko = 1
    if faits:
        strict = os.path.join(E("OUTILS"), "passation.sh") if E("OUTILS") and os.path.isfile(os.path.join(E("OUTILS"), "passation.sh")) else ""
        print(f"Outils remplacés : {len(faits)}. " + (f"Lancer {strict} --strict, réparer d'abord ce qui passe au rouge, puis un" if strict else "Un")
              + f" commit « Mise à jour des outils » qui ne nomme que : {' '.join(faits)}")
    elif not ko and not vus:
        print(f"✓ aucun fichier posé par les skills dans ce dossier (empreinte {emp}) : rien à mettre à jour")
    elif not ko:
        print(f"✓ outils à jour des skills (empreinte {emp}, {vus} fichier(s) comparé(s))")
    return ko

def annexes():
    d, ko = E("SKDIR"), 0
    vus, b, c = skills_de(d), bases(), conf()
    poses, versions, armer, a_poser = {}, {}, [], set()     # skill -> [(destination, source, requis)]
    suivi = git("rev-parse", "--git-dir")[0] == 0
    for nom in sorted(n for n in vus if porte(vus[n])):
        r = choisir(vus, nom); p = os.path.join(r, "assets", "DEPLOIEMENT")
        if not os.path.isfile(p):
            continue
        versions[nom], lignes, hooks = lire(open(p, encoding="utf-8").read(), nom)
        armer += destinations(hooks, b) if hooks else []
        for s, dst, cond in sources(lignes, fichiers_de(r)):
            requis = cond == "requis" or (cond.startswith("requis:") and bool(c.get(cond[7:])))
            poses.setdefault(nom, []).extend((p2, s, requis) for p2 in destinations(dst, b))
            if cond == "pose": a_poser.update((p2, s) for p2 in destinations(dst, b))
    memes_versions(versions)
    if not versions and b["OUTILS"] and any(os.path.isfile(os.path.join(b["OUTILS"][0], f)) for f in os.listdir(b["OUTILS"][0])):
        print(f"✗ aucune skill de {d} ne déclare de fichiers à poser (assets/DEPLOIEMENT) : copie des skills plus ancienne que ce script, outils du dépôt non comparés"); ko = 1
    ici = [n for n, l in poses.items() if any(q or os.path.exists(p) for p, _, q in l)]     # skills dont ce dépôt porte un fichier
    projet = [x.rsplit(":", 1)[-1] for x in E("SKILLS").split()]                             # « compte:nom » : le nom seul
    textes = {}
    for nom in dict.fromkeys(projet + ici):
        r = choisir(vus, nom)
        if not r:
            print(f"✗ skill {nom} introuvable dans {d}"); ko = 1; continue
        t = textes[nom] = open(os.path.join(r, "SKILL.md"), encoding="utf-8").read()
        cites = sorted(set(re.findall(r"`((?:references|scripts|assets)/[^`\s]+)`", t)))
        ailleurs = lambda x: any(os.path.exists(os.path.join(y, x)) for l in vus.values() for y in l)
        manque = [x for x in cites if not os.path.exists(os.path.join(r, x)) and not ailleurs(x)]   # citation d'une skill voisine admise
        if manque: print(f"✗ skill {nom} : fichiers cités absents : {', '.join(manque)}"); ko = 1
        else: print(f"✓ skill {nom} : {len(cites)} fichier(s) cité(s), tous présents")
    for nom in ici:
        r = choisir(vus, nom)
        for p, s, requis in poses[nom]:
            if not os.path.exists(os.path.join(r, s)): print(f"✗ skill {nom} : {s} déclaré dans assets/DEPLOIEMENT, absent de la skill"); ko = 1
            elif not os.path.exists(p):
                if requis: print(f"✗ {p} absent (copier {s} de {nom})"); ko = 1
                elif (p, s) in a_poser: print(f"· {p} absent : passation.sh --maj-outils le pose" + (" et l'arme" if "/hooks/" in p else ""))
                else: print(f"· {p} absent du dépôt (non utilisé ici)")
            elif open(p, "rb").read() == open(os.path.join(r, s), "rb").read(): print(f"✓ {p} identique à {nom}")
            else: print(f"✗ {p} diffère de {s} de {nom} : reporter le plus complet des deux, la skill d'abord"); ko = 1
    for h in armer if suivi else []:
        if not os.path.isdir(h): continue
        if git("config", "--local", "core.hooksPath")[1] == h: print(f"✓ hooks git armés ({h})")
        else: print(f"✗ hooks de {h} désarmés (clone, ou dépôt jamais mis à jour) : passation.sh --maj-outils les arme"); ko = 1
    # fichiers du dépôt cités par les skills du projet (CITES) : un fichier cité qui disparaît ne passe pas au vert
    _noms = []
    def noms_depot():                       # noms de fichiers du dépôt (hors dossiers cachés), lus une fois
        if not _noms:
            n = set()
            for _, ds, fs in os.walk("."):
                ds[:] = [x for x in ds if not x.startswith(".")]
                n |= set(fs)
            _noms.append(n)
        return _noms[0]
    for P in E("CITES").split():
        P = P.rstrip("/") + "/"
        if not os.path.isdir(P): print(f"✗ {P} (CITES de passation.conf) absent du dépôt"); ko = 1; continue
        exts = {os.path.splitext(f)[1] for f in os.listdir(P) if os.path.isfile(os.path.join(P, f))}
        cites, manque = set(), []
        for nom in projet:
            t = textes.get(nom, "")
            jetons = set(re.findall(r"`([^`\s]+)`", t))
            if not any(j.startswith(P) for j in jetons): continue          # skill qui ne cite pas le dossier
            for j in sorted({re.sub(r"(#.*|:\d+(-\d+)?)$", "", x) for x in jetons if "*" not in x}):   # sans ancre ni ligne ; motifs écartés
                if j.startswith(P) and j != P: x = j                  # chemin complet
                elif "/" not in j and os.path.splitext(j)[1] in exts: x = P + j      # nom seul : dans le dossier, sinon ailleurs
                else: continue
                if os.path.exists(x): cites.add(os.path.normpath(x))
                elif not ("/" not in j and j in noms_depot()): manque.append(f"{j} ({nom})")
        if manque: print(f"✗ {P} : fichiers cités par une skill absents du dépôt : {', '.join(manque)}"); ko = 1
        else: print(f"✓ {P} : {len(cites)} fichier(s) cité(s) par les skills, tous présents")
        seuls = sorted(f for f in os.listdir(P) if os.path.isfile(os.path.join(P, f)) and os.path.normpath(P + f) not in cites)
        if seuls: print(f"· {P} : fichier(s) cité(s) par aucune skill : {', '.join(seuls)}")
    return ko

try:
    sys.exit({"references": references, "maj": maj, "annexes": annexes}[MODE]())
except Ecart as e:
    print(f"✗ {e}"); sys.exit(1)
PY
}

# ---------- copies de référence : lues dans les skills par ce script, jamais dans la conversation ----------
if [ -n "$REFS" ]; then
  [ -n "$SKDIR" ] || SKDIR="$HOME/.claude/skills"
  [ -d "$SKDIR" ] || { echo "✗ --skills : dossier introuvable ($SKDIR)"; exit 2; }
  SKDIR="$SKDIR" REFS="$(abs "$REFS")" SOI="$(abs "$0")" deploiement references
  exit $?
fi

# chemins physiques des deux côtés : sous un lien (/var, /tmp sur macOS), git rend le chemin réel
ICI="$(cd "$(dirname "$0")" && pwd -P)"
if [ -n "$RACINE_OPT" ]; then RACINE="$(git -C "$RACINE_OPT" rev-parse --show-toplevel 2>/dev/null || (cd "$RACINE_OPT" && pwd -P))"
else
RACINE="$(git -C "$ICI" rev-parse --show-toplevel 2>/dev/null)"
[ -n "$RACINE" ] || { RACINE="$ICI"; while [ "$RACINE" != / ] && [ ! -f "$RACINE/passation.conf" ]; do RACINE="$(dirname "$RACINE")"; done; }
fi
cd "$RACINE" || exit 1
SANS_CONF=""
if [ ! -f passation.conf ]; then
  [ -n "$MAJ" ] || [ $ANNEXES -eq 1 ] || { echo "passation.conf absent à la racine du dépôt ($RACINE)"; exit 2; }
  SANS_CONF=1                   # dépôt sans suivi (une pièce, un document révisé) : ses outils se mettent à jour quand même
fi
# Valeurs par défaut, surchargées par passation.conf
PROJET="$(basename "$RACINE")"
GIT="git"                       # ou un wrapper (gitw.sh)
CONTEXTE="orientation.md"       # doc de contexte, à jour en place, recopié dans le projet Claude
FEUILLE=""                      # feuille de route (facultatif) ; préfixe d'étiquette FEUILLE_TAG
FEUILLE_TAG="feuille-de-route-"   # l'en-tête de la feuille porte « Statut : vX.Y »
LIVRABLES=""                    # "préfixe_tag:fichier_journal:fichier_version" séparés par des espaces
                                #   ex. "app-v:app/CHANGELOG.md:app/config/settings.py"
JOURNAL_MAX=600                 # longueur maximale (caractères, espaces réduits) de l'entrée de la dernière étiquette de chaque
                                #   journal de LIVRABLES : « deux phrases » (passation, étape 4) ; 0 : non contrôlé
SYNTHESE_MAX=300                # longueur maximale de chaque synthèse de série « # vN.x — … » de ces journaux ; 0 : non contrôlé
DOCS=""                         # documents web suivis par un journal détaché (journal.html et journal-data.js à côté)
BLOCS=""                        # dossier des sources où vivent les blocs réutilisables de document-versionne (assets/blocs/),
                                #   ex. "dev/src" : chaque bloc présent doit être identique à celui de la skill
CONTEXTE_MOTIF=""               # comment le contexte nomme l'étiquette livrée (printf), ex. 'étiquette **%s**' ; vide : l'étiquette quelque part
AVANCEMENT=""                   # registre unique de ce qui reste à faire (ex. dev/AVANCEMENT.md) : en-tête à l'étiquette livrée (CONTEXTE_MOTIF),
                                #   identifiants uniques, et le contexte ne tient plus de liste à faire (sections Reporté, Prochaines étapes…)
ARCHIVE_AVANCEMENT=""           # archive des lignes closes du registre (facultatif, ex. dev/AVANCEMENT-clos.md) : un identifiant
                                #   n'existe qu'une fois sur le registre et son archive (06/10/2026)
LISTES_PERMISES=""              # fichiers versionnés autorisés à tenir des cases à cocher malgré le registre (exception nommée, chemins séparés par des espaces)
INDEX_PIECES=""                 # index tabulé numero,date,type,dossier,montant,sha,fichier (facultatif)
SKILLS="document-versionne passation"
CITES=""                        # dossiers du dépôt dont les skills de SKILLS citent les fichiers (ex. "dev/methode/") : --annexes
                                #   vérifie que chaque fichier cité existe (chemin complet, ou nom seul dans une skill qui cite le
                                #   dossier) et signale les fichiers du dossier qu'aucune skill ne cite
CONTROLES=""                    # contrôles avant relecture du projet (noms séparés par des espaces, ex. "différentiel sonde fuzz") :
                                #   à partir de CONSTATS_DEPUIS, le commit étiqueté porte une ligne « Contrôles: » qui donne le
                                #   résultat de chacun (« différentiel rien ; sonde 1 (<ID>) ; fuzz rien ») ; vide : non exigée
REVUE_MOTIFS=10                 # revue des motifs (règle de passation) due toutes les N étiquettes livrées
                                #   depuis la dernière revue (étiquette REVUE_TAG<étiquette du lot>), ou depuis CONSTATS_DEPUIS, et
                                #   après toute majeure vN.0 livrée sans revue ; 0 : non suivie (ni l'un ni l'autre)
REVUE_TAG="revue-motifs-"
LOTS="dev/lots"                 # dossier des cahiers de lots (--suivant, vue d'avancement)
VUE_PORT=""                     # force le port de la vue d'avancement (calculé depuis PROJET sinon) ; renseigné, les copies de la
                                #   vue deviennent requises (condition « requis:VUE_PORT » d'un DEPLOIEMENT)
OUTILS=""                       # dossier d'outils du dépôt ; vide : celui de ce script, de l'enveloppe GIT, sinon dev/outils/ ou outils/
SKILLS_SOURCE=""                # dossier des skills dans le dépôt qui en est la source (ex. "skills") : --skills par défaut
REPRISE=""                      # commande lancée à chaque passage (04/11/2026), ex. un contrôle de veille : code 0 à jour ; code 1
                                #   (geste dû) ou autre (contrôle impossible) : échec sans --strict (la reprise), « ! » sous
                                #   --strict, si bien qu'elle ne bloque jamais une livraison ; vide : rien
LIGNE_MAX=""                    # longueur au-delà de laquelle une ligne du registre est signalée (caractères), « ! » sans échec ;
                                #   vide : non contrôlée (04/11/2026)
SAVOIR_LIGNES=60                # section « Savoir » du contexte (06/11/2026) : au plus tant de lignes de liste, de tant de caractères
                                #   (valeurs posées le 06/11/2026, sans mesure)
SAVOIR_CAR=300                  #   chacune ; au-delà, « ! » sans échec ; 0 : non contrôlé ; non numérique ou négatif : échec
VOISINES_OCTETS=50000           # --voisines : un registre de cette taille ou moins tient en une lecture : plafond de 25000 jetons de
                                #   l'outil de lecture, à 2.14 à 2.67 octets par jeton (registre de 146 à 182 Ko pour 68058 jetons
                                #   le 23/10/2026, contexte de 76291 octets pour 33338 jetons le 04/11/2026), avec marge
[ -n "$SANS_CONF" ] || . ./passation.conf

[ -z "$SKDIR" ] && [ -n "$SKILLS_SOURCE" ] && SKDIR="$RACINE/$SKILLS_SOURCE"
[ -z "$SKDIR" ] && [ -d "$HOME/.claude/skills" ] && SKDIR="$HOME/.claude/skills"

ko=0; echec(){ printf '✗ %s\n' "$*"; ko=1; }; ok(){ printf '✓ %s\n' "$*"; }; note(){ printf '· %s\n' "$*"; }
derniere(){ $GIT tag -l "$1*" --sort=-v:refname 2>/dev/null | head -1; }
if [ -n "$OUTILS" ]; then OUTILS="${OUTILS%/}"; [ -d "$OUTILS" ] || { echo "✗ OUTILS de passation.conf : dossier absent ($OUTILS)"; exit 2; }
else
  case "$ICI/" in "$RACINE"/*) [ "$ICI" != "$RACINE" ] && OUTILS="${ICI#"$RACINE"/}";; esac   # ce script vit dans le dépôt
  [ "$ICI" = "$RACINE" ] && OUTILS="."
  G="${GIT##* }"                                # enveloppe git du dépôt : le dossier d'outils est le sien
  [ -z "$OUTILS" ] && [ "$G" != "${G%/*}" ] && [ -f "$G" ] && OUTILS="${G%/*}"
  [ -n "$OUTILS" ] || for c in dev/outils outils; do [ -d "$c" ] && { OUTILS="$c"; break; }; done
fi

# ---------- mise à jour des outils à la reprise ----------
# lancé depuis la copie de référence (--references, extraite hors du dépôt), avec --depot : un script ancien ne connaît
# pas cette option. Un fichier du dépôt modifié depuis le dernier commit n'est jamais écrasé (amélioration à reporter
# d'abord dans la skill).
if [ -n "$MAJ" ]; then
  [ -n "$OUTILS" ] || note "aucun dossier d'outils (OUTILS de passation.conf, dev/outils/ ou outils/) dans $RACINE : scripts non comparés"
  MAJ="$MAJ" ATTENDU="$ATTENDU" OUTILS="$OUTILS" DOCS="$DOCS" BLOCS="$BLOCS" GITCMD="$GIT" SANS_CONF="$SANS_CONF" deploiement maj
  exit $?
fi

# ---------- annexes : skills et recopie du contexte (sans git) ----------
annexes(){
  if [ -n "$SKDIR" ] && [ -d "$SKDIR" ]; then
    SKDIR="$SKDIR" SKILLS="$SKILLS" CITES="$CITES" OUTILS="$OUTILS" DOCS="$DOCS" BLOCS="$BLOCS" GITCMD="$GIT" SANS_CONF="$SANS_CONF" deploiement annexes || ko=1
  elif [ -n "$SKDIR" ]; then echec "--skills : dossier introuvable ($SKDIR)"
  else note "skills non contrôlées ici (--skills DIR, ou ~/.claude/skills absent) : lancer --annexes côté Claude"; fi
  if [ -n "$PROJ" ]; then
    if python3 -c 'import sys;a,b=(open(f,encoding="utf-8").read().rstrip("\n") for f in sys.argv[1:]);sys.exit(a!=b)' "$CONTEXTE" "$PROJ" 2>/dev/null; then
      ok "$CONTEXTE identique à sa recopie ($PROJ)"
    else echec "$CONTEXTE diffère de sa recopie ($PROJ), ou l'un des deux est illisible : la refaire (project_write)"; fi
  fi
  # 06/10/2026 : la recopie s'écrit par project_write local_path (octets du fichier, jamais lus dans la conversation) ;
  # project_search en rend le premier morceau : sa ligne d'en-tête (celle qui porte CONTEXTE_MOTIF) doit être
  # celle du contexte. created_at de project_info n'est pas rafraîchi quand un doc est remplacé (06/10/2026).
  if [ -n "$PROJT" ]; then
    R=$(CONTEXTE_MOTIF="$CONTEXTE_MOTIF" python3 - "$CONTEXTE" "$PROJT" <<'PY'
import os, re, sys
try:
    lignes = [l.strip() for l in open(sys.argv[1], encoding="utf-8").read().splitlines()]
except (OSError, UnicodeDecodeError) as e:
    print("illisible\t%s" % e); sys.exit()
m = os.environ.get("CONTEXTE_MOTIF", "")
n = lambda x: " ".join(x.split())
if m:                                   # motif de la version, chaque %s pris en entier (sans espace)
    rx = re.compile(r"\S+".join(re.escape(x) for x in m.split("%s")))
    def coupe(l):                       # ligne coupée après la dernière occurrence du motif, None sans motif
        f = [x.end() for x in rx.finditer(l)]
        return n(l[:f[-1]]) if f else None
    tete = next((coupe(l) for l in lignes if coupe(l)), None)
    autre = coupe(sys.argv[2])
else:                                   # sans motif : première ligne non vide après le titre, entière
    tete = next((n(l) for l in lignes if l and not l.startswith("#")), None)
    autre = n(sys.argv[2])
if tete is None: print("illisible\taucune ligne portant le motif dans le contexte"); sys.exit()
print("%s\t%s" % ("ok" if autre == tete else "autre", tete))
PY
)
    IFS=$'\t' read -r E T <<< "$R"
    case "$E" in
      ok) ok "recopie de $CONTEXTE à jour (en-tête : « $T »)";;
      autre) echec "recopie de $CONTEXTE : son en-tête ne commence pas par « $T » : la refaire (project_write local_path)";;
      *) echec "--projet-tete : $CONTEXTE illisible ou sans en-tête ($T)";;
    esac
  fi
  if [ -z "$PROJ$PROJT" ] && [ -f "$CONTEXTE" ]; then note "empreinte de $CONTEXTE : $(shasum -a 256 "$CONTEXTE" | cut -c1-16) (recopie du projet Claude : --projet-tete, ou --projet)"; fi
}
if [ $ANNEXES -eq 1 ]; then [ -n "$SUIVANT" ] && note "--suivant ignoré avec --annexes (le lot suivant se contrôle sur le dépôt)"; annexes; [ $ko -eq 0 ] && echo "Annexes à jour." || { echo "Annexes à reprendre."; [ $STRICT -eq 1 ] && exit 1; }; exit 0; fi

# ---------- registre : passe ligne à ligne, « fait » des lots d'étude, voisines (04/11/2026) ----------
# colonnes lues par le nom de leur en-tête, jamais par leur position : l'archive d'un dépôt peut ranger ses colonnes
# autrement que son registre. Sortie : une ligne « ok|ko|note|signal<TAB>texte » par constat
REGISTRE_DEPUIS=1793746800      # 04/11/2026 00:00 heure de Paris : bloc « Registre: » exigé à partir de là (étiquette, ou
                                #   commit qui écrit « fait JJ/MM » d'un lot d'étude)
FAIT_DEPUIS=1793574000          # 02/11/2026 00:00 heure de Paris : « fait JJ/MM » d'un lot d'étude porte « ; arrivé : <lieu> »
SUITE_DEPUIS=1793977200         # 06/11/2026 16:00 heure de Paris, entrée de la règle : lignes « non joué : » des cahiers suivies
                                #   à partir de là (les plus anciennes sont l histoire des lots)
registre(){                     # $1 : etiquette <T> | etudes | voisines <lot> | longueurs | suite | cibles | savoir
  MODE="$1" CIBLE="${2:-}" AV="$AVANCEMENT" AR="$ARCHIVE_AVANCEMENT" CTX="$CONTEXTE" LOTS_DIR="${LOTS%/}" GITCMD="$GIT" \
  RD="$REGISTRE_DEPUIS" FD="$FAIT_DEPUIS" VO="$VOISINES_OCTETS" LM="$LIGNE_MAX" \
  CD="${CONSTATS_DEPUIS:-0}" SD="$SUITE_DEPUIS" PREFS="${SUITE_PREFS:-}" SL="$SAVOIR_LIGNES" SC="$SAVOIR_CAR" python3 - <<'PY'
import os, re, subprocess, sys
E = lambda k: os.environ.get(k, "")
AV, AR, CTX, LOTS = E("AV"), E("AR"), E("CTX"), E("LOTS_DIR")
ID = r"[A-Z][A-Z0-9]{1,5}-[A-Z0-9]*\d[A-Z0-9]*"        # préfixe de capitales, tiret, numéro (lettres admises après le tiret)
CLOS = re.compile(r"(fait|abandonné|fusionné)\b")       # les trois statuts clos de passation
REPARER = "à corriger avant d'étiqueter ; une étiquette posée ne se reprend pas : la suivante porte le bloc"
def dire(etat, texte):
    print(etat + "\t" + " ".join(str(texte).split()))
def git(*a, entree=None):
    r = subprocess.run(["bash", "-c", E("GITCMD") + ' "$@"', "_", *a], capture_output=True, input=entree)
    return r.returncode, r.stdout.decode("utf-8", "replace")
def lire(chemin, rev=None):
    if not chemin:
        return ""
    if rev is None:
        try:
            return open(chemin, encoding="utf-8").read()
        except OSError:
            return ""
    c, t = git("show", "%s:%s" % (rev, chemin))
    return t if c == 0 else ""
def lire_lot(revs, chemin):                # plusieurs révisions d un fichier en un seul appel à git (cat-file --batch)
    if not revs:
        return {}
    r = subprocess.run(["bash", "-c", E("GITCMD") + ' "$@"', "_", "cat-file", "--batch"], capture_output=True,
                       input="".join("%s:%s\n" % (x, chemin) for x in revs).encode("utf-8"))
    out, b, i = {}, r.stdout, 0
    for x in revs:
        j = b.index(b"\n", i); tete = b[i:j].split(); i = j + 1
        if len(tete) == 3:
            n = int(tete[2]); out[x] = b[i:i + n].decode("utf-8", "replace"); i += n + 1
        else:
            out[x] = ""                        # « missing » : fichier absent à cette révision
    return out
def cellules(l):
    return [x.strip() for x in re.split(r"(?<!\\)\|", l.strip().strip("|"))]
def tables(texte):                         # [(en-tête en minuscules, lignes en cellules, lignes brutes)]
    out, ent = [], None
    for l in texte.splitlines():
        if not l.startswith("|"):
            ent = None; continue
        if ent is None:
            ent = [x.lower() for x in cellules(l)]; out.append((ent, [], [])); continue
        if re.fullmatch(r"[-: |]+", l.strip()):
            continue
        out[-1][1].append(cellules(l)); out[-1][2].append(l)
    return out
def col(ent, *noms):                       # première colonne dont l en-tête commence par un des noms
    return next((k for k, x in enumerate(ent) if any(x.startswith(n) for n in noms)), None)
val = lambda c, i: c[i] if i is not None and i < len(c) else ""
def lots_de(texte):                        # table des lots : nom -> cellules utiles ; None sans table (lecture arrêtée après elle)
    ent, rows = None, []
    for l in texte.splitlines():
        if ent is None:
            if l.startswith("|") and cellules(l)[0].lower() == "lot":
                ent = [x.lower() for x in cellules(l)]
            continue
        if not l.startswith("|"):
            break
        if not re.fullmatch(r"[-: |]+", l.strip()):
            rows.append(cellules(l))
    if ent is None:
        return None
    it, st, fi, pr = col(ent, "item"), col(ent, "statut"), col(ent, "fichier"), col(ent, "prér", "prer")
    st = len(ent) - 1 if st is None else st
    return {c[0]: {"items": val(c, it), "statut": val(c, st), "fichiers": val(c, fi), "prereq": val(c, pr)} for c in rows if c and c[0]}
def lignes_de(texte):                      # tables dont la première colonne est ID : ID -> ligne
    out = {}
    for ent, rows, bruts in tables(texte):
        if ent and ent[0] == "id":
            st, li, de = col(ent, "statut"), col(ent, "ligne"), col(ent, "dépend", "dép.", "dep")
            st = len(ent) - 1 if st is None else st
            for c, b in zip(rows, bruts):
                if c and re.fullmatch(ID, c[0]):
                    texte_l = val(c, li) if li is not None else max((x for k, x in enumerate(c) if k not in (0, st, de)), key=len, default="")
                    out.setdefault(c[0], {"statut": val(c, st), "ligne": texte_l, "dep": val(c, de), "brut": b})
    return out
def ids(texte):                            # identifiants cités ; une plage « X-3 à X-6 » ou « X-3 à 6 » est dépliée
    vus = []
    for m in re.finditer(r"\b(%s)\b(?:\s+à\s+(?:([A-Z][A-Z0-9]{1,5})-)?(\d+)\b(?!\s*%%|[.,]\d))?" % ID, texte):
        a = m.group(1); vus.append(a)
        pa, na = a.rsplit("-", 1)
        if m.group(3) and na.isdigit():
            pb, nb = m.group(2) or pa, int(m.group(3))
            if pb == pa and int(na) < nb <= int(na) + 200:
                vus += ["%s-%d" % (pa, n) for n in range(int(na) + 1, nb + 1)]
            elif m.group(2):
                vus.append("%s-%d" % (pb, nb))
    return list(dict.fromkeys(vus))
def cahiers(statut):                       # chemins de cahiers cités dans un statut
    return re.findall(r"(?:^|[\s`(])(" + re.escape(LOTS) + r"/[^`\s)]+\.md)", statut)
def premier_cahier(lot, statut):           # même règle que --suivant : le cahier au nom du lot, sinon le premier cité
    c = cahiers(statut)
    siens = [x for x in c if os.path.basename(x).startswith(lot + "-") or os.path.basename(x) == lot + ".md"]
    return (siens or c or [None])[0]
def bloc(msg):                             # bloc « Registre: » d un message de commit : (verdicts, écarts) ; None absent
    l = msg.splitlines()
    i = next((k for k, x in enumerate(l) if x.startswith("Registre:")), None)
    if i is None:
        return None, []
    v, mal = {}, []
    if l[i][len("Registre:"):].strip():
        mal.append("« Registre: » suivi de texte sur sa ligne (une ligne par identifiant en dessous)")
    for x in l[i + 1:]:
        if not x.startswith("- "):
            break
        m = re.fullmatch(r"- (\S+) : (close|ouverte|inchangée)(?: — \S.*)?", x.rstrip())
        if not m:
            mal.append("ligne « %s » illisible (- <ID> : close | ouverte | inchangée[ — remesuré : …])" % x[:60])
        elif m.group(1) in v:
            mal.append("%s : deux verdicts" % m.group(1))
        else:
            v[m.group(1)] = m.group(2)
    if not v and not mal:
        mal.append("bloc « Registre: » vide")
    return v, mal
def passe(rev, avant, msg, fermes, quoi):  # (écarts, signaux) du bloc Registre: d un commit qui passe des lots à « fait »
    av = lire(AV, rev)
    L, lg, la = lots_de(av) or {}, lignes_de(av), lignes_de(lire(AR, rev))
    connus = set(L) | set(lg) | set(la)
    attendus = list(dict.fromkeys(x for n in fermes for x in [n] + ids(L.get(n, {}).get("items", ""))))
    signaux = ["%s : %s cité dans les items de %s, absent de la table des lots, du registre et de l'archive : sans verdict exigé"
               % (quoi, x, ", ".join(fermes)) for x in attendus if x not in connus]
    attendus = [x for x in attendus if x in connus]
    ecarts = []
    if AR:                                 # lignes descendues depuis la révision d avant : closes ; les plus anciennes, signalées
        anciennes = set(lignes_de(lire(AR, avant))) if avant else set()
        ouvertes = [x for x, d in la.items() if not CLOS.match(d["statut"])]
        neuves = [x for x in ouvertes if x not in anciennes]
        if neuves:
            ecarts.append("%s : %s reçoit des lignes au statut non clos (fait, abandonné, fusionné) : %s" % (quoi, AR, ", ".join(neuves[:8])))
        if len(ouvertes) > len(neuves):
            signaux.append("%s : %s garde %d ligne(s) plus ancienne(s) au statut non clos : %s" % (quoi, AR, len(ouvertes) - len(neuves),
                           ", ".join(x for x in ouvertes if x in anciennes)[:200]))
    v, mal = bloc(msg)
    if v is None:
        ecarts.append("%s : bloc « Registre: » absent (une ligne par item de %s et par lot : « - <ID> : close | ouverte | inchangée »)"
                      % (quoi, ", ".join(fermes)))
        return ecarts, signaux
    ecarts += ["%s : %s" % (quoi, x) for x in mal]
    sans = [x for x in attendus if x not in v]
    if sans:
        ecarts.append("%s : sans verdict dans « Registre: » : %s%s" % (quoi, ", ".join(sans[:12]), " (+%d)" % (len(sans) - 12) if len(sans) > 12 else ""))
    for x, verdict in v.items():
        st = L[x]["statut"] if x in L else (lg.get(x) or la.get(x) or {}).get("statut")
        if st is None:
            ecarts.append("%s : %s absent de la table des lots, du registre et de l'archive" % (quoi, x)); continue
        if (verdict == "close") != bool(CLOS.match(st)):
            ecarts.append("%s : %s « %s » contre son statut « %s »" % (quoi, x, verdict, st[:40]))
    return ecarts, signaux
def rendre_passe(e, s, quoi_ok, conseil):
    for x in s:
        dire("signal", x)
    for x in e:
        dire("ko", "%s (passe ligne à ligne de passation ; %s)" % (x, conseil))
    if not e:
        dire("ok", quoi_ok)

MODE, CIBLE = E("MODE"), E("CIBLE")
if MODE == "etiquette":                    # étiquette livrée : les lots passés à « fait <étiquette> »
    L = lots_de(lire(AV, CIBLE)) or {}
    fermes = [n for n, d in L.items() if re.match(r"fait %s(?![\w.])" % re.escape(CIBLE), d["statut"])]
    if not fermes:
        dire("note", "%s : aucun lot « fait %s » dans la table des lots : bloc Registre: non exigé" % (CIBLE, CIBLE))
    else:
        c, avant = git("describe", "--tags", "--abbrev=0", CIBLE + "^")
        e, s = passe(CIBLE, avant.strip() if c == 0 else None, git("log", "-1", "--format=%B", CIBLE)[1], fermes, CIBLE)
        rendre_passe(e, s, "%s : bloc Registre conforme (%s)" % (CIBLE, ", ".join(fermes)), REPARER)
elif MODE == "etudes":                     # lots d étude : le commit qui écrit « fait JJ/MM »
    actuels = lots_de(lire(AV)) or {}
    etude = lambda st: re.match(r"fait \d{2}/\d{2}\b", st or "")
    depuis = min(int(E("RD")), int(E("FD")))
    # seuls les commits qui ajoutent ou retirent une ligne portant « fait JJ/MM » (git log -G) : le coût ne suit pas
    # le nombre de commits du registre
    _, journal = git("log", "--reverse", "-G", "fait [0-9][0-9]/[0-9][0-9]", "--format=%H %ct", "--", AV)
    # dates filtrées ici, pas par --since, qui arrête le parcours au premier commit plus ancien (06/11/2026)
    commits = [c for c in (l.split() for l in journal.splitlines() if l.strip()) if int(c[1]) >= depuis]
    textes = lire_lot([h for h, _ in commits] + [h + "^" for h, _ in commits], AV)
    ecrit = {}
    for h, ct in commits:
        avant, apres = lots_de(textes[h + "^"]) or {}, lots_de(textes[h]) or {}
        for n, d in apres.items():
            if etude(d["statut"]) and not avant.get(n, {}).get("statut", "").startswith("fait"):
                ecrit[n] = (h, int(ct))
    vus = 0
    for n, (h, ct) in sorted(ecrit.items()):
        if n not in actuels or not etude(actuels[n]["statut"]):
            continue                           # rouvert depuis
        vus += 1; quoi = "lot d'étude %s (fait par %s)" % (n, h[:7])
        L = lots_de(textes[h]) or {}; st = L[n]["statut"]
        if ct >= int(E("FD")):
            m = re.search(r";\s*arrivé\s*:(.*)", st)
            if not m:
                dire("ko", "%s : « fait JJ/MM » sans « ; arrivé : <lieu> » (règle « fait » des lots d'étude, 02/11/2026 ; rouvrir le lot puis l'écrire « fait » dans un commit conforme)" % quoi)
            else:
                chemins = re.findall(r"`([^`\s]+)`", m.group(1))
                touches = git("-c", "core.quotePath=false", "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", h)[1].split("\n")
                siens = set(cahiers(st[:m.start()])) | {x for x in chemins if x.startswith(LOTS + "/") and os.path.basename(x).startswith(n + "-")}
                autres = {premier_cahier(k, d["statut"]) for k, d in L.items() if k != n and not CLOS.match(d["statut"])}
                raisons, bon = [], None
                for p in chemins:
                    q = p.rstrip("/")
                    if q in (AV, AR):
                        raisons.append("%s : le registre ne compte pas" % p)
                    elif git("cat-file", "-e", "%s:%s" % (h, q))[0] != 0:
                        raisons.append("%s : absent au commit" % p)
                    elif not any(f == q or f.startswith(q + "/") for f in touches if f):
                        raisons.append("%s : non modifié par le commit" % p)
                    elif q in siens and q not in autres:
                        raisons.append("%s : cahier cité par le statut du lot, premier cahier d'aucun autre lot ouvert" % p)
                    else:
                        bon = p; break
                if bon:
                    dire("ok", "%s : arrivé à %s" % (quoi, bon))
                else:
                    dire("ko", "%s : aucun lieu d'arrivée valable (%s ; rouvrir le lot puis l'écrire « fait » dans un commit conforme)"
                         % (quoi, " ; ".join(raisons) or "aucun chemin entre accents graves après « arrivé : »"))
        if ct >= int(E("RD")):
            e, s = passe(h, h + "^", git("log", "-1", "--format=%B", h)[1], [n], quoi)
            rendre_passe(e, s, "%s : bloc Registre conforme" % quoi, "rouvrir le lot puis l'écrire « fait » dans un commit conforme")
    if not vus:
        dire("note", "aucun lot d'étude passé à « fait JJ/MM » depuis les dates de contrôle")
elif MODE == "longueurs":                  # LIGNE_MAX : lignes du registre trop longues pour se lire d un coup
    try:
        lm = int(E("LM"))
        if lm < 0:
            raise ValueError
    except ValueError:
        dire("ko", "LIGNE_MAX de passation.conf non numérique ou négatif : « %s »" % E("LM")); sys.exit(0)
    if lm == 0:
        sys.exit(0)                            # 0 : non contrôlé, comme JOURNAL_MAX
    longues = sorted(((len(d["brut"]), x) for x, d in lignes_de(lire(AV)).items() if len(d["brut"]) > lm), reverse=True)
    if longues:
        dire("signal", "%s : %d ligne(s) de plus de %d caractères (LIGNE_MAX) : %s" % (AV, len(longues), lm,
             ", ".join("%s (%d)" % (x, n) for n, x in longues[:8]) + (" (+%d)" % (len(longues) - 8) if len(longues) > 8 else "")))
    else:
        dire("ok", "%s : aucune ligne de plus de %d caractères (LIGNE_MAX)" % (AV, lm))
elif MODE in ("suite", "cibles"):          # suite des constats (06/11/2026) : chaque constat suivi jusqu'à un changement de sa cible
    import statistics, time
    jour = time.strftime("%Y%m%d")
    SANS_LOT = {"", "—", "–", "-"}
    def regl(texte):                       # ID -> (statut, lot, priorité) des tables dont la première colonne est ID
        out = {}
        for ent, rows, bruts in tables(texte):
            if ent and ent[0] == "id":
                st, lo = col(ent, "statut"), col(ent, "lot")
                pr = next((k for k, x in enumerate(ent) if x == "p"), None)   # colonne « P », nom exact
                st = len(ent) - 1 if st is None else st
                for c in rows:
                    if c and re.fullmatch(ID, c[0]):
                        out.setdefault(c[0], (val(c, st), val(c, lo), val(c, pr)))
        return out
    HAUTES = {"P0", "P1", "P2"}            # décision de Romain du 06/11/2026 : seules ces cibles sont signalées
    basses = set()                         # lignes sans suite de priorité P3, P4 ou V : comptées, pas signalées
    memo = {None: (regl(lire(AV)), regl(lire(AR)))}
    def etat(x, rev=None):
        if rev not in memo:
            memo[rev] = (regl(lire(AV, rev)), regl(lire(AR, rev)))
        a, b = memo[rev]
        return a.get(x) or b.get(x)
    date = lambda t: time.strftime("%d/%m/%Y", time.localtime(t))
    def juge_id(x, rev, quand, profondeur=0):   # None : suivie ; sinon la raison du signal
        e = etat(x)
        if e is None:
            return "%s introuvable au registre et à l'archive" % x
        st, lot, prio = e
        def sans_suite(raison):            # une priorité basse est comptée, pas signalée ; priorité absente : signalée
            if prio and prio not in HAUTES and prio not in SANS_LOT:   # « — » vaut priorité absente (14/11)
                basses.add(x)
                return None
            return raison
        if st.startswith("fusionné"):          # une ligne fusionnée vaut ce que vaut la ligne qui la reçoit
            vers = [y for y in ids(st) if y != x]
            return juge_id(vers[0], rev, quand, profondeur + 1) if vers and profondeur < 3 else None
        if CLOS.match(st) or lot not in SANS_LOT:
            return None
        m = re.search(r"échéance (\d{2})/(\d{2})/(\d{4})", st)
        if m and m[3] + m[2] + m[1] >= jour:
            return None
        if m:
            return sans_suite("%s : échéance du %s/%s/%s passée, sans lot" % (x, m[1], m[2], m[3]))
        avant, depuis = etat(x, rev), quand
        if avant is None:                      # ligne née après le constat : jugée depuis sa naissance
            c, t = git("log", "--reverse", "--format=%H %ct", "-G", r"^[|] %s [|]" % x, "--", AV, *([AR] if AR else []))
            nee = next((y.split() for y in t.splitlines() if y.strip() and int(y.split()[1]) >= quand), None)
            if nee is None:
                return None
            avant, depuis = etat(x, nee[0]), int(nee[1])
        if avant is None or avant[:2] != e[:2]:
            return None                        # statut ou lot changés depuis le constat ; la priorité seule ne vaut pas suite (14/11)
        return sans_suite("%s : ni lot ni échéance, statut inchangé depuis le %s" % (x, date(depuis)))
    def juge_chemin(p, quand):
        p = p.strip("`").split(":")[0]
        if not os.path.exists(p):
            return "%s : chemin absent du dépôt" % p
        c, t = git("log", "--format=%ct", "--", p)   # dates filtrées ici : git ne lit pas « --since=@<horodatage> »
        if any(int(x) > quand for x in t.split()):
            return None
        return "%s : aucun commit depuis le %s" % (p, date(quand))
    CHEMIN = r"`[^`\s]+`"
    def juge(cible, rev, quand):           # raisons des signaux d une cible (liste vide : suivie, ou sans suite voulue)
        if re.match(r"\s*(corrigé|écarté\s*:)", cible):
            return []
        # chaque ligne citée est jugée seule ; les chemins sont suivis si l un d eux a reçu un commit depuis le constat,
        # ou si une ligne citée par la même cible est suivie (elle porte le changement)
        li = [juge_id(x, rev, quand) for x in ids(cible)]
        ch = [juge_chemin(p, quand) for p in re.findall(CHEMIN, cible)]
        r = li + (ch if ch and all(ch) and (not li or all(li)) else [])
        if not ids(cible) and not re.findall(CHEMIN, cible):
            nus = re.findall(r"(?<![\w/.~-])[\w.-]+(?:/[\w.-]+)+(?::\d+)?", cible)
            r = [juge_chemin(p, quand) for p in nus] or ["cible illisible « %s » (identifiant, `chemin`, corrigé, ou écarté : raison)"
                                                         % " ".join(cible.split())[:50]]
        return [x for x in r if x]
    if MODE == "cibles":                   # --cibles : lignes « horodatage<TAB>lieu<TAB>cible » d un autre outil (la veille)
        c, t = git("log", "--format=%H %ct", "--", AV, *([AR] if AR else []))
        hist = [x.split() for x in t.splitlines() if x.strip()]
        def change(cible, quand):          # délai (jours) jusqu au premier changement : chemin modifié, ligne écrite « fait »
            d = []
            for p in re.findall(CHEMIN, cible):
                c, t = git("log", "--format=%ct", "--", p.strip("`").split(":")[0])
                d += [int(x) for x in t.split() if int(x) > quand]
            for y in ids(cible):
                if etat(y) and etat(y)[0].startswith("fait"):
                    c, t = git("log", "--format=%ct", "-G", r"^[|] %s [|].*[|] *fait" % y, "--", AV, *([AR] if AR else []))
                    d += [int(x) for x in t.split() if int(x) >= quand]
            return (min(d) - quand) / 86400 if d else None
        classes = {}
        for l in CIBLE.splitlines():
            x = l.split("\t")
            if len(x) < 3 or not x[0].strip().isdigit():
                if l.strip():
                    dire("ko", "--cibles : ligne illisible « %s » (horodatage, lieu, cible[, classe], séparés par des tabulations)" % l[:60])
                continue
            quand = int(x[0])
            k = classes.setdefault(x[3].strip() if len(x) > 3 and x[3].strip() else "cibles", [0, [], 0])
            k[0] += 1
            rev = next((h for h, ct in hist if int(ct) <= quand), None)   # registre tel qu il était au constat
            r = juge(x[2], rev, quand)
            for s in r:
                dire("signal", "suite : %s : %s" % (x[1], s))
            k[2] += bool(r)
            dl = None if re.match(r"\s*écarté", x[2]) else change(x[2], quand)
            if dl is not None:
                k[1].append(dl)
        if basses:
            dire("note", "suite : %d ligne(s) sans suite de priorité P3, P4 ou V, comptée(s) sans signal : %s" % (len(basses), ", ".join(sorted(basses))))
        dire("note", "suite : " + (" ; ".join("%s : %d, dont %d devenu(s) un changement%s, %d sans suite signalé(s)"
             % (nom, v[0], len(v[1]), " (délai médian %.0f j)" % statistics.median(v[1]) if v[1] else "", v[2])
             for nom, v in classes.items()) or "aucune cible"))
        sys.exit(0)
    # 1. blocs Constats: des étiquettes livrées depuis CONSTATS_DEPUIS
    p = [re.escape(x) for x in E("PREFS").split()]
    rx = re.compile("^(" + "|".join(p) + r")[0-9]+\.[0-9]+(\.[0-9]+)?$") if p else None
    c, t = git("for-each-ref", "--sort=creatordate", "--format=%(refname:short) %(committerdate:unix) %(*committerdate:unix)", "refs/tags")
    etiq = [(x[0], int(x[-1])) for x in (l.split() for l in t.splitlines()) if rx and len(x) >= 2 and rx.match(x[0]) and int(x[-1]) >= int(E("CD") or 0)]
    vus, compte, delais, signaux = set(), {"corrigé": 0, "renvoyé": 0, "fait": 0, "écarté": 0}, [], []
    for tag, quand in etiq:
        c, msg = git("log", "-1", "--format=%B", tag)
        l = msg.splitlines()
        i = next((k for k, x in enumerate(l) if x.startswith("Constats:")), None)
        if i is None:
            continue
        for x in l[i + 1:]:
            if not x.startswith("- "):
                break
            m = re.match(r"^(bloquant|à corriger|mineur) : (.+)$", x[2:].strip())
            parts = m[2].rsplit(" — ", 2) if m else []
            if len(parts) < 3:
                continue                       # forme contrôlée par la règle « Constats »
            cle = (m[1], " ".join(parts[0].split()), parts[2].strip())
            if cle in vus:
                continue                       # constat recopié d une étiquette à l autre
            vus.add(cle)
            devenir = parts[2].strip()
            if m[1] == "à corriger":
                if re.match(r"corrigé", devenir) and not ids(devenir): compte["corrigé"] += 1
                elif devenir.startswith("écarté"): compte["écarté"] += 1
                else:
                    compte["renvoyé"] += 1
                    faits = [y for y in ids(devenir) if etat(y) and etat(y)[0].startswith("fait")]
                    if faits and len(faits) == len(ids(devenir)):
                        compte["fait"] += 1
                        premiers = []                  # pour chaque ligne, le premier commit qui l écrit « fait » après le constat
                        for y in faits:
                            c, d = git("log", "--format=%ct", "-G", r"^[|] %s [|].*[|] *fait" % y,
                                       "--", AV, *([AR] if AR else []))   # barre entre crochets : « \\| » est une alternative pour git -G
                            apres = sorted(int(z) for z in d.split() if int(z) >= quand)
                            premiers.append(apres[0] if apres else None)
                        if all(premiers):
                            delais.append((max(premiers) - quand) / 86400)
            reste = re.sub(r"^corrigé\s*(,\s*|$)", "", devenir)
            if m[1] in ("bloquant", "à corriger") and reste and not reste.startswith("écarté"):
                for r in juge(reste, tag, quand):
                    signaux.append("constat de %s « %s » : %s" % (tag, parts[0].strip()[:60], r))
    # 2. lignes « non joué : » des cahiers, écrites depuis SUITE_DEPUIS
    nj = 0
    if LOTS and os.path.isdir(LOTS):
        c, t = git("-c", "core.quotePath=false", "ls-files", "--", LOTS)
        for f in sorted(x for x in t.splitlines() if x.endswith(".md")):
            if not re.search(r"(?i)non jou(é|ée|és|ées)\s*:", lire(f)):
                continue
            c, b = git("blame", "--line-porcelain", "--", f)
            quand, rev = 0, None
            for k, x in enumerate(b.splitlines()):
                if re.match(r"^[0-9a-f]{40} ", x):
                    rev = x.split()[0]
                elif x.startswith("author-time "):
                    quand = int(x.split()[1])
                elif x.startswith("\t"):
                    for m in re.finditer(r"(?i)non jou(?:é|ée|és|ées)\s*:\s*(.*)", x[1:]):
                        avant_m = x[1:m.start()]
                        if quand < int(E("SD") or 0) or avant_m.count("«") > avant_m.count("»") or avant_m.count("`") % 2:
                            continue                   # ligne d avant la règle, ou mention citée entre « » ou accents graves
                        nj += 1
                        reste = m[1]
                        cible = re.split(r"[.;](?:\s|$)", reste, maxsplit=1)[0]   # fin de phrase, après un identifiant compris (14/11)
                        lieu = "%s (ligne du %s)" % (f, date(quand))
                        if not re.match(r"\s*(\*\*)?\s*(%s\b|%s|écarté\s*:\s*\S)" % (ID, CHEMIN), reste):
                            signaux.append("%s : « non joué : %s » sans cible (identifiant, `chemin`, ou écarté : raison)" % (lieu, " ".join(reste.split())[:50]))
                            continue
                        for r in juge(cible, None if rev and rev.startswith("0000000") else rev, quand):
                            signaux.append("%s : « non joué » : %s" % (lieu, r))
    for s in signaux:
        dire("signal", "suite : " + s)
    med = statistics.median(delais) if delais else None
    dire("note", "suite des constats « à corriger » (étiquettes depuis le %s, en double comptés une fois) : %d corrigé(s) dans leur lot ; "
         "%d renvoyé(s) à une ligne, dont %d fait(s)%s ; %d écarté(s) ; %d condition(s) « non joué » contrôlée(s) depuis le %s ; %d sans suite signalé(s)%s"
         % (date(int(E("CD") or 0)), compte["corrigé"], compte["renvoyé"], compte["fait"],
            " (délai médian %.0f j)" % med if med is not None else "", compte["écarté"], nj, date(int(E("SD") or 0)), len(signaux),
            " ; %d ligne(s) sans suite de priorité P3, P4 ou V, comptée(s) sans signal (%s)" % (len(basses), ", ".join(sorted(basses))) if basses else ""))
elif MODE == "savoir":                     # section « Savoir » du contexte (06/11/2026) : pointeurs datés, une ligne par sujet
    import time
    ctx = lire(CTX).splitlines()
    L = lots_de(lire(AV)) or {}
    def nu(p):                             # chemin:12 ou chemin:3-9 -> chemin ; ./ de tête et / de fin retirés
        p = re.sub(r":\d+(?:-\d+)?$", "", p.strip())
        return (p[2:] if p.startswith("./") else p).rstrip("/")
    def chemin(x):                         # un chemin, pas un mot de code ; une espace seulement dans un chemin qui existe
        return ("*" not in x and ("/" in x or "." in x) and not re.fullmatch(ID, x)
                and (" " not in x or os.path.exists(nu(x))))
    def web(p):                            # adresse web : schéma, ou premier segment en nom de domaine (pas un dossier à point)
        tete = p.split("/")[0]
        return bool(re.match(r"[a-z][a-z0-9+.-]*://", p)) or ("/" in p and not os.path.exists(tete) and bool(
            re.fullmatch(r"(?:localhost|(?:[a-z0-9-]+\.)+[a-z]{2,})(?::\d+)?", tete, re.I)))
    hors = {AV, AR, CTX} - {""}
    def couvre(a, b):                      # b (pièce d une ligne) est le chemin a, ou un fichier du dossier a
        return b == a or b.startswith(a + "/")
    cites_par = {}                         # chemin -> lots dont le statut le cite : un lieu commun ne fait pas la ligne d une étude
    for n, d in L.items():
        for x in re.findall(r"`([^`]+)`", d["statut"]):
            if chemin(x):
                cites_par.setdefault(nu(x), set()).add(n)
    etudes = {}
    for n, d in L.items():
        if re.match(r"fait \d{2}/\d{2}\b", d["statut"]):
            ch = [nu(x) for x in re.findall(r"`([^`]+)`", d["statut"]) if chemin(x) and nu(x) not in hors]
            propres = [x for x in ch if cites_par.get(x, set()) == {n}]
            etudes[n] = propres or ch
    debut = next((k for k, l in enumerate(ctx) if re.fullmatch(r"#{1,6}\s*Savoir\s*", l.strip())), None)
    if debut is None:
        if etudes:
            dire("signal", "savoir : section « Savoir » absente de %s ; %d étude(s) close(s) sans ligne : %s (règle « Savoir d'un projet » de passation)"
                 % (CTX, len(etudes), ", ".join(etudes)))
        sys.exit(0)
    niveau = len(ctx[debut].strip()) - len(ctx[debut].strip().lstrip("#"))
    fin = next((k for k in range(debut + 1, len(ctx)) if re.match(r"#{1,%d}\s" % niveau, ctx[k])), len(ctx))
    lignes = [(k + 1, ctx[k]) for k in range(debut + 1, fin) if ctx[k].startswith("- ")]
    try:
        sl, sc = int(E("SL") or 0), int(E("SC") or 0)
        if sl < 0 or sc < 0:
            raise ValueError
    except ValueError:
        dire("ko", "SAVOIR_LIGNES ou SAVOIR_CAR de passation.conf non numérique ou négatif : « %s », « %s »" % (E("SL"), E("SC"))); sys.exit(0)
    if sl and len(lignes) > sl:
        dire("signal", "savoir : %s, section « Savoir » : %d lignes, au-delà du plafond de %d (remplacer plutôt qu'empiler)" % (CTX, len(lignes), sl))
    longues = [(n, len(l)) for n, l in lignes if sc and len(l) > sc]
    if longues:
        dire("signal", "savoir : %s, section « Savoir » : %d ligne(s) de plus de %d caractères : %s" % (CTX, len(longues), sc,
             ", ".join("l. %d (%d)" % x for x in longues[:8]) + (" (+%d)" % (len(longues) - 8) if len(longues) > 8 else "")))
    dernier = {}                               # chemin suivi -> date du dernier commit (unix), en un seul passage de git log
    _, journal = git("-c", "core.quotePath=false", "log", "--format=@%ct", "--name-only")
    ct = 0
    for l in journal.splitlines():
        if l.startswith("@"):
            ct = int(l[1:] or 0)
        elif l.strip() and ct > dernier.get(l.strip(), 0):
            dernier[l.strip()] = ct
    def date_commit(p):                        # fichier ou dossier : le plus récent des commits qui le touchent
        return max([c for f, c in dernier.items() if f == p or f.startswith(p + "/")] or [0])
    jour = lambda c: time.strftime("%d/%m/%Y", time.localtime(c))
    cites, comparees, dehors, non_suivies = [], 0, 0, 0
    for n, l in lignes:
        pieces = [nu(x) for x in re.findall(r"`([^`]+)`", l) if chemin(x)]
        cites += pieces
        m = ([None] + list(re.finditer(r"vérifié (\d{2})/(\d{2})/(\d{4})\b", l)))[-1]   # la dernière, en fin de ligne
        if not m:
            dire("signal", "savoir : %s:%d : ligne sans « vérifié JJ/MM/AAAA »" % (CTX, n))
        for p in pieces:
            if p.startswith(("~", "/")) or web(p):
                dehors += 1; continue                  # hors du dépôt : `~/…`, `/…`, adresse web
            if p in hors or ("/" not in p and not os.path.exists(p)):
                continue                       # registre, archive, contexte ; ou un nom sans dossier (`confronter.py`, `template/`)
            if not os.path.exists(p):
                dire("signal", "savoir : %s:%d : `%s` absent du dépôt (pointeur cassé)" % (CTX, n, p)); continue
            c = date_commit(p)
            if not c:
                non_suivies += 1; continue
            comparees += 1
            if m and time.localtime(c)[:3] > (int(m.group(3)), int(m.group(2)), int(m.group(1))):
                dire("signal", "savoir : %s:%d : `%s` modifié le %s, après la vérification du %s/%s/%s : relire la pièce, remplacer la ligne ou sa date"
                     % (CTX, n, p, jour(c), m.group(1), m.group(2), m.group(3)))
    sans = [x for x, ch in etudes.items() if not any(couvre(a, b) for a in ch for b in cites)]
    if sans:
        dire("signal", "savoir : %d étude(s) close(s) sans ligne dans la section « Savoir » de %s : %s (une ligne qui cite un chemin propre à son statut, cahier, étude ou lieu d'arrivée, ou un fichier de son dossier ; un chemin que cite aussi un autre lot ne compte que si l'étude n'en a pas d'autre)"
             % (len(sans), CTX, ", ".join(sans)))
    dire("note", "savoir : section « Savoir » de %s : %d ligne(s), %d pièce(s) comparée(s) à leur dernier commit, %d hors du dépôt (`~/…`, `/…`, adresse web), %d non suivie(s) par git ; %d étude(s) close(s), %d avec leur ligne"
         % (CTX, len(lignes), comparees, dehors, non_suivies, len(etudes), len(etudes) - len(sans)))
elif MODE == "voisines":
    lot, av = CIBLE, lire(AV)
    if not av:
        print("Registre %s absent ou illisible : rien à indexer." % (AV or "(AVANCEMENT vide)")); sys.exit(0)
    taille = len(av.encode("utf-8"))
    L = lots_de(av)
    if taille <= int(E("VO") or 0):
        print("%s : %d octets, tient en une lecture : le lire en entier." % (AV, taille)); sys.exit(0)
    if L is None:
        print("%s : pas de table des lots : le lire en entier." % AV); sys.exit(0)
    if lot not in L:
        print("%s : lot %s absent de la table des lots : le lire en entier." % (AV, lot)); sys.exit(0)
    items = set(ids(L[lot]["items"]))
    prereq = set(ids(L[lot]["prereq"])) - items
    norm = lambda x: x.strip()[2:] if x.strip().startswith("./") else x.strip()
    jetons = lambda t: {norm(x) for x in re.findall(r"`([^`]+)`", t)}
    chemin = lambda x: (" " not in x and "*" not in x and ("/" in x or "." in x) and not re.fullmatch(ID, x))
    def couvre(a, b):                      # a et b désignent le même fichier, ou l un est un dossier qui contient l autre
        return a == b or (a.endswith("/") and b.startswith(a)) or (b.endswith("/") and a.startswith(b))
    autres = [x for n, d in L.items() if n != lot and not CLOS.match(d["statut"]) for x in filter(chemin, jetons(d["fichiers"]))]   # lots ouverts : un lot clos ne garde rien
    hors = {AV, AR, CTX, "CLAUDE.md", ".claude/CLAUDE.md"} - {""}
    tous = sorted(filter(chemin, jetons(L[lot]["fichiers"])))
    siens = [x for x in tous if x not in hors and not any(couvre(x, y) for y in autres)]
    ecartes = [x for x in tous if x not in siens]
    motifs = [(p, re.compile(r"(?<![\w./~-])" + re.escape(p) + ("" if p.endswith("/") else r"(?![\w/-])"))) for p in siens]
    trouve = []
    for lieu, texte in (("registre", av), ("archive", lire(AR))):
        for x, d in lignes_de(texte).items():
            if x in items:
                continue
            deps = set(ids(d["dep"]))
            cites = set(ids(d["brut"].replace(d["dep"], "", 1) if d["dep"] else d["brut"])) - {x}
            r = ["dépend de %s" % i for i in sorted(deps & (items | prereq))]
            r += ["cite %s (item)" % i for i in sorted((cites - deps) & items)]
            r += ["cite `%s` (fichier du lot)" % p for p, rx in motifs if rx.search(d["brut"])]
            r += ["cite %s (prérequis)" % i for i in sorted((cites - deps) & prereq)]
            if r:
                trouve.append((lieu, x, d["ligne"], r))
    print("Voisines du lot %s dans %s%s : %d ligne(s) hors du lot. Clés : %d item(s), %d fichier(s) du lot seul, %d prérequis%s."
          % (lot, AV, " et " + AR if AR else "", len(trouve), len(items), len(siens), len(prereq),
             " ; non comptés (aussi à un autre lot ouvert, registre, contexte, CLAUDE.md) : " + ", ".join(ecartes) if ecartes else ""))
    print("Index seulement : ouvrir une ligne au besoin (grep -m1 '^| <ID> ' sur le fichier).")
    for lieu, x, ligne, r in trouve:
        debut = " ".join(ligne.split())
        print("- %s (%s) : %s — %s" % (x, lieu, debut[:90] + ("…" if len(debut) > 90 else ""),
              ", ".join(r[:3]) + (" (+%d)" % (len(r) - 3) if len(r) > 3 else "")))
PY
}
rendre(){                       # lignes « ok|ko|note|signal<TAB>texte » de registre(), lues dans le shell courant
  local etat texte
  while IFS=$'\t' read -r etat texte; do
    case "$etat" in ok) ok "$texte";; ko) echec "$texte";; note) note "$texte";; signal) echo "! $texte";; "") ;; *) echec "registre : sortie inattendue « $etat $texte »";; esac
  done <<< "$1"
}
if [ -n "$VOISINES" ]; then
  [ -n "$AVANCEMENT" ] || { echo "--voisines : aucun registre (AVANCEMENT de passation.conf vide) : rien à indexer."; exit 0; }
  [ $STRICT -eq 1 ] || [ -n "$SUIVANT" ] && echo "· --strict et --suivant ignorés avec --voisines (index seul, sans contrôle)"
  registre voisines "$VOISINES"; exit $?
fi
if [ $CIBLES -eq 1 ]; then      # --cibles (06/11/2026) : juge les cibles d'un autre outil, lues sur l'entrée standard
  [ -n "$AVANCEMENT" ] || { echo "--cibles : aucun registre (AVANCEMENT de passation.conf vide)"; exit 2; }
  X="$(cat)"; S=$(registre cibles "$X") || { echo "--cibles : contrôle en erreur (python3)"; exit 2; }; rendre "$S"; exit $ko
fi

# ---------- fichier de reprise retiré (décision du 12/10/2026) : la reprise tient par le CLAUDE.md du dépôt, la ligne de
# lancement et le cahier du lot. Un dépôt ancien est toléré, jamais en silence : signalé, sans échec, jusqu'à sa mise à niveau
VIEILLES=$(grep -oE '^[[:space:]]*(PROMPT|REGLES|DEPOT)=' passation.conf 2>/dev/null | tr -d ' \t=' | tr '\n' ' ')
case " $VIEILLES " in *" REGLES "*) QUOI="les phrases de REGLES vont dans le CLAUDE.md du dépôt, puis retirer ces clés";; *) QUOI="les retirer";; esac
[ -n "$VIEILLES" ] && echo "! passation.conf porte ${VIEILLES}: clés du fichier de reprise retiré, que ce script ne lit plus : $QUOI"
CLAUDE_MD=""; for c in CLAUDE.md .claude/CLAUDE.md; do [ -f "$c" ] && { CLAUDE_MD="$c"; break; }; done   # Claude Code lit l'un et l'autre
[ -n "$CLAUDE_MD" ] || echo "! CLAUDE.md absent, ni à la racine ni dans .claude/ : avec la ligne de lancement et le cahier du lot, il porte seul la reprise ; l'écrire (ce qu'est le projet, où sont contexte, registre et cahiers, skills, marche de reprise, règles propres au projet)"
{ case " $VIEILLES " in *" PROMPT "*) printf '%s\n' "${PROMPT:-}";; esac; printf '%s\n' PROMPT-REPRISE.md dev/PROMPT-REPRISE.md; } | awk 'NF && !vu[$0]++' |
while IFS= read -r F; do
  [ -f "$F" ] || continue
  if [ -n "$CLAUDE_MD" ]; then echo "! $F : fichier de reprise figé, plus réécrit ni lu à la reprise : à supprimer sur l'accord de l'utilisateur, avec sa ligne de .gitignore"
  else echo "! $F : fichier de reprise figé, plus réécrit : gardé jusqu'à ce que le CLAUDE.md du dépôt soit écrit"; fi
done

# ---------- dépôt ----------
if [ -n "$($GIT status --short 2>/dev/null)" ]; then
  echec "fichiers non commités :"; $GIT status --short 2>/dev/null | sed 's/^/    /'
else ok "dépôt propre"; fi
Z=$(find . -path ./.git -prune -o -type d -name _to_delete -print 2>/dev/null | while read -r z; do [ -n "$(ls -A "$z" 2>/dev/null)" ] && echo "$z"; done)
[ -n "$Z" ] && echec "à jeter, oublié : $Z (à vider par l'utilisateur)" || ok "aucun _to_delete/ en attente"
# contrôle de reprise du projet (REPRISE, 04/11/2026) : il dit un geste à faire avant le lot, jamais un défaut de livraison
if [ -n "$REPRISE" ]; then
  SR=$(bash -c "$REPRISE" 2>&1); CR=$?
  [ -n "$SR" ] && printf '%s\n' "$SR" | sed 's/^/    /'
  case "$CR" in 0) QUOI="à jour";; 1) QUOI="geste dû, à faire avant le lot (sortie ci-dessus)";; *) QUOI="contrôle impossible (code $CR) : à réparer";; esac
  if [ "$CR" -eq 0 ]; then ok "reprise ($REPRISE) : $QUOI"
  elif [ $STRICT -eq 1 ]; then echo "! reprise ($REPRISE) : $QUOI ; sans effet sur la livraison"
  else echec "reprise ($REPRISE) : $QUOI"; fi
fi

# longueur de l entrée de la dernière étiquette et des synthèses de série (08/10/2026) : les entrées passées ne
# sont jamais réécrites, les synthèses sont tenues à jour en place
longueurs(){
  J="$1" T="$2" JM="$JOURNAL_MAX" SM="$SYNTHESE_MAX" python3 - <<'PY' || ko=1
import os, re, sys
j, t = os.environ["J"], os.environ["T"]
try:
    jm, sm = int(os.environ["JM"] or 0), int(os.environ["SM"] or 0)
    if jm < 0 or sm < 0:
        raise ValueError
except ValueError:
    print("✗ JOURNAL_MAX ou SYNTHESE_MAX de passation.conf non numérique ou négatif : " + os.environ["JM"] + ", " + os.environ["SM"])
    sys.exit(1)
txt = open(j, encoding="utf-8").read()
ko = 0
if jm:
    m = re.search(r"^#{2,3} \[?" + re.escape(t) + r"(?![\w.])[^\n]*\n(.*?)(?=^#{1,2} |\Z)", txt, re.M | re.S)
    n = len(" ".join(m.group(1).split())) if m else None
    if n is None:
        print(f"· {j} : entrée de {t} introuvable (titre « ## {t} … ») : longueur non contrôlée")
    elif n > jm:
        print(f"✗ {j} : entrée de {t} trop longue ({n} caractères, au plus {jm} : deux phrases, le détail va au contexte ou au cahier du lot ; JOURNAL_MAX)"); ko = 1
    else:
        print(f"✓ {j} : entrée de {t} en {n} caractères (au plus {jm})")
if sm:
    longues = [(m.group(1), len(" ".join(m.group(2).split()))) for m in re.finditer(r"^# (\S+)\.x\s*[—–-]\s*(.+)$", txt, re.M)]
    trop = [f"{s}.x ({n})" for s, n in longues if n > sm]
    if trop:
        print(f"✗ {j} : synthèse de série trop longue, au plus {sm} caractères (une ou deux phrases ; SYNTHESE_MAX) : " + ", ".join(trop)); ko = 1
    elif longues:
        print(f"✓ {j} : {len(longues)} synthèse(s) de série, au plus {sm} caractères")
sys.exit(ko)
PY
}
ETIQ=""
for L in $LIVRABLES; do
  IFS=: read -r pref journal version <<<"$L"
  T=$(derniere "$pref"); ETIQ="$ETIQ $T"
  [ -z "$T" ] && { echec "aucune étiquette $pref*"; continue; }
  [ -n "$journal" ] && { grep -q "$T" "$journal" 2>/dev/null && ok "$journal mentionne $T" || echec "$journal ne mentionne pas $T"; }
  [ -n "$journal" ] && [ -f "$journal" ] && longueurs "$journal" "$T"
  [ -n "$version" ] && { grep -q "$T" "$version" 2>/dev/null && ok "$version porte $T" || echec "$version ne porte pas $T"; }
  M="$T"; [ -n "$CONTEXTE_MOTIF" ] && M="$(printf "$CONTEXTE_MOTIF" "$T")"
  grep -qF -- "$M" "$CONTEXTE" 2>/dev/null && ok "$CONTEXTE à jour de $T (« $M »)" || echec "$CONTEXTE n'annonce pas « $M » — le mettre à jour en place puis le recopier dans le projet Claude"
done
# documents web (DOCS) : étiquettes vX.Y de document-versionne, contrôlés même sans LIVRABLES
if [ -n "$DOCS" ]; then
  T=$($GIT tag -l 'v[0-9]*' --sort=-v:refname 2>/dev/null | grep -E '^v[0-9]+\.[0-9]+(\.[0-9]+)?$' | head -1)
  if [ -z "$T" ]; then echec "aucune étiquette vX.Y pour les documents : $DOCS"
  else
    case " $ETIQ " in *" $T "*) ;; *) ETIQ="$ETIQ $T"
      M="$T"; [ -n "$CONTEXTE_MOTIF" ] && M="$(printf "$CONTEXTE_MOTIF" "$T")"
      grep -qF -- "$M" "$CONTEXTE" 2>/dev/null && ok "$CONTEXTE à jour de $T (« $M »)" || echec "$CONTEXTE n'annonce pas « $M » — le mettre à jour en place puis le recopier dans le projet Claude";;
    esac
    for D in $DOCS; do
      if $GIT diff --quiet "$T" HEAD -- "$D" 2>/dev/null && $GIT diff --quiet HEAD -- "$D" 2>/dev/null; then ok "$D identique à l'étiquette $T"
      else echec "$D a changé depuis $T : étiqueter la livraison"; fi
      [ -f "$(dirname "$D")/journal.html" ] || echec "$(dirname "$D")/journal.html absent"
      J="$(dirname "$D")/journal-data.js"
      if [ ! -f "$J" ]; then echec "$J absent : journal-build.sh $D"
      elif ! grep -q "\"tag\": *\"$T\"" "$J"; then echec "$J n'embarque pas $T : régénérer après l'étiquette"
      elif [ "$(stat -c %Y "$J" 2>/dev/null || stat -f %m "$J")" -lt "$($GIT log -1 --format=%ct "$T")" ]; then echec "$J antérieur à $T : régénérer"
      else ok "$J régénéré après $T"; fi
    done
  fi
fi
if [ -n "$AVANCEMENT" ]; then
  if [ ! -f "$AVANCEMENT" ]; then echec "$AVANCEMENT absent (registre d'avancement)"
  else
    for T in $ETIQ; do
      M="$T"; [ -n "$CONTEXTE_MOTIF" ] && M="$(printf "$CONTEXTE_MOTIF" "$T")"
      grep -qF -- "$M" "$AVANCEMENT" && ok "$AVANCEMENT à jour de $T" || echec "$AVANCEMENT n'annonce pas « $M » : statuts et lignes à mettre à jour"
    done
    # identifiants uniques sur le registre et son archive (ARCHIVE_AVANCEMENT, 06/10/2026)
    A=""; if [ -n "$ARCHIVE_AVANCEMENT" ]; then [ -f "$ARCHIVE_AVANCEMENT" ] && A="$ARCHIVE_AVANCEMENT" || echec "$ARCHIVE_AVANCEMENT absent (archive du registre, ARCHIVE_AVANCEMENT)"; fi
    ID='^\| [A-Z]{2,4}-[A-Z0-9]+ \|'
    D=$(grep -hoE "$ID" "$AVANCEMENT" ${A:+"$A"} | sort | uniq -d | tr -d '| ' | tr '\n' ' ')
    N="$(grep -cE "$ID" "$AVANCEMENT") lignes"; [ -n "$A" ] && N="$N, $A : $(grep -cE "$ID" "$A") lignes"
    [ -n "$D" ] && echec "$AVANCEMENT${A:+ et $A} : identifiants en double : $D" || ok "$AVANCEMENT : $N, identifiants uniques"
    L=$(grep -nE '^#+ *(Reporté|Prochaines étapes|À faire|A faire|Feuille de route|TODO)' "$CONTEXTE" 2>/dev/null | head -3 | tr '\n' ' ')
    [ -n "$L" ] && echec "$CONTEXTE tient encore une liste à faire ($L) : la reporter dans $AVANCEMENT" || ok "$CONTEXTE sans liste à faire (source unique : $AVANCEMENT)"
    # aucune liste à faire concurrente (02/10/2026) : ni case à cocher ni consigne de relecture d'un fichier hors du registre
    # (script python entre apostrophes : n'y écrire aucune apostrophe)
    L=$($GIT ls-files -z 2>/dev/null | AVANCEMENT="$AVANCEMENT" ARCHIVE="$ARCHIVE_AVANCEMENT" LISTES_PERMISES="$LISTES_PERMISES" python3 -c '
import os, re, sys
garde = {os.environ["AVANCEMENT"], os.environ["ARCHIVE"], *os.environ["LISTES_PERMISES"].split()}
case = re.compile(r"^\s*[-*] \[[ xX]\]")
relit = re.compile("relit" + " ce fichier")          # écrit en deux morceaux : ce script est lui-même versionné
cite = re.compile("«[^»]*relit" + " ce fichier[^«]*»")  # une citation entre guillemets n est pas une consigne
vus = []
for f in sys.stdin.buffer.read().decode("utf-8", "replace").split("\0"):
    if not f or f in garde or not os.path.isfile(f):
        continue
    b = open(f, "rb").read()
    if b"\0" in b[:8192]:
        continue
    try:
        t = b.decode("utf-8")
    except UnicodeDecodeError:
        continue
    for n, l in enumerate(t.split("\n"), 1):
        if case.match(l) or (relit.search(l) and not cite.search(l)):
            vus.append(f"{f}:{n}")
print(" ".join(vus[:5]) + (f" (+{len(vus) - 5})" if len(vus) > 5 else ""), end=" " if vus else "")
'); rc=$?
    if [ $rc -ne 0 ]; then echec "contrôle des listes à faire hors de $AVANCEMENT en erreur (python3, code $rc)"
    elif [ -n "$L" ]; then echec "liste à faire hors de $AVANCEMENT (case à cocher ou consigne de relecture) : $L— la reporter dans le registre, ou LISTES_PERMISES"
    else ok "aucune liste à faire hors de $AVANCEMENT"; fi
    # statut de chaque lot (règle « Statut d'un lot » de passation, 10/10/2026) : premier mot lu par la vue
    # (script python entre apostrophes : n y écrire aucune apostrophe)
    L=$(AVANCEMENT="$AVANCEMENT" python3 -c '
import os, re
ok = re.compile(r"(proposé|à cadrer|préparé|en cours \(\d{2}/\d{2} \d{2}:\d{2}\)|reste\b|fait (v\d+\.\d+(?:\.\d+)?|\d{2}/\d{2})|abandonné)")
fautifs, entete = [], None
for l in open(os.environ["AVANCEMENT"], encoding="utf-8").read().splitlines():
    if not l.startswith("|"):
        entete = None; continue
    c = [x.strip() for x in re.split(r"(?<!\\)\|", l.strip().strip("|"))]
    if entete is None:
        entete = c if c and c[0] == "Lot" else []; continue
    if not entete or re.fullmatch(r"[-: |]+", l.strip()): continue
    i = next((k for k, n in enumerate(entete) if n.lower().startswith("statut")), len(entete) - 1)
    st = c[i] if i < len(c) else ""
    if not ok.match(st): fautifs.append("%s (« %s »)" % (c[0], st[:30]))
print(" ".join(fautifs), end=" " if fautifs else "")
'); rc=$?
    if [ $rc -ne 0 ]; then echec "contrôle des statuts de lots de $AVANCEMENT en erreur (python3, code $rc)"
    elif [ -n "$L" ]; then echec "statut de lot hors des mots de passation (proposé, à cadrer, préparé, en cours (JJ/MM HH:MM), reste, fait vX.Y, vX.Y.Z ou JJ/MM, abandonné) : $L"
    else ok "$AVANCEMENT : statuts des lots conformes"; fi
    if [ -n "$LIGNE_MAX" ]; then S=$(registre longueurs) || echec "contrôle de LIGNE_MAX en erreur (python3)"; rendre "$S"; fi
    # carte des fichiers (02/10/2026) : chaque fichier versionné y a un rôle (chemin, dossier finissant par /, ou motif *)
    # (script python entre apostrophes : n y écrire aucune apostrophe)
    if grep -qE '^## Carte des fichiers' "$AVANCEMENT"; then
      L=$($GIT ls-files -z 2>/dev/null | AVANCEMENT="$AVANCEMENT" python3 -c '
import fnmatch, os, re, sys
t = open(os.environ["AVANCEMENT"], encoding="utf-8").read()
m = re.search(r"^## Carte des fichiers[ \t]*$(.*?)(?=^## |\Z)", t, re.M | re.S)
entrees = []
for l in m.group(1).splitlines():
    if l.startswith("|") and not re.match(r"^\|[-: |]+\|?$", l):
        entrees += re.findall(r"`([^`]+)`", l.split("|")[1])
def couvert(f):
    return any(f.startswith(e) if e.endswith("/") else (f == e or fnmatch.fnmatchcase(f, e)) for e in entrees)
hors = [f for f in sys.stdin.buffer.read().decode("utf-8", "replace").split("\0") if f and not couvert(f)]
print(" ".join(hors[:5]) + (" (+%d)" % (len(hors) - 5) if len(hors) > 5 else ""), end=" " if hors else "")
'); rc=$?
      if [ $rc -ne 0 ]; then echec "contrôle de la carte des fichiers de $AVANCEMENT en erreur (python3, code $rc)"
      elif [ -n "$L" ]; then echec "fichiers versionnés absents de la carte des fichiers de $AVANCEMENT : $L— leur donner un rôle"
      else ok "carte des fichiers de $AVANCEMENT : tous les fichiers versionnés ont un rôle"; fi
    else note "$AVANCEMENT sans section « Carte des fichiers » : couverture non contrôlée"; fi
  fi
fi
# lot suivant (--suivant, à la clôture ; il remplace le fichier de reprise, décision du 12/10/2026) : chaque lot nommé est
# une ligne de la table des lots, ni fait ni abandonné, avec son cahier présent et suivi par git ; sa ligne de lancement est
# rendue. Cahier : parmi les chemins LOTS/….md cités dans le statut, celui dont le nom commence par <lot>-, sinon le premier
# (un statut peut citer le cahier d'un autre lot) ; sans chemin, le fichier LOTS/<lot>-….md
if [ -n "$SUIVANT" ]; then
  if [ -z "$AVANCEMENT" ] || [ ! -f "$AVANCEMENT" ]; then echec "--suivant : aucun registre où lire la table des lots (AVANCEMENT de passation.conf)"
  elif ! S=$(AVANCEMENT="$AVANCEMENT" LOTS="${LOTS%/}" SUIVANT="$SUIVANT" python3 - <<'PY'
import glob, os, re
lots, entete = {}, None
for l in open(os.environ["AVANCEMENT"], encoding="utf-8").read().splitlines():
    if not l.startswith("|"):
        entete = None; continue
    c = [x.strip() for x in re.split(r"(?<!\\)\|", l.strip().strip("|"))]
    if entete is None:
        entete = [x.lower() for x in c] if c and c[0] == "Lot" else []; continue
    if not entete or re.fullmatch(r"[-: |]+", l.strip()): continue
    col = lambda n: next((k for k, x in enumerate(entete) if x.startswith(n)), None)
    i, t = col("statut"), col("type")
    i = len(entete) - 1 if i is None else i
    lots.setdefault(c[0], (c[i] if i < len(c) else "", c[t] if t is not None and t < len(c) else ""))
rep = os.environ["LOTS"]
for lot in dict.fromkeys(os.environ["SUIVANT"].split()):
    if lot not in lots:
        print("ko\tlot suivant %s absent de la table des lots de %s : lui donner sa ligne" % (lot, os.environ["AVANCEMENT"])); continue
    st, ty = lots[lot]
    if re.match(r"(fait|abandonné)\b", st):
        print("ko\tlot suivant %s déjà clos (« %s ») : nommer un lot ouvert" % (lot, st[:40])); continue
    cites = re.findall(r"(?:^|[\s`(])(" + re.escape(rep) + r"/[^`\s)]+\.md)", st)
    siens = [x for x in cites if os.path.basename(x).startswith(lot + "-") or os.path.basename(x) == lot + ".md"]
    cands = (siens or cites)[:1] or sorted(glob.glob(os.path.join(rep, glob.escape(lot) + "-*.md")) + glob.glob(os.path.join(rep, glob.escape(lot) + ".md")))
    if not cands or not os.path.isfile(cands[0]):
        print("ko\tlot suivant %s sans cahier (%s) : l’écrire dans %s/ et le nommer dans son statut" % (lot, cands[0] + " absent" if cands else "aucun", rep)); continue
    print("ok\t%s\t%s\t%s\t%s" % (lot, ty or "-", st.split(" :")[0][:40] or "-", cands[0]))   # « - » : jamais de champ vide
PY
); then echec "--suivant : contrôle en erreur (python3)"
  else
    while IFS=$'\t' read -r E A B C D; do
      [ -n "$E" ] || continue
      if [ "$E" != ok ]; then echec "$A"; continue; fi
      [ "$B" = - ] && B=""; [ "$C" = - ] && C="statut vide"
      if ! $GIT ls-files --error-unmatch -- "$D" >/dev/null 2>&1; then echec "lot suivant $A : cahier $D non suivi par git : le commiter"; continue; fi
      ok "lot suivant $A${B:+ ($B)}, $C : cahier $D"
      case "$C" in proposé*) note "lot $A proposé : il attend l'accord de l'utilisateur avant d'être lancé";; esac
      # shellcheck disable=SC2016   # accents graves voulus : ils entourent le chemin du cahier dans la ligne de lancement
      printf '    ligne de lancement : %s — lot %s. Reprise selon passation, puis uniquement `%s`.\n' "$PROJET" "$A" "$D"
    done <<< "$S"
  fi
else note "lot suivant non contrôlé : à la clôture, passation.sh --strict --suivant <lot>"; fi
if [ -n "$FEUILLE" ]; then
  F=$(derniere "$FEUILLE_TAG"); ETIQ="$ETIQ $F"
  grep -q "Statut : ${F#$FEUILLE_TAG}" "$FEUILLE" 2>/dev/null && ok "feuille de route en ${F#$FEUILLE_TAG}" || echec "l'en-tête de « $FEUILLE » n'est pas en ${F#$FEUILLE_TAG}"
fi
if [ -n "$INDEX_PIECES" ] && [ -f "$INDEX_PIECES" ]; then
  while IFS=$'\t' read -r num d t dossier m sha f; do
    [ -z "${num:-}" ] && continue; [ -f "$dossier/$f" ] || echec "pièce $num : fichier absent ($dossier/$f)"
  done < "$INDEX_PIECES"; ok "pièces de $INDEX_PIECES présentes"
fi
# chaque étiquette livrée dit dans son commit comment le lot a été relu (barème de passation, règle du 01/10/2026)
# et ce qu'il a coûté (règle « Mesure des tokens » de passation, 08/10/2026)
RELECTURE_DEPUIS=1790820000     # 01/10/2026 02:00 UTC : les étiquettes plus anciennes en sont dispensées
MESURE_DEPUIS=1791496800        # 09/10/2026 00:00 heure de Paris : contexte final, appels et pondéré exigés à partir de là
CHEF_APPELS_DEPUIS=1791642600   # 10/10/2026 16:30 heure de Paris : le segment « chef de
                                #   projet » porte aussi son nombre d'appels, facteur de tout gain de lecture
mesure_manquante(){             # champs de mesure absents d'une ligne Relecture: (vide si complète)
  # segment par segment (08/10/2026) : la ligne se coupe aux « ; » hors parenthèses ; chaque sous-agent (relecteur,
  # contre-vérification, segment dont la tête nomme Sonnet, Opus ou Haiku) porte son contexte final, ses appels et son
  # pondéré dans son propre segment, hors parenthèses ; le segment « chef de projet » porte son pondéré, et ses appels à
  # partir de CHEF_APPELS_DEPUIS
  python3 - "$1" "${2:-0}" <<'PY'
import re, sys
r, chef_appels = sys.argv[1], sys.argv[2] == "1"
segs, cur, prof = [], "", 0
for ch in r:
    prof = max(0, prof + (ch == "(") - (ch == ")"))
    if ch == ";" and prof <= 0:
        segs.append(cur.strip()); cur = ""
    else:
        cur += ch
segs.append(cur.strip())
segs = [x for x in segs if x]
manque, chef = (["parenthèse fermante"] if prof > 0 else []), False
for k, x in enumerate(segs):
    if k == 0:
        if x.startswith("Relecture: auteur"):
            continue
        nom = "du relecteur"
    elif x.lower().startswith("chef de projet"):
        chef = True
        y = x                              # hors parenthèses, imbriquées comprises
        while re.search(r"\([^()]*\)", y):
            y = re.sub(r"\([^()]*\)", "", y)
        if "pondéré" not in y:
            manque.append("pondéré du chef de projet")
        if chef_appels and not re.search(r"\d+ appels?\b", y):
            manque.append("appels du chef de projet")
        continue
    elif x.startswith("contre-vérification"):
        nom = "de la contre-vérification"
    elif re.match(r"^[^,—]*\b(Sonnet|Opus|Haiku)\b", x):
        nom = "de « " + re.split(r"\s*[—,(]", x)[0].strip() + " »"
    else:
        continue
    y = x                                  # mesure hors parenthèses : le texte libre des constats ne compte pas
    while re.search(r"\([^()]*\)", y):
        y = re.sub(r"\([^()]*\)", "", y)
    champs = [c for c, ok in (("contexte final", "contexte final" in y), ("appels", re.search(r"\d+ appels?\b", y)),
                              ("pondéré", "pondéré" in y)) if not ok]
    if champs:
        manque.append(", ".join(champs) + " " + nom)
if not chef:
    manque.append("pondéré du chef de projet")
print(" ; ".join(manque), end="")
PY
}
# motif de chaque constat (10/10/2026) : après la ligne Relecture:, un bloc « Constats: » d'une ligne par constat
# bloquant ou « à corriger » de la relecture, des contre-vérifications et de tout autre segment qui porte « constats :
# a / b / c », un second relecteur par exemple (05/11/2026) (« - <gravité> : <motif> — <fichier ou écran> —
# <corrigé | ID du registre | corrigé, ID | écarté : raison> »), ou « Constats: aucun » ; avec CONTROLES, une ligne « Contrôles: » qui
# donne le résultat de chaque contrôle avant relecture (« <nom> <résultat> » séparés par « ; »)
CONSTATS_DEPUIS=1791590400      # 10/10/2026 02:00 heure de Paris : bloc Constats: exigé à partir de là
constats_manquants(){           # écarts du bloc Constats: et de la ligne Contrôles: d'un corps de commit (vide si conforme)
  CONTROLES="$CONTROLES" python3 - "$1" <<'PY'
import os, re, sys
lignes = sys.argv[1].splitlines()
rel = next((l for l in lignes if re.match(r"^Relecture: (auteur|ciblée Sonnet|complète Opus)", l)), "")
segs, cur, prof = [], "", 0
for ch in rel:
    prof = max(0, prof + (ch == "(") - (ch == ")"))
    if ch == ";" and prof <= 0:
        segs.append(cur.strip()); cur = ""
    else:
        cur += ch
segs = [x for x in segs + [cur.strip()] if x]
def hors(x):                               # texte hors parenthèses
    while re.search(r"\([^()]*\)", x):
        x = re.sub(r"\([^()]*\)", "", x)
    return x
GRAV = ("bloquant", "à corriger")
attendu, compte, manque = dict.fromkeys(GRAV, 0), False, []
TROIS = r"(?<![\d/])(\d+) / (\d+) / (\d+)(?![\d/])"
for k, x in enumerate(segs):               # comptes « bloquants / à corriger / mineurs » de chaque relecture
    if k == 0:
        if x.startswith("Relecture: auteur"):
            continue
        nom = "du relecteur"
    elif x.startswith("contre-vérification"):
        nom = "de la contre-vérification"
    elif re.search(r"\bconstats :", hors(x)):   # tout autre relecteur qui donne ses comptes (05/11/2026) ; comptes mal formés : « comptes manquants »
        nom = "de « " + re.split(r"\s*[—,(]", x)[0].strip() + " »"
    else:
        continue
    m = re.search(TROIS, hors(x))
    if not m:
        manque.append("comptes « bloquants / à corriger / mineurs » " + nom)
        continue
    compte = True
    attendu["bloquant"] += int(m[1]); attendu["à corriger"] += int(m[2])
r = next((j for j, l in enumerate(lignes) if l == rel), -1)
i = next((j for j, l in enumerate(lignes) if j > r and re.match(r"^Constats:", l)), None)
if i is None:
    manque.append("bloc « Constats: » après la ligne Relecture: (« Constats: aucun » s’il n’y en a pas)")
else:
    reste, items = lignes[i][len("Constats:"):].strip(), []
    for l in lignes[i + 1:]:
        if not l.startswith("- "):
            break
        items.append(l[2:].strip())
    if reste and reste != "aucun":
        manque.append("« Constats: » suivi d’autre chose que « aucun » sur sa ligne")
    elif reste and items:
        manque.append("« Constats: aucun » suivi de lignes de constat")
    elif not reste and not items:
        manque.append("bloc « Constats: » vide (« Constats: aucun » s’il n’y en a pas)")
    vus = dict.fromkeys(GRAV, 0)
    for it in items:
        m = re.match(r"^(bloquant|à corriger|mineur) : (.+)$", it)
        parts = m[2].rsplit(" — ", 2) if m else []
        if len(parts) < 3 or not all(p.strip() for p in parts):
            manque.append("constat illisible « %s » (- gravité : motif — fichier ou écran — devenir)" % it[:60])
            continue
        if not re.fullmatch(r"(corrigé|[A-Z][A-Z0-9]{1,5}-\d+)(, [A-Z][A-Z0-9]{1,5}-\d+)*|écarté : \S.*", parts[2].strip()):
            manque.append("devenir « %s » (corrigé, ID du registre, corrigé, ID, ou écarté : raison)" % parts[2].strip()[:40])
        if m[1] in vus:
            vus[m[1]] += 1
    if compte:
        for g in GRAV:
            if vus[g] != attendu[g]:
                manque.append("%d constat(s) « %s » listé(s) pour %d dans la ligne Relecture" % (vus[g], g, attendu[g]))
ctrl = os.environ.get("CONTROLES", "").split()
if ctrl:
    l = next((l for l in lignes if l.startswith("Contrôles:")), None)
    if l is None:
        manque.append("ligne « Contrôles: » (" + ", ".join(ctrl) + ")")
    else:
        res = [s.strip().split(None, 1) for s in l[len("Contrôles:"):].split(";")]
        for n in ctrl:
            if not any(len(x) == 2 and x[0].rstrip(":") == n for x in res):
                manque.append("résultat du contrôle « %s » dans « Contrôles: »" % n)
print(" ; ".join(manque), end="")
PY
}
for T in $ETIQ; do
  B=$($GIT log -1 --format=%B "$T" 2>/dev/null)
  R=$(printf '%s\n' "$B" | grep -m1 -E '^Relecture: (auteur|ciblée Sonnet|complète Opus)')
  D=$($GIT log -1 --format=%ct "$T" 2>/dev/null || echo 0)
  if [ -z "$R" ]; then
    if [ "$D" -lt "$RELECTURE_DEPUIS" ]; then note "$T antérieure à la ligne Relecture (01/10/2026)"
    else echec "$T : pas de ligne « Relecture: auteur | ciblée Sonnet | complète Opus — mesure » dans son commit (barème de passation)"; fi
  elif [ "$D" -lt "$MESURE_DEPUIS" ]; then ok "$T : $R"
  elif ! M=$(mesure_manquante "$R" "$([ "$D" -ge "$CHEF_APPELS_DEPUIS" ] && echo 1)"); then echec "$T : contrôle de la mesure en erreur (python3)"
  else
    if [ -z "$M" ]; then ok "$T : $R"
    else echec "$T : ligne Relecture sans $M (règle « Mesure des tokens » de passation)"; fi
  fi
  if [ -n "$R" ] && [ "$D" -ge "$CONSTATS_DEPUIS" ]; then
    if ! C=$(constats_manquants "$B"); then echec "$T : contrôle des constats en erreur (python3)"
    elif [ -z "$C" ]; then ok "$T : bloc Constats conforme${CONTROLES:+, contrôles listés}"
    else echec "$T : $C (règle « Constats » de passation)"; fi
  fi
done
# passe ligne à ligne (règle « Registre d'avancement » de passation, 12/10/2026 ; contrôle du 04/11/2026) : le commit étiqueté
# porte un bloc « Registre: », une ligne par item de chaque lot passé à « fait <étiquette> » et par lot, dont le verdict
# s'accorde au statut ; l'archive ne porte que des lignes closes. Lot d'étude : le commit qui écrit « fait JJ/MM »
if [ -n "$AVANCEMENT" ] && [ -f "$AVANCEMENT" ]; then
  for T in $ETIQ; do
    [ "$($GIT log -1 --format=%ct "$T" 2>/dev/null || echo 0)" -ge "$REGISTRE_DEPUIS" ] || continue
    S=$(registre etiquette "$T") || echec "$T : contrôle du bloc Registre en erreur (python3)"; rendre "$S"
  done
  S=$(registre etudes) || echec "contrôle des lots d'étude en erreur (python3)"; rendre "$S"
  # suite des constats (06/11/2026) : la cible de chaque constat (ligne du registre, chemin) a-t-elle changé depuis ?
  # signalé « ! », sans faire échouer --strict ; indicateur en note
  SUITE_PREFS=""; for L in $LIVRABLES; do SUITE_PREFS="$SUITE_PREFS ${L%%:*}"; done; [ -n "$DOCS" ] && SUITE_PREFS="$SUITE_PREFS v"
  S=$(registre suite) || echec "contrôle de la suite des constats en erreur (python3)"; rendre "$S"
fi
# section « Savoir » du contexte (06/11/2026) : étude close sans ligne, pièce plus récente que sa ligne, forme ; « ! » sans échec
if [ -n "$CONTEXTE" ] && [ -f "$CONTEXTE" ]; then
  S=$(registre savoir) || echec "contrôle de la section « Savoir » en erreur (python3)"; rendre "$S"
fi
printf '  étiquettes :%s\n' "$ETIQ"
# revue des motifs (règle de passation, 10/10/2026) : due toutes les REVUE_MOTIFS étiquettes livrées
# depuis la dernière revue (étiquette REVUE_TAG<étiquette du lot>, posée sur le commit étiqueté du lot qui l'a faite), ou
# depuis le premier bloc Constats (CONSTATS_DEPUIS) ; signalée, sans faire échouer --strict
if [ "$REVUE_MOTIFS" -gt 0 ] 2>/dev/null; then
  PREFS=""; for L in $LIVRABLES; do PREFS="$PREFS ${L%%:*}"; done; [ -n "$DOCS" ] && PREFS="$PREFS v"
  RV=$($GIT for-each-ref --sort=-creatordate --count=1 --format='%(refname:short)' "refs/tags/$REVUE_TAG*" 2>/dev/null)
  N=$($GIT for-each-ref ${RV:+--no-merged "$RV"} --format='%(refname:short) %(committerdate:unix) %(*committerdate:unix)' refs/tags 2>/dev/null |
      PREFS="$PREFS" DEPUIS="$CONSTATS_DEPUIS" python3 -c '
import os, re, sys
p = [re.escape(x) for x in os.environ["PREFS"].split()]
rx = re.compile("^(" + "|".join(p) + r")[0-9]+\.[0-9]+(\.[0-9]+)?$") if p else None
n, majeures = 0, []
for l in sys.stdin:
    c = l.split()
    if rx and len(c) >= 2 and rx.match(c[0]) and int(c[-1]) >= int(os.environ["DEPUIS"]):
        n += 1
        if c[0].endswith(".0"):
            majeures.append(c[0])
print(n, " ".join(majeures))')
  MAJ_SANS=${N#* }; N=${N%% *}
  [ -n "$RV" ] && DEP="la revue $RV" || DEP="le premier bloc Constats (10/10/2026)"
  if [ "${N:-0}" -ge "$REVUE_MOTIFS" ] || [ -n "$MAJ_SANS" ]; then
    [ -n "$MAJ_SANS" ] && POURQUOI="version majeure livrée sans revue ($MAJ_SANS)" || POURQUOI="$N étiquettes depuis $DEP"
    printf '! revue des motifs due : %s : la faire dans ce lot (règle « Revue des motifs » de passation), puis étiqueter %s<étiquette du lot>\n' "$POURQUOI" "$REVUE_TAG"
  else note "revue des motifs : ${N:-0} étiquette(s) sur $REVUE_MOTIFS depuis $DEP"; fi
fi
annexes

[ $ko -eq 0 ] && echo "Passation prête." || { echo "Passation incomplète."; [ $STRICT -eq 1 ] && exit 1; }
exit 0

# ---- exemple de passation.conf (racine du dépôt) ----
# PROJET="Exemple"
# GIT="commun/outils/gitw.sh"
# CONTEXTE="commun/orientation.md"
# FEUILLE="commun/Feuille de route.md"
# LIVRABLES="app-v:app/CHANGELOG.md:app/config/settings.py"
# DOCS=""                          (ex. "comparatif.html" : document web et son journal-data.js)
# AVANCEMENT="commun/avancement.md"
# ARCHIVE_AVANCEMENT=""          (ex. "commun/avancement-clos.md" : lignes closes du registre, identifiants uniques sur les deux)
# LISTES_PERMISES=""             (fichiers autorisés à tenir des cases à cocher, exception nommée)
# CITES=""                       (ex. "dev/methode/" : annexes des skills tenues dans le dépôt, contrôlées par --annexes)
# CONTROLES=""                   (ex. "différentiel sonde fuzz" : résultat de chacun exigé dans la ligne « Contrôles: » du commit étiqueté)
# REVUE_MOTIFS=10               (revue des motifs due toutes les 10 étiquettes depuis la dernière étiquette revue-motifs-…, et après une majeure livrée sans revue ; 0 : non suivie)
# LOTS="dev/lots"                (dossier des cahiers de lots : --suivant, vue d'avancement)
# VUE_PORT=""                    (ex. 8850 : force le port de la vue d'avancement, sinon calculé depuis PROJET ; renseigné, ses copies sont requises)
# OUTILS=""                      (ex. "commun/outils" : dossier d'outils hors de dev/outils/ et outils/)
# SKILLS_SOURCE=""               (ex. "skills" : le dépôt est la source de ses skills, contrôlées là plutôt que dans la copie installée)
# REPRISE=""                     (ex. "python3 -I outils/veille.py etat" : commande de reprise, code 1 = geste dû ; échec sans --strict, « ! » sous --strict)
# LIGNE_MAX=""                   (ex. 4000 : lignes du registre plus longues signalées, sans échec)
# VOISINES_OCTETS=50000          (--voisines : en dessous, le registre se lit en entier)
# SAVOIR_LIGNES=60  SAVOIR_CAR=300   (section « Savoir » du contexte : plafonds signalés, sans échec ; 0 : non contrôlé ; non numérique ou négatif : échec)
# INDEX_PIECES="commun/pieces.index"
# Les règles propres au projet vont dans le CLAUDE.md du dépôt (PROMPT, REGLES et DEPOT, clés du fichier de reprise retiré
# le 12/10/2026, ne sont plus lues : signalées tant qu'elles restent).
