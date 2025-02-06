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

    def calc_open_price(self, close_list):
        """
        计算目标开盘价格：使得当天价格落入MA5区间的最低价格

        参数：
            close_list：列表，包含过去四天的收盘价（顺序为最早到最近）
                      （注意：此处不含当天价格x，因为x是需要计算的目标）

        计算逻辑：
            当天的5日均线（MA5）= (C1 + C2 + C3 + C4 + x) / 5.
            要使得价格 x 恰好“落入”MA5区间，我们取边界情况 x = MA5，
            则有 x = (C1 + C2 + C3 + C4 + x) / 5.
            解得：4x = C1 + C2 + C3 + C4，即 x = (C1+C2+C3+C4) / 4.

        返回：
            x 的最小值，使得当天价格刚好触及MA5。
        """
        if len(close_list) < 4:
            raise ValueError("需要至少4天的收盘价")
        sum_four = sum(close_list[:4])
        min_x = sum_four / 4.0
        return min_x

    def is_in_range(self, current_price, ma5):
        """
        判断当前价格是否位于 [ma5, ma5*(1 + tolerance)] 区间
        """
        if ma5 is None:
            return False

        lower_bound = ma5
        upper_bound = ma5 * (1 + self.tolerance)
        return lower_bound <= current_price <= upper_bound
