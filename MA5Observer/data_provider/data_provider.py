# data_provider.py
import adata
import pandas as pd
from datetime import datetime, timedelta

class AdataProvider:
    """
    利用 adata 库获取股票行情、历史K线等信息的提供者。
    可以在此处扩展或更换数据源，只需保证对外提供的函数签名/返回格式一致。
    """

    def __init__(self):
        # 根据需要可以在这里初始化一些配置信息
        pass

    def get_history_k_data(self, stock_code, start_date=None, end_date=None):
        """
        获取单只股票的历史K线数据(日K)，并返回 DataFrame.
        - stock_code: 股票代码，如 '000001'
        - start_date: 开始日期 str，如 '2023-01-01'
        - end_date:   结束日期 str，如 '2023-12-31'
        返回的 DataFrame 至少包含字段: ['trade_date', 'open', 'close', 'high', 'low', ...]
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


if __name__ == '__main__':
    # # 测试数据提供者
    data_provider = AdataProvider()
    # 获取历史K线数据
    df = data_provider.get_history_k_data('000001')
    print(df.head())
    # 获取实时价格
    price = data_provider.get_realtime_price('000001')
    print(price)


