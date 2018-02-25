import sqlite3


class DataBaseConnector(object):
	def __init__(self, db_name, user=None, password=None):
		super(DataBaseConnector, self).__init__()
		self.db_name = db_name
		self.user = user
		self.password = password

	def get_connection(self):
		con = sqlite3.connect(self.db_name)
		return con



