from app import app, db
from app.models import User, Market, Transactions, Offer

if __name__ == '__main__':
    app.run(debug=True, port=50052)  # josef (depot) 50050, andi (firmen) 50051


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Market': Market}
