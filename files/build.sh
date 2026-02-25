#!/bin/bash
# ─────────────────────────────────────────────────────────
# build.sh — Compile jdat-shell en binaire autonome
# Usage : bash build.sh
# ─────────────────────────────────────────────────────────

set -e

PYTHON=python3.13
BINARY_NAME=jdat-shell

echo "╔══════════════════════════════════╗"
echo "║   Build JDAT Shell → binaire     ║"
echo "╚══════════════════════════════════╝"

# 1. Vérifie Python 3.13
echo ""
echo "▶ Vérification Python 3.13..."
if ! command -v $PYTHON &>/dev/null; then
    echo "  Python 3.13 non trouvé. Installation..."
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update -q
    sudo apt install -y python3.13 python3.13-venv python3.13-dev
fi
echo "  ✓ $($PYTHON --version)"

# 2. Crée un environnement virtuel propre
echo ""
echo "▶ Création de l'environnement virtuel..."
$PYTHON -m venv .venv
source .venv/bin/activate
echo "  ✓ venv activé"

# 3. Installe les dépendances
echo ""
echo "▶ Installation des dépendances..."
pip install --upgrade pip -q
pip install cryptography pyinstaller -q
echo "  ✓ cryptography + pyinstaller installés"

# 4. Compile avec PyInstaller
echo ""
echo "▶ Compilation en binaire unique..."
pyinstaller \
    --onefile \
    --name "$BINARY_NAME" \
    --clean \
    --strip \
    shell.py

echo "  ✓ Binaire créé : dist/$BINARY_NAME"

# 5. Installe dans /usr/local/bin pour accès global
echo ""
echo "▶ Installation dans /usr/local/bin..."
sudo cp "dist/$BINARY_NAME" "/usr/local/bin/$BINARY_NAME"
sudo chmod +x "/usr/local/bin/$BINARY_NAME"
echo "  ✓ Installé ! Tu peux maintenant lancer : $BINARY_NAME"

# 6. Nettoyage
echo ""
echo "▶ Nettoyage des fichiers temporaires..."
rm -rf build __pycache__ *.spec
deactivate
echo "  ✓ Nettoyé"

echo ""
echo "╔══════════════════════════════════╗"
echo "║  ✓ Build terminé avec succès !   ║"
echo "╚══════════════════════════════════╝"
echo ""
echo "  Lance avec : jdat-shell"
echo "  Ou avec un fichier : jdat-shell mon_fichier.jdat"
echo ""
