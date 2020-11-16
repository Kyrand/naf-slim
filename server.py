from flask import Flask, request, render_template, send_from_directory
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__, static_url_path='/examples', static_folder='examples')
# CORS(app)

app.config['SECRET_KEY'] = 'secret!'
app.config['EXAMPLES_STATIC_PATH'] = 'examples/'
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}
cur_room = None

# @app.route('/', defaults={'file': 'index.html'})
# @app.route('/<path:file>')
# @app.route('/examples/<path:file>')
# def serve_results(file):
#     app.logger.info(file)
#     # Haven't used the secure way to send files yet
#     return send_from_directory(app.config['EXAMPLES_STATIC_PATH'], file)


@socketio.on('joinRoom')
def on_join(data):
    global cur_room
    global rooms

    room = data['room']
    app.logger.info(f"room: {room}")

    if not rooms.get(room):
        rooms[room] = {
            'name': room,
            'occupants': {},
        }

    joined_time = str(datetime.now())
    rooms[room]['occupants'][request.sid] = joined_time;
    cur_room = room

    app.logger.info(f'{request.sid} joined room {room}')
    join_room(room)

    emit("connectSuccess", { 'joinedTime': joined_time })
    occupants = rooms[room]['occupants']

    emit("occupantsChanged", {'occupants': occupants}, room=cur_room)


@socketio.on('send')
def on_send(data):
    app.logger.info("Sending: " + str(data))
    socketio.emit("send", data, room=data["to"])


@socketio.on('broadcast')
def on_broadcast(data):
    app.logger.info("Broadcasting: " + str(data))
    emit("send", data, broadcast=True)


@socketio.on('disconnect')
def on_disconnect():
    global rooms
    sid = request.sid
    app.logger.info(f'disconnected, id:{sid} room:{cur_room}' )
    if rooms.get(cur_room):
        app.logger.info(f'user disconnected, id: {sid}' )
        rooms[cur_room]['occupants'].pop(sid)
        occupants = rooms[cur_room]['occupants']
        emit("occupantsChanged", {'occupants': occupants}, room=cur_room, broadcast=True)
        app.logger.info(f'current occupants: {occupants}')

        if len(occupants) == 0:
            app.logger.info('everybody left the room')
            try:
                rooms.pop(cur_room)
            except KeyError:
                app.logger.info(f'Room {cur_room} already closed')


if __name__ == '__main__':
    socketio.run(app, debug=True, port=8080)
