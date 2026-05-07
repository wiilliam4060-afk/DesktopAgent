# Desktop_Agent/ui/stickman_engine/actions/action_landing.py
import math
from PyQt5.QtCore import QPointF

class ActionLanding:
    @staticmethod
    def calculate_v_nodes(agent, v_head, v_chest_base, v_hips_base, t, current_vx, current_vy):
        # 🌟 重心极度下压：不压下去手永远摸不到地！
        ground = agent.ground_line - agent.thickness / 2
        
        # 骨盆沉到底，胸口贴近膝盖
        v_hips = QPointF(v_hips_base.x() - 15 * agent.dir, ground - 35)
        v_chest = QPointF(v_hips.x() + 25 * agent.dir, ground - 70)
        return v_chest, v_hips

    @staticmethod
    def get_spine_params(agent, t, current_vx, current_vy):
        # 低头弓背，承受巨大的下落冲击力
        head_lag = 0.5 * agent.dir
        flex_amount = 35 * agent.dir 
        return head_lag, flex_amount

    @staticmethod
    def calculate_limbs(agent, t, current_vx, current_vy, target_pos, p_hips, p_chest, sh_l, sh_r):
        ground = agent.ground_line - agent.thickness / 2
        
        # 🌟 标准单膝跪地
        # 后脚（拖在后方，IK自然折叠出跪地的姿势）
        f_r = QPointF(p_hips.x() - 40 * agent.dir, ground)
        # 前脚（踩在身体前方支撑）
        f_l = QPointF(p_hips.x() + 35 * agent.dir, ground)
        
        # 🌟 超英铁拳
        # 一手死死砸在重心正前方的地板上
        h_r = QPointF(p_chest.x() + 15 * agent.dir, ground)
        # 另一只手向斜后方高高扬起甩动
        h_l = sh_l + QPointF(-55 * agent.dir, -65)
        
        agent.smooth_r_hand = h_r
        return f_l, f_r, h_l, h_r