"""
   This is a very simple Object relational mapper (ORM)
   Use this code for fun. It isn't tested on a lot of cases.

   Author: Juan Manuel García <jmg.utn@gmail.com>
"""


# -*- coding: utf-8 -*-

class DataBase(object):
    """
       A database agnostic from the engine that you're using.
       At this time implements MySQLdb, sqlite3, psycopg2 but it's easy
       to extend...
   """

    def __init__(self, provider, host='', user='', passwd='', db=''):
        """
           provider: The module for the database connection
               Ej: (MySQLdb, sqlite3, psycopg2)

           host: The Host on the database service is running

           user: user to connect to the database

           passwd: the password of the user

           db: the name of the database
       """

        self.provider = provider

        self.connections = {"MySQLdb": self.get_mysql_connection,
                            "sqlite3": self.get_sqlite_connection,
                            "psycopg2": self.get_postgre_connection, }

        self.connections[self.provider.__name__](host, user, passwd, db)
        self.cursor = self.db.cursor()

        self.providers = {"MySQLdb": self.get_mysql_columns,
                          "sqlite3": self.get_sqlite_columns,
                          "psycopg2": self.get_postgre_columns, }

    def get_mysql_connection(self, host='', user='', passwd='', db=''):
        """
           Get the connection for mysql databases
       """
        self.db = self.provider.connect(host=host, user=user, passwd=passwd, db=db)

    def get_postgre_connection(self, host='', user='', passwd='', db=''):
        """
           Get the connection for postgres databases
       """
        self.db = self.provider.connect(host=host, user=user, password=passwd, database=db)

    def get_sqlite_connection(self, host='', user='', passwd='', db=''):
        """
           Get the connection for sqlite databases
       """
        self.db = self.provider.connect(db)

    def get_mysql_columns(self, name):
        """
           Get the columns name information for mysql databases
       """
        self.sql_rows = 'Select * From %s' % name
        sql_columns = "describe %s" % name
        self.cursor.execute(sql_columns)
        return [row[0] for row in self.cursor.fetchall()]

    def get_sqlite_columns(self, name):
        """
           Get the columns name information for sqlite databases
       """
        self.sql_rows = 'Select * From %s' % name
        sql_columns = "PRAGMA table_info(%s)" % name
        self.cursor.execute(sql_columns)
        return [row[1] for row in self.cursor.fetchall()]

    def get_postgre_columns(self, name):
        """
           Get the columns name information for postgres databases
       """
        self.sql_rows = 'Select * From "%s"' % name
        sql_columns = """select column_name
                       from information_schema.columns
                       where table_name = '%s';""" % name
        self.cursor.execute(sql_columns)
        return [row[0] for row in self.cursor.fetchall()]

    def Table(self, name):
        """
           A queryable table of the database

           name: the name of the table to query

           return: a Query object
       """
        columns = self.providers[self.provider.__name__](name)
        return Query(self.cursor, self.sql_rows, columns, name)


class Query(object):
    """
       A query Class wich recursive generate the query-string
   """

    def __init__(self, cursor, sql_rows, columns, name):
        self.cursor = cursor
        self.sql_rows = sql_rows
        self.columns = columns
        self.name = name

    def filter(self, criteria):
        """
           Implement the "Where" statment of the standard sql
       """
        key_word = "AND" if "WHERE" in self.sql_rows else "WHERE"
        sql = self.sql_rows + " %s %s" % (key_word, criteria)
        return Query(self.cursor, sql, self.columns, self.name)

    def order_by(self, criteria):
        """
           Implement the "Order by" statment of the standard sql
       """
        return Query(self.cursor, self.sql_rows + " ORDER BY %s" % criteria, self.columns, self.name)

    def group_by(self, criteria):
        """
           Implement the "Group by" statment of the standard sql
       """
        return Query(self.cursor, self.sql_rows + " GROUP BY %s" % criteria, self.columns, self.name)

    def get_rows(self):
        """
           Execute the generated query on the database and return a list of Row Objects
       """
        print(self.sql_rows)
        self.cursor.execute(self.sql_rows)
        return [Row(zip(self.columns, fields), self.name) for fields in self.cursor.fetchall()]

    rows = property(get_rows)


class Row(object):
    """
       A row Class dynamically implemented for each table
   """

    def __init__(self, fields, table_name):
        """
           fields: A list of [column_name : value of column]

           table_name: the name of the table
       """
        # Assign the name of the current table to the class
        self.__class__.__name__ = table_name + "_Row"

        for name, value in fields:
            setattr(self, name, value)


# TODO https://speakerdeck.com/lig/your-own-orm-in-python-how-and-why