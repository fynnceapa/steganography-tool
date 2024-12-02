import os
from flask import Flask, render_template, request, send_file, redirect, url_for
from PIL import Image

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ENCODED_FOLDER'] = 'encoded'

def convert_to_binary(message):
    binary_message = "".join(format(ord(char), '08b') for char in message)
    return binary_message

def check_capacity(img, secret_message):
    width, height = img.size
    max_bytes = width * height * 3 // 8
    return len(secret_message) <= max_bytes

def encode_message(image_path, secret_message, output_path):
    img = Image.open(image_path)
    img = img.convert("RGB")
    width, height = img.size
    binary_message = convert_to_binary(secret_message) + "00000000"

    if not check_capacity(img, binary_message):
        raise ValueError("Message is too large for the selected image.")

    pixels = list(img.getdata())
    new_pixels = []

    message_index = 0
    for r, g, b in pixels:
        if message_index < len(binary_message):
            r = (r & 0b11111110) | int(binary_message[message_index])
            message_index += 1
        if message_index < len(binary_message):
            g = (g & 0b11111110) | int(binary_message[message_index])
            message_index += 1
        if message_index < len(binary_message):
            b = (b & 0b11111110) | int(binary_message[message_index])
            message_index += 1
        new_pixels.append((r, g, b))

    img.putdata(new_pixels)
    img.save(output_path)

def decode_message(image_path):
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = list(img.getdata())

    binary_message = ""
    for r, g, b in pixels:
        binary_message += str(r & 1)
        binary_message += str(g & 1)
        binary_message += str(b & 1)

    message = ""
    for i in range(0, len(binary_message), 8):
        byte = binary_message[i:i + 8]
        if byte == "00000000":
            break
        message += chr(int(byte, 2))
    
    return message


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/image/encode', methods=['POST'])
def encode():
    image_file = request.files['file']
    secret_message = request.form['message']
    
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
    image_file.save(image_path)

    encoded_image_filename = 'encoded_' + image_file.filename
    output_path = os.path.join(app.config['ENCODED_FOLDER'], encoded_image_filename)

    encode_message(image_path, secret_message, output_path)

    return send_file(output_path, as_attachment=True)

@app.route('/image/last/encoded')
def download_last_encoded_image():
    encoded_images = os.listdir(app.config['ENCODED_FOLDER'])
    if encoded_images:
        last_encoded_image = encoded_images[-1]
        encoded_image = os.path.join(app.config['ENCODED_FOLDER'], last_encoded_image)
        encode_message = decode_message(encoded_image)
        return render_template('results.html', text = encode_message)
    else:
        return render_template('results.html', text = "No encoded image found.")

@app.route('/image/decode', methods=['POST'])
def decode():
    image_file = request.files['file']
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
    image_file.save(image_path)

    decoded_message = decode_message(image_path)

    return render_template('index.html', decoded_message = decoded_message)

@app.route('/image/last/decoded', methods=['GET'])
def download_last_decoded_image():
    decoded_images = os.listdir(app.config['UPLOAD_FOLDER'])
    if decoded_images:
        last_decoded_image = decode_message(os.path.join(app.config['UPLOAD_FOLDER'], decoded_images[-1]))
        return render_template('results.html', decoded_message = last_decoded_image)
    else:
        return render_template('results.html', decoded_message = "No decoded image found.")

@app.route('/results')
def results():
    return render_template('results.html')

@app.route('/go_back')
def go_back():
    return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['ENCODED_FOLDER']):
        os.makedirs(app.config['ENCODED_FOLDER'])
    
    app.run(debug=False, port=5003)


    
