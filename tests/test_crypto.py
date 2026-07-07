"""Tests for encryption utilities."""

from cryptography.fernet import InvalidToken

from app.crypto import decrypt, encrypt


def test_encrypt_decrypt_round_trip():
    """Test basic round-trip encryption and decryption."""
    original = "ghp_test_token_123456"
    encrypted = encrypt(original)
    assert encrypted != original
    decrypted = decrypt(encrypted)
    assert decrypted == original


def test_encrypted_values_differ():
    """Test that same plaintext produces different ciphertexts (IV randomization)."""
    t1 = encrypt("same-value")
    t2 = encrypt("same-value")
    assert t1 != t2


def test_decrypt_invalid_token():
    """Test that decrypting garbage raises InvalidToken."""
    try:
        decrypt("not-a-valid-encrypted-token")
        assert False, "Expected InvalidToken"
    except InvalidToken:
        pass


def test_decrypt_empty_string():
    """Test that decrypting empty string raises InvalidToken."""
    try:
        decrypt("")
        assert False, "Expected InvalidToken"
    except InvalidToken:
        pass


def test_decrypt_tampered_token():
    """Test that tampered ciphertext raises InvalidToken."""
    token = encrypt("secret")
    tampered = token[:-1] + ("X" if token[-1] != "X" else "Y")
    try:
        decrypt(tampered)
        assert False, "Expected InvalidToken"
    except InvalidToken:
        pass
