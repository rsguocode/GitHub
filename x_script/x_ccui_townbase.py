# $Id: x_ccui_townbase.py 174687 2015-03-13 02:41:53Z akara@NETEASE.COM $
# -*- coding:gbk -*-

import x_ccui_base
import x_glb
import x_ccontrol_tab
import x_ccui_util
import x_ccui_consts

from cocosui import cc, ccui, ccs


class CCUI(x_ccui_base.CCUI):
	def __init__(self,):
		super(CCUI, self).__init__()
		self.style = x_ccui_consts.CCUI_STYLE_PINNED

	def register_btn_event(self, name, btn_idx):
		widget = self.get_child_by_name(name)
		if not widget:
			return
		widget.setTouchEnabled(True)
		if widget is not None:
			x_ccui_util.bind_events_func(button=widget, 
				event2func={
				ccui.WIDGET_TOUCHEVENTTYPE_BEGAN: self.on_btn_down,
				ccui.WIDGET_TOUCHEVENTTYPE_CANCELED: self.on_btn_cancel,
				ccui.WIDGET_TOUCHEVENTTYPE_ENDED: self.on_btn_up,
				}, args=(widget, btn_idx))
			icon_path = x_ccui_consts.BUTTON_IDX_2_ICON.get(btn_idx, None)
			if icon_path is not None:
				image_view = ccui.ImageView.create()
				content_size = widget.getLayoutSize()
				image_view.setContentSize(content_size)
				image_view.loadTexture(icon_path)
				image_view.setPosition(content_size.width/2, content_size.height/2)
				widget.addChild(image_view)
				if btn_idx != x_ccui_consts.BUTTON_IDX_MAIN and btn_idx != x_ccui_consts.BUTTON_IDX_TASKNAV:
					image_view = ccui.ImageView.create()
					content_size = widget.getLayoutSize()
					image_view.setContentSize(content_size)
					image_view.loadTexture(icon_path[:-4] + "2" + ".png")
					image_view.setPosition(content_size.width/2, content_size.height/2)
					widget.addChild(image_view)


	#按钮被按下的时候的统一处理
	def on_btn_down(self, widget, btn_idx):
		widget.setScaleX(1.05)
		widget.setScaleY(1.05)

	def on_btn_cancel(self, widget, btn_idx):
		widget.setScaleX(1)
		widget.setScaleY(1)


	#按钮被释放时候的统一处理
	def on_btn_up(self, widget, btn_idx):
		widget.setScaleX(1)
		widget.setScaleY(1)
		if btn_idx == x_ccui_consts.BUTTON_IDX_SKILL:
			import x_ccui_skill_mgr
			x_ccui_skill_mgr.CCUI.instance().show()
		elif btn_idx == x_ccui_consts.BUTTON_IDX_ATTR:
			import x_ccui_attr
			ui = x_ccui_attr.CCUI.instance()
			ui.set_layout_me()
			ui.show_attr()
		elif btn_idx == x_ccui_consts.BUTTON_IDX_BAG:
			import x_ccui_attr
			ui = x_ccui_attr.CCUI.instance()
			ui.set_layout_me()
			ui.show_bag()
		elif btn_idx == x_ccui_consts.BUTTON_IDX_ELBLEM:
			import x_ccui_emblem_mgr
			x_ccui_emblem_mgr.CCUI.instance().show()
		elif btn_idx == x_ccui_consts.BUTTON_IDX_RUNE:
			import x_ccui_rune_mgr
			x_ccui_rune_mgr.CCUI.instance().show()
		elif btn_idx == x_ccui_consts.BUTTON_IDX_SYSTEM:
			if x_glb.gmcmd.is_gm_mode:
				import x_ccui_gm_command
				x_ccui_gm_command.CCUI.instance().show()
			else:
				import x_ccui_messagebox
				import x_text
				x_ccui_messagebox.CCUI.instance().show_message(x_text.CANT_USE_SYS)
		elif btn_idx == x_ccui_consts.BUTTON_IDX_TASK:
			import x_ccui_task_mgr
			x_ccui_task_mgr.CCUI.instance().show()
		elif btn_idx == x_ccui_consts.BUTTON_IDX_ACTIVITY:
			import x_ccui_various_entry
			x_ccui_various_entry.CCUI.instance().show()
		elif btn_idx == x_ccui_consts.BUTTON_IDX_ARENA:
			x_glb.world.scene.me.goto_arena()
		elif btn_idx == x_ccui_consts.BUTTON_IDX_TASKNAV:
			is_ok = x_glb.world.scene.me.goto_task(task_id=0)
			if not is_ok:
				import x_sysopen_attr
				x_glb.goto_ui(x_sysopen_attr.DAILY_TASK)
		elif btn_idx == x_ccui_consts.BUTTON_IDX_FAIRY:
			import x_ccui_fairy
			x_ccui_fairy.CCUI.instance().show()
		elif btn_idx == x_ccui_consts.BUTTON_IDX_STAR:
			import x_ccui_xingzuo
			x_ccui_xingzuo.CCUI.instance().show()
		elif btn_idx == x_ccui_consts.BUTTON_IDX_RANK:
			import x_ccui_ranking_list
			x_ccui_ranking_list.CCUI.instance().show()
		elif btn_idx == x_ccui_consts.BUTTON_IDX_MAIL:
			#import x_ccui_mailbox
			#x_ccui_mailbox.CCUI.instance().show()
			import x_ccui_chest_homepage
			x_ccui_chest_homepage.CCUI.instance().show()
			
		elif btn_idx == x_ccui_consts.BUTTON_IDX_FRIEND:
			import x_ccui_relation
			x_glb.gmcmd._do_up("ccui_relation")
			x_ccui_relation.CCUI.instance().show()
		elif btn_idx == x_ccui_consts.BUTTON_IDX_STONE:
			import x_ccui_gem_mgr
			x_ccui_gem_mgr.CCUI.instance().show()
		elif btn_idx == x_ccui_consts.BUTTON_IDX_UNION:
			import x_ccui_union_list
			x_ccui_union_list.CCUI.instance().show()
		elif btn_idx == x_ccui_consts.BUTTON_IDX_FATE:
			import x_ccui_soul
			x_ccui_soul.CCUI.instance().show()
		if btn_idx != x_ccui_consts.BUTTON_IDX_TASKNAV:
			x_glb.world.scene.me.enable_auto_move(False)

	#开放按钮的统一处理
	def on_btn_open(self, widget, btn_idx):
		pass