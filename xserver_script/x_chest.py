# $Id$
# -*- coding: gbk -*-
import x_common_consts
import x_coreobj
import x_map_data
import x_misc_consts
import time
import x_chest_config_all
import x_prize_data
import x_chest_config
import x_consts

class CObj(x_coreobj.CObj):
	
	CLASS_TAG = "chest"
	
	PATCH_MODULE_NAME = "x_chest_sys_attr"	
		
	def on_create(self, base=None):		
		self.room = None
		self.player = None		
		super(CObj, self).on_create(base=base)	
	
	# 只作为调试用
	def check_chest_state(self, player, now_time): 
		if not self.room or not self.player:
			return
		self.now_time = int(self.room.now())		
		if self.can_open_silver_free():
			pass #self.player.send_to_self("s_chest_free", chest_id=0)
		if self.can_open_gold_free():
			pass #self.player.send_to_self("s_chest_free", chest_id=1)
	
	def init_data(self, player):		
		self.player = player
		self.room = self.player.room		
		self.room.print_msg('设置room')
			
	def open_chest_ctr(self, chest_id):
		
		if not self.open_silver_free():
			self.open_diamond_by_reddiamond()
			
		"""
		if 1 == chest_id: # bronze
			pass
		elif 2 == chest_id: # sliver
			if not self.open_silver_free():
				self.open_diamond_by_reddiamond()
				
		elif 3 == chest_id: # gold
			pass
		elif 4 == chest_id: # diamond
			pass
		"""	
	def silver_remain_free(self):		
		return self.silver_remain
	
	def gold_remain_free(self):
		return self.gold_next
	
	def can_open_silver_free(self):
		if not self.room or not self.player:
			return False
		self.now_time = int(self.room.now())
		cd_time = x_chest_config_all.DATA["白银"]["免费CD"]		
		self.player.room.print_msg("grsn1304:can_open_silver_free:now_time = " + str(self.now_time))
		self.player.room.print_msg("grsn1304:can_open_silver_free:silver_remain = " + str(self.silver_remain))	
		if (self.now_time - self.silver_last) >= cd_time and self.silver_remain > 0:
			return True
		
		return False
			
	#免费的方式 打开银宝箱
	def open_silver_free(self):
		if not self.can_open_silver_free():
			return False
		
		self.player.room.print_msg("grsn1304:已经免费打开银宝箱")
		self.silver_remain -= 1
		self.silver_last = self.now_time
		self.is_dirty = True
		return True
	
	#一颗红钻打开钻石宝箱
	def open_diamond_by_reddiamond(self):
		diamond_cnt = x_chest_config_all.DATA["钻石"]["单次红钻"]
		self.player.room.print_msg("grsn1304:一颗红钻打开银宝箱")
		
		
		if self.player.level < 10:
			self.room.print_msg('self.player.level < 10')
			return
		
		prize_id = x_chest_config.DATA[(self.player.level / 10) * 10]['''白银'''] #10~19, 20~29
		self.room.print_msg('prize_id = ' + str(prize_id))
		prize_data = x_prize_data.DATA.get(prize_id, None) if prize_id else None
		if prize_data:
			self.room.print_msg('准备调用 apply_reward()')
			
			
			############################# 记得添加 reson ##############################################
			reward_attrs, reward_items = self.player.apply_reward(prize_id, prize_data, x_consts.REASON_MAP_CLEAR)
			
			self.room.print_msg('reward_attrs = ' + reward_attrs)
			self.room.print_msg('reward_items = ' + reward_items)
		else:
			self.room.print_msg('prize_data is none')
			
			
		return self.player.sub_coin("red_diamond", diamond_cnt)
	
	#十颗红钻打开钻石宝箱
	def open_diamond_by_reddiamond_ten(self):
		diamond_cnt = x_chest_config_all.DATA["钻石"]["十次红钻"]
		
		#self.player.apply_reward(self.prize_id, reason=x_consts.REASON_ITEM_PACKAGE)
		if self.player.level < 10:
			self.room.print_msg('self.player.level < 10')
			return
		
		prize_id = x_chest_config.DATA[(self.player.level / 10) * 10]['''白银'''] #10~19, 20~29
		prize_data = x_prize_data.DATA.get(prize_id, None) if prize_id else None
		if prize_data:
			self.room.print_msg('准备调用 apply_reward()')
			reward_attrs, reward_items = self.player.apply_reward(prize_id, prize_data, x_consts.REASON_MAP_CLEAR)
		else:
			self.room.print_msg('prize_data is none')
		
		return self.player.sub_coin("red_diamond", diamond_cnt)
	
	def open_gold_jipin(self):
		pass
	
	def can_open_gold_free(self):
		if not self.room or not self.player:
			return False
		
		self.now_time = int(self.room.now())		
		cd_time = x_chest_config_all.DATA["黄金"]["免费CD"]
		
		if (self.now_time - self.gold_last) >= cd_time:
			return True
		
		return False
	
	#免费的方式 打开黄金宝箱
	def open_gold_free(self):
		if not self.can_open_gold_free():
			return False
		
		self.gold_last = self.now_time
		self.gold_next -= 1
		self.is_dirty = True
		
		if self.gold_next == 0:
			self.open_gold_jipin()
			
		return True

	def init_silver(self):
		self.silver_remain = x_chest_config_all.DATA["白银"]["日免费次数"]
		
	def on_daily_work(self):
		self.init_silver()
	
	
	# 青铜钥匙日常副本产出
	def open_bronze(self):
		pass	
	