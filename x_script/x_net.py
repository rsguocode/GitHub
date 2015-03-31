# $Id: x_net.py 175491 2015-03-20 12:26:37Z ycwang@NETEASE.COM $
# -*- coding: gbk -*-

import zlib
import struct
import cPickle

import ilobby_api
import game3d

import x_msg
import x_glb
import x_consts
import x_common_consts
import x_common_util
import x_serialize
import x_world
import x_multimsg
import x_multimsg_codec
import x_errcode
import x_text

import x_item_creator
import x_ccui_notice
import x_ccui_map_entrance
import x_big_data
import x_big_data_callback
import x_ccui_waiting
import x_ccui_ranking_list
import x_ccui_gem_mgr
import x_ccui_mailbox
import x_ccui_emblem_mgr
import x_ccui_util
import x_signal_data
import x_misc_consts
import x_fight_attr_num
import x_new_flag_define


def auto_hide(method):
	def wrapper(*args, **kwargs):
		inst = x_ccui_waiting.CCUI.try_get_instance()
		if inst:
			inst.hide()
		return method(*args, ** kwargs)
	return wrapper


# 提供一个统一的类对象，控制所有的收发接口调用源
class CNet(object):
	def __init__(self):
		self.mm = x_multimsg.CMultiMsg()

		self._big_data = x_big_data.CBigData()
		self._big_data.register_callbacks({
			"snapshot": x_big_data_callback.snapshot,
		})

		self.register_callback()

	def send_big_data(self, data, tag, filename = "NOFILE"):
		param_list = self._big_data.send(data, tag, filename)
		for param in param_list:
			self.sender.c_send_big_data_to_server(\
				flag=param["flag"], 
				tag=param["tag"], 
				filename=param["filename"], 
				data=param["data"])
		
	def get_sceneobj(self, pid):
		scn = x_glb.world.scene
		if scn is None:
			return None
		return scn.get_object(pid)

	def get_me(self):
		scn = x_glb.world.scene
		if scn is None:
			return None
		return scn.me

	def get_my_data(self):
		return x_glb.my_data

	def get_fairy(self):
		me = x_glb.my_data
		if me is None: return None
		return me.fairy

	# 绑定网络回调(本函数支持多次调用！)
	def register_callback(self):
		self._event_map = {
			# 大厅及房间相关的协议
			"s_common_kick": self.on_s_common_kick,
			"s_fatal_kick": self.on_s_fatal_kick,
			"s_get_message": self.on_s_get_message,
			"s_role_list":self.on_s_role_list,
			"s_register_role":self.on_s_register_role,
			"s_delete_role" : self.on_s_delete_role,
			"s_login_room" : self.on_s_login_room,
			"s_trace_leak": self.on_s_trace_leak,
			"s_restore": self.on_s_restore,

			# 房间以及游戏内均支持的协议
			"s_gm_cmd_result": self.on_s_gm_cmd_result,
			"s_send_big_data_to_server": self.on_s_send_big_data_to_server,
			"s_send_big_data_to_client": self.on_s_send_big_data_to_client,
			"s_rtt": self.on_s_rtt,
			"s_player_rtt": self.on_s_player_rtt,
			"s_tell": self.on_s_tell,
			"s_ping": self.on_s_ping,
			"s_player_in": self.on_s_player_in,
			"s_player_out": self.on_s_player_out,

			"s_item_list": self.on_s_item_list,
			"s_item_change_list": self.on_s_item_change_list,
			"s_item_log_list": self.on_s_item_log_list,
			"s_item_add": self.on_s_item_add,
			"s_error_message" : self.on_s_error_message,

			"s_emblem_upgrade_main": self.on_s_emblem_upgrade_main,
			"s_emblem_upgrade_sub": self.on_s_emblem_upgrade_sub,
			"s_emblem_add_gem": self.on_s_emblem_add_gem,
			"s_emblem_remove_gem": self.on_s_emblem_remove_gem,
			
			"s_gem_convert_next_gongming_level": self.on_s_gem_convert_next_gongming_level,
			"s_gem_levelup_equiped": self.on_s_gem_levelup_equiped,

			"s_new_team": self.on_s_new_team,
			"s_join_team": self.on_s_join_team,
			"s_team_leader": self.on_s_team_leader,
			"s_team_list": self.on_s_team_list,
			"s_player_ready": self.on_s_player_ready,

			# 游戏内协议
			"s_game_init": self.on_s_game_init,
			"s_game_init_stage_end": self.on_s_game_init_stage_end,
			"s_get_ready_to_load_stage": self.on_s_get_ready_to_load_stage,
			"s_load_stage_begin": self.on_s_load_stage_begin,
			"s_load_stage_end": self.on_s_load_stage_end,
			"s_game_start": self.on_s_game_start,
			"s_game_end": self.on_s_game_end,
			"s_enter_area": self.on_s_enter_area,
			"s_stage_clear":self.on_s_stage_clear,
			"s_create_player": self.on_s_create_player,
			"s_create_obj": self.on_s_create_obj,
			"s_delete_obj": self.on_s_delete_obj,
			"s_load_group": self.on_s_load_group,
			"c_sync": self.on_s_sync,
			"c_mm": self.on_s_mm,
			"s_produce_monster": self.on_s_produce_monster,
			"s_npc_sync": self.on_s_npc_sync,
			"c_npc_hurt": self.on_c_npc_hurt,
			"c_enter_field": self.on_c_enter_field,
			"s_update_town_players": self.on_s_update_town_players,
			"s_revive": self.on_s_revive,

			"s_goto_town": self.on_s_goto_town,
			"s_goto_game": self.on_s_goto_game,
			"s_gm_goto_game": self.on_s_gm_goto_game,
			"s_activate_obj": self.on_s_activate_obj,
			"s_goto_npc": self.on_s_goto_npc,
			"s_goto_login": self.on_s_goto_login,

			"s_task_list": self.on_s_task_list,
			"s_task_list_mine": self.on_s_task_list_mine,
			"s_task_accept": self.on_s_task_accept,
			"s_task_return": self.on_s_task_return,
			"s_task_update": self.on_s_task_update,
			"s_task_pool_init": self.on_s_task_pool_init,
			"s_get_active_level_prize": self.on_s_get_active_level_prize,

			"s_skill_list" : self.on_s_skill_list,
			"s_skill_update" : self.on_s_skill_update,
			"s_skill_clear_cd" : self.on_s_skill_clear_cd,
			"s_levelup_passive_skill": self.on_s_levelup_passive_skill,
			"s_player_map_data" : self.on_s_player_map_data,

			"s_fairy_feed_soul": self.on_s_fairy_feed_soul,
			"s_fairy_breed": self.on_s_fairy_breed,
			"s_fairy_train": self.on_s_fairy_train,
			"s_fairy_add_exp": self.on_s_fairy_add_exp,

			"s_item_use": self.on_s_item_use,
			"s_item_base" : self.on_s_item_base,
			"s_equip_re_create_rune" : self.on_s_equip_re_create_rune,
			"s_equip_absorb": self.on_s_equip_absorb,
			"s_equip_swap_rune": self.on_s_equip_swap_rune,

			"s_xingzuo_levelup": self.on_s_xingzuo_levelup,

			"s_sync_attr": self.on_s_sync_attr,
			"s_sync_unsigned": self.on_s_sync_unsigned,
			"s_sync_signed": self.on_s_sync_signed,
			"s_sync_float": self.on_s_sync_float,
			"s_sync_map_rec": self.on_s_sync_map_rec,
			"s_open_maps": self.on_s_open_maps,
			"s_map_data": self.on_s_map_data,
			"s_daily_reset": self.on_s_daily_reset,

			"s_notice": self.on_s_notice,

			"c_pvp_player_hurt": self.on_c_pvp_player_hurt,
			"c_pvp_player_die": self.on_c_pvp_player_die,
			"c_buff_sync": self.on_c_buff_sync,
			"s_do_daily_work":self.on_s_do_daily_work,
			"s_buy_res": self.on_s_buy_res,


			# 竞技场模式相关的协议
			"s_arena_notify": self.on_s_arena_notify,
			"s_arena_enter": self.on_s_arena_enter,
			"s_arena_rivals": self.on_s_arena_rivals,
			"s_arena_game_result": self.on_s_arena_game_result,
			"s_arena_best_rank": self.on_s_arena_best_rank,
			"s_arena_game_end": self.on_s_arena_game_end,
			"s_arena_get_prize": self.on_s_arena_get_prize,

			"s_ranking_list": self.on_s_ranking_list,
			"s_do_worship": self.on_s_do_worship,
			"s_worship_reward": self.on_s_worship_reward,

			#邮件模块相关的协议
			"s_mail_insert": self.on_s_mail_insert,
			"s_mail_list": self.on_s_mail_list,
			"s_mail_read": self.on_s_mail_read,
			"s_mail_delete": self.on_s_mail_delete,
			"s_mail_fetch": self.on_s_mail_fetch,

			#兽魂模块相关的协议
			"s_soul_levelup": self.on_s_soul_levelup,
			"s_soul_rankup": self.on_s_soul_rankup,
			"s_soul_add_stone": self.on_s_soul_add_stone,
			"s_soul_refresh_colosseum": self.on_s_soul_refresh_colosseum,
			"s_soul_fetch": self.on_s_soul_fetch,
			"s_soul_unlock": self.on_s_soul_unlock,
			"s_soul_activate_fete": self.on_s_soul_activate_fete,
			"s_soul_buy_grain": self.on_s_soul_buy_grain,
			"s_soul_challenge_again": self.on_s_soul_challenge_again,
			"s_soul_level_down": self.on_s_soul_level_down,
			"s_soul_update_link": self.on_s_soul_update_link,

			# 好友系统
			"s_query_role": self.on_s_query_role,
			"s_query_recommend_players": self.on_s_query_recommend_players,
			"s_get_relation": self.on_s_get_relation,
			
			"s_add_friend": self.on_s_add_friend,
			"s_remove_friend": self.on_s_remove_friend,
			"s_add_to_blacklist": self.on_s_add_to_blacklist,
			"s_remove_from_blacklist": self.on_s_remove_from_blacklist,
			
			# 聊天系统
			"s_chat": self.on_s_chat,
			"s_get_stam": self.on_s_get_stam,
			"s_open_box": self.on_s_open_box,
			"s_wipe_map": self.on_s_wipe_map,
			
			# 时装系统
			"s_costume_expire": self.on_s_costume_expire,
			"s_costume_equip": self.on_s_costume_equip,
			
			# 宝箱系统
			"s_chest_free": self.on_s_chest_free,	
			"s_chest_buy":self.on_s_chest_buy,		
		}
		x_glb.API.register_game_room_msgdefine_and_callback(x_msg.MSG, self._event_map)

		# 引用底层的sender
		self.sender = x_glb.API.sender
		self.msg_mgr = x_glb.API.get_game_room_msgmgr()

		# 集合式批量协议
		codec_map = {
			1: x_multimsg_codec.CSyncCodec(self.on_delta_sync_data),  # 玩家增量同步
		}

		def send_func(data):
			self.sender.c_mm(data=data)
		self.mm.register_callback(codec_map, send_func)

	#发送消息并显示菊花
	def send_and_wait(self, *args, **kwargs):
		msg = getattr(self.sender, args[0])
		if callable(msg):
			msg(**kwargs)
			x_ccui_waiting.CCUI.instance().wait_for(args[0])

	#接收消息并隐藏菊花
	def receive_and_dispatch(self, msg):
		msgname = msg.__msgname__
		msg_proc = getattr(self, "on_%s" % msgname, None)
		if callable(msg_proc):
			msg_proc(msg)
			x_ccui_waiting.CCUI.instance().hide()
	
	def query_role(self, rid=0, name=""):
		my_data = self.get_my_data()
		if my_data.relation is None:
			self.sender.c_get_relation()
		self.send_and_wait("c_query_role", rid=rid, name=name)
		
	def destroy(self):
		del self.sender

	def _get_dummy_sender(self):
		class CSender(object):
			def __getattr__(self, attr_name):
				def func(*args, **kwargs):
					pass
				return func
		return CSender()

	def disable_sender(self, disabled):
		if disabled:
			self.sender = self._get_dummy_sender()
		else:
			self.sender = x_glb.API.sender

	def pause_network(self, b):
		x_glb.API.pause_network(b) # 处理真正的引擎网络

	def _print_texts(self, texts):
		print texts

	def send_msg_directly(self, msg):
		self.sender._Sender__sendfunc(msg)

	#-------------------------------------------------------
	# 响应服务器指令
	#------------------------/-------------------------------

	@auto_hide
	def on_s_register_role(self,msg):
		role_list = x_serialize.loads(msg.pickled_role_list)
		import x_ccui_account
		x_ccui_account.CCUI.instance().refresh_role_list(role_list)
		import x_ccui_chr_create
		instance = x_ccui_chr_create.CCUI.try_get_instance()
		if instance: instance.visible = False

	def on_s_delete_role(self,msg):
		role_list = x_serialize.loads(msg.pickled_role_list)
		import x_ccui_account
		x_ccui_account.CCUI.instance().refresh_role_list(role_list)

	@auto_hide
	def on_s_role_list(self,msg):
		role_list = x_serialize.loads(msg.pickled_role_list)
		import x_ccui_account
		instance = x_ccui_account.CCUI.instance()
		instance.refresh_role_list(role_list, msg.last_login_rid)
		instance.visible = True

	def on_s_login_room(self, msg):
		my_data = x_glb.my_data
		if not my_data:
			print "[ERROR] x_glb.my_data should be created!"
			import x_my_data
			my_data = x_my_data.CObj()
			x_glb.my_data = my_data
		base = my_data.get_base_from_string(msg.base)
		my_data.on_create(base)
		#属性计算没有加上装备、纹章、精灵、星座的属性，因此强制重新计算一次
		my_data.rebuild_all_attr(True)
		print "--------------------------------------------"
		print "[USER] Login: uid =", my_data.uid
		print "--------------------------------------------"
		x_glb.lobby.set_auto_room_id(msg.room_id, 0)
		import x_ccui_account
		x_ccui_account.CCUI.instance().visible = True

		game3d.set_dump_info("username", my_data.name.decode("gbk").encode("utf8"))
		
	def on_s_restore(self, msg):
		print "------------------> s_restore !!!"
		import x_my_data
		my_data = x_glb.my_data
		uid = my_data.uid
		ctx = my_data.before_restore()
		my_data = x_my_data.CObj(uid)
		base = my_data.get_base_from_string(msg.base)
		my_data.on_create(base)
		my_data.after_restore(ctx)
		x_glb.my_data = my_data

	def on_s_update_town_players(self, msg):
		for uid in msg.delete_list:
			x_glb.world.scene.del_player_by_uid(uid)
		for create_msg in msg.create_list:
			self.on_s_create_player(create_msg)
		update_list = x_serialize.loads(msg.update_list)
		for i in xrange(0, len(update_list), 4):
			pid = update_list[i]
			x = update_list[i + 1]
			d = update_list[i + 2]
			cos = x_serialize.loads(update_list[i + 3])
			player = x_glb.world.scene.get_object(pid)
			if player is None:
				continue
			player.set_dest_x(x)
			player.cur_costume_id = cos
			player.avatar_mgr.update_costume()

	def on_s_common_kick(self, msg):
		print "common kick:", msg.why
		x_glb.lobby.init_auto_join_info()

	def on_s_fatal_kick(self, msg):
		self._goto_login()
		import x_ccui_messagebox
		txt = x_errcode.MSG[msg.why]
		x_ccui_messagebox.CCUI.instance().show_message(txt)

	def on_s_get_message(self, msg):
		if msg.mid == x_common_consts.MESSAGE_ID_LOGIN:
			x_glb.API.chat_add_msg(msg.msg)

	def on_s_gm_cmd_result(self, msg):
		result_text = x_glb.gmcmd.on_s_gm_cmd_result(msg)
		self._print_texts(result_text)
		
		x_ccui_notice.CCUI.instance().info(result_text)

	def on_s_send_big_data_to_server(self, msg):
		self._print_texts("[S_SEND_BIG_DATA RESULT]msg=%s, tag=%s, filename=%s"%(\
			msg.msg, msg.tag, msg.filename))
			

	def on_s_send_big_data_to_client(self, msg):
		is_done, result_msg = self._big_data.recv(self.get_me(), msg.flag, msg.tag, msg.filename, msg.data)
		if is_done:
			print "[%s] %s"%(msg.tag, result_msg)

	def on_s_ping(self, msg):
		x_glb.net.sender.c_ping(time=msg.time)
		x_glb.world.on_server_ping(msg.time)

	def on_s_rtt(self, msg):
		#print "--> rtt:", msg.rtt
		x_glb.my_data.rtt = msg.rtt

	def on_s_player_rtt(self, msg):
		pass

	def on_s_tell(self, msg):
		print "[TELL]%s" % msg

	def on_s_create_player(self, msg):
		if msg.attrs:
			base = x_serialize.loads_with_coreobj(msg.attrs)
			#print "create player base=%r" % base
		else:
			base = None
		pos_face = None if msg.born else (msg.x, msg.y, msg.face)
		# print "--> craete player(UID=%d) at:" % msg.uid, pos
		x_glb.world.scene.add_player(msg.uid, msg.pid, msg.tid,
			pos_face, msg.name, seat=msg.seat, base=base)

	@auto_hide
	def on_s_game_init(self, msg):
		my_data = x_glb.my_data
		world = x_glb.world
		goto_town = x_common_consts.GAMEMODE_TOWN[0] <= msg.game_mode <= x_common_consts.GAMEMODE_TOWN[-1]
		if world:
			if world.scene.is_town() and not goto_town:
				me = world.scene.me
				my_data.town_pos_face = (me.x, me.y, me.d)
			world.destroy()
			# 在新 world 的创建过程中禁止访问 x_glb.world
			x_glb.world = None
		if msg.game_cfg:
			game_cfg = x_serialize.loads(msg.game_cfg)
		else:
			game_cfg = None
		world = x_world.CWorld(msg.game_mode, msg.pid_base, bool(msg.is_multi), msg.map_id, game_cfg)
		x_glb.world = world
		world.load_stage(msg.stage_id)
		if not msg.is_multi and msg.pid_self:
			# 单人游戏或城镇, 客户端直接开始
			import x_role_class_data
			game_mode = msg.game_mode
			if game_mode in x_common_consts.GAMEMODE_SINGLE:
				base = my_data.get_fight_base()
			else:
				base = my_data.get_town_base()
			tid = x_role_class_data.DATA[my_data.role_class]["obj_tid"]
			if world.scene.is_town():
				new_town_id = world.scene.get_town_id()
				if my_data.town_id != new_town_id:
					my_data.town_id = new_town_id
					portal_town = world.scene.get_objects_by_class_tag("portal_town")[0]
					pos_face = portal_town.x, portal_town.y, x_consts.DIR_RIGHT
				else:
					pos_face = my_data.town_pos_face
					my_data.town_pos_face = None
			else:
				pos_face = None
			world.scene.add_player(my_data.uid, msg.pid_self, tid, pos_face, my_data.name, 0, base)
			world.scene.wait_for_stage_loading(world.on_stage_start)
			world.create_gui()
		print "[USER] on_s_game_init", msg.is_multi, msg.pid_self, my_data.town_pos_face

	def on_s_game_init_stage_end(self, msg):
		need_response = msg.response
		world = x_glb.world
		callback = x_glb.net.sender.c_game_init_ok if need_response else \
			world.on_stage_start
		world.scene.wait_for_stage_loading(callback)
		world.create_gui()

	def on_s_get_ready_to_load_stage(self, msg):
		world = x_glb.world
		world.is_stage_start = False  # 停止update
		x_glb.net.sender.c_ready_to_load_stage()

	def on_s_load_stage_begin(self, msg):
		# print "[USER] s_load_stage_begin"
		x_glb.world.load_stage(msg.stage_id)

	def on_s_load_stage_end(self, msg):
		# print "[USER] s_load_stage_end"
		x_glb.world.scene.wait_for_stage_loading(x_glb.net.sender.c_load_stage_ok)

	def on_s_game_start(self, msg):
		# 游戏开始
		x_glb.world.game_start(msg.time)

	def on_s_game_end(self, msg):
		# print "--> on_s_game_end"
		# 游戏结束
		world = x_glb.world
		world.game_end(msg)

	def on_s_enter_area(self, msg):
		# 进入新的区域
		world = x_glb.world
		world.on_server_ping(msg.time)
		x_glb.world.on_stage_start()

	def on_s_stage_clear(self, msg):
		# 区域达成
		pass

	def on_s_create_obj(self, msg):
		scene = x_glb.world.scene
		if not msg.attrs:
			base = None
		else:
			base = x_serialize.loads_with_coreobj(msg.attrs)
		scene.add_object(msg.tid, msg.x, msg.y, pid=msg.pid, base=base)
		#print '[USER] create %s[%d]'%(obj.ocd["show_name"],obj.pid), "at (%f,%f)"%(obj.x,obj.y), "borntime",obj.borntime

	def on_s_delete_obj(self, msg):
		obj = x_glb.world.scene.get_object(msg.pid)
		if obj:
			name = obj.ocd["show_name"]
			#print '[USER] delete object %s[%d] (reason %d)'%(name,msg.pid,msg.reason)
		else:
			#print '[WARNING] delete unknown object[%d] (reason %d)'%(msg.pid,msg.reason)
			return
		if msg.reason == 0: # caused by game logic
			if not obj.client_decide_when_to_destroy():
				x_glb.world.scene.del_object(msg.pid)
		elif msg.reason == 1: # caused by aoi
			x_glb.world.scene.del_object(msg.pid)
		else:
			print '[ERROR] s_delete_obj: unknown reason', msg.reason
			assert(0)

	def on_s_load_group(self, msg):
		obj = x_glb.world.scene.get_object(msg.pid)
		if not obj or not hasattr(obj,"on_s_load_group"):
			return
		obj.on_s_load_group(msg.idx)

	# 玩家rt同步	
	def on_s_sync(self, msg):
		obj = self.get_sceneobj(msg.pid)
		if not obj: return
		if obj.pid != x_glb.world.scene.me.pid:
			obj.add_sync_pack(msg)

	# 处理集合式同步包
	def on_s_mm(self, msg):
		self.mm.unpack_all(msg.data)

	# 处理增量同步包
	def on_delta_sync_data(self, data):

		pid = ord(data[0])
		player = x_glb.world.scene.get_object(pid)

		#if __debug__:
		#	oldx, oldy = player.delta_data.data[x_player_delta_sync_data.X], \
		#		player.delta_data.data[x_player_delta_sync_data.Y]

		changes = player.delta_data.recv_diff_and_update_self(data)
		# dd = player.delta_data.data

		# 生成一个新对象吧
		msg = player.delta_data.to_msg(self.msg_mgr.c_sync)
		msg.pid = player.pid
		assert msg.state != 0, "state == 0????!!!!"

		self.on_s_sync(msg)

	def on_s_produce_monster(self, msg):
		#print '[USER] on_s_produce_monster', msg.pid, msg.seed, msg.count
		generator = x_glb.world.scene.get_object(msg.pid)
		if not generator:
			return
		generator.on_s_produce_monster(msg.seed, msg.count)

	def on_s_player_in(self, msg):
		pass

	def on_s_player_out(self, msg):
		world = x_glb.world
		if world and world.scene:
			world.scene.del_player_by_uid(msg.uid)

	# 道具相关的操作
	def on_s_item_list(self, msg):
		x_glb.my_data.bag_reset_page(msg.bag_id, msg.pidx, msg.cur_page_max_slot, msg.items)

	def on_s_item_log_list(self, msg):
		logs = x_serialize.loads(msg.pickled_log_list)
		x_glb.my_data.bag_update(logs)

	# 某次操作导致某个背包里面不定个数的道具发生了变化
	# 比如，修理装备
	def on_s_item_change_list(self, msg):
		#x_glb.data.data_cache.cache_bag.msg_proc(msg)
		pass

	# 与s_item_log_list格式完全一致。log里的物品是新获得的。
	def on_s_item_add(self, msg):
		logs = x_serialize.loads(msg.pickled_log_list)
		x_glb.my_data.bag_update(logs)

	def on_s_npc_sync(self, msg):
		obj = x_glb.world.scene.get_object(msg.pid)
		if not obj:
			return
		ai_actor = getattr(obj, "ai_actor", None)
		if not ai_actor:
			return
		ai_actor.on_sync(msg.seed, msg.period)

	def on_c_npc_hurt(self, msg):
		# print "--> on_c_npc_hurt"
		scene = x_glb.world.scene
		data = zlib.decompress(msg.data)
		data_len = len(data)
		format = "<HHffIIBb"
		sz = struct.calcsize(format)
		beg = 0
		end = sz
		while end <= data_len:
			pid, hit_seq, x, y, skill_tid, damage, hit_event, hit_dir = struct.unpack(
				format, data[beg:end])
			beg = end
			end += sz
			obj = scene.get_object(pid)
			if not obj:
				continue
			skill = x_glb.data.mgr_skill_cache.get(skill_tid)
			skill.critical = bool(hit_event >> 7)
			hit_event &= 0x7F
			# print "obj(PID=%d).on_sync_hurt:"%pid, hit_seq, x, y, skill,
			# damage
			obj.on_sync_hurt(hit_seq, x, y, skill, damage, hit_event, hit_dir)

	def on_c_pvp_player_hurt(self, msg):
		scene = x_glb.world.scene
		player = scene.get_object(msg.pid)
		if not player:
			return
		player.on_sync_hurt(msg.damage, bool(msg.is_critical))

	def on_c_pvp_player_die(self, msg):
		scene = x_glb.world.scene
		player = scene.get_object(msg.pid)
		if not player:
			return
		player.on_sync_die(msg.skill_tid, msg.skill_dir)

	def on_c_enter_field(self, msg):
		scene = x_glb.world.scene
		m = __import__("x_field_" + msg.field_type)
		for pid in msg.objs:
			obj = scene.get_object(pid)
			if not obj:
				continue
			field_obj = m.CField()
			field_obj.on_sync_attrs(msg.field_attrs)
			obj.on_enter_field(field_obj)

	@auto_hide
	def on_s_error_message(self, msg):
		message = msg.message if msg.message else x_text.FMT[msg.code]
		show_type_2_func = {
			x_common_consts.SHOW_TYPE_MESSAGEBOX_YESNO: self.show_message,
			x_common_consts.SHOW_TYPE_MESSAGEBOX_OK: self.show_message,
		}
		show_type_2_func[msg.show_type](message, msg.show_type)

	def show_message(self, message, show_type):
		x_ccui_notice.CCUI.instance().warning(message)

	@auto_hide
	def on_s_goto_town(self, msg):
		if not msg.ok:
			x_glb.world.scene.me.is_transfering = False
		else:
			# 有明确的room_id了，不需要game_mode
			x_glb.lobby.set_auto_room_id(msg.room_id, 0)

	@auto_hide
	def on_s_goto_game(self, msg):
		if not msg.err:
			return
		description = x_text.FMT[msg.err]
		x_ccui_notice.CCUI.instance().info(description)
		if x_glb.world.scene.is_town():
			x_glb.world.scene.me.is_transfering = False

	def on_s_gm_goto_game(self, msg):
		if msg.ok == x_common_consts.GOTO_GAME_OK:
			x_glb.lobby.set_auto_room_id(msg.room_id, msg.game_mode)
			return
		description = x_text.FMT[msg.ok]
		x_ccui_notice.CCUI.instance().info(description)

	def on_s_goto_login(self, msg):
		self._goto_login()

	def _goto_login(self):
		x_glb.lobby.set_auto_room_id(0, x_common_consts.GAMEMODE_LOGIN)
		if x_glb.world:
			x_glb.world.destroy()
			x_glb.world = None

	def on_s_activate_obj(self, msg):
		#print "[USER] on_s_activate_obj", msg.pid, msg.activated
		obj = x_glb.world.scene.get_object(msg.pid)
		if not obj: return
		obj.on_s_activate_obj(msg.activated)

	def on_s_goto_npc(self, msg):
		scene = x_glb.world.scene
		if scene is not None and scene.is_town():
			player = scene.me
			player.goto_npc(msg.npc_id)

	def on_s_goto_task(self, msg):
		scene = x_glb.world.scene
		if scene is not None and scene.is_town():
			player = scene.me
			player.goto_task(msg)

	def on_s_task_list(self, msg):
		pass

	def on_s_task_list_mine(self, msg):
		pass

	@auto_hide
	def on_s_task_accept(self, msg):
		if not msg.is_ok:
			return False
		x_glb.my_data.task_mgr.do_accept_task(msg.task_id)
		x_glb.world.scene.me.check_tutorial(accept_task=msg.task_id)
		task = x_glb.my_data.task_mgr.get_task(msg.task_id)
		if task.type == "剧情":
			if not x_glb.has_tutorial():
				x_glb.world.scene.me.goto_task(task_id=msg.task_id)
			x_glb.my_data.new_flag_mgr.check(x_new_flag_define.TASK_CAN_ACCEPT)
			x_glb.my_data.new_flag_mgr.check(x_new_flag_define.TASK_CURRENT)					
			x_glb.world.scene.refresh_npc_task_status(msg.task_id)
				
	@auto_hide
	def on_s_task_return(self, msg):
		task_mgr = x_glb.my_data.task_mgr
		task_mgr.do_return_task(msg.task_id)
		
		if msg.is_ok:
			task = task_mgr.get_task(msg.task_id)
			# 是否需要触发新手教学
			x_glb.world.scene.me.check_tutorial(return_task=msg.task_id)
			# 在剧情模式时才需要触发下一步自动寻路
			if not x_glb.has_tutorial() and task.type == "剧情":
				x_glb.world.scene.me.goto_task(task_id=0)
			# 如果是挑战任务，则需要主动去接受“任务链”的下一环
			if task.type == "挑战":
				new_task_id = task_mgr.get_following_challenge_task(msg.task_id)
				if new_task_id:
					x_glb.net.sender.c_task_accept(task_id=new_task_id)
			# 刷新红点
			if task.type == "挑战":
				x_glb.my_data.new_flag_mgr.check(x_new_flag_define.TASK_CHALLENGE)
			elif task.type == "每日":
				x_glb.my_data.new_flag_mgr.check(x_new_flag_define.TASK_DAILY)
			elif task.type == "剧情":
				x_glb.my_data.new_flag_mgr.check(x_new_flag_define.TASK_CAN_ACCEPT)
				x_glb.my_data.new_flag_mgr.check(x_new_flag_define.TASK_CURRENT)
			# 刷新UI
			import x_ccui_task_mgr
			task_ui = x_ccui_task_mgr.CCUI.try_get_instance()
			if task_ui and task_ui.visible:
				task_ui.on_task_finish(msg.task_id)
			# 刷新NPC头顶状态
			for npc in x_glb.world.scene.tid_to_npc.itervalues():
				npc.refresh_task_status()
			# 显示所获得的奖励
			if task.type in ("挑战", "每日"):
				res, item_prize = task.get_reward()
				x_ccui_util.show_reward(res, item_prize)
			
	def on_s_task_update(self, msg):
		updated_progress = x_serialize.loads(msg.progress_data)
		x_glb.my_data.task_mgr.do_update_task(updated_progress)
		# 刷新红点标记
		x_glb.my_data.new_flag_mgr.check(x_new_flag_define.TASK_CHALLENGE)
		x_glb.my_data.new_flag_mgr.check(x_new_flag_define.TASK_DAILY)
		# 刷新NPC头顶标记
		for tid, prog1, prog2, prog3 in updated_progress:
			x_glb.world.scene.refresh_npc_task_status(tid)
		# 刷新UI
		import x_ccui_task_mgr
		task_ui = x_ccui_task_mgr.CCUI.try_get_instance()
		if task_ui:
			task_ui.refresh()
		
	# 每日到点或第一次升级到该类任务开放时触发
	def on_s_task_pool_init(self, msg):
		task_mgr = x_glb.my_data.task_mgr
		task_mgr.clear_outdated((msg.type, ))
		assert msg.type in ("挑战", "每日"), "该类任务【%s】没有任务池。" % msg.type
		# 自动接受
		map(task_mgr.do_accept_task, msg.task_ids)
		task_mgr._rebuild_runtime()
		# 刷新UI
		import x_ccui_task_mgr
		task_ui = x_ccui_task_mgr.CCUI.try_get_instance()
		if task_ui:
			task_ui.refresh()
		
	@auto_hide
	def on_s_get_active_level_prize(self, msg):
		if msg.is_ok:
			x_glb.my_data.task_mgr.active_level_prize[msg.index] = True
			import x_ccui_task_mgr
			ui = x_ccui_task_mgr.CCUI.try_get_instance()
			if ui:
				ui.refresh_active_level_panel()
				
	@auto_hide
	def on_s_skill_list(self, msg):
		x_glb.my_data.on_skill_list(msg)

	@auto_hide
	def on_s_skill_update(self, msg):
		x_glb.my_data.on_skill_update(msg)
		if msg.action == "levelup":
			x_ccui_notice.CCUI.instance().info(x_text.SKILL_LEVELUP_SUCCESS)

	def on_s_skill_clear_cd(self, msg):
		pass

	def on_s_new_team(self, msg):
		if msg.is_ok != x_common_consts.GOTO_GAME_OK:
			# create team failed
			description = x_text.FMT[msg.is_ok]
			print "创建队伍失败:", description
			return
		x_glb.lobby.set_auto_room_id(msg.team_id, msg.mode)
		print "创建队伍成功"

	def on_s_join_team(self, msg):
		if msg.is_ok != x_common_consts.GOTO_GAME_OK:
			description = x_text.FMT[msg.is_ok]
			print "加入队伍失败:", description
			return
		x_glb.lobby.set_auto_room_id(msg.team_id, x_common_consts.GAMEMODE_PVE_MULTI)
		print "加入队伍成功:", msg.team_id

	def on_s_team_leader(self, msg):
		pass

	def on_s_team_list(self, msg):
		team_list = []
		data = msg.data
		format = "<IIIBBB"
		sz = struct.calcsize(format)
		beg = 0
		end = sz
		while end <= len(data):
			team_id, leader_uid, leader_power, leader_level, player_count, name_len = struct.unpack(format, data[beg:end])
			beg = end + name_len
			leader_name = data[end:beg]
			end = beg + sz
			team_list.append(
				{
				"team_id" : team_id,
				"count" : player_count,
				"leader_name" : leader_name,
				"leader_level" : leader_level,
				"leader_power" : leader_power,
				"leader_uid" : leader_uid,
				})
			print "\tteam id:", team_id

	def on_s_player_ready(self, msg):
		pass
	
	def on_s_player_map_data(self,msg):
		pass

	@auto_hide
	def on_s_emblem_upgrade_main(self, msg):
		if not msg.is_ok:
			return
		my_data = self.get_my_data()
		if my_data is None:
			return
		emobj = my_data.emblem[msg.idx]
		old_level = emobj.main_level
		emobj.main_level = msg.level[-1]
		my_data.rebuild_all_attr(True)
		def _show_notice(level_diff):
			if level_diff <= 0:
				x_ccui_notice.CCUI.instance().error(x_text.EMBLEM_UPGRADE_LEVEL_LIMIT)
				return
			x_ccui_notice.CCUI.instance().info(level_diff == 1 and x_text.UPGRADE_MAIN_SUCCESS or (level_diff == 2 and x_text.UPGRADE_MAIN_CRITE or x_text.UPGRADE_MAIN_CRITE_TWICE))
		for i, ok in enumerate(msg.is_ok):
			if ok:
				level_diff = (i == 0 and (msg.level[i] - old_level) or (msg.level[i] - msg.level[i-1]))
				x_glb.world.per_sec_callout.add(0.1 + i * 0.3, _show_notice, level_diff)
		if 0 < i < 9 and emobj.main_level >= my_data.level * 2:
				x_glb.world.per_sec_callout.add(0.1 + i * 0.3, _show_notice, 0)
		x_ccui_emblem_mgr.CCUI.instance().update_emblem_info(msg.idx, x_common_consts.EMBLEM_INDEX_MAIN)
		
		my_data.new_flag_mgr.check(x_new_flag_define.EMBLEM_TAB1_STR)

	@auto_hide
	def on_s_emblem_upgrade_sub(self, msg):
		if not msg.is_ok:
			return		
		my_data = self.get_my_data()
		if my_data is None:
			return
		emobj = my_data.emblem[msg.idx]
		emobj.sub_level = msg.level
		my_data.rebuild_all_attr(True)
		x_ccui_emblem_mgr.CCUI.instance().update_emblem_info(msg.idx, x_common_consts.EMBLEM_INDEX_SUB)
		success_time = len(msg.is_ok)
		if msg.is_ok[-1] <= 0: success_time -= 1
		if success_time > 1: x_ccui_notice.CCUI.instance().info(x_text.BATCH_UPGRADE_SUB_SUCCESS % (success_time, emobj.sub_level/10, emobj.sub_level%10))
		
		my_data.new_flag_mgr.check(x_new_flag_define.EMBLEM_TAB2_UPSTAR)

	@auto_hide
	def on_s_emblem_add_gem(self, msg):
		if not msg.is_ok:
			return		
		me = self.get_my_data()
		if me is None:
			return
		gem = x_item_creator.create_item(0, msg.gem_tid)
		emobj = me.emblem[msg.idx]
		emobj.gems[msg.pos] = gem
		x_glb.my_data.rebuild_all_attr(True)
		x_ccui_gem_mgr.CCUI.instance().refresh_widget_data(emobj)
		
	@auto_hide
	def on_s_emblem_remove_gem(self, msg):
		if not msg.is_ok:
			return		
		me = self.get_my_data()
		if me is None:
			return
		emobj = me.emblem[msg.idx]
		emobj.gems[msg.pos] = None
		x_glb.my_data.rebuild_all_attr(True)
		x_ccui_gem_mgr.CCUI.instance().refresh_widget_data(emobj)

	# 测试用GM：/x x_glb.net.sender.c_gem_convert_next_gongming_level()
	@auto_hide
	def on_s_gem_convert_next_gongming_level(self, msg):
		if not msg.is_ok:
			print "兑换下一级共鸣失败。"
			return
		me = self.get_my_data()
		if me is None:
			return
		curr_level = me.gem_mgr.get_gongming_level()
		if curr_level + 1 != msg.next_level:
			print "共鸣等级不同步。有错误。"
			return
		import x_item_creator
		me.gem_mgr.set_create_gem_callback(x_item_creator.create_item_simple)
		is_ok = me.gem_mgr.convert_next_gongming_level(check_coin=False)
		assert is_ok, "在数据同步的情况下，应该客户端也成功。"
		if is_ok:
			import x_ccui_gem_mgr
			x_ccui_gem_mgr.CCUI.instance().on_info_tab_changed(0, 0)
				
	@auto_hide
	def on_s_gem_levelup_equiped(self, msg):
		if not msg.is_ok:
			return
		my_data = self.get_my_data()
		if my_data is None:
			return
		emobj = my_data.emblem[msg.emblem_idx]
		new_gem = x_item_creator.create_item_simple(msg.gem_tid)
		emobj.gems[msg.idx] = new_gem
		my_data.rebuild_all_attr(force=True)
		x_ccui_gem_mgr.CCUI.instance().refresh_widget_data(emobj)

	@auto_hide
	def on_s_item_use(self, msg):
		import x_ccui_tips
		inst = x_ccui_tips.CCUI.try_get_instance()
		if inst:
			inst.on_use_item_result(msg.is_ok)

	def on_s_item_base(self, msg):
		x_glb.data.data_cache.cache_equip.msg_proc(msg)

	@auto_hide
	def on_s_equip_re_create_rune(self, msg):
		#x_glb.data.data_cache.cache_equip.msg_proc(msg)
		import x_ccui_rune_mgr
		x_ccui_rune_mgr.CCUI.instance().on_s_equip_recreate_rune(msg)

	@auto_hide
	def on_s_equip_absorb(self, msg):
		if not msg.is_ok:
			print "符文吞噬失败！"
		else:
			log = x_serialize.loads(msg.pickled_log_list)
			x_glb.my_data.bag_update(log)

	@auto_hide
	def on_s_equip_swap_rune(self, msg):
		x_ccui_notice.CCUI.instance().info(x_text.RUNE_EXCHANGE_SUCCESS)
		src_equip = x_glb.my_data.get_bag_item(msg.src_bag_id, msg.src_pidx, msg.src_sidx)
		dst_equip = x_glb.my_data.get_bag_item(msg.dst_bag_id, msg.dst_pidx, msg.dst_sidx)
		src_equip.do_swap_rune(dst_equip)
		x_glb.my_data.rebuild_all_attr(True)
		import x_ccui_rune_mgr
		x_ccui_rune_mgr.CCUI.instance().show_rune_swap_result()
		#x_glb.data.data_cache.cache_equip.msg_proc(msg)
		# 把装备放上去的时候已经通过c_item_base来取得了装备信息
		# 通过调用equipA.swap_rune(equipB)来更新本地

	# 精灵系统测试代码
	# 显示精灵属性：/x print x_glb.world.scene.me.fairy.detail()
	# 测试注灵：/x x_glb.net.sender.c_fairy_feed_soul()
	# 测试培养：/x x_glb.net.sender.c_fairy_breed(style=1)
	# 测试训练：/x x_glb.net.sender.c_fairy_train()
	# 测试保存培养结果：/x x_glb.net.sender.c_fairy_save_breed_result()
	# 精灵加EXP：
	# /x x_glb.net.get_fairy().add_exp(999)
	# #x player.fairy.add_exp(999)

	# 如果某些功能无效，请看SERVER LOG
	@auto_hide
	def on_s_fairy_feed_soul(self, msg):
		fairy = self.get_fairy()
		if fairy is None: return
		old_level = fairy.rank_level
		old_exp = fairy.rank_exp
		for ball in msg.ball: fairy.add_rank_exp_by_ball(ball)
		x_glb.my_data.rebuild_all_attr(True)
		import x_ccui_fairy
		if x_ccui_fairy.CCUI.instance().visible: x_ccui_fairy.CCUI.instance().on_zhuling_result(msg)
		new_level = fairy.rank_level
		new_exp = fairy.rank_exp
		if len(msg.ball) > 0:
			if old_level != new_level:
				x_ccui_notice.CCUI.instance().info(x_text.BATCH_ZHULING_SUCCESS1 % (len(msg.ball), new_level))
			else:
				x_ccui_notice.CCUI.instance().info(x_text.BATCH_ZHULING_SUCCESS2 % (len(msg.ball), new_exp-old_exp))
			x_glb.my_data.new_flag_mgr.check(x_new_flag_define.FAIRY_TAB4_ZHULING)

	@auto_hide
	def on_s_fairy_breed(self, msg):
		fairy = self.get_fairy()
		if fairy is None: return
		import x_ccui_fairy
		if x_ccui_fairy.CCUI.instance().visible: x_ccui_fairy.CCUI.instance().on_feed_result(msg)

		# 保存培养结果只需要：
		# 1.向服务端发送：c_save_breed_result
		# 2.客户端自行调用fairy.save_breed_result(msg.attr_deltas)进行保存

	@auto_hide
	def on_s_fairy_train(self, msg):
		fairy = self.get_fairy()
		if fairy is None: return
		old_attrs = zip(fairy.train_attr_levels, fairy.train_attr_exps)
		fairy.blue_diamond_train_count += msg.diamond_train_count
		for i in xrange(0, int(len(msg.patterns)/x_misc_consts.FAIRY_TRAIN_PATTERN_COUNT)):
			fairy.add_train_exp_by_patterns(msg.patterns[i*x_misc_consts.FAIRY_TRAIN_PATTERN_COUNT:(i+1)*x_misc_consts.FAIRY_TRAIN_PATTERN_COUNT])
		x_glb.my_data.rebuild_all_attr(True)
		import x_ccui_fairy
		x_ccui_fairy.CCUI.instance().on_train_result(msg)
		if len(msg.patterns) <= 0: 
			error_code = msg.error_code_list[-1]
			x_ccui_notice.CCUI.instance().info(x_text.FMT[error_code])
			return
		x_glb.my_data.new_flag_mgr.check(x_new_flag_define.FAIRY_TAB2_TRAIN)
		new_attrs = zip(fairy.train_attr_levels, fairy.train_attr_exps)
		zh_names = [x_fight_attr_num.EN_2_SHOW_NAME[attr] for attr in fairy.get_train_attr_names()]
		def _show_notice(i, error_code=None):
			if error_code:
				x_ccui_notice.CCUI.instance().info(x_text.FMT[error_code])
				return
			if old_attrs[i][0] != new_attrs[i][0]:
				x_ccui_notice.CCUI.instance().info(x_text.BATCH_TRAIN_SUCCESS1 % (int(len(msg.patterns)/x_misc_consts.FAIRY_TRAIN_PATTERN_COUNT), zh_names[i], new_attrs[i][0]))
			elif new_attrs[i][1] != old_attrs[i][1]:
				x_ccui_notice.CCUI.instance().info(x_text.BATCH_TRAIN_SUCCESS2 % (int(len(msg.patterns)/x_misc_consts.FAIRY_TRAIN_PATTERN_COUNT), zh_names[i], new_attrs[i][1] - old_attrs[i][1]))

		for i, v in enumerate(old_attrs):
			x_glb.world.per_sec_callout.add(1 + i * 0.3, _show_notice, i)
		if msg.error_code_list[-1] != 0:
			x_glb.world.per_sec_callout.add(1 + i * 0.3, _show_notice, i, msg.error_code_list[-1])

	def on_s_fairy_add_exp(self, msg):
		fairy = self.get_fairy()
		if fairy is None: return
		prev_level = fairy.level
		fairy.add_exp(msg.exp)
		if prev_level != fairy.level:
			x_glb.my_data.rebuild_all_attr(True)
			x_glb.my_data.new_flag_mgr.on_fairy_level_up()
		import x_ccui_fairy
		ui = x_ccui_fairy.CCUI.try_get_instance()
		if ui:
			ui.show_base_info()
		
	@auto_hide
	def on_s_notice(self, msg):
		type_2_func = {
		x_common_consts.NOTICE_TYPE_INFO: x_ccui_notice.CCUI.instance().info,
		x_common_consts.NOTICE_TYPE_WARNING: x_ccui_notice.CCUI.instance().warning,
		x_common_consts.NOTICE_TYPE_ERROR: x_ccui_notice.CCUI.instance().error,
		x_common_consts.BROADCAST_TYPE_INFO: x_ccui_notice.CCUI.instance().info,
		x_common_consts.BROADCAST_TYPE_WARNING: x_ccui_notice.CCUI.instance().warning,
		x_common_consts.BROADCAST_TYPE_ERROR: x_ccui_notice.CCUI.instance().error,
		}
		type_2_func[msg.msg_type](msg.msg)

	@auto_hide
	def on_s_map_data(self, msg):
		pass

	def on_s_sync_unsigned(self, msg):
		self._on_s_sync_single_attr(msg)
	def on_s_sync_signed(self, msg):
		self._on_s_sync_single_attr(msg)
	def on_s_sync_float(self, msg):
		self._on_s_sync_single_attr(msg)
	
	def _on_s_sync_single_attr(self, msg):
		x_glb.my_data.attr_update_single(msg.idx, msg.val)

	def on_s_sync_attr(self, msg):
		logs = x_serialize.loads(msg.pickled_log_list)
		x_glb.my_data.attr_update(logs)

	def on_s_sync_map_rec(self, msg):
		attrs = x_serialize.loads(msg.attrs)
		x_glb.my_data.update_map_rec(msg.map_id, attrs, msg.area_star)

	def on_s_open_maps(self, msg):
		x_glb.my_data.add_map_recs(msg.new_maps)

	def on_s_daily_reset(self, msg):
		x_glb.my_data.daily_mgr.reset()

	@auto_hide
	def on_s_levelup_passive_skill(self, msg):
		me = self.get_my_data()
		if me and msg.is_ok:
			pskill = me.passive_skills[msg.tid - 1]
			pskill.do_level_up()
			me.rebuild_all_attr(force=True)
			x_glb.my_data.emit_signal(x_signal_data.SG_PSKILL_UPDATE, msg.tid)

	def on_c_buff_sync(self, msg):
		obj = x_glb.world.scene.get_object(msg.pid)
		if not obj:
			return
		buff_mgr = getattr(obj, "buff_mgr", None)
		if buff_mgr is None:
			return
		buff_mgr.unpack(msg.data)

	@auto_hide
	def on_s_arena_notify(self, msg):
		import x_ccui_arena
		ui_arena = x_ccui_arena.CCUI.try_get_instance()
		if not ui_arena:
			return
		if msg.result != x_common_consts.GOTO_GAME_OK:
			description = x_text.FMT[msg.result]
			ui_arena.show_message(description)

	def on_s_arena_enter(self, msg):
		import x_ccui_arena
		ui_arena = x_ccui_arena.CCUI.instance()
		player_info = msg.player[0]
		ui_arena.refresh(player_info)
		if msg.prize:
			ui_arena.show_prize(cPickle.loads(msg.prize))
		ui_arena.set_prize_cd(msg.prize_cd)

	@auto_hide
	def on_s_arena_rivals(self, msg):
		import x_ccui_arena
		ui_arena = x_ccui_arena.CCUI.instance()
		ui_arena.refresh_rivals(msg.rivals)
		ui_arena.is_ready = True

	def on_s_arena_game_result(self, msg):
		if msg.is_win:
			import x_ccui_arena_win
			ui_arena_result = x_ccui_arena_win.CCUI.instance()
		else:
			import x_ccui_arena_end
			ui_arena_result = x_ccui_arena_end.CCUI.instance()
		if msg.prize:
			ui_arena_result.set_prize(cPickle.loads(msg.prize))

	def on_s_arena_best_rank(self, msg):
		import x_ccui_arena_win
		ui_arena_result = x_ccui_arena_win.CCUI.try_get_instance()
		if ui_arena_result:
			prize = cPickle.loads(msg.prize) if msg.prize else None
			ui_arena_result.set_best_rank_prize(prize)

	def on_s_arena_game_end(self, msg):
		x_glb.world.game_end(msg)

	def on_s_arena_get_prize(self, msg):
		import x_ccui_arena
		ui_arena = x_ccui_arena.CCUI.instance()
		if msg.prize:
			ui_arena.show_prize(cPickle.loads(msg.prize), True)
			ui_arena.set_prize_cd(msg.prize_cd)

	def on_s_xingzuo_levelup(self, msg):
		me = x_glb.my_data
		if not me:
			return
		if not me.xingzuos:
			return
		if msg.result == x_common_consts.XINGZUO_LEVELUP_FAIL:
			return
		xingzuo = me.xingzuos[msg.tid - 1]
		import x_ccui_xingzuo
		ui = x_ccui_xingzuo.CCUI.instance()
		if msg.result == x_common_consts.XINGZUO_LEVELUP_SUCCESS:
			xingzuo.do_level_up()
			x_glb.my_data.rebuild_all_attr(True)
			ui.on_levelup_ok(xingzuo)
		else:
			xingzuo.do_level_fail()
			ui.on_levelup_fail(xingzuo)

	@auto_hide
	def on_s_revive(self, msg):
		if msg.result == x_common_consts.RESURRECTION_NO_TIME:
			x_ccui_notice.CCUI.instance().error(x_text.RESURRECTION_NO_TIME)
			return
		elif msg.result == x_common_consts.RESURRECTION_NO_BLUE_DIAMOND:
			x_ccui_notice.CCUI.instance().error(x_text.NO_BLUE_DIAMOND)
			return
		if msg.result == 0:
			import x_ccui_misc_resurrection
			ui = x_ccui_misc_resurrection.CCUI.try_get_instance()
			if ui: ui.destroy()
			player = x_glb.world.scene.get_object(msg.pid)
			if not player:
				return
			player.revive()
			player.remain_resurrection_time = msg.remain_time

	@auto_hide
	def on_s_ranking_list(self, msg):
		#print("on_s_ranking_list:%s" % msg)
		#x_glb.data.data_cache.cache_ranking_list.msg_proc(msg)
		x_glb.my_data.on_ranking_list(msg)

	@auto_hide
	def on_s_do_worship(self, msg):
		#print("on_s_do_worship:%s" % msg)
		if msg.result == 0:
			me = x_glb.my_data
			me.worship = me.worship | (1 << msg.ranking_type)
			rewards = x_common_util.get_worship_reward()
			x_ccui_notice.CCUI.instance().info(x_text.WORSHIP_SUCCESS_TIPS % (rewards.get("gold", 0), rewards.get("honor", 0)))
			x_glb.my_data.new_flag_mgr.check(x_new_flag_define.RANK_TABS)

	def on_s_worship_reward(self, msg):
		x_ccui_ranking_list.CCUI.instance().on_worship_reward(msg)


	#邮件模块相关协议
	def on_s_mail_insert(self, msg):
		print "on_s_mail_insert:", msg

	@auto_hide
	def on_s_mail_list(self, msg):
		print "on_s_mail_list:", msg
		x_glb.data.data_cache.cache_mail.msg_proc(msg)
		
		x_glb.my_data.new_flag_mgr.check(x_new_flag_define.MAIL)

	def on_s_mail_read(self, msg):
		print "on_s_mail_read:", msg

	def on_s_mail_delete(self, msg):
		print "on_s_mail_delete:", msg

	@auto_hide
	def on_s_mail_fetch(self, msg):
		print "on_s_mail_fetch:", msg
		x_ccui_mailbox.CCUI.instance().on_fetch_result(msg)
		
		x_glb.my_data.new_flag_mgr.check(x_new_flag_define.MAIL)

	@auto_hide
	def on_s_query_role(self, msg):
		import x_ccui_relation
		x_ccui_relation.CCUI.instance().on_s_query_role(msg)
		
	@auto_hide
	def on_s_query_recommend_players(self, msg):
		import x_ccui_relation
		x_ccui_relation.CCUI.instance().on_s_query_recommend_players(msg)
	
	@auto_hide
	def on_s_get_relation(self, msg):
		print "relation coreobj created!"
		mydata = ( x_glb.my_data )
		
		import x_relation
		mydata.relation = x_serialize.loads_with_coreobj(msg.base)
		
		import x_ccui_relation
		x_ccui_relation.CCUI.instance().on_relation_local_data_ready()
		
		print mydata.relation.detail()

	def on_s_trace_leak(self, msg):
		import zlib
		import x_objreport
		for dotname, data in zip(msg.dotname_list, msg.data_list):
			f = open(dotname, "w")
			data = zlib.decompress(data)
			f.write(data)
			f.close()
			x_objreport.draw_png(dotname)
			
	def _on_relation_change(self):
		import x_ccui_attr
		ui = x_ccui_attr.CCUI.try_get_instance()
		if ui and ui.layout == ui.LAYOUT_OTHER:
			ui.refresh_relation_buttons()
			
		import x_ccui_relation
		ui = x_ccui_relation.CCUI.try_get_instance()
		if ui:
			ui.refresh()
	
	def on_s_add_friend(self, msg):
		print "Add friend", msg.is_ok
		if msg.is_ok:
			obj = x_serialize.loads_with_coreobj(msg.base)
			
			my_data = x_glb.my_data
			my_data.relation.add_friend(obj.rid, obj)
			
			self._on_relation_change()
	
	def on_s_remove_friend(self, msg):
		print "Remove friend", msg.is_ok
		if msg.is_ok:
			my_data = x_glb.my_data
			my_data.relation.remove_friend(msg.rid)
			
			import x_ccui_attr
			ui = x_ccui_attr.CCUI.try_get_instance()
			if ui and ui.layout == ui.LAYOUT_OTHER:
				ui.refresh_relation_buttons()
				
			self._on_relation_change()

	def on_s_add_to_blacklist(self, msg):
		print "Add to blacklist", msg.is_ok
		if msg.is_ok:
			obj = x_serialize.loads_with_coreobj(msg.base)
			
			my_data = x_glb.my_data
			my_data.relation.add_to_blacklist(obj.rid, obj)
			
			self._on_relation_change()
	
	def on_s_remove_from_blacklist(self, msg):
		print "Remove from blacklist", msg.is_ok
		if msg.is_ok:
			my_data = x_glb.my_data
			my_data.relation.remove_from_blacklist(msg.rid)

			self._on_relation_change()
	
	def on_s_chat(self, msg):
		print "channel: %d, from_id=%d, from_vip=%d, text=%s" % (msg.channel,
																 msg.from_id,
																 msg.from_vip,
																 msg.text)
		import x_ccui_town_bottomleft
		ui = x_ccui_town_bottomleft.CCUI.try_get_instance()
		if ui is not None and ui.visible:
			ui.set_chat_text(msg.channel, msg.from_name, msg.text)

	def on_s_get_stam(self, msg):
		if msg.result == 0:
			my_data = x_glb.my_data
			my_data.worship =  my_data.worship | (1 << x_common_consts.WORSHIP_BIT_GET_STAM_1 + msg.stam_type)
			x_ccui_notice.CCUI.instance().info(x_text.GET_STAM_SUCCESS % x_common_consts.GET_STAM_COUNT)
		else:
			x_ccui_notice.CCUI.instance().error(msg.result == 1 and x_text.GET_STAM_ALREADY or x_text.NOT_IN_GET_STAM_TIME)

	@auto_hide
	def on_s_open_box(self, msg):
		if msg.result == 0:
			x_ccui_notice.CCUI.instance().info(x_text.OPEN_BOX_SUCCESS)
			import x_ccui_map_entrance
			x_ccui_map_entrance.CCUI.instance().on_box_opened(msg.area_id, msg.box_id)
			x_glb.my_data.on_area_box_opened(msg.area_id, msg.box_id)
		else:
			x_ccui_notice.CCUI.instance().info(x_text.OPEN_BOX_FAILED)

	@auto_hide
	def on_s_wipe_map(self, msg):
		import x_ccui_map_detail_wipe
		x_ccui_map_detail_wipe.CCUI.instance().on_wipe_map(msg)

	@auto_hide
	def on_s_soul_levelup(self, msg):
		if msg.is_ok:
			import x_ccui_soul_info
			import x_ccui_soul
			instance = x_ccui_soul_info.CCUI.instance()
			for tid in x_common_consts.SOUL_GRAIN_TID_LIST:
				instance.grain_num[tid] = 0
			soul = x_glb.my_data.soul_mgr.atlas_list[msg.tid]
			base = soul.get_base_from_string(msg.pickled_soul)
			soul.level = base["level"]
			soul.exp = base["exp"]
			x_glb.my_data.rebuild_all_attr(force=True)
			max_level = x_common_consts.SOUL_MAX_LEVEL_LIST[soul.rank - 1]
			if soul.level == max_level:
				instance.on_show_foster()
			else:
				if instance.tid is not None and instance.tid > 0:
					instance.show()
			instance = x_ccui_soul.CCUI.try_get_instance()
			if instance:
				instance.refresh_atlas(msg.tid)
			x_glb.my_data.new_flag_mgr.check("SOUL_ICONS%d" % soul.chapter)
			x_glb.my_data.new_flag_mgr.check(x_new_flag_define.SOUL_TAB3_FETE)
		else:
			x_ccui_notice.CCUI.instance().info(x_text.SOUL_LVLUP_FAILED)

	@auto_hide
	def on_s_soul_rankup(self, msg):
		if msg.is_ok:
			soul = x_glb.my_data.soul_mgr.atlas_list[msg.tid]
			base = soul.get_base_from_string(msg.pickled_soul)
			soul.rank = base["rank"]
			soul.soul_stone = base["soul_stone"]
			soul.exp = base["exp"]
			x_glb.my_data.rebuild_all_attr(force=True)
			x_glb.my_data.new_flag_mgr.check("SOUL_ICONS%d" % soul.chapter)
			import x_ccui_soul
			import x_ccui_soul_info
			inst = x_ccui_soul_info.CCUI.try_get_instance()
			if inst:
				inst.hide()
			inst = x_ccui_soul.CCUI.try_get_instance()
			if inst:
				inst.refresh_atlas(msg.tid)
		else:
			x_ccui_notice.CCUI.instance().info(x_text.SOUL_RANKUP_FAILED)

	def on_s_soul_add_stone(self, msg):
		soul = x_glb.my_data.soul_mgr.atlas_list[msg.tid]
		base = soul.get_base_from_string(msg.pickled_soul)
		soul.soul_stone = base["soul_stone"]
		
		x_glb.my_data.new_flag_mgr.check("SOUL_ICONS%d" % soul.chapter)
		x_glb.my_data.new_flag_mgr.check(x_new_flag_define.SOUL_TAB3_FETE)

	@auto_hide
	def on_s_soul_refresh_colosseum(self, msg):
		if msg.is_ok:
			soul_mgr = x_glb.my_data.soul_mgr
			soul_mgr.colosseum_list = x_serialize.loads(msg.colosseum_list)
			import x_ccui_colosseum
			inst = x_ccui_colosseum.CCUI.try_get_instance()
			if inst:
				inst.refresh_all_slots()
				inst.refresh_slot_info()
		else:
			x_ccui_notice.CCUI.instance().info(x_text.SOUL_RES_NOT_ENOUGH)

	@auto_hide
	def on_s_soul_fetch(self, msg):
		if msg.is_ok:
			soul = x_glb.my_data.soul_mgr.atlas_list[msg.tid]
			base = soul.get_base_from_string(msg.pickled_soul)
			soul.soul_stone = base["soul_stone"]
			soul.colosseum_level = base["colosseum_level"]
			import x_ccui_colosseum_win
			instance = x_ccui_colosseum_win.CCUI.instance()
			instance.set_result(soul.tid)
			instance.show()
		else:
			x_ccui_notice.CCUI.instance().info(x_text.SOUL_RES_NOT_ENOUGH)

	def on_s_soul_unlock(self, msg):
		atlas_list = x_glb.my_data.soul_mgr.atlas_list
		tid_list = x_serialize.loads(msg.tid_list)
		for tid in tid_list:
			import x_monster_soul
			soul_base = {"tid": tid, "level": 1, "rank": 0, "exp": 0, "soul_stone": 0, "colosseum_level": x_misc_consts.COLOSSEUM_MIN_LEVEL}
			soul = x_monster_soul.CObj()
			soul.on_create(soul_base)
			atlas_list[tid] = soul
			x_glb.my_data.new_flag_mgr.check("SOUL_ICONS%d" % soul.chapter)

	def on_s_soul_activate_fete(self, msg):
		if msg.is_ok:
			soul_mgr = x_glb.my_data.soul_mgr
			import x_monster_soul_mgr_attr
			fete_item = x_monster_soul_mgr_attr.DATA["table_sheets"]["魂祭表"][msg.fete_id]
			for idx in xrange(1, 6):
				tid = fete_item["魂兽%d" % idx]
				need_num = fete_item["数量%d" % idx]
				if tid == 0:
					continue
				soul = soul_mgr.atlas_list[tid]
				soul.consume_soul_stone(need_num)
			soul_mgr.fete_list.append(msg.fete_id)
			soul_mgr.fete_attr_list = x_serialize.loads(msg.fete_attr_list)
			x_glb.my_data.rebuild_all_attr(force=True)
			# 显示成功，刷新魂祭界面
			x_ccui_notice.CCUI.instance().info(x_text.SOUL_ACTIVATE_OK)
			import x_ccui_soul
			instance = x_ccui_soul.CCUI.instance()
			instance.on_tab_selected(2, None)
			
			x_glb.my_data.new_flag_mgr.check(x_new_flag_define.SOUL_TAB3_FETE)
		else:
			x_ccui_notice.CCUI.instance().info(x_text.SOUL_ACTIVATE_FAILED)

	@auto_hide
	def on_s_soul_buy_grain(self, msg):
		if msg.is_ok:
			x_ccui_notice.CCUI.instance().info(x_text.SOUL_BUY_GRAIN_OK)
			import x_ccui_soul_info
			instance = x_ccui_soul_info.CCUI.instance()
			instance.show()
		else:
			x_ccui_notice.CCUI.instance().info(x_text.SOUL_BUY_GRAIN_FAILED)

	@auto_hide
	def on_s_soul_challenge_again(self, msg):
		if msg.err:
			x_ccui_notice.CCUI.instance().error(x_text.FMT[msg.err])
		else:
			import x_ccui_colosseum_win
			inst = x_ccui_colosseum_win.CCUI.try_get_instance()
			if inst:
				inst.destroy()
			world = x_glb.world
			if world and world.game_mode == x_common_consts.GAMEMODE_COLOSSEUM:
				pass

	@auto_hide
	def on_s_soul_level_down(self, msg):
		if msg.result != 0:  # fail
			x_glb.my_data.daily_mgr.colosseum_reset = x_serialize.loads(msg.down_list)
			x_ccui_notice.CCUI.instance().info(x_text.FMT[msg.result])
		else:  # success
			soul_mgr = x_glb.my_data.soul_mgr
			down_list = x_serialize.loads(msg.down_list)
			for (tid, colosseum_level) in down_list.iteritems():
				soul = soul_mgr.atlas_list[tid]
				soul.colosseum_level = colosseum_level
			x_glb.my_data.daily_mgr.colosseum_reset += 1
			x_ccui_notice.CCUI.instance().info(x_text.COLOSSEUM_RESET_SUCCESS)
		import x_ccui_colosseum
		inst = x_ccui_colosseum.CCUI.try_get_instance()
		if inst:
			inst.refresh_slot_info()

	@auto_hide
	def on_s_soul_update_link(self, msg):
		change_log = msg.log
		if not change_log:
			return
		import x_ccui_soul_info
		import x_ccui_soul
		cnt = len(change_log)
		i = 1
		battle_list = x_glb.my_data.soul_mgr.battle_list
		inst = x_ccui_soul.CCUI.try_get_instance()
		while i < cnt:
			slot_idx = change_log[i-1]
			soul_tid = change_log[i]
			battle_list[slot_idx] = soul_tid
			i += 2
			if inst:
				inst.set_slot(slot_idx + 1)
		inst = x_ccui_soul_info.CCUI.try_get_instance()
		if inst:
			inst.hide()
		x_glb.my_data.rebuild_all_attr(force=True)

	def on_s_do_daily_work(self, msg):
		x_glb.my_data.do_daily_work()

	@auto_hide
	def on_s_buy_res(self, msg):
		if msg.result != 0:  # fail
			x_ccui_notice.CCUI.instance().info(x_text.FMT[msg.result])
			return
		res_name, res_buy, res_ch_name = x_common_consts.BUY_RES_INFO[msg.buy_type]
		txt = x_text.BUY_RES_SUCCESS.format(amount=msg.amount, name=res_ch_name)
		if msg.critical > 1:
			txt = "%d倍暴击！" % msg.critical + txt
		x_ccui_notice.CCUI.instance().info(txt)
		# 增加当天购买次数
		cur_buy_times = getattr(x_glb.my_data.daily_mgr, res_buy, 0)
		cur_buy_times += 1
		setattr(x_glb.my_data.daily_mgr, res_buy, cur_buy_times)

	def on_costume_update(self):
		x_glb.my_data.rebuild_all_attr(force=True)
		
		import x_ccui_costume
		ui = x_ccui_costume.CCUI.try_get_instance()
		if ui:
			ui.refresh_equip_items()
			ui.populate_part_list()
			
		if x_glb.world.scene.is_town():
			x_glb.world.scene.me.avatar_mgr.update_costume()
		
		import x_ccui_attr	
		ui = x_ccui_attr.CCUI.try_get_instance()
		if ui:
			ui.update_avatar(*x_glb.my_data.get_costume_id())
		
	def on_s_costume_expire(self, msg):
		my_data = x_glb.my_data
		if not my_data:
			return
		my_data.costume.on_cos_expire(msg.expire)

		self.on_costume_update()
		
	@auto_hide	
	def on_s_costume_equip(self, msg):
		my_data = x_glb.my_data
		if not my_data:
			return
		if not msg.is_ok:
			return
		import x_costume_misc
		if msg.part_id == x_costume_misc.PART_ID_ALL:
			part_id_list = range(x_costume_misc.PART_COUNT)
		else:
			part_id_list = (msg.part_id,)

		if msg.activate:
			my_data.costume.activate(msg.cos_id, part_id_list)
		else:
			my_data.costume.equip(msg.cos_id, part_id_list)
		
		self.on_costume_update()
	
	def on_s_chest_free(self, msg):	
		if 0 == msg.chest_id:			
			import x_ccui_chest_homepage
			ui = x_ccui_chest_homepage.CCUI.try_get_instance()
			if ui:
				ui.on_show()
			else:
				print 'grsn1304:x_ccui_chest_homepage.CCUI.try_get_instance()获取失败'
	
	@auto_hide
	def on_s_chest_buy(self, msg):		
		print '购买成功'
		if 1 == msg.chest_id:			
			import x_ccui_chest_homepage
			ui = x_ccui_chest_homepage.CCUI.try_get_instance()
			
			
			"""
			if ui:
				ui.on_show()
			else:
				print 'grsn1304:x_ccui_chest_homepage.CCUI.try_get_instance()获取失败'	
				"""