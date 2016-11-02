from __future__ import division
from numbers import Number
import numpy as np
import cv2
from menpo.transform import Transform, Translation, Rotation


class PerspectiveProjection(Transform):

    def __init__(self, f, image_shape):
        f = [f, f] if isinstance(f, Number) else f
        self.f_x = f[0]
        self.f_y = f[1]
        self.height = image_shape[0]
        self.width = image_shape[1]

    @property
    def n_dims(self):
        return 3

    def _apply(self, x, **kwargs):
        c_x = self.width / 2
        c_y = self.height / 2

        f_z = (self.f_x + self.f_y) / 2

        output = np.empty_like(x)
        output[:, 0] = (self.f_x * x[:, 0]) / x[:, 2] + c_x
        output[:, 1] = self.height - ((self.f_y * x[:, 1]) / x[:, 2] + c_y)
        output[:, 2] = f_z * x[:, 2]

        return output


def optimal_perspective_camera(points_image, points_3d, image_shape,
                               f=None, distortion_coeffs=None):
    height, width = image_shape
    # Create camera matrix
    f = max(height, width) if f is None else f
    c_x = width / 2.0
    c_y = height / 2.0
    camera_matrix = np.array([[f, 0, c_x],
                              [0, f, c_y],
                              [0, 0, 1.0]])

    # If distortion coefficients are None, set them to zero
    if distortion_coeffs is None:
        distortion_coeffs = np.zeros(4)
    # Estimate the camera pose given the 3D sparse pointcloud on the
    # mesh, its 2D projection on the image, the camera matrix and the
    # distortion coefficients
    lm2d = points_image.points[:, ::-1]
    lm2d[: 1] = height - lm2d[: 1]
    _, r_vec, t_vec = cv2.solvePnP(points_3d.points,
                                   lm2d,
                                   camera_matrix, distortion_coeffs)

    # Create rotation and translation transform objects from the vectors
    # acquired at the previous step
    rotation_matrix = cv2.Rodrigues(r_vec)[0]
    r = Rotation(rotation_matrix)
    t = Translation(t_vec.ravel())

    projection = PerspectiveProjection(f, image_shape)

    return r, t, projection, r.compose_before(t).compose_before(projection)
