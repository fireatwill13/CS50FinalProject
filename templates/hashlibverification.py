from werkzeug.security import generate_password_hash

password = "examplepassword"
hashed = generate_password_hash(password, method='pbkdf2:sha256')
print(hashed)
