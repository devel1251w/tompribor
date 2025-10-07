from flask import Flask, request, send_file, jsonify, send_from_directory
import os, threading, uuid
import excel2json, json2html, html2pdf

app = Flask(__name__)

tasks = {}  # словарь {task_id: {"status": "pending"|"processing"|"done"|"error"}}

def process_file(task_id, filename):
    try:
        tasks[task_id]['status'] = 'processing'
        in_xlsx = os.path.join("tmp", filename)
        excel2json.process(in_xlsx, f'tmp/{task_id}.json')
        json2html.process(f'tmp/{task_id}.json', f'tmp/{task_id}.html')
        html2pdf.process(f'tmp/{task_id}.html', f'tmp/{task_id}.pdf')
        tasks[task_id]['status'] = 'done'
    except Exception as e:
        tasks[task_id]['status'] = 'error'
        tasks[task_id]['error'] = str(e)


@app.route('/tompribor_generator/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Имя файла пустое'}), 400

    task_id = str(uuid.uuid4())
    tasks[task_id] = {'status': 'pending'}

    filepath = os.path.join("tmp", f"{task_id}_{file.filename}")
    file.save(filepath)

    threading.Thread(target=process_file, args=(task_id, f"{task_id}_{file.filename}")).start()

    return jsonify({'task_id': task_id}), 200


@app.route('/tompribor_generator/api/status/<task_id>', methods=['GET'])
def check_status(task_id):
    task = tasks.get(task_id)
    if not task:
        return jsonify({'error': 'Задача не найдена'}), 404
    return jsonify(task)


@app.route('/tompribor_generator/api/download/<task_id>', methods=['GET'])
def download_file(task_id):
    file_path = f'tmp/{task_id}.pdf'
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': 'Файл не готов'}), 404


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
    app.run(debug=False, host='0.0.0.0', port=61236)