#main.py
import sys
import threading
import time
from datetime import datetime, time as dtime, timedelta

from loguru import logger
import pandas as pd
import sys
# 获取父目录,绝对路径
sys.path.append("..")
from MA5Observer.Stock import Stock
from data_provider.data_provider import AdataProvider
from strategy import PriceRangeStrategy
from notifier import Notifier
import adata


def read_observed_stocks(filepath="observe.txt"):
    # 使用 set 去重
    stock_set = set()
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            code = line.strip()
            if code:
                stock_set.add(code)  # 将股票代码添加到 set 中
    return list(stock_set)  # 转换为列表并返回


def read_holding_stocks(filepath="holding.txt"):
    holding_list = []
    holding_codes = []

    data_provider = AdataProvider()
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            code = line.strip()
            if code:
                # stock_name = "SomeStockName"  # 你可以通过股票代码获取股票名称
                holding_list.append(Stock(stock_code=code,data_provider=data_provider,is_held=True))
                holding_codes.append(code)
    return holding_list, holding_codes

def is_market_open():
    """
    判断是否在交易时段内(包括盘前竞价)
    """
    now = datetime.now()
    current_time = now.time()

    morning_open = dtime(9, 30)
    morning_close = dtime(11, 30)
    afternoon_open = dtime(13, 0)
    afternoon_close = dtime(15, 0)
    pre_market_open = dtime(9, 15)  # 盘前竞价开始时间

    # 获取当前年份的交易日历
    year = now.year
    trade_calendar = adata.stock.info.trade_calendar(year=year)
    trade_dates = trade_calendar['trade_date'].astype(str).tolist()

    # 当前日期
    current_date = now.strftime("%Y-%m-%d")

    # 如果当前日期不是交易日，返回 False
    if current_date not in trade_dates:
        return False

    # 盘前竞价
    if pre_market_open <= current_time <= morning_open:
        return True
    # 上午时段
    if morning_open <= current_time <= morning_close:
        return True
    # 下午时段
    if afternoon_open <= current_time <= afternoon_close:
        return True
    # 在盘前竞价和交易时段内
    if pre_market_open <= current_time <= afternoon_close:
        return True

    return False


def main():
    observe_codes = read_observed_stocks("observe.txt")
    holding_stocks,holding_codes  = read_holding_stocks("holding.txt")

    data_provider = AdataProvider()
    strategy = PriceRangeStrategy(tolerance=0.03)
    notifier = Notifier()

    historical_data_dict = {}
    last_alert_time = {}  # 用于记录最后提醒的时间

    # Set up logging
    logger.remove()  # Remove the default logger
    logger.add("app.log", rotation="1 week", level="DEBUG", retention="10 days")  # Log to file
    logger.add(sys.stdout, level="INFO")  # Print log to stdout for important info

    # 获取今天的日期，再获取今天日期往前4天的交易日期
    today = datetime.now().strftime("%Y-%m-%d")
    trade_calendar = adata.stock.info.trade_calendar(year=int(today[:4]))
    # 只取交易日的日期'trade_status'==1
    trade_dates = trade_calendar[trade_calendar["trade_status"] == 1]["trade_date"].astype(str).tolist()
    today_index = trade_dates.index(today)
    last_4_trade_dates = trade_dates[today_index - 4:today_index]


    for code in observe_codes:
        df = data_provider.get_history_k_data(code)
        df = df.tail(30).reset_index(drop=True)

        df = df.sort_values("trade_date")
        last_4_close = df[df["trade_date"].isin(last_4_trade_dates)]["close"].tolist()

        historical_data_dict[code] = last_4_close

    logger.info("历史数据准备完毕。开始进入观察模式...")

    try:
        while True:
            if is_market_open():
                # #卖点监控
                # holding_df = data_provider.get_realtime(holding_codes)
                # for stock in holding_stocks:  # 遍历持仓股进行卖点监控
                #     stock.update_current(holding_df[holding_df["stock_code"] == stock.stock_code])
                #     # current_price = stock.current_price
                #     sell_flag,sell_msg =  stock.check_sell_conditions()
                #     # 检查卖点条件
                #     if sell_flag:
                #         # 卖出提醒
                #         logger.info(
                #             f"[SELL ALERT] {stock.stock_code} {stock.stock_name} 满足卖点条件, 当前价格: {current_price}, 卖出信号{sell_msg}")
                #         msg_title = f"股票 {stock.stock_name} 卖出提醒"
                #         msg_body = f"当前价: {current_price:.2f}, 卖出信号: {sell_msg}"
                #         threading.Thread(
                #             target=notifier.send_notification,
                #             args=(msg_title, msg_body)
                #         ).start()


                # 买点监控
                for code in observe_codes:
                    current_price, stock_name = data_provider.get_realtime_price(code)
                    if current_price is None:
                        continue

                    last_4_close = historical_data_dict[code]
                    data_for_ma5 = last_4_close + [current_price]

                    if len(data_for_ma5) < 5:
                        continue

                    ma5 = strategy.calc_ma5(data_for_ma5)
                    if strategy.is_in_range(current_price, ma5):
                        # 检查是否是5分钟内的重复提醒
                        current_time = datetime.now()
                        if code not in last_alert_time or (current_time - last_alert_time[code]).seconds > 10:
                            logger.info(f"[ALERT] {code} {stock_name} 价格 {current_price:.2f} 已进入区间 [{ma5:.2f}, {ma5 * 1.02:.2f}]")
                            msg_title = f"股票 {stock_name} 触发策略"
                            msg_body = f"当前价: {current_price:.2f}, MA5区间: [{ma5:.2f}, {ma5 * 1.02:.2f}]"
                            # logger.info(f"[ALERT] {msg_title} - {msg_body}")
                            threading.Thread(
                                target=notifier.send_notification,
                                args=(msg_title, msg_body)
                            ).start()
                            last_alert_time[code] = current_time  # 更新最后提醒时间
                    else:
                        # 如果价格走出区间，移除提醒记录
                        if code in last_alert_time:
                            del last_alert_time[code]

                    logger.debug(f"{datetime.now()} - {code} current: {current_price:.2f} - MA5: {ma5:.2f}")

                time.sleep(1)
            else:
                # 非交易时间，计算最近5天的MA5
                logger.info("现在不在交易时段，等待中...")
                for code in observe_codes:
                    # 获取过去5天的历史数据进行MA5计算
                    df = data_provider.get_history_k_data(code)

                    df = df.tail(5).reset_index(drop=True)
                    df = df.sort_values("trade_date")
                    close_list = df["close"].tolist()

                    if len(close_list) >= 5:
                        ma5 = strategy.calc_ma5(close_list)

                        # 截取传入最近4天的收盘价，计算开盘价目标区间
                        open_price = strategy.calc_open_price(close_list[:-1])
                        logger.info(f"{code} - 非交易时间计算 MA5: {ma5:.2f} - 开盘价大于MA5的最低价格: {open_price:.2f}")
                    else:
                        logger.warning(f"{code} - 数据不足，无法计算MA5")
                # 输出持仓股的今天最低价、最高价、开盘价、5日均线
                for stock in holding_stocks:
                    stock.update_current(data_provider.get_realtime(stock.stock_code))
                    # 获取stock.k_day,再用昨日时间筛选获取昨日k线数据,来获取昨日最高价、最低价、开盘价
                    yesterday_data = stock.k_day[stock.k_day["trade_date"] == stock.yesterday].iloc[0]
                    highest_price_yesterday = yesterday_data["high"]
                    open_price_yesterday = yesterday_data["open"]
                    lowest_price_yesterday = yesterday_data["low"]
                    logger.info(
                        f"{stock.stock_code} {stock.stock_name} 昨日最高价: {highest_price_yesterday:.2f}, 昨日最低价: {lowest_price_yesterday:.2f}, 昨日开盘价: {open_price_yesterday:.2f}, 5日均线: {stock.ma5:.2f}")

                # 根据交易时间判断到下一次交易日需要睡眠的大概时间，等待到下一个交易时间段
                now = datetime.now()
                current_time = now.time()
                morning_open = dtime(9, 30)
                afternoon_open = dtime(13, 0)
                if current_time < morning_open:
                    next_trade_time = datetime(now.year, now.month, now.day, 9, 30)
                elif current_time < afternoon_open:
                    next_trade_time = datetime(now.year, now.month, now.day, 13, 0)
                else:
                    next_trade_time = datetime(now.year, now.month, now.day, 9, 30) + timedelta(days=1)
                sleep_seconds = (next_trade_time - now).seconds
                logger.info(f"等待到下一个交易时间段，大约需要睡眠 {sleep_seconds} 秒")
                time.sleep(sleep_seconds-1)

    except KeyboardInterrupt:
        logger.info("\n手动结束观察。")


if __name__ == "__main__":
    main()
