import os
import subprocess
import time


class Debug:

    @staticmethod
    def dump(exception):
        if os.uname()[4] == 'x86_64':
            print(exception)
        else:
            ts = int(time.time())
            os.system("sudo datamount")

            print(exception)
            with open("/data/exception-{}.log".format(ts), "w") as log_file:
                log_file.write(exception)

            journal = subprocess.Popen(['journalctl', '-u', 'infotainment'], stdout=subprocess.PIPE).stdout.read()
            with open("/data/journal-{}.log".format(ts), "wb") as log_file:
                log_file.write(journal)

            os.system("sudo dataumount")

        exit(1)
