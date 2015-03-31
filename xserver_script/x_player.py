# $Id: x_player.py 174680 2015-03-13 01:58:17Z ycwang@NETEASE.COM $
#-*- coding:gbk -*-
import x_serialize
import struct
import weakref
import datetime
import math
import time
import random
import hall_callback
import x_coreobj
import x_sceneobj

import x_item_bag
import x_map_record
import x_map_data

import x_consts
import x_common_util
import x_common_consts
import x_misc_consts

import x_multimsg
import x_multimsg_codec
import x_player_delta_sync_data
import x_player_skill_mgr
import x_new_flag_mgr
import x_task_mgr
import x_map_level
import x_emblem
import x_emblem_attr
import x_item_tree_data
import x_prize_data
import x_prize_mul_data
import x_gem_mgr
import x_area_data
import x_area_record
import x_item_creator
import x_fight_attr
import random
import x_sysopen_attr
import x_daily_data
import x_misc_consts
import x_errcode
import x_text
import x_vip_data
import x_chest

class CPlayerCookie(x_coreobj.CObj):
	CLASS_TAG = "player_cookie"
	BASE = {
		"map_id": 0,  # 要进入的副本ID
		"restore": False,  # 是否要restore
		"last_stam_recovery_time": 0,  # 上次体力回复的时间
		"last_arena_check_time": 0,  # 上次检查竞技场的时间
	}


class CObj(x_sceneobj.CObj):

	CLASS_TAG = "player"

	PATCH_MODULE_NAME = "x_player_attr"

	# 前3个参数，是scene_obj的参数
	# 后面是room_player的参数
	def __init__(self, scn=None, pid=None, tid=None,
			hall_player=None, room=None):
		super(CObj, self).__init__(scn, pid, tid)
		self.hall_player = hall_player
		# 平台字段
		self.room = room
		self.room_id = room.room_id	if room else 0  #当前所在房间号
		# uid和hid是冗余存储
		if hall_player:
			self.uid = hall_player.uid
			self.hid = hall_player.hid  # 玩家网络链接的唯一标识
		else:
			self.uid = 0
			self.hid = 0
		self.seat = None # 座位号, 从0开始, 由room分配
		self.is_ready = False # 多人模式下的准备状态
		self.gender = 1 # 玩家性别
		self.keep_town_clone = False # 保留城镇镜像
		self.town_clone_level = None # 生成城镇镜像那一刻的等级
		self.town_timer = 0  # 城镇中的计时器
		self.single_game_ctx = None  # 单人模式下, 游戏相关数据
		self.sync_set = []	# 在主城时需要同步自身坐标给此集合的玩家(UID)
		self.is_dead = False
		# 网络延迟(round-trip-time)毫秒数
		self.rtt = 0

		# 上次上排行榜的战斗力值
		self._ranking_battle_pow = 0
		
		# 上次存盘的绝对时间
		self._prev_save_db_time = int(time.time())

		# TODO: delete this
		# gm用一份存盘覆盖了自身的角色，这个时候，应该尽快下线，因为这个角色无论做什么都不会被存盘了。
		self._gm_restored = False

		self.gem_mgr = x_gem_mgr.CMgr(weakref.proxy(self))

	def _get_rid(self):
		return self._id
	rid = property(_get_rid)

	def _get_battle_pow(self):
		return x_common_util.get_battle_power(self, x_sysopen_attr.CHARA)
	battle_pow = property(_get_battle_pow)

	def on_create(self, base):
		super(CObj, self).on_create(base)

		self.is_gm_mode = True

		# 初始化各种背包
		if self.bag_1 is None:
			self.bag_1 = x_item_bag.CBag()
			self.bag_1.on_create({"bag_id": x_common_consts.BAG_ID_1, "owner_uid": self.uid,
				"max_page": 1, "max_slot_per_page": x_common_consts.BAG_NORMAL_MAX_ITEM_COUNT,
				"pages": None})
		if self.bag_2 is None:
			self.bag_2 = x_item_bag.CBag()
			self.bag_2.on_create({"bag_id": x_common_consts.BAG_ID_2, "owner_uid": self.uid,
				"max_page": 1, "max_slot_per_page": x_common_consts.BAG_NORMAL_MAX_ITEM_COUNT,
				"pages": None})
		if self.bag_3 is None:
			self.bag_3 = x_item_bag.CBag()
			self.bag_3.on_create({"bag_id": x_common_consts.BAG_ID_3, "owner_uid": self.uid,
				"max_page": 1, "max_slot_per_page": x_common_consts.BAG_NORMAL_MAX_ITEM_COUNT,
				"pages": None})

		if self.bag_wear is None:
			self.bag_wear = x_item_bag.CBag()
			self.bag_wear.on_create({"bag_id": x_common_consts.BAG_ID_WEAR, "owner_uid": self.uid,
				"max_page": 1, "max_slot_per_page": x_common_consts.BAG_WEAR_MAX_ITEM_COUNT,
				"pages": None})

		if self.bag_gem is None:
			self.bag_gem = x_item_bag.CBag()
			self.bag_gem.on_create({"bag_id": x_common_consts.BAG_ID_GEM, "owner_uid": self.uid,
				"max_page": 1, "max_slot_per_page": x_common_consts.BAG_GEM_MAX_ITEM_COUNT,
				"pages": None})

		self.bags = {}
		for bag in (self.bag_1, self.bag_2,self.bag_3, self.bag_wear, self.bag_gem):
			bag.set_player(self)
			self.bags[bag.bag_id] = bag

		# 武神纹章赋默认值
		if self.emblem is None:
			config = x_emblem_attr.DATA["table_sheets"]["配置表"]
			self.emblem = [None] * len(config)
			for part in config.iterkeys():
				emblem_obj = x_emblem.CObj()
				emblem_obj.on_create(base={"part": part})
				#self.print_msg("emblem_part: %s" % emblem_obj.part)
				self.emblem[emblem_obj.bag_wear_idx] = emblem_obj
		elif False:
			# 兼容补丁。TODO：求修正
			def fix_string(v):
				if ord(v[0]) >= 128:
					return v
				x = ""
				for i in xrange(0, len(v), 3):
					x += chr(int(v[i+1:i+3], 16))
				return x
			for emblem_obj in self.emblem:
				emblem_obj.part = fix_string(emblem_obj.part)

		if self.fairy is None:
			import x_fairy
			self.fairy = x_fairy.CObj()
			self.fairy.on_create({"tid": 1})

		if self.skill_mgr is None:
			self.skill_mgr = x_player_skill_mgr.CObj()
			self.skill_mgr.set_owner(weakref.proxy(self))
			self.skill_mgr.on_create({})
		else:
			self.skill_mgr.set_owner(weakref.proxy(self))

		if self.passive_skills is None:
			import x_passive_skill
			import x_passive_skill_attr
			config = x_passive_skill_attr.DATA["table_sheets"]["配置表"]
			self.passive_skills = [None] * len(config)
			for tid in config.iterkeys():
				pskill = x_passive_skill.CObj()
				pskill.on_create(base={"tid": tid, "level": 0, "addon_attr_value": 0})
				self.passive_skills[tid - 1] = pskill

		if self.xingzuos is None:
			import x_xingzuo
			import x_xingzuo_attr
			config = x_xingzuo_attr.DATA["table_sheets"]["配置表"]
			self.xingzuos = [None] * len(config)
			for tid in config.iterkeys():
				xingzuo = x_xingzuo.CObj()
				xingzuo.on_create(base={"tid": tid})
				self.xingzuos[tid - 1] = xingzuo

		if self.soul_mgr is None:
			import x_monster_soul_mgr
			soul_mgr = x_monster_soul_mgr.CObj()
			# define base
			colosseum_list = []
			for index in xrange(0, x_common_consts.COLOSSEUM_SLOT_NUM):
				colosseum_list.append({"lock": False, "type": x_common_consts.COLOSSEUM_TYPE_EMPTY,
					"buff": 0, "quality": 0, "tid": 0, "level": 0, "amount": 0})
			base = {"battle_list": [0] * 5, "atlas_list": {}, "colosseum_list": colosseum_list,
				"fete_list": [], "fete_attr_list": {}}
			soul_mgr.on_create(base)
			# soul_mgr.refresh_colosseum(x_common_consts.COLOSSEUM_REFRESH_FREE)
			self.soul_mgr = soul_mgr
		self.soul_mgr.set_owner(weakref.proxy(self))

		# 任务管理
		if self.task_mgr is None:
			self.task_mgr = x_task_mgr.CMgr()
			self.task_mgr.on_create()
			self.task_mgr.set_owner(weakref.proxy(self))
			self.task_mgr.init_daily_pool(
				level=x_sysopen_attr.DATA[x_sysopen_attr.DAILY_TASK]["open_level"],
				sync=False)
		else:
			self.task_mgr.set_owner(weakref.proxy(self))

		if self.done_tutorial is None:
			self.done_tutorial = {}

		# 副本记录
		if self.map_records is None:
			self.map_records = {}
		if self.area_records is None:
			self.area_records = {}

		# 关键掉落
		if self.treasure is None:
			self.treasure = {}

		# 时装
		if self.costume is None:
			import x_costume_mgr
			self.costume = x_costume_mgr.CObj()
			self.costume.on_create()
			
		# 非关键运行时信息
		if self.cookie is None:
			self.cookie = CPlayerCookie()
			t = self.logout_time
			base = {
				"last_stam_recovery_time": t,
				"last_arena_check_time": t,
			}
			self.cookie.on_create(base)
		
		# 宝箱
		if self.chest is None:					
			self.chest = x_chest.CObj()
			self.chest.on_create()
			self.room.print_msg('player 准备设置room')
		self.chest.init_data(self)
			
		
		#每日清空的记录信息
		if self.daily_mgr is None:
			self.daily_mgr = x_daily_data.CObj()
			self.daily_mgr.on_create()

		# 部分需要存储的小红点
		if self.new_flag_mgr is None:
			self.new_flag_mgr = x_new_flag_mgr.CObj()
			self.new_flag_mgr.on_create()
			
		# 提取记录, 用于支持安全的物品交换
		# if self.fetch_rec is None:
		# 	self.fetch_rec = {}

	def get_client_base_string(self):
		# 不发送到客户端的数据
		svr_attrs = ("treasure", "cookie")
		client_attrs = dict(self._base_)
		for k in svr_attrs:
			del client_attrs[k]
		return x_serialize.dumps_with_coreobj(client_attrs)

	def treasure_probability(self, prize_id, p0, p1, p2):
		data = self.treasure.get(prize_id, None)
		if data:
			s0, s1, s2 = data
		else:
			s0 = s1 = s2 = 0
		ret = [False, False, False]
		if p0:
			ret[0], s0 = self._dice(p0, s0)
		if p1:
			ret[1], s1 = self._dice(p1, s1)
		if p2:
			ret[2], s2 = self._dice(p2, s2)
		self.treasure[prize_id] = (s0, s1, s2)
		# self.print_msg("--> treasure_probability", (s0, s1, s2))
		return ret

	def _dice(self, pf, s):
		#####################################################
		## 1.令L=INT(10000/CEIL(1/P)),R=INT(10000/FLOOR(1/P))。	
		## 2.均匀随机出一个[L,R]的整数A，令当前积分S=S+A。	
		## 3.检定S：	
		## 3.1.若S>=10000，则S=0，将该道具加入掉落结果。	
		## 3.2.若S<10000，则该次不掉落。	
		#####################################################
		p, fac = pf  # 基础概率和倍率
		w = 10000
		inv_p = 1.0 / p
		l = int(max(1, math.floor(w / (inv_p + 1))))
		r = int(math.floor(w / (inv_p - 1)))
		#l = int(w/math.ceil(1.0/p))
		#r = int(w/math.floor(1.0/p))
		a = random.randint(l, r)
		# self.print_msg("\tdice:", "probability =", p, "; range =", (l, r),
		# "; result =", "%d (%d + %d)"%(s + a * fac, s, a * fac) )
		s += int(a * fac)
		if s >= w:
			s = 0
			#self.print_msg("\t!!!!!!!!BINGO!!!!!!!!")
			return True, s
		return False, s

	# 重置每日数据
	def do_daily_work(self):
		# 刷新副本记录
		invalid_maps = []
		all_map = x_map_data.DATA
		for map_id, rec in self.map_records.iteritems():
			map_data = all_map.get(map_id, None)
			if map_data is None:
				# this map is not available anymore
				invalid_maps.append(map_id)
				continue
			rec.tickets = map_data.get("daily_tickets", 0)
			rec.buy_tickets = 0
		if invalid_maps:
			for map_id in invalid_maps:
				del self.map_records[map_id]
		# 刷新任务
		self.task_mgr.on_daily_work()
		# 刷新精灵每日训练次数
		if self.fairy is not None:
			self.fairy.blue_diamond_train_count = 1
		#--------------------------------------------
		# 属性刷新
		log = {}
		if self.cur_stam < self.max_stam:  # 刷新体力
			self.add_coin(x_common_consts.COIN_TYPE_CUR_STAM, self.max_stam - self.cur_stam,
				x_consts.REASON_DAILY_RECOVERY, log)
		self.modify_attr("worship", 0, x_consts.REASON_DAILY_RECOVERY, log)  # 膜拜次数
		if self.arena_ticket < x_misc_consts.AERNA_DAILY_TICKET:  # 竞技场挑战次数
			self.modify_attr("arena_ticket", x_misc_consts.AERNA_DAILY_TICKET,
				x_consts.REASON_DAILY_RECOVERY, log)
		# 同步属性
		self.send_to_self("s_sync_attr", pickled_log_list=x_serialize.dumps(log))
		# 属性刷新结束
		#--------------------------------------------

		# todo: 测试期间每天发一封邮件
		self.room.send_mail(self.rid, "G30日报", "请继续努力，喵！", mail_type=x_common_consts.MAIL_TYPE_GM)

		#刷新宝箱每日数据
		if self.chest:
			self.chest.on_daily_work()
		
		#刷新每日数据
		if self.daily_mgr:
			self.daily_mgr.reset()
			self.send_to_self("s_daily_reset")
		return True

	# 房间玩家退出
	# 这里做存盘操作，保存非平台数据到游戏独立数据库中
	def destroy(self):
		self.save_db_props()
		if self.gem_mgr is not None:
			self.gem_mgr.destroy()
			self.gem_mgr = None
		if self.skill_mgr is not None:
			self.skill_mgr.destroy()
			self.skill_mgr = None
		super(CObj, self).destroy()

	# 将字典存到数据库中
	def save_db_props(self, callback=None, callback_args=None):
		if self._gm_restored:
			self.print_msg("_gm_restored is True, skip")
			return

		# 写数据库
		self.digest_battle_pow = self.battle_pow
		sql = self.__class__.gen_sql_update_table()
		param = self.save_to_sql_base()
		self.room.sql_execute(sql, param, room_player=self, callback=callback, data=callback_args)
		# 记录时间
		self._prev_save_db_time = int(time.time())
		# 写日志
		self.room.report("SAVE", self.uid, 0)

		# 更新摘要信息
		base = {
			"vip": self.vip,
			"level": self.level,
			"battle_pow": self.battle_pow,
		}
		self.room.send_to_static_room("rc_up_digest", rid=self.rid,
			base=x_serialize.dumps(base))

	def get_digest(self):
		import x_player_digest
		_BASE = x_player_digest.CObj.BASE
		_base = {}
		for k, v in _BASE.iteritems():
			_base[k] = getattr(self, k, v)
		_base["_id"] = self.rid
		return x_serialize.dumps(_base)

	def tell(self, msg):
		self.send_to_self("s_tell", msg=msg)

	# 申请开启gm模式
	def open_gm_mode(self):
		if hall_callback.is_debug(): # TODO：判断数据库中的标志
			self.is_gm_mode = True
			return True

		# 非内服，必须存档中的gm_level > 0
		if self.gm_level > 0:
			self.is_gm_mode = True
			return True
		return False

	def print_msg(self, *args):
		s = (str(a) for a in args)
		self.room.print_msg(" ".join(s))

	# 关闭gm模式
	def close_gm_mode(self):
		if self.is_gm_mode: # 处于gm模式的才返回True
			self.is_gm_mode = False
			return True
		return False

	def send_to_self(self, proto_name, *args, **kargs):
		pack_func = getattr(self.room.msg_mgr, proto_name)
		msg = pack_func(*args, **kargs)
		self.room.cghall_send(self.hid, msg)

	def send_to_others(self, proto_name, *args, **kargs):
		pack_func = getattr(self.room.msg_mgr, proto_name)
		msg = pack_func(*args, **kargs)
		self.room.cghall_broadcast(msg, exclude=[self.hid])

	def send_to_self_msg(self, msg):
		self.room.cghall_send(self.hid, msg)

	def send_to_all_msg(self, msg):
		self.room.cghall_broadcast(msg)

	def send_to_others_msg(self, msg):
		self.room.cghall_broadcast(msg, exclude=[self.hid])

	def get_addon_attrs_to_self(self):
		return x_common_util.get_player_addon_attrs(self)

	# 设置副本ID, 是否自动开始(单人)
	def prepare_enter_game(self, map_id):
		self.cookie.map_id = map_id

	def on_level_up(self, sync=True):
		# 玩家升级时的回调函数
		# 根据当前等级开启副本
		if self.level < len(x_map_level.DATA):
			new_maps = x_map_level.DATA[self.level]
			if new_maps:
				self.open_maps(new_maps, sync)
		# self.debug_print_map_records()

		# 首次刷新挑战任务
		if self.level == x_sysopen_attr.DATA[x_sysopen_attr.CHALLENGE_TASK]["open_level"]:
			self.task_mgr.init_challenge_pool()
		# 首次刷新魂兽场
		if self.level == x_misc_consts.COLOSSEUM_FIRST_REFRESH_LEVEL:
			self.soul_mgr.refresh_colosseum(x_common_consts.COLOSSEUM_REFRESH_FREE)

	# 获得经验值并升级
	def add_exp(self, exp, reason=0, log=None):
		import x_player_attr
		exp_table = x_player_attr.DATA["table_sheets"]["经验表"]
		if (self.level + 1) not in exp_table:
			# 到达最大等级限制
			return
		exp = max(0, exp)
		self.cur_exp += exp
		prev_level = self.level
		
		# 记录精灵获得的经验，未到开放等级不取得经验
		fairy_open_level = x_sysopen_attr.DATA[x_sysopen_attr.FAIRY]["open_level"]
		if self.level < fairy_open_level:
			fairy_exp = self.cur_exp
		else:
			fairy_exp = exp
		while self.cur_exp >= self.level_exp:
			self.cur_exp -= self.level_exp
			if self.level < fairy_open_level:
				fairy_exp -= self.level_exp
			self.level += 1
			self.on_level_up()
			if (self.level + 1) not in exp_table:
				# 到达最大等级限制
				self.cur_exp = 0
				break
		if self.level < fairy_open_level:
			fairy_exp = 0
		
		if log is None:
			log = {}
			need_send = True
		else:
			need_send = False
		if prev_level != self.level:
			attr_idx = self.__class__.en_2_num("level")
			log[attr_idx] = self.level
		attr_idx = self.__class__.en_2_num("cur_exp")
		log[attr_idx] = self.cur_exp
		if need_send:
			self.send_to_self("s_sync_attr", pickled_log_list=x_serialize.dumps(log))
		# self.print_msg("[GAIN] --> Exp: %d (+%d)"%(self.cur_exp, exp), "(Lv.%d->Lv.%d)"%(prev_level, self.level) if prev_level != self.level else "")
		
		# 同步更新精灵的经验
		if self.fairy:
			self.fairy.add_exp(fairy_exp)
			self.send_to_self("s_fairy_add_exp", exp=fairy_exp)

		self.rebuild_all_attr()
		
	# 修改基础属性
	def modify_attr(self, attr_name, value, reason=0, log=None):
		setattr(self, attr_name, value)
		new_value = getattr(self, attr_name)
		attr_idx = self.__class__.en_2_num(attr_name)
		if log is None:
			self.send_to_self("s_sync_unsigned", idx=attr_idx, val=new_value)
		else:
			log[attr_idx] = new_value
		# self.print_msg("[GAIN] --> %s: %d (+%d)"%(coin_name, v, amount))
		return True

	def _get_diamond(self):
		return self.blue_diamond + self.red_diamond
	diamond = property(_get_diamond)

	# 获得货币/星石/荣誉等等
	# 该接口不会失败, 如果试图修改无效的属性, 会抛异常
	def add_coin(self, coin_name, amount, reason=0, log=None):
		v = getattr(self, coin_name)
		v += max(amount, 0)
		setattr(self, coin_name, v)
		attr_idx = self.__class__.en_2_num(coin_name)
		if log is None:
			self.send_to_self("s_sync_unsigned", idx=attr_idx, val=v)
		else:
			log[attr_idx] = getattr(self, coin_name)
		# self.print_msg("[GAIN] --> %s: %d (+%d)"%(coin_name, v, amount))
		return True

	# 扣除货币/星石/荣誉等等, 返回是否扣除成功
	def sub_coin(self, coin_name, amount, reason=0, log=None):
		if coin_name == x_common_consts.COIN_TYPE_BLUE_DIAMOND:
			return self.sub_diamond(amount, reason, log)
		v = getattr(self, coin_name)
		if v < amount:
			return False
		v -= max(0, amount)
		setattr(self, coin_name, v)
		attr_idx = self.__class__.en_2_num(coin_name)
		if log is None:
			self.send_to_self("s_sync_unsigned", idx=attr_idx, val=v)
		else:
			log[attr_idx] = getattr(self, coin_name)
		return True

	def sub_diamond(self, amount, reason=0, log=None):
		if self.blue_diamond + self.red_diamond < amount:
			return False
		idx_blue = self.__class__.en_2_num("blue_diamond")
		if self.blue_diamond >= amount:
			self.blue_diamond -= amount
			if log is None:
				self.send_to_self("s_sync_unsigned", idx=idx_blue, val=self.blue_diamond)
			else:
				log[idx_blue] = self.blue_diamond
		else:
			amount -= self.blue_diamond
			self.blue_diamond = 0
			self.red_diamond -= amount
			idx_red = self.__class__.en_2_num("red_diamond")
			if log is None:
				log = {
				idx_blue: 0,
				idx_red: self.red_diamond
				}
				self.send_to_self("s_sync_attr", pickled_log_list=x_serialize.dumps(log))
			else:
				log[idx_blue] = 0
				log[idx_red] = self.red_diamond
		return True

	def has_enough_coin(self, coin_name, value):
		if getattr(self, coin_name, 0) >= value:
			return True
		if coin_name == "blue_diamond":
			return (self.blue_diamond + self.red_diamond) >= value
		return False

	def has_enough_coins(self, name2amount):
		for coin_name, amount in name2amount.iteritems():
			has_amount = getattr(self, coin_name)
			if amount < 0 or has_amount < amount:
				return False
		return True

	# 该接口不会失败, 如果试图修改无效的属性, 会抛异常
	def add_many_coins(self, name2amount, reason=0, log=None):
		if log is None:
			log = {}
			need_send = True
		else:
			need_send = False
		for coin_name, amount in name2amount.iteritems():
			v = getattr(self, coin_name)
			v += max(amount, 0)
			setattr(self, coin_name, v)
			attr_idx = self.__class__.en_2_num(coin_name)
			log[attr_idx] = v
		if need_send:
			self.send_to_self("s_sync_attr", pickled_log_list=x_serialize.dumps(log))
		return True

	# 批量消耗多种货币, 要么全部成功, 要么不改变原有货币
	def consume_coins(self, name2amount, reason=0, log=None):
		if not self.has_enough_coins(name2amount):
			return False
		if log is None:
			log = {}
			need_send = True
		else:
			need_send = False
		for coin_name, amount in name2amount.iteritems():
			has_amount = getattr(self, coin_name)
			has_amount -= max(amount, 0)
			setattr(self, coin_name, has_amount)
			attr_idx = self.__class__.en_2_num(coin_name)
			log[attr_idx] = has_amount
		if need_send:
			self.send_to_self("s_sync_attr", pickled_log_list=x_serialize.dumps(log))
		return True

	def sync_coin(self, coin_name):
		idx = self.__class__.en_2_num(coin_name)
		if idx is not None:
			self.send_to_self("s_sync_unsigned", idx=idx, val=getattr(self, coin_name))

	# 添加物品
	def add_item(self, item, reason=0, log=None):
		if log is None:
			log = []
			need_send = True
		else:
			need_send = False
		is_ok = item.assign_to(self, log=log)
		if is_ok and need_send:
			self.send_to_self("s_item_log_list", pickled_log_list=x_serialize.dumps(log))
		# self.print_msg("[GAIN] --> %s: %d" % (item.show_name, amount))
		return is_ok

	# 添加多种物品
	def add_many_items(self, item_list, reason=0, log=None):
		bag2items = {}
		for item_obj in item_list:
			bag_id = item_obj.get_bag_id()
			if not bag_id:
				raise Exception("{0} can't add to bag".format(str(item_obj)))
			bag2items.setdefault(bag_id, []).append(item_obj)
		if not bag2items:
			return False
		for bag_id, items in bag2items.iteritems():
			bag = self.get_bag_by_id(bag_id)
			if not bag.can_add_many(items):
				return False
		if log is None:
			log = []
			need_send = True
		else:
			need_send = False
		for bag_id, items in bag2items.items():
			for item_obj in items:
				if not item_obj.assign_to(self, log=log):
					raise Exception("add item failed")
		if need_send:
			self.send_to_self("s_item_log_list", pickled_log_list=x_serialize.dumps(log))
		return True

	def remove_item(self, bag_id, pidx, sidx, amount=0, reason=0, log=None):
		bag = self.get_bag_by_id(bag_id)
		if not bag:
			self.print_msg("NO BAG", bag_id)
			return False, None
		item = bag.peek(pidx, sidx)
		if not item:
			self.print_msg("NO ITEM")
			return False, None
		if log is None:
			log = []
			need_send = True
		else:
			need_send = False
		if amount > 0:
			amount_left, log = bag.remove_amount(item, amount, log=log)
		else:
			log = bag.remove(pidx, sidx, log=log)
		if need_send:
			self.send_to_self("s_item_log_list", pickled_log_list=x_serialize.dumps(log))
		return True, item

	# 消耗品 -->《消耗品.xls》
	def add_consumption_item(self, item_tid, amount, reason=0, log=None):
		import x_item_consumption_attr
		if item_tid not in x_item_consumption_attr.DATA["table_sheets"]["配置表"]:
			return False
		item_list = x_item_creator.create_and_split_item(0, item_tid, amount)
		if len(item_list) > 1:
			is_ok = self.add_many_items(item_list, reason=reason, log=log)
		else:
			is_ok = self.add_item(item_list[0], reason=reason, log=log)
		if not is_ok:
			return False
		return True

	def sub_consumption_item(self, item_tid, amount, reason=0, log=None):
		if not self.has_enough_consumption_item(item_tid, amount):
			return False
		need_send = log is None
		bag = self.bag_2
		is_ok, log = bag.remove_and_destroy_amount(item_tid, amount=amount, log=log)
		if need_send:
			self.send_to_self("s_item_log_list", pickled_log_list=x_serialize.dumps(log))
		return True

	def has_enough_consumption_item(self, item_tid, amount):
		if amount <= 0:
			# amount 不允许为0
			return False
		import x_item_consumption_attr
		if item_tid not in x_item_consumption_attr.DATA["table_sheets"]["配置表"]:
			return False
		has_amount = self.bag_2.get_amount(item_tid)
		return has_amount >= amount

	def consume_many_items(self, tid2amount, reason=0, log=None):
		import x_item_consumption_attr
		consumption_set = x_item_consumption_attr.DATA["table_sheets"]["配置表"]
		bag = self.bag_2
		for item_tid, amount in tid2amount.iteritems():
			if amount <= 0 or item_tid not in consumption_set:
				return False
			has_amount = bag.get_amount(item_tid)
			if has_amount < amount:
				return False
		if log is None:
			log = []
			need_send = True
		else:
			need_send = False
		for item_tid, amount in tid2amount.iteritems():
			is_ok, _ = bag.remove_and_destroy_amount(item_tid, amount=amount, log=log)
			if not is_ok:
				raise Exception("consume item failed")
		if need_send:
			self.send_to_self("s_item_log_list", pickled_log_list=x_serialize.dumps(log))
		return True

	def sell_item(self, bag_id, pidx, sidx, amount, log=None):
		item = self.peek_item(bag_id, pidx, sidx)
		if item is None:
			return False
		if log is None:
			log = []
			need_send = True
		else:
			need_send = False
		if amount == 0:
			amount = item.amount
		is_ok, remain, price, log = item.on_sell(self, amount, log)
		if is_ok and need_send:
			self.print_msg("--> sell item OK:", remain, price)
			self.add_coin(x_common_consts.COIN_TYPE_GOLD, price, x_consts.REASON_AREA_PRIZE)
			self.send_to_self("s_item_log_list", pickled_log_list=x_serialize.dumps(log))
		return is_ok

	#-------------------------------------------------------------------------------------
	# 下面开始是 scene player 的逻辑
	#-------------------------------------------------------------------------------------

	################################
	# 相当于 sceneobj.__init__()
	################################
	def __scene_player_init__(self, scn, pid, tid):
		self._init_(scn, pid, tid)

		# 集合式批量协议
		codec_map = {
			1: x_multimsg_codec.CSyncCodec(self.on_delta_sync_data),  # 玩家增量同步
		}

		def send_func(data):
			self.send_to_self("c_mm", data=data)

		self.mm = x_multimsg.CMultiMsg()
		self.mm.register_callback(codec_map, send_func)

		# 最近一个同步包（完整状态）。

		# 增量差异同步器
		# 新玩家加入时，客户端用self.delta_data.data初始化远端玩家。
		# TODO：组队加入的逻辑完成后可以移除。		
		self.delta_data = x_player_delta_sync_data.CData(pid)

	################################
	# 相当于 sceneobj.on_create()
	################################
	def __scene_player_on_create__(self, base):
		# 重置当前战斗数值
		self.reset_cur_status()

	################################
	# 相当于 sceneobj.destroy()
	################################
	def __scene_player_destroy__(self):
		self.delta_data = None
		self.mm = None

		self._destroy_()

	def fill_attr(self, attrs, attr_names):
		for attr_name in attr_names:
			attrs[attr_name] = getattr(self, attr_name)

	# 获取战场属性子集
	def get_fight_base(self):
		# 基础战斗属性
		base = dict(x_fight_attr.DATA["base_default"])
		for k in base:
			base[k] = getattr(self, k)
		# 装备
		equips = [None] * len(self.emblem)
		for equip_item in self.bag_wear.peek_all():
			equips[equip_item.bag_wear_idx] = equip_item
		base["equips"] = equips
		# 外部系统
		extra_attrs = ("role_class", "level", "emblem", "fairy",
			"passive_skills", "xingzuos", "soul_mgr",
			"done_tutorial", "skill_mgr")
		for k in extra_attrs:
			base[k] = getattr(self, k)
		if self.costume:
			base["costume_base"] = self.costume.get_create_attr_remote()
		return base

	#获取需要同步的公共属性
	def get_create_attr(self):
		attrs = super(CObj, self).get_create_attr()
		if getattr(self, "delta_data", None):
			attrs["delta_data"] = self.delta_data.data
		equips = [None] * len(self.emblem)
		for equip_item in self.bag_wear.peek_all():
			equips[equip_item.bag_wear_idx] = equip_item
		attrs["equips"] = equips
		attr_names = ("role_class", "level", "emblem", "fairy", "passive_skills",
					  "xingzuos", "done_tutorial", "skill_mgr")
		self.fill_attr(attrs, attr_names)
		attrs["cur_costume_id"] = self.get_costume_id()
		return attrs

	def get_create_attr_remote_town(self):
		attrs = super(CObj, self).get_create_attr()
		attrs["cur_costume_id"] = self.get_costume_id()
		self.fill_attr(attrs, ("role_class", "level",))
		return attrs

	#获取需要同步自己的属性
	def get_self_attr(self):
		attrs = super(CObj, self).get_self_attr()
		attr_names = ("gold", "red_diamond", "blue_diamond", "cur_exp", "honor",
					  "soulstone", "trainticket", "polish_stone", "recast_sign",
					  "crystal", "cur_stam", "worship", "star_diam",)
		self.fill_attr(attrs, attr_names)
		return attrs

	def reset_cur_status(self):
		# 重置当前战斗数值
		self.cur_hp = self.max_hp
		self.cur_sld = self.max_sld

	# 回调: 进入副本, 游戏开始之后
	# todo: deprecated!
	def on_game_start(self, map_id):
		pass

	# 回调: 游戏结束, 离开副本之前
	# todo: deprecated!
	def on_game_end(self):
		pass

	# 回调: 进入(副本内)区域之后
	def on_enter_area(self):
		pass

	#-------------------------------------------------------------------------------------
	# 下面开始是 client 协议的处理
	#-------------------------------------------------------------------------------------
	def on_mm(self, msg):
		self.send_to_others_msg(msg)

		self.mm.unpack_all(msg.data)

	def on_delta_sync_data(self, data):
		self.delta_data.recv_diff_and_update_self(data)

	#-------------------------------------------------------------------------------------
	# 下面开始是背包相关接口
	#-------------------------------------------------------------------------------------
	def get_bag_by_id(self, bag_id):
		return self.bags.get(bag_id, None)

	def peek_item(self, bag_id, pidx, sidx):
		bag = self.get_bag_by_id(bag_id)
		if bag is None:
			return None

		if pidx < 0 or pidx >= bag.max_page:
			return None
		if sidx < 0 or sidx >= bag.max_slot_per_page:
			return None

		item = bag.peek(pidx, sidx)
		if item is None:
			return None
		if not item.CLASS_TAG.startswith("item_"):
			return None

		return item

	def _sort_item_bag(self, bag_id):
		bag = self.get_bag_by_id(bag_id)
		if bag is None:
			return
		is_sort_performed = bag.sort(cmp_func=self._bag_item_cmp_func)
		if is_sort_performed:
			# 自动显示回第一页
			self._peek_item_page(bag_id, 0)
	
	def _peek_item_page(self, bag_id, pidx, need_send=True):
		bag = self.get_bag_by_id(bag_id)
		if bag is None:
			return None
		return self._peek_item_page_by_bag(bag, pidx, need_send)

	def _create_s_item_info(self, item, is_in_shop=False, need_sync_base=False):
		if is_in_shop:
			player = None
		else:
			player = self
		if item.can_use(player):
			can_use = 1
		else:
			can_use = 0
		if not need_sync_base:
			base = ""
		else:
			base = item.save_to_string()
		return self.room.msg_mgr.s_item_info(\
			tid=item.tid, quality=item.quality, can_use=can_use, pidx=item.pidx,
			sidx=item.sidx, amount=item.amount, bag_id=item.bag_id,
			base=base)

	def _peek_item_page_by_bag(self, bag, pidx, need_send):
		items = bag.peek_page(pidx)
		item_infos = []
		# 装备背包：追加物品base, 方便client计算属性
		need_sync_base = (bag.bag_id == x_common_consts.BAG_ID_WEAR)
		for item in items:
			info = self._create_s_item_info(item, need_sync_base=need_sync_base)
			item_infos.append(info)

		next_scale_info = bag.get_next_scale_info()
		if next_scale_info is None:
			expand_state = x_common_consts.BAG_EXPAND_STATE_UNSUPPORTED
		elif next_scale_info == "END":
			expand_state = x_common_consts.BAG_EXPAND_STATE_END
		else:
			expand_state = x_common_consts.BAG_EXPAND_STATE_NEXT

		msg_object = self.room.msg_mgr.s_item_list(bag_id=bag.bag_id,
			max_page=bag.max_page,
			total_max_slot=bag.get_pos_amount(),
			pidx=pidx,
			cur_page_max_slot=bag.pages[pidx].max,
			expand_state=expand_state,
			items=item_infos)

		if need_send:
			self.send_to_self_msg(msg_object)

		return msg_object

	def on_c_item_page(self, msg):
		self._peek_item_page(msg.bag_id, msg.pidx)

	def on_c_item_sell(self, msg):
		self.print_msg("--> c_item_sell", msg.bag_id, msg.pidx, msg.sidx, msg.count)
		if msg.bag_id == self.bag_wear.bag_id:
			return
		is_ok = self.sell_item(msg.bag_id, msg.pidx, msg.sidx, msg.count)
		if not is_ok:
			self.send_to_self("s_notice", msg_type=x_common_consts.NOTICE_TYPE_ERROR, msg="物品不可以出售")
		self.print_msg("\tsell", is_ok)

	# 通用的道具使用函数
	def on_c_item_use(self, msg):
		#if not self.check_can_do_with_send_text(x_status_data.ACT_ITEM_USE):
		#	return		
		item = self.peek_item(msg.bag_id, msg.pidx, msg.sidx)
		if item is not None:
			if not item.can_use(self):
				self.send_to_self("s_notice", msg_type=x_common_consts.NOTICE_TYPE_ERROR, msg=x_text.FMT[x_text.NUM_LEVEL_LIMIT])
				return
			if msg.amount <= 1:
				is_ok = self.use_item(item, msg.target_pid)
			else:
				is_ok = self.use_many_items(item, msg.target_pid, msg.amount)
		else:
			is_ok = 0
		self.send_to_self("s_item_use", is_ok=1 if is_ok else 0)

	def use_item(self, item, target_pid):
		urv = item.on_use(self, target_pid)
		# 是否需要删除一个道具
		if urv == x_consts.ITEM_URV_OK_AND_DELETE_ONE:
			bag = self.get_bag_by_id(item.bag_id)
			remain_amount, log = bag.remove_amount(item, 1)
			# self.report_sub_item(item.tid, item.quality, 1, why="use")
			self.send_to_self("s_item_log_list", pickled_log_list=x_serialize.dumps(log))
			return True
		elif urv == x_consts.ITEM_URV_OK_AND_ALREADY_DELETE_ONE:
			# self.report_sub_item(item.tid, item.quality, 1, why="use")
			return True
		elif urv == x_consts.ITEM_URV_FAIL:
			return False
		return False

	def use_many_items(self, item, target_pid, amount):
		amount = min(item.amount, amount)
		urv = item.on_use_amount(self, target_pid, amount)
		if urv == x_consts.ITEM_URV_OK_AND_DELETE_ONE:
			bag = self.get_bag_by_id(item.bag_id)
			remain_amount, log = bag.remove_amount(item, amount)
			self.send_to_self("s_item_log_list", pickled_log_list=x_serialize.dumps(log))
			return True
		elif urv == x_consts.ITEM_URV_OK_AND_ALREADY_DELETE_ONE:
			return True
		elif urv == x_consts.ITEM_URV_FAIL:
			return False
		return False

	def try_use_item(self, bag_id, item_tid, target_pid):
		bag = self.get_bag_by_id(bag_id)
		if bag is None:
			return False
		item = bag.find_item_by_tid(item_tid)
		if item is None:
			return False
		return self.use_item(item, target_pid)

	def _bag_item_cmp_func(self, item_a, item_b):
		# 新手礼包是永远在前面的
		a_weight = x_consts.ITEM_SUB_TYPENAME_WEIGHT.get(item_a.sub_type_name)
		b_weight = x_consts.ITEM_SUB_TYPENAME_WEIGHT.get(item_b.sub_type_name)
		if a_weight != b_weight:
			return cmp(b_weight, a_weight)

		# 从根类型开始排
		a_weight = x_consts.ROOT_ITEM_TYPENAME_WEIGHT.get(item_a.root_type_name, 0)
		b_weight = x_consts.ROOT_ITEM_TYPENAME_WEIGHT.get(item_b.root_type_name, 0)
		if a_weight != b_weight:
			return cmp(b_weight, a_weight)

		# 武器 > xx > xx
		#a_weight = x_consts.ITEM_TYPENAME_WEIGHT.get(item_a.type_name, 0)
		#b_weight = x_consts.ITEM_TYPENAME_WEIGHT.get(item_b.type_name, 0)
		#if a_weight != b_weight:
		#	return cmp(b_weight, a_weight)

		# 稀有度排序
		if item_b.quality != item_a.quality:
			return cmp(item_b.quality, item_a.quality)
		# 类型名排序
		#if item_b.type_name != item_a.type_name:
		#	return cmp(item_b.type_name, item_a.type_name)
		# 子类型名排序
		if item_b.sub_type_name != item_a.sub_type_name:
			return cmp(item_b.sub_type_name, item_a.sub_type_name)
		# 卖出价值
		if item_b.sell_value != item_a.sell_value:
			return cmp(item_b.sell_value, item_a.sell_value)
		# 道具名称
		if item_b.show_name != item_a.show_name:
			return cmp(item_b.show_name, item_a.show_name)
		# 最后是道具数量
		return cmp(item_b.amount, item_a.amount)

	def on_c_item_sort(self, msg):
		# 不能整理穿着和宝石背包
		if msg.bag_id in (x_common_consts.BAG_ID_WEAR, x_common_consts.BAG_ID_GEM):
			return
		self._sort_item_bag(msg.bag_id)

	def on_c_item_buy(self, msg):
		item = self.room.create_item(msg.tid)
		if hasattr(item, "buy_value"):
			is_ok = self.consume_coins(dict(item.buy_value))
			if not is_ok:
				self.send_to_self("s_notice", msg_type=x_common_consts.NOTICE_TYPE_ERROR, msg=x_text.NO_ENOUGH_COIN)
			else:
				item.assign_to(self)
			
	# 指定副本是否可进入
	def check_map_available(self, map_id, game_mode):
		map_data = x_map_data.DATA.get(map_id)
		if not map_data:
			return x_text.NUM_GOTO_GAME_UNKNOWN_MAP
		if not map_data["is_open"] and not self.is_gm_mode:
			return x_text.NUM_GOTO_GAME_NOT_AVAILABLE
		# 游戏进度限制
		rec = self.map_records.get(map_id, None)
		if rec is None:
			return x_text.NUM_GOTO_GAME_NOT_AVAILABLE
		# 进入次数限制(目前只有单人精英和多人模式才有)
		if game_mode == x_common_consts.GAMEMODE_PVE_ELITE or game_mode == \
				x_common_consts.GAMEMODE_PVE_MULTI:
			if map_data.get("daily_tickets", 0) > 0 and rec.tickets < 1:
				return x_text.NUM_GOTO_GAME_NO_TICKETS
		# 等级限制
		required_level = map_data["player_level"]
		if required_level > 0 and self.level < required_level:
			return x_text.NUM_GOTO_GAME_LEVEL_LIMITED
		# 时段限制
		open_time = map_data["open_time"]
		if open_time:
			beg, end = map_data["open_time"]
			# self.print_msg("map_id=%d"%map_id, open_time)
			now = datetime.datetime.now()
			t = now.hour * 1000 + now.minute
			if t < beg or t > end:
				return x_text.NUM_GOTO_GAME_TIME_LIMITED
		#体力限制
		stam_cost = map_data["stamina"]
		if game_mode == x_common_consts.GAMEMODE_PVE_ELITE: 
			stam_cost *= x_common_consts.STAM_ELITE_COEFFICIENT
		if self.cur_stam < stam_cost:
			return x_text.NUM_GOTO_GAME_NO_STAM

		return x_common_consts.GOTO_GAME_OK

	# 开启指定副本
	def open_maps(self, map_list, sync=True):
		logs = []
		for map_id in map_list:
			if map_id not in self.map_records:
				rec = x_map_record.CMapRecord()
				rec.on_create()
				rec.tickets = x_map_data.DATA[map_id].get("daily_tickets", 0)
				self.map_records[map_id] = rec
				logs.append(map_id)
		if sync and logs:
			self.send_to_self("s_open_maps", new_maps=logs)
		return logs

	# 返回副本 (每日可进入次数, 剩余进入次数, 剩余可购买的次数)
	def get_map_tickets(self, map_id):
		rec = self.map_records.get(map_id, None)
		if not rec:  # 副本尚未开启
			return 0, 0, 0
		map_data = x_map_data.DATA.get(map_id)
		can_buy = x_common_consts.DAILY_MAP_TICKETS_BUY_LIMIT - rec.buy_tickets
		return map_data.get("daily_tickets", 0), rec.tickets, can_buy

	# 消耗副本入场券
	def consume_map_tickets(self, map_id, game_mode=None):
		rec = self.map_records.get(map_id, None)
		if not rec:
			return False
		game_mode = game_mode or self.room.game_mode
		if game_mode == x_common_consts.GAMEMODE_PVE_ELITE \
				or game_mode == x_common_consts.GAMEMODE_PVE_MULTI:
			rec.tickets = max(0, rec.tickets - 1)
			sync_data = x_serialize.dumps({"tickets": rec.tickets})
			self.send_to_self("s_sync_map_rec", map_id=map_id, attrs=sync_data)
		return True

	# 购买副本入场券
	def buy_map_tickets(self, map_id, ticket_count):
		rec = self.map_records.get(map_id, None)
		if not rec:
			# ERROR!
			return False
		map_data = x_map_data.DATA.get(map_id)
		if not map_data.get("daily_tickets", 0):
			# No limits
			return False
		actual_buy = min(ticket_count, x_common_consts.DAILY_MAP_TICKETS_BUY_LIMIT - rec.buy_tickets)
		if actual_buy <= 0:
			return False
		# TODO: buy tickets

		# Buy OK
		rec.buy_tickets += actual_buy
		rec.tickets += actual_buy
		return True

	# 完成指定副本
	def on_map_clear(self, map_id, game_mode, evaluate, map_data):
		rec = self.map_records.get(map_id, None)
		if not rec:
			# ERROR!
			return
		# 更新评价
		sync_attr = {}
		evaluate = int(evaluate)
		star = 0
		if evaluate > rec.evaluate:
			area_id = map_data["area_id"]
			if area_id:
				star = evaluate - rec.evaluate
				self.add_area_star(area_id, star)
			rec.evaluate = evaluate
			sync_attr["evaluate"] = evaluate
		if game_mode == x_common_consts.GAMEMODE_PVE_ELITE:
			rec.clear_elite = 1
			sync_attr["clear_elite"] = 1
		if sync_attr:
			sync_attr = x_serialize.dumps(sync_attr)
			self.send_to_self("s_sync_map_rec", map_id=map_id, attrs=sync_attr, area_star=star)

		# 开放新的关卡
		next_map = map_data["next_map"]
		if next_map and next_map not in self.map_records:
			self.open_maps((next_map,))

		# 解锁新的兽魂
		tid_list = []
		unlock_soul = map_data["unlock_soul"]
		for soul_id in unlock_soul:
			has_soul = self.soul_mgr.atlas_list.get(soul_id, None)
			if not has_soul:
				import x_monster_soul
				soul_base = {"tid": soul_id, "level": 1, "rank": 0, "exp": 0, "soul_stone": 0, "colosseum_level": x_misc_consts.COLOSSEUM_MIN_LEVEL}
				soul = x_monster_soul.CObj()
				soul.on_create(soul_base)
				self.soul_mgr.atlas_list[soul_id] = soul
				tid_list.append(soul_id)
		if len(tid_list) > 0:
			self.send_to_self("s_soul_unlock", tid_list=x_serialize.dumps(tid_list))

	# 增加区域评价
	def add_area_star(self, area_id, star):
		area_rec = self.area_records.get(area_id, None)
		if not area_rec:
			area_rec = x_area_record.CObj()
			area_rec.on_create()
			self.area_records[area_id] = area_rec
		area_rec.star += star
		for i in xrange(1, 4):
			if area_rec.star < i * 10:
				break
			elif getattr(area_rec, "prize%d" % i) == x_common_consts.AREA_PRIZE_NONE:
				setattr(area_rec, "prize%d" % i, x_common_consts.AREA_PRIZE_AVAILABLE)

	# 获取区域奖励
	def get_area_prize(self, area_id, prize_idx):
		area_rec = self.area_records.get(area_id, None)
		if not area_rec:
			return None
		attr_name = "prize%d" % prize_idx
		is_prize = getattr(area_rec, attr_name, True)
		if is_prize != x_common_consts.AREA_PRIZE_AVAILABLE:
			return None
		data = x_area_data.DATA.get(area_id, None)
		if not data:
			return None
		attr_name = "box%d_drop_id" % prize_idx
		prize_id = data.get(attr_name, None)
		if not prize_id:
			return None
		# 发放奖励
		setattr(area_rec, "prize%d" % prize_idx,  x_common_consts.AREA_PRIZE_FETCHED)
		prize_data = x_prize_data.DATA.get(prize_id, None)
		if not prize_data:
			return None
		reward_attrs, reward_items = self.apply_reward(
			prize_id, prize_data, x_consts.REASON_AREA_PRIZE)
		return reward_attrs, reward_items

	# DEBUG: 打印副本记录
	def debug_print_map_records(self):
		splitter = "|--------------------------------"
		self.print_msg(splitter)
		self.print_msg("| Player(UID=%d) map records"%self.uid)
		for map_id, rec in self.map_records.iteritems():
			self.print_msg("| [%d]" % map_id, str(rec))
		self.print_msg(splitter)

	def get_scene_obj_tid(self):
		import x_role_class_data
		return x_role_class_data.DATA[self.role_class]["obj_tid"]

	def apply_reward(self, prize_id, prize_data=None, reason=0, factor_id=0):
		# self.print_msg("|------------------------------")
		if prize_data is None:
			prize_data = x_prize_data.DATA.get(prize_id, None)
			if prize_data is None:
				return "", ""
		drop_cnt = 1  # 奖励应用的次数
		coin_mul = None  # 属性奖励倍数
		tree_mul = None  # 掉落树概率倍数
		if factor_id:
			factor_data = x_prize_mul_data.DATA.get(factor_id, None)
			prize_id_range = factor_data["prize_id_range"]
			if prize_id_range:
				is_factor = False
				for beg, end in prize_id_range:
					if prize_id >= beg and prize_id <= end:
						is_factor = True
						break
			else:
				is_factor = True
			if is_factor:
				drop_cnt = min(x_consts.PRIZE_DROP_COUNT_MAX, factor_data["count"])
				coin_mul = factor_data["coin_mul"]
				tree_mul = factor_data["tree_mul"]
				# self.print_msg("facotr: x%d" % drop_cnt, coin_mul, tree_mul)
		reward_attrs = []
		reward_items = {}
		attr_log = {}
		# 货币产出
		exp = prize_data["exp"]
		if exp > 0:
			if coin_mul:
				exp *= min(x_consts.PRIZE_COIN_MUL_MAX, coin_mul.get("exp", 1))
			exp *= drop_cnt
			self.add_exp(exp, reason, log=attr_log)
			reward_attrs.append(struct.pack("<BI",
				x_common_consts.REWARD_NAME2ID["exp"], exp))
		coin = prize_data["coin"]
		if coin:
			for k, v in coin:
				if coin_mul:
					v *= min(x_consts.PRIZE_COIN_MUL_MAX, coin_mul.get(k, 1))
				v *= drop_cnt
				self.add_coin(k, v, reason, log=attr_log)
				reward_attrs.append(struct.pack("<BI",
					x_common_consts.REWARD_NAME2ID[k], v))
		if reward_attrs:
			self.send_to_self("s_sync_attr", pickled_log_list=x_serialize.dumps(attr_log))
		# 普通道具产出
		prize = prize_data["prize"]
		if prize:
			for tree_id in prize:
				self._apply_item_tree(reward_items, tree_id, drop_cnt, tree_mul)
		# 关键道具产出
		tree_id = prize_data["treasure"]
		if tree_id:
			self._apply_treasure_tree(reward_items, prize_id, tree_id, drop_cnt, tree_mul)
		if reward_items:
			item_list = x_item_creator.create_many_items(0, reward_items)
			if not self.add_many_items(item_list, reason):
				self.room.send_mail(self.rid, x_text.MAIL_REWARD_SUBJECT, x_text.MAIL_REWARD_CONTENT,
					item_list=item_list)
		# 生成摘要信息
		s1 = "".join(reward_attrs)
		s2 = "".join(struct.pack("<IH", item_tid, amount) for item_tid, amount in reward_items.iteritems())
		return s1, s2

	def _apply_item_tree(self, reward_items, tree_id, drop_cnt=1, tree_mul=None):
		tree = x_item_tree_data.NORMAL.get(tree_id, None)
		if tree is None:
			return
		# 固定掉落树
		if tree["fixed"]:
			for node in tree["nodes"]:
				item_type = node[x_consts.TREE_NODE_IDX_TYPE]
				if item_type == x_consts.TREE_NODE_TYPE_TREE:
					for i in xrange(drop_cnt):
						tid, amount = self._walk_item_tree(node[x_consts.TREE_NODE_IDX_TID])
						if tid and amount:
							reward_items[tid] = reward_items.get(tid, 0) + amount
				elif item_type == x_consts.TREE_NODE_TYPE_EQUIP:
					tid = node[x_consts.TREE_NODE_IDX_TID]
					amount = node[x_consts.TREE_NODE_IDX_AMOUNT]
					if tid and amount:
						reward_items[tid] = reward_items.get(tid, 0) + amount * drop_cnt
			return
		# 随机掉落树
		if tree_mul:
			# 计算倍率奖励
			total_weight = tree["weight"]
			tree_weights = {}
			for node in tree["nodes"]:
				item_type = node[x_consts.TREE_NODE_IDX_TYPE]
				if item_type == x_consts.TREE_NODE_TYPE_TREE and node[
					x_consts.TREE_NODE_IDX_TID] in tree_mul:
					k = node[x_consts.TREE_NODE_IDX_TID]
					v = min(x_consts.PRIZE_TREE_MUL_MAX, tree_mul.get(k, 1))
					w = node[x_consts.TREE_NODE_IDX_WEIGHT]
					tree_weights[k] = w * v
					total_weight += w * (v - 1)
			tree_mul = (total_weight, tree_weights)
		for c in xrange(drop_cnt):
			tid, amount = self._walk_item_tree(tree_id, tree_mul)
			if tid and amount:
				reward_items[tid] = reward_items.get(tid, 0) + amount

	def _apply_treasure_tree(self, reward_items, prize_id, tree_id, drop_cnt=1,
			tree_mul=None):
		tree = x_item_tree_data.TREASURE.get(tree_id, None)
		if tree is None:
			return
		all_nodes = tree["nodes"]
		max_reward = 3
		p = [None] * max_reward
		for i, node in enumerate(all_nodes):
			if i >= max_reward:
				break
			v = 1
			if tree_mul:
				item_type = node[x_consts.TREE_NODE_IDX_TYPE]
				if item_type == x_consts.TREE_NODE_TYPE_TREE:
					v = tree_mul.get(node[x_consts.TREE_NODE_IDX_TID], 1)
			w = node[x_consts.TREE_NODE_IDX_WEIGHT]
			if w > 0 and v > 0:
				p[i] = (w, v)
		for c in xrange(drop_cnt):
			result = self.treasure_probability(prize_id, p[0], p[1], p[2])
			for i, is_ok in enumerate(result):
				if not is_ok:
					continue
				node = all_nodes[i]
				item_type = node[x_consts.TREE_NODE_IDX_TYPE]
				if item_type == x_consts.TREE_NODE_TYPE_EQUIP:
					tid, amount = node[x_consts.TREE_NODE_IDX_TID], node[
						x_consts.TREE_NODE_IDX_AMOUNT]
				elif item_type == x_consts.TREE_NODE_TYPE_TREE:
					tid, amount = self._walk_item_tree(
						node[x_consts.TREE_NODE_IDX_TID])
				else:
					tid = amount = 0
				# self.print_msg("!!!!TREASURE!!!!", tid, amount)
				if tid and amount:
					reward_items[tid] = reward_items.get(tid, 0) + amount

	def _walk_item_tree(self, tree_id, adjust_weights=None):
		tree = x_item_tree_data.NORMAL.get(tree_id, None)
		if tree is None:
			return 0, 0
		if adjust_weights:
			total_weight, tree_weights = adjust_weights
		else:
			total_weight, tree_weights = tree["weight"], None
		cur_weight = random.randint(1, total_weight)
		for node in tree["nodes"]:
			w = node[x_consts.TREE_NODE_IDX_WEIGHT]
			if tree_weights and node[
				x_consts.TREE_NODE_IDX_TYPE] == x_consts.TREE_NODE_TYPE_TREE:
				w = tree_weights.get(node[x_consts.TREE_NODE_IDX_TID], w)
			if cur_weight > w:
				cur_weight -= w
				continue
			item_type = node[x_consts.TREE_NODE_IDX_TYPE]
			if item_type == x_consts.TREE_NODE_TYPE_TREE:
				return self._walk_item_tree(node[x_consts.TREE_NODE_IDX_TID])
			elif item_type == x_consts.TREE_NODE_TYPE_EQUIP:
				tid = node[x_consts.TREE_NODE_IDX_TID]
				amount = node[x_consts.TREE_NODE_IDX_AMOUNT]
				return tid, amount
			else:
				break
		return 0, 0

	def get_costume_id(self):
		return self.costume.cur_part

	def has_empty_equip_slot(self):
		return self.bag_wear.get_free_pos_amount() != 0

	def set_tutorial_done(self, tid):
		if tid > 0:
			self.done_tutorial[tid] = True

	def _get_is_playing(self):
		return self.single_game_ctx is not None
	is_playing = property(_get_is_playing)

	# 城镇人物心跳
	def town_update(self):
		# self.print_msg("--> player(uid=%d).town_update" % self.uid)
		# 刷新时间相关的数据
		now_time = int(self.room.now())
		now_date = datetime.datetime.fromtimestamp(now_time)
		# 每日刷新
		last_date = datetime.datetime.fromtimestamp(self.recover_time)
		dt = now_date - last_date
		is_same_date = last_date.date() == now_date.date()
		next_day = dt.days > 0 or (not is_same_date and now_date.hour >= x_consts.DAILY_RECOVERY_TIME) or (
			is_same_date and last_date.hour < x_consts.DAILY_RECOVERY_TIME <= now_date.hour)
		# self.print_msg("\t", now_date, last_date, next_day, dt.days)
		if next_day:
			self.do_daily_work()
			self.recover_time = self.cookie.last_stam_recovery_time = now_time
			# self.print_msg("\tdo daily work")
		else:
			# 刷新体力
			ds = now_time - self.cookie.last_stam_recovery_time			
			
			if ds > x_common_consts.STAM_RECOVERY_CD:
				self.cookie.last_stam_recovery_time = now_time
				if self.cur_stam < self.max_stam:
					add_stam = min(self.max_stam - self.cur_stam, ds / x_common_consts.STAM_RECOVERY_CD)
					self.add_coin(x_common_consts.COIN_TYPE_CUR_STAM, add_stam, x_consts.REASON_TIME_RECOVERY)
				# self.print_msg("\trecover stam", self.cur_stam)

		
		# 查询竞技场奖励
		last_date = datetime.datetime.fromtimestamp(self.cookie.last_arena_check_time)
		is_same_date = last_date.date() == now_date.date()
		if not is_same_date or last_date.hour / x_consts.ARENA_BALANCE_HOUR != now_date.hour / x_consts.ARENA_BALANCE_HOUR:
			# self.print_msg("\tcheck arena")
			self.cookie.last_arena_check_time = now_time
			self.room.send_to_static_room("rc_arena_check_prize", uid=self.uid, rid=self.rid)

		# 更新玩家战斗力数据
		if self.room:
			#self.room.print_msg("_ranking_battle_pow:%d battle_pow:%d" % (self._ranking_battle_pow, self.battle_pow))
			if self._ranking_battle_pow < self.battle_pow:
				self.room.refresh_player_ranking_list(self)
				self._ranking_battle_pow = self.battle_pow

		# 刷新时装过期
		if self.costume:
			self.costume.on_timer(self, now_time)
		
		# 刷新宝箱情况
		if self.chest:
			self.chest.check_chest_state(self, now_time)	
			
		# 存盘
		if now_time - self._prev_save_db_time >= x_consts.AUTO_SAVE_PERIOD_PLAYER:
			self.save_db_props()
			
	#为兼容战斗力计算做，慎用
	def get_bag_item(self, bag_id, pidx, sidx):
		if bag_id == x_common_consts.BAG_ID_WEAR:
			bag = self.bag_wear
			if bag is None: return None
			page = bag.pages[pidx]
			if page.items and len(page.items) > sidx:
				return bag.peek(pidx, sidx)
			else:
				return None
		else:
			return None

	#为兼容战斗力计算做，慎用
	def get_gongming_lvl(self):
		if self.emblem is None:
			return 0
		unbound_func = self.emblem[0].__class__.get_min_gem_level
		gongming_lvl = min(map(unbound_func, self.emblem))
		return gongming_lvl

	def buy_res(self, buy_type):
		if not buy_type or buy_type >= len(x_common_consts.BUY_RES_INFO):
			return x_text.NUM_BUY_RES_FORBID, None
		res_name, res_buy, res_ch_name = x_common_consts.BUY_RES_INFO[buy_type]
		is_resource = False
		item_tid = 0
		on_buy = None
		if res_name:
			if isinstance(res_name, str):
				is_resource = True
				if not hasattr(self, res_name):
					return x_text.NUM_BUY_RES_FORBID, None
			elif isinstance(res_name, int):
				item_tid = res_name
				if not x_item_creator.is_item(item_tid):
					return x_text.NUM_BUY_RES_FORBID, None
		else:
			on_buy = getattr(self, "on_buy_" + res_buy, None)
			if not callable(on_buy):
				return x_text.NUM_BUY_RES_FORBID, None
		daily_mgr = self.daily_mgr
		vip_data = x_vip_data.DATA[self.vip]
		cur_buy_times = getattr(daily_mgr, res_buy, 0)
		remain_time = max(0, vip_data[res_buy] - cur_buy_times)
		if not remain_time:
			return x_text.NUM_BUY_RES_DAILY_LIMIT, None
		buy_cost = getattr(daily_mgr, res_buy + "_cost", 0)
		if not buy_cost:
			return x_text.NUM_BUY_RES_FORBID, None
		buy_amount = getattr(daily_mgr, res_buy + "_amount", 1)
		log_attr = {}
		if not self.sub_diamond(buy_cost, reason=x_consts.REASON_BUY_RES, log=log_attr):
			return x_text.NUM_BUY_RES_NO_DIAMOND, None
		cur_buy_times += 1
		setattr(daily_mgr, res_buy, cur_buy_times)
		cri_rate = 0
		# 自定义on_buy处理需要自己回应客户端, 除此之外会自动发送s_buy_res
		if is_resource:
			if buy_type == x_common_consts.BUY_RES_GOLD:
				cri_rate = random.choice(x_misc_consts.BUY_GOLD_CRIT_RATE)
				buy_amount *= cri_rate
			self.add_coin(res_name, buy_amount, reason=x_consts.REASON_BUY_RES, log=log_attr)
		elif item_tid:
			item = x_item_creator.create_item(0, item_tid, buy_amount)
			if not self.add_item(item, reason=x_consts.REASON_BUY_RES):
				self.room.send_mail(self.rid, x_text.MAIL_BUY_ITEM_SUBJECT, x_text.MAIL_BUY_ITEM_CONTENT, item_list=[item])
		else:
			on_buy(buy_amount)
		self.send_to_self("s_sync_attr", pickled_log_list=x_serialize.dumps(log_attr))
		return 0, (buy_amount, cri_rate, on_buy is None)

	def on_buy_colosseum_reset(self, buy_amount=0):
		down_list = {}
		for attr in self.soul_mgr.colosseum_list:
			if attr["type"] == x_common_consts.COLOSSEUM_TYPE_SOUL:
				soul_tid = attr["tid"]
				soul = self.soul_mgr.atlas_list[soul_tid]
				soul.colosseum_level = max(x_misc_consts.COLOSSEUM_MIN_LEVEL,
					soul.colosseum_level - x_misc_consts.COLOSSEUM_FETCH_SUB_LEVEL)
				down_list[soul.tid] = soul.colosseum_level
		down_list = x_serialize.dumps(down_list)
		self.send_to_self("s_soul_level_down", down_list=down_list)
