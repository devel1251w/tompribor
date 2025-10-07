from flask import Flask, request, send_file, jsonify, send_from_directory
import os
import excel2json
import json2html
import html2pdf

app = Flask(__name__)

@app.route('/tompribor_generator/api/upload', methods=['POST'])
def upload_file():
    # Проверяем, что пришёл файл
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Имя файла пустое'}), 400

    # Формируем путь для сохранения во временную папку
    in_xlsx = os.path.join("tmp", file.filename)
    file.save(in_xlsx)

    excel2json.process(in_xlsx, 'tmp/m.json')
    json2html.process('tmp/m.json', 'tmp/m.html')
    html2pdf.process('tmp/m.html', 'tmp/m.pdf')

    # Отправляем файл клиенту
    return send_file('tmp/m.pdf', as_attachment=True)

@app.route('/tompribor_generator/api/instruction', methods=['GET'])
def get_instruction():
    return send_file('static/instruction.pdf', as_attachment=True)

@app.route('/tompribor_generator')
def index():
    return send_from_directory('.', 'static/index.html')

@app.route('/')
def home():
    return "404 Not Found", 404


if __name__ == '__main__':
    app.run(debug=True, port=5000)
