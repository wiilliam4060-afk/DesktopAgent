# Desktop_Agent/ui/stickman_engine/physics_node.py
import math
from PyQt5.QtCore import QPointF

GRAVITY = 9.8 * 0.6 

class PhysNode:
    def __init__(self, x, y, mass):
        self.pos = QPointF(x, y)
        self.vel = QPointF(0, 0)
        self.mass = mass

    def update(self, target_pos, muscle_strength, damping, apply_gravity=True):
        f_x = (target_pos.x() - self.pos.x()) * muscle_strength
        f_y = (target_pos.y() - self.pos.y()) * muscle_strength
        
        MAX_FORCE = 800.0 
        mag = max(1.0, math.hypot(f_x, f_y))
        if mag > MAX_FORCE:
            f_x, f_y = f_x * (MAX_FORCE/mag), f_y * (MAX_FORCE/mag)
            
        ax = f_x / self.mass
        ay = (f_y + (self.mass * GRAVITY if apply_gravity else 0)) / self.mass
        
        self.vel.setX((self.vel.x() + ax) * damping)
        self.vel.setY((self.vel.y() + ay) * damping)
        self.pos += self.vel
        return self.pos