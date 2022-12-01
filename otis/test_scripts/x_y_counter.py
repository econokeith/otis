from otis.helpers import timers

class TimedRectangleCycle(timers.Timer):

    def __init__(self,  x_range, y_range, cycle_t, repeat=True):
        self.x_min, self.x_max = x_range
        self.y_min, self.y_max = y_range

        self.x_dist =  x_dist = (x_range[1]-x_range[0] + 1 )
        self.y_dist =  y_dist =  (y_range[1]-y_range[0]+1)
        self.total_distance = 2*(self.x_dist + self.y_dist)
        self.speed = self.total_distance / cycle_t
        self.counter = timers.TimedCycle(min_i=0, max_i = self.total_distance - 1, cycle_t=cycle_t, repeat=repeat)

        self.c0 = x_dist
        self.c1 = x_dist + y_dist
        self.c2 = 2*x_dist + y_dist

    def __call__(self):

        i = self.counter()
        if i < self.c0:
            self.side = 0
            return (self.x_min + i, self.y_min)
        elif i < self.c1:
            self.side = 1
            return (self.x_max, self.y_min + (i-self.c0))
        elif i < self.c2:
            self.side = 2
            return (self.x_max - (i-self.c1), self.y_max)
        else:
            self.side = 3
            return (self.x_min, self.y_max - (i-self.c2))


if __name__=='__main__':
    import time
    sleeper = timers.SmartSleeper(.1)
    counter =TimedRectangleCycle((1, 10), (1, 10), 2)
    for _ in range(80):
        print(counter(), f"-{counter.side}")
        sleeper()






