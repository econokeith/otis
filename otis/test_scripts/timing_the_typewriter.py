import queue
import signal
import sys
import time
import cv2
import numpy as np

from otis.helpers import multitools, cvtools, coordtools, colortools, timers
from otis.overlay import scenes, imageassets, assetholders, textwriters, shapes

waits = [0, 0, 0, 0]
OTIS_SCRIPT= [ ("Hello Keith, I am O.T.I.S, I heard that mean lady stole your best friend the cat.", waits[0]),
               ("I know I am a computer and not a cat, but can a cat make all these little bouncy Keith's on the screen?!?", waits[1]),
               ("Plus, I promise I will not poop in your bathroom sink or walk on your keyboard while you are using it.",waits[2]),
               ("Although, that is mostly because computers do not poop nor do we have feet...", waits[3])
        ]

key_waits = [.035, .0345, .0351, .034]
key_wait = .03475
otis = textwriters.TypeWriter(coords=(0, 20),
                              ref='cb',
                              jtype='l',
                              anchor_point='cb',
                              scale=1.5,
                              max_line_length=1080 - 100,
                              one_border=True,
                              thickness=2,
                              border_spacing=(.5, .5),
                              max_lines=3,
                              loop=False,
                              color='g',
                              transparent_background=.1,
                              perma_border=True,
                              key_wait_range=.03475
                              )

black_screen = np.zeros((1080, 1080, 3), dtype='uint8')
the_script = queue.Queue()
fps_sleeper = timers.SmartSleeper()

i = 0
for line in OTIS_SCRIPT:
    the_script.put(line)

if __name__=='__main__':

    line_timer = timers.TimeSinceFirst().start()
    total_timer = timers.TimeSinceFirst().start()
    while True:
        black_screen[:, :, :] = 0

        otis.write(black_screen)
        fps_sleeper()
        cv2.imshow('otis', black_screen)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if otis.text_complete is True and the_script.empty() is False:
            print(round(line_timer(), 2))
            new_line = the_script.get()
            otis.text = new_line
            line_timer.reset(True)
            otis.key_wait_range = key_waits[i]
            i+=1


        if otis.text_complete is True and the_script.empty() is True:
            print(round(line_timer(), 2))
            break

        fps_sleeper()
    print(round(total_timer(), 2))
    cv2.destroyAllWindows()