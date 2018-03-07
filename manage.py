from flask_script import Manager
from database import Database
from server import app
from bot import run_bot

manager = Manager(app)

@manager.command
def bot():
    """
    Clean database & run scrapbot
    """
    restore()
    run_bot()

@manager.command
def restore():
    """
    Clean database
    """
    database = Database()
    database.connect()
    database.drop()
    database.close()

if __name__ == "__main__":
    manager.run()
