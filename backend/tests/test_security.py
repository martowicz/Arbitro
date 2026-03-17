import pytest
from core.security import encrypt_data, decrypt_data
from cryptography.fernet import InvalidToken

def test_encryption_decryption_cycle():
    #Given
    original_text = "ThisIsComplicatedPassword12348765%$"

    #When
    encrypted = encrypt_data(original_text)
    decrypted = decrypt_data(encrypted)
    
    #Then
    assert original_text == decrypted
    assert original_text != encrypted
    assert isinstance(encrypted, str)

def test_encrypt_empty_string():
    original_text=""

    encrypted = encrypt_data(original_text)
    decrypted = decrypt_data(encrypted)

    assert decrypted == ""
    assert encrypted == ""

def test_decrypt_invalid_token():
    
    fake_encrypted_data = "this_is_not_real_AES_cipher_12345"
    
    with pytest.raises(InvalidToken):
        decrypt_data(fake_encrypted_data)

def test_encryption_is_randomized():
    password = "This_is_my_new_password1234"

    encrypted_1 = encrypt_data(password)
    encrypted_2 = encrypt_data(password)
    
    assert encrypted_1 != encrypted_2
    assert decrypt_data(encrypted_1) == password
    assert decrypt_data(encrypted_2) == password

def test_special_characters_and_emojis():
    crazy_password = "Zaźółć_gęślą_jaźń_⚽🚀!@#$%^&*()_+"
    
    encrypted = encrypt_data(crazy_password)
    decrypted = decrypt_data(encrypted)
    
    assert decrypted == crazy_password

def test_encrypt_none_value():

    assert encrypt_data(None) == ""
    assert decrypt_data(None) == ""

def test_whitespace_string():
    whitespace_text = "   \n\t  "
    
    encrypted = encrypt_data(whitespace_text)
    decrypted = decrypt_data(encrypted)
    
    assert decrypted == whitespace_text
    assert encrypted != ""