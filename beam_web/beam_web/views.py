# -*- coding: utf-8 -*-
from flask import request, redirect, url_for, flash, render_template
import os
import datetime

from flask.ext.login import login_user, logout_user, login_required, LoginManager, current_user
from werkzeug.utils import secure_filename

from beam_application.presentation import Presentation, Vnc
from beam_projector.projector import Projector
from beam_web.forms import ConnectionControlForm
from beam_web.forms import PresentationControlForm
from beam_web.forms import LoginForm
from beam_web.forms import ProjectorControlForm
from beam_web.models import UserDatabase, BeamAnonymousUserMixin
from beam_web import app


"""
    Local Variables
"""

# Objects for Application Control
presentation = Presentation()
projector = Projector()

# Objects for Authentication
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.anonymous_user = BeamAnonymousUserMixin
user_database = UserDatabase(app.config["SAFE_ENVIRONMENT"])

"""
    Helper Functions
"""


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config["ALLOWED_EXTENSIONS"]


def get_upload_folder():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        app.config["UPLOAD_FOLDER"])


def get_human_size(nbytes):
    """
    Method to get filesize in human readable sizes
    """
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    if nbytes == 0:
        return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


"""
    Index
"""


@app.route("/")
@app.route("/index")
def index():
    """
    Method for python flask, to set path for landing page of the web frontend
    """
    # generate the file list
    file_list = list()
    for filename in os.listdir(get_upload_folder()):
        if allowed_file(filename):
            file_list.append((filename,
                              get_human_size(os.path.getsize(os.path.join(get_upload_folder(), filename))),
                              datetime.datetime.fromtimestamp(
                                  os.path.getmtime(os.path.join(get_upload_folder(), filename))
                              ).strftime("%Y-%m-%d %H:%M:%S")
                              ))
    # check vnc
    if presentation.vnc.status() == Vnc.STATUS_ERROR:
        flash(presentation.vnc.message(), "danger")

    # render the template
    return render_template("index.html",
                           vnc_status=presentation.vnc.status_text(),
                           vnc_failure=presentation.vnc.message(),
                           file_list=file_list)


"""
    Projector
"""


@app.route("/projector/control", methods=["POST"])
def projector_control():
    """
    Method for python flask, to set path for settings page of the web frontend
    """
    if not current_user.is_lecturer():
        flash("Zugriff nicht moeglich, bitte melden Sie sich an.", "danger")
        return redirect(url_for("index"))

    form = ProjectorControlForm(request.form)
    if form.action.data == "power_on":
        projector.power_on()
    elif form.action.data == "power_off":
        projector.power_off()
    elif form.action.data == "mute_on":
        projector.mute_on()
    elif form.action.data == "mute_off":
        projector.mute_off()

    return redirect(url_for("index"))


"""
    Software
"""


@app.route("/software")
def software():
    """
    Method for python flask, to set path for software page of the web frontend;
    there one can download the one-click VNC applications for his/her os.
    """

    return render_template("software.html")


"""
    Connections VNC Client/Server
"""


@app.route("/connections")
def connections():
    """
    Method for python flask, to set path for connections page of the web frontend;
    there one can handle the vnc connections
    """

    return render_template("connections.html",
                           ip_address=str(request.remote_addr),
                           active=presentation.vnc.is_active(),
                           user_list=user_database.user_database)


@app.route("/connections/control", methods=["POST"])
def connections_control():
    """
    Method for python flask, to set path for connection control page of the web frontend;
    one needs to be logged in, to get access. Here the user_list can be managed
    """
    if not current_user.is_lecturer():
        flash("Zugriff nicht moeglich, bitte melden Sie sich an.", "danger")
        return redirect(url_for("index"))

    form = ConnectionControlForm(request.form)
    if form.action.data == "start":
        presentation.stop()
        result = presentation.vnc.start_connection(form.param.data, "5900")
        if result:
            flash("Verbindung wird aufgebaut", "success")
        else:
            flash("Fehler beim Verbindungsaufbau", "danger")
    elif form.action.data == "stop":
        presentation.stop()
    return redirect(url_for("index"))


"""
    File Management and Upload
"""


@app.route("/upload")
def upload():
    """
    Method for python flask, to set path for uploaded files page of the web frontend,
    one can upload several filetypes, to start for example pdf presentation
    directly on the mediabox instead of using vnc connection
    """
    file_list = list()
    for filename in os.listdir(get_upload_folder()):
        if allowed_file(filename):
            file_list.append((filename,
                              get_human_size(os.path.getsize(os.path.join(get_upload_folder(), filename))),
                              datetime.datetime.fromtimestamp(
                                  os.path.getmtime(os.path.join(get_upload_folder(), filename))
                              ).strftime("%Y-%m-%d %H:%M:%S")
                              ))
    return render_template("upload.html",
                           file_list=file_list)


@app.route("/upload/file", methods=["POST"])
def upload_file():
    """
    Method for python flask, to set path for upload page of the web frontend;
    one can upload files for presentation. login required
    """
    if not current_user.is_lecturer():
        flash("Zugriff nicht moeglich, bitte melden Sie sich an.", "danger")
        return redirect(url_for("index"))

    file_obj = request.files['file']
    if file_obj and allowed_file(file_obj.filename):
        filename = secure_filename(file_obj.filename)
        file_obj.save(os.path.join(get_upload_folder(), filename))
        return redirect(url_for("index"))


"""
    Presentation of Files
"""


@app.route("/presentation/start", methods=["POST"])
def presentation_start():
    """
    Method for python flask, to set path for starting presentation page of the web frontend
    here, you can start presentation of the former uploaded files. login required
    """
    if not current_user.is_lecturer():
        flash("Zugriff nicht moeglich, bitte melden Sie sich an.", "danger")
        return redirect(url_for("index"))

    # stop all previous presentations
    presentation.stop()

    # get content of the form
    form = PresentationControlForm(request.form)

    # get file_name and file_extension
    file_name = os.path.join(get_upload_folder(), form.param.data)
    file_extension = str(os.path.splitext(file_name)[1]).lower()

    # when the file exists start the matching presentation
    if os.path.isfile(file_name):
        # start pdf presentation
        if file_extension == ".pdf":
            res = presentation.pdf.start_presentation(get_upload_folder(), form.param.data)
            if res:
                return redirect(url_for("presentation_pdf"))
        # start video presentation
        elif file_extension == ".avi" or file_extension == ".mp4":
            res = presentation.video.start_presentation(get_upload_folder(), form.param.data)
            if res:
                return redirect(url_for("presentation_video"))
        return redirect(url_for("index"))
    else:
        return redirect(url_for("index"))


@app.route("/presentation/pdf")
def presentation_pdf():
    """
    Method for python flask, to set path for presenting pdf page of the web frontend
    login required
    """
    if not current_user.is_lecturer():
        flash("Zugriff nicht moeglich, bitte melden Sie sich an.", "danger")
        return redirect(url_for("index"))

    if not presentation.pdf.is_active():
        return redirect(url_for("index"))
    return render_template("presentation/presentation_pdf.html",
                           current_file=presentation.pdf.filename,
                           active=presentation.pdf.is_active(),
                           page_count=presentation.pdf.get_page_count())


@app.route("/presentation/pdf/control", methods=["POST"])
def presentation_pdf_control():
    """
    Method for python flask, to set path for presenting pdf page of the web frontend
    each document type has its own needs of control buttons. login required
    """
    if not current_user.is_lecturer():
        flash("Zugriff nicht moeglich, bitte melden Sie sich an.", "danger")
        return redirect(url_for("index"))

    form = PresentationControlForm(request.form)
    if presentation.pdf.is_active():
        # Stop the Presentation
        if form.action.data == "stop":
            presentation.stop()
            return redirect(url_for("index"))
        elif form.action.data == "next":
            presentation.pdf.next_page()
        elif form.action.data == "previous":
            presentation.pdf.previous_page()
        elif form.action.data == "go_to_page":
            presentation.pdf.go_to_page(form.param.data)
    return redirect(url_for("presentation_pdf"))


@app.route("/presentation/video")
def presentation_video():
    """
    Method for python flask, to set path for presenting video page of the web frontend
    login required
    """
    if not current_user.is_lecturer():
        flash("Zugriff nicht moeglich, bitte melden Sie sich an.", "danger")
        return redirect(url_for("index"))

    if not presentation.video.is_active():
        return redirect(url_for("index"))

    return render_template("presentation/presentation_video.html",
                           current_file=presentation.video.filename,
                           active=presentation.video.is_active())


@app.route("/presentation/video/control", methods=["POST"])
def presentation_video_control():
    """
    Method for python flask, to set path for presenting video page of the web frontend
    each document type has its own needs of control buttons. login required
    """
    if not current_user.is_lecturer():
        flash("Zugriff nicht moeglich, bitte melden Sie sich an.", "danger")
        return redirect(url_for("index"))

    form = PresentationControlForm(request.form)
    if presentation.video.is_active():
        # Stop the Presentation
        if form.action.data == "stop":
            presentation.stop()
            return redirect(url_for("index"))
        elif form.action.data == "play_pause":
            presentation.video.toggle_play()
        elif form.action.data == "volume_up":
            presentation.video.volume_up()
        elif form.action.data == "volume_down":
            presentation.video.volume_down()
        elif form.action.data == "jump_further":
            presentation.video.jump_further()
        elif form.action.data == "jump_back":
            presentation.video.jump_back()
    return redirect(url_for("presentation_video"))


"""
    Voip
"""


@app.route("/voip/control", methods=["POST"])
def voip_control():
    if not current_user.is_lecturer():
        flash("Zugriff nicht moeglich, bitte melden Sie sich an.", "danger")
        return redirect(url_for("index"))

    form = PresentationControlForm(request.form)
    presentation.stop()
    presentation.voip.start_voip(form.param.data)

    return redirect(url_for("index"))

"""
    Doc
"""


@app.route("/doc")
def doc():
    """
    Method for python flask, to set path for documentation landing page of the web frontend
    """
    return render_template("doc/doc_start.html")


@app.route("/doc/evince")
def doc_evince():
    """
    Method for python flask, to set path for evince documentation page of the web frontend
    """
    return render_template("doc/doc_evince.html")


@app.route("/doc/flask")
def doc_flask():
    """
    Method for python flask, to set path for flask documentation page of the web frontend
    """
    return render_template("doc/doc_flask.html")


@app.route("/doc/ipython")
def doc_ipython():
    """
    Method for python flask, to set path for ipython documentation page of the web frontend
    """
    return render_template("doc/doc_ipython.html")


@app.route("/doc/minipc")
def doc_minipc():
    """
    Method for python flask, to set path for mediabox documentation page of the web frontend
    """
    return render_template("doc/doc_minipc.html")


@app.route("/doc/vlc")
def doc_vlc():
    """
    Method for python flask, to set path for vlc documentation page of the web frontend
    """
    return render_template("doc/doc_vlc.html")


@app.route("/doc/vnc")
def doc_vnc():
    """
    Method for python flask, to set path for vnc documentation page of the web frontend
    """
    return render_template("doc/doc_vnc.html")


@app.route("/doc/vncclient")
def doc_vncclient():
    """
    Method for python flask, to set path for vnc client documentation page of the web frontend
    """
    return render_template("doc/doc_vncclient.html")


@app.route("/doc/vncserver")
def doc_vncserver():
    """
    Method for python flask, to set path for vnc server documentation page of the web frontend
    """
    return render_template("doc/doc_vncserver.html")


@app.route("/doc/webserver")
def doc_webserver():
    """
    Method for python flask, to set path for webserver documentation page of the web frontend
    """
    return render_template("doc/doc_webserver.html")


@app.route("/doc/reverse")
def doc_reverse():
    """
    Method for python flask, to set path for reverse vnc documentation page of the web frontend
    """
    return render_template("doc/doc_reverse.html")


"""
    Login / Logout / Session
"""


@app.before_request
def before_request():
    # check sessions
    user_database.process_sessions(current_user, presentation)

    # auto login user
    user = user_database.auto_login(current_user, request.remote_addr)
    if user is not None:
        login_user(user)


@app.route("/login", methods=["POST"])
def login():
    """
    Method for python flask, to set path for login page of the web frontend. handle login data with care,
    full control over mediabox
    """
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        if form.level.data == "lecturer":

            user = user_database.login_lecturer(form.username.data,
                                                form.password.data,
                                                request.remote_addr)
            if user is not None:
                login_user(user)
                flash("Login erfolgreich als Dozent", "success")
            else:
                flash("Login nicht erfolgreich als Dozent", "danger")

        elif form.level.data == "guest":
            user = user_database.login_guest(form.username.data,
                                             form.password.data,
                                             request.remote_addr)
            if user is not None:
                login_user(user)
                flash("Login erfolgreich als Gast", "success")
            else:
                flash("Login nicht erfolgreich als Gast", "danger")

    return redirect(url_for("index"))


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    """
    Method for flask login, to handle logout for the web frontend
    """
    # if the user was a lecturer stop all presentations
    if current_user.is_lecturer():
        presentation.stop()
    # logout the user
    user_database.logout_user(current_user.id)
    logout_user()
    flash("Logout erfolgreich", "success")
    return redirect(url_for("index"))


@login_manager.user_loader
def load_user(userid):
    """
    Method for flask login, to load user
    """
    return user_database.get(userid)

