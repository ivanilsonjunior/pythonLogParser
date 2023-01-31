import sys
import os
from subprocess import CalledProcessError, Popen, PIPE, STDOUT


'''
Based on run-cooja.py
'''
class Runner:
    def __init__(self, simFile, useJar=False):    
        # get the path of this example
        self.useJar = useJar
        self.SELF_PATH = os.getcwd()
        # move three levels up
        self.CONTIKI_PATH = os.path.dirname(os.path.dirname(self.SELF_PATH))
        self.COOJA_PATH = os.path.normpath(os.path.join(self.CONTIKI_PATH, "tools", "cooja"))
        if self.useJar:
            self.cooja_jar = os.path.normpath(os.path.join(self.CONTIKI_PATH, "tools", "cooja", "build", "libs", "cooja-full.jar"))
        self.cooja_input = simFile
        self.cooja_output = "COOJA.testlog"

    #######################################################
    # Run a child process and get its output

    def run_subprocess(self, args, input_string):
        retcode = -1
        stdoutdata = '\n'
        try:
            proc = Popen(args, stdout = PIPE, stderr = STDOUT, stdin = PIPE, shell = True)
            #proc = Popen(args, stdout = self.cooja_output, stderr = STDOUT, stdin = PIPE, shell = True)
            (stdoutdata, stderrdata) = proc.communicate(input_string)
            if not stdoutdata:
                stdoutdata = '\n'
            if stderrdata:
                stdoutdata += stderrdata
            retcode = proc.returncode
        except OSError as e:
            sys.stderr.write("run_subprocess OSError:" + str(e))
        except CalledProcessError as e:
            sys.stderr.write("run_subprocess CalledProcessError:" + str(e))
            retcode = e.returncode
        except Exception as e:
            sys.stderr.write("run_subprocess exception:" + str(e))
        finally:
            return (retcode, stdoutdata)

    #############################################################
    # Run a single instance of Cooja on a given simulation script

    def execute_test(self, cooja_file):
        # cleanup
        try:
            os.rm(self.cooja_output)
        except:
            pass
        filename = os.path.join(self.SELF_PATH, cooja_file)
        if self.useJar:
            args = " ".join(["java -Djava.awt.headless=true -jar ", self.cooja_jar, "-nogui=" + filename, "-contiki=" + self.CONTIKI_PATH, "--logname=COOJA.log"])
        else:
            args = " ".join([self.COOJA_PATH + "/gradlew run --no-watch-fs --parallel --build-cache -p", self.COOJA_PATH, "--args='-nogui=" + filename, "-contiki=" + self.CONTIKI_PATH, "-logdir=" + self.SELF_PATH, "--logname=COOJA.log" + "'"])
        sys.stdout.write("  Running Cooja, args={}\n".format(args))

        (retcode, output) = self.run_subprocess(args, '')
        if retcode != 0:
            sys.stderr.write("Failed, retcode=" + str(retcode) + ", output:")
            sys.stderr.write(output)
            return False

        sys.stdout.write("  Checking for output...")

        is_done = False
        with open(self.cooja_output, "r") as f:
            for line in f.readlines():
                line = line.strip()
                if line == "TEST OK":
                    sys.stdout.write(" done.\n")
                    is_done = True
                    continue

        if not is_done:
            sys.stdout.write("  test failed.\n")
            return False

        sys.stdout.write(" test done\n")
        return True

    #######################################################
    # Run the application

    def run(self):
        if self.useJar:
            if not os.access(self.cooja_jar, os.R_OK):
                print('The file "{}" does not exist, trying to build cooja-full.jar !'.format(self.cooja_jar))
                proc = Popen(self.COOJA_PATH + "/gradlew fulljar", shell=True)

        input_file = self.cooja_input

        if not os.access(input_file, os.R_OK):
            print('Simulation script "{}" does not exist'.format(input_file))
            return (-1)

        print('Using simulation script "{}"'.format(input_file))
        if not self.execute_test(input_file):
            return (-1)

#######################################################

#if __name__ == '__main__':
#    main()
