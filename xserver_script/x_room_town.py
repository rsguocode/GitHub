# $Id: x_room_town.py 175291 2015-03-19 05:40:27Z ycwang@NETEASE.COM $
# -*- coding: gbk -*-
import time
import random
import datetime
import struct
import weakref
import x_world_town
import x_gmcmd
import x_consts
import x_misc_consts
import x_common_consts
import x_common_util
import x_serialize
import x_task_cond
import x_big_data
import x_big_data_callback
import x_room_common_service_base
import x_map_data
import x_item_bag
import x_text
import x_game_reward
import x_vip_data


class CRoom(x_room_common_service_base.CRoom):

	ROOM_TAG = "town"
	
	def on_create(self):
		self.gmcmd = x_gmcmd.CGmCmd(self)
		# 用于处理用户传过来的大数据
		self._big_data = x_big_data.CBigData()
		self._big_data.register_callbacks({
			"update": x_big_data_callback.update_one,
			"reload": x_big_data_callback.reload_one,
			"update_many": x_big_data_callback.update_many,
			"reload_many": x_big_data_callback.reload_many,
			"map": x_big_data_callback.reload_map,
			"restore": x_big_data_callback.restore,
		})

		# 持有强引用
		self.uid_map_lazy = {}
		# 管理座位号的分配/回收
		self.seat_idx = 0
		self.seat_cache = []
		# 当前组队列表
		self.all_teams = {}
		self.teams_of_map = {}
		# 当前PVP列表
		self.all_pvp_rooms = set()
		# 玩家的等级分布（快速匹配的需要）
		self.player_num_by_level = [0] * 100
		self.player_ref_by_level = [None] * 100
		# 城镇时钟控制
		self.time_delta = datetime.timedelta()

		# 创建world
		stage_id = self.get_stage_id()
		world = x_world_town.CWorld(self)
		for msg in world.WORLD_MESSAGE:
			self.msg_callback[msg] = getattr(world, "on_" + msg)
		self.world = world
		world.load_town_stage(stage_id)

		self.cghall_set_static_room_ready()

	def cghall_clean(self):
		self._big_data.destroy()
		self.uid_map_lazy.clear()
		self.uid_map_lazy = None
		super(CRoom, self).cghall_clean()

	def init_msg_callback(self):
		super(CRoom, self).init_msg_callback()
		# 游戏中协议
		self.msg_callback.update({
		# 房间状态下的协议
		"c_gm_cmd": self.on_c_gm_cmd,
		"c_send_big_data_to_server": self.on_c_send_big_data_to_server,
		"c_leave_room": self.on_c_leave_room,
		"c_leave_game": self.on_c_leave_game,
		"c_goto_town": self.on_c_goto_town,
		"c_goto_game": self.on_c_goto_game,
		"c_gm_goto_game": self.on_c_gm_goto_game,
		"c_goto_login": self.on_c_goto_login,
		"c_team_list": self.on_c_team_list,
		# 单人游戏协议
		"c_game_end": self.on_c_game_end,
		"c_revive": self.on_c_revive,
		# 任务相关协议
		"c_task_list": self.on_c_task_list,
		"c_task_list_mine": self.on_c_task_list_mine,
		"c_task_accept": self.on_c_task_accept,
		"c_task_cancel": self.on_c_task_cancel,
		"c_task_return": self.on_c_task_return,
		"c_get_active_level_prize": self.on_c_get_active_level_prize,
		
		"c_new_team": self.on_c_new_team,
		"c_join_team": self.on_c_join_team,
		"c_join_pvp": self.on_c_join_pvp,
		"c_item_page" : self.on_c_item_page,
		"c_item_use" : self.on_c_item_use,
		"c_item_sort" : self.on_c_item_sort,
		"c_item_sell": self.on_c_item_sell,
		"c_item_base": self.on_c_item_base,
		"c_item_buy": self.on_c_item_buy,
		# 邮件相关协议
		"c_mail_insert": self.on_c_mail_insert,
		"c_mail_list": self.on_c_mail_list,
		"c_mail_read": self.on_c_mail_read,
		"c_mail_delete": self.on_c_mail_delete,
		"c_mail_fetch": self.on_c_mail_fetch,

		# 兽魂相关协议
		"c_soul_update_link": self.on_c_soul_update_link,
		"c_soul_levelup": self.on_c_soul_levelup,
		"c_soul_rankup": self.on_c_soul_rankup,
		"c_soul_refresh_colosseum": self.on_c_soul_refresh_colosseum,
		"c_soul_fetch": self.on_c_soul_fetch,
		"c_soul_activate_fete": self.on_c_soul_activate_fete,
		"c_soul_buy_grain": self.on_c_soul_buy_grain,
		"c_soul_challenge_again": self.on_c_soul_challenge_again,
		"c_soul_level_down": self.on_c_soul_level_down,

		"c_equip_re_create_rune": self.on_c_equip_re_create_rune,
		"c_equip_absorb": self.on_c_equip_absorb,
		"c_equip_save_random": self.on_c_equip_save_random,
		"c_equip_swap_rune": self.on_c_equip_swap_rune,
		
		"c_emblem_upgrade_main": self.on_c_emblem_upgrade_main,
		"c_emblem_upgrade_sub": self.on_c_emblem_upgrade_sub,
		"c_emblem_add_gem": self.on_c_emblem_add_gem,
		"c_emblem_remove_gem": self.on_c_emblem_remove_gem,

		"c_gem_merge": self.on_c_gem_merge,
		"c_gem_levelup_equiped": self.on_c_gem_levelup_equiped,
		"c_gem_merge_bag_to_max": self.on_c_gem_merge_bag_to_max,
		"c_gem_degrade_trade": self.on_c_gem_degrade_trade,
		"c_gem_convert_next_gongming_level": self.on_c_gem_convert_next_gongming_level,
		
		"c_fairy_feed_soul": self.on_c_fairy_feed_soul,
		"c_fairy_breed": self.on_c_fairy_breed,
		"c_fairy_save_breed_result": self.on_c_save_breed_result,
		"c_fairy_train": self.on_c_fairy_train,

		"c_xingzuo_levelup": self.on_c_xingzuo_levelup,
		
		"c_equip_skill" : self.on_c_equip_skill,
		"c_batch_equip_skill" : self.on_c_batch_equip_skill,
		"c_dequip_skill" : self.on_c_dequip_skill,
		"c_levelup_skill" : self.on_c_levelup_skill,
		"c_levelup_passive_skill": self.on_c_levelup_passive_skill,
		"c_player_skill_list" : self.on_c_player_skill_list,
		"c_skill_clear_cd" : self.on_c_skill_clear_cd,
		"c_player_map_data" : self.on_c_player_map_data,
		"c_map_data" : self.on_c_map_data,
		"c_tutorial_done": self.on_c_tutorial_done,

		"c_query_recommend_players": self.on_c_query_recommend_players,
		
		"c_add_friend": self.on_c_add_friend,
		"c_remove_friend": self.on_c_remove_friend,
		"c_add_to_blacklist": self.on_c_add_to_blacklist,
		"c_remove_from_blacklist": self.on_c_remove_from_blacklist,
		"c_open_box": self.on_c_open_box,
		"c_get_stam": self.on_c_get_stam,
		"c_wipe_map": self.on_c_wipe_map,
		"c_buy_res": self.on_c_buy_res,
		
		"c_costume_equip": self.on_c_costume_equip,
		
		"c_save_new_flag_data": self.on_c_save_new_flag_data,
		
		# 宝箱系统
		"c_chest_buy": self.on_c_chest_buy,
		})
		
	def init_msg_callback_r2r(self):
		super(CRoom, self).init_msg_callback_r2r()
		self.msg_callback_r2r.update({
		"rc_del_town_player": self.on_rc_del_town_player,
		"rs_do_daily_work": self.on_rs_do_daily_work,
		"rc_update_team": self.on_rc_update_team,
		"rc_team_player_count": self.on_rc_team_player_count,
		"rc_remove_team": self.on_rc_remove_team,
		"rc_time_adv": self.on_rc_time_adv,

		#邮件模块相关协议
		"rs_mail_insert": self.on_rs_mail_insert,
		"rs_mail_list": self.on_rs_mail_list,
		"rs_mail_read": self.on_rs_mail_read,
		"rs_mail_delete": self.on_rs_mail_delete,
		"rs_mail_fetch": self.on_rs_mail_fetch,

		"rs_add_friend": self.on_rs_add_friend,
		"rs_add_to_blacklist": self.on_rs_add_to_blacklist,
		"rs_remove_friend": self.on_rs_remove_friend,
		"rs_remove_from_blacklist": self.on_rs_remove_from_blacklist,
		"rs_arena_check_prize": self.on_rs_arena_check_prize,
		})

	def add_player_level_ref(self, player):
		level = player.level
		extend_count = (level - len(self.player_num_by_level) + 1)
		if extend_count > 0:
			self.player_num_by_level.extend([0] * extend_count)
			self.player_ref_by_level.extend([None] * extend_count)
		player.town_clone_level = level
		self.player_num_by_level[level] += 1
		if self.player_ref_by_level[level] is None:
			self.player_ref_by_level[level] = []
		self.player_ref_by_level[level].append(weakref.ref(player))
	
	def remove_player_level_ref(self, player):
		import x_util
		level = player.town_clone_level
		self.player_num_by_level[level] -= 1
		ref_list = self.player_ref_by_level[level]
		if len(ref_list) >= 2 * self.player_num_by_level[level]:
			for _, _ in x_util.list_shrink_iter(ref_list, 0, x_util.is_dead_ref):
				pass
				
	def get_recommend_players(self, ref_player, num=10, max_range=50, hint=(0,0)):
		import x_util
		hint_lv, hint_pos = hint
		players = []

		if abs(hint_lv) <= max_range:
			end_hint_lv = hint_lv
		else:
			end_hint_lv = -max_range
		
		while len(players) < num:
			
			lv = hint_lv + ref_player.level
			
			if 0 <= lv < len(self.player_ref_by_level) \
				and self.player_ref_by_level[lv] is not None:
				
				ref_list = self.player_ref_by_level[lv]
				for hint_pos, ref in x_util.list_shrink_iter(ref_list, hint_pos, x_util.is_dead_ref):
					player = ref()
					# import log
					# log.info("id(player) = %d" % id(player))
					# 不在这里判断friend或者blacklist，每次多抽一些人回去给客户端
					# 以弥补不合适的玩家数量，若超出，则客户端可以缓存超过的部分
					# 若本地缓存超过需要请求的上限，则下次不需要请求。
					#if ref_player.relation.is_friend(player):
					is_friend_or_blacklist_or_self = False
					if not is_friend_or_blacklist_or_self:
						players.append(player)
						if len(players) >= num:
							return players, (hint_lv, hint_pos + 1)

			hint_pos = 0				
			if hint_lv == 0:
				hint_lv = 1
			elif hint_lv > 0:
				hint_lv = -hint_lv
			else:
				hint_lv = -hint_lv + 1
				if hint_lv > max_range: hint_lv = 0
				if hint_lv == end_hint_lv: break
				
		return players, (hint_lv, hint_pos)
	
	def get_stage_id(self):
		town_index = self.game_mode - x_common_consts.GAMEMODE_TOWN0
		return x_common_consts.STAGE_TOWN[town_index]
	
	def get_town_id(self):
		return self.game_mode - x_common_consts.GAMEMODE_TOWN0
	
	def get_broadcast_set_for(self, target):
		result = []
		for player in self.uid_map_lazy.itervalues():
			if player.uid == target.uid or len(result) >= 5:
				continue
			result.append(player.uid)
		
		return result
	
	def sync_player_for(self, target):
		new_set = self.get_broadcast_set_for(target)
		old_set = target.sync_set
		
		delete_list = []
		create_list = []
		update_list = []
		
		for uid in old_set:
			if uid not in new_set:
				delete_list.append(uid)
				
		for uid in new_set:
			player = self.uid_map_lazy[uid]
			if uid in old_set:
				update_list.extend((player.pid, player.x, player.d, x_serialize.dumps(player.get_costume_id())))
			else:
				attrs = x_serialize.dumps_with_coreobj( player.get_create_attr_remote_town() )
				msg = self.msg_mgr.s_create_player(uid=uid, pid=player.pid,
					tid=player.tid, name=player.name, x=player.x, y=player.y,
					face=player.d, attrs=attrs)
				create_list.append(msg)
		target.send_to_self("s_update_town_players", delete_list=delete_list,
							create_list=create_list, update_list=x_serialize.dumps(update_list))
		target.sync_set = new_set
		
	def on_player_enter_room(self, room_player):
		# 重新发送玩家数据
		if room_player.cookie.restore:
			room_player.cookie.restore = False
			room_player.send_to_self("s_restore", base=room_player.get_client_base_string())

		# 玩家重新加入，恢复到镜像的位置
		init_pos = None
		has_clone = (room_player.uid in self.uid_map_lazy)
		if has_clone:
			old_player = self.uid_map_lazy[room_player.uid]
			init_pos = (old_player.x, old_player.y)
			self.remove_player_level_ref(old_player)
			
		self.add_player_level_ref(room_player)
			
		# 分配座位号
		if not self.seat_cache:
			room_player.seat = self.seat_idx
			self.seat_idx += 1
		else:
			room_player.seat = self.seat_cache[-1]
			del self.seat_cache[-1]
		# 更新主城ID
		room_player.town_id = self.get_town_id() 
		self.print_msg("ENTERING TOWN: TOWN=%d, SEAT=%d" % (room_player.town_id, room_player.seat) )
		self.uid_map_lazy[room_player.uid] = room_player
		self.world.on_player_join(room_player, pos=init_pos)

		skill_mgr = room_player.skill_mgr
	
	def cghall_on_player_leave_room(self, hid):
		if self.cghall_has_started():
			# 游戏中途退出
			self.cghall_gametime_stop(hid)
		player = self.cghall_get_player_by_hid(hid)
		if player:
			if not player.keep_town_clone:
				self.remove_town_player_clone(player.uid)
			self.world.on_player_leave(player)
		super(CRoom, self).cghall_on_player_leave_room(hid)
		
	# 移除城镇玩家镜像
	def remove_town_player_clone (self, uid):
		player = self.uid_map_lazy.pop(uid,None)
		if player: 
			assert(player.seat is not None)
			self.seat_cache.append(player.seat)
			player.seat = None
			self.remove_player_level_ref(player)
	
	def on_c_gm_cmd(self, room_player, msg):
		is_ok, result_msg = self.gmcmd.on_text_command(room_player, msg.cmd_str)
		self.cghall_send(room_player.hid, self.msg_mgr.s_gm_cmd_result(
			cmd=msg.cmd_str, is_ok=is_ok, msg=result_msg))

	# 进入单人游戏模式
	def on_c_goto_game(self, player, msg):
		game_mode = msg.mode
		if game_mode not in x_common_consts.GAMEMODE_SINGLE:
			# 游戏模式错误
			result = x_text.NUM_GOTO_GAME_WRONG_MODE
		elif player.is_playing:
			# 玩家已经在游戏中
			result = x_text.NUM_GOTO_GAME_IS_PLAYING
		else:
			# 检查是否能进入副本
			result = player.check_map_available(msg.map_id, game_mode)
		if result != x_common_consts.GOTO_GAME_OK:
			player.send_to_self("s_goto_game", err=result)
			return

		# 单人模式不需要创建房间, 直接开始游戏
		self._start_game_single(player, msg.map_id, game_mode)

	def get_stam_cost(self, map_id, is_elite):
		map_data = x_map_data.DATA[map_id]
		stam_cost = map_data["stamina"]
		if is_elite: stam_cost *= x_common_consts.STAM_ELITE_COEFFICIENT
		return stam_cost

	def _start_game_single(self, player, map_id, game_mode, game_cfg=None, game_ctx=None):
		ctx = x_common_util.CEmpty()
		ctx.map_id = map_id
		ctx.game_mode = game_mode
		ctx.game_start_time = time.time()
		ctx.remain_resurrection_time = x_misc_consts.RESURRECTION_TIME
		if game_ctx:
			ctx.__dict__.update(game_ctx)
		player.single_game_ctx = ctx
		map_data = x_map_data.DATA[map_id]
		stage_id = map_data["stage"]
		self.send_to_player(player.hid, "s_game_init", map_id=map_id,
			stage_id=stage_id, pid_base=1, pid_self=1, game_mode=game_mode,
			game_cfg=x_serialize.dumps(game_cfg) if game_cfg else "")

	def _end_game_single(self, player):
		if player.single_game_ctx:
			player.single_game_ctx = None
		stage_id = self.world.stage_id
		pid_base = self.max_num
		self.send_to_player(player.hid, "s_game_init", stage_id=stage_id,
			pid_base=pid_base, pid_self=player.pid)
		player.sync_set = []
		self.sync_player_for(player)

	def on_c_gm_goto_game(self, player, msg):
		if not player.is_gm_mode:
			return
		if msg.mode == 1:
			game_mode = x_common_consts.GAMEMODE_PVE_ELITE
		else:
			game_mode = x_common_consts.GAMEMODE_PVE
		player.send_to_self("s_gm_goto_game", ok=x_common_consts.GOTO_GAME_OK, room_id=-1, game_mode=game_mode)
		player.prepare_enter_game(msg.map_id)
		player.keep_town_clone = True
		if msg.jump:
			self.cghall_tell_hall_player_leave_room(player.hid)

	def on_c_goto_login(self, player, msg):
		player.send_to_self("s_goto_login")
		player.keep_town_clone = False
		self.cghall_tell_hall_player_leave_room(player.hid)

	def on_c_task_list(self, player, msg):
		task_type = msg.type
		task_ids, task_prog, task_done = player.task_mgr.get_full_info_by_type(task_type)
		player.send_to_self("s_task_list", type=task_type, task_ids=task_ids,
							progress_data=x_serialize.dumps(task_prog), task_done=task_done)

	def on_c_task_list_mine(self, player, msg):
		data = x_serialize.dumps(player.task_mgr.progress)
		player.send_to_self("s_task_list_mine", progress_data=data)
		
	def on_c_task_accept(self, player, msg):
		is_ok = player.task_mgr.accept_task(msg.task_id)
		player.send_to_self("s_task_accept", is_ok=is_ok, task_id=msg.task_id)
		if is_ok:	# 立刻检查一遍，以免状态型的任务漏更新
			player.task_mgr.update_task(x_task_cond.ACTION_FLUSH_ALL)

	def on_c_task_cancel(self, player, msg):
		is_ok = player.task_mgr.cancel_task(msg.task_id)
		player.send_to_self("s_task_cancel", is_ok=is_ok, task_id=msg.task_id)
		
	def on_c_task_return(self, player, msg):
		is_ok = player.task_mgr.return_task(msg.task_id)
		player.send_to_self("s_task_return", is_ok=is_ok, task_id=msg.task_id)
		if is_ok:
			task = player.task_mgr.get_task(msg.task_id)
			player.task_mgr.update_task(x_task_cond.ACTION_RETURN_TASK, task_type=task.type)

	def on_c_new_team(self, player, msg):
		if not msg.mode:
			msg.mode = x_common_consts.GAMEMODE_PVE_MULTI
		result = player.check_map_available(msg.map_id, msg.mode)
		player.send_to_self("s_new_team", is_ok=result, team_id=0, mode=msg.mode)
		if result != x_common_consts.GOTO_GAME_OK: 
			return
		player.prepare_enter_game(msg.map_id)
		player.keep_town_clone = True
		self.cghall_tell_hall_player_leave_room(player.hid)

	def on_c_join_team(self, player, msg):
		team_room_id = msg.team_id
		self.on_player_join_team(player, team_room_id)
		
	def on_player_join_team (self, player, team_room_id):
		# TODO: 先向组队服务器查询能否加入
		player.send_to_self("s_join_team", is_ok=x_common_consts.GOTO_GAME_OK, team_id=team_room_id)
		player.keep_town_clone = True
		self.cghall_tell_hall_player_leave_room(player.hid)
		
	def on_rc_del_town_player(self, server_id, room_id, msg):
		# 玩家正在当前房间
		if msg.uid in self.uid_map:
			return
		# 玩家的镜像在当前房间
		self.remove_town_player_clone(msg.uid)
		
	# 每天的计划任务通知	
	def on_rs_do_daily_work(self, server_id, room_id, msg):
		return

	def create_item(self, tid, amount=1):
		import x_item_creator
		return x_item_creator.create_item(0, tid, amount=amount)
	
	def on_c_item_page(self, room_player, msg):
		room_player.on_c_item_page(msg)
		
	def on_c_item_sell(self, room_player, msg):
		room_player.on_c_item_sell(msg)
		
	def on_c_item_use(self, room_player, msg):
		room_player.on_c_item_use(msg)
	
	def on_c_item_sort(self, room_player, msg):
		room_player.on_c_item_sort(msg)
		
	def on_c_item_base(self, room_player, msg):
		bag = room_player.get_bag_by_id(msg.bag_id)
		if bag is None:
			return
		item = bag.peek(msg.pidx, msg.sidx)
		if item is None:
			return
		room_player.send_to_self("s_item_base", bag_id=msg.bag_id, pidx=msg.pidx,
			sidx=msg.sidx, base=item.save_to_string())

	def on_c_item_buy(self, room_player, msg):
		room_player.on_c_item_buy(msg)
		
	def on_c_mail_insert(self, room_player, msg):
		self.print_msg("on_c_mail_insert, msg:", msg)
		rid = room_player._id
		name = room_player.name
		self.send_to_static_room("rc_mail_insert", rid=rid, to_rid=msg.to_rid, type=msg.type, name=name,
			subject=msg.subject, body=msg.body, resources=msg.resources, items=msg.items)
		room_player.send_to_self("s_mail_insert", is_ok=True)

	def on_c_mail_list(self, room_player, msg):
		uid = room_player.uid
		rid = room_player._id
		self.send_to_static_room("rc_mail_list", uid=uid, rid=rid, type=msg.type,
			index=msg.index, size=msg.size)

	def on_c_mail_read(self, room_player, msg):
		rid = room_player._id
		self.send_to_static_room("rc_mail_read", rid=rid, mail_ids=msg.mail_ids)
		room_player.send_to_self("s_mail_read", is_ok=True, mail_ids=msg.mail_ids)

	def on_c_mail_delete(self, room_player, msg):
		rid = room_player._id
		self.send_to_static_room("rc_mail_delete", rid=rid, mail_ids=msg.mail_ids)
		room_player.send_to_self("s_mail_delete", is_ok=True, mail_ids=msg.mail_ids)

	def on_c_mail_fetch(self, room_player, msg):
		uid = room_player.uid
		rid = room_player._id
		self.send_to_static_room("rc_mail_fetch", uid=uid, rid=rid, mail_ids=msg.mail_ids)

	def on_c_leave_room(self, player, msg):
		player.keep_town_clone = True
		self.cghall_tell_hall_player_leave_room(player.hid)

	def on_c_leave_game(self, player, msg):
		if player.single_game_ctx:
			self._end_game_single(player)

	def on_c_goto_town(self, player, msg):
		if 0 <= msg.town_id < len(x_common_consts.GAMEMODE_TOWN):
			# TODO：还需要检查玩家的主城开放进度
			can_goto = True
		else:
			can_goto = False

		if can_goto:
			room_id = self.get_town_room_id(msg.town_id)
			player.send_to_self("s_goto_town", ok=can_goto, room_id=room_id)
			player.keep_town_clone = False  # 删除镜像
			self.cghall_tell_hall_player_leave_room(player.hid)			
		else:
			player.send_to_self("s_goto_town", ok=can_goto, room_id=0)

	def on_c_equip_skill(self,room_player,msg):
		skill_mgr = room_player.skill_mgr
		if skill_mgr is None:
			raise Exception("room player skill_mgr error.not found.")
		else:
			skill_mgr.equip_skill(msg.tid,msg.position)

	def on_c_batch_equip_skill(self, room_player, msg):
		skill_mgr = room_player.skill_mgr
		if skill_mgr is None:
			raise Exception("room player skill_mgr error.not found.")
		else:
			self.print_msg("xxxxxxxx batch_equip_skill:%s" % msg)
			skill_mgr.batch_equip_skill(msg.tids)

	def on_c_dequip_skill(self,room_player,msg):
		skill_mgr = room_player.skill_mgr
		if skill_mgr is None:
			raise Exception("room player skill_mgr error.not found.")
		else:
			skill_mgr.dequip_skill(msg.tid)
		pass

	def on_c_player_skill_list(self,room_player,msg):
		skill_mgr = room_player.skill_mgr
		if skill_mgr is None:
			raise Exception("room player skill_mgr error.not found.")
		else:
			skill_mgr.skill_list(msg.skill_type)
		pass

	def on_c_levelup_skill(self,room_player,msg):
		skill_mgr = room_player.skill_mgr
		if skill_mgr is None:
			raise Exception("room player skill_mgr error.not found.")
		else:
			skill_mgr.levelup_skill(msg.tid)
			room_player.task_mgr.update_task(x_task_cond.ACTION_FLUSH_SKILL)

	def on_c_skill_clear_cd(self,room_player,msg):
		skill_mgr = room_player.skill_mgr
		if skill_mgr is None:
			raise Exception("room player skill_mgr error.not found.")
		else:
			skill_mgr.clear_cd(skill_type = msg.skill_type)
		
	# 刷新队伍信息
	def on_rc_update_team(self, server_id, room_id, msg):
		#self.print_msg("on_rc_update_team", room_id, msg.map_id)
		team = self.all_teams.get(room_id, None)
		if not team:
			team = x_common_util.CEmpty()
			team.team_id = room_id
			team.map_id = msg.map_id
			team_list = self.teams_of_map.setdefault(msg.map_id, [])
			self.all_teams[room_id] = team
			team.index = len(team_list)
			team_list.append(team)
			# 登记PVP房间
			team.mode = msg.mode
			if msg.mode == x_common_consts.GAMEMODE_PVP:
				self.all_pvp_rooms.add(room_id)
		team.leader_uid = msg.leader_uid
		team.leader_name = msg.leader_name
		team.leader_level = msg.leader_level
		team.leader_power = msg.leader_power
		team.player_count = msg.player_count
		
	# 刷新队伍人数
	def on_rc_team_player_count(self, server_id, room_id, msg):
		team = self.all_teams.get(room_id, None)
		if not team: return
		team.player_count = msg.player_count
		
	# 移除队伍(已经开始游戏或者已经解散)
	def on_rc_remove_team(self, server_id, room_id, msg):
		#self.print_msg("on_rc_remove_team", room_id)
		team = self.all_teams.pop(room_id, None)
		if not team: 
			self.print_msg("[WARNING] room(ID=%d) not found"%room_id)
			return
		team_list = self.teams_of_map[team.map_id]
		if team.index >= len(team_list) or team_list[team.index] is not team:
			self.print_msg("[ERROR] bad team list")
			return
		last_team = team_list[-1]
		if last_team is not team:
			last_team.index = team.index
			team_list[team.index] = last_team
		del team_list[-1]
		# 移除PVP房间
		if team.mode == x_common_consts.GAMEMODE_PVP:
			self.all_pvp_rooms.discard(room_id)
		
	def on_c_team_list(self, player, msg):
		# TODO: 根据玩家的等级和进度进行过滤，只返回可以加入的队伍
		team_list = self.teams_of_map.get(msg.map_id, None)
		if team_list:
			page_begin = msg.page_begin
			if page_begin >= len(team_list):
				page_begin = 0
			page_end = min(page_begin + min(msg.page_count, 32), len(team_list))
			page_count = page_end - page_begin
			slist = []
			for i in xrange(page_begin, page_end):
				team = team_list[i]
				s = struct.pack("<IIIBBB", team.team_id, team.leader_uid, team.leader_power, team.leader_level, team.player_count, len(team.leader_name))
				slist.append(s)
				slist.append(team.leader_name)
			team_data = "".join(slist)
		else:
			team_data = ""
			page_begin = 0
			page_count = 0
		player.send_to_self("s_team_list", data=team_data, page_begin=page_begin, page_count=page_count, remain_tickets = player.get_map_tickets(msg.map_id)[1])

	def on_c_player_map_data(self,player,msg):
		#map_mgr = player.map_mgr
		#player.send_to_self("s_player_map_data" , map_data = x_serialize.dumps(map_mgr.get_tickets_info()))
		pass
		
	def on_c_join_pvp(self, player, msg):
		# TODO: 这里为了方便测试, 自动加入并开始
		if not self.all_pvp_rooms:
			new_msg = self.msg_mgr.c_new_team(map_id=x_consts.PVP_MAP_ID,
				mode=x_common_consts.GAMEMODE_PVP)
			self.on_c_new_team(player, new_msg)
			return
		if msg.room_id != 0 and msg.room_id in self.all_pvp_rooms:
			room_id = msg.room_id
		else:
			room_id = self.all_pvp_rooms.pop()
		player.send_to_self("s_join_team", is_ok=x_common_consts.GOTO_GAME_OK, team_id=room_id)
		player.keep_town_clone = True
		self.cghall_tell_hall_player_leave_room(player.hid)

	def on_c_emblem_upgrade_main(self, player, msg):
		if msg.idx >= len(player.emblem):
			return
		emobj = player.emblem[msg.idx]
		is_ok_list = []
		level_list = []
		for i in xrange(0, msg.is_batch and 10 or 1):
			is_ok = emobj.upgrade_main_s(player)
			is_ok_list.append(is_ok)
			level_list.append(emobj.main_level)
			if not is_ok: break
		player.send_to_self("s_emblem_upgrade_main", is_ok=is_ok_list, idx=msg.idx, level=level_list)
		if is_ok:
			player.task_mgr.update_task(x_task_cond.ACTION_FLUSH_EMBLEM)
	
	def on_c_emblem_upgrade_sub(self, player, msg):
		if msg.idx >= len(player.emblem):
			return
		emobj = player.emblem[msg.idx]
		is_ok_list = []
		for i in xrange(0, msg.is_batch and 10 or 1):
			is_ok = emobj.upgrade_sub_s(player)
			is_ok_list.append(is_ok)
			if not is_ok: break
		player.send_to_self("s_emblem_upgrade_sub", is_ok=is_ok_list, idx=msg.idx, level=emobj.sub_level)
		
		if is_ok:
			player.task_mgr.update_task(x_task_cond.ACTION_FLUSH_EMBLEM)
		
	def on_c_emblem_add_gem(self, player, msg):
		if msg.idx >= len(player.emblem):
			return
		emobj = player.emblem[msg.idx]
		if not player.bag_gem.has_amount(msg.gem_tid, 1):
			return
		gem = self.create_item(msg.gem_tid)
		is_ok = emobj.add_gem_s(player, gem, msg.pos)
		if is_ok:
			player.send_to_self("s_emblem_add_gem", is_ok=is_ok, idx=msg.idx, pos=msg.pos, gem_tid=msg.gem_tid)
			player.task_mgr.update_task(x_task_cond.ACTION_FLUSH_EMBLEM)
		else:
			player.send_to_self("s_emblem_add_gem", is_ok=is_ok)
		
	def on_c_emblem_remove_gem(self, player, msg):
		if msg.idx >= len(player.emblem):
			return
		emobj = player.emblem[msg.idx]
		is_ok = emobj.remove_gem_s(player, msg.pos)
		player.send_to_self("s_emblem_remove_gem", is_ok=is_ok, idx=msg.idx, pos=msg.pos)
			
	def on_c_gem_merge(self, player, msg):
		player.gem_mgr.set_create_gem_callback(self.create_item)
		is_ok, log = player.gem_mgr.merge_gem(msg.tid, msg.merge_all)
		if is_ok and log:
			player.send_to_self("s_item_log_list", pickled_log_list=x_serialize.dumps(log))
	
	def on_c_gem_levelup_equiped(self, player, msg):
		is_ok, log = player.gem_mgr.levelup_gem_equiped(msg.emblem_idx, msg.idx)
		if is_ok:
			gem_tid = player.emblem[msg.emblem_idx].gems[msg.idx].tid
		else:
			gem_tid = 0
		player.send_to_self("s_gem_levelup_equiped", is_ok=is_ok, emblem_idx=msg.emblem_idx, idx=msg.idx, gem_tid=gem_tid)
		if is_ok and log:
			player.send_to_self("s_item_log_list", pickled_log_list=x_serialize.dumps(log))
			
	def on_c_gem_merge_bag_to_max(self, player, msg):
		player.gem_mgr.set_create_gem_callback(self.create_item)
		is_ok, item_log = player.gem_mgr.merge_gem_bag_to_max()
		if is_ok and item_log:
			player.send_to_self("s_item_log_list", pickled_log_list=x_serialize.dumps(item_log))
		player._sort_item_bag(x_common_consts.BAG_ID_GEM)
			
	def on_c_gem_degrade_trade(self, player, msg):
		bag = player.bag_gem
		gem0 = bag.find_item_by_tid(msg.tid)
		# 无此物品
		if gem0 is None:
			return
		if msg.new_tid not in gem0.get_degrade_gem_tids():
			return False
		if not msg.trade_all:
			trade_amount = 1
		else:
			trade_amount = bag.get_amount(msg.tid)
		if not msg.trade_all:	# 看在移除了一个A宝石以后能不能再加一个B宝石
			add_items = [self.create_item(msg.new_tid, amount=trade_amount)]
			remove_tid_and_amount_info_list = [{"tid": gem0.tid, "remove_amount": 1}]
			can_add = bag.can_add_many_with_remove_many(add_items,
				fake_remove_tid_and_amount_info_list=remove_tid_and_amount_info_list)
		else:
			import x_item_client_info
			max_stack = x_item_client_info.DATA[msg.new_tid]["叠放上限"]
			add_items = []
			rem_amount = trade_amount
			while rem_amount > 0:
				if rem_amount <= max_stack:
					add_items.append(self.create_item(msg.new_tid, amount=rem_amount))
				else:
					add_items.append(self.create_item(msg.new_tid, amount=max_stack))
				rem_amount -= max_stack
			can_add = True
		if can_add:
			is_ok, log = bag.remove_and_destroy_amount(gem0.tid, amount=trade_amount)
			assert is_ok, "should be ok after check!"
			for add_item in add_items:
				is_ok, log = bag.add(add_item, log=log)
				assert is_ok, "should be ok after check!"		
			player.send_to_self("s_item_log_list", pickled_log_list=x_serialize.dumps(log))
	
	def on_c_gem_convert_next_gongming_level(self, player, msg):
		mgr = player.gem_mgr
		curr_level = mgr.get_gongming_level()
		if curr_level != msg.curr_level:
			is_ok = False
			next_level = curr_level
		else:
			mgr.set_create_gem_callback(self.create_item)
			is_ok, err_text = mgr.convert_next_gongming_level(check_coin=True)
			if is_ok:
				next_level = curr_level + 1
			else:
				next_level = curr_level
				player.send_to_self("s_notice", msg_type=x_common_consts.NOTICE_TYPE_ERROR, msg=err_text)
		player.send_to_self("s_gem_convert_next_gongming_level",
							is_ok=is_ok, next_level=next_level)
		player.task_mgr.update_task(x_task_cond.ACTION_FLUSH_EMBLEM)		
		
	def on_c_equip_re_create_rune(self, player, msg):
		bag = player.get_bag_by_id(msg.bag_id)
		if bag is None:
			return
		item = bag.peek(msg.pidx, msg.sidx)
		if item is None:
			return
		if not item.is_equip():
			return
		success = item.re_create_rune(player)
				
		player.send_to_self("s_equip_re_create_rune", bag_id=msg.bag_id,
			pidx=msg.pidx, sidx=msg.sidx, old_base=item.save_to_string(),
			new_base=success and item.get_pickled_preview_base() or "")
		# NOTE：不需要检查任务，需等到保存结果
	
	def on_c_equip_absorb(self, player, msg):
		# src_item
		src_bag = player.get_bag_by_id(msg.src_bag_id)
		if src_bag is None:
			return
		src_item = src_bag.peek(msg.src_pidx, msg.src_sidx)
		if src_item is None:
			return
		if not src_item.is_equip():
			return

		# dst_item
		dst_bag = player.get_bag_by_id(msg.dst_bag_id)
		if dst_bag is None:
			return
		dst_item = dst_bag.peek(msg.dst_pidx, msg.dst_sidx)
		if dst_item is None:
			return
		if not dst_item.is_equip():
			return
			
		is_ok = dst_item.absorb_equip(player, src_item)
		if not is_ok:
			player.send_to_self("s_equip_absorb", is_ok=is_ok)
		else:
			log = x_item_bag.log_item_base(dst_item)
			player.send_to_self("s_equip_absorb", is_ok=is_ok, pickled_log_list=x_serialize.dumps(log))
			player.task_mgr.update_task(x_task_cond.ACTION_EQUIP_ABSORB)
		
	def on_c_equip_save_random(self, player, msg):
		bag = player.get_bag_by_id(msg.bag_id)
		if bag is None:
			return
		item = bag.peek(msg.pidx, msg.sidx)
		if item is None:
			return
		if not item.is_equip():
			return
		item.apply_operation()
		player.task_mgr.update_task(x_task_cond.ACTION_FLUSH_EQUIP)
		
	def on_c_equip_swap_rune(self, player, msg):
		src_bag = player.get_bag_by_id(msg.src_bag_id)
		if src_bag is None:
			return
		src_item = src_bag.peek(msg.src_pidx, msg.src_sidx)
		if src_item is None:
			return
		if not src_item.is_equip():
			return
	
		dst_bag = player.get_bag_by_id(msg.dst_bag_id)
		if dst_bag is None:
			return
		dst_item = dst_bag.peek(msg.dst_pidx, msg.dst_sidx)
		if dst_item is None:
			return
		
		is_ok = src_item.swap_rune(player, dst_item)
		if is_ok:
			player.send_to_self("s_equip_swap_rune",
				src_bag_id=msg.src_bag_id, src_pidx=msg.src_pidx, src_sidx=msg.src_sidx,
				dst_bag_id=msg.dst_bag_id, dst_pidx=msg.dst_pidx, dst_sidx=msg.dst_sidx)
			player.task_mgr.update_task(x_task_cond.ACTION_FLUSH_EQUIP)
		
	def on_c_fairy_feed_soul(self, player, msg):
		ball_list = []
		for i in xrange(0, msg.is_batch and 10 or 1):
			ball = player.fairy.feed_soul(player)
			if ball is None:
				break
			ball_list.append(ball)
		player.send_to_self("s_fairy_feed_soul", ball=ball_list)
		player.task_mgr.update_task(x_task_cond.ACTION_FLUSH_FAIRY)
		
	# NOTE：不触发任务检查，需要保存培养结果。
	def on_c_fairy_breed(self, player, msg):
		attr_deltas = player.fairy.breed(player, msg.style)
		if attr_deltas is None:
			return
		player.send_to_self("s_fairy_breed", attr_deltas=list(attr_deltas))
	
	def on_c_save_breed_result(self, player, msg):
		player.fairy.save_breed_result()
		player.task_mgr.update_task(x_task_cond.ACTION_FLUSH_FAIRY)
		
	def on_c_fairy_train(self, player, msg):
		patterns_list = []
		error_code_list = []
		diamond_train_count = 0
		for i in xrange(0, msg.is_batch and 10 or 1):
			error_code, patterns, is_diamond_train = player.fairy.train(player)
			if is_diamond_train:
				diamond_train_count += 1
			error_code_list.append(error_code)
			if error_code != 0 or patterns is None: break
			patterns_list.extend(patterns)
		player.send_to_self("s_fairy_train", error_code_list=error_code_list, patterns=patterns_list, diamond_train_count=diamond_train_count)
		player.task_mgr.update_task(x_task_cond.ACTION_FLUSH_FAIRY)

	def on_c_map_data(self, player, msg):
		map_data = {}
		map_data["clear_elite"] = []
		for map_id, rec in player.map_records.iteritems():
			map_data[map_id] = rec is not None and rec.evaluate or 0
			if rec.clear_elite: map_data["clear_elite"].append(map_id)
		for area_id, area_rec in player.area_records.iteritems():
			map_data["area_%d" % area_id] = (area_rec.star, area_rec.prize1 == x_common_consts.AREA_PRIZE_FETCHED, area_rec.prize2 == x_common_consts.AREA_PRIZE_FETCHED, area_rec.prize3 == x_common_consts.AREA_PRIZE_FETCHED)
		
		player.send_to_self("s_map_data", pickled_map_data=x_serialize.dumps(map_data))

	def on_c_levelup_passive_skill(self, player, msg):
		if not (1 <= msg.tid <= len(player.passive_skills)):
			return
		
		pskill = player.passive_skills[msg.tid - 1]
		is_ok = pskill.level_up(player)
		player.send_to_self("s_levelup_passive_skill", is_ok=is_ok, tid=msg.tid)
		if is_ok:
			player.task_mgr.update_task(x_task_cond.ACTION_FLUSH_SKILL)

	def on_c_send_big_data_to_server(self, room_player, msg):
		is_done, result_msg = self._big_data.recv(room_player, msg.flag, msg.tag, msg.filename, msg.data)
		if is_done:
			self.print_msg("[%s] %s"%(msg.tag, result_msg))
			self.send_to_player(room_player.hid, "s_send_big_data_to_server",
				tag=msg.tag, filename=msg.filename, msg=result_msg)

	def on_c_xingzuo_levelup(self, room_player, msg):
		xingzuos = room_player.xingzuos
		if xingzuos is None or not (0 <= msg.tid - 1 < len(xingzuos)):
			return
		xingzuo = xingzuos[msg.tid - 1]
		result = xingzuo.level_up(room_player)
		room_player.send_to_self("s_xingzuo_levelup", result=result, tid=msg.tid)
		if result == x_common_consts.XINGZUO_LEVELUP_SUCCESS:
			room_player.task_mgr.update_task(x_task_cond.ACTION_FLUSH_XINGZUO)
			
	def on_c_tutorial_done(self, room_player, msg):
		room_player.set_tutorial_done(msg.tid)

	# 邮件模块
	def on_rs_mail_insert(self, server_id, room_id, msg):
		player = self.uid_map.get(msg.uid, None)
		if player is not None:
			player.send_to_self("s_mail_insert", is_ok=msg.is_ok, mail_id=msg.mail_id)

	def on_rs_mail_list(self, server_id, room_id, msg):
		player = self.uid_map.get(msg.uid, None)
		self.print_msg("on_rs_mail_list,msg:", msg)
		_mail_list = [self.msg_mgr.s_mail_info(
			base=mail_item.base
		) for mail_item in msg.mail_list]
		if player is not None:
			player.send_to_self("s_mail_list", is_ok=msg.is_ok, index=msg.index,
				size=msg.size, mail_list=_mail_list)

	def on_rs_mail_read(self, server_id, room_id, msg):
		player = self.uid_map.get(msg.uid, None)
		if player is not None:
			player.send_to_self("s_mail_read", is_ok=msg.is_ok, mail_id=msg.mail_id)

	def on_rs_mail_delete(self, server_id, room_id, msg):
		player = self.uid_map.get(msg.uid, None)
		if player is not None:
			player.send_to_self("s_mail_delete", is_ok=msg.is_ok, mail_id=msg.mail_id)

	def on_rs_mail_fetch(self, server_id, room_id, msg):
		player = self.uid_map.get(msg.uid, None)
		if player and msg.is_ok:
			is_ok = x_common_consts.MAIL_RESULT_SUCCESS
			failed = False
			if msg.items:
				_items = x_serialize.loads_with_coreobj(msg.items)
				if not player.add_many_items(_items, reason=x_consts.REASON_MAIL):
					is_ok = x_common_consts.MAIL_RESULT_BAG_FULL
					failed = True
			if msg.resources and not failed:
				_resources = x_serialize.loads(msg.resources)
				player.add_many_coins(dict(_resources), reason=x_consts.REASON_MAIL)
		else:
			is_ok = x_common_consts.MAIL_RESULT_FAIL
		self.send_to_static_room("rc_mail_fetch_result", uid=msg.uid, rid=msg.rid, mail_ids=msg.mail_ids, is_ok=int(is_ok))
		player.send_to_self("s_mail_fetch", mail_ids=msg.mail_ids, is_ok=is_ok)
	
	def on_c_query_recommend_players(self, room_player, msg):
		players, (hint_lv, hint_pos) = self.get_recommend_players(
			room_player, num=msg.num, max_range=50, hint=(msg.hint_lv, msg.hint_pos))
		import x_player_digest
		entry_base_lst = []
		for player in players:
			entry_base_lst.append(x_serialize.dumps(x_player_digest.CObj.gen_base(player)))
		room_player.send_to_self("s_query_recommend_players",
								 players=entry_base_lst, hint_lv=hint_lv, hint_pos=hint_pos)
	
	def on_c_add_friend(self, room_player, msg):
		self.send_to_static_room("rc_add_friend", rid=room_player.rid,
								 other_rid=msg.rid)
	
	def on_c_remove_friend(self, room_player, msg):
		self.send_to_static_room("rc_remove_friend", rid=room_player.rid,
								 other_rid=msg.rid)
	
	def on_c_add_to_blacklist(self, room_player, msg):
		self.send_to_static_room("rc_add_to_blacklist", rid=room_player.rid,
								 other_rid=msg.rid)
		
	def on_c_remove_from_blacklist(self, room_player, msg):
		self.send_to_static_room("rc_remove_from_blacklist", rid=room_player.rid,
								 other_rid=msg.rid)
		
	def on_rs_add_friend(self, server_id, room_id, msg):
		room_player = self.rid_map.get(msg.rid)
		if room_player is None: return
		room_player.send_to_self("s_add_friend", is_ok=msg.is_ok, base=msg.base)

	def on_rs_remove_friend(self, server_id, room_id, msg):
		room_player = self.rid_map.get(msg.rid)
		if room_player is None: return
		room_player.send_to_self("s_remove_friend", is_ok=msg.is_ok, rid=msg.other_rid)
		
	def on_rs_add_to_blacklist(self, server_id, room_id, msg):
		room_player = self.rid_map.get(msg.rid)
		if room_player is None: return
		room_player.send_to_self("s_add_to_blacklist", is_ok=msg.is_ok, base=msg.base)
		
	def on_rs_remove_from_blacklist(self, server_id, room_id, msg):
		room_player = self.rid_map.get(msg.rid)
		if room_player is None: return
		room_player.send_to_self("s_remove_from_blacklist", is_ok=msg.is_ok, rid=msg.other_rid)

	def on_c_game_end(self, room_player, msg):
		ctx = room_player.single_game_ctx
		if not ctx:
			return
		game_time = time.time() - ctx.game_start_time
		reward = None
		if msg.reason == x_common_consts.GAME_END_WIN:  # 胜利
			if ctx.game_mode == x_common_consts.GAMEMODE_COLOSSEUM:  # 魂兽场结算
				reward = x_game_reward.game_win_colosseum(room_player, ctx.map_id, ctx.soul_tid, ctx.retry)
			else:  # PVE结算
				reward = x_game_reward.game_win_pve(room_player, ctx.map_id, ctx.game_mode,
					game_time, msg.score, msg.kill_count)
			result = x_common_consts.GAME_END_WIN
		else:  # 失败
			result = x_common_consts.GAME_END_TASK_FAIL
		msg = self.msg_mgr.s_game_end()
		msg.reason = result
		msg.game_time = game_time
		if reward:
			msg.reward = x_serialize.dumps(reward)
		self.cghall_send(room_player.hid, msg)

	def on_c_revive(self, room_player, msg):
		if not room_player.is_playing:
			return
		# todo: 扣除资源
		#self.print_msg("on_c_revive:.............")
		result = 0
		ctx = room_player.single_game_ctx
		if ctx.remain_resurrection_time <= 0: result = 1
		if not room_player.has_enough_coin(x_common_consts.COIN_TYPE_BLUE_DIAMOND, x_misc_consts.RESURRECTION_COST): result = 2
		if not result:
			room_player.sub_coin(x_common_consts.COIN_TYPE_BLUE_DIAMOND, x_misc_consts.RESURRECTION_COST, x_consts.REASON_RESURRECTION)
			ctx.remain_resurrection_time -= 1
		self.send_to_player(room_player.hid, "s_revive", pid=msg.pid, result=result, remain_time=ctx.remain_resurrection_time)
		

	def on_c_get_stam(self, room_player, msg):
		now = x_common_util.get_seconds_of_day()
		for i, v in enumerate(x_common_consts.GET_STAM_RANGE):
			if now >= v[0] and now <= v[1]:
				#if room_player.cur_stam < room_player.max_stam:
				if room_player.worship & (1 << x_common_consts.WORSHIP_BIT_GET_STAM_1 + i) <= 0: 
					add_stam =  x_common_consts.GET_STAM_COUNT
					room_player.add_coin(x_common_consts.COIN_TYPE_CUR_STAM, add_stam, x_consts.REASON_GET_STAM)
					self.send_to_player(room_player.hid, "s_get_stam", stam_type=i, result=0)
					room_player.worship = room_player.worship | (1 << x_common_consts.WORSHIP_BIT_GET_STAM_1 + i)
				else:
					self.send_to_player(room_player.hid, "s_get_stam", stam_type=i, result=1)
				return
		self.send_to_player(room_player.hid, "s_get_stam", stam_type=msg.stam_type, result=2)

	def on_c_open_box(self, room_player, msg):
		if room_player.get_area_prize(msg.area_id, msg.box_id):
			self.send_to_player(room_player.hid, "s_open_box", area_id=msg.area_id, box_id=msg.box_id, result=0)
		else:
			self.send_to_player(room_player.hid, "s_open_box", area_id=msg.area_id, box_id=msg.box_id, result=1)

	def on_c_wipe_map(self, room_player, msg):
		wipe_times = max_wipe_times = ((msg.wipe_type == x_common_consts.WIPE_TYPE_ONCE) and 1 or 3)
		wipe_log = []
		bag = room_player.bag_2  # 扫荡券不足
		game_mode = msg.is_elite and x_common_consts.GAMEMODE_PVE_ELITE or x_common_consts.GAMEMODE_PVE
		result = -1
		while wipe_times > 0:
			if not bag.has_amount(x_misc_consts.WIPETICKET_ITEM_TID, max_wipe_times-wipe_times+1):
				result = -1
				break
			result = room_player.check_map_available(msg.map_id, msg.is_elite and x_common_consts.GAMEMODE_PVE_ELITE or x_common_consts.GAMEMODE_PVE)
			if result != x_common_consts.GOTO_GAME_OK: break
			wipe_log.append(x_game_reward.game_win_pve(room_player, msg.map_id, game_mode, None, 0, []))
			wipe_times -= 1
		if result == -1:
			room_player.send_to_self("s_wipe_map", result=2, pickled_log_list="")
		elif result != x_common_consts.GOTO_GAME_OK:
			room_player.send_to_self("s_notice", msg_type=x_common_consts.NOTICE_TYPE_ERROR, msg=x_text.FMT[result])
		room_player.sub_consumption_item(x_misc_consts.WIPETICKET_ITEM_TID, max_wipe_times - wipe_times)
		if len(wipe_log) > 0: room_player.send_to_self("s_wipe_map", result=0, pickled_log_list=x_serialize.dumps(wipe_log))

	def on_c_soul_update_link(self, room_player, msg):
		soul_mgr = room_player.soul_mgr
		slot_idx = -1
		for level in x_common_consts.SOUL_SLOT_OPEN_LEVEL:
			if room_player.level >= level:
				slot_idx += 1
			else:
				break
		is_ok = slot_idx >= msg.slot_idx >= 0 and msg.soul_tid in soul_mgr.atlas_list
		if not is_ok:
			room_player.send_to_self("s_soul_update_link")
		change_log = []
		for idx, tid in enumerate(soul_mgr.battle_list):
			if tid == msg.soul_tid:
				soul_mgr.battle_list[idx] = 0
				change_log.append(idx)
				change_log.append(0)
				break
		change_log.append(msg.slot_idx)
		change_log.append(msg.soul_tid)
		soul_mgr.battle_list[msg.slot_idx] = msg.soul_tid
		room_player.send_to_self("s_soul_update_link", log=change_log)

	def on_c_soul_levelup(self, room_player, msg):
		soul = room_player.soul_mgr.atlas_list[msg.tid]
		grains = x_serialize.loads(msg.grains)
		is_ok = room_player.consume_many_items(grains)
		if is_ok:
			soul.levelup(grains)
			room_player.rebuild_all_attr()
		room_player.send_to_self("s_soul_levelup", tid=msg.tid, pickled_soul=soul.save_to_string(), is_ok=is_ok)

	def on_c_soul_rankup(self, room_player, msg):
		soul = room_player.soul_mgr.atlas_list[msg.tid]
		is_ok = soul.rankup()
		if is_ok:
			room_player.rebuild_all_attr()
		room_player.send_to_self("s_soul_rankup", tid=msg.tid, pickled_soul=soul.save_to_string(), is_ok=is_ok)

	def on_c_soul_refresh_colosseum(self, room_player, msg):
		is_ok = True
		if msg.refresh_type == x_common_consts.COLOSSEUM_REFRESH_NORMAL:
			is_ok = room_player.sub_coin(x_common_consts.COIN_TYPE_GOLD, x_misc_consts.COLOSSEUM_NORMAL_COST, reason=x_consts.REASON_SOUL)
		elif msg.refresh_type == x_common_consts.COLOSSEUM_REFRESH_ADVANCE:
			is_ok = room_player.sub_coin(x_common_consts.COIN_TYPE_BLUE_DIAMOND, x_misc_consts.COLOSSEUM_ADVANCE_COST, reason=x_consts.REASON_SOUL)
		if not is_ok:
			room_player.send_to_self("s_soul_refresh_colosseum", is_ok=0)
		else:
			room_player.soul_mgr.refresh_colosseum(msg.refresh_type)
			room_player.add_consumption_item(x_common_consts.SOUL_GRAIN_TID_LIST[0], 1, reason=x_consts.REASON_SOUL)

	def on_c_soul_fetch(self, room_player, msg):
		if not room_player.sub_consumption_item(x_common_consts.SOUL_TICKET_TID, 1):
			room_player.send_to_self("s_notice", msg_type=x_common_consts.NOTICE_TYPE_ERROR, msg=x_text.COLOSSEUM_NO_TICKETS)
			return
		slot = room_player.soul_mgr.colosseum_list[msg.slot]
		type = slot["type"]
		gain_stone = False
		if type == x_common_consts.COLOSSEUM_TYPE_SOUL:
			soul_tid = slot["tid"]
			soul = room_player.soul_mgr.atlas_list[soul_tid]
			# # todo: 暂时屏蔽直接收复
			# if True or soul.colosseum_level >= room_player.level:
			# 进入斗兽场副本
			map_id = random.choice(soul.map_id)
			game_cfg = {"enemy_lvl": soul.colosseum_level - 1}
			game_ctx = {"soul_tid": soul_tid, "retry": x_misc_consts.COLOSSEUM_CHALLENGE_AGAIN_NUM}
			self._start_game_single(room_player, map_id, x_common_consts.GAMEMODE_COLOSSEUM, game_cfg, game_ctx)
			return
			# # 直接收服
			# soul.colosseum_level = min(x_misc_consts.COLOSSEUM_MAX_LEVEL,
			# 	soul.colosseum_level + x_misc_consts.COLOSSEUM_FETCH_ADD_LEVEL)
			# gain_stone = True
		elif type == x_common_consts.COLOSSEUM_TYPE_BOX:
			gain_stone = True
		elif type == x_common_consts.COLOSSEUM_TYPE_BUFF:
			# todo: 实现BUFF逻辑
			return
		else:
			room_player.send_to_self("s_notice", msg_type=x_common_consts.NOTICE_TYPE_ERROR, msg=x_text.COLOSSEUM_NO_TICKETS)
			return
		if gain_stone:
			# 获得灵魂石
			import x_item_creator
			soul_tid = slot["tid"]
			soul = room_player.soul_mgr.atlas_list[soul_tid]
			# 策划信誓旦旦永远只加1个, 写死数量就可以了
			item = x_item_creator.create_item(0, soul.stone_tid, 1)
			is_ok = room_player.add_item(item, reason=x_consts.REASON_COLOSSEUM)
			# 刷新斗兽场
			room_player.soul_mgr.refresh_colosseum(x_common_consts.COLOSSEUM_REFRESH_FREE)
			# 返回获取
			room_player.send_to_self("s_soul_fetch", tid=soul_tid, pickled_soul=soul.save_to_string(), is_ok=is_ok)

	def on_c_soul_challenge_again(self, room_player, msg):
		ctx = room_player.single_game_ctx
		if ctx.game_mode != x_common_consts.GAMEMODE_COLOSSEUM:
			return
		err = 0
		if ctx.retry < 1:
			err = x_text.NUM_COLOSSEUM_NO_CHALLENGE_AGAIN
		elif room_player.diamond < x_misc_consts.COLOSSEUM_CHALLENGE_AGAIN_COST:
			err = x_text.NUM_NO_BLUE_DIAMOND
		elif not room_player.has_enough_consumption_item(x_common_consts.SOUL_TICKET_TID, 1):
			err = x_text.NUM_COLOSSEUM_NO_TICKETS
		if err:
			room_player.send_to_self("s_soul_challenge_again", err=err)
			return
		room_player.sub_consumption_item(x_common_consts.SOUL_TICKET_TID, 1, reason=x_consts.REASON_COLOSSEUM)
		room_player.sub_coin(x_common_consts.COIN_TYPE_BLUE_DIAMOND,
			x_misc_consts.COLOSSEUM_CHALLENGE_AGAIN_COST, reason=x_consts.REASON_COLOSSEUM)
		ctx.retry -= 1
		ctx.game_start_time = time.time()
		ctx.remain_resurrection_time = x_misc_consts.RESURRECTION_TIME
		map_data = x_map_data.DATA[ctx.map_id]
		soul = room_player.soul_mgr.atlas_list[ctx.soul_tid]
		game_cfg = {"enemy_lvl": soul.colosseum_level - 1}
		stage_id = map_data["stage"]
		self.send_to_player(room_player.hid, "s_game_init", map_id=ctx.map_id, stage_id=stage_id, pid_base=1,
			pid_self=1, game_mode=ctx.game_mode, game_cfg=x_serialize.dumps(game_cfg))

	def on_c_soul_activate_fete(self, room_player, msg):
		is_ok = room_player.soul_mgr.activate_fete(msg.fete_id)
		if is_ok:
			room_player.rebuild_all_attr()
			fete_attr_list = x_serialize.dumps(room_player.soul_mgr.fete_attr_list)
			room_player.send_to_self("s_soul_activate_fete", fete_id=msg.fete_id, fete_attr_list=fete_attr_list, is_ok=is_ok)
		else:
			room_player.send_to_self("s_soul_activate_fete", fete_id=msg.fete_id, fete_attr_list="", is_ok=is_ok)

	def on_c_soul_buy_grain(self, room_player, msg):
		tid, coin_amount = -1, -1
		for idx in xrange(0, len(x_common_consts.SOUL_GRAIN_TID_LIST)):
			if msg.tid == x_common_consts.SOUL_GRAIN_TID_LIST[idx]:
				tid = msg.tid
				coin_amount = x_misc_consts.SOUL_GRAIN_BUY_COST[idx] * msg.amount
				break
		if tid == -1:
			room_player.send_to_self("s_soul_buy_grain", tid=msg.tid, is_ok=False)
		else:
			is_ok = room_player.sub_coin(x_common_consts.COIN_TYPE_BLUE_DIAMOND, coin_amount, reason=x_consts.REASON_SOUL)
			if is_ok:
				is_ok = room_player.add_consumption_item(msg.tid, msg.amount, reason=x_consts.REASON_SOUL)
			room_player.send_to_self("s_soul_buy_grain", tid=msg.tid, is_ok=is_ok)

	def on_c_soul_level_down(self, room_player, msg):
		if room_player.daily_mgr.colosseum_reset > 0:
			data = x_serialize.dumps(room_player.daily_mgr.colosseum_reset)
			room_player.send_to_self("s_soul_level_down", down_list=data, result=x_text.NUM_COLOSSEUM_NO_FREE_RESET)
			return
		room_player.daily_mgr.colosseum_reset += 1
		room_player.on_buy_colosseum_reset()

	def on_rc_time_adv(self, server_id, room_id, msg):
		self.time_delta += datetime.timedelta(days=msg.days, hours=msg.hours, minutes=msg.minutes)

	def now(self):
		now_time = time.time() + self.time_delta.total_seconds()
		return now_time

	def on_rs_arena_check_prize(self, server_id, room_id, msg):
		room_player = self.uid_map.get(msg.uid, None)
		if not room_player:
			return
		self.print_msg("--> arena has prize:", msg.uid, "True" if msg.prize else "False")

	def on_c_buy_res(self, room_player, msg):
		err, buy_result = room_player.buy_res(msg.buy_type)
		if err:
			room_player.send_to_self("s_buy_res", buy_type=msg.buy_type, result=err)
			return
		amount, cri_rate, need_response = buy_result
		if need_response:
			room_player.send_to_self("s_buy_res", buy_type=msg.buy_type, critical=cri_rate, amount=amount)
		# 成功之后，更新任务状态
		room_player.task_mgr.update_task(x_task_cond.ACTION_BUY_RES, buy_type=msg.buy_type)

	# 注：此处不负责获得&激活时装，获取途径其实算在物品系统里面
	def on_c_costume_equip(self, room_player, msg):
		import x_costume_mgr
		is_ok = room_player.costume.equip(msg.cos_id, (msg.part_id, ))
		room_player.send_to_self("s_costume_equip", is_ok=is_ok, cos_id=msg.cos_id, part_id=msg.part_id, activate=False)
		
	def on_c_get_active_level_prize(self, room_player, msg):
		is_ok = room_player.task_mgr.get_active_level_prize(msg.index)
		room_player.send_to_self("s_get_active_level_prize", index=msg.index, is_ok=is_ok)
		
	def on_c_save_new_flag_data(self, room_player, msg):
		import x_new_flag_define
		room_player.new_flag_mgr.set_sdata(msg.flag, x_serialize.loads(msg.data))
	
	def on_c_chest_buy(self, room_player, msg):
		room_player.print_msg('收到前端的协议')
		
		
		chest = room_player.chest
		chest.open_chest_ctr(msg.chest_id)
		room_player.send_to_self("s_chest_buy", chest_id=1,is_ok=1)
		
		
		if 0 == msg.buy_type: #免费
			pass
		elif 1== msg.buy_type:
			pass
		
		if 1 == msg.chest_id:
			pass
		elif 2 == msg.chest_id:
			pass
		elif 3 == msg.chest_id:
			pass
		elif 4 == msg.chest_id:
			pass
	