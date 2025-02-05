# akshare_provider.py
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

class AkshareProvider:
    """
    利用 akshare 获取股票行情、历史K线等信息的提供者。
    与原 AdataProvider 类似，对外提供相同的函数接口，用于与主程序衔接。
    """

    def __init__(self):
        pass

    def _convert_to_akshare_symbol(self, stock_code):
        """
        辅助函数：
        将纯数字形式的股票代码转换为 akshare 需要的 交易所前缀+代码 的格式:
          - '6' 开头 => 'shxxxxxx'
          - 其他 => 'szxxxxxx'
        也可自行判断北交所 '8' 开头 => 'bjxxxxxx'，或更复杂情况。
        """
        if stock_code.startswith("6"):
            return f"sh{stock_code}"
        elif stock_code.startswith("8"):
            # 北交所
            return f"bj{stock_code}"
        else:
            # 默认深市
            return f"sz{stock_code}"

    def get_history_k_data(self, stock_code, start_date=None, end_date=None):
        """
        获取单只股票的历史K线数据(日频)。返回 DataFrame。
        - stock_code: 纯数字形式的股票代码，如 '000001'、'600001'、'833xxx'
        - start_date: '2023-01-01'
        - end_date:   '2024-01-01'
        """
        # 若未指定开始结束日期，可自定义默认值
        if start_date is None:
            one_year_ago = datetime.now() - timedelta(days=365)
            start_date = one_year_ago.strftime("%Y%m%d")  # akshare 接口常用 'YYYYMMDD'
        else:
            # akshare一般需要纯数字格式 YYYYMMDD
            start_date = start_date.replace("-", "")

        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        else:
            end_date = end_date.replace("-", "")

        ak_symbol = self._convert_to_akshare_symbol(stock_code)

        # 使用 ak.stock_zh_a_hist 接口获取不复权数据：period='daily', adjust=''
        df = ak.stock_zh_a_hist(
            symbol=ak_symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust=""
        )

        if df.empty:
            return pd.DataFrame()

        # ak.stock_zh_a_hist 返回字段示例：
        #   ["日期","开盘","收盘","最高","最低","成交量","成交额","振幅","涨跌幅","涨跌额","换手率"]
        # 为了和之前 AdataProvider 保持一致，可重命名
        df.rename(
            columns={
                "日期": "trade_date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
                "成交额": "amount",
                "振幅": "amplitude",
                "涨跌幅": "change_pct",
                "涨跌额": "change",
                "换手率": "turnover_ratio",
            },
            inplace=True
        )
        # 增加 stock_code 字段，方便后续使用
        df["stock_code"] = stock_code

        # 转换日期格式为 YYYY-MM-DD
        # 有时候 akshare 返回的日期就是字符串 YYYY-MM-DD，可根据实际情况决定是否需要转换
        # df["trade_date"] = pd.to_datetime(df["trade_date"], format="%Y-%m-%d").dt.date

        # 统一字段顺序(可自定义)
        cols = [
            "stock_code", "trade_date", "open", "close", "high", "low",
            "volume", "amount", "change", "change_pct", "turnover_ratio"
        ]
        df = df[cols]

        return df

    def get_realtime_price(self, stock_code):
        """
        获取单只股票的最新价格。
        akshare 实时数据可以通过 stock_zh_a_spot_em() 拿到全市场行情，然后筛选出对应股票。
        也可以改用其他更快速的接口——示例仅演示最简做法。
        """
        # 全市场行情
        df_spot = ak.stock_zh_a_spot_em()
        # stock_zh_a_spot_em 返回字段一般包括：
        #   ["代码","名称","最新价","涨跌幅","涨跌额","成交量","成交额","振幅","最高","最低","今开","昨收","量比","换手率","市盈率-动态","市净率","总市值","流通市值","涨速","5分钟涨跌","60日涨跌幅","年初至今涨跌幅"]
        # 我们需要在 代码==stock_code 的那一行找到 "最新价"
        # 但要注意 df_spot 里的 "代码" 可能是纯数字(带不带市场?)，此处需要匹配。
        # 如果 df_spot 的 "代码" 列是 6 位数字，我们就做如下匹配：
        row = df_spot[df_spot["代码"] == stock_code]
        # 如果代码不匹配，则可能要做更多解析，比如 '000001.SZ' 之类；可根据实际需要调整

        if row.empty:
            # 未找到说明不在列表或者代码有差异
            return None

        # 取“最新价”
        current_price = float(row["最新价"].values[0])
        return current_price

if __name__ == '__main__':
    # 测试数据提供者
    provider = AkshareProvider()
    # 获取历史K线
    df = provider.get_history_k_data("000001", "2023-01-01", "2023-12-31")
    print(df.head())
    # 获取实时价格
    price = provider.get_realtime_price("000001")
    print(price)