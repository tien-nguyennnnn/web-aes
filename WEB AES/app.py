import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64
import hashlib

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULT_FOLDER'] = 'results'

# Tạo thư mục nếu chưa tồn tại
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULT_FOLDER'], exist_ok=True)

def derive_key(key_string):
    """Tạo khóa AES 256-bit từ chuỗi bất kỳ"""
    return hashlib.sha256(key_string.encode()).digest()

def encrypt_file(input_file, output_file, key):
    """Mã hóa file bằng AES-CBC"""
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    
    with open(input_file, 'rb') as f:
        plaintext = f.read()
    
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
    
    with open(output_file, 'wb') as f:
        f.write(iv + ciphertext)

def decrypt_file(input_file, output_file, key):
    """Giải mã file bằng AES-CBC"""
    with open(input_file, 'rb') as f:
        data = f.read()
    
    iv = data[:16]
    ciphertext = data[16:]
    
    cipher = AES.new(key, AES.MODE_CBC, iv)
    plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
    
    with open(output_file, 'wb') as f:
        f.write(plaintext)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Kiểm tra file và khóa
        if 'file' not in request.files:
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected!', 'error')
            return redirect(request.url)
        
        key = request.form.get('key')
        if not key:
            flash('No key provided!', 'error')
            return redirect(request.url)
        
        # Lưu file upload
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(input_path)
        
        # Xử lý mã hóa/giải mã
        operation = request.form.get('operation')
        output_filename = f"{operation}d_{file.filename}"
        output_path = os.path.join(app.config['RESULT_FOLDER'], output_filename)
        
        try:
            aes_key = derive_key(key)
            
            if operation == 'encrypt':
                encrypt_file(input_path, output_path, aes_key)
                flash('File encrypted successfully!', 'success')
            elif operation == 'decrypt':
                decrypt_file(input_path, output_path, aes_key)
                flash('File decrypted successfully!', 'success')
            else:
                flash('Invalid operation!', 'error')
                return redirect(request.url)
            
            return redirect(url_for('download', filename=output_filename))
        
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('index.html')

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)