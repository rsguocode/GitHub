# -*- coding: gbk -*-
import math
NUM_SILVER_LAST = 0
NUM_SILVER_REMAIN = 1
NUM_GOLD_LAST = 2
NUM_GOLD_NEXT = 3

NUM_2_EN = ('''silver_last''', '''silver_remain''', '''gold_last''', '''gold_next''', )

NUM_2_CH = ('''�����������ʱ��''', '''���հ���ʣ�����''', '''�ƽ��������ʱ��''', '''�ƽ�Ʒʣ�����''', )

EN_2_CH = {
'''gold_last''': '''�ƽ��������ʱ��''',
'''silver_last''': '''�����������ʱ��''',
'''gold_next''': '''�ƽ�Ʒʣ�����''',
'''silver_remain''': '''���հ���ʣ�����''',
}

EN_2_NUM = {
'''gold_last''': 2,
'''silver_last''': 0,
'''gold_next''': 3,
'''silver_remain''': 1,
}

EN_2_SHOW_NAME = {
'''gold_last''': '''�ƽ��������ʱ��''',
'''silver_last''': '''�����������ʱ��''',
'''gold_next''': '''�ƽ�Ʒʣ�����''',
'''silver_remain''': '''���հ���ʣ�����''',
}



FORMAT_FUNC_MAP = {
}

def format_attr(attr_name, attr_value):
  if attr_name in FORMAT_FUNC_MAP:
    return FORMAT_FUNC_MAP[attr_name]( attr_value )
  else:
    return str(attr_value)