import efinance as ef
import time
import os
from tqdm import tqdm


def main():
    # 第一步：获取沪深市场所有 A 股股票代码
    # 这里我们直接获取了“沪A”和“深A”两个市场的所有股票
    df_all_stocks = ef.stock.get_realtime_quotes(['沪A', '深A'])
    stock_codes = df_all_stocks['股票代码'].unique().tolist()

    print(f"共获取到 {len(stock_codes)} 只股票代码，开始逐只下载日K数据...")

    # 若不存在 data 文件夹则创建，用于存放 CSV 文件
    if not os.path.exists('data'):
        os.makedirs('data')

    # 第二步：遍历每个股票代码，获取从 2007 年至今的日 K 线数据
    for code in tqdm(stock_codes, desc="下载进度"):
        try:
            # 获取日 K 数据 (前复权)
            df_k = ef.stock.get_quote_history(
                stock_codes=code,
                beg='20070101',  # 开始日期
                end='20500101',  # 结束日期，给个足够大的年份
                klt=101,  # 101 -> 日 K
                fqt=1,  # 1 -> 前复权
                suppress_error=True  # 遇到未查到的股票代码不报错，返回空
            )
            # 如果成功获取且数据不为空，将其保存到 CSV
            if not df_k.empty:
                # 文件命名：如 600519.csv
                csv_path = os.path.join('data', f"{code}.csv")
                df_k.to_csv(csv_path, index=False, encoding='utf-8')
        except Exception as e:
            # 如果发生错误，可根据需要进行日志记录或忽略
            print(f"下载 {code} 时出现错误: {e}")

        # 第三步：暂停一段时间，避免请求过于频繁
        time.sleep(1)

    print("所有股票数据下载完成！")


if __name__ == '__main__':
    main()
