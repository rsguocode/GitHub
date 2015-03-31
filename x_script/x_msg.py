# $Id: x_msg.py 175608 2015-03-21 09:01:26Z ycwang@NETEASE.COM $
# -*- coding:GBK -*-

"""
���ݻ������� Python �е����� Ĭ��ֵ ��Сֵ ���ֵ ��ռ�ֽ�
b integer 0 -128 127 1
B integer 0 0 255 1
h integer 0 -32768 32767 2
H integer 0 0 65535 2
i integer 0 -2147483648 2147483647 4
I integer 0 0 4294967295 4
f float 0.0 4
d double 0.0 8
s string ''

�ṩ�� list ���ͣ�
List ���� ����
blist list ��ÿ��Ԫ���� b ����
Blist list ��ÿ��Ԫ���� B ����
hlist list ��ÿ��Ԫ���� h ����
Hlist list ��ÿ��Ԫ���� H ����
ilist list ��ÿ��Ԫ���� i ����
Ilist list ��ÿ��Ԫ���� I ����
flist list ��ÿ��Ԫ���� f ����
dlist list ��ÿ��Ԫ���� d ����
slist list ��ÿ��Ԫ���� s ����
msglist List ��ÿ��Ԫ�����Զ������ͣ�
����ÿ��Ԫ���ǲ�һ�����Զ������͡�
�����Զ�����Ϣ ���ͬ�� msglist

ע�⣺
1) ��Ϣ���ƣ�������һ�����ȴ��� 1 ���ַ������Ҳ��������ϵ� List ����������ͬ��
2) ���� integer ���ͣ������������� float�� SDK �᳢�԰���ת�� int��
3) ���� float ���ͣ�����Ϣ����ٽ���󣬻���һ�����벻Ҫʹ��"==" �����жϣ�
��Ǳ�Ҫ�����Ƽ�ʹ�� float ���͡�
"""

MSG = {

########## �ͻ��˷�����������ָ�� ######
# �������������������һ�δ�����
"c_send_big_data_to_server": {
	"flag": "B",
	"tag": "s",
	"filename": "s",
	"data": "s",
},

"c_ping": {
	"time" : "d",
},

"c_game_init_ok": {
},

"c_gm_cmd": {
	"cmd_str" : "s",
},

"c_ready_to_load_stage": {
},

"c_load_stage_ok": {
},

# ���ֱ����������
# ����һ����������Ʒҳ
"c_item_page":{
	"bag_id": "I",
	"pidx": "B",
},

# �������Ʒ���ŵ�����һ��λ�ã��������κα������ͺ��κ�ҳ֮�������
"c_item_move": {
	"src_bag_id": "I",
	"src_pidx": "B",
	"src_sidx": "B",
	
	"dst_bag_id": "I",
	"dst_just_add": "B", # ����������Ϊ1�����ʾdst_pidx��dst_sidx�ɷ������Զ��ҳ�
	"dst_pidx": "B",
	"dst_sidx": "B",
	
	"bind_confirmed": "B", # ����������Ϊ1�����ʾͬ���
},

"c_item_delete": {
	"bag_id": "I",
	"pidx": "B",
	"sidx": "B",
},
	
"c_item_use": {
	"bag_id": "I",
	"pidx": "B",
	"sidx": "B",
	"target_pid": "I", # 0Ҳ��ʾ����
	"bind_confirmed": "B", # ����������Ϊ1�����ʾͬ���
	"amount": "H",
},

"s_item_use": {
	"is_ok": "B"
},

"c_item_sort": {
	"bag_id": "I",
},
	
#����
"c_item_sell": {
	"bag_id": "I",
	"pidx": "B",
	"sidx": "B",
	"count": "B",
},

# �����̵�ϵͳ��δ��������ʵ��һ���򵥵Ĺ������ڹ���ʱװ
"c_item_buy": {
	"tid": "I",
},
	
"c_equip_re_create_rune": {
	"bag_id": "I",
	"pidx": "B",
	"sidx": "B",
},
	
"c_equip_absorb": {
	"src_bag_id": "I",
	"src_pidx": "B",
	"src_sidx": "B",	
	"dst_bag_id": "I",
	"dst_pidx": "B",
	"dst_sidx": "B",
},

"c_equip_swap_rune": {
	"src_bag_id": "I",
	"src_pidx": "I",
	"src_sidx": "I",
	
	"dst_bag_id": "I",
	"dst_pidx": "I",
	"dst_sidx": "I",
},
	
"c_equip_save_random": {
	"bag_id": "I",
	"pidx": "B",
	"sidx": "B",	
},

"c_item_base": {
	"bag_id": "I",
	"pidx": "B",
	"sidx": "B",
},
	
# ͬ��״̬
"c_sync": {
	"pid" : "B",
	"ani" : "B",
	"state" : "B",
	"x" : "f",
	"y" : "f",
	"dir" : "b",
	"speed" : "f",
	"vspeed" : "f",
	"acc" : "f",
	"vacc" : "f",
	"prd": "B",
	"seq_id": "B",
	},

"c_sync_town": {
	"dest_x": "f",
},

"c_mm": {
	"data": "s",
},

# NPC�ܻ��ƶ�
"c_npc_hurt": {
	"data": "s", # compressed hit data
},

"c_pvp_player_hurt": {
	"pid": "H",
	"damage": "I", 
	"is_critical": "B",
},

"c_pvp_player_die": {
	"pid": "H",
	"skill_tid": "I",
	"skill_dir": "b"
},

# �뿪��ǰ����
"c_leave_room": {
},

# ����ǰ������
"c_goto_town": {
	"town_id": "b",
},

# ����ǰ����Ϸ
"c_goto_game": {
	"map_id": "H",
	"mode": "B", # ��Ϸģʽ, ��common_consts�ж���
},

# �뿪ս��
"c_leave_game": {
},

# (GM)ǰ��Ŀ�ĵ�
"c_gm_goto_game": {
	"map_id": "H",
	"mode": "B", # 0-��ͨ; 1-��Ӣ
	"jump": "B", # �Ƿ�ֱ����ת
},

"c_goto_login": {
},

# ���봫����
"c_enter_portal": {
	"pid": "I",
},

# ��������Ϊtype�Ŀɽ������б�
"c_task_list": {
	"type": "s",
},
	
"c_task_list_mine": {
},
	
"c_task_accept": {
	"task_id": "I",
},
	
"c_task_cancel": {
	"task_id": "I",
},

"c_task_return": {
	"task_id": "I",
},

# ��Ծ�Ƚ���
"c_get_active_level_prize": {
	"index": "B",
},

#����ע���ʺ�
"c_register_role" :{
	"name" : "s",
	"role_class" : "B",
},

"c_delete_role" :{
	"rid":"Q"
},

#��ɫ��¼
"c_role_login" :{
	"rid":"Q",
},

#���װ������
"c_equip_skill" : {
	"tid" : "I",
	"position" : "B",
},

"c_batch_equip_skill" : {
	"tids" : "Hlist",
},

#��ҽ������
"c_dequip_skill" : {
	"tid" : "I",
},

#�����������
"c_levelup_skill" :{
	"tid" : "I",
},

"c_levelup_passive_skill" :{
	"tid" : "I",
},
	
#������Ҽ����б�
"c_player_skill_list" :{
	"skill_type" : "B",	
},

"c_skill_clear_cd" : {
	"skill_type" : "B",
},

"c_game_end": {
	"reason": "B",
	"score": "H",  # ���ڼ������۵Ĳ���
	"kill_count": "Ilist", # [tid0, count0, tid1, count1, ...]
},

# ����Ŀ�����
"c_activate_obj": {
	"pid": "H",
	"activated": "B", # 0-ȡ������; 1-����
},

"c_new_team": {
	"map_id": "I",
	"mode": "B",
},

"c_join_team": {
	"team_id": "I",
},

"c_leave_team": {
},

"c_team_start": {
},

"c_load_group": {
	"pid": "H",
	"idx": "B",
},

"c_team_list": {
	"map_id": "I",
	"page_begin": "I",
	"page_count": "B",
},

"c_player_ready": {
	"is_ready": "B", # 0-Ϊ׼��; 1-�Ѿ�׼��
},

"c_player_map_data" : {
	
},

"c_enter_field": {
	"field_type": "s",
	"field_attrs": "s",
	"objs": "Hlist",
},

"c_join_pvp": {
	"room_id": "I",
},

"c_emblem_upgrade_main": {
	"idx": "B",		# ���200��
	"level": "B",
	"is_batch": "B",
},

"c_emblem_upgrade_sub": {
	"idx": "B",
	"level": "B",
	"is_batch": "B",
},

"c_emblem_add_gem": {
	"idx": "B",
	"pos": "B",
	"gem_tid": "I",
},
	
"c_emblem_remove_gem": {
	"idx": "B",
	"pos": "B",
},

"c_gem_merge": {
	"tid": "I",
	"merge_all": "B",
},
	
"c_gem_levelup_equiped": {
	"emblem_idx": "B",
	"idx": "B",
},
	
"c_gem_merge_bag_to_max": {
},
	
"c_gem_degrade_trade": {
	"tid": "I",
	"new_tid": "I",
	"trade_all": "B",
},

"c_gem_convert_next_gongming_level": {
	"curr_level": "B",
},
	
"c_fairy_feed_soul": {
	"is_batch": "B",
},

"c_fairy_breed": {
	"style": "B",
},

"c_fairy_save_breed_result": {
},
	
"c_fairy_train": {
	"is_batch": "B",
},

#��ҿ��õĵ�ͼ��Ϣ
"c_map_data": {
	"pidx": "B",
},

"c_buff_sync": {
	"pid": "I",
	"data": "s",
},

"c_arena_start": {
	"rival_id": "B"
},

"c_arena_end": {
	"result": "B"
},

"c_arena_get_prize": {
},

"c_xingzuo_levelup": {
	"tid": "B",
},

"c_tutorial_done": {
	"tid": "B",
},

"c_revive": {
	"pid": "I",
},

"c_ranking_list": {
	"ranking_type": "B",
	"start": "I",
	"end": "I",	
},

"c_do_worship": {
	"ranking_type": "B",
},

"c_worship_reward": {
	
},

# �ʼ�ϵͳ��ز���
"c_mail_insert": {
	"to_rid": "Q",
	"type": "B",
	"subject": "s",
	"body": "s",
	"resources": "s",
	"items": "s",
},

"c_mail_list": {
	"type": "B",
	"index": "I",
	"size": "I",
},

"c_mail_read": {
	"mail_ids": "s",
},

"c_mail_delete": {
	"mail_ids": "s",
},

"c_mail_fetch": {
	"mail_ids": "s",
},

# ��ѯ����������ɫ������
"c_query_role": {
	"rid": "Q",
	"name": "s",
},

# ��ѯϵͳ�Ƽ��ĺ������
# ��ʼ��ѯʱ��{hint_lv=0, hint_pos=0}���в�ѯ��
# ��ѯ��������µ�hint_lv, hint_pos��ʹ��ÿ�β�ѯ�����ͬ��
"c_query_recommend_players": {
	"hint_lv": "b",
	"hint_pos": "I",
	"num": "B",
},

"c_get_relation": {
},

#�򿪱���
"c_open_box": {
	"area_id": "I",
	"box_id": "B",
},

"c_add_friend": {
	"rid": "Q",
},
	
"c_remove_friend": {
	"rid": "Q",
},
	
"c_add_to_blacklist": {
	"rid": "Q",
},
	
"c_remove_from_blacklist": {
	"rid": "Q",
},
	
"c_chat": {
	"channel": "B",		
	"to_id": "Q",		# ���磺�̶�Ϊ0�����᣺����ID��˽�ģ�RID
	"text": "s",		
},

#��ȡ����������
"c_get_stam": {
	"stam_type": "B",
},

# �����޻���
"c_soul_update_link": {
	"slot_idx": "B",
	"soul_tid": "I",
},

# �޻�����
"c_soul_levelup": {
	"tid": "I",
	"grains": "s",
},

"c_soul_rankup": {
	"tid": "I",
},

"c_soul_refresh_colosseum": {
	"refresh_type": "I",
},

"c_soul_fetch": {
	"slot": "I",
},

"c_soul_activate_fete": {
	"fete_id": "I",
},

"c_soul_buy_grain": {
	"tid": "I",
	"amount": "I",
},

"c_soul_challenge_again": {
},

"c_soul_level_down": {
},

# ����һЩ��Ҫ�洢��flag��״̬
"c_save_new_flag_data": {
	"flag": "B",
	"data": "s",
},
	
#ɨ������
"c_wipe_map": {
	"map_id":  "I",
	"wipe_type": "B",
	"is_elite": "B", #�Ƿ�Ӣ
},

"c_buy_res": {
	"buy_type": "B",	
},

# ʱװװ��
"c_costume_equip": {
	"cos_id": "B",
	"part_id": "B",
},

# ����
"c_chest_buy": {
	"chest_id": "b",
	"buy_type": "b", # 0:��ѣ�1:�շ�
	"cnt": "b", # ʹ����ʯ������
},

########## �����������ͻ��˵�ָ�� #####
# ���ڻ�Ӧ�ͻ��˷������Ĵ�����
"s_send_big_data_to_server": {
	"tag": "s",
	"filename": "s",
	"msg": "s", # �����Ϣ�ַ���
},

# ����������ͻ��˷�һ�δ�����
"s_send_big_data_to_client": {
	"flag": "B",
	"tag": "s",
	"filename": "s",
	"data": "s",
},

"s_gm_cmd_result": {
	"cmd": "s", # ԭָ��
	"is_ok": "B", # 0��ʧ�ܣ�1���ɹ�
	"msg": "s",	# ��Ϣ�ַ���
},

"s_fatal_kick": {
	"why": "H", # ԭ��
},

"s_common_kick": {
	"why": "H", # ԭ��
},

# ����ģʽ: ��ҽ��뷿��
"s_player_in": {
	"uid": "I",
	"seat": "B",
	"name": "s",
	"icon": "I",
	"role_class": "B",
	"level": "I",
	"is_ready": "B", # 0-Ϊ׼��; 1-�Ѿ�׼��
	"is_leader": "B", # 0-��ͨ; 1-���� 
	"rtt": "i",
},

# ����ģʽ: ����뿪����	
"s_player_out": {
	"uid": "I",
},

# ���ض��鴴�����
"s_new_team": {
	"is_ok": "I",
	"team_id": "i",
	"mode": "B",
},

# ������ӽ��
"s_join_team": {
	"is_ok": "B",
	"team_id": "I",
},

# �ӳ��ı�
"s_team_leader": {
	"leader_uid": "I",
},
	
"s_ping": {
	"time" : "d",
},

"s_rtt": {
	"rtt": "I",
},

"s_player_rtt": {
	"uid": "I",
	"rtt": "I",
},

# ��һ�ν�����Ϸ��ʼ��
"s_game_init": {
	"map_id": "I",
	"stage_id": "H", # ����ID 
	"pid_base": "H", # ��ʼPID
	"pid_self": "H", # me��PID
	"is_multi": "B", # �Ƿ����ģʽ
	"game_mode":"B", # ��Ϸģʽ
	# [��ѡ]��������, ѡ���Ĭ��ֵ����:
	# {
	# 	"diffi": 1,  # �����Ѷ�
	# 	"def_group": "default",  # ����������
	# 	"enemy_lvl": 0,  # ���˵ȼ��ӳ�
	#   "ex_atk_rate": 0,  # ���˽��������ӳ�: 0~1
	# }
	"game_cfg": "s",

},

# ������ϳ���
"s_game_init_stage_end": {
	"response": "B",
},

# ������������
"s_get_ready_to_load_stage": {
	"transition": "B", # �����л���ʽ
},

"s_load_stage_begin": {
	"stage_id" : "H", # ����ID
},

"s_load_stage_end": {
},

"s_game_start": {
	"time" : "d", # ��Ϸ��ʼ���ж�ʱ
},

"s_enter_area": {
	"time" : "d", # ��Ϸ��ʼ���ж�ʱ
},

#------------------------------------------
# ��Ϸ����ԭ��
#------------------------------------------
# GAME_END_ERROR: ����
# GAME_END_TASK_FAIL: ����ʧ��
# GAME_END_WIN: ʤ��
#-------------------------------------------
"s_game_end": { # ��Ϸ����
	"reason": "B", # ����ԭ��
	"game_time": "f", # ͨ��ʱ��
	# ��Ϸ��������, ������Ϸģʽ����
	"reward": "s",
},

"s_stage_clear": { # �������
},

"s_update_town_players": {
	"delete_list": "Ilist",	# ��Ҫɾ����uid
	"create_list": "s_create_player",	# ��Ҫ������
	"update_list": "s",	# ֻ��Ҫ����[pid0, x0, dir0, pid1, x1, dir1, ...]��y����Ҫ����
},

"s_create_player": {
	"uid":  "I",
	"pid":  "I",  # pid=0, ����ζ���ǿͻ��˶���
	"tid":  "I",
	"seat": "B",
	"born": "B",  # born=1, ����(x,y), ȡ����������
	"face": "b",
	"x": "f",
	"y": "f",
	"name": "s",
	"attrs": "s",
},
	
"s_create_obj": {
	"pid":	"I",
	"tid":	"I",
	"owner":"I", 
	"x":	"f", 
	"y":	"f",
	"attrs":"s", # ����
},

"s_delete_obj": {
	"pid":	"I",
	# ����ɾ����ԭ��, Ŀǰ�õ��ı�ʶ����
	#	0: (Ĭ��) Don't ask why !
	#	1: Leave player's scope
	"reason": "B",
},

# ������������������
"s_produce_monster": {
	"pid":	"I",
	"seed": "H",
	"count":"H",
},
	
"s_npc_sync": {
	"pid": "I",
	"seed": "H",
	"period": "B",
},

# ����
"s_item_info": {
	"tid": "H",
	"quality": "B",
	"can_use": "B",
	"pidx": "B",
	"sidx": "B",
	"bag_id" : "I",
	"amount": "H",
	"base": "s",
},

# ĳ�β�������ĳ���������治�������ĵ��߷����˱仯
"s_item_change_list": {
	"bag_id": "I",
	"items": "s_item_info",
},

# �����б�
"s_item_list": {
	"bag_id": "I",
	"max_page": "B",
	"total_max_slot": "B",
	"pidx": "B",
	"cur_page_max_slot": "B",
	# ֻ��3��ֵ���� common_consts.BAG_EXPAND_STATE_*
	"expand_state": "B", 
	"items": "s_item_info",
},
	
# ֪ͨ�ͻ��˵õ�һ��ȫ�£�֮ǰδӵ�У�����Ʒ
"s_item_add": {
	"pickled_log_list": "s",
},

# ����������־
# ��ʽ��fish_item_bag���ļ�ͷ˵��
"s_item_log_list": {
	"pickled_log_list": "s",
},

#����ڵ�ǰ�������Ľ�ɫ��Ϣ
"s_role_list" :{
	"last_login_rid" : "Q",
	"pickled_role_list" : "s",
},

#ע���ʺŽ��
"s_register_role" :{
	"errcode" : "B",
	"pickled_role_list" : "s"
},

"s_delete_role" :{
	"errcode" : "B",
	"pickled_role_list" : "s",	
},

#�����֪ͨ�ͻ���Ӧ�����ĸ�����
"s_login_room":{
	"room_id" : "i",
	"base": "s",
},

#����˷��ʹ�����Ϣ���ͻ���
"s_error_message" :{
	"code": "I",
	"show_type" : "B",
	"message" : "s",
	"tag" : "s",
},
	
# ��Ӧǰ������
"s_goto_town": {
	"ok": "B",
	"room_id": "B",
},

# ��Ӧǰ����Ϸ
"s_goto_game": {
	"err": "H",
},

# GMģʽ������Ϸ
"s_gm_goto_game": {
	"ok": "B",
	"room_id": "i",
	"game_mode": "B",
},

"s_goto_login": {
},
	
# ���������
"s_activate_obj": {
	"pid": "I",
	"activated": "B", # 0-ȡ������; 1-����
},


#��Ҽ�����Ϣ
"s_skill_info" : {
	"tid" : "I",
	"level" : "I",
	"position" : "B",
},

#��Ҽ����б�
"s_skill_list" : {
	"skills" : "s_skill_info",
	"skill_type" : "B",
},

#��Ҽ��ܸ���
"s_skill_update" : {
	"skills" : "s_skill_info",
	"action" : "s",
},

#������cd���
"s_skill_clear_cd" : {
	"skill_type" : "B",
	"skill_cd" : "I",
	"is_in_cd" : "B",	
},
	
# ����ĳ�����͵�ȫ���ɽ�&�ѽ�����
# msg.task_ids:ȫ���ɽ�����ID
# msg.progress_data:ȫ���ѽ�����Ľ���
# msg.task_done:ȫ���Ѿ���������ID
# loads(msg.progress_data) = [(task_id, ����1, ����2, ����3), ...]
"s_task_list": {
	"type": "s",
	"task_ids": "Hlist",
	"progress_data": "s",
	"task_done": "Hlist",
},
	
# ����Ŀǰ�����ѽ��������
# loads(msg.progress_data) = [(task_id, ����1, ����2, ����3), ...]
"s_task_list_mine": {
	"progress_data": "s"	
},
	
"s_task_accept": {
	"is_ok": "I",
	"task_id": "I",
},
	
"s_task_cancel": {
	"is_ok": "I",
	"task_id": "I",
},

"s_task_return": {
	"is_ok": "I",
	"task_id": "I",
},

# ��������и���
# loads(msg.progress_data) = [(task_id, ����1, ����2, ����3), ...]
"s_task_update": {
	"progress_data": "s",
},

"s_task_pool_init": {
	"type": "s",
	"task_ids": "Hlist",
},
	
# ָʾ�ͻ���ǰ��NPC_ID��
"s_goto_npc": {
	"npc_id": "I",
},
	
# ���س��������
"s_load_group": {
	"pid": "H",
	"idx": "B",
},

"s_team_list": {
	"data": "s",
	"remain_tickets" : "H",
	"page_begin": "H",
	"page_count": "B",
},

"s_player_ready": {
	"uid": "I",
	"is_ready": "B", # 0-Ϊ׼��; 1-�Ѿ�׼��
},

"s_player_map_data" : {
	"map_data" : "s",
},

"s_emblem_upgrade_main": {
	"is_ok": "Blist",
	"idx": "B",		# ���200��
	"level": "Blist",
},

"s_emblem_upgrade_sub": {
	"is_ok": "Blist",
	"idx": "B",
	"level": "B",
},

"s_emblem_add_gem": {
	"is_ok": "B",
	"idx": "B",
	"pos": "B",
	"gem_tid": "I",
},
	
"s_emblem_remove_gem": {
	"is_ok": "B",
	"idx": "B",
	"pos": "B",
},

"s_equip_re_create_rune": {
	"bag_id": "I",
	"pidx": "B",
	"sidx": "B",
	"old_base": "s",
	"new_base": "s",
},
	
"s_equip_absorb": {
	"is_ok": "B",
	"pickled_log_list": "s",
},
	
"s_item_base": {
	"bag_id": "I",
	"pidx": "B",
	"sidx": "B",
	"base": "s"
},

"s_equip_swap_rune": {
	"src_bag_id": "I",
	"src_pidx": "I",
	"src_sidx": "I",
	
	"dst_bag_id": "I",
	"dst_pidx": "I",
	"dst_sidx": "I",
},

"s_fairy_feed_soul": {
	"ball": "Blist",
},

"s_fairy_breed": {
	"attr_deltas": "blist",
},
	
"s_fairy_train": {
	"error_code_list": "Hlist",
	"patterns": "Blist",
	"diamond_train_count": "B",
},

"s_fairy_add_exp": {
	"exp": "I",
},
	
#ͨ�ù���֪ͨ��Ϣ
"s_notice": {
	"msg_type": "B",
	"msg": "s",	
},

"s_sync_unsigned": {
	"idx": "B",
	"val": "I"
},

"s_sync_signed": {
	"idx": "B",
	"val": "i",	
},

"s_sync_float": {
	"idx": "B",
	"val": "f",
},

"s_sync_attr": {
	"pickled_log_list": "s",
},

"s_sync_map_rec": {
	"map_id": "H",
	"attrs": "s",
	"area_star": "B",
},

"s_open_maps": {
	"new_maps": "Hlist",
},

"s_map_data": {
	"pickled_map_data" : "s",
},

"s_gem_convert_next_gongming_level": {
	"is_ok": "B",
	"next_level": "B", 
},

"s_gem_levelup_equiped": {
	"is_ok": "B",
	"emblem_idx": "B",
	"idx": "B",
	"gem_tid": "I",
},
	
"s_levelup_passive_skill": {
	"is_ok": "B",
	"tid": "B",
},

"s_arena_notify": {
	"result": "I",
},

"s_arena_player": {
	"rank": "H",
	"best_rank": "H",
	"tickets": "B",
	"history": "s",
},

"s_arena_enter": {
	"player": "s_arena_player",
	"prize": "s",
	"prize_cd": "H",
},

"s_arena_rival": {
	"name": "s",
	"role_class": "B",
	"rank": "H",
	"level": "H",
	"battle_pow": "I",
},

"s_arena_rivals": {
	"rivals": "s_arena_rival",
},

"s_arena_game_result": {
	"is_win": "B",
	"prize": "s",
},

"s_arena_best_rank": {
	"best_rank": "H",
	"promote": "H",
	"prize": "s",
},

"s_arena_game_end": {
	"reason": "B",
	"player": "s_arena_player",
	"rank_up": "H",
	"prize_cd": "H",
},

"s_arena_get_prize": {
	"prize": "s",
	"prize_cd": "H",
},

"s_xingzuo_levelup": {
	"tid": "B",
	"result": "b",	# �μ�x_common_consts.XINGZUO_LEVELUP_XXX
},

"s_revive": {
	"pid": "I",
	"remain_time": "B",
	"result": "B",
},

"s_ranking_item_info": {
	"uid": "I",
	"rid": "Q",
	"name": "s",
	"role_class": "B",
	"labour_name": "s",
	"attr_value": "Q",
},

"s_ranking_list": {
	"ranking_type": "B",
	"worship_count": "I",
	"me_worship": "I",
	"me_ranking": "I",
	"items": "s_ranking_item_info",
},

"s_do_worship": {
	"ranking_type": "B",
	"result": "B",
},

"s_worship_reward": {
	"rewards": "Hlist",	
},

"s_query_role": {
	"rid": "Q",
	"name": "s",
	"base": "s",
},

"s_query_recommend_players": {
	"players": "slist",
	"hint_lv": "b",
	"hint_pos": "I",
},

"s_open_box": {
	"area_id": "I",
	"box_id": "B",
	"result": "B",
},

# �ʼ�ϵͳ��ز���
"s_mail_info": {
	"base": "s",
},

"s_mail_insert": {
	"is_ok": "B",
	"mail_id": "Q",
},

"s_mail_list": {
	"is_ok": "B",
	"index": "I",
	"size": "I",
	"mail_list": "s_mail_info",
},

"s_mail_read": {
	"is_ok": "B",
	"mail_ids": "s",
},

"s_mail_delete": {
	"is_ok": "B",
	"mail_ids": "s",
},

"s_mail_fetch": {
	"is_ok": "B",
	"mail_ids": "s",
},
####################

"s_get_relation": {
	"base": "s",
},

"s_trace_leak": {
	"dotname_list": "slist",
	"data_list": "slist",
},

"s_add_friend": {
	"is_ok": "B",
	"base": "s",
},
	
"s_remove_friend": {
	"is_ok": "B",
	"rid": "Q",
},
	
"s_add_to_blacklist": {
	"is_ok": "B",
	"base": "s",
},
	
"s_remove_from_blacklist": {
	"is_ok": "B",
	"rid": "Q",
},

"s_chat": {
	"channel": "B",
	"from_id": "Q",		# ������c_chat
	"from_name": "s",
	"from_vip": "B",	# �����ߵ�VIP�ȼ�
	"text": "s",
},

"s_restore": {
	"base": "s",
},

"s_get_stam": {
	"stam_type": "B",
	"result": "B",
},

"s_wipe_map": {
	"result": "B",
	"pickled_log_list": "s",	
},

"s_soul_levelup":{
	"tid": "I",
	"pickled_soul": "s",
	"is_ok": "B",
},

"s_soul_rankup":{
	"tid": "I",
	"pickled_soul": "s",
	"is_ok": "B",
},

"s_soul_update_link":{
	"log": "Ilist",
},

"s_soul_add_stone": {
	"tid": "I",
	"pickled_soul": "s"
},

"s_soul_refresh_colosseum": {
	"colosseum_list": "s",
	"is_ok": "B",
},

"s_soul_fetch": {
	"tid": "I",
	"pickled_soul": "s",
	"is_ok": "I",
},

"s_soul_unlock": {
	"tid_list" : "s",
},

"s_soul_activate_fete": {
	"fete_id": "I",
	"fete_attr_list": "s",
	"is_ok": "I",
},

"s_soul_buy_grain": {
	"tid": "I",
	"is_ok": "B"
},

"s_soul_challenge_again": {
	"err": "H",
},

"s_soul_level_down": {
	"result": "H",
	"down_list": "s",
},

"s_do_daily_work": {
},

"s_buy_res": {
	"result": "H",
	"buy_type": "B",
	"critical": "B",
	"amount": "I",
},

# ʱװ����
"s_costume_expire": {
	"expire": "f",	# ��ʱ��֮ǰ��ʱװȫ������
},

# ʱװװ��
"s_costume_equip": {
	"is_ok": "B",
	"cos_id": "B",
	"part_id": "b",		# -1 ȫ��ʱװ
	"activate": "B",	# �Ƿ�˴μ���
},

"s_get_active_level_prize": {
	"index": "B",
	"is_ok": "B",
},

# ����ÿ������
"s_daily_reset": {
},

# ��������
"s_chest_interface": {
	"chest_ids": "blist",
	"key_values": "blist",
	"free_cnt": "blist",
},

"s_chest_buy": {
	"chest_id": "b",
	"is_ok": "B"
},
	
"s_chest_free": {
	"chest_id": "b", # 0:������1:�ƽ�
},

}