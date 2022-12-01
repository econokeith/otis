import queue
import signal
import sys
import time
import cv2
import numpy as np


from otis.helpers import multitools, cvtools, coordtools, colortools
from otis.overlay import scenes, writergroups, shapes, boundingobjects, textwriters, imageassets, assetmover, \
    typewriters
from otis.helpers import shapefunctions, timers
from otis.overlay.assetmover import AssetMover


MAX_KEYS_PER_SECOND = 10

OTIS_SCRIPT = [
    ("Keith, I heard that mean lady stole your best friend, the cat.", 1),
    ("I know I'm not a cat, but I can do things a cat can't do like make all these bouncy you's!", 1),
    ("Plus, I promise I won't poop in your bathroom sink or walk on your keyboard... ", 1),
    ("... because both of things are physically impossible", 1)
    ]


def target(shared, pargs):
    signal.signal(signal.SIGTERM, multitools.close_gracefully)
    signal.signal(signal.SIGINT, multitools.close_gracefully)
    pargs.record = False

    ####################################### SETUP #####################################################################

    manager = scenes.SceneManager(shared, pargs, file=__file__)
    capture = manager.capture  # for convenience
    # setup bounding manager
    color_cycle = colortools.ColorCycle()  # so boxes have different colors
    # base_function
    base_bounding_shape = shapes.Circle(color=None,
                                        radius_type='diag',
                                        thickness=2,
                                        ltype=2
                                        )
    # it's easier define the box_fun as an input to the BoundingManager when you have a more complex setup
    new_bounder_function = lambda: boundingobjects.BoundingAsset(asset=base_bounding_shape,
                                                                 moving_average=(None, None, 100, 100),
                                                                 scale=1.25,
                                                                 stabilizer=.01,
                                                                 color='g',
                                                                 name_tag_outliner='border',
                                                                 name_tag_inverted=False,

                                                                 )
    #
    box_manager = boundingobjects.BoundingManager(manager,
                                                  box_fun=new_bounder_function,
                                                  )

    # both are adhoc effects managers defined below
    mirror = MirrorEffects(manager)
    sprinkler = BallSprinkler(manager, frame_portion_scale=1.1)

    # set up info writers to monitor import variables while this runs
    # they toggle on and off by hitting '1' on the keyboard

    info_group = writergroups.BasicInfoGroup((10, 40), manager) # fps, model update, resolution
    extra_writers = [
        textwriters.InfoWriter(text_fun=lambda: f'n_faces= {shared.n_observed_faces.value}', coords=(50, -200)),
        textwriters.InfoWriter(text_fun=lambda: f'a_faces= {box_manager.active_names}', coords=(50, -250)),
        textwriters.InfoWriter(text_fun=lambda: f'primary= {box_manager.primary_target}', coords=(50, -300)),
        textwriters.InfoWriter(text_fun=lambda: f'target = {shared.servo_target}', coords=(50, -350)),
        textwriters.InfoWriter(text_fun=lambda: f'key_input= {shared.keyboard_input.value}', coords=(50, -400)),
        textwriters.InfoWriter(text_fun=lambda: f'n_bouncers= {sprinkler.movement_manager.n}', coords=(50, -450)),
        textwriters.InfoWriter(text_fun=lambda: f'servo_active= {shared.servo_tracking.value}', coords=(50, -500))
    ]
    info_group2 = writergroups.AssetGroup((0, 0)).add(extra_writers)

    otis = typewriters.TypeWriter(coords=(50, 120),
                                  ref='lb',
                                  jtype='l',
                                  scale=1.5,
                                  max_line_length=capture.f_dim[0] - 100,
                                  one_border=True,
                                  perma_background=True,
                                  border_spacing=(.5, .5),
                                  n_lines=3,
                                  transparent_background=.9,
                                  loop=False,
                                  color='g',
                                  perma_border=True,
                                  key_wait_range=(.06, .07),
                                  )

    the_script = queue.Queue()
    for line in OTIS_SCRIPT:
        the_script.put(line)

    #################################### THE LOOOP #####################################################################
    otis_speaks = False
    start_raining_balls = False
    show_info = False
    tick = time.time()
    capture.record = False

    while True:

        ############################### ##graphics ####################################################################

        _, frame = capture.read()
        shared.frame[:] = frame  # latest frame copied to shared frame

        box_manager.update_boxes()  # load data from model process and update box name locations
        box_manager.update_primary()  # choose primary target for servo process

        if box_manager.primary_box is not None: # nothing starts until otis finds someone
            capture.record = True
            start_raining_balls = True

        box_manager.write(frame)
        if start_raining_balls is True:
            sprinkler.loop(frame, box_manager.primary_box)  # send the balls everywhere
        # frame_portion = coordtools.get_frame_portion(frame, (0, 0, 200, 200), ref='c')
        # mirror.write(frame, frame_portion)

        otis.write(frame)
        # otis waits until there's someone here to talk
        if box_manager.primary_box is not None:
            if otis_speaks is False:
                tick = time.time()
            otis_speaks = True

        if otis_speaks is True and otis.text_complete is True and the_script.empty() is False:
            new_line = the_script.get()
            otis.text = new_line

        otis.write(frame)
        if show_info is True:
            info_group.write(frame)
            info_group2.write(frame)

        capture.show(frame)

        if otis_speaks is True and otis.text_complete is True and the_script.empty() is True:
            print(round(time.time() - tick, 2))

            shared.keyboard_input.value = ord('q')
            shared.new_keyboard_input.value = True
            break

        ############################ keyboard inputs ###################################################################

        keyboard_input = cv2.waitKey(1) & 0xFF  # only camera process receives the keyboard input

        if shared.new_keyboard_input.value is False and keyboard_input != 255:  # 255 is the value given for no input

            shared.keyboard_input.value = keyboard_input
            shared.new_keyboard_input.value = True

            if shared.keyboard_input.value == ord('q'):  # exit / destroy windows on 'q'
                break

            elif shared.keyboard_input.value == ord('1'):  # toggle info data on screen
                show_info = not show_info

            shared.key_input_received[0] = True  # set as received

        if np.count_nonzero(shared.key_input_received) == 3:  # reset once all have processes have received the input
            shared.new_keyboard_input.value = False
            shared.key_input_received[:] = False
            shared.keyboard_input.value = 255

    # exit and destroy frames, etc
    capture.stop()
    sys.exit()


#######################################################################################################################
########################   Extra Object Managers                          #############################################
#######################################################################################################################

class MirrorEffects:

    def __init__(self,
                 manager
                 ):
        self.manager = manager
        self.shared = manager.shared
        self.pargs = manager.pargs
        self.image_writers = []
        self.image_writer = imageassets.ImageAsset(copy_updates=True)
        self.sizes = [(300, 300)]

    def write(self, frame, image):
        image_writer = self.image_writer
        image_writer.resize_to = size = (300, 300)
        self.image_writer.image = image

        os = 20
        corners = ('rt', 'lb', 'lt', 'rb')
        offsets = ((-os, -os), (os, os), (os, -os), (-os, os))

        for corner, offset in zip(corners, offsets):
            image_writer.write(frame,
                               coords=(*offset, *size),
                               ref=corner,
                               in_format=corner + 'wh')


class BallSprinkler:

    def __init__(self,
                 manager,
                 x_border=75,
                 frame_portion_scale=1):

        self.shared = manager.shared
        self.capture = manager.capture
        self.pargs = manager.pargs
        self.n_bouncers = 20
        self.gravity = -10
        self.dampen = .01
        self.new_ball_wait = 1
        self.time_since_ball = timers.TimeSinceLast()
        self.ball_buffer = 10
        self.circle_buffer = 10
        self.ball_collision = True
        self.ball_diameter = 80
        self.big_ball_diameter = 100
        self.big_ball_on = False
        self.box_collisions = True
        self.x_range = (x_border, self.pargs.f_dim[0] - x_border)
        self.y_range = (x_border, 950 - x_border)
        self.cycle_time = 4
        self.x_border = x_border
        self.x_value_counter = timers.TimedCycle(*self.x_range,
                                                 updown=True,
                                                 cycle_t=self.cycle_time
                                                 )

        self.rectangle_counter = timers.TimedRectangleCycle(self.x_range,
                                                            self.y_range,
                                                            cycle_t=self.cycle_time
                                                            )

        self.circle = shapes.Circle((0, 0), 100, ref='c', dim=self.capture.f_dim, to_abs=True)

        self.counter_check = timers.TimeSinceLast()
        # this function creates new bouncers
        def mover_function():
            resize_to = np.random.randint(2*self.ball_diameter,6*int(self.ball_diameter))//4
            # resize_to = self.ball_diameter
            image_balls = imageassets.ImageAsset(center=(0, 0),
                                                 resize_to=(resize_to, resize_to),
                                                 hitbox_type='circle0',
                                                 use_circle_mask=True,
                                                 )
            side_pi = [np.pi / 4, 3 / 4 * np.pi, 5 / 4 * np.pi, 7 / 4 * np.pi]
            ball_origin = self.rectangle_counter()
            side = self.rectangle_counter.side
            mover = AssetMover(image_balls,
                               center=(self.x_value_counter(), 50),
                               # center = ball_origin,
                               velocity=(np.random.randint(400, 700),
                                         np.random.rand() * np.pi / 2 + np.pi / 4
                                         ),
                               # np.random.rand() * np.pi/2+ np.pi/4 - side*np.pi/2),
                               dim=self.capture.f_dim,
                               ups=self.capture.max_fps,
                               border_collision=True,
                               gravity=self.gravity,
                               dampen=self.dampen,
                               y_range=(0, 950)

                               )
            return mover

        self.mover_function = mover_function
        self.movement_manager = assetmover.CollidingAssetManager(collisions=self.ball_collision,
                                                                 max_movers=self.n_bouncers,
                                                                 buffer=self.ball_buffer)

        self.new_ball_timer = timers.CallFrequencyLimiter(self.new_ball_wait)
        self.frame_portion_scale = frame_portion_scale

        self.big_ball = imageassets.ImageAsset(center=(0, 0),
                                               resize_to=(self.big_ball_diameter, self.big_ball_diameter),
                                               hitbox_type='circle0',
                                               use_circle_mask=True,
                                               )

        self.rectangle_counters = []
        self.new_big_ball_wait = 2
        self.new_big_ball_timer = timers.CallFrequencyLimiter()
        self._new_wait_list = np.array([0, .25, .25, .25, .125, .25, .25, .25])*4

    def loop(self, frame, target):
        # if there is no target, the balls will focus on a circle0 in the middle of the screen
        if target is None:
            w = self.circle.width
            h = self.circle.height
            c = self.circle.center
        else:
            w = target.width
            h = target.height
            c = target.center

        p_space = self.frame_portion_scale
        frame_portion = coordtools.get_frame_portion(frame, (*c, int(w * p_space), int(h * p_space)))
        movement_manager = self.movement_manager

        if  self.new_ball_timer() is True and len(self.rectangle_counters) >-1:  # and manager.n < n_bouncers:
            ball = self.mover_function()
            movement_manager.movers.append(ball)

        movement_manager.update_velocities()

        if target is not None:
            for mover in movement_manager.movers:
                movement_manager.detector.collide(target, mover, buffer=self.circle_buffer)
                # assetmover.remove_overlap_w_no_mass(target, mover)

        movement_manager.move()
        #
        # try:
        if 0 not in frame_portion.shape:
            if len(self.rectangle_counters) > 0:
                self.big_ball.image = frame_portion
            small_frame_portion = cv2.resize(frame_portion, (self.ball_diameter, self.ball_diameter))

            for mover in movement_manager.movers:
                mover.asset.write(frame, small_frame_portion)

            lrc = len(self.rectangle_counters)

            # make the 8 big balls that circle0
            if self.big_ball_on is True and lrc < 8 and self.new_big_ball_timer(self._new_wait_list[lrc]):
                new_timer = timers.TimedRectangleCycle(self.x_range,
                                                        self.y_range,
                                                        cycle_t=self.cycle_time
                                                        )
                self.rectangle_counters.append(new_timer)

            frame_portion = cv2.resize(frame_portion, (self.big_ball_diameter, self.big_ball_diameter))

            for timer in self.rectangle_counters:
                self.big_ball.center = timer()
                self.big_ball.write(frame, frame_portion)


############################################### OTIS SCRIPT ############################################################



