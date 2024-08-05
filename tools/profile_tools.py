from datetime import datetime
def market_open():
    today = datetime.now()  
    eastern = pytz.timezone('US/Eastern')
    current_time_et = datetime.now(eastern).time()
    market_open = datetime.strptime("09:30", "%H:%M").time()
    market_close = datetime.strptime("16:00", "%H:%M").time()
    return market_open <= current_time_et <= market_close and today.weekday() < 5 and today not in holidays.US() 
