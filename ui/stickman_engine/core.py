# Desktop_Agent/ui/stickman_engine/core.py
import math
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QPen, QColor, QPainter, QPainterPath

from .physics_node import PhysNode
from .actions.action_run import ActionRun
from .actions.action_climb import ActionClimb
from .actions.action_idle import ActionIdle
from .actions.action_parkour import ActionParkour
from .actions.action_grapple import ActionGrapple
from .actions.action_landing import ActionLanding
from .actions.action_hover import ActionHover 
from .actions.action_wall_jump import ActionWallJump

class StickmanPhysical:
    def __init__(self, color, thickness, base_height, start_x, start_y):
        self.color = color
        self.thickness = thickness
        self.h = base_height
        self.ground_line = start_y 
        self.phase = 0.0
        self.virtual_x = start_x
        
        self.arm_len_up, self.arm_len_low = self.h * 0.40, self.h * 0.38
        self.leg_len_up, self.leg_len_low = self.h * 0.45, self.h * 0.42
        self.total_leg_len = self.leg_len_up + self.leg_len_low
        
        self.virtual_y = self.ground_line - (self.total_leg_len * 0.95) - (self.h * 0.65)
        self.dir = 1
        
        self.n_head = PhysNode(start_x, self.virtual_y - self.h*0.65, mass=3.5)
        self.n_chest = PhysNode(start_x, self.virtual_y - self.h*0.45, mass=12.0)
        self.n_hips = PhysNode(start_x, self.virtual_y, mass=12.0)
        
        self.smooth_r_hand = QPointF(start_x, self.virtual_y)
        self.last_vx, self.smooth_ax = 0.0, 0.0
        self.last_vy, self.smooth_ay = 0.0, 0.0
        self.prev_state = "IDLE"
        self.climb_locks = {'hl': None, 'hr': None, 'fl': None, 'fr': None}
        
        self.target_anchor = None 
        self.hook_pos = None
        self.hover_seq_stage = "IDLE"
        self.hover_seq_frame = 0
        
        self.wall_jump_timer = 0
        self.wall_jump_dir = 1

    def draw_organic_bone(self, painter, p1, p2, p3):
        path = QPainterPath()
        path.moveTo(p1)
        path.lineTo(p2)
        path.lineTo(p3)
        painter.drawPath(path)

    def safe_ik_limb(self, painter, start, target, l1, l2, flip):
        dx, dy = target.x() - start.x(), target.y() - start.y()
        d = max(1.0, math.hypot(dx, dy))
        max_reach = l1 + l2 - 0.1
        if d > max_reach:
            dx, dy, d = dx*(max_reach/d), dy*(max_reach/d), max_reach
            target = QPointF(start.x() + dx, start.y() + dy)
        phi = math.atan2(dy, dx)
        cos_a = max(-1.0, min(1.0, (l1**2 + d**2 - l2**2) / (2 * l1 * d)))
        mid = QPointF(start.x() + l1 * math.cos(phi + math.acos(cos_a) * flip), 
                      start.y() + l1 * math.sin(phi + math.acos(cos_a) * flip))
        self.draw_organic_bone(painter, start, mid, target)

    def draw(self, painter, state, target_pos, current_vx=0, current_vy=0):
        if getattr(self, 'prev_state', None) != state:
            if state in ["CLIMBING", "CLIMBING_IDLE"]:
                self.climb_locks = dict.fromkeys(self.climb_locks, None)
            self.prev_state = state

        # ==============================================================
        # 🌟 修复抽搐的核心：加速度强制 Clamp！
        # 如果 vx 瞬间清零，delta_v 会是个天文数字，这里强制约束极限范围
        # ==============================================================
        delta_vx = current_vx - self.last_vx
        delta_vy = current_vy - self.last_vy
        
        delta_vx = max(-3.0, min(3.0, delta_vx))
        delta_vy = max(-3.0, min(3.0, delta_vy))

        self.smooth_ax += (delta_vx - self.smooth_ax) * 0.25
        self.smooth_ay += (delta_vy - self.smooth_ay) * 0.25
        self.last_vx, self.last_vy = current_vx, current_vy

        self.virtual_x += current_vx
        self.virtual_y += current_vy
        
        if abs(current_vx) > 1.5: 
            self.dir = 1 if current_vx > 0 else -1
            
        is_climbing = state in ["CLIMBING", "CLIMBING_IDLE"]
        is_parkour = state == "PARKOUR"
        is_grappling = state == "GRAPPLING" 
        is_landing = state == "LANDING" 
        is_hovering = state == "HOVER" 
        is_wall_jumping = state == "WALL_JUMP"
        
        is_moving = (state in ["RUNNING", "CLIMBING", "HOVER", "WALL_JUMP"]) and math.hypot(current_vx, current_vy) > 0.5
        t = self.phase
        v_speed = math.hypot(current_vx, current_vy)
        self.phase += v_speed * 0.035 

        v_head = QPointF(self.virtual_x, self.virtual_y) 
        v_chest_base = v_head + QPointF(0, self.h * 0.2)
        v_hips_base = v_chest_base + QPointF(0, self.h * 0.45)
        
        if state == "RUNNING": v_chest, v_hips = ActionRun.calculate_v_nodes(self, v_head, v_chest_base, v_hips_base, t, current_vx, current_vy)
        elif is_climbing: v_chest, v_hips = ActionClimb.calculate_v_nodes(self, v_chest_base, v_hips_base, t, current_vx, current_vy, is_moving)
        elif is_parkour: v_chest, v_hips = ActionParkour.calculate_v_nodes(self, v_head, v_chest_base, v_hips_base, t, current_vx, current_vy)
        elif is_grappling: v_chest, v_hips = ActionGrapple.calculate_v_nodes(self, v_head, v_chest_base, v_hips_base, t, current_vx, current_vy)
        elif is_landing: v_chest, v_hips = ActionLanding.calculate_v_nodes(self, v_head, v_chest_base, v_hips_base, t, current_vx, current_vy)
        elif is_hovering: v_chest, v_hips = ActionHover.calculate_v_nodes(self, v_head, v_chest_base, v_hips_base, t, current_vx, current_vy)
        elif is_wall_jumping: v_chest, v_hips = ActionWallJump.calculate_v_nodes(self, v_head, v_chest_base, v_hips_base, t, current_vx, current_vy)
        else: v_chest, v_hips = ActionIdle.calculate_v_nodes(self, v_chest_base, v_hips_base, t, current_vx, current_vy)

        apply_grav = not (is_climbing or is_parkour or is_grappling or is_hovering or is_wall_jumping)
        k_core, d_core = 35.0, 0.75
        p_hips = self.n_hips.update(v_hips, k_core, d_core, apply_grav)
        p_chest = self.n_chest.update(v_chest, k_core, d_core, apply_grav)
        p_head = self.n_head.update(v_head, k_core, d_core, apply_grav)

        spine_dx, spine_dy = p_chest.x() - p_hips.x(), p_chest.y() - p_hips.y()
        spine_angle = math.atan2(spine_dy, spine_dx)
        
        if state == "RUNNING": head_lag, flex_amount = ActionRun.get_spine_params(self, t, current_vx, current_vy)
        elif is_climbing: head_lag, flex_amount = ActionClimb.get_spine_params(self, t, current_vx, current_vy, is_moving)
        elif is_parkour: head_lag, flex_amount = ActionParkour.get_spine_params(self, t, current_vx, current_vy)
        elif is_grappling: head_lag, flex_amount = ActionGrapple.get_spine_params(self, t, current_vx, current_vy)
        elif is_landing: head_lag, flex_amount = ActionLanding.get_spine_params(self, t, current_vx, current_vy)
        elif is_hovering: head_lag, flex_amount = ActionHover.get_spine_params(self, t, current_vx, current_vy)
        elif is_wall_jumping: head_lag, flex_amount = ActionWallJump.get_spine_params(self, t, current_vx, current_vy)
        else: head_lag, flex_amount = ActionIdle.get_spine_params(self, t, current_vx, current_vy)
            
        current_shoulder_dir = 1 if (is_climbing or is_wall_jumping) else self.dir
        sh_l, sh_r = p_chest + QPointF(-12 * current_shoulder_dir, 5), p_chest + QPointF(12 * current_shoulder_dir, 5)

        if is_climbing: f_l, f_r, h_l, h_r = ActionClimb.calculate_limbs(self, t, current_vx, current_vy, target_pos, p_hips, p_chest, sh_l, sh_r, state, is_moving)
        elif state == "RUNNING": f_l, f_r, h_l, h_r = ActionRun.calculate_limbs(self, t, current_vx, current_vy, target_pos, p_hips, p_chest, sh_l, sh_r)
        elif is_parkour: f_l, f_r, h_l, h_r = ActionParkour.calculate_limbs(self, t, current_vx, current_vy, target_pos, p_hips, p_chest, sh_l, sh_r)
        elif is_grappling: f_l, f_r, h_l, h_r = ActionGrapple.calculate_limbs(self, t, current_vx, current_vy, target_pos, p_hips, p_chest, sh_l, sh_r)
        elif is_landing: f_l, f_r, h_l, h_r = ActionLanding.calculate_limbs(self, t, current_vx, current_vy, target_pos, p_hips, p_chest, sh_l, sh_r)
        elif is_hovering: f_l, f_r, h_l, h_r = ActionHover.calculate_limbs(self, t, current_vx, current_vy, target_pos, p_hips, p_chest, sh_l, sh_r)
        elif is_wall_jumping: f_l, f_r, h_l, h_r = ActionWallJump.calculate_limbs(self, t, current_vx, current_vy, target_pos, p_hips, p_chest, sh_l, sh_r)
        else: f_l, f_r, h_l, h_r = ActionIdle.calculate_limbs(self, t, current_vx, current_vy, target_pos, p_hips, p_chest, sh_l, sh_r, state)

        painter.setRenderHint(QPainter.Antialiasing)
        
        if is_hovering:
            self.draw_plasma_flame(painter, [f_l, f_r, h_l, h_r], current_vx, current_vy, t, state)

        pen = QPen(QColor(self.color), self.thickness, Qt.SolidLine)
        pen.setCapStyle(Qt.RoundCap); pen.setJoinStyle(Qt.RoundJoin) 
        painter.setPen(pen)

        head_radius = self.h * 0.2
        p_head_draw = p_chest + QPointF(math.cos(spine_angle+head_lag)*head_radius, math.sin(spine_angle+head_lag)*head_radius - 12)
        neck_base = p_head_draw - QPointF(math.cos(spine_angle+head_lag)*head_radius, math.sin(spine_angle+head_lag)*head_radius)
        
        painter.drawEllipse(p_head_draw, head_radius, head_radius)
        
        spine_len = max(1.0, math.hypot(spine_dx, spine_dy))
        spine_ctrl_x = (p_hips.x() + p_chest.x())/2 + (-spine_dy/spine_len) * flex_amount
        spine_ctrl_y = (p_hips.y() + p_chest.y())/2 + (spine_dx/spine_len) * flex_amount
        
        path_spine = QPainterPath()
        path_spine.moveTo(p_hips)
        path_spine.quadTo(QPointF(spine_ctrl_x, spine_ctrl_y), p_chest)
        path_spine.lineTo(neck_base) 
        painter.drawPath(path_spine)

        self.safe_ik_limb(painter, p_hips, f_l, self.leg_len_up, self.leg_len_low, 1 if (is_climbing or is_wall_jumping) else -self.dir)
        self.safe_ik_limb(painter, p_hips, f_r, self.leg_len_up, self.leg_len_low, -1 if (is_climbing or is_wall_jumping) else -self.dir)
        self.safe_ik_limb(painter, sh_l, h_l, self.arm_len_up, self.arm_len_low, -1 if (is_climbing or is_wall_jumping) else self.dir)
        self.safe_ik_limb(painter, sh_r, h_r, self.arm_len_up, self.arm_len_low, 1 if (is_climbing or is_wall_jumping) else -self.dir)

    def draw_plasma_flame(self, painter, points, vx, vy, t, state):
        painter.setPen(Qt.NoPen)
        flicker = 3.0 * math.sin(t * 15.0)
        
        stage = getattr(self, 'hover_seq_stage', "IDLE")
        is_boosting = stage == "START_SEQUENCE"
        is_braking = stage == "BRAKING"

        color_inner = QColor(180, 255, 255, 255) if is_boosting else QColor(150, 255, 255, 200)
        color_outer = QColor(0, 150, 255, 180) if is_boosting else QColor(0, 229, 255, 80)

        if is_braking:
            color_inner = QColor(255, 180, 100, 255) 
            color_outer = QColor(255, 80, 0, 180)

        size_mul = 2.5 if is_boosting else (1.8 if is_braking else 1.2)
        flame_len = 70.0 if is_boosting else (50.0 if is_braking else 40.0)

        v_mag = max(1.0, math.hypot(vx, vy))
        dx, dy = -vx / v_mag, -vy / v_mag
        if is_braking:
            dx, dy = -dx, -dy
            
        if v_mag < 2.0 and not is_braking:
            dx, dy = 0, 1.0 

        for pt in points:
            tip_x = pt.x() + dx * flame_len
            tip_y = pt.y() + dy * flame_len + 5 
            
            px, py = -dy, dx 

            path = QPainterPath()
            path.moveTo(pt + QPointF(px * 4 * size_mul, py * 4 * size_mul))
            path.lineTo(tip_x, tip_y)
            path.lineTo(pt - QPointF(px * 4 * size_mul, py * 4 * size_mul))
            path.closeSubpath()
            
            painter.setBrush(color_outer); painter.drawPath(path)
            painter.setBrush(color_inner); painter.drawEllipse(pt, 5.0 * size_mul + flicker, 5.0 * size_mul + flicker)
            
        painter.setBrush(Qt.NoBrush)