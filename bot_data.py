db = None

def set_db(database):
    global db
    db = database

def get_db():
    return db