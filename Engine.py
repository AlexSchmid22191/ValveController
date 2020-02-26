from functools import wraps
from threading import Thread, Lock

from pubsub.pub import subscribe, sendMessage
from serial import Serial, SerialException


def in_new_thread(target_func):
    @wraps(target_func)
    def wrapper(*args, **kwargs):
        com_thread = Thread(target=target_func, args=args, kwargs=kwargs)
        com_thread.start()
    return wrapper


class Valvolino(Serial):
    """Driver class for Ventolino MFC controllers, uses Pubsub to communicate with GUI"""
    def __init__(self, port=None, channels=4, timeout=1):
        super().__init__(port, timeout=timeout)
        self.port = port
        self.channels = channels

        self.com_lock = Lock()

        self.state_array = [False]*channels

        subscribe(self.connect, 'GTE_connect')
        subscribe(self.disconnect, 'GTE_disconnect')
        subscribe(self.toggle_valve, 'GTE_toggle_valve')
        subscribe(self.read_all_channels, 'GTE_request_valve_state')

    def connect(self, port=None):
        """Connect to serial port, emmit success/error message"""
        if port:
            self.port = port
        try:
            self.open()
            sendMessage(topicName='ETG_status', text='Valvolino connected')
        except SerialException:
            sendMessage(topicName='ETG_status', text='Serial connection error')

    def disconnect(self):
        with self.com_lock:
            self.close()
            sendMessage(topicName='ETG_status', text='Valvolino disconnected')

    @in_new_thread
    def toggle_valve(self, channel):
        """Toggle a valve"""

        assert 1 <= channel <= self.channels, 'Invalid channel'

        self.state_array[channel-1] = not self.state_array[channel-1]
        string = '{:02d}SSP{:1d}'.format(channel, self.state_array[channel - 1])

        with self.com_lock:
            try:
                self.write(b'\x02')
                self.write(string.encode())
                self.write(b'\x0D')

                answer = self.readline()
                if answer == b'OK\n':
                    sendMessage('ETG_status', text='Valve {:1d} toggled!'.format(channel))
                else:
                    sendMessage('ETG_status', text='Valvolino not answering')

            except (ValueError, SerialException):
                sendMessage(topicName='ETG_status', text='Serial communication error!')

    @in_new_thread
    def read_valve_state(self, channel):
        """Read state of a valve"""
        assert 1 <= channel <= self.channels, 'Invalid channel'

        string = '{:02d}RSP'.format(channel)

        with self.com_lock:
            try:
                self.write(b'\x02')
                self.write(string.encode())
                self.write(b'\x0D')

                answer = self.readline()
                self.state_array[channel - 1] = bool(int(answer.decode()))
                sendMessage(topicName='ETG_answer_valve_state', channel=channel, state=self.state_array[channel - 1])

            except (ValueError, SerialException):
                sendMessage(topicName='ETG_status', text='Serial communication error!')

    def read_all_channels(self):
        for channel in range(self.channels):
            self.read_valve_state(channel + 1)
