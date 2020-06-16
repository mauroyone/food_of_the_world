from app import create_app, db
from app.models import User, Country, Post


app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Country': Country, 'Post': Post}