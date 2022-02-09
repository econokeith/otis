import numpy as np
from collections import defaultdict

with open('robocam/otismeetsguydebord/log.log') as log:
    scores = []
    whose = []
    for line in log:
        _last = line.split(':')[-1]
        _last = _last.split(',')
        last = [l.strip(' \n') for l in _last]
        whose.append(last[0])
        scores.append(last[1:])

who = np.array(whose, dtype=int)
scores = np.array(scores, dtype=float)
import robocam.helpers.timers as timers

fun = lambda: [timers.TimeSinceFirst().start(), 0]
hd = defaultdict(fun)