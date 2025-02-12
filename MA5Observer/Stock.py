
import pandas as pd

from MA5Observer.data_provider.data_provider import AdataProvider

import time


class Stock:
    def __init__(self, stock_code, data_provider, is_held=True, time_interval=60):
        self.stock_code = stock_code
        self.stock_name = data_provider.all_info[data_provider.all_info['stock_code'] == stock_code]['short_name'].iloc[
            0]
        self.data_provider = data_provider  # 注入数据提供者实例
        self.k_day = None
        self._current_price = None  # 当前实时价格
        self._ma5 = None  # 5日均线
        self.highest_price_yesterday = None  # 昨日最高价
        self.open_price_yesterday = None  # 昨日开盘价
        self.lowest_price_yesterday = None  # 昨日最低价
        self.is_held = is_held  # 是否持有该股票
        self.isOpened = False  # 是否开盘
        # 获取当前日期年月日
        self.today = pd.Timestamp.now().strftime('%Y-%m-%d')
        self.yesterday = self.data_provider.get_yesterday_trade_date()
        # 创建一个空的当日tick数据 表格 表头 ：stock_code short_name  price change change_pct     volume        amount trade_time
        self.today_tick_data = pd.DataFrame(
            columns=['stock_code', 'short_name', 'price', 'change', 'change_pct', 'volume', 'amount'])

        # 初始化股票数据
        self.initialize_stock_data()

        # 存储每个卖点的上次触发时间戳
        self.sell_signals_timestamp = {
            "highest_price_break": 0,
            "open_price_break": 0,
            "lowest_price_break": 0,
            "ma5_break": 0
        }

        # 设置时间间隔，默认 60 秒
        self.time_interval = time_interval

    def initialize_stock_data(self):
        """初始化股票的历史数据"""
        df = self.data_provider.get_history_k_data(self.stock_code)
        # 取最新的30条数据（可根据需要修改）
        df = df.tail(30).reset_index(drop=True)
        self.k_day = df

        # 获取用today昨日的收盘价、最高价、最低价和开盘价等
        self.highest_price_yesterday = df[df["trade_date"] == self.yesterday]["high"].iloc[0]
        self.open_price_yesterday = df[df["trade_date"] == self.yesterday]["open"].iloc[0]
        self.lowest_price_yesterday = df[df["trade_date"] == self.yesterday]["low"].iloc[0]

        # 初始化5日均线
        close_prices = df["close"].tolist()
        if len(close_prices) >= 5:
            self._ma5 = sum(close_prices[-5:]) / 5

    @property
    def ma5(self):
        """获取5日均线"""
        return self._ma5

    @ma5.setter
    def ma5(self, value):
        """更新5日均线并同步更新历史数据"""
        self._ma5 = value
        close_prices = self.k_day["close"].tolist()
        # 更新最后一条数据的close（即今天的收盘价）
        if self.today in self.k_day['trade_date'].values:
            self.k_day.loc[self.k_day['trade_date'] == self.today, 'close'] = value
        else:
            # 如果今天没有数据，添加今天的收盘价
            self.k_day = self.k_day.append({'trade_date': self.today, 'close': value}, ignore_index=True)

        # 重新计算5日均线
        close_prices.append(value)  # 加入今天的价格
        if len(close_prices) >= 5:
            self._ma5 = sum(close_prices[-5:]) / 5

    def update_current(self, real_time_data):
        """更新当前行情 stock_code short_name price change change_pct volume amount"""
        if self.today_tick_data.empty:
            real_time_data['trade_time'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
            self.today_tick_data = self.today_tick_data.append(real_time_data, ignore_index=True)
        else:
            latest_data = self.today_tick_data.iloc[-1]
            # 去掉trade_time列后与real_time_data比较若不同则更新
            if latest_data.drop('trade_time').equals(real_time_data):
                return
            else:
                real_time_data['trade_time'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                self.today_tick_data = self.today_tick_data.append(real_time_data, ignore_index=True)

        # 更新当前价格
        self._current_price = real_time_data['price']
        # 更新 ma5
        self.ma5 = self._current_price  # 当价格更新时，也自动更新 ma5

    def check_sell_conditions(self):
        """检查卖点条件"""
        if self._current_price is None or self._ma5 is None:
            return False, "价格或5日均线数据不足"

        # 获取昨日的最高价、开盘价、最低价
        if self.highest_price_yesterday is None or self.open_price_yesterday is None or self.lowest_price_yesterday is None:
            return False, "昨日数据不足"

        current_time = time.time()  # 获取当前时间戳（秒）

        # 卖点1: 突破上一日最高价后回落卖出
        if self._current_price > self.highest_price_yesterday:
            if current_time - self.sell_signals_timestamp["highest_price_break"] > self.time_interval:
                self.sell_signals_timestamp["highest_price_break"] = current_time
                return True, "突破上一日最高价"

        # 卖点2: 突破上一日开盘价后回落卖出
        if self._current_price > self.open_price_yesterday:
            if current_time - self.sell_signals_timestamp["open_price_break"] > self.time_interval:
                self.sell_signals_timestamp["open_price_break"] = current_time
                return True, "突破上一日开盘价"

        # 卖点5: 开盘价跌破上一日最低价，同时跌破5日均线，坚决卖出
        if self._current_price < self.lowest_price_yesterday and self._current_price < self._ma5:
            if current_time - self.sell_signals_timestamp["lowest_price_break"] > self.time_interval:
                self.sell_signals_timestamp["lowest_price_break"] = current_time
                return True, "开盘价跌破上一日最低价，同时跌破5日均线，坚决卖出"

        # 卖点6: 盘中跌破5日均线，同时跌破上一日最低价，坚决卖出
        if self._current_price < self._ma5 and self._current_price < self.lowest_price_yesterday:
            if current_time - self.sell_signals_timestamp["ma5_break"] > self.time_interval:
                self.sell_signals_timestamp["ma5_break"] = current_time
                return True, "盘中跌破5日均线，同时跌破上一日最低价，坚决卖出"

        return False, "未满足卖出条件"


if __name__ == '__main__':
    #测试Stock类
    # 初始化数据提供者
    data_provider = AdataProvider()
    # 初始化股票实例
    stock = Stock('000001', data_provider)

