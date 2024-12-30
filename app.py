import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from RPD import create_revenue_df, calculate_yearly_rpd, log_power_function, fit_revenue_parameters

from datetime import datetime
import numpy as np

def plot_retention_decay(yearly_params, year_params, start_year):
    """绘制金额留存率衰减曲线"""
    fig = go.Figure()
    
    # 生成x轴数据点（1-720天）
    days = np.linspace(1, 1110)
    
    # 为每年添加一条曲线
    for i, year in enumerate(yearly_params.keys(), 1):
        a, b = year_params[year]
        # 直接计算留存率
        retention_rates = np.exp(log_power_function(days, a, b))
        
        # 将留存率转换为百分比
        retention_rates_percent = retention_rates * 100
        
        fig.add_trace(go.Scatter(
            x=days,
            y=retention_rates_percent,
            name=f'{year}年（第{i}年）',
            mode='lines',
            line=dict(width=2)
        ))

    fig.update_layout(
        title='金额留存率衰减曲线',
        xaxis_title='激活后天数',
        yaxis_title='金额留存率(%)',
        height=500,
        showlegend=True
    )
    
    return fig

def main():
    st.title('收入预测分析工具')
    
    # 侧边栏：基础设置
    with st.sidebar:
        st.header('基本参数设置')
        start_date = st.date_input(
            "产品上线日期",
            min_value=datetime(2000, 1, 1),
            max_value=datetime(2024, 12, 31),
            value=datetime(2024, 1, 1)
        )
        end_date = datetime(2024, 12, 31)
        active_users = st.number_input('每日激活用户数', value=1000, min_value=1)

    # 主界面：年度收入数据输入
    st.header('年度金额留存率输入')
    
    start_year = start_date.year
    end_year = end_date.year
    yearly_params = {}
    
    # 计算每年是产品上线后的第几年
    for i, year in enumerate(range(start_year, end_year + 1), 1):
        st.subheader(f'{year}年（产品上线第{i}年）')
        col1, col2, col3 = st.columns(3)
        with col1:
            day1_rate = st.number_input(
                f'Day1留存率(%)', 
                value=80.0, 
                min_value=0.0, 
                max_value=1000.0,
                key=f'day1_{year}'
            )
        with col2:
            day7_rate = st.number_input(
                f'Day7留存率(%)', 
                value=40.0, 
                min_value=0.0, 
                max_value=1000.0,
                key=f'day7_{year}'
            )
        with col3:
            day30_rate = st.number_input(
                f'Day30留存率(%)', 
                value=20.0, 
                min_value=0.0, 
                max_value=1000.0,
                key=f'day30_{year}'
            )
        
        yearly_params[year] = (day1_rate/100, day7_rate/100, day30_rate/100)

    # 计算按
    if st.button('开始计算'):
        # 创建收入DataFrame
        df = create_revenue_df(active_users, start_date, end_date, yearly_params)
        
        # 计算RPD和增长率
        results = calculate_yearly_rpd(df, start_year, end_year)
        
        # 显示结果
        st.header('计算结果')
        
        # RPD结果表格
        rpd_data = []
        for i, (year, data) in enumerate(results.items(), 1):
            row = {
                '年份': f'{year}年（产品上线第{i}年）',
                'RPD': f"{data['RPD']:.2f}",
                '增长率': f"{data.get('Growth_Rate', '-'):.2f}%" if 'Growth_Rate' in data else '-'
            }
            rpd_data.append(row)
        
        st.subheader('年度RPD统计')
        st.table(pd.DataFrame(rpd_data))
        
        # 获取拟合参数
        year_params = {}
        for year, revenues in yearly_params.items():
            days = np.array([1, 7, 30])
            a, b = fit_revenue_parameters(days, np.array(revenues))
            year_params[year] = (a, b)
        
        # 显示金额留存率衰减曲线
        st.subheader('金额留存率衰减曲线')
        fig = plot_retention_decay(yearly_params, year_params, start_year)
        st.plotly_chart(fig, use_container_width=True)
        
        # 提供下载详细数据的功能
        st.download_button(
            label="下载详细数据",
            data=df.to_csv().encode('utf-8'),
            file_name='revenue_detail.csv',
            mime='text/csv'
        )

if __name__ == '__main__':
    main()
