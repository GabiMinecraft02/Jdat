"""
JDAT - Module Python pour lire/écrire des fichiers .jdat
Format de données structurées avec chiffrement par bloc (AES-256)
"""

import re
import json
from pathlib import Path
from crypto import JDATCrypto


class JDATBlock:
    def __init__(self, name: str, link: str, btype: int, content: str, encrypted: bool = False):
        self.name = name
        self.link = link
        self.type = btype          # 1 = données structurées, 2 = texte/code brut
        self.content = content     # contenu brut (déchiffré ou non)
        self.encrypted = encrypted
        self._data = None          # cache parsé pour type 1

    def parse_data(self) -> dict:
        """Parse le contenu type 1 en dict clé:valeur"""
        if self.type != 1:
            return {}
        if self._data is not None:
            return self._data
        data = {}
        for line in self.content.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            if ':' in line:
                key, _, value = line.partition(':')
                data[key.strip()] = value.strip()
        self._data = data
        return data

    def get(self, key: str, default=None):
        """Accès rapide à une clé (type 1 uniquement)"""
        return self.parse_data().get(key, default)

    def set(self, key: str, value: str):
        """Modifie une clé (type 1 uniquement)"""
        d = self.parse_data()
        d[key] = value
        self._data = d
        self._rebuild_content()

    def _rebuild_content(self):
        """Reconstruit le contenu brut depuis _data"""
        if self.type == 1 and self._data is not None:
            lines = [f"  {k}: {v}" for k, v in self._data.items()]
            self.content = "\n".join(lines)

    def to_jdat(self) -> str:
        """Sérialise le bloc en texte JDAT"""
        if self.encrypted:
            header = f"(n:{self.name} l:{self.link} t:{self.type} encrypted{{"
            return f"{header}\n{self.content}\n}})"
        else:
            if self.type == 1:
                self._rebuild_content()
                header = f"(n:{self.name} l:{self.link} t:{self.type} {{"
                return f"{header}\n{self.content}\n}})"
            else:
                header = f"(n:{self.name} l:{self.link} t:{self.type}{{"
                return f"{header}\n{self.content}\n}})"

    def __repr__(self):
        status = "🔒" if self.encrypted else "🔓"
        return f"JDATBlock({status} n:{self.name} l:{self.link} t:{self.type})"


class JDATFile:
    def __init__(self, path: str = None):
        self.path = Path(path) if path else None
        self.blocks: list[JDATBlock] = []
        self.comments: list[str] = []
        self.crypto = JDATCrypto()

    # ─────────────────────────────────────────
    # PARSING
    # ─────────────────────────────────────────

    def load(self, path: str = None):
        """Charge et parse un fichier .jdat"""
        if path:
            self.path = Path(path)
        if not self.path or not self.path.exists():
            raise FileNotFoundError(f"Fichier introuvable : {self.path}")
        text = self.path.read_text(encoding='utf-8')
        self._parse(text)
        return self

    def _parse(self, text: str):
        """Parse le texte JDAT complet"""
        self.blocks = []
        self.comments = []

        # Commentaires : ({<...>})
        comment_pattern = re.compile(r'\(\{<(.*?)>\}\)', re.DOTALL)
        for m in comment_pattern.finditer(text):
            self.comments.append(m.group(1).strip())

        # Blocs : (n:... l:... t:N [encrypted]{ ... })
        block_pattern = re.compile(
            r'\(n:(\S+)\s+l:(\S+)\s+t:(\d+)\s*(encrypted)?\s*\{(.*?)\}\)',
            re.DOTALL
        )
        for m in block_pattern.finditer(text):
            name    = m.group(1)
            link    = m.group(2)
            btype   = int(m.group(3))
            enc     = m.group(4) == 'encrypted' if m.group(4) else False
            content = m.group(5)
            self.blocks.append(JDATBlock(name, link, btype, content, enc))

    # ─────────────────────────────────────────
    # ACCÈS
    # ─────────────────────────────────────────

    def get_by_link(self, link: str) -> JDATBlock | None:
        for b in self.blocks:
            if b.link == link:
                return b
        return None

    def get_by_name(self, name: str) -> JDATBlock | None:
        for b in self.blocks:
            if b.name == name:
                return b
        return None

    def list_blocks(self) -> list[dict]:
        return [{"name": b.name, "link": b.link, "type": b.type, "encrypted": b.encrypted}
                for b in self.blocks]

    # ─────────────────────────────────────────
    # MODIFICATION
    # ─────────────────────────────────────────

    def add_block(self, name: str, link: str, btype: int, content: str):
        """Ajoute un nouveau bloc"""
        if self.get_by_link(link):
            raise ValueError(f"Un bloc avec le lien '{link}' existe déjà")
        self.blocks.append(JDATBlock(name, link, btype, content))

    def remove_block(self, link: str) -> bool:
        """Supprime un bloc par son lien"""
        for i, b in enumerate(self.blocks):
            if b.link == link:
                del self.blocks[i]
                return True
        return False

    # ─────────────────────────────────────────
    # CHIFFREMENT PAR BLOC
    # ─────────────────────────────────────────

    def encrypt_block(self, link: str, password: str) -> bool:
        """Chiffre un bloc spécifique"""
        block = self.get_by_link(link)
        if not block:
            return False
        if block.encrypted:
            raise ValueError("Bloc déjà chiffré")
        if block.type == 1:
            block._rebuild_content()
        block.content = self.crypto.encrypt(block.content, password)
        block.encrypted = True
        return True

    def decrypt_block(self, link: str, password: str) -> bool:
        """Déchiffre un bloc spécifique"""
        block = self.get_by_link(link)
        if not block:
            return False
        if not block.encrypted:
            raise ValueError("Bloc non chiffré")
        block.content = self.crypto.decrypt(block.content, password)
        block.encrypted = False
        block._data = None  # reset cache
        return True

    # ─────────────────────────────────────────
    # SAUVEGARDE
    # ─────────────────────────────────────────

    def save(self, path: str = None):
        """Sauvegarde le fichier .jdat"""
        if path:
            self.path = Path(path)
        if not self.path:
            raise ValueError("Aucun chemin de fichier défini")
        self.path.write_text(self.to_jdat(), encoding='utf-8')

    def to_jdat(self) -> str:
        """Sérialise tout le fichier en texte JDAT"""
        parts = []
        if self.comments:
            for c in self.comments:
                parts.append(f"({{<{c}>}})")
        for b in self.blocks:
            parts.append(b.to_jdat())
        return "\n\n".join(parts) + "\n"
