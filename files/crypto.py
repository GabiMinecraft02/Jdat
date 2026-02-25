"""
JDAT Crypto - Chiffrement AES-256 par bloc
Utilise AES-256-GCM (authentifié) via la bibliothèque cryptography
"""

import os
import base64
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class JDATCrypto:
    """Chiffrement AES-256-GCM par bloc, dérivation de clé via SHA-256"""

    NONCE_SIZE = 12   # 96 bits pour GCM
    SALT_SIZE  = 16   # sel pour renforcer le mot de passe

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Dérive une clé AES-256 depuis un mot de passe + sel"""
        key_material = password.encode('utf-8') + salt
        return hashlib.sha256(key_material).digest()  # 32 bytes = 256 bits

    def encrypt(self, plaintext: str, password: str) -> str:
        """
        Chiffre un texte avec AES-256-GCM.
        Retourne une chaîne base64 : salt(16) + nonce(12) + ciphertext
        """
        salt  = os.urandom(self.SALT_SIZE)
        nonce = os.urandom(self.NONCE_SIZE)
        key   = self._derive_key(password, salt)

        aesgcm = AESGCM(key)
        ct     = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)

        raw    = salt + nonce + ct
        return base64.b64encode(raw).decode('ascii')

    def decrypt(self, ciphertext_b64: str, password: str) -> str:
        """
        Déchiffre un texte AES-256-GCM depuis base64.
        Lève une exception si le mot de passe est incorrect.
        """
        try:
            raw   = base64.b64decode(ciphertext_b64.strip())
            salt  = raw[:self.SALT_SIZE]
            nonce = raw[self.SALT_SIZE:self.SALT_SIZE + self.NONCE_SIZE]
            ct    = raw[self.SALT_SIZE + self.NONCE_SIZE:]

            key    = self._derive_key(password, salt)
            aesgcm = AESGCM(key)
            pt     = aesgcm.decrypt(nonce, ct, None)
            return pt.decode('utf-8')
        except Exception:
            raise ValueError("❌ Mot de passe incorrect ou données corrompues")
