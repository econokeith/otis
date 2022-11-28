import signal
import sys
import cv2
import numpy as np

from otis import camera as camera
from otis.helpers import multitools, cvtools, coordtools
from otis.overlay import scenes, writergroups, shapes, boundingobjects, textwriters, imageassets, assetmover
from otis.helpers import shapefunctions, timers
from otis.overlay.assetmover import AssetMover

pie_path = 'photo_asset_files/pie_asset'
MAX_KEYS_PER_SECOND = 10


def target(shared, pargs):
    signal.signal(signal.SIGTERM, multitools.close_gracefully)
    signal.signal(signal.SIGINT, multitools.close_gracefully)


    ####################################### SETUP #####################################################################

    manager = scenes.SceneManager(shared, pargs, file=__file__)
    manager.capture.silent_sleep = False

    # base shape for bounding
    base_bounder = shapes.Circle(
                                 color=None,
                                 update_format='trbl',
                                 radius_type='diag'
                                 )

    box_manager = boundingobjects.BoundingManager(manager,
                                                  base_asset=base_bounder,
                                                  moving_average=(2, 2, 40, 40),
                                                  )

    info_group = writergroups.BasicInfoGroup((10, 40), manager)
    capture = manager.capture

    mirror = MirrorEffects(manager)
    sprinkler = BallSprinkler(manager, frame_portion_scale=1.5)

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

    show_info = True

    #################################### THE LOOOP #####################################################################

    while True:

        ############################### graphics ######################################################################
        check, frame = capture.read()
        shared.frame[:] = frame  # latest frame to shared frame

        box_manager.update_boxes()
        box_manager.update_primary()

        sprinkler.loop(frame, box_manager.primary_box)
        frame_portion = coordtools.get_frame_portion(frame, (0, 0, 200, 200), ref='c')
        #mirror.write(frame, frame_portion)
        box_manager.write(frame)

        if show_info is True:
            info_group2.write(frame)
            info_group.write(frame)

        capture.show(frame)

        ############################ keyboard inputs #####################################################

        keyboard_input = cv2.waitKey(1) & 0xFF

        if shared.new_keyboard_input.value is False and keyboard_input != 255:

            shared.keyboard_input.value = keyboard_input
            shared.new_keyboard_input.value = True

            if shared.keyboard_input.value == ord('q'):
                break

            elif shared.keyboard_input.value == ord('1'):
                show_info = not show_info

            shared.key_input_received[0] = True

        if np.count_nonzero(shared.key_input_received) == 3:
            shared.new_keyboard_input.value = False
            shared.key_input_received[:] = False

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
        self.image_writer = imageassets.AssetWithImage(copy_updates=True)
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

        self.n_bouncers = 200
        self.gravity = -10
        self.dampen = .05
        self.new_ball_wait = .05
        self.time_since_ball = timers.TimeSinceLast()

        self.ball_buffer = 5
        self.circle_buffer = 5
        self.ball_collision = False
        self.ball_diamter = 50
        self.box_collisions = True
        self.x_value_min = x_border
        self.x_value_max = self.capture.dim[0] - x_border
        self.cycle_time = 4
        self.x_value_counter = timers.TimedCycle(self.x_value_min,
                                                 self.x_value_max,
                                                 updown=True,
                                                 cycle_t=self.cycle_time)

        self.circle = shapes.Circle((0, 0), 100, ref='c', dim=self.capture.dim, to_abs=True)

        def mover_function():
            pie = imageassets.AssetWithImage(center=(0, 0),
                                             resize_to=(self.ball_diamter, self.ball_diamter),
                                             hitbox_type='circle',
                                             use_circle_mask=True,
                                             )

            mover = AssetMover(pie,
                               center=(self.x_value_counter(), 50),
                               velocity=(np.random.randint(100, 200),
                                         np.random.rand() * np.pi / 2 + np.pi / 4),
                               dim=self.capture.dim,
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
            for mover in movement_manager.movers:
                mover.asset.write(frame, frame_portion)

        except:
            print("error in writing frame_portion has occured")

