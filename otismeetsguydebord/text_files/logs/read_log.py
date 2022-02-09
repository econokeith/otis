import numpy as np

with open('robocam/otismeetsguydebord/log.log') as log:
    who = []
    scores = []
    for line in log:
        last = line.split(':')[-1]
        which, _score = last.split('/')
        who.append(int(which))
        score = []
        for v in _score[1:-2].split(' '):
            if v != '':
                score.append(float(v))
        scores.append(score)

    who = np.array(who)
    scores = np.array(scores)