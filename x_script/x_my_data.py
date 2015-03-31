# $Id: x_my_data.py 174751 2015-03-13 07:44:55Z ycwang@NETEASE.COM $
#-*- coding:gbk -*-
import time
import weakref
import x_glb
import x_coreobj
import x_item_bag
import x_item_page
import x_item_creator
import x_item_equip
import x_item_rune
import x_item_gem
import x_item_consumption
import x_item_general_weapon
import x_item_package
import x_item_res
import x_item_costume
import x_fairy
import x_emblem
import x_passive_skill
import x_xingzuo
import x_relation
import x_area_record
import x_map_record
import x_map_data
import x_task_mgr
import x_costume_mgr
import x_player_skill_mgr
import x_monster_soul_mgr
import x_monster_soul
import x_daily_data
import x_common_consts
import x_consts
import x_signal
import x_signal_data
import x_fight_attr
import x_common_util
import x_sysopen_attr
import x_gem_mgr
import x_new_flag_mgr
import x_new_flag_define
import x_chest


class CObj(x_coreobj.CObj):

	CLASS_TAG = "my_data"

	PATCH_MODULE_NAME = "x_player_attr"

	def __init__(self, uid):
		super(CObj, self).__init__()
		self.uid = uid
		self.rtt = 0
		self.relation = None
		self.bags = {}
		# 上次在城镇的位置
		self.town_pos_face = None
		# 数据缓存
		self.battle_pow = 0
		self.cache_ranking_list = {}
		self.better_equips = [None] * x_common_consts.BAG_WEAR_MAX_ITEM_COUNT

		# 注册触发器接口
		self.signal_emitter = x_signal.CEmitter2()
		self.append_listener = self.signal_emitter.append
		self.remove_listener = self.signal_emitter.remove
		self.emit_signal = self.signal_emitter.emit

	def rebuild_all_attr(self, force=False):
		super(CObj, self).rebuild_all_attr(force=force)
		self.battle_pow = x_common_util.get_battle_power(self, x_sysopen_attr.CHARA)
		self.emit_signal(x_signal_data.SG_POWER_CHANGED, self.battle_pow)
		
	def on_create(self, base=None):
		self.gem_mgr = x_gem_mgr.CMgr(weakref.proxy(self))		
		super(CObj, self).on_create(base)
		for bag in (self.bag_1, self.bag_2, self.bag_3, self.bag_wear, self.bag_gem):
			bag.set_player(self)
			self.bags[bag.bag_id] = bag
		self.init_consumption_items()
		self.task_mgr.set_owner(weakref.proxy(self))
		self.skill_mgr.set_owner(weakref.proxy(self))
		self.init_new_flag_mgr()

	def init_new_flag_mgr(self):
		# 排行榜
		self.append_listener(x_signal_data.SG_RANKING_LIST_UPDATE, self.new_flag_mgr.on_rank_tabs_update)
		# 监听依赖的资源
		used = []
		for res_names in x_new_flag_define.RES_DEPEND.itervalues():
			for res_name in res_names:
				if res_name in used: continue
				res_idx = self.en_2_num(res_name)
				self.append_listener(x_signal_data.sg_player_attr_changed(res_idx), self.new_flag_mgr.on_res_update, res_name)
				used.append(res_name)
		# 监听背包
		self.append_listener(x_signal_data.SG_BAG_ITEM_CHANGED, self.new_flag_mgr.on_bag_update)
		self.append_listener(x_signal_data.SG_OBTAIN_OBJECT, self.new_flag_mgr.on_obtain_object)
		self.append_listener(x_signal_data.SG_SKILL_LIST, self.new_flag_mgr.on_skill_list)
		self.append_listener(x_signal_data.SG_SKILL_UPDATE, self.new_flag_mgr.on_skill_update)
			
	def _get_rid(self):
		return self._id
	rid = property(_get_rid)

	def _get_diamond(self):
		return self.blue_diamond + self.red_diamond
	diamond = property(_get_diamond)

	def get_bag_by_id(self, bag_id):
		return self.bags.get(bag_id, None)

	# 在restore前被调用, 用于记录restore后需要还原的数据
	def before_restore(self):
		return self.rtt, self.town_pos_face

	# 在restore后被调用
	def after_restore(self, pre_data):
		self.rtt, self.town_pos_face = pre_data

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
		extra_attrs = ("role_class", "emblem", "fairy", "passive_skills", "xingzuos", "done_tutorial")
		for k in extra_attrs:
			base[k] = getattr(self, k)
		return base

	# 获取城镇属性子集
	def get_town_base(self):
		# todo: 不需要这么多属性
		return self.get_fight_base()

	# 根据日志, 更新背包数据, 日志格式如下
	#
	# 所有可能对背包内容产生影响的接口的返回值中的最后一项
	# 都一定是一个log列表，
	# log列表的条目格式为
	# {
	#   ### 固定key如下 ###
	#	"tid": tid,
	#	"bag_id", bag_id,
	#	"pidx": pidx,
	#	"sidx": sidx,
	#	"amount": amount,
	#   "can_use": can_use,
	#
	#   ### 同时只会出现一个的key如下三个  ###
	#   "delete": True,  # 表示这个物品已经删除
	#     或
	#   "new": True,  # 表示这个物品已经添加
	#     或
	#   "stack": value, #叠加的delta量（可能是负数）,
	# 	  或
	#	"base": value, # 更新物品的基础属性
	#  }
	#
	def bag_update(self, logs):
		obtain_items = []
		modified_tids = set()
		modified_grids = set()
		modified_wears = set()
		swap_stack = []
		has_better_equips = False
		for log_entry in logs:
			bag_id, pidx, sidx = log_entry["bag_id"], log_entry["pidx"], log_entry["sidx"]
			bag = self.bags[bag_id]
			tid = 0
			is_new = False
			if "new" in log_entry:
				bag.assert_pos_free(pidx, sidx)
				if "swap" in log_entry:
					# print "--> bag.swap", log_entry
					item = swap_stack[-1]
					del swap_stack[-1]
				else:
					# print "--> bag.new", log_entry
					item = x_item_creator.create_item(0, log_entry["tid"], log_entry["amount"])
					is_new = True
				bag.do_insert(item, pidx, sidx)
				tid = log_entry["tid"]
			elif "delete" in log_entry:
				# print "--> bag.delete", log_entry
				item = bag.peek(pidx, sidx)
				tid = item.tid
				bag.assert_pos_not_free(pidx, sidx)
				bag.do_remove(pidx, sidx)
				if "swap" in log_entry:
					# swap operation
					swap_stack.append(item)
			elif "stack" in log_entry:
				# print "--> bag.stack", log_entry
				bag.assert_pos_not_free(pidx, sidx)
				item = bag.peek(pidx, sidx)
				tid = item.tid
				diff_amount = log_entry["stack"]
				if diff_amount > 0:
					if item.get_can_stack_amount() < diff_amount:
						raise Exception("stack item failed")
					item.add_amount(diff_amount)
					is_new = True
				else:
					item.sub_amount(abs(diff_amount))
			elif "base" in log_entry:
				# print "--> bag.base", log_entry
				bag.assert_pos_not_free(pidx, sidx)
				item = bag.peek(pidx, sidx)
				base = item.get_base_from_string(log_entry["base"])
				item.on_create(base)
				# notice: on_create之后代码属性会被重置, 要重新attach
				item.attach(bag.owner_uid, bag_id, pidx, sidx)
			else:
				raise Exception("Unknown bag operation: log = %s" % str(log_entry))
			if __debug__:
				if pidx >= 16 or bag_id >= 16:
					err = "bag id = %d, page id = %d, they should be <= 16" % (bag_id, pidx)
					raise OverflowError(err)
			grid_id = (sidx << 8) | (pidx << 4) | bag_id
			modified_grids.add(grid_id)
			if tid != 0 and bag_id == self.bag_2.bag_id:
				modified_tids.add(tid)
			if bag_id == x_common_consts.BAG_ID_WEAR:
				modified_wears.add(grid_id)
			if is_new:
				obtain_items.append(item)
				if item.is_equip() and self.is_better_equip(item, self.better_equips[item.bag_wear_idx]):
					self.better_equips[item.bag_wear_idx] = item
					has_better_equips = True

		if modified_wears:
			self.rebuild_all_attr(True)

		for grid_id in modified_grids:
			bag_id = grid_id & 0xF
			pidx = (grid_id >> 4) & 0xF
			sidx = grid_id >> 8
			self.emit_signal(x_signal_data.SG_BAG_ITEM_CHANGED, bag_id, pidx, sidx)

		if obtain_items:
			self.emit_signal(x_signal_data.SG_OBTAIN_OBJECT, obtain_items)

		if has_better_equips:
			self.emit_signal(x_signal_data.SG_OBTAIN_BETTER_EQUIPS)

		if modified_wears:
			wears = []
			for grid_id in modified_wears:
				sidx = grid_id >> 8
				wears.append(sidx)
			self.emit_signal(x_signal_data.SG_WEAR_CHANGED, wears)
		
		# 更新消耗品
		self.update_consumption_items(modified_tids)

	def is_better_equip(self, new_item, other):
		if self.level < x_consts.SHOW_BETTER_EQUIP_LEVEL or self.level < new_item.level:
			return False
		if not other:
			other = self.bag_wear.peek(0, new_item.bag_wear_idx)
			if not other:
				return True
		return other.get_battle_power() < new_item.get_battle_power()

	def reset_better_equips(self):
		ret = []
		for i, item in enumerate(self.better_equips):
			if item:
				ret.append(item)
				self.better_equips[i] = None
		return ret

	@staticmethod
	def swap_id(bag_id, pidx, sidx):
		return bag_id, pidx, sidx
		
	def init_consumption_items(self):
		import x_item_consumption_attr
		table = x_item_consumption_attr.DATA["table_sheets"]["配置表"]
		for tid, config in table.iteritems():
			coin_name = config["属性名"]
			amount = self.bag_2.get_amount(tid)
			setattr(self, coin_name, amount)
	
	def update_consumption_items(self, modified_tids):
		import x_item_client_info
		attr_update_log = {}
		for tid in modified_tids:
			config = x_item_client_info.DATA[tid]
			if config["根类型"] == "消耗品":
				coin_name = config["属性名"]
				amount = self.bag_2.get_amount(tid)
				attr_idx = self.__class__.en_2_num(coin_name)
				attr_update_log[attr_idx] = amount
		if attr_update_log:
			self.attr_update(attr_update_log)
	
	def get_bag_item(self, bag_id, pidx, sidx):
		bag = self.bags.get(bag_id, None)
		if bag is None: return None
		page = bag.pages[pidx]
		if page.items and len(page.items) > sidx:
			return bag.peek(pidx, sidx)
		else:
			return None

	def set_bag_item(self, bag_id, pidx, sidx, item):
		bag = self.bags.get(bag_id, None)
		if bag is None: return None
		page = bag.pages[pidx]
		if page.items and len(page.items) > sidx:
			page.items[sidx] = item

	def bag_item_count(self, bag_id, pidx, tid):
		bag = self.bags.get(bag_id, None)
		if not bag or not bag.pages[pidx]: return 0
		return sum(map(lambda x: x is not None and x.tid == tid and x.amount or 0, bag.pages[pidx].items))

	# 重置背包数据
	def bag_reset_page(self, bag_id, pidx, cur_page_max_slot, items):
		bag = self.bags[bag_id]
		page = x_item_page.CPage()
		page.on_create({
			"bag_id": bag_id,
			"owner_uid": bag.owner_uid,
			"pidx": pidx,
			"max": cur_page_max_slot,
		})
		bag.pages[pidx] = page
		for item_info in items:
			item_obj = x_item_creator.restore_item(item_info.tid, item_info.amount, item_info.base)
			bag.do_insert(item_obj, pidx, item_info.sidx)
		self.emit_signal(x_signal_data.SG_BAG_PAGE_CHANGED, bag_id, pidx)
		if bag_id == x_common_consts.BAG_ID_WEAR:
			self.rebuild_all_attr(True)

	def attr_update(self, logs):
		prev_level = self.level
		for attr_idx, value in logs.iteritems():
			attr_name = self.num_2_en(attr_idx)
			setattr(self, attr_name, value)
			signal_id = x_signal_data.sg_player_attr_changed(attr_idx)
			self.emit_signal(signal_id, value)
		if self.level > prev_level:
			# level up!
			self.rebuild_all_attr()
			#self.emit_signal(x_signal_data.SG_LEVEL_UP, self.level)
			self.new_flag_mgr.on_level_up(prev_level, self.level)
			
	def attr_update_single(self, attr_idx, value):
		attr_name = self.num_2_en(attr_idx)
		setattr(self, attr_name, value)
		signal_id = x_signal_data.sg_player_attr_changed(attr_idx)
		self.emit_signal(signal_id, value)

	def get_gongming_lvl(self):
		return self.gem_mgr.get_gongming_level()

	def has_empty_equip_slot(self):
		return self.bag_wear.get_free_pos_amount() != 0
	
	def get_addon_attrs_to_self(self):
		return x_common_util.get_player_addon_attrs(self)

	def on_ranking_list(self, msg):
		self.cache_ranking_list[msg.ranking_type] = (time.time(), msg)
		signal_id = x_signal_data.SG_RANKING_LIST_UPDATE
		self.emit_signal(signal_id, msg.ranking_type)

	def get_ranking_list(self, ranking_type):
		data = self.cache_ranking_list.get(ranking_type, None)
		if data is None or time.time() - data[0] > x_common_consts.RANKING_CLIENT_CACHE_TIME:
			x_glb.net.send_and_wait("c_ranking_list", ranking_type=ranking_type, start=0, end=0)
		else:
			signal_id = x_signal_data.SG_RANKING_LIST_UPDATE
			self.emit_signal(signal_id, ranking_type)

	def do_daily_work(self):
		if self.daily_mgr: self.daily_mgr.reset()
		
	def get_costume_id(self):
		return list(self.costume.cur_part)

	def on_skill_list(self, msg):
		for skill in msg.skills: self.skill_mgr.on_skill_update(skill)
		self.emit_signal(x_signal_data.SG_SKILL_LIST, msg.skill_type)

	def on_skill_update(self, msg):
		for skill in msg.skills: self.skill_mgr.on_skill_update(skill)
		self.emit_signal(x_signal_data.SG_SKILL_UPDATE, msg.skills, msg.action)

	def update_map_rec(self, map_id, base, area_star=0):
		rec = self.map_records.get(map_id, None)
		if rec is None:
			rec = x_map_record.CMapRecord()
			rec.on_create(base)
			self.map_records[map_id] = rec
		else:
			for k, v in base.iteritems():
				setattr(rec, k, v)
		if area_star > 0:
			area_id = x_map_data.DATA[map_id]["area_id"]
			if area_id:
				self.add_area_star(area_id, area_star)

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
		return area_rec.star

	def add_map_recs(self, map_list):
		for map_id in map_list:
			rec = x_map_record.CMapRecord()
			rec.on_create()
			rec.tickets = x_map_data.DATA[map_id].get("daily_tickets", 0)
			self.map_records[map_id] = rec

	def get_map_tickets(self, map_id):
		rec = self.map_records.get(map_id, None)
		return rec and rec.tickets or 0

	def get_map_data(self):
		map_data = {}
		map_data["clear_elite"] = []
		for map_id, rec in self.map_records.iteritems():
			map_data[map_id] = rec is not None and rec.evaluate or 0
			if rec.clear_elite: map_data["clear_elite"].append(map_id)
		for area_id, area_rec in self.area_records.iteritems():
			map_data["area_%d" % area_id] = (area_rec.star, area_rec.prize1 == x_common_consts.AREA_PRIZE_FETCHED, area_rec.prize2 == x_common_consts.AREA_PRIZE_FETCHED, area_rec.prize3 == x_common_consts.AREA_PRIZE_FETCHED)
		return map_data

	def on_area_box_opened(self, area_id, box_id):
		area_data = self.area_records.get(area_id, None)
		setattr(area_data, "prize%d" % box_id, x_common_consts.AREA_PRIZE_FETCHED)

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
	
	def has_enough_consumption_item(self, item_tid, amount):
		if amount <= 0:
			# amount 不允许为0
			return False
		import x_item_consumption_attr
		if item_tid not in x_item_consumption_attr.DATA["table_sheets"]["配置表"]:
			return False
		has_amount = self.bag_2.get_amount(item_tid)
		return has_amount >= amount