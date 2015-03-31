# $Id: x_ccui_mailbox.py 174802 2015-03-14 03:10:16Z guoqing@NETEASE.COM $
# -*- coding:gbk -*-
import time
from cocosui import cc, ccui, ccs
import x_ccui_base
import x_glb
import x_ccui_util
import x_ccui_consts
import x_cache_base
import x_ccui_notice
import x_serialize
#import x_item_client_info
import x_common_consts
import x_ccontrol_items
import x_text
import x_item_general_weapon
import x_weakcall
import x_chest_Tips_config
from __builtin__ import str

class CCUI(x_ccui_base.CCUI):
	def __init__(self):
		super(CCUI, self).__init__()
		self.style = x_ccui_consts.CCUI_STYLE_POPUP
		self.create_ui("chest_homepage.json")
		self.init_products_info()
	
	def init_products_info(self):
		for k, v in enumerate(x_chest_Tips_config.DATA):
			dic = {}
			if  x_chest_Tips_config.DATA[v]['''对应宝箱'''] == '钻石':
				dic['钻石'] = (x_chest_Tips_config.DATA[v]['''格式化描述'''], x_chest_Tips_config.DATA[v]['''图标'''])
				self.list_products_diamond.append(dic)
			elif x_chest_Tips_config.DATA[v]['对应宝箱'] == '青铜':
				dic['青铜'] = (x_chest_Tips_config.DATA[v]['''格式化描述'''], x_chest_Tips_config.DATA[v]['''图标'''])
				self.list_products_bronze.append(dic)
			elif x_chest_Tips_config.DATA[v]['对应宝箱'] == '白银':
				dic['白银'] = (x_chest_Tips_config.DATA[v]['''格式化描述'''], x_chest_Tips_config.DATA[v]['''图标'''])
				self.list_products_silver.append(dic)
			elif x_chest_Tips_config.DATA[v]['对应宝箱'] == '黄金':
				dic['黄金'] = (x_chest_Tips_config.DATA[v]['''格式化描述'''], x_chest_Tips_config.DATA[v]['''图标'''])
				self.list_products_gold.append(dic)
			
		#x_chest_Tips_config.DATA[]
	def on_destroy(self):
		if self.chest_combine_key_page:
			gui_layer = x_glb.get_cocosui_layer()
			gui_layer.removeChild(self.chest_combine_key_page)
			self.chest_combine_key_page = None			
		if self.chest_open_result_page:
			gui_layer = x_glb.get_cocosui_layer()
			gui_layer.removeChild(self.chest_open_result_page)
			self.chest_open_result_page = None
			
	def on_create(self):
		self.set_params()
		self.load_widgets()
		#self.set_widgets()
		self.bind_events()
		#self.reg_actions()

	def set_params(self):				
		self.list_products_bronze = []
		self.list_products_silver = []
		self.list_products_gold = []
		self.list_products_diamond = []
		
	def load_widgets(self):
		self.button_close = self.get_child_by_name("button_close")		
		self.button_combine_key = self.get_child_by_name("btn_combine")
		
		self.panel_bronze = self.get_child_by_name("panel_bronze", True)						
		self.panel_sliver = self.get_child_by_name("panel_sliver", True)
		self.panel_gold = self.get_child_by_name("panel_gold", True)
		self.panel_diamond = self.get_child_by_name("panel_diamond", True)
		self.panel_girl = self.get_child_by_name("panel_girl", True)
		
		self.panel_bronze.setTouchEnabled(True)
		self.panel_sliver.setTouchEnabled(True)
		self.panel_gold.setTouchEnabled(True)
		self.panel_diamond.setTouchEnabled(True)
		#self.panel_picture.setTouchEnabled(True)
		
		#几点后免费
		self.item_txt_bronze = self.get_child_by_name("item_txt1", True)
		self.item_txt_sliver = self.get_child_by_name("item_txt2", True)
		self.item_txt_gold = self.get_child_by_name("item_txt3", True)
		self.item_txt_diamond = self.get_child_by_name("item_txt4", True)
		
		# 再开几次得橙色物品
		self.title_bronze = self.get_child_by_name("TextField_item1", True)
		self.title_sliver = self.get_child_by_name("TextField_item2", True)
		self.title_gold = self.get_child_by_name("TextField_item3", True)
		self.title_diamond = self.get_child_by_name("TextField_item4", True)
		
		#消耗
		self.text_consume_bronze = self.get_child_by_name("text_consume1", True)
		self.text_consume_sliver = self.get_child_by_name("text_consume2", True)
		self.text_consume_gold = self.get_child_by_name("text_consume3", True)
		self.text_consume_diamond = self.get_child_by_name("text_consume4", True) 
		
		#消耗具体数字
		self.cost_consume_bronze = self.get_child_by_name("cost_consume1", True)
		self.cost_consume_sliver = self.get_child_by_name("cost_consume2", True)
		self.cost_consume_gold = self.get_child_by_name("cost_consume3", True)
		self.cost_consume_diamond = self.get_child_by_name("cost_consume4", True) 
		
		#消耗图标
		self.icon_consume_bronze = self.get_child_by_name("icon_consume1", True)
		self.icon_consume_sliver = self.get_child_by_name("icon_consume2", True)
		self.icon_consume_gold = self.get_child_by_name("icon_consume3", True)
		self.icon_consume_diamond = self.get_child_by_name("icon_consume4", True) 
		
		#组合钥匙面板
		self.chest_combine_key_page = x_ccui_base.load_ui_page(self.root_path + "chest_combine_key.json")
		x_glb.get_cocosui_layer().addChild(self.chest_combine_key_page, 0, "chest_combine_key.json")
		self.chest_combine_key_page.setVisible(False)
		
		self.button_close_combinekeypage = x_ccui_util.get_child_by_name(self.chest_combine_key_page, "combine_key_close") 
		self.button_combine_combinekeypage = x_ccui_util.get_child_by_name(self.chest_combine_key_page, "combineBtn") 
		
		#宝箱开启结果面板
		self.chest_open_result_page = x_ccui_base.load_ui_page(self.root_path + "chest_open_result.json")
		x_glb.get_cocosui_layer().addChild(self.chest_open_result_page, 0, "chest_open_result.json")
		self.chest_open_result_page.setVisible(False)
		
		# 单项宝箱item
		self.chest_item_page = x_ccui_base.load_ui_page(self.root_path + "chest_item.json")
		self.item_panel = self.chest_item_page.getChildByName("item_panel") 
		self.item_panel.retain()
		self.item_panel.setVisible(False)			
		
		# 开启1次 或 10次
		self.button_open_1 = x_ccui_util.get_child_by_name(self.chest_item_page, "open_1")
		self.button_open_10 = x_ccui_util.get_child_by_name(self.chest_item_page, "open_10") 
		
		# 物品列表
		self.chest_product_list_page = x_ccui_base.load_ui_page(self.root_path + "chest_product_list.json")		
		x_glb.get_cocosui_layer().addChild(self.chest_product_list_page, 0, "chest_product_list.json")
		self.chest_product_list_page.setVisible(False)
		
		self.listlview_products = x_ccui_util.get_child_by_name(self.chest_product_list_page, "listlview_products")
		self.listlview_products.setTouchEnabled(True)
		self.listlview_products.setBounceEnabled(True)
		self.listlview_products.setInertiaScrollEnabled(False)
		self.item_product = x_ccui_util.get_child_by_name(self.chest_product_list_page, "item_product")
		self.icon_grid_product = x_ccui_util.get_child_by_name(self.chest_product_list_page, "icon_grid_product")
		self.txt_product = x_ccui_util.get_child_by_name(self.chest_product_list_page, "txt_product")

		
	def set_widgets(self):
		"""
		# widget settings
		self.mail_detail_page.setTouchEnabled(True)
		self.button_write.setVisible(False)
		self.item_mail.setTouchEnabled(True)
		self.item_mail.retain()
		self.item_mail.removeFromParent()
		self.listview_mails.setTouchEnabled(True)
		self.listview_mails.setBounceEnabled(True)
		self.listview_mails.setInertiaScrollEnabled(False)
		self.mail_detail_page.setVisible(False)
		self.item_item.retain()
		self.item_item.removeFromParent()
		"""
	
	def on_hide_homepage(self):
		#self.listlview_products.setVisible(False)		
		self.hide()
		self.chest_product_list_page.setVisible(False)
		
	def on_hide_key_combinepage(self):
		if self.chest_combine_key_page:
			self.chest_combine_key_page.setVisible(False)
	
	def on_combine_key_combinepage(self):
		print'grsn1304:click on_combine_key_combinepage()'

	def refresh_product_listview(self, chest_id):
		self.chest_product_list_page.setVisible(True)
		self.panel_girl.setVisible(False)		
		
		
		#self.listlview_products.retain()
		#self.listlview_products.removeFromParent()
		#self.panel_girl.addChild(self.listlview_products)
		#self.listlview_products.setPosition(0, 0)
				
		self.listlview_products.setVisible(True)
		self.listlview_products.removeAllItems()
		self.item_product.setVisible(True)
		
		len_products = 0
		if "1" == chest_id:
			len_products = len(self.list_products_bronze)	
			for i in range(0, len_products):			
				self.txt_product.setString(x_ccui_util.gbk2utf8(self.list_products_bronze[i]['青铜'][0]))				
				self.icon_grid_product.loadTexture(self.list_products_bronze[i]['青铜'][1])
				product_item = self.item_product.clone()
				self.listlview_products.pushBackCustomItem(product_item)
		elif "2" == chest_id:
			len_products = len(self.list_products_silver)		
			for i in range(0, len_products):
				self.txt_product.setString(x_ccui_util.gbk2utf8(self.list_products_silver[i]['白银'][0]))
				product_item = self.item_product.clone()
				self.listlview_products.pushBackCustomItem(product_item)		
		elif "3" == chest_id:
			len_products = len(self.list_products_gold)		
			for i in range(0, len_products):
				self.txt_product.setString(x_ccui_util.gbk2utf8(self.list_products_gold[i]['黄金'][0]))
				product_item = self.item_product.clone()
				self.listlview_products.pushBackCustomItem(product_item)
		elif "4" == chest_id:
			len_products = len(self.list_products_diamond)		
			for i in range(0, len_products):
				self.txt_product.setString(x_ccui_util.gbk2utf8(self.list_products_diamond[i]['钻石'][0]))
				product_item = self.item_product.clone()
				self.listlview_products.pushBackCustomItem(product_item)		
		
				
		self.item_product.setVisible(False)
		
	
	# 开户非点击宝箱item 的所有信息
	def show_info_for_item(self, chestId):
		if "1" == chestId:
			self.item_txt_sliver.setVisible(True)
			self.title_sliver.setVisible(True)
			self.icon_consume_sliver.setVisible(True)
			self.cost_consume_sliver.setVisible(True)
			self.text_consume_sliver.setVisible(True)
					
			self.item_txt_gold.setVisible(True)
			self.title_gold.setVisible(True)
			self.icon_consume_gold.setVisible(True)
			self.cost_consume_gold.setVisible(True)
			self.text_consume_gold.setVisible(True)
			
			self.item_txt_diamond.setVisible(True)
			self.title_diamond.setVisible(True)
			self.icon_consume_diamond.setVisible(True)
			self.cost_consume_diamond.setVisible(True)
			self.text_consume_diamond.setVisible(True)	
						
		elif "2" == chestId:
			self.item_txt_bronze.setVisible(True)
			self.title_bronze.setVisible(True)
			self.icon_consume_bronze.setVisible(True)
			self.cost_consume_bronze.setVisible(True)
			self.text_consume_bronze.setVisible(True)

			self.item_txt_gold.setVisible(True)
			self.title_gold.setVisible(True)
			self.icon_consume_gold.setVisible(True)
			self.cost_consume_gold.setVisible(True)
			self.text_consume_gold.setVisible(True)

			self.item_txt_diamond.setVisible(True)
			self.title_diamond.setVisible(True)
			self.icon_consume_diamond.setVisible(True)
			self.cost_consume_diamond.setVisible(True)
			self.text_consume_diamond.setVisible(True)	
			
		elif "3" == chestId:
			self.item_txt_bronze.setVisible(True)
			self.title_bronze.setVisible(True)
			self.icon_consume_bronze.setVisible(True)
			self.cost_consume_bronze.setVisible(True)
			self.text_consume_bronze.setVisible(True)

			self.item_txt_sliver.setVisible(True)
			self.title_sliver.setVisible(True)
			self.icon_consume_sliver.setVisible(True)
			self.cost_consume_sliver.setVisible(True)
			self.text_consume_sliver.setVisible(True)

			self.item_txt_diamond.setVisible(True)
			self.title_diamond.setVisible(True)
			self.icon_consume_diamond.setVisible(True)
			self.cost_consume_diamond.setVisible(True)
			self.text_consume_diamond.setVisible(True)
			
		elif "4" == chestId:
			self.item_txt_bronze.setVisible(True)
			self.title_bronze.setVisible(True)
			self.icon_consume_bronze.setVisible(True)
			self.cost_consume_bronze.setVisible(True)
			self.text_consume_bronze.setVisible(True)

			self.item_txt_sliver.setVisible(True)
			self.title_sliver.setVisible(True)
			self.icon_consume_sliver.setVisible(True)
			self.cost_consume_sliver.setVisible(True)
			self.text_consume_sliver.setVisible(True)

			self.item_txt_gold.setVisible(True)
			self.title_gold.setVisible(True)
			self.icon_consume_gold.setVisible(True)
			self.cost_consume_gold.setVisible(True)
			self.text_consume_gold.setVisible(True)
			
	def on_show_chest_item(self, chestId):
		self.item_panel.removeFromParent()
		products_cnt = 0
		if "1" == chestId:
			self.panel_bronze.addChild(self.item_panel)
			self.item_txt_bronze.setVisible(False)
			self.title_bronze.setVisible(False)
			self.icon_consume_bronze.setVisible(False)
			self.cost_consume_bronze.setVisible(False)
			self.text_consume_bronze.setVisible(False)
			
		elif "2" == chestId:
			self.panel_sliver.addChild(self.item_panel)
			self.item_txt_sliver.setVisible(False)
			self.title_sliver.setVisible(False)
			self.icon_consume_sliver.setVisible(False)
			self.cost_consume_sliver.setVisible(False)
			self.text_consume_sliver.setVisible(False)
			
		elif "3" == chestId:
			self.panel_gold.addChild(self.item_panel)
			self.item_txt_gold.setVisible(False)
			self.title_gold.setVisible(False)
			self.icon_consume_gold.setVisible(False)
			self.cost_consume_gold.setVisible(False)
			self.text_consume_gold.setVisible(False)
			
		elif "4" == chestId:
			self.panel_diamond.addChild(self.item_panel)
			self.item_txt_diamond.setVisible(False)
			self.title_diamond.setVisible(False)
			self.icon_consume_diamond.setVisible(False)
			self.cost_consume_diamond.setVisible(False)
			self.text_consume_diamond.setVisible(False)
			
				
		self.item_panel.setPosition(0, 0)
		self.item_panel.setVisible(True)
		self.show_info_for_item(chestId)		
		self.refresh_product_listview(chestId)
							
	def on_open_chest(self, cnt, chest_id):
		if "1" == cnt:
			#x_glb.net.send_and_wait("c_chest_open", chest_id=int(chest_id), buy_type=1, cnt=1)
			x_glb.net.send_and_wait("c_chest_buy", chest_id=int(chest_id), buy_type=1, cnt=1)
		else:
			pass
		
	def bind_events(self):
		# button event func
		x_ccui_util.bind_event_func(self.button_combine_key, self.on_show_combine_key)
		x_ccui_util.bind_event_func(self.button_close, self.on_hide_homepage)
		
		x_ccui_util.bind_event_func(self.button_close_combinekeypage, self.on_hide_key_combinepage)
		x_ccui_util.bind_event_func(self.button_combine_combinekeypage, self.on_combine_key_combinepage)
		
		x_ccui_util.bind_event_func(button=self.panel_bronze, func=self.on_show_chest_item, args=("1"))
		x_ccui_util.bind_event_func(button=self.panel_sliver, func=self.on_show_chest_item, args=("2"))
		x_ccui_util.bind_event_func(button=self.panel_gold, func=self.on_show_chest_item, args=("3"))
		x_ccui_util.bind_event_func(button=self.panel_diamond, func=self.on_show_chest_item, args=("4"))
		
		x_ccui_util.bind_event_func(button=self.button_open_1, func=self.on_open_chest, args=("1", 1))
		x_ccui_util.bind_event_func(button=self.button_open_10, func=self.on_open_chest, args=("10", 1))		

	def on_show_combine_key(self):
		if self.chest_combine_key_page:
			self.chest_combine_key_page.setVisible(True)		
			
	def reg_actions(self):
		x_glb.data.data_cache.cache_mail.reg_action_receiver(
			(
				(x_cache_base.Action.UPDATE, self, self.on_mail_list),
			))
	
	"""
	def on_destroy(self):
		super(CCUI, self).on_destroy()
		if self.item_control:
			self.item_control.destroy()
			self.item_control = None
	"""

	def on_show(self):
		super(CCUI, self).on_show()
		print 'grsn1304:接受到后端协议，准备设置字体'
		if self.item_txt_bronze:
			self.item_txt_bronze.setString(x_ccui_util.gbk2utf8("免费"))
		else:
			print 'grsn1304:self.item_txt_bronze is none'
		
		if self.item_panel.isVisible():
			self.item_panel.setVisible(False)
		if not self.panel_girl.isVisible():
			self.panel_girl.setVisible(True)
		self.listlview_products.setVisible(False)	