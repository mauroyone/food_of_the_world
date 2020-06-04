from app import app, db
from app.models import User, Countries

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Countries': Countries}