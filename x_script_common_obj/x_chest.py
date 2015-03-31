# $Id: x_task.py 173467 2015-03-02 12:56:33Z guoqing@NETEASE.COM $
# -*- coding: gbk -*-
import x_common_consts
import x_coreobj
import x_map_data
import x_misc_consts
import time
import x_chest_config_all

class CObj(x_coreobj.CObj):
	
	CLASS_TAG = "chest"
	
	PATCH_MODULE_NAME = "x_chest_sys_attr"
	
	#def __init__(self, room, red_diamond, player):
		#super(CObj, self).__init__()
		#self.room = room
		#self.red_diamond = red_diamond
		#self.player = player
		
	def on_create(self, base=None):				
		super(CObj, self).on_create(base=base)		
	
	def silver_remain_free(self):
		return self.silver_remain
	
	def gold_remain_free(self):
		return self.gold_next
	
	def can_open_silver_free(self):
		cd_time = x_chest_config_all.DATA["白银"]["免费CD"]
		
		if (time.time() - self.silver_last) >= cd_time and self.silver_remain > 0:
			return True
		
		return False
			
	def open_silver_free(self):
		if not self.can_open_silver_free():
			return False
		
		self.silver_remain -= 1
		self.silver_last = time.time() # 时间需要商量
		self.is_dirty = True
		self.save_db_props()
		return True
	
	def open_silver_by_reddiamond(self):
		diamond_cnt = x_chest_config_all.DATA["白银"]["单次红钻"]
		return self.player.sub_coin("red_diamond", diamond_cnt)
	
	def open_silver_by_reddiamond_ten(self):
		diamond_cnt = x_chest_config_all.DATA["白银"]["十次红钻"]
		return self.player.sub_coin("red_diamond", diamond_cnt)
	
	def open_gold_jipin(self):
		pass
	
	def can_open_gold_free(self):
		cd_time = x_chest_config_all.DATA["黄金"]["免费CD"]
		
		if (time.time() - self.gold_last) >= cd_time:
			return True
		
		return False
	
	def open_gold_free(self):
		if not self.can_open_gold_free():
			return False
		
		self.gold_last = time.time()
		self.gold_next -= 1
		self.is_dirty = True
		self.save_db_props()
		
		if self.gold_next == 0:
			self.open_gold_jipin()
			
		return True

	def save_db_props(self, callback=None, data=None):
		#if not self.is_new and not self.is_dirty:
			#return
		#if self.is_new:
			#sql = self.__class__.gen_sql_insert_table()
		#elif self.is_dirty:
			#sql = self.__class__.gen_sql_update_table()
		if not self.is_dirty:
			return
		sql = self.__class__.gen_sql_update_table()	
		param = self.save_to_sql_base()
		self.room.sql_execute(sql, param, callback=callback, data=data)
		
		
	
	
	
	
	
	
	def destroy(self):
		self.room.print_msg("destroy")
		self.save_db_props()
		super(CObj, self).destroy()

	def save_db_props(self, callback=None, data=None):
		if not self.is_new and not self.is_dirty:
			return
		if self.is_new:
			sql = self.__class__.gen_sql_insert_table()
		elif self.is_dirty:
			sql = self.__class__.gen_sql_update_table()
		param = self.save_to_sql_base()
		self.room.sql_execute(sql, param, callback=callback, data=data)
		self.is_new = False

	def mark_read(self):
		if self.read_tag == x_consts.MAIL_TAG_FALSE:
			self.read_tag = x_consts.MAIL_TAG_TRUE
			self.is_dirty = True
			self.save_db_props()

	def mark_fetch(self):
		if self.fetch_tag == x_consts.MAIL_TAG_FALSE:
			self.fetch_tag = x_consts.MAIL_TAG_TRUE
			self.is_dirty = True
			self.save_db_props()

	def mark_delete(self):
		if self.delete_tag == x_consts.MAIL_TAG_FALSE:
			self.delete_tag = x_consts.MAIL_TAG_TRUE
			self.is_dirty = True
			self.save_db_props()
	