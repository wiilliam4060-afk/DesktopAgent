# Desktop_Agent/ui/stickman_engine/actions/action_grapple.py
import math
from PyQt5.QtCore import QPointF

class ActionGrapple:
    @staticmethod
    def calculate_v_nodes(agent, v_head, v_chest_base, v_hips_base, t, current_vx, current_vy):
        # 荡秋千时身体彻底放松，顺着惯性和重力自然倾斜
        v_chest = v_chest_base + QPointF(current_vx * 0.1, -5)
        v_hips = v_hips_base + QPointF(current_vx * 0.2, 0)
        return v_chest, v_hips

    @staticmethod
    def get_spine_params(agent, t, current_vx, current_vy):
        # 脊柱挺直，随风微仰
        head_lag = -math.sin(t) * 0.05
        flex_amount = 5 * agent.dir
        return head_lag, flex_amount

    @staticmethod
    def calculate_limbs(agent, t, current_vx, current_vy, target_pos, p_hips, p_chest, sh_l, sh_r):
        if hasattr(agent, 'hook_pos') and agent.hook_pos:
            hx, hy = agent.hook_pos.x(), agent.hook_pos.y()
        else:
            hx, hy = p_chest.x(), p_chest.y() - 300

        # 🌟 绝不脱手：将手强制拉向绳索锚点的直线上
        cx, cy = p_chest.x(), p_chest.y()
        dist = max(1.0, math.hypot(hx - cx, hy - cy))
        reach = agent.arm_len_up + agent.arm_len_low - 4 # 手臂拉到极限长度
        
        h_r = QPointF(cx + (hx - cx)/dist * reach, cy + (hy - cy)/dist * reach)
        agent.smooth_r_hand += (h_r - agent.smooth_r_hand) * 0.8 # 极速平滑
        
        h_l = agent.smooth_r_hand + QPointF(-5, 5) # 双手紧握在一起

        # 🌟 修复扭曲：双腿被重力拉直，受风阻向后飘
        f_l = QPointF(p_hips.x() - 10 - current_vx * 0.5, p_hips.y() + 45 - current_vy * 0.1)
        f_r = QPointF(p_hips.x() + 10 - current_vx * 0.5, p_hips.y() + 50 - current_vy * 0.1)

        return f_l, f_r, h_l, h_r