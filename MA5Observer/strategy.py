# strategy.py
import numpy as np

class PriceRangeStrategy:
    """
    简单策略示例：判断股票价格是否在 [MA5, MA5 * 1.02] 区间内
    """
    def __init__(self, tolerance=0.02):
        """
        :param tolerance: 对应 5日线 * (1 + tolerance)，默认0.02 (2%)
        """
        self.tolerance = tolerance

    def calc_ma5(self, close_list):
        """
        计算MA5。传入最近5个收盘价(或其中包含最新1个实时价)的列表
        """
        if len(close_list) < 5:
            # 如果数据不足5条，这里简单返回None
            return None
        return np.mean(close_list)

    def is_in_range(self, current_price, ma5):
        """
        判断当前价格是否位于 [ma5, ma5*(1 + tolerance)] 区间
        """
        if ma5 is None:
            return False

        lower_bound = ma5
        upper_bound = ma5 * (1 + self.tolerance)
        return lower_bound <= current_price <= upper_bound
