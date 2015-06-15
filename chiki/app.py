# coding: utf-8
import os
from flask import Blueprint, current_app, Response, render_template
from flask import abort, request, redirect
from flask.ext.babelex import Babel
from .jinja import init_jinja
from .logger import init_logger
from .settings import TEMPLATE_ROOT
from ._flask import Flask

__all__ = [
	"init_app", 'init_api', "init_admin",
]


def init_babel(app):
	""" 初始化语言本地化 """

	babel = Babel(app)

	@babel.localeselector
	def get_locale():
		return 'zh_Hans_CN'


def init_error_handler(app):
	""" 错误处理 """

	@app.errorhandler(403)
	def error_403(error):
		return render_template('403.html'), 403

	@app.errorhandler(404)
	def error_404(error):
		return render_template('404.html'), 404

	@app.errorhandler(500)
	def error_500(error):
		return render_template('500.html'), 500


def before_request():
	""" Admin 权限验证 """

	auth = request.authorization
	username = current_app.config.get('ADMIN_USERNAME')
	password = current_app.config.get('ADMIN_PASSWORD')
	if username and not (auth 
			and auth.username == username 
			and auth.password == password):
		return Response(u'请登陆', 401, {'WWW-Authenticate': 'Basic realm="login"'})


def init_app(init, config=None, pyfile=None, 
		template_folder='templates', index=False, error=True):
	""" 创建应用 """

	app = Flask(__name__, template_folder=template_folder)
	if config: app.config.from_object(config)
	if pyfile: app.config.from_pyfile(pyfile)

	ENVVAR = app.config.get('ENVVAR')
	if ENVVAR and os.environ.get(ENVVAR): 
		app.config.from_envvar(app.config['ENVVAR'])

	app.static_folder = app.config.get('STATIC_FOLDER')
		
	init(app)
	init_babel(app)
	init_jinja(app)
	init_logger(app)

	if error:
		init_error_handler(app)

	if index:
		@app.route('/')
		def index():
			return redirect(app.config.get('INDEX_REDIRECT'))

	return app


def init_api(init, config=None, pyfile=None, 
		template_folder='templates', index=False, error=False):
	return init_app(init, config, pyfile, template_folder, index, error)


def init_admin(init, config=None, pyfile=None, 
		template_folder='templates', index=True, error=True):
	""" 创建后台管理应用 """

	app = init_app(init, config, pyfile, template_folder, index, error)

	@app.before_request
	def _before_request():
		return before_request()

	blueprint = Blueprint('xadmin', __name__, 
		template_folder=TEMPLATE_ROOT)
	app.register_blueprint(blueprint)

	return app