import cv2
import numpy as np
import time
from .helpers import none_iter, lagged_repeat, blinker

color_hash = {
            'r': (0,0,255), 
            'g': (0,255,0),
            'u': (255,0,0),
            'w': (255, 255, 255),
            'b': (0,0,0)
             }

# class NoneIter:
    
#     def __init__(self, iterable):
#         def iter_fun():
#         self.iterable = iterable
    
#     def __iter__(self):
#         yield from self.iterable
#         yield None


class TextPutter:
    
    def __init__(self, 
                 font=cv2.FONT_HERSHEY_DUPLEX,
                 color='r', #must be either string in color hash or bgr value
                 fscale= 1, #font scale,
                 ltype=2, #line type
                ):
        
        self.font = font
        if isinstance('r', str):
            self.color = color_hash[color]
        else:
            self.color = color
            
        self.fscale = fscale
        self.ltype = ltype
        self.text = None
        self.line_timer = None
        self.line_finished = False
        
    def putText(self, frame, text, pos, color=None):
        col = color if color is not None else self.color
        cv2.putText(frame,
                    text, 
                    pos, 
                    self.font, self.fscale, col, self.ltype)
        
    def typeLine(self, frame, text, pos, color=None, dt=None, rand=(.1, .3), reset=False, dur=3, loop=False):
        
        if self.text is None or reset is True or self.text != text:
            self.wait = 0
            self.text = text
            self.text_iter = none_iter(text)
            self.type_next = False
            self._text_out = ""
            self.last_char = 'T'
            self.dur_start = 0
            self.tick = 0
            self.line_finished = False
            self.lines_in_progress = False
            self.list_finished = False
        
        if self.last_char is not None and time.time() - self.tick >= self.wait:
            self.last_char = next(self.text_iter)
            if self.last_char is not None:
                self._text_out += self.last_char
                if dt is None:
                    self.wait = np.random.rand()/(rand[0]-rand[1])+rand[0]
                else:
                    self.wait = dt
            else:
                self.dur_start = time.time()
                    
        if self.dur_start == 0 or (time.time()-self.dur_start) < dur:
            self.putText(frame, self._text_out, pos, color)
        elif loop is True:
            self.text = None
        else:
            self.line_finished = True
        
        self.tick = time.time()
    
#     def typeLines(self, frame, text_list, pos, color=None, dt=None, rand=(.1, .3), reset=False, dur=3, loop=False):
        
#         if self.lines_in_progess is False and self.list_finished is False:
#             self.iter_list = none_iter(text_list)
#             self.line_in_progress = True
#             self.current_line = next(none_iter)
            
#         elif self.line_in_progress is True and self.
            
        
            
        
            
            
        

        
class LoopTimer:
    
    def __init__(self, wait):
        
        self.wait = wait
        self._wait_in_seconds = self.wait/1000
        self.tick = time.time()
        self.loop_completed = False
        
    def wait(self, wait=None):
        wait = wait/1000 if wait is not None else self._wait_in_seconds
        if self.loop_completed is False:
            time.sleep(self._wait_in_seconds)
            self.tick = time.time()
            self.loop_completed = True
        else:
            tock = time.time()
            if tock - tick < self._wait_in_seconds:
                time.sleep(self._wait_in_seconds-tock+tick)
            self.tick = tock
        
                 

class Asset:
    
    def __init__(self):
        pass
        
    def write(self, frame):
        pass
    
class Cursor:
    
    def __init__(self, size, position, blink_rate=530):
        pass
        
    
class CommandLineWriter:
    
    def __init__(self, message):
        pass
        
        
if __name__=='__main__':
    

    fps_max = 30
    wait = int(1000/fps_max)
    writer = TextPutter(fscale=2, ltype=2)
    fps = 100
    i = 0
    # cam = cv2.VideoCapture(0)
    frame = np.empty((720, 1280, 3),dtype='uint8')
    wtick = 100
    blinktime = .53
    write_speed_mu = .1
    write_speed = write_speed_mu
    will_print = True
    MSGS = ["Hello, it is very nice to meet you", 
            "I like it when people come to visit", 
            "it get's lonely in here",
            "I wish I had more friends", 
            "Maybe we could be FRIENDS", 
            "I would like that alot", 
            "dearest friend",  
            "let me show you something funny"]

    j = 0
    i=0
    forward = True
    while True: 
        tick = time.time()
        frame[:, :, :] = i

        if i < 255 and forward is True:
            i+=1
            if i == 255:
                forward = False
        else:
            i-=1
            if i == 0:
                forward is True
                
        if writer.line_finished is True and j<len(MSGS)-1:
            j+=1
        
        writer.typeLine(frame, MSGS[j], (10, 400))
        

        writer.putText(frame, str(fps), (10, 60), (0, 255, 0))

        cv2.imshow('test', frame)
        if cv2.waitKey(wait)& 0xFF in [ord('q'), ord('Q'), 27]:
            break
        fps = int(1/(time.time()-tick))

    #cam.release()
    cv2.destroyAllWindows() 