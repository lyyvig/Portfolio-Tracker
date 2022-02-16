from datetime import datetime
import functools
from logging import Logger
import os
import traceback

def singleton(cls, *args, **kw):
    instances = {}
    def _singleton(*args, **kw):
        if cls not in instances:
                instances[cls] = cls(*args, **kw)
        return instances[cls]
    return _singleton

def log_error(file_name):

	def decorated(f):

		@functools.wraps(f)

		def wrapped(*args, **kwargs):
			try:
				return f(*args, **kwargs)

			except Exception as e:
				if file_name:
					try:
						a = open("logs/"+ file_name, "a")
					except FileNotFoundError:
						os.mkdir('logs')
						a = open("logs/"+ file_name, "a")
					except:
						pass
					time = datetime.now()
					a.write(time.isoformat())
					a.write("\n".join(traceback.format_exception(e)))
					for arg in args:
						try:
							a.write(arg.__dict__ + "   ")
						except:
							a.write(arg + "   ")
					a.write("\n" +str(kwargs))
					a.write("\n\n\n\n\n")
					a.close()

		return wrapped

	return decorated
