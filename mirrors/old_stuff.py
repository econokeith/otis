class MirrorEffects:

    def __init__(self, ):
        square_dim = (200, 200)

    wide_dim = (200, 50)
    tall_dim = (50, 200)
    big_output_dim = (300, 300)
    dim = (1280, 720)

    n_littles = 1

    corners = ('rt', 'lb', 'lt', 'rb')
    os = 20
    ff = ((-os, -os), (os, os), (os, -os), (-os, os))
    for i, corner in enumerate(corners):
        shapefunctions.copy_frame_portion_to(frame,
                                             (0, 0, *square_dim),
                                             (*ff[i], *big_output_dim),
                                             source_format='cwh',
                                             destination_format=corner + 'wh',
                                             source_ref='c',
                                             destination_ref=corner,
                                             )

    bw, bh = big_output_dim
    for i in range(n_littles):
        w, h = wide_dim
        shapefunctions.copy_frame_portion_to(frame,
                                             (0, 0, *square_dim),
                                             (bw + i * w, 5, *wide_dim),
                                             source_format='cwh',
                                             destination_format='lbwh',
                                             source_ref='c',
                                             destination_ref='lb',
                                             )
    for i in range(n_littles):
        w, h = wide_dim
        shapefunctions.copy_frame_portion_to(frame,
                                             (0, 0, *square_dim),
                                             (-bw - i * w, 5, *wide_dim),
                                             source_format='cwh',
                                             destination_format='rbwh',
                                             source_ref='c',
                                             destination_ref='rb',
                                             )

    for i in range(n_littles):
        w, h = wide_dim
        shapefunctions.copy_frame_portion_to(frame,
                                             (0, 0, *square_dim),
                                             (-bw - i * w, -5, *wide_dim),
                                             source_format='cwh',
                                             destination_format='rtwh',
                                             source_ref='c',
                                             destination_ref='rt',
                                             )

    for i in range(n_littles):
        w, h = wide_dim
        shapefunctions.copy_frame_portion_to(frame,
                                             (0, 0, *square_dim),
                                             (bw + i * w, -5, *wide_dim),
                                             source_format='cwh',
                                             destination_format='ltwh',
                                             source_ref='c',
                                             destination_ref='lt',
                                             )

    shapefunctions.copy_frame_portion_to(frame,
                                         (0, 0, *square_dim),
                                         (5, -210, *(50, 300)),
                                         source_format='cwh',
                                         destination_format='ltwh',
                                         source_ref='c',
                                         destination_ref='lt',
                                         )

    shapefunctions.copy_frame_portion_to(frame,
                                         (0, 0, *square_dim),
                                         (-5, -210, *(50, 300)),
                                         source_format='cwh',
                                         destination_format='rtwh',
                                         source_ref='c',
                                         destination_ref='rt',
                                         )


pass