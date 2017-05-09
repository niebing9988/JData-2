#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import pandas as pd
from collections import Counter

ACTION_201602_FILE = "data/JData_Action_201602.csv"
ACTION_201603_FILE = "data/JData_Action_201603.csv"
ACTION_201604_FILE = "data/JData_Action_201604.csv"
USER_FILE = "data/JData_User_UTF8.csv"

# ACTION_201602_FILE = "sample_data/actions2.csv"
# ACTION_201603_FILE = "sample_data/actions3.csv"
# ACTION_201604_FILE = "sample_data/actions4.csv"
# USER_FILE = "sample_data/user.csv"

COMMENT_FILE = "data/JData_Comment.csv"
PRODUCT_FILE = "data/JData_Product.csv"

# ACTION_201603_EXTRA_FILE = "cache/JData_Action_201603_extra.csv"
NEW_USER_FILE = "cache2/JData_User_New.csv"
USER_TABLE_FILE = "cache2/user_table.csv"


def convert_age(age_str):
    if age_str == '-1':
        return -1
    elif age_str == '15岁以下':
        return 0
    elif age_str == '16-25岁':
        return 1
    elif age_str == '26-35岁':
        return 2
    elif age_str == '36-45岁':
        return 3
    elif age_str == '46-55岁':
        return 4
    elif age_str == '56岁以上':
        return 5
    else:
        return -1

def tranform_user_age():
    # Load data, header=0 means that the file has column names
    df = pd.read_csv(USER_FILE, header=0)
    # for i in range(len(df['age'])):
    #     print(i)
    #     if df['age'][i] == u"15岁以下":
    #         df['age'][i] = 0
    #     elif df['age'][i] == u"16-25岁":
    #         df['age'][i] = 1
    #     elif df['age'][i] == u"26-35岁":
    #         df['age'][i] = 2
    #     elif df['age'][i] == u"36-45岁":
    #         df['age'][i] = 3
    #     elif df['age'][i] == u"46-55岁":
    #         df['age'][i] = 4
    #     elif df['age'][i] == u"56岁以上":
    #         df['age'][i] = 5
    #     else:
    #         df['age'][i] = -1

    df['age'] = df['age'].map(convert_age)
    df['user_reg_tm'] = pd.to_datetime(df['user_reg_tm'])
    min_date = min(df['user_reg_tm'])

    df['user_reg_diff'] = [i for i in (df['user_reg_tm'] - min_date).dt.days]

    df.to_csv(NEW_USER_FILE, index=False)

def get_from_jdata_user():
    df_usr = pd.read_csv(NEW_USER_FILE, header=0)
    df_usr = df_usr[["user_id", "age", "sex", "user_lv_cd"]]
    return df_usr

def merge_action_data():
    df_ac = []
    df_ac.append(get_from_action_data(fname=ACTION_201602_FILE))
    df_ac.append(get_from_action_data(fname=ACTION_201603_FILE))
    # df_ac.append(get_from_action_data(fname=ACTION_201603_EXTRA_FILE))
    df_ac.append(get_from_action_data(fname=ACTION_201604_FILE))

    df_ac = pd.concat(df_ac, ignore_index=True)
    df_ac = df_ac.groupby(['user_id'], as_index=False).sum()

    df_ac['buy_addcart_ratio'] = df_ac['buy_num'] / df_ac['addcart_num']
    df_ac['buy_browse_ratio'] = df_ac['buy_num'] / df_ac['browse_num']
    df_ac['buy_click_ratio'] = df_ac['buy_num'] / df_ac['click_num']
    df_ac['buy_favor_ratio'] = df_ac['buy_num'] / df_ac['favor_num']

    df_ac.ix[df_ac['buy_addcart_ratio'] > 1., 'buy_addcart_ratio'] = 1.
    df_ac.ix[df_ac['buy_browse_ratio'] > 1., 'buy_browse_ratio'] = 1.
    df_ac.ix[df_ac['buy_click_ratio'] > 1., 'buy_click_ratio'] = 1.
    df_ac.ix[df_ac['buy_favor_ratio'] > 1., 'buy_favor_ratio'] = 1.

    return df_ac

# apply type count
def add_type_count(group):
    behavior_type = group.type.astype(int)
    type_cnt = Counter(behavior_type)

    group['browse_num'] = type_cnt[1]
    group['addcart_num'] = type_cnt[2]
    group['delcart_num'] = type_cnt[3]
    group['buy_num'] = type_cnt[4]
    group['favor_num'] = type_cnt[5]
    group['click_num'] = type_cnt[6]

    return group[['user_id', 'browse_num', 'addcart_num',
                  'delcart_num', 'buy_num', 'favor_num',
                  'click_num']]


def get_from_action_data(fname, chunk_size=100000):
    reader = pd.read_csv(fname, header=0, iterator=True)
    chunks = []
    loop = True
    while loop:
        try:
            chunk = reader.get_chunk(chunk_size)[["user_id", "type"]]
            chunks.append(chunk)
        except StopIteration:
            loop = False
            print("Iteration is stopped")

    df_ac = pd.concat(chunks, ignore_index=True)

    df_ac = df_ac.groupby(['user_id'], as_index=False).apply(add_type_count)
    # Select unique row
    df_ac = df_ac.drop_duplicates('user_id')

    return df_ac

if __name__ == "__main__":
    tranform_user_age()
    user_base = get_from_jdata_user()
    user_behavior = merge_action_data()

    # SQL: left join
    user_behavior = pd.merge(
        user_base, user_behavior, on=['user_id'], how='left')

    user_behavior.to_csv(USER_TABLE_FILE, index=False)

