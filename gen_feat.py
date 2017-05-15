#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import time
from datetime import datetime
from datetime import timedelta
import pandas as pd
import pickle
import os
import math
import numpy as np

action_1_path = "./data/actions2.csv"
action_2_path = "./data/actions3.csv"
action_3_path = "./data/actions4.csv"
user_path = "./data/add_cart_11_users.csv"

comment_path = "./data/comment.csv"
product_path = "./data/product.csv"


comment_date = ["2016-02-01", "2016-02-08",
                "2016-02-15", "2016-02-22",
                "2016-02-29", "2016-03-07",
                "2016-03-14", "2016-03-21",
                "2016-03-28", "2016-04-04", "2016-04-11", "2016-04-15"]


def convert_age(age_str):
    if age_str == '-1':
        return 0
    elif age_str == '15岁以下':
        return 1
    elif age_str == '16-25岁':
        return 2
    elif age_str == '26-35岁':
        return 3
    elif age_str == '36-45岁':
        return 4
    elif age_str == '46-55岁':
        return 5
    elif age_str == '56岁以上':
        return 6
    else:
        return -1

def get_basic_user_feat():
    """
    这里只是简单将用户表类型进行转换
    :return:
    """

    dump_path = './cache/basic_user.pkl'
    if os.path.exists(dump_path):
        user = pickle.load(open(dump_path))
    else:

        # user = pd.read_csv(user_path, encoding='gbk')
        user = pd.read_csv(user_path)
        user['age'] = user['age'].map(convert_age)
        age_df = pd.get_dummies(user["age"], prefix="age")
        sex_df = pd.get_dummies(user["sex"], prefix="sex")
        user_lv_df = pd.get_dummies(user["user_lv_cd"], prefix="user_lv_cd")

        user = pd.concat([user['user_id'], age_df, sex_df, user_lv_df], axis=1)
        pickle.dump(user, open(dump_path, 'w'))
    return user


def get_basic_product_feat():
    dump_path = './cache/basic_product.pkl'
    if os.path.exists(dump_path):
        product = pickle.load(open(dump_path))
    else:
        product = pd.read_csv(product_path)
        attr1_df = pd.get_dummies(product["a1"], prefix="a1")
        attr2_df = pd.get_dummies(product["a2"], prefix="a2")
        attr3_df = pd.get_dummies(product["a3"], prefix="a3")
        product = pd.concat([product[['sku_id', 'cate', 'brand']], attr1_df, attr2_df, attr3_df], axis=1)
        pickle.dump(product, open(dump_path, 'w'))
    return product


def get_actions_1():
    action = pd.read_csv(action_1_path)
    return action

def get_actions_2():
    action2 = pd.read_csv(action_2_path)
    return action2

def get_actions_3():
    action3 = pd.read_csv(action_3_path)
    return action3


def get_actions(start_date, end_date):
    """
    获取指定时间间隔的 actions
    :param start_date:
    :param end_date:
    :return: actions: pd.Dataframe
    """
    dump_path = './cache/all_action_%s_%s.pkl' % (start_date, end_date)
    if os.path.exists(dump_path):
        actions = pickle.load(open(dump_path))
    else:
        action_1 = get_actions_1()
        action_2 = get_actions_2()
        action_3 = get_actions_3()
        actions = pd.concat([action_1, action_2, action_3])
        actions = actions[(actions.time >= start_date) & (actions.time < end_date)]
        pickle.dump(actions, open(dump_path, 'w'))
    return actions


def get_action_feat(start_date, end_date):
    dump_path = './cache/action_accumulate_%s_%s.pkl' % (start_date, end_date)
    if os.path.exists(dump_path):
        actions = pickle.load(open(dump_path))
    else:
        actions = get_actions(start_date, end_date)
        actions = actions[['user_id', 'sku_id', 'type']]

        df = pd.get_dummies(actions['type'], prefix='%s-%s-action' % (start_date, end_date))
        acLen = df.shape[0]
        for i in range(1, 7):
            if '%s-%s-action' % (start_date, end_date) + str(i) not in df:
                df['%s-%s-action' % (start_date, end_date) + str(i)] = np.zeros(acLen)

        actions = pd.concat([actions, df], axis=1)
        actions = actions.groupby(['user_id', 'sku_id'], as_index=False).sum()
        del actions['type']
        pickle.dump(actions, open(dump_path, 'w'))
    return actions


def get_accumulate_action_feat(start_date, end_date):
    dump_path = './cache/action_accumulate_%s_%s.pkl' % (start_date, end_date)
    if os.path.exists(dump_path):
        actions = pickle.load(open(dump_path))
    else:
        actions = get_actions(start_date, end_date)
        df = pd.get_dummies(actions['type'], prefix='action')
        actions = pd.concat([actions, df], axis=1) # type: pd.DataFrame
        #近期行为按时间衰减
        actions['weights'] = actions['time'].map(lambda x: datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(x, '%Y-%m-%d %H:%M:%S'))
        #actions['weights'] = time.strptime(end_date, '%Y-%m-%d') - actions['datetime']
        actions['weights'] = actions['weights'].map(lambda x: math.exp(-x.days))
        print actions.head(10)
        actions['action_1'] = actions['action_1'] * actions['weights']
        actions['action_2'] = actions['action_2'] * actions['weights']
        actions['action_3'] = actions['action_3'] * actions['weights']
        actions['action_4'] = actions['action_4'] * actions['weights']
        actions['action_5'] = actions['action_5'] * actions['weights']
        actions['action_6'] = actions['action_6'] * actions['weights']
        del actions['model_id']
        del actions['type']
        del actions['time']
        del actions['datetime']
        del actions['weights']
        actions = actions.groupby(['user_id', 'sku_id', 'cate', 'brand'], as_index=False).sum()
        pickle.dump(actions, open(dump_path, 'w'))
    return actions

def get_comments_product_feat(start_date, end_date):

    """

    计算规定时间内的，对应商品下不同类型的评论总数和

    :param start_date:
    :param end_date:
    :return:
    """

    dump_path = './cache/comments_accumulate_%s_%s.pkl' % (start_date, end_date)
    if os.path.exists(dump_path):
        comments = pickle.load(open(dump_path))
    else:
        comments = pd.read_csv(comment_path)
        comment_date_end = end_date
        comment_date_begin = comment_date[0]
        for date in reversed(comment_date):
            if date < comment_date_end:
                comment_date_begin = date
                break
        comments = comments[(comments.dt >= comment_date_begin) & (comments.dt < comment_date_end)]
        df = pd.get_dummies(comments['comment_num'], prefix='comment_num')
        comments = pd.concat([comments, df], axis=1) # type: pd.DataFrame
        #del comments['dt']
        #del comments['comment_num']
        comments = comments[['sku_id', 'has_bad_comment', 'bad_comment_rate', 'comment_num_1', 'comment_num_2', 'comment_num_3', 'comment_num_4']]
        pickle.dump(comments, open(dump_path, 'w'))
    return comments

def get_accumulate_user_feat(start_date, end_date):

    """

    累加计算给定时间段内，不同用户下 action_4/action_i 操作数的占比
    也即是 下单数与其他类型操作数的比率

    :param start_date: 开始时间
    :param end_date: 结束时间
    :return:
    """

    feature = ['user_id', 'user_action_1_ratio', 'user_action_2_ratio', 'user_action_3_ratio',
               'user_action_5_ratio', 'user_action_6_ratio']
    dump_path = './cache/user_feat_accumulate_%s_%s.pkl' % (start_date, end_date)
    if os.path.exists(dump_path):
        actions = pickle.load(open(dump_path))
    else:
        actions = get_actions(start_date, end_date)
        df = pd.get_dummies(actions['type'], prefix='action')
        actions = pd.concat([actions['user_id'], df], axis=1)
        actions = actions.groupby(['user_id'], as_index=False).sum()

        # 解决小样本测试出现的bug
        acLen = actions.shape[0]
        for i in range(1, 7):
            if "action_" + str(i) not in actions:
                actions["action_" + str(i)] = np.zeros(acLen)
        
        actions['user_action_1_ratio'] = actions['action_4'] / actions['action_1']
        actions['user_action_2_ratio'] = actions['action_4'] / actions['action_2']
        actions['user_action_3_ratio'] = actions['action_4'] / actions['action_3']
        actions['user_action_5_ratio'] = actions['action_4'] / actions['action_5']
        actions['user_action_6_ratio'] = actions['action_4'] / actions['action_6']
        actions = actions[feature]
        pickle.dump(actions, open(dump_path, 'w'))
    return actions

def get_accumulate_product_feat(start_date, end_date):
    """
    累加计算给定时间段内，不同商品下 下单数/操作数 的占比
    :param start_date:
    :param end_date:
    :return:
    """
    feature = ['sku_id', 'product_action_1_ratio', 'product_action_2_ratio', 'product_action_3_ratio',
               'product_action_5_ratio', 'product_action_6_ratio']
    dump_path = './cache/product_feat_accumulate_%s_%s.pkl' % (start_date, end_date)
    if os.path.exists(dump_path):
        actions = pickle.load(open(dump_path))
    else:
        actions = get_actions(start_date, end_date)
        df = pd.get_dummies(actions['type'], prefix='action')
        actions = pd.concat([actions['sku_id'], df], axis=1)
        actions = actions.groupby(['sku_id'], as_index=False).sum()
        
        # 解决小样本测试出现的bug
        acLen = actions.shape[0]
        for i in range(1, 7):
            if "action_" + str(i) not in actions:
                actions["action_" + str(i)] = np.zeros(acLen)
        
        actions['product_action_1_ratio'] = actions['action_4'] / actions['action_1']
        actions['product_action_2_ratio'] = actions['action_4'] / actions['action_2']
        actions['product_action_3_ratio'] = actions['action_4'] / actions['action_3']
        actions['product_action_5_ratio'] = actions['action_4'] / actions['action_5']
        actions['product_action_6_ratio'] = actions['action_4'] / actions['action_6']
        actions = actions[feature]
        pickle.dump(actions, open(dump_path, 'w'))
    return actions

def get_labels(start_date, end_date):
    """
    给定时间内用户是否有下单购买商品
    :param start_date:
    :param end_date:
    :return:
    """
    dump_path = './cache/labels_%s_%s.pkl' % (start_date, end_date)
    if os.path.exists(dump_path):
        actions = pickle.load(open(dump_path))
    else:
        actions = get_actions(start_date, end_date)
        actions = actions[actions['type'] == 4]
        actions = actions.groupby(['user_id', 'sku_id'], as_index=False).sum()
        actions['label'] = 1
        actions = actions[['user_id', 'sku_id', 'label']]
        pickle.dump(actions, open(dump_path, 'w'))
    return actions

def make_test_set(train_start_date, train_end_date):
    dump_path = './cache/test_set_%s_%s.pkl' % (train_start_date, train_end_date)
    if os.path.exists(dump_path):
        actions = pickle.load(open(dump_path))
    else:
        start_days = "2016-02-01"
        user = get_basic_user_feat()
        product = get_basic_product_feat()
        user_acc = get_accumulate_user_feat(start_days, train_end_date)

        product_acc = get_accumulate_product_feat(start_days, train_end_date)
        comment_acc = get_comments_product_feat(train_start_date, train_end_date)
        #labels = get_labels(test_start_date, test_end_date)

        # generate 时间窗口
        # actions = get_accumulate_action_feat(train_start_date, train_end_date)
        actions = None
        for i in (1, 2, 3, 5, 7, 11, 15):
            start_days = datetime.strptime(train_end_date, '%Y-%m-%d') - timedelta(days=i)
            start_days = start_days.strftime('%Y-%m-%d')
            if actions is None:
                actions = get_action_feat(start_days, train_end_date)
            else:
                actions = pd.merge(actions, get_action_feat(start_days, train_end_date), how='left',
                                   on=['user_id', 'sku_id'])

        actions = pd.merge(actions, user, how='left', on='user_id')
        actions = pd.merge(actions, user_acc, how='left', on='user_id')
        actions = pd.merge(actions, product, how='left', on='sku_id')
        actions = pd.merge(actions, product_acc, how='left', on='sku_id')
        actions = pd.merge(actions, comment_acc, how='left', on='sku_id')
        #actions = pd.merge(actions, labels, how='left', on=['user_id', 'sku_id'])
        actions = actions.fillna(0)
        # actions = actions[actions['cate'] == 8]

    users = actions[['user_id', 'sku_id']].copy()
    del actions['user_id']
    del actions['sku_id']
    del actions['cate']
    return users, actions

def make_train_set(train_start_date, train_end_date, test_start_date, test_end_date):
    dump_path = './cache/train_set_%s_%s_%s_%s.pkl' % (train_start_date, train_end_date, test_start_date, test_end_date)
    if os.path.exists(dump_path):
        actions = pickle.load(open(dump_path))
    else:
        start_days = "2016-02-01"
        # ['user_id',
        #  'age_0',
        #  'age_2',
        #  'age_3',
        #  'age_4',
        #  'age_5',
        #  'age_6',
        #  'sex_0',
        #  'sex_1',
        #  'sex_2',
        #  'user_lv_cd_1',
        #  'user_lv_cd_2',
        #  'user_lv_cd_3',
        #  'user_lv_cd_4',
        #  'user_lv_cd_5']         
        user = get_basic_user_feat()
        # ['sku_id',
        #  'cate',
        #  'brand',
        #  'a1_-1',
        #  'a1_1',
        #  'a1_2',
        #  'a1_3',
        #  'a2_-1',
        #  'a2_1',
        #  'a2_2',
        #  'a3_-1',
        #  'a3_1',
        #  'a3_2']        
        product = get_basic_product_feat()
        # 累加计算给定时间段内，不同用户下的下单数与其他类型操作数的比率
        # ['user_id',
        #  'user_action_1_ratio',
        #  'user_action_2_ratio',
        #  'user_action_3_ratio',
        #  'user_action_5_ratio',
        #  'user_action_6_ratio']
        user_acc = get_accumulate_user_feat(start_days, train_end_date)
        # 累加计算给定时间段内，不同商品下 下单数/操作数 的占比
        # ['sku_id',
        #  'product_action_1_ratio',
        #  'product_action_2_ratio',
        #  'product_action_3_ratio',
        #  'product_action_5_ratio',
        #  'product_action_6_ratio']        
        product_acc = get_accumulate_product_feat(start_days, train_end_date)
        # 计算规定时间内的，对应商品下不同类型的评论总数和
        # ['sku_id',
        #  'has_bad_comment',
        #  'bad_comment_rate',
        #  'comment_num_1',
        #  'comment_num_2',
        #  'comment_num_3',
        #  'comment_num_4']        
        comment_acc = get_comments_product_feat(train_start_date, train_end_date)
        # 在测试的段时间内，用户是否有下单买过某些商品
        # ['user_id', 'sku_id', 'label']
        labels = get_labels(test_start_date, test_end_date)

        # generate 时间窗口
        # actions = get_accumulate_action_feat(train_start_date, train_end_date)
        actions = None
        for i in (1, 2, 3, 5, 7, 11, 15):
            start_days = datetime.strptime(train_end_date, '%Y-%m-%d') - timedelta(days=i)
            start_days = start_days.strftime('%Y-%m-%d')
            if actions is None:
                actions = get_action_feat(start_days, train_end_date)
            else:
                actions = pd.merge(actions, get_action_feat(start_days, train_end_date), how='left',
                                   on=['user_id', 'sku_id'])

        actions = pd.merge(actions, user, how='left', on='user_id')
        actions = pd.merge(actions, user_acc, how='left', on='user_id')
        actions = pd.merge(actions, product, how='left', on='sku_id')
        actions = pd.merge(actions, product_acc, how='left', on='sku_id')
        actions = pd.merge(actions, comment_acc, how='left', on='sku_id')
        actions = pd.merge(actions, labels, how='left', on=['user_id', 'sku_id'])
        actions = actions.fillna(0)

    users = actions[['user_id', 'sku_id']].copy()
    labels = actions['label'].copy()
    # 删除掉无用的字段
    del actions['user_id']
    del actions['sku_id']
    del actions['label']
    del actions['cate']

    # ['2016-02-29-2016-03-01-action_1',
    #  '2016-02-29-2016-03-01-action_6',
    #  '2016-02-28-2016-03-01-action_1',
    #  '2016-02-28-2016-03-01-action_6',
    #  '2016-02-27-2016-03-01-action_1',
    #  '2016-02-27-2016-03-01-action_6',
    #  '2016-02-25-2016-03-01-action_1',
    #  '2016-02-25-2016-03-01-action_6',
    #  '2016-02-23-2016-03-01-action_1',
    #  '2016-02-23-2016-03-01-action_6',
    #  '2016-02-19-2016-03-01-action_1',
    #  '2016-02-19-2016-03-01-action_2',
    #  '2016-02-19-2016-03-01-action_4',
    #  '2016-02-19-2016-03-01-action_6',
    #  '2016-02-15-2016-03-01-action_1',
    #  '2016-02-15-2016-03-01-action_2',
    #  '2016-02-15-2016-03-01-action_4',
    #  '2016-02-15-2016-03-01-action_6',
    #  '2016-02-09-2016-03-01-action_1',
    #  '2016-02-09-2016-03-01-action_2',
    #  '2016-02-09-2016-03-01-action_4',
    #  '2016-02-09-2016-03-01-action_6',
    #  '2016-01-31-2016-03-01-action_1',
    #  '2016-01-31-2016-03-01-action_2',
    #  '2016-01-31-2016-03-01-action_4',
    #  '2016-01-31-2016-03-01-action_6',
    #  'age_0',
    #  'age_2',
    #  'age_3',
    #  'age_4',
    #  'age_5',
    #  'age_6',
    #  'sex_0',
    #  'sex_1',
    #  'sex_2',
    #  'user_lv_cd_1',
    #  'user_lv_cd_2',
    #  'user_lv_cd_3',
    #  'user_lv_cd_4',
    #  'user_lv_cd_5',
    #  'user_action_1_ratio',
    #  'user_action_2_ratio',
    #  'user_action_3_ratio',
    #  'user_action_5_ratio',
    #  'user_action_6_ratio',
    #  'cate',
    #  'brand',
    #  'a1_-1',
    #  'a1_1',
    #  'a1_2',
    #  'a1_3',
    #  'a2_-1',
    #  'a2_1',
    #  'a2_2',
    #  'a3_-1',
    #  'a3_1',
    #  'a3_2',
    #  'product_action_1_ratio',
    #  'product_action_2_ratio',
    #  'product_action_3_ratio',
    #  'product_action_5_ratio',
    #  'product_action_6_ratio',
    #  'has_bad_comment',
    #  'bad_comment_rate',
    #  'comment_num_1',
    #  'comment_num_2',
    #  'comment_num_3',
    #  'comment_num_4']
    return users, actions, labels

if __name__ == '__main__':
    get_action_feat("2016-02-01", "2016-02-05")

    # train_start_date = '2016-02-01'
    # train_end_date = '2016-03-01'
    # test_start_date = '2016-03-01'
    # test_end_date = '2016-03-05'

    # user, action, label = make_train_set(train_start_date, train_end_date, test_start_date, test_end_date)
    
    # print user.head(10)
    # print action.head(10)
    # print label.head(10)



