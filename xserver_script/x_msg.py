# $Id: x_msg.py 175608 2015-03-21 09:01:26Z ycwang@NETEASE.COM $
# -*- coding:GBK -*-

"""
数据基本类型 Python 中的类型 默认值 最小值 最大值 所占字节
b integer 0 -128 127 1
B integer 0 0 255 1
h integer 0 -32768 32767 2
H integer 0 0 65535 2
i integer 0 -2147483648 2147483647 4
I integer 0 0 4294967295 4
f float 0.0 4
d double 0.0 8
s string ''

提供的 list 类型：
List 类型 描述
blist list 的每个元素是 b 类型
Blist list 的每个元素是 B 类型
hlist list 的每个元素是 h 类型
Hlist list 的每个元素是 H 类型
ilist list 的每个元素是 i 类型
Ilist list 的每个元素是 I 类型
flist list 的每个元素是 f 类型
dlist list 的每个元素是 d 类型
slist list 的每个元素是 s 类型
msglist List 的每个元素是自定义类型，
可以每个元素是不一样的自定义类型。
其他自定义消息 则等同于 msglist

注意：
1) 消息名称，必须是一个长度大于 1 的字符串，且不能与以上的 List 类型名称相同。
2) 关于 integer 类型，如果您传入的是 float， SDK 会尝试把它转成 int。
3) 关于 float 类型，在消息打包再解包后，会有一定误差，请不要使用"==" 进行判断；
如非必要，不推荐使用 float 类型。
"""

MSG = {

########## 客户端发往服务器的指令 ######
# 用于主动向服务器发送一次大数据
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

# 各种背包操作相关
# 请求一个背包的物品页
"c_item_page":{
	"bag_id": "I",
	"pidx": "B",
},

# 点击起物品，放到另外一个位置（可以在任何背包类型和任何页之间操作）
"c_item_move": {
	"src_bag_id": "I",
	"src_pidx": "B",
	"src_sidx": "B",
	
	"dst_bag_id": "I",
	"dst_just_add": "B", # 如果这个参数为1，则表示dst_pidx和dst_sidx由服务器自动找出
	"dst_pidx": "B",
	"dst_sidx": "B",
	
	"bind_confirmed": "B", # 如果这个参数为1，则表示同意绑定
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
	"target_pid": "I", # 0也表示自身
	"bind_confirmed": "B", # 如果这个参数为1，则表示同意绑定
	"amount": "H",
},

"s_item_use": {
	"is_ok": "B"
},

"c_item_sort": {
	"bag_id": "I",
},
	
#出售
"c_item_sell": {
	"bag_id": "I",
	"pidx": "B",
	"sidx": "B",
	"count": "B",
},

# 购买：商店系统尚未开做，先实现一个简单的购买，用于购买时装
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
	
# 同步状态
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

# NPC受击破盾
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

# 离开当前房间
"c_leave_room": {
},

# 请求前往城镇
"c_goto_town": {
	"town_id": "b",
},

# 请求前往游戏
"c_goto_game": {
	"map_id": "H",
	"mode": "B", # 游戏模式, 在common_consts中定义
},

# 离开战场
"c_leave_game": {
},

# (GM)前往目的地
"c_gm_goto_game": {
	"map_id": "H",
	"mode": "B", # 0-普通; 1-精英
	"jump": "B", # 是否直接跳转
},

"c_goto_login": {
},

# 进入传送门
"c_enter_portal": {
	"pid": "I",
},

# 请求类型为type的可接任务列表
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

# 活跃度奖励
"c_get_active_level_prize": {
	"index": "B",
},

#请求注册帐号
"c_register_role" :{
	"name" : "s",
	"role_class" : "B",
},

"c_delete_role" :{
	"rid":"Q"
},

#角色登录
"c_role_login" :{
	"rid":"Q",
},

#玩家装备技能
"c_equip_skill" : {
	"tid" : "I",
	"position" : "B",
},

"c_batch_equip_skill" : {
	"tids" : "Hlist",
},

#玩家解除技能
"c_dequip_skill" : {
	"tid" : "I",
},

#玩家升级技能
"c_levelup_skill" :{
	"tid" : "I",
},

"c_levelup_passive_skill" :{
	"tid" : "I",
},
	
#请求玩家技能列表
"c_player_skill_list" :{
	"skill_type" : "B",	
},

"c_skill_clear_cd" : {
	"skill_type" : "B",
},

"c_game_end": {
	"reason": "B",
	"score": "H",  # 用于计算评价的参数
	"kill_count": "Ilist", # [tid0, count0, tid1, count1, ...]
},

# 激活目标对象
"c_activate_obj": {
	"pid": "H",
	"activated": "B", # 0-取消激活; 1-激活
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
	"is_ready": "B", # 0-为准备; 1-已经准备
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
	"idx": "B",		# 最多200级
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

#玩家可用的地图信息
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

# 邮件系统相关参数
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

# 查询任意其他角色的属性
"c_query_role": {
	"rid": "Q",
	"name": "s",
},

# 查询系统推荐的好友玩家
# 初始查询时以{hint_lv=0, hint_pos=0}进行查询。
# 查询结果附带新的hint_lv, hint_pos，使得每次查询结果不同。
"c_query_recommend_players": {
	"hint_lv": "b",
	"hint_pos": "I",
	"num": "B",
},

"c_get_relation": {
},

#打开宝箱
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
	"to_id": "Q",		# 世界：固定为0；公会：公会ID；私聊：RID
	"text": "s",		
},

#领取、购买体力
"c_get_stam": {
	"stam_type": "B",
},

# 更新兽魂链
"c_soul_update_link": {
	"slot_idx": "B",
	"soul_tid": "I",
},

# 兽魂升级
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

# 保存一些需要存储的flag的状态
"c_save_new_flag_data": {
	"flag": "B",
	"data": "s",
},
	
#扫荡副本
"c_wipe_map": {
	"map_id":  "I",
	"wipe_type": "B",
	"is_elite": "B", #是否精英
},

"c_buy_res": {
	"buy_type": "B",	
},

# 时装装备
"c_costume_equip": {
	"cos_id": "B",
	"part_id": "B",
},

# 宝箱
"c_chest_buy": {
	"chest_id": "b",
	"buy_type": "b", # 0:免费；1:收费
	"cnt": "b", # 使用钻石的数量
},

########## 服务器发往客户端的指令 #####
# 用于回应客户端发过来的大数据
"s_send_big_data_to_server": {
	"tag": "s",
	"filename": "s",
	"msg": "s", # 结果信息字符串
},

# 用于主动向客户端发一次大数据
"s_send_big_data_to_client": {
	"flag": "B",
	"tag": "s",
	"filename": "s",
	"data": "s",
},

"s_gm_cmd_result": {
	"cmd": "s", # 原指令
	"is_ok": "B", # 0，失败；1，成功
	"msg": "s",	# 信息字符串
},

"s_fatal_kick": {
	"why": "H", # 原因
},

"s_common_kick": {
	"why": "H", # 原因
},

# 多人模式: 玩家进入房间
"s_player_in": {
	"uid": "I",
	"seat": "B",
	"name": "s",
	"icon": "I",
	"role_class": "B",
	"level": "I",
	"is_ready": "B", # 0-为准备; 1-已经准备
	"is_leader": "B", # 0-普通; 1-房主 
	"rtt": "i",
},

# 多人模式: 玩家离开房间	
"s_player_out": {
	"uid": "I",
},

# 返回队伍创建结果
"s_new_team": {
	"is_ok": "I",
	"team_id": "i",
	"mode": "B",
},

# 返回组队结果
"s_join_team": {
	"is_ok": "B",
	"team_id": "I",
},

# 队长改变
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

# 第一次进入游戏初始化
"s_game_init": {
	"map_id": "I",
	"stage_id": "H", # 区域ID 
	"pid_base": "H", # 初始PID
	"pid_self": "H", # me的PID
	"is_multi": "B", # 是否多人模式
	"game_mode":"B", # 游戏模式
	# [可选]启动参数, 选项和默认值如下:
	# {
	# 	"diffi": 1,  # 副本难度
	# 	"def_group": "default",  # 启动场景组
	# 	"enemy_lvl": 0,  # 敌人等级加成
	#   "ex_atk_rate": 0,  # 敌人进攻欲望加成: 0~1
	# }
	"game_cfg": "s",

},

# 加载完毕场景
"s_game_init_stage_end": {
	"response": "B",
},

# 场景加载流程
"s_get_ready_to_load_stage": {
	"transition": "B", # 区域切换方式
},

"s_load_stage_begin": {
	"stage_id" : "H", # 区域ID
},

"s_load_stage_end": {
},

"s_game_start": {
	"time" : "d", # 游戏开始进行对时
},

"s_enter_area": {
	"time" : "d", # 游戏开始进行对时
},

#------------------------------------------
# 游戏结束原因
#------------------------------------------
# GAME_END_ERROR: 错误
# GAME_END_TASK_FAIL: 任务失败
# GAME_END_WIN: 胜利
#-------------------------------------------
"s_game_end": { # 游戏结束
	"reason": "B", # 结束原因
	"game_time": "f", # 通关时间
	# 游戏结算数据, 根据游戏模式而变
	"reward": "s",
},

"s_stage_clear": { # 区域完成
},

"s_update_town_players": {
	"delete_list": "Ilist",	# 需要删除的uid
	"create_list": "s_create_player",	# 需要创建的
	"update_list": "s",	# 只需要更新[pid0, x0, dir0, pid1, x1, dir1, ...]，y不需要更新
},

"s_create_player": {
	"uid":  "I",
	"pid":  "I",  # pid=0, 则意味着是客户端对象
	"tid":  "I",
	"seat": "B",
	"born": "B",  # born=1, 忽略(x,y), 取场景出生点
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
	"attrs":"s", # 属性
},

"s_delete_obj": {
	"pid":	"I",
	# 对像被删除的原因, 目前用到的标识如下
	#	0: (默认) Don't ask why !
	#	1: Leave player's scope
	"reason": "B",
},

# 怪物生成器创建怪物
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

# 道具
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

# 某次操作导致某个背包里面不定个数的道具发生了变化
"s_item_change_list": {
	"bag_id": "I",
	"items": "s_item_info",
},

# 道具列表
"s_item_list": {
	"bag_id": "I",
	"max_page": "B",
	"total_max_slot": "B",
	"pidx": "B",
	"cur_page_max_slot": "B",
	# 只有3种值，见 common_consts.BAG_EXPAND_STATE_*
	"expand_state": "B", 
	"items": "s_item_info",
},
	
# 通知客户端得到一个全新（之前未拥有）的物品
"s_item_add": {
	"pickled_log_list": "s",
},

# 操作操作日志
# 格式见fish_item_bag的文件头说明
"s_item_log_list": {
	"pickled_log_list": "s",
},

#玩家在当前服务器的角色信息
"s_role_list" :{
	"last_login_rid" : "Q",
	"pickled_role_list" : "s",
},

#注册帐号结果
"s_register_role" :{
	"errcode" : "B",
	"pickled_role_list" : "s"
},

"s_delete_role" :{
	"errcode" : "B",
	"pickled_role_list" : "s",	
},

#服务端通知客户端应进入哪个房间
"s_login_room":{
	"room_id" : "i",
	"base": "s",
},

#服务端发送错误消息给客户端
"s_error_message" :{
	"code": "I",
	"show_type" : "B",
	"message" : "s",
	"tag" : "s",
},
	
# 响应前往城镇
"s_goto_town": {
	"ok": "B",
	"room_id": "B",
},

# 响应前往游戏
"s_goto_game": {
	"err": "H",
},

# GM模式进入游戏
"s_gm_goto_game": {
	"ok": "B",
	"room_id": "i",
	"game_mode": "B",
},

"s_goto_login": {
},
	
# 激活场景对象
"s_activate_obj": {
	"pid": "I",
	"activated": "B", # 0-取消激活; 1-激活
},


#玩家技能信息
"s_skill_info" : {
	"tid" : "I",
	"level" : "I",
	"position" : "B",
},

#玩家技能列表
"s_skill_list" : {
	"skills" : "s_skill_info",
	"skill_type" : "B",
},

#玩家技能更新
"s_skill_update" : {
	"skills" : "s_skill_info",
	"action" : "s",
},

#玩家清楚cd结果
"s_skill_clear_cd" : {
	"skill_type" : "B",
	"skill_cd" : "I",
	"is_in_cd" : "B",	
},
	
# 返回某个类型的全部可接&已接任务
# msg.task_ids:全部可接任务ID
# msg.progress_data:全部已接任务的进度
# msg.task_done:全部已经完结的任务ID
# loads(msg.progress_data) = [(task_id, 进度1, 进度2, 进度3), ...]
"s_task_list": {
	"type": "s",
	"task_ids": "Hlist",
	"progress_data": "s",
	"task_done": "Hlist",
},
	
# 返回目前所有已接任务进度
# loads(msg.progress_data) = [(task_id, 进度1, 进度2, 进度3), ...]
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

# 任务进度有更新
# loads(msg.progress_data) = [(task_id, 进度1, 进度2, 进度3), ...]
"s_task_update": {
	"progress_data": "s",
},

"s_task_pool_init": {
	"type": "s",
	"task_ids": "Hlist",
},
	
# 指示客户端前往NPC_ID处
"s_goto_npc": {
	"npc_id": "I",
},
	
# 加载场景物件组
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
	"is_ready": "B", # 0-为准备; 1-已经准备
},

"s_player_map_data" : {
	"map_data" : "s",
},

"s_emblem_upgrade_main": {
	"is_ok": "Blist",
	"idx": "B",		# 最多200级
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
	
#通用滚动通知消息
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
	"result": "b",	# 参见x_common_consts.XINGZUO_LEVELUP_XXX
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

# 邮件系统相关参数
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
	"from_id": "Q",		# ↑参照c_chat
	"from_name": "s",
	"from_vip": "B",	# 发送者的VIP等级
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

# 时装过期
"s_costume_expire": {
	"expire": "f",	# 此时间之前的时装全部过期
},

# 时装装备
"s_costume_equip": {
	"is_ok": "B",
	"cos_id": "B",
	"part_id": "b",		# -1 全套时装
	"activate": "B",	# 是否此次激活
},

"s_get_active_level_prize": {
	"index": "B",
	"is_ok": "B",
},

# 重置每日数据
"s_daily_reset": {
},

# 开启宝箱
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
	"chest_id": "b", # 0:白银；1:黄金
},

}