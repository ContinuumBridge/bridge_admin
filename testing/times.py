    """
    from datetime import datetime, timedelta
    tt = datetime.fromtimestamp(t)
    today = tt.replace(hour=0, minute=0, second=0, microsecond=0)
    self.cbLog("debug", "betweenTime, today: " + str(today))
    yesterday = today - timedelta(days=1)
    tisplit - [int(t1.split(":")[0]), int(t1.split(":")[1])]
    t2split - [int(t2.split(":")[0]), int(t2.split(":")[1])]
    self.cbLog("debug", "t1split: " + str(t1split) + " t2split: " + str(t2split))
    t1s[0] = yesterday.replace(hour=t1split[0], minute=t1split[1])
    t1s[1] = today.replace(hour=t1split[0], minute=t1split[1])
    t2s[0] = yesterday.replace(hour=t2split[0], minute=t2split[1])
    t2s[1] = today.replace(hour=t2split[0], minute=t2split[1])
    self.cbLog("debug", "t1s: " + str(t1s) + " t2s: " + str(t2s))
    """
