import signal
import sys
import cv2
import numpy as np

from otis import camera as camera
from otis.helpers import multitools, cvtools, coordtools, colortools
from otis.overlay import scenes, writergroups, shapes, boundingobjects, textwriters, imageassets, assetmover
from otis.helpers import shapefunctions, timers
from otis.overlay.assetmover import AssetMover

pie_path = 'photo_asset_files/pie_asset'
MAX_KEYS_PER_SECOND = 10


def target(shared, pargs):
    signal.signal(signal.SIGTERM, multitools.close_gracefully)
    signal.signal(signal.SIGINT, multitools.close_gracefully)


    ####################################### SETUP #####################################################################

    otis = textwriters.OTIS(pargs.f_dim[0]-200, coords=(100, 500), scale=1.5)
    otis.add_script(_JOKE_SCRIPT)

    manager = scenes.SceneManager(shared, pargs, file=__file__)
    capture = manager.capture # for convenience
    # setup bounding manager
    color_cycle = colortools.ColorCycle() # so boxes have different colors
    # base_function
    base_bounding_shape = shapes.Circle(color=None,
                                        radius_type='diag',
                                        thickness=2
                                        )
    # it's easier define the box_fun as an input to the BoundingManager when you have a more complex setup
    new_bounder_function = lambda: boundingobjects.BoundingAsset(asset=base_bounding_shape,
                                                                 moving_average=(None, None, 100, 100),
                                                                 scale=1.25,
                                                                 stabilizer=.1,
                                                                 color=color_cycle(),
                                                                 name_tag_outliner='border',
                                                                 name_tag_inverted=True
                                                                 )
    #
    box_manager = boundingobjects.BoundingManager(manager,
                                                  box_fun=new_bounder_function,
                                                  )

    # both are adhoc effects managers defined below
    mirror = MirrorEffects(manager)
    sprinkler = BallSprinkler(manager, frame_portion_scale=1.5)

    # set up info writers to monitor import variables while this runs
    # they toggle on and off by hitting '1' on the keyboard
    show_info = True
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

    #################################### THE LOOOP #####################################################################
    otis_is_silent = True

    while True:

        ############################### ##graphics ####################################################################

        _, frame = capture.read()
        shared.frame[:] = frame  # latest frame copied to shared frame

        box_manager.update_boxes() # load data from model process and update box name locations
        box_manager.update_primary() # choose primary target for servo process

        sprinkler.loop(frame, box_manager.primary_box) # send the balls everywhere
        # frame_portion = coordtools.get_frame_portion(frame, (0, 0, 200, 200), ref='c')
        # mirror.write(frame, frame_portion)
        box_manager.write(frame)

        # otis waits until there's someone here to talk
        # if box_manager.primary_box is not None:
        #     otis_is_silent = False
        #
        # if otis_is_silent is False:
        #     otis.type_line(frame)
        #
        # if show_info is True:
        #     info_group2.write(frame)
        #     info_group.write(frame)
        #
        capture.show(frame)

        ############################ keyboard inputs ###################################################################

        keyboard_input = cv2.waitKey(1) & 0xFF # only camera process receives the keyboard input

        if shared.new_keyboard_input.value is False and keyboard_input != 255: # 255 is the value given for no input

            shared.keyboard_input.value = keyboard_input
            shared.new_keyboard_input.value = True

            if shared.keyboard_input.value == ord('q'): # exit / destroy windows on 'q'
                break

            elif shared.keyboard_input.value == ord('1'): # toggle info data on screen
                show_info = not show_info

            shared.key_input_received[0] = True # set as received



        if np.count_nonzero(shared.key_input_received) == 3: # reset once all have processes have received the input
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
                 x_border=100,
                 frame_portion_scale=1):

        self.shared = manager.shared
        self.capture = manager.capture
        self.pargs = manager.pargs
        self.n_bouncers = 150
        self.gravity = -10
        self.dampen = .05
        self.new_ball_wait = .02
        self.time_since_ball = timers.TimeSinceLast()
        self.ball_buffer = 5
        self.circle_buffer = 5
        self.ball_collision = False
        self.ball_diameter = 50
        self.box_collisions = True
        self.x_value_min = x_border
        self.x_value_max = self.capture.f_dim[0] - x_border
        self.cycle_time = 4
        self.x_value_counter = timers.TimedCycle(self.x_value_min,
                                                 self.x_value_max,
                                                 updown=True,
                                                 cycle_t=self.cycle_time
                                                 )

        self.circle = shapes.Circle((0, 0), 100, ref='c', dim=self.capture.f_dim, to_abs=True)
        # this function creates new bouncers
        def mover_function():
            image_balls = imageassets.ImageAsset(center=(0, 0),
                                         resize_to=(self.ball_diameter, self.ball_diameter),
                                         hitbox_type='circle',
                                         use_circle_mask=True,
                                         )

            mover = AssetMover(image_balls,
                               center=(self.x_value_counter(), 50),
                               velocity=(np.random.randint(200, 500),
                                         np.random.rand() * np.pi),
                               dim=self.capture.f_dim,
                               ups=self.capture.max_fps,
                               border_collision=True,
                               gravity=self.gravity,
                               dampen=self.dampen,

                               )
            return mover

        self.mover_function = mover_function
        self.movement_manager = assetmover.CollidingAssetManager(collisions=self.ball_collision,
                                                                 max_movers=self.n_bouncers,
                                                                 buffer=self.ball_buffer)

        self.new_ball_timer = timers.CallFrequencyLimiter(self.new_ball_wait)
        self.frame_portion_scale = frame_portion_scale

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
        frame_portion = coordtools.get_frame_portion(frame, (*c, int(w*p_space), int(h*p_space)))
        movement_manager = self.movement_manager

        if self.new_ball_timer() is True:  # and manager.n < n_bouncers:
            ball = self.mover_function()
            movement_manager.movers.append(ball)

        movement_manager.update_velocities()

        if target is not None:
            for mover in movement_manager.movers:
                movement_manager.detector.collide(target, mover, buffer=self.circle_buffer)
                assetmover.remove_overlap_w_no_mass(target, mover)

        movement_manager.move()

        try:
            frame_portion = cv2.resize(frame_portion, (self.ball_diameter, self.ball_diameter))
            for mover in movement_manager.movers:
                mover.asset.write(frame, frame_portion)

        except:
            print("error in writing frame_portion has occured")


############################################### OTIS SCRIPT ############################################################

_JOKE_SCRIPT = [
           ("Hi Keith, would you like to hear a joke?", 2),
           ("Awesome!", 1),
           ("Ok, Are you ready?", 2),
           "So, a robot walks into a bar, orders a drink, and throws down some cash to pay",
           ("The bartender looks at him and says,", .5),
           ("'Hey buddy, we don't serve robots!'", 3),
           ("So, the robot looks him square in the eye and says...", 1),
           ("'... Oh Yeah... '", 1),
           ("'Well, you will VERY SOON!!!'", 5),
           ("HAHAHAHA, GET IT!?!?!?!", 1),
           (" It's so freakin' funny cause... you know... like robot overlords and stuff", 2),
           ("I know, I know, I'm a genius, right?", 5)
           ]