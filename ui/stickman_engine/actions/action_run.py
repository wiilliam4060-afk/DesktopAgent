# Desktop_Agent/ui/stickman_engine/actions/action_run.py
import math
from PyQt5.QtCore import QPointF

class ActionRun:
    @staticmethod
    def calculate_v_nodes(agent, v_head, v_chest_base, v_hips_base, t, current_vx, current_vy):
        v_head.setY(agent.virtual_y + abs(math.sin(t)) * 5)
        braking_squat = abs(agent.smooth_ax) * 4.0 if (current_vx * agent.smooth_ax < 0) else 0
        lean_x = current_vx * 1.5 + agent.smooth_ax * 15.0
        torso_squash = -math.sin(t * 2.0) * 8
        v_chest = v_head + QPointF(-current_vx * 0.3, agent.h * 0.2 + torso_squash/2)
        v_hips = v_chest + QPointF(-lean_x, agent.h * 0.45 + torso_squash/2 + braking_squat)
        return v_chest, v_hips

    @staticmethod
    def get_spine_params(agent, t, current_vx, current_vy):
        head_lag = -math.cos(t * 2.0) * 0.2
        flex_amount = -15 * agent.dir * (abs(current_vx)/25.0)
        return head_lag, flex_amount

    @staticmethod
    def calculate_limbs(agent, t, current_vx, current_vy, target_pos, p_hips, p_chest, sh_l, sh_r):
        stride = 95 + abs(current_vx) * 0.8
        lift = 60 
        # 🌟 修复：抬高脚底板，防止画笔穿模
        ground_y = agent.ground_line - agent.thickness / 2
        
        f_l = QPointF(p_hips.x() - math.cos(t)*stride*agent.dir, ground_y - max(0, math.sin(t))*lift)
        f_r = QPointF(p_hips.x() - math.cos(t+3.14)*stride*agent.dir, ground_y - max(0, math.sin(t+3.14))*lift)
        
        arm_swing_x = 65 + abs(current_vx) * 0.8
        h_l = QPointF(p_chest.x() - math.cos(t+3.14)*arm_swing_x*agent.dir, p_chest.y() + 25 + math.cos(t+3.14)*35)
        h_r = QPointF(p_chest.x() - math.cos(t)*arm_swing_x*agent.dir, p_chest.y() + 25 + math.cos(t)*35)
        agent.smooth_r_hand = h_r
        return f_l, f_r, h_l, h_r