# def delay(delay):
#     def decorate(func):
#         func.tick = 0
#         def wait_function(*args, **kwargs):
#             tock = time.time()
#             if tock - func.tick >= max_wait:
#                 func.tick = tock
#                 return func(*args, **kwargs)
#             else:
#                 return
#         return wait_function
#     return decorate

def none_iter(iterable):
    """
    turns an iterable data structure into an iter where the last .next()
    returns None
    """
    yield from iterable
    yield None

# def min_wait_between_calls
def lagged_repeat(max_wait=1/3):
    """
    max_frequency(hz):
    sets a maximum frequency (hz) a function can be run
    
    """
    def decorate(func):
        
        def wait_function(*args, **kwargs):
            tock = time.time()
            
            if tock - wait_function.tick >= wait_function.max_wait:
                wait_function.tick = tock
                return func(*args, **kwargs)
            
            else:
                return None
            
        return wait_function
    
        wait_function.min_wait = max_wait
        wait_function.tick = 0
        
    return decorate

#def make_me_blink
def blinker(on_time=.5, off_time=.5):
    """
    blinker(period, duty_cycle)
    sets when a function when and won't respond to a call
    """
    def decorate(func):

        def blink_fun(*args, **kwargs):
            tock = time.time()
            
            if blink_fun.on is True:
                
                if tock - blink_fun.tick > blink_fun.on_time:
                    blink_fun.on = False
                    blink_fun.tick = time.time()
                    
                return func(*args, *kwargs)
            
            else:
                
                if tock - blink_fun.tick > blink_fun.off_time:
                    blink_fun.on = True
                    blink_fun.tick = time.time()
                    
                return None
            
        blink_fun.on_time = on_time
        blink_fun.off_time = off_time
        blink_fun.tick = time.time()
        blink_fun.on = True
        
        return blink_fun
    
    return decorate

#count_my_frequency
def frequency_tracker():
    """
    count the frequency of executions per second
    """
    pass

#time_for_last_execution()

class UpDownCounter:
    
    def __init__(self, mini=0, maxi=255, step=1):
        self.mini = mini
        self.maxi = maxi
        self.i = 0
        self.forward = True
        self.step = 1
        
    def get_next(self):
        
        if self.i < self.maxi and self.forward is True:
            self.i = min(self.i + self.step, self.maxi)
            if self.i == 255:
                self.forward = False
                
        else:
            self.i = max(self.i - self.step, self.mini)
            if self.i == self.mini:
                self.forward = True
                
        return self.i