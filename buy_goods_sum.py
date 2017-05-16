import numpy as np
import pandas as pd
import os

def buy_goods_sum():

    # read user purchase action file
    actions_path = './data/actions2.csv'
    actions = pd.read_csv(actions_path, encoding='gbk')

    # get the columns user_id and type 
    actions = actions[['user_id', 'type']]

    # get the actions whose type is 4
    index = 0
    for tp in actions['type']:
        if tp != 4:
            actions = actions.drop(index)
        index = index + 1

    # the list put the reulst value
    resultList = list()

    index = 0
    # get the user buy goods sum
    for user in actions['user_id']:
        # if user is already in the result list, skip it
        if user in [x[0] for x in resultList]:
            continue
        goodsSum = 0
        # adds as a goods sum if user_id is same
        for i in actions['user_id'][index:]:
            if i == user:
                goodsSum = goodsSum + 1
               
        resultList.append([user, goodsSum])
        index = index + 1

    # get the result with DataFrame type 
    result = pd.DataFrame(resultList, columns=['user_id', 'buy_goods_sum'])
    return result

if __name__ == '__main__':
    buy_goods_sum()
