import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from scipy.optimize import curve_fit

def log_power_function(x, a, b):
    """定义对数函数: y = log(a * x^b)，用于拟合留存率"""
    return np.log(a * np.power(x, b))

def fit_revenue_parameters(days, retention_rates):
    """拟合留存率衰减参数"""
    # 将留存率转换为对数形式
    log_retention_rates = np.log(retention_rates)
    
    # 使用curve_fit进行拟合
    popt, _ = curve_fit(log_power_function, days, log_retention_rates)
    return popt

def create_revenue_df(active_users, start_date, end_date, yearly_params):
    """
    创建收入DataFrame
    yearly_params: 字典，key为年份，value为(day1, day7, day30)留存率元组
    """
    # 创建日期范围
    dates = pd.date_range(start=start_date, end=end_date)
    
    # 为每年拟合衰减参数
    year_params = {}
    for year, retention_rates in yearly_params.items():
        days = np.array([1, 7, 30])
        a, b = fit_revenue_parameters(days, np.array(retention_rates))
        year_params[year] = (a, b)
    
    # 创建基础数据
    data = {'激活人数': [active_users] * len(dates)}
    base_revenue = 1000  # 设置day0基础收入
    
    # 计算最大需要的天数
    max_days = (pd.Timestamp(end_date) - pd.Timestamp(start_date)).days + 1
    
    # 为每一天创建收入列
    for day in range(max_days):
        col_name = f'day{day}收入'
        revenues = []
        for idx, date in enumerate(dates):
            if idx + day < len(dates):
                # 确定使用哪一年的衰减参数
                activation_date = date
                revenue_date = date + pd.Timedelta(days=day)
                year = activation_date.year
                
                if day == 0:
                    revenues.append(base_revenue)  # day0收入
                else:
                    a, b = year_params[year]
                    # 计算留存率，然后乘以基础收入
                    retention_rate = np.exp(log_power_function(day, a, b))
                    revenue = base_revenue * retention_rate
                    revenues.append(revenue)
            else:
                revenues.append(None)
        data[col_name] = revenues
    
    # 创建DataFrame
    df = pd.DataFrame(data, index=dates)
    df.index.name = '激活日期'
    
    return df

def calculate_yearly_rpd(df, start_year, end_year):
    """计算每年的RPD和增长率（累计方式）"""
    results = {}
    
    for year in range(start_year, end_year + 1):
        # 计算到当前年份为止的累计用户数
        mask_cumulative = df.index.year <= year
        users_cumulative = df[mask_cumulative]['激活人数'].sum()
        
        # 计算到当前年份为止的累计收入
        revenue_cumulative = 0
        for idx, row in df[mask_cumulative].iterrows():
            # 计算从激活日到当前年份年末的收入
            days_until_year_end = (pd.Timestamp(f'{year}-12-31') - idx).days
            revenue_cols = [f'day{i}收入' for i in range(0, days_until_year_end + 1)]
            revenue_cumulative += row[revenue_cols].sum()
        
        # 计算累计RPD
        rpd_year = revenue_cumulative / users_cumulative
        results[year] = {'RPD': rpd_year}
        
        # 计算增长率（除第一年外）
        if year > start_year:
            growth_rate = (rpd_year / results[year-1]['RPD'] - 1) * 100
            results[year]['Growth_Rate'] = growth_rate
    
    return results

# 主程序
# def main():
#     # 获取基本信息
#     start_date = input("请输入产品上线日期 (YYYY-MM-DD): ")
#     end_date = '2024-12-31'
#     active_users = 1000  # 固定每日激活人数为1000
    
#     # 获取年份范围
#     start_year = pd.Timestamp(start_date).year
#     end_year = pd.Timestamp(end_date).year
    
#     # 收集每年的收入数据
#     yearly_params = {}
#     for year in range(start_year, end_year + 1):
#         print(f"\n请输入{year}年的收入数据：")
#         day1 = float(input(f"{year}年 day1收入: "))
#         day7 = float(input(f"{year}年 day7收入: "))
#         day30 = float(input(f"{year}年 day30收入: "))
#         yearly_params[year] = (day1, day7, day30)
    
#     # 创建收入DataFrame
#     df = create_revenue_df(active_users, start_date, end_date, yearly_params)
    
#     # 保存详细数据到Excel
#     df.to_excel('revenue_detail.xlsx')
    
#     # 计算每年的RPD和增长率
#     results = calculate_yearly_rpd(df, start_year, end_year)
    
#     # 打印结果
#     print("\n年度RPD统计：")
#     for year, data in results.items():
#         print(f"\n{year}年:")
#         print(f"RPD: {data['RPD']:.2f}")
#         if 'Growth_Rate' in data:
#             print(f"增长率: {data['Growth_Rate']:.2f}%")
    
#     # 打印基本信息
#     print("\n基本信息：")
#     for year in range(start_year, end_year + 1):
#         year_users = len(df[df.index.year == year]) * active_users
#         print(f"{year}年总激活用户数: {year_users:,}")

if __name__ == "__main__":
    # main()
    print("请通过streamlit界面运行此程序")