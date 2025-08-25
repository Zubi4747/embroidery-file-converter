from flask import Flask, request, render_template, send_file
from pyembroidery import read, write
import os
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

SUPPORTED_FORMATS = [
    'dst','exp','pes','jef','vp3','hus','xxx','pcs','vip','sew','shv','svg'
]

@app.route('/', methods=['GET','POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part', 400
        file = request.files['file']
        if file.filename == '':
            return 'No selected file', 400

        output_format = request.form.get('output_format')
        if output_format not in SUPPORTED_FORMATS:
            return f'Unsupported output format. Supported: {SUPPORTED_FORMATS}', 400

        filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        try:
            pattern = read(input_path)
        except Exception as e:
            return f'Failed to read file: {e}', 500

        output_filename = os.path.splitext(filename)[0] + '.' + output_format
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        try:
            write(pattern, output_path)
        except Exception as e:
            return f'Failed to write file: {e}', 500

        svg_preview = None
        if output_format != 'svg':
            try:
                svg_preview_path = os.path.join(app.config['UPLOAD_FOLDER'], 'preview.svg')
                write(pattern, svg_preview_path)
                with open(svg_preview_path, 'r') as f:
                    svg_preview = f.read()
            except Exception as e:
                svg_preview = f'Preview not available: {e}'

        return render_template('result.html', download_file=output_filename, svg_preview=svg_preview)

    return render_template('index.html', formats=SUPPORTED_FORMATS)

@app.route('/download/<filename>')
def download(filename):
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(path):
        return 'File not found', 404
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, use_reloader=False, threaded=True, host='0.0.0.0', port=port)
