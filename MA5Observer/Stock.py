
import pandas as pd

from MA5Observer.data_provider.data_provider import AdataProvider


class Stock:
    def __init__(self, stock_code, data_provider,is_held=True):
        self.stock_code = stock_code
        self.stock_name = data_provider.all_info[data_provider.all_info['stock_code'] == stock_code]['short_name'].iloc[0]
        self.data_provider = data_provider  # 注入数据提供者实例
        self.history_data = []  # 存储历史数据，如上一日的价格
        self.current_price = None  # 当前实时价格
        self.ma5 = None  # 5日均线
        self.highest_price_yesterday = None  # 昨日最高价
        self.open_price_yesterday = None  # 昨日开盘价
        self.lowest_price_yesterday = None  # 昨日最低价
        self.is_held = is_held  # 是否持有该股票
        # 获取当前日期年月日
        self.today  = pd.Timestamp.now().strftime('%Y-%m-%d')
        self.yesterday = self.data_provider.get_yesterday_trade_date()
        self.today_tick_data = []  # 存储当日tick数据


        # 初始化股票数据
        self.initialize_stock_data()

    def initialize_stock_data(self):
        """初始化股票的历史数据"""
        df = self.data_provider.get_history_k_data(self.stock_code)
        # 取最新的30条数据（可根据需要修改）
        df = df.tail(30).reset_index(drop=True)
        self.history_data = df

        # 获取用today昨日的收盘价、最高价、最低价和开盘价等
        self.highest_price_yesterday = df[df["trade_date"] == self.yesterday]["high"].iloc[0]
        self.open_price_yesterday = df[df["trade_date"] == self.yesterday]["open"].iloc[0]
        self.lowest_price_yesterday = df[df["trade_date"] == self.yesterday]["low"].iloc[0]


        # 初始化5日均线
        close_prices = df["close"].tolist()
        if len(close_prices) >= 5:
            self.ma5 = sum(close_prices[-5:]) / 5



    def update_current_price(self, current_price):
        """更新当前价格"""
        self.current_price = current_price
        # 重新计算实时5日均线
        # 添加今天价格作为今天日期的收盘价
        # 先找今天有无数据
        if self.today in self.history_data['trade_date'].values:
            self.history_data.loc[self.history_data['trade_date'] == self.today, 'close'] = current_price
        else:
            # 今天无数据，添加今天数据
            self.history_data = self.history_data.append({'trade_date': self.today, 'close': current_price}, ignore_index=True)

        # 重新计算5日均线
        close_prices = self.history_data["close"].tolist()
        if len(close_prices) >= 5:
            self.ma5 = sum(close_prices[-5:]) / 5




    def check_sell_conditions(self):
        """检查卖点条件"""
        if self.current_price is None or self.ma5 is None:
            return False, "价格或5日均线数据不足"

        # 卖点1: 突破上一日最高价后回落卖出
        if self.current_price > self.highest_price_yesterday and self.current_price < self.history_data[-1]:
            return True, "突破上一日最高价后回落卖出"

        # 卖点2: 突破上一日开盘价后回落卖出
        if self.current_price > self.open_price_yesterday and self.current_price < self.history_data[-1]:
            return True, "突破上一日开盘价后回落卖出"

        # 卖点3: 突破零轴后回落卖出
        if self.current_price < 0 and self.history_data[-1] > 0:
            return True,

        # 卖点4: 冲高被5日均线压制后回落卖出
        if self.current_price > self.ma5 and self.history_data[-1] < self.ma5:
            return True

        # 卖点5: 开盘价跌破上一日最低价，同时跌破5日均线，坚决卖出
        if self.current_price < self.lowest_price_yesterday and self.current_price < self.ma5:
            return True , "开盘价跌破上一日最低价，同时跌破5日均线，坚决卖出"

        # 卖点6: 盘中跌破5日均线，同时跌破上一日最低价，坚决卖出
        if self.current_price < self.ma5 and self.current_price < self.lowest_price_yesterday:
            return True, "盘中跌破5日均线，同时跌破上一日最低价，坚决卖出"

        return False

if __name__ == '__main__':
    #测试Stock类
    # 初始化数据提供者
    data_provider = AdataProvider()
    # 初始化股票实例
    stock = Stock('000001', data_provider)

