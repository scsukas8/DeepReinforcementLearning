import json
import os
import copy
import random
import bottle
import time

from api import ping_response, start_response, move_response, end_response

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

from alpha_snake import Battlesnake


class App():

    def __init__(self):
        self.battlesnake = Battlesnake()

    def run(self):
        bottle.run(
            application,
            host=os.getenv('IP', '0.0.0.0'),
            port=os.getenv('PORT', '8080'),
            debug=os.getenv('DEBUG', True)
        )

    def index(self):
        return '''
        Battlesnake documentation can be found at
           <a href="https://docs.battlesnake.io">https://docs.battlesnake.io</a>.
        '''

    def static(path):
        """
        Given a path, return the static file located relative
        to the static folder.

        This can be used to return the snake head URL in an API response.
        """
        return bottle.static_file(path, root='static/')

    def ping(self):
        """
        A keep-alive endpoint used to prevent cloud application platforms,
        such as Heroku, from sleeping the application instance.
        """
        return ping_response()


    def start(self):
        data = bottle.request.json

        """
        TODO: If you intend to have a stateful snake AI,
                initialize your snake state here using the
                request's data if necessary.
        """
        print(json.dumps(data))
        
        self.battlesnake.start(data)
        print("Snek Started")
        action, _, _, _ =  self.battlesnake.act(data)


        color = "#342D7E"

        return start_response(color)


    def move(self):
        data = bottle.request.json

        """
        TODO: Using the data from the endpoint request object, your
                snake AI must choose a direction to move in.
        """
        print(json.dumps(data))

        directions = ['up', 'down', 'left', 'right']

        action, _, _, _ =  self.battlesnake.act(data)

        direction = directions[action]
        print(direction)

        return move_response(direction)


    def end(self):
        data = bottle.request.json

        """
        TODO: If your snake AI was stateful,
            clean up any stateful objects here.
        """
        print(json.dumps(data))

        return end_response()



# Expose WSGI app (so gunicorn can find it)
application = bottle.default_app()




if __name__ == '__main__':
    app = App()
    bottle.route('/')(app.index)
    bottle.route('/static/<path:path>')(app.static)
    bottle.post('/ping')(app.ping)
    bottle.post('/start')(app.start)
    bottle.post('/move')(app.move)
    bottle.post('/end')(app.end)
    app.run()
