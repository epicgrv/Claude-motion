"""Station frames: local +Z faces the viewer, +Y is up, +X is right (as seen by the viewer)."""
from __future__ import annotations

import math

import numpy as np
from mathutils import Matrix, Vector

from . import geo


class Frame:
    def __init__(self, origin, facing=(0, -1, 0), up_hint=(0, 0, 1)):
        self.o = np.asarray(origin, float)
        z = np.asarray(facing, float)
        z = z / np.linalg.norm(z)
        h = np.asarray(up_hint, float)
        y = h - np.dot(h, z) * z
        if np.linalg.norm(y) < 1e-6:
            y = np.array([0, 1.0, 0]) - z[1] * z
        y = y / np.linalg.norm(y)
        x = np.cross(y, z)
        self.x, self.y, self.z = x, y, z
        self.R = np.stack([x, y, z], axis=1)         # columns = local axes in world

    def p(self, x=0.0, y=0.0, z=0.0):
        """Local point(s) -> world. Accepts scalars or arrays."""
        x, y, z = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float), np.asarray(z, float))
        v = np.stack([x, y, z], axis=-1)
        return self.o + v @ self.R.T

    def d(self, x=0.0, y=0.0, z=0.0):
        """Local direction -> world direction."""
        v = np.stack(np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float), np.asarray(z, float)), axis=-1)
        return v @ self.R.T

    def euler(self):
        m = Matrix(self.R.tolist())
        return m.to_euler("XYZ")

    def empty(self, name, coll, parent=None):
        e = geo.empty(name, coll, loc=tuple(self.o), parent=parent)
        e.rotation_euler = self.euler()
        return e
