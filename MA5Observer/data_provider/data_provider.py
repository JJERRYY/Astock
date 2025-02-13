# data_provider.py
import adata
import pandas as pd
from datetime import datetime, timedelta, time as dtime

class AdataProvider:
    """
    利用 adata 库获取股票行情、历史K线等信息的提供者。
    可以在此处扩展或更换数据源，只需保证对外提供的函数签名/返回格式一致。
    """

    def __init__(self):
        self.all_info = self.get_all_code_info()

        pass

    def get_history_k_data(self, stock_code, start_date=None, end_date=None):
        """
        获取单只股票的历史K线数据(日K)，并返回 DataFrame.
        - stock_code: 股票代码，如 '000001'
        - start_date: 开始日期 str，如 '2023-01-01'
        - end_date:   结束日期 str，如 '2023-12-31'
        返回的 DataFrame 至少包含字段: ['trade_date', 'open', 'close', 'high', 'low', ...]
        #### 返回结果
| 字段           | 类型    | 说明           |
|----------------|---------|----------------|
| stock_code     | string  | 股票代码       |
| trade_time     | time    | 交易时间       |
| trade_date     | date    | 交易日期       |
| open           | decimal | 开盘价(元)     |
| close          | decimal | 收盘价(元)     |
| high           | decimal | 最高价(元)     |
| low            | decimal | 最低价(元)     |
| volume         | decimal | 成交量(股)     |
| amount         | decimal | 成交额(元)     |
| change         | decimal | 涨跌额(元)     |
| change_pct     | decimal | 涨跌幅(%)      |
| turnover_ratio | decimal | 换手率(%)      |
| pre_close      | decimal | 昨收(元)       |

        """
        if start_date is None:
            # 默认回溯一段时间，比如1年
            one_year_ago = datetime.now() - timedelta(days=365)
            start_date = one_year_ago.strftime("%Y-%m-%d")

        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        df = adata.stock.market.get_market(
            stock_code=stock_code,
            start_date=start_date,
            end_date=end_date,
            k_type=1,         # 1=日K线
            adjust_type=1     # 1=前复权
        )
        return df

    def get_realtime_price(self, stock_code):
        """
        获取单只股票的最新价格（可以从实时行情接口获取）。
        如果需要五档行情、分时行情等，可在这里扩展。
        """
        # 这里调用多只股票实时行情的接口，传入单只也OK
        df = adata.stock.market.list_market_current(code_list=[stock_code])
        # 返回DataFrame格式:
        # ['stock_code','short_name','price','change','change_pct','volume','amount']
        if df.empty:
            return None
        current_price = float(df.loc[0, 'price'])
        stock_name = df.loc[0, 'short_name']
        return current_price, stock_name
    # 获取股票的实时行情
    def get_realtime(self, stock_code):
        """
        获取股票或列表的实时行情
        # 结果示例
  stock_code short_name  price change change_pct     volume        amount
0     000001       平安银行  11.34  -0.06      -0.53   42348200   479720000.0
1     000795        英洛华   8.10   0.53       7.00  140166000  1098610000.0
2     872925       锦好医疗  9.530  0.000      0.000     318846   3008578.290
        :param stock_code:
        :return:
        """
        return adata.stock.market.list_market_current(code_list=stock_code)

    def get_trade_calendar(self, year=2025):
        """
        获取指定年份的交易日历
        """
        return adata.stock.info.trade_calendar(year=year)

    def get_yesterday_trade_date(self):
        """
        收盘后，今日即为昨日
        获取上一个的交易日期
        """
        today = pd.Timestamp.now().strftime('%Y-%m-%d')
        trade_calendar = self.get_trade_calendar()
        # 判断当天是否是交易日，时间为15:00之后
        if trade_calendar.loc[trade_calendar['trade_date'] == today, 'trade_status'].values[0] == 1 and  pd.Timestamp.now().hour >= 15:
            return today
        # 如果不是交易日，或者是交易日但时间小于15:00
        else:
            # 获取比今天小的交易日历中trade_status==1 的第一个作为昨天的日期
            # 先筛选出比今天小的日期，再筛选出trade_status==1的日期，再取第一个
            yesterday = trade_calendar[trade_calendar['trade_date'] < today]
            yesterday = yesterday[yesterday['trade_status'] == 1]
            yesterday = yesterday['trade_date'].iloc[-1]
            return yesterday
    def get_all_code_info(self):
        """
        获取所有股票代码信息
        # 结果示例
     stock_code short_name exchange   list_date
0        000001       平安银行       SZ  1991-04-03
1        000002      万  科Ａ       SZ  1991-01-29
2        000003      PT金田A       SZ         NaN
...         ...        ...      ...         ...
5637     900955       退市海B       SH         NaN
5638     900956       东贝B股       SH         NaN
5639     900957       凌云Ｂ股       SH  2000-07-28
        """

        return adata.stock.info.all_code()

    def is_market_open(self,):
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

        return True

if __name__ == '__main__':
    # # 测试数据提供者
    data_provider = AdataProvider()
    # 获取历史K线数据
    df = data_provider.get_history_k_data('000001')
    print(df.head())
    # 获取实时价格
    price = data_provider.get_realtime_price('000001')
    print(price)
    # 测试获取昨日交易日期
    yesterday = data_provider.get_yesterday_trade_date()

