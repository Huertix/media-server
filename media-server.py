
import os
import time
import hashlib
import zipfile
from io import BytesIO

from flask import Flask, render_template, redirect, url_for, request, send_file
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SubmitField

app = Flask(__name__)
app.config['SECRET_KEY'] = 'I have a dream'
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(app.root_path, 'media')
video_ext = ('mp4','mkv')
app.config['UPLOADED_PHOTOS_ALLOW'] = video_ext

media = UploadSet('photos', IMAGES)

configure_uploads(app, media)
patch_request_class(app)  # set maximum file size, default is 16MB


class UploadForm(FlaskForm):
    photo = FileField(validators=[FileAllowed(media, u'media Only!'), FileRequired(u'Choose a file!')])
    submit = SubmitField(u'Upload')


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    form = UploadForm()
    if form.validate_on_submit():
        for filename in request.files.getlist('photo'):
            # name = filename.filename
            # photos.save(filename, name=name + '.')
            if not os.path.isfile(os.path.join(app.root_path, 'media', filename.filename)):
                media.save(filename)
        success = True
    else:
        success = False
    return render_template('upload.html', form=form, success=success)


@app.route('/', methods=["GET", "POST"])
def manage_file():
    if request.method == 'POST':

        all_selected = request.form.getlist('media')
        all_files = [open(os.path.join(app.root_path, 'media', f), "rb") for f in all_selected]

        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            for individualFile in all_files:
                file_data = individualFile.read()
                file_name = individualFile.name.split('/')[-1]
                data = zipfile.ZipInfo(file_name)
                data.date_time = time.localtime(time.time())[:6]
                data.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(data, file_data)
        memory_file.seek(0)
        return send_file(memory_file, attachment_filename='media.zip', as_attachment=True)


    files_list = os.listdir(app.config['UPLOADED_PHOTOS_DEST'])

    files = []
    for file in files_list:
        ext = file.split('.')[-1]
        if ext in video_ext + IMAGES:
            files.append({'name': file, 'url': media.url(file), 'video': ext in video_ext})

    return render_template('manage.html', files=files)


@app.route('/open/<filename>')
def open_file(filename):
    ext = filename.rsplit(".")[-1]
    video = ext in video_ext
    file_url = media.url(filename)
    return render_template('browser.html', file_url=file_url, video=video)


@app.route('/delete/<filename>')
def delete_file(filename):
    file_path = media.path(filename)
    os.remove(file_path)
    return redirect(url_for('manage_file'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)