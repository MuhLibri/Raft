import random
import time
import threading

class Address:
    def __init__(self):
        self.t_min = 3000
        self.t_max = 5000
        self.t2 = 2000
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        
    def reset(self):
        with self._lock:
            self._stop_event.set()
            print("Reset")
    
    def countdown(self, timeout_min, timeout_max):
        while True:
            self._stop_event.clear()
            with self._lock:
                timeout = timeout_min + (timeout_max - timeout_min) * random.random()
            start_timer = time.time()
            while time.time() < start_timer + timeout / 1000:
                if self._stop_event.is_set():
                    break
                milis = (start_timer + timeout / 1000 - time.time()) * 1000
                secs, milis = divmod(milis, 1000)
                timer = '{:02d}:{:02d}'.format(int(secs), int(milis))
                print("Timeout:", timer)
                time.sleep(0.1)
            if not self._stop_event.is_set():
                break

    def start_countdown(self, timeout_countdown_min, timeout_countdown_max):
        self._thread = threading.Thread(target=self.countdown, args=(timeout_countdown_min, timeout_countdown_max))
        self._thread.start()

a = Address()
a.start_countdown(3000, 5000)
time.sleep(1)
a.reset()
time.sleep(2)
a.reset()
