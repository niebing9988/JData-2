import pandas as pd

# 去掉只有购买记录的用户(没有可用的历史浏览等记录来预测用户将来的购买意向)
# 去掉浏览量很大而购买量很少的用户(惰性用户或爬虫用户)
# 去掉最后5(7)天没有记录(交互)的商品和用户

RAW_USER_TABLE_FILE = "data/JData_User_UTF8.csv"
FILTER_RAW_USER_TABLE_FILE = "data/New_JData_User_UTF8.csv"
USER_TABLE_FILE = "cache2/user_table.csv"
ITEM_TABLE_FILE = "cache2/item_table.csv"
FILTER_USER_TABLE_FILE = "cache2/filter_user_table.csv"

# 读取数据
# ['user_id',
#  'age',
#  'sex',
#  'user_lv_cd',
#  'browse_num',
#  'addcart_num',
#  'delcart_num',
#  'buy_num',
#  'favor_num',
#  'click_num',
#  'buy_addcart_ratio',
#  'buy_browse_ratio',
#  'buy_click_ratio',
#  'buy_favor_ratio']
df_usr = pd.read_csv(USER_TABLE_FILE, header=0)
# 提取有购买记录的用户
df_usr = df_usr[df_usr['buy_num'] != 0]
# 去除掉僵尸或者爬虫用户
df_usr = df_usr[(df_usr['buy_num'] > 2) & (df_usr['browse_num'] < 6000)]
df_usr.to_csv(FILTER_USER_TABLE_FILE, index = False)

# 原始的用户数据也进行过滤一下
df_raw_usr = pd.read_csv(RAW_USER_TABLE_FILE, header=0)
df_raw_usr = df_raw_usr[df_raw_usr.user_id.isin(df_usr['user_id'].unique())]
df_raw_usr.to_csv(FILTER_RAW_USER_TABLE_FILE, index = False)

# 去除掉没有任何交互的商品条目
df_item = pd.read_csv(ITEM_TABLE_FILE, header=0)
test = df_item[df_item['browse_num'] == ""]


# 去除掉最后 5 (7) 天没有记录（交互）的商品和用户
# 因为没有交互，说明未来也就没有购买物品的欲望
# 虽然可能会有些用户种草很久
df_item = pd.read_csv(ITEM_TABLE_FILE, header = 0)



# 计算一下每个用户一般几天内会买一个商品
