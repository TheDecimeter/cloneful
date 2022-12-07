import os
basedir = os.path.abspath(os.path.dirname(__file__))

print("start")
print(basedir)
print(os.path.join(basedir, 'app.db'))
print(os.environ.get('SQLALCHEMY_DATABASE_URI ') or \
        'postgresql :///' + os.path.join(basedir, 'app.db'))
print("done")