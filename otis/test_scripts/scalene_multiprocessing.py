from multiprocessing import Process
import time

def target():
    try:
        import queue
        print('queue is good')
    except:
        print('could not import queue')
    try:
        import face_recognition
        print('face_recognition is good')
    except:
        print('could not import face_recognition')

    try:
        import numpy
        print('numpy is good')
    except:
        print('could not import numpy')

    print('done')


process = Process(target=target)
process.start()
process.join()