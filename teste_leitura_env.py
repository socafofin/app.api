import base64

# Simule a leitura da ENCRYPTION_KEY do .env (COLE A SUA CHAVE DO .ENV AQUI DENTRO DAS ASPAS!)
encryption_key_from_env_str = "b'\\x9b(\\x1ao\\x11\\x87\\x14\\xa5\\xb5\\xc0\\xf5{\\xa4\\xb2\\x1em\\xa8\\xeb2\\x8f\\x97v\\x84f\\xc2\\x1b\\xdb\\x7f\\xcf~\\xdbL'"  # <-- SUA CHAVE DO .ENV AQUI!

# Remova as aspas extras se estiverem presentes no início e final
if encryption_key_from_env_str.startswith("'") and encryption_key_from_env_str.endswith("'"):
    encryption_key_from_env_str = encryption_key_from_env_str[1:-1]
if encryption_key_from_env_str.startswith("b'") and encryption_key_from_env_str.endswith("'"):
    encryption_key_from_env_str = encryption_key_from_env_str[2:-1]


# Converta a string para bytes literais
encryption_key_from_env = encryption_key_from_env_str.encode('latin-1').decode('unicode_escape').encode('latin-1')


# Codifique para Base64 URL-safe
encryption_key_encoded = base64.urlsafe_b64encode(encryption_key_from_env)

print("Chave Original (bytes):", encryption_key_from_env)
print("Chave Codificada (Base64 URL-safe):", encryption_key_encoded)
print("Tamanho da Chave Codificada:", len(encryption_key_encoded))

# Decodifique de volta para verificar
encryption_key_decoded = base64.urlsafe_b64decode(encryption_key_encoded)
print("Chave Decodificada (bytes):", encryption_key_decoded)
print("Chave Decodificada é igual à Original?", encryption_key_decoded == encryption_key_from_env)