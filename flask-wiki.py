# FIXME: DOCUMENTATION
from json import load, dumps
from passlib.hash import sha256_crypt

import os
import shutil
import time

from flask import Flask, session, flash, request, render_template, redirect, url_for, abort, g

app = Flask(__name__)
app.template_folder = app.root_path + '/system/templates/'
app.config.update(
    DEBUG=True,
    SECRET_KEY='Every pony is the best pony!',
    SESSION_COOKIE_NAME='library',
    SITE_TITLE='Flask Wiki',
    USERS_PATH=app.root_path + '/system/users/',
    PAGES_PATH=app.static_folder + '/pages/',
    DUMPS_PATH=app.static_folder + '/dumps/',
)

@app.route('/')
def main():
    return render_template('main.html', content='<h1>This is main page!</h1>')


@app.route('/login/', methods=['POST', 'GET'])
def login():  # TODO: error handling
    # FIXME: DOCUMENTATION
    if 'username' in session:
        flash('You are already logged in!', 'info')  #
        return redirect(url_for('main'))             # FIXME: decorate this!
    if request.method == 'POST':
        # TODO: add input check
        username = request.form.get('username', None)
        password = request.form.get('password', None)
        app.logger.debug(request.form['username'])
        try:
            user_file = open(app.config['USERS_PATH'] + username, 'r')  # user_file on json format
            user_conf = load(user_file)
            user_file.close()
            if not sha256_crypt.verify(password, user_conf['password']):
                flash('Wrong password!', 'error')
                return redirect(url_for('login'))
            else:
                flash('You successfully logged in!', 'info')
                session['username'] = request.form['username']
        except FileNotFoundError:
            flash('User not exist!', 'error')
            return redirect(url_for('login'))
        except Exception:
            abort(500)
        return redirect(request.args.get('next', url_for('main')))

    return render_template('login.html')


@app.route('/reg/', methods=['POST', 'GET'])
def reg():  # TODO: error handling
    # FIXME: DOCUMENTATION
    if 'username' in session:                        #
        flash('You are already logged in!', 'info')  # FIXME: decorate this!
        return redirect(url_for('main'))             #
    if request.method == 'POST':
        # TODO: add input check
        username = request.form.get('username', None)
        password = request.form.get('password', None)
        password = sha256_crypt.encrypt(password)
        try:
            user_file = open(app.config['USERS_PATH'] + username, 'x')
            user_file.write(dumps({'password': password}))
            user_file.close()
            flash('Success!', 'info')
            return redirect(url_for('main'))
        except FileExistsError:
            flash('User exist!', 'error')
        except OSError:
            flash('Registration failed!', 'error')
    return render_template('reg.html')


@app.route('/logout/')
def logout():
    # FIXME: DOCUMENTATION
    if 'username' in session:
        session.pop('username', None)
        flash('You successfully logged out!', 'info')
        return redirect(url_for('main'))
    flash('You are not logged in!', 'error')
    return redirect(url_for('main'))


@app.route('/page/<page_name>')
def page(page_name):
    """ Render page with content from page file """
    if '@' in page_name:  # check for stamp file
        page_path = app.config['DUMPS_PATH'] + page_name
    else:
        page_path = app.config['PAGES_PATH'] + page_name
    try:
        page_file = open(page_path, 'r')
        content = page_file.read()
        page_file.close()
        return render_template('page.html', context={'title': page_name, 'content': content})
    except FileNotFoundError:
        abort(404)
    except Exception:
        abort(500)


@app.route('/write/', methods=['POST', 'GET'])
def write():  # TODO: error handling
    # FIXME: DOCUMENTATION
    if 'username' not in session:         #
        g.login_back = request.path       #
        abort(403)                        # FIXME: decorate this!
    if request.method == 'POST':
        # TODO: add input check
        page_name = request.form.get('title')
        content = request.form.get('content')
        create = request.form.get('create', '0')
        page_file = app.config['PAGES_PATH'] + page_name
        if create == '1' and os.path.isfile(page_file):
            flash('Page already exist with same name!', 'error')
        else:
            try:
                if create != '1':
                    dump_page(page_name)
                page_file = open(page_file, 'w')
                page_file.write(content)
                page_file.close()
                flash('Success!', 'info')
                return redirect(url_for('page', page_name=page_name))
            except OSError:
                flash('Error writing to file!', 'error')

    return render_template('editor.html', context={})


@app.route('/write/<page_name>', methods=['POST', 'GET'])
def edit(page_name):  # TODO: error handling
    # FIXME: DOCUMENTATION
    content = ''
    page_file = app.config['PAGES_PATH'] + page_name
    try:
        page_file = open(page_file, 'r')
        content = page_file.read()
        page_file.close()
    except OSError:
        abort(404)
    return render_template('editor.html', context={'title': page_name, 'content': content})


@app.route('/delete/', methods=['POST', 'GET'])
def delete_page():
    # FIXME: DOCUMENTATION
    if 'username' not in session:         #
        g.login_back = request.path       #
        abort(403)                        # FIXME: decorate this!
    if request.method == 'POST':
        try:
            page_name = request.form.get('title')
            dump_page(page_name)
            os.remove(app.config['PAGES_PATH'] + page_name)
            flash('Success!', 'info')
        except OSError:
            flash('That page does not exist!', 'error')
    return redirect(url_for('main'))


@app.route('/restore/', methods=['POST'])
def restore():  # TODO: test this
    # FIXME: DOCUMENTATION
    if 'username' not in session:         #
        g.login_back = request.path       #
        abort(403)                        # FIXME: decorate this!
    page_name = request.form.get('title')
    timestamp = request.form.get('time')
    page_file = app.config['PAGES_PATH'] + page_name
    dump_file = app.config['DUMPS_PATH'] + page_name + '@' + timestamp
    try:
        shutil.copyfile(dump_file, page_file)
        flash('Success!', 'info')
    except OSError:
        flash('Can not restore this page!', 'error')
    return redirect(url_for('main'))


def dump_page(page_name):  # FIXME
    """ Backup current page to <dumps_path> directory """
    dumps_list = show_dumps(page_name)
    print(dumps_list)
    if len(dumps_list) > 9:
        os.remove(app.config['DUMPS_PATH'] + page_name + '@' + dumps_list[0])
    page_file = app.config['PAGES_PATH'] + page_name
    stamp_file = app.config['DUMPS_PATH'] + page_name + '@' + str(int(time.time()))
    shutil.copyfile(page_file, stamp_file)


def show_dumps(page_name):  # TODO: test this
    dumps_list = []
    for root, dirs, files in os.walk(app.config['DUMPS_PATH']):
        for dump_name in files:
            dump_name = dump_name.split('@')
            if page_name in dump_name:
                dumps_list.append(dump_name[1])  # timestamp
    return sorted(dumps_list)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(403)
def access_denied(error):
    return render_template('403.html'), 403


@app.errorhandler(500)
def something_wrong(error):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run()
