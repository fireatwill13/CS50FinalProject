import ssl
import hashlib

print(ssl.OPENSSL_VERSION)  # Should return OpenSSL 1.1.1 or later
print(dir(hashlib))         # Check for 'scrypt' in the output
