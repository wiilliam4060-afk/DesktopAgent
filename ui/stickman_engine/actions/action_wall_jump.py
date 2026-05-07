# Desktop_Agent/ui/stickman_engine/actions/action_wall_jump.py
import math
from PyQt5.QtCore import QPointF

class ActionWallJump:
    @staticmethod
    def calculate_v_nodes(agent, v_head, v_chest_base, v_hips_base, t, current_vx, current_vy):
        timer = getattr(agent, 'wall_jump_timer', 0)
        wdir = getattr(agent, 'wall_jump_dir', 1) # 1: 墙在左侧，向右跳；-1: 墙在右侧，向左跳

        if timer > 10:
            # 🌟 阶段 1：触墙吸能期。胸口靠近墙面，骨盆下压准备发力
            v_chest = v_head + QPointF(-20 * wdir, agent.h * 0.15)
            v_hips = v_chest + QPointF(-5 * wdir, agent.h * 0.35)
        else:
            # 🌟 阶段 2：爆发腾空期。身体被猛烈推开，胸腔挺起迎向飞行方向
            v_chest = v_head + QPointF(10 * wdir, agent.h * 0.2)
            v_hips = v_chest + QPointF(-15 * wdir, agent.h * 0.45)

        return v_chest, v_hips

    @staticmethod
    def get_spine_params(agent, t, current_vx, current_vy):
        timer = getattr(agent, 'wall_jump_timer', 0)
        wdir = getattr(agent, 'wall_jump_dir', 1)

        if timer > 10:
            # 吸能期：低头看墙脚落点，背部弓起积蓄力量
            head_lag = 0.4 * wdir
            flex_amount = 25 * wdir
        else:
            # 爆发期：猛然转头看向飞行目标，脊柱反向拉伸
            head_lag = -0.5 * wdir
            flex_amount = -15 * wdir
            
        return head_lag, flex_amount

    @staticmethod
    def calculate_limbs(agent, t, current_vx, current_vy, target_pos, p_hips, p_chest, sh_l, sh_r):
        timer = getattr(agent, 'wall_jump_timer', 0)
        wdir = getattr(agent, 'wall_jump_dir', 1) 

        reach_leg = agent.total_leg_len * 0.95
        reach_arm = (agent.arm_len_up + agent.arm_len_low) * 0.95

        # 估算墙壁的绝对坐标点 (考虑线宽避免穿模)
        wall_x = agent.virtual_x - 12 * wdir

        if timer > 10:
            # ==========================================
            # 🌟 真实跑酷：吸能与蓄力
            # ==========================================
            if wdir > 0: # 墙在左侧
                # 左脚(内侧脚)曲腿死死踩在墙面上
                f_l = QPointF(wall_x, p_hips.y() + 15) 
                # 右脚(外侧脚)向后垂下，准备做“提膝”动作
                f_r = QPointF(p_hips.x() + 25, p_hips.y() + reach_leg * 0.7) 
            else:        # 墙在右侧
                f_r = QPointF(wall_x, p_hips.y() + 15) 
                f_l = QPointF(p_hips.x() - 25, p_hips.y() + reach_leg * 0.7) 

            # 一只手按在墙上辅助平衡，另一只手收在胸前准备发力甩出
            h_l = QPointF(wall_x, p_chest.y() - 10) if wdir > 0 else p_chest + QPointF(-20, 20)
            h_r = p_chest + QPointF(20, 20) if wdir > 0 else QPointF(wall_x, p_chest.y() - 10)
            
        else:
            # ==========================================
            # 🌟 真实跑酷：爆发蹬踹与提膝带动 (Knee Drive)
            # ==========================================
            # extension 模拟腿部猛然蹬直的过程 (1.0 代表完全蹬直)
            extension = min(1.0, (10 - timer) / 4.0) 
            
            if wdir > 0:
                # 左脚(踩墙脚)像弹簧一样猛然拉直，将身体推离墙面
                f_l = QPointF(p_hips.x() - reach_leg * extension, p_hips.y() + 10)
                # 右脚(外侧脚)猛烈向上提膝，带动重心起飞
                f_r = QPointF(p_hips.x() + 20, p_hips.y() - 15)
            else:
                f_r = QPointF(p_hips.x() + reach_leg * extension, p_hips.y() + 10)
                f_l = QPointF(p_hips.x() - 20, p_hips.y() - 15)

            # 双手顺着起飞的方向（wdir）猛烈向上方甩出，引导身体重心
            h_l = sh_l + QPointF(reach_arm * 0.9 * wdir, -reach_arm * 0.6)
            h_r = sh_r + QPointF(reach_arm * 0.9 * wdir, -reach_arm * 0.6)

        # 极速平滑右手的 IK 目标点
        agent.smooth_r_hand += (h_r - agent.smooth_r_hand) * 0.6
        return f_l, f_r, h_l, agent.smooth_r_hand