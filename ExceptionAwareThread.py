import threading
import traceback
from Debug import Debug


class ExceptionAwareThread(threading.Thread):

    def run(self):
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
            else:
                self.try_run()
        except:
            ex = traceback.format_exc()
            Debug.dump(ex)
