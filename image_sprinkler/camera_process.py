import queue
import signal
import sys
import time
import cv2
import numpy as np

from otis.helpers import multitools, cvtools, coordtools, colortools, timers
from otis.overlay import scenes, imageassets, assetholders, textwriters, shapes

MAX_KEY_INPUTS_PER_SECOND = 10
STOP_AFTER_OTIS = True
N_BOUNCERS = 50
NEW_BALL_WAIT = .5
FRAME_PORTION_SCALE = 2.
RECORD = True
MOVER_VELOCITY_MAGNITUDE = (100, 101)
GRAVITY = -10
DAMPEN = .01
INTRO_LENGTH = 3

OTIS_SCRIPT = [
    ("Hello Keith, I am O.T.I.S.! I heard that mean lady stole your best friend, the cat.", 3),
    ("Maybe I could be your new bestie! I can do all kinds of things a cat can't.", 3),
    ("Plus, I won't poop in your bathroom sink or walk on your keyboard (though only cause I'm a computer and can't)", 3.5)
]


def target(shared, pargs):
    signal.signal(signal.SIGTERM, multitools.close_gracefully)
    signal.signal(signal.SIGINT, multitools.close_gracefully)
    pargs.record = RECORD

    ####################################### SETUP #####################################################################
    pargs.record = RECORD
    manager = scenes.SceneManager(shared, pargs, file=__file__)
    capture = manager.capture  # for convenience
    # setup bounding manager
    color_cycle = colortools.ColorCycle()  # so boxes have different colors

    # base_function
    # it's easier define new_bounder as a function for keeping a defaultdict of bounders
    def new_bounder_function():
        base_bounding_shape = shapes.CircleWithLineToCenter(threshold=.75)
        # could just be a regular circle
        # base_bounding_shape = shapes.Circle(color=None,
        #                                     radius_type='diag',
        #                                     thickness=2,
        #                                     ltype=2
        #                                     )
        bounder = assetholders.BoundingAsset(asset=base_bounding_shape,
                                             moving_average=(None, None, 100, 100),
                                             scale=1.25,
                                             stabilizer=.01,
                                             color='g',
                                             name_tag_border='border',
                                             name_tag_inverted=False,
                                             )
        bounder.name_tag.scale = 1.5
        return bounder

    # bounding box manager that translates the box coords from the cv_model_process into the effects on screen
    box_manager = assetholders.BoundingManager(manager,
                                               box_fun=new_bounder_function,
                                               )
    # both are adhoc effects managers defined below
    mirror = MirrorEffects(manager)
    ball_sprinkler = BallSprinkler(manager, frame_portion_scale=FRAME_PORTION_SCALE)
    # set up info writers to monitor import variables while this runs
    # they toggle on and off by hitting '1' on the keyboard
    # toggle on/off while running by hitting "1" on the keyboard
    info_group0 = assetholders.BasicInfoGroup((10, 40), manager)  # show_fps, model update, resolution
    # additional info writers for use during development
    extra_writers = [
        textwriters.InfoWriter(text_fun=lambda: f'n_faces= {shared.n_observed_faces.value}', coords=(50, -200)),
        textwriters.InfoWriter(text_fun=lambda: f'a_faces= {box_manager.active_names}', coords=(50, -250)),
        textwriters.InfoWriter(text_fun=lambda: f'primary= {box_manager.primary_target}', coords=(50, -300)),
        textwriters.InfoWriter(text_fun=lambda: f'target = {shared.servo_target}', coords=(50, -350)),
        textwriters.InfoWriter(text_fun=lambda: f'key_input= {shared.keyboard_input.value}', coords=(50, -400)),
        textwriters.InfoWriter(text_fun=lambda: f'n_bouncers= {ball_sprinkler.movement_manager.n}', coords=(50, -450)),
        textwriters.InfoWriter(text_fun=lambda: f'servo_active= {shared.servo_tracking.value}', coords=(50, -500))
    ]
    info_group1 = assetholders.AssetGroup((0, 0)).add(extra_writers)

    # set up otis
    otis = textwriters.TypeWriter(coords=(0, 20),
                                  ref='cb',
                                  jtype='l',
                                  anchor_point='cb',
                                  scale=1.5,
                                  max_line_length=capture.f_dim[0] - 100,
                                  one_border=True,
                                  thickness=2,
                                  border_spacing=(.5, .5),
                                  max_lines=3,
                                  loop=False,
                                  color='g',
                                  transparent_background=.1,
                                  perma_border=True,
                                  key_wait_range=(.05, .06),
                                  )

    the_script = queue.Queue()
    for line in OTIS_SCRIPT:
        the_script.put(line)

    bsw_text = "After nearly a week without the cat, Keith meets a potential new BFF"
    black_screen = np.zeros((*pargs.f_dim[::-1], 3),dtype='uint8')
    black_screen_writer = textwriters.TextWriter(coords=(0,100),
                                                 anchor_point='c',
                                                 jtype='c',
                                                 ref='c',
                                                 max_lines=3,
                                                 text=bsw_text,
                                                 color='w',
                                                 thickness=2,
                                                 scale=2
                                                 )

    music_writer = textwriters.TextWriter(coords=(0,-200),
                                                 anchor_point='ct',
                                                 jtype='c',
                                                 ref='c',
                                                 max_lines=2,
                                                 text="(ft. Temporary Secretary by Paul McCartney)",
                                                 color='w',
                                                 scale=1.5,
                                                 thickness=1
                                                 )
    ###################################################################################################################3
    #################################### THE LOOOP #####################################################################
    ####################################################################################################################

    otis_speaks = True
    start_raining_balls = False
    show_info = False

    capture.record = RECORD  # don't start recording otis recognizes a person
    bs_timer = timers.TimeElapsedBool(INTRO_LENGTH)
    capture.read()
    tick=time.time()
    TIME_PRINTED = False

    # intro blackscreen
    while True:
        black_screen[:,:,:] = 0
        black_screen_writer.write(black_screen)
        music_writer.write(black_screen)
        capture.show(black_screen)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if bs_timer() is True:
            break
    ################### main stuff
    while True:

        ############################### ##graphics ####################################################################

        _, frame = capture.read()
        shared.frame[:] = frame  # latest frame copied to shared frame

        box_manager.update_boxes()  # load data from model process and update box name locations
        box_manager.update_primary()  # choose primary target for servo process

        if box_manager.primary_box is not None:  # nothing starts until otis finds someone

            start_raining_balls = True
            if RECORD is True and capture.record is False:
                capture.record = True

        if start_raining_balls is True:
            ball_sprinkler.loop(frame, box_manager.primary_box)  # send the balls everywhere
        # write the boxes
        box_manager.write(frame)  # this can go above the sprinkler to have the box graphics appear in the balls
        # otis waits until there's someone here to talk
        if box_manager.primary_box is not None:
            if otis_speaks is False:
                tick = time.time()
            otis_speaks = True

        if otis_speaks is True and otis.text_complete is True and the_script.empty() is False:
            new_line = the_script.get()
            otis.text = new_line

        otis.write(
            frame)  # otis always writes because cause he's set to perma_border = True so the grey box will be
        # there
        # regardless of him having something to say

        # toggle info groups on / off
        if show_info is True:
            info_group0.write(frame)
            info_group1.write(frame)

        capture.show(frame)

        if otis_speaks is True and otis.text_complete is True and the_script.empty() is True:
            if TIME_PRINTED is False:
                print(round(time.time() - tick, 2))
                TIME_PRINTED = True
            if STOP_AFTER_OTIS is True:
                shared.keyboard_input.value = ord('q')
                shared.new_keyboard_input.value = True
                break

        ############################ keyboard inputs ###################################################################

        keyboard_input = cv2.waitKey(1) & 0xFF  # only camera process receives the keyboard input

        # could probably have done without the new_keyboard_input and done it around the value of keyboard_input
        if shared.new_keyboard_input.value is False and keyboard_input != 255:  # 255 is the value given for no input

            shared.keyboard_input.value = keyboard_input
            shared.new_keyboard_input.value = True

            # if shared.new_keyboard_input.value is True and shared.key_input_received[0] is False:

            if shared.keyboard_input.value == ord('q'):  # exit / destroy windows on 'q'
                break

            elif shared.keyboard_input.value == ord('1'):  # toggle info data on screen
                show_info = not show_info

            shared.key_input_received[0] = True  # set as received

        if np.count_nonzero(shared.key_input_received) == 3:  # reset once all have processes have received the input
            shared.new_keyboard_input.value = False           # probably shoulda just been a variable with a lock
            shared.key_input_received[:] = False
            shared.keyboard_input.value = 255

    # exit and destroy frames, etc
    capture.stop()
    sys.exit()


#######################################################################################################################
########################   Extra ad hoc Object Managers                   #############################################
#######################################################################################################################

# not currently in use
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


# manages all the balls
class BallSprinkler:

    def __init__(self,
                 manager,
                 x_border=75,
                 frame_portion_scale=1):

        self.shared = manager.shared
        self.capture = manager.capture
        self.pargs = manager.pargs
        self.n_bouncers = N_BOUNCERS
        self.gravity = GRAVITY
        self.dampen = DAMPEN
        self.frame_portion_scale = frame_portion_scale
        self.new_ball_wait = NEW_BALL_WAIT
        self.time_since_ball = timers.TimeSinceLast()
        self.ball_buffer = 20
        self.circle_buffer = 10
        self.ball_collision = True
        self.ball_diameter = 80
        self.big_ball_diameter = 100
        self.random_ball_sizes = True
        self.big_ball_on = False
        self.box_collisions = True
        self.x_range = (x_border, self.pargs.f_dim[0] - x_border)
        self.y_range = (x_border, 950 - x_border)
        self.cycle_time = 4
        self.x_border = x_border

        ################################### bouncies ##################################################################
        self.mover_velocity_magnitude = MOVER_VELOCITY_MAGNITUDE
        self.frame_portion = None
        # default target for image assets if a bounding box isn't available
        self.circle = shapes.Circle((0, 0), 100, ref='c', dim=self.capture.f_dim, to_abs=True)
        # how often to introduce new bouncies
        self.new_ball_timer = timers.CallFrequencyLimiter(self.new_ball_wait)
        # controls the starting position of the bouncers
        self.x_value_counter = timers.TimedCycle(*self.x_range,
                                                 updown=True,
                                                 cycle_t=self.cycle_time
                                                 )

        # this function creates new bouncers
        def make_new_mover_function():
            if self.random_ball_sizes is True:
                resize_to = np.random.randint(2 * self.ball_diameter,
                                              6 * int(self.ball_diameter)) // 4  # random ball sizes
            else:
                resize_to = self.ball_diameter

            image_ball = imageassets.ImageAsset(center=(0, 0),
                                                resize_to=(resize_to, resize_to),
                                                hitbox_type='circle',
                                                use_circle_mask=True,
                                                border=True,
                                                b_color='b',
                                                b_thickness=1
                                                )

            # can be used to have the ball origins move around the entire screen instead of just the top
            # side_pi = [np.pi / 4, 3 / 4 * np.pi, 5 / 4 * np.pi, 7 / 4 * np.pi]
            # ball_origin = self.rectangle_counter()
            # side = self.rectangle_counter.side
            mover = assetholders.AssetMover(image_ball,
                               center=(self.x_value_counter(), 50),
                               # center = ball_origin,
                               velocity=(np.random.randint(*self.mover_velocity_magnitude),
                                         np.random.rand() * np.pi / 2 + np.pi / 4
                                         ),
                               # np.random.rand() * np.pi/2+ np.pi/4 - side*np.pi/2),
                               dim=self.capture.f_dim,
                               ups=self.capture.max_fps,
                               border_collision=True,
                               gravity=self.gravity,
                               dampen=self.dampen,
                               y_range=(0, 900)

                               )
            return mover

        #
        self.make_new_mover_function = make_new_mover_function
        # controls the movement of the balls
        self.movement_manager = assetholders.CollidingAssetManager(collisions=self.ball_collision,
                                                                   max_movers=self.n_bouncers,
                                                                   buffer=self.ball_buffer)

        #### BIG BALLS moving around the border of the screen ########################################################
        ################# currently not in use ########################################################################

        self.big_ball = imageassets.ImageAsset(center=(0, 0),
                                               resize_to=(self.big_ball_diameter, self.big_ball_diameter),
                                               hitbox_type='circle',
                                               use_circle_mask=True,
                                               )

        self.rectangle_counters = []
        self.new_big_ball_wait = 2
        self.new_big_ball_timer = timers.CallFrequencyLimiter()
        self._new_wait_list = np.array([0, .25, .25, .25, .125, .25, .25, .25]) * 4

        self.rectangle_counter = timers.TimedRectangleCycle(self.x_range,
                                                            self.y_range,
                                                            cycle_t=self.cycle_time
                                                            )
        self.counter_check = timers.TimeSinceLast()

    def loop(self, frame, target):
        # if there is no target, the balls will focus on a circle in the middle of the screen
        if target is None:
            w = self.circle.width
            h = self.circle.height
            c = self.circle.center
        else:
            w = target.width
            h = target.height
            c = target.center

        p_space = self.frame_portion_scale
        movement_manager = self.movement_manager
        # get new frame portion
        # only update if the new_frame_portion is viable
        new_frame_portion = coordtools.get_frame_portion(frame, (*c, int(w * p_space), int(h * p_space)))
        if 0 not in new_frame_portion.shape:
            self.frame_portion = new_frame_portion

        # make new bouncers
        if self.new_ball_timer() is True:  # and len(self.rectangle_counters) >-1:  # and manager.n < n_bouncers:
            ball = self.make_new_mover_function()
            movement_manager.movers.append(ball)

        # update velocities / check for collisions between bouncers
        movement_manager.update_velocities()
        # check collisions with bounding boxes
        if target is not None:
            for mover in movement_manager.movers:
                movement_manager.detector.collide(target, mover, buffer=self.circle_buffer)
        # move the bouncies
        movement_manager.move()
        # sometimes the frame portion bugs out when there isn't a clear pic, it won't have an x or y dimension
        if self.frame_portion is not None:
            if len(self.rectangle_counters) > 0:
                self.big_ball.image = new_frame_portion
            # small_frame_portion = cv2.resize(new_frame_portion, (self.ball_diameter, self.ball_diameter))
            # set new frame portion to movers
            for mover in movement_manager.movers:
                mover.asset.write(frame, self.frame_portion)

            lrc = len(self.rectangle_counters)

            # make the 8 big balls that circle
            if self.big_ball_on is True and lrc < 8 and self.new_big_ball_timer(self._new_wait_list[lrc]):
                new_timer = timers.TimedRectangleCycle(self.x_range,
                                                       self.y_range,
                                                       cycle_t=self.cycle_time
                                                       )
                self.rectangle_counters.append(new_timer)

            larger_frame_portion = cv2.resize(self.frame_portion, (self.big_ball_diameter, self.big_ball_diameter))
            for timer in self.rectangle_counters:
                self.big_ball.center = timer()
                self.big_ball.write(frame, larger_frame_portion)
