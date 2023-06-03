from datetime import datetime, timedelta

from bot.config import conf, mongo_client

statistic = mongo_client.tasks.statistic


def get_now_statistic():
    now = datetime.now()
    res, repets = None, -1

    while not res and repets < 25:
        repets += 1

        res = statistic.find_one({'date': str(now.date())})
        if not res: now -= timedelta(days=1.0)

    return res