#!/usr/bin/env python3
"""
JDAT Shell - Shell interactif pour fichiers .jdat
Commandes : open, new, save, list, read, find, add, edit, del,
            enc, dec, goto, back, pwd, help, exit
"""

import sys
import os
import getpass
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jdat import JDATFile, JDATBlock


# ─────────────────────────────────────────────────────────────
# Couleurs ANSI
# ─────────────────────────────────────────────────────────────
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    CYAN    = "\033[96m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    RED     = "\033[91m"
    GREY    = "\033[90m"
    MAGENTA = "\033[95m"

def color(text, *codes):
    return "".join(codes) + str(text) + C.RESET

def header():
    print(color("╔══════════════════════════════════════╗", C.CYAN, C.BOLD))
    print(color("║        JDAT Shell  v1.1              ║", C.CYAN, C.BOLD))
    print(color("║  Format de données .jdat + AES-256   ║", C.CYAN, C.BOLD))
    print(color("╚══════════════════════════════════════╝", C.CYAN, C.BOLD))
    print(color("  Tapez 'help' pour la liste des commandes\n", C.GREY))

def prompt(jf, current) -> str:
    name = jf.path.name if jf and jf.path else "aucun fichier"
    base = color("jdat", C.CYAN, C.BOLD) + color(f"({name})", C.GREY)
    if current:
        base += color(f" → {current.link}", C.MAGENTA, C.BOLD)
    return base + color(" > ", C.CYAN)

def print_ok(msg):   print(color(f"  ✓ {msg}", C.GREEN))
def print_err(msg):  print(color(f"  ✗ {msg}", C.RED))
def print_info(msg): print(color(f"  ℹ {msg}", C.YELLOW))

HELP = f"""
\033[1m\033[96mCommandes disponibles :\033[0m

  \033[93mFichiers\033[0m
    open  <fichier.jdat>     Ouvre un fichier existant
    new   <fichier.jdat>     Crée un nouveau fichier vide
    save  [fichier.jdat]     Sauvegarde (chemin optionnel)

  \033[93mNavigation  (comme cd dans un terminal)\033[0m
    goto  <lien|nom>         Entre dans un bloc  (alias : cd)
    back                     Retourne à la racine (alias : ..)
    pwd                      Affiche le bloc courant
    ls                       Alias de list

  \033[93mLecture\033[0m
    list                     Liste tous les blocs
    read  [lien]             Affiche un bloc (vide = bloc courant)
    find  <texte>            Recherche dans les noms/liens

  \033[93mÉcriture\033[0m
    add                      Ajoute un nouveau bloc (assistant)
    edit  [lien]             Modifie un bloc (vide = bloc courant)
    del   [lien]             Supprime un bloc (vide = bloc courant)

  \033[93mChiffrement\033[0m
    enc   [lien]             Chiffre un bloc (vide = bloc courant)
    dec   [lien]             Déchiffre un bloc (vide = bloc courant)

  \033[93mAutres\033[0m
    help                     Affiche cette aide
    exit / quit / q          Quitte le shell
"""

def display_block(block: JDATBlock):
    status = color("🔒 CHIFFRÉ", C.RED, C.BOLD) if block.encrypted else color("🔓 clair", C.GREEN)
    ttype  = "données (t:1)" if block.type == 1 else "code/texte brut (t:2)"
    print()
    print(color(f"  ┌─ {block.name} ", C.CYAN, C.BOLD) + color(f"({ttype}) {status}", C.GREY))
    print(color(f"  │  lien : {block.link}", C.GREY))
    print(color(f"  ├{'─'*40}", C.CYAN))
    if block.encrypted:
        print(color("  │  [contenu chiffré — utilisez 'dec' pour lire]", C.YELLOW))
    elif block.type == 1:
        data = block.parse_data()
        for k, v in data.items():
            print(color("  │  ", C.CYAN) + color(f"{k}", C.BOLD) + color(f" : {v}", C.RESET))
    else:
        for line in block.content.strip().splitlines():
            print(color("  │  ", C.CYAN) + line)
    print(color(f"  └{'─'*40}", C.CYAN))
    print()

# ── Fichiers ──────────────────────────────────────────────────
def cmd_open(args, jf):
    if not args:
        print_err("Usage : open <fichier.jdat>")
        return jf
    try:
        new_jf = JDATFile(args[0])
        new_jf.load()
        print_ok(f"Fichier ouvert : {args[0]} ({len(new_jf.blocks)} bloc(s))")
        return new_jf
    except FileNotFoundError:
        print_err(f"Fichier introuvable : {args[0]}")
    except Exception as e:
        print_err(f"Erreur de lecture : {e}")
    return jf

def cmd_new(args, jf):
    if not args:
        print_err("Usage : new <fichier.jdat>")
        return jf
    path = args[0] if args[0].endswith('.jdat') else args[0] + '.jdat'
    new_jf = JDATFile(path)
    print_ok(f"Nouveau fichier : {path}")
    return new_jf

def cmd_save(args, jf):
    if not jf:
        print_err("Aucun fichier ouvert")
        return
    try:
        jf.save(args[0] if args else None)
        print_ok(f"Sauvegardé : {jf.path}")
    except Exception as e:
        print_err(f"Erreur : {e}")

# ── Navigation ────────────────────────────────────────────────
def cmd_goto(args, jf, current):
    if not jf:
        print_err("Aucun fichier ouvert")
        return current
    if not args:
        if current:
            display_block(current)
            return current
        print_err("Usage : goto <lien>")
        return current
    target = args[0]
    if target in ('..', '/'):
        print_ok("Retour à la racine")
        return None
    block = jf.get_by_link(target) or jf.get_by_name(target)
    if not block:
        print_err(f"Bloc introuvable : '{target}'")
        return current
    print_ok(f"Entré dans '{block.name}'  (lien: {block.link})")
    display_block(block)
    return block

def cmd_back(current):
    if current:
        print_ok(f"Retour à la racine  (quitté : {current.link})")
    else:
        print_info("Déjà à la racine")
    return None

def cmd_pwd(current):
    if current:
        display_block(current)
    else:
        print_info("Racine — aucun bloc sélectionné  (utilisez 'goto <lien>')")

# ── Lecture ───────────────────────────────────────────────────
def cmd_list(jf):
    if not jf:
        print_err("Aucun fichier ouvert")
        return
    if not jf.blocks:
        print_info("Aucun bloc dans ce fichier")
        return
    print()
    print(color(f"  {'NOM':<20} {'LIEN':<20} {'TYPE':<8} {'ÉTAT'}", C.BOLD))
    print(color(f"  {'─'*60}", C.GREY))
    for b in jf.blocks:
        etat = color("🔒 chiffré", C.RED) if b.encrypted else color("🔓 clair", C.GREEN)
        t    = "données" if b.type == 1 else "code"
        print(f"  {color(b.name, C.CYAN):<29} {color(b.link, C.YELLOW):<29} {t:<8} {etat}")
    print()

def cmd_read(args, jf, current):
    if not jf:
        print_err("Aucun fichier ouvert")
        return
    if not args:
        if current:
            display_block(current)
        else:
            print_err("Usage : read <lien>  (ou 'goto <lien>' d'abord)")
        return
    block = jf.get_by_link(args[0]) or jf.get_by_name(args[0])
    if not block:
        print_err(f"Bloc introuvable : {args[0]}")
        return
    display_block(block)

def cmd_find(args, jf):
    if not jf:
        print_err("Aucun fichier ouvert")
        return
    if not args:
        print_err("Usage : find <texte>")
        return
    q     = args[0].lower()
    found = [b for b in jf.blocks if q in b.name.lower() or q in b.link.lower()]
    if not found:
        print_info("Aucun résultat")
        return
    print_info(f"{len(found)} résultat(s) :")
    for b in found:
        display_block(b)

# ── Écriture ──────────────────────────────────────────────────
def cmd_add(jf):
    if not jf:
        print_err("Aucun fichier ouvert")
        return
    print(color("\n  ── Nouveau bloc ──", C.CYAN, C.BOLD))
    name  = input(color("  nom  (n:) > ", C.CYAN)).strip()
    link  = input(color("  lien (l:) > ", C.CYAN)).strip()
    btype = input(color("  type [1=données / 2=code] > ", C.CYAN)).strip()
    btype = int(btype) if btype in ('1', '2') else 1
    print(color("  Contenu (ligne vide pour terminer) :", C.GREY))
    lines = []
    while True:
        line = input(color("  > ", C.CYAN))
        if not line:
            break
        lines.append(("  " if btype == 1 else "") + line)
    try:
        jf.add_block(name, link, btype, "\n".join(lines))
        print_ok(f"Bloc '{name}' ajouté  (lien: {link})")
    except ValueError as e:
        print_err(str(e))

def cmd_edit(args, jf, current):
    if not jf:
        print_err("Aucun fichier ouvert")
        return
    target = args[0] if args else (current.link if current else None)
    if not target:
        print_err("Usage : edit <lien>  (ou 'goto <lien>' d'abord)")
        return
    block = jf.get_by_link(target) or jf.get_by_name(target)
    if not block:
        print_err(f"Bloc introuvable : {target}")
        return
    if block.encrypted:
        print_err("Déchiffrez le bloc avant de le modifier  (dec)")
        return
    display_block(block)
    if block.type == 1:
        key = input(color("  clé à modifier > ", C.CYAN)).strip()
        if not key:
            return
        val = input(color(f"  nouvelle valeur pour '{key}' > ", C.CYAN)).strip()
        block.set(key, val)
        print_ok(f"'{key}' mis à jour")
    else:
        print(color("  Nouveau contenu (ligne vide pour terminer) :", C.GREY))
        lines = []
        while True:
            line = input(color("  > ", C.CYAN))
            if not line:
                break
            lines.append(line)
        block.content = "\n".join(lines)
        print_ok("Contenu mis à jour")

def cmd_del(args, jf, current):
    if not jf:
        print_err("Aucun fichier ouvert")
        return current
    target = args[0] if args else (current.link if current else None)
    if not target:
        print_err("Usage : del <lien>  (ou 'goto <lien>' d'abord)")
        return current
    confirm = input(color(f"  Supprimer '{target}' ? (oui/non) > ", C.RED)).strip().lower()
    if confirm in ('oui', 'o', 'yes', 'y'):
        if jf.remove_block(target):
            print_ok(f"Bloc '{target}' supprimé")
            if current and current.link == target:
                print_info("Bloc courant supprimé → retour à la racine")
                return None
        else:
            print_err(f"Bloc introuvable : {target}")
    return current

# ── Chiffrement ───────────────────────────────────────────────
def cmd_enc(args, jf, current):
    if not jf:
        print_err("Aucun fichier ouvert")
        return
    target = args[0] if args else (current.link if current else None)
    if not target:
        print_err("Usage : enc <lien>  (ou 'goto <lien>' d'abord)")
        return
    block = jf.get_by_link(target) or jf.get_by_name(target)
    if not block:
        print_err(f"Bloc introuvable : {target}")
        return
    if block.encrypted:
        print_err("Ce bloc est déjà chiffré")
        return
    pwd  = getpass.getpass(color("  Mot de passe > ", C.YELLOW))
    pwd2 = getpass.getpass(color("  Confirmer    > ", C.YELLOW))
    if pwd != pwd2:
        print_err("Les mots de passe ne correspondent pas")
        return
    try:
        jf.encrypt_block(target, pwd)
        print_ok(f"Bloc '{target}' chiffré avec AES-256-GCM ✓")
    except Exception as e:
        print_err(str(e))

def cmd_dec(args, jf, current):
    if not jf:
        print_err("Aucun fichier ouvert")
        return
    target = args[0] if args else (current.link if current else None)
    if not target:
        print_err("Usage : dec <lien>  (ou 'goto <lien>' d'abord)")
        return
    block = jf.get_by_link(target) or jf.get_by_name(target)
    if not block:
        print_err(f"Bloc introuvable : {target}")
        return
    if not block.encrypted:
        print_err("Ce bloc n'est pas chiffré")
        return
    pwd = getpass.getpass(color("  Mot de passe > ", C.YELLOW))
    try:
        jf.decrypt_block(target, pwd)
        print_ok(f"Bloc '{target}' déchiffré")
        display_block(block)
    except ValueError as e:
        print_err(str(e))

# ─────────────────────────────────────────────────────────────
# BOUCLE PRINCIPALE
# ─────────────────────────────────────────────────────────────
def main():
    header()
    jf      = None
    current = None

    if len(sys.argv) > 1:
        jf = cmd_open([sys.argv[1]], jf)

    while True:
        try:
            raw = input(prompt(jf, current)).strip()
        except (KeyboardInterrupt, EOFError):
            print(color("\n  Au revoir !", C.CYAN))
            break

        if not raw:
            continue

        parts = raw.split()
        cmd   = parts[0].lower()
        args  = parts[1:]

        if   cmd in ('exit', 'quit', 'q'):   print(color("  Au revoir !", C.CYAN)); break
        elif cmd == 'help':                   print(HELP)
        elif cmd == 'open':                   jf = cmd_open(args, jf);  current = None
        elif cmd == 'new':                    jf = cmd_new(args, jf);   current = None
        elif cmd == 'save':                   cmd_save(args, jf)
        elif cmd in ('goto', 'cd'):           current = cmd_goto(args, jf, current)
        elif cmd in ('back', '..'):           current = cmd_back(current)
        elif cmd == 'pwd':                    cmd_pwd(current)
        elif cmd in ('list', 'ls'):           cmd_list(jf)
        elif cmd == 'read':                   cmd_read(args, jf, current)
        elif cmd == 'find':                   cmd_find(args, jf)
        elif cmd == 'add':                    cmd_add(jf)
        elif cmd == 'edit':                   cmd_edit(args, jf, current)
        elif cmd == 'del':                    current = cmd_del(args, jf, current)
        elif cmd == 'enc':                    cmd_enc(args, jf, current)
        elif cmd == 'dec':                    cmd_dec(args, jf, current)
        else:
            print_err(f"Commande inconnue : '{cmd}' — tapez 'help'")


if __name__ == '__main__':
    main()
