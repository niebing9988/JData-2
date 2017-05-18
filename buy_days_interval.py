import numpy as np
import pandas as pd
from datetime import datetime

def buy_days_interval(date):

    # change the type from date to string
    if type(date) == datetime:
        dateStr = date.strftime('%Y-%m-%d')
    else:
        dateStr = date
        date = datetime.strptime(date, '%Y-%m-%d')

    # read user purchase action file
    actions2 = pd.read_csv('./data/actions2.csv')
    actions3 = pd.read_csv('./data/actions3.csv')
    actions4 = pd.read_csv('./data/actions4.csv')

    # cancat three csv file
    actions = pd.concat([actions2, actions3, actions4], ignore_index=True)

    # get the user_id and purchase time
    actions = actions[['user_id', 'time', 'type']]
    # backup the data
    actionsBk = pd.DataFrame(actions)

    # get the actions whose type is 4
    actions = actions[actions['type']==4]

    # reset the index and remove the column type
    actions = actions[['user_id', 'time']].reset_index(drop=True)

    # set the userList record who have purchase action before the date
    userList = list()

    index = 0
    # get the user who have purchased before the date
    for time in actions['time']:
        if time >= dateStr:
            break
        userList.append([actions['user_id'][index], time])
        index = index + 1

    # reverse the userList
    userList = userList[::-1]

    resultList = list()

    # get the result from the userList
    for user,time in userList:
        if user in [x[0] for x in resultList]:
            continue
        resultList.append([user, (date-datetime.strptime(time, '%Y-%m-%d %H:%M:%S')).days])

    for user in actionsBk['user_id']:
        if user in [x[0] for x in resultList]:
            continue
        resultList.append([user, -1])

    # set the result with type DataFrame
    result = pd.DataFrame(resultList, columns=['user_id', 'buy_days_interval'])

    return result

if __name__ == '__main__':
    buy_days_interval(date)
    # buy_days_interval('2016-02-05')
