#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from gen_feat import make_train_set
from gen_feat import make_test_set
from sklearn.model_selection import train_test_split
import xgboost as xgb
from local_evaluation import report
from scipy import stats
import matplotlib.pyplot as plt


def xgboost_make_submission():
    train_start_date = '2016-03-10'
    train_end_date = '2016-04-11'
    test_start_date = '2016-04-11'
    test_end_date = '2016-04-16'

    sub_start_date = '2016-04-05'
    sub_end_date = '2016-04-16'

    user_index, training_data, label = make_train_set(train_start_date, train_end_date, test_start_date, test_end_date)
    # 简单划分 训练集和验证集
    X_train, X_test, y_train, y_test = train_test_split(training_data.values, label.values, test_size=0.2, random_state=0)
    # 转换成他们内建的矩阵
    dtrain=xgb.DMatrix(X_train, label=y_train)
    dtest=xgb.DMatrix(X_test, label=y_test)
    param = {'learning_rate' : 0.1, 'n_estimators': 1000, 'max_depth': 3, 
        'min_child_weight': 5, 'gamma': 0, 'subsample': 1.0, 'colsample_bytree': 0.8,
        'scale_pos_weight': 1, 'eta': 0.05, 'silent': 1, 'objective': 'binary:logistic'}
    num_round = 150
    param['nthread'] = 4
    #param['eval_metric'] = "auc"
    # 转换成元组
    plst = param.items()
    # 设置模型的评价指标
    plst += [('eval_metric', 'logloss')]
    evallist = [(dtest, 'eval'), (dtrain, 'train')]
    bst=xgb.train(plst, dtrain, num_round, evallist)
    
    sub_user_index, sub_trainning_data = make_test_set(sub_start_date, sub_end_date)
    sub_trainning_data = xgb.DMatrix(sub_trainning_data.values)
    
    y = bst.predict(sub_trainning_data)
    sub_user_index['label'] = y
    pred = sub_user_index[sub_user_index['label'] >= 0.03]
    pred = pred[['user_id', 'sku_id']]
    pred = pred.groupby('user_id').first().reset_index()
    pred['user_id'] = pred['user_id'].astype(int)
    pred.to_csv('./sub/submission.csv', index=False, index_label=False)



def xgboost_cv():
    # 一个月为训练数据
    train_start_date = '2016-02-15'
    train_end_date = '2016-03-15'
    # 根据上一个月训练的数据，预测未来五天的数据
    test_start_date = '2016-03-16'
    test_end_date = '2016-03-20'

    # 用之前的数据验证模型的有效性
    # 输入
    sub_start_date = '2016-03-21'
    sub_end_date = '2016-04-02'
    # 输出
    sub_test_start_date = '2016-04-03'
    sub_test_end_date = '2016-04-08'

    user_index, training_data, label = make_train_set(train_start_date, train_end_date, test_start_date, test_end_date)
    # 简单划分 训练集和验证集
    X_train, X_test, y_train, y_test = train_test_split(training_data, label, test_size=0.2, random_state=0)
    dtrain=xgb.DMatrix(X_train.values, label=y_train)
    dtest=xgb.DMatrix(X_test.values, label=y_test)
    param = {'max_depth': 10, 'eta': 0.05, 'silent': 1, 'objective': 'binary:logistic'}
    num_round = 166
    param['nthread'] = 5
    param['eval_metric'] = "auc"
    plst = param.items()
    evallist = [(dtest, 'eval'), (dtrain, 'train')]
    bst=xgb.train(plst, dtrain, num_round, evallist)

    sub_user_index, sub_trainning_data, sub_label = make_train_set(sub_start_date, sub_end_date,
                                                                   sub_test_start_date, sub_test_end_date)
    sub_trainning_data = xgb.DMatrix(sub_trainning_data.values)
    y = bst.predict(sub_trainning_data)

    y_mean = stats.describe(y).mean
    # plt.hist(y)
    # plt.show()

    pred = sub_user_index.copy()
    y_true = sub_user_index.copy()
    pred['label'] = y
    y_true['label'] = label

    pred = pred[pred['label'] >= 0.04]
    y_true = y_true[y_true['label'] == 1]

    report(pred, y_true)

if __name__ == '__main__':
    xgboost_cv()
    # xgboost_make_submission()
