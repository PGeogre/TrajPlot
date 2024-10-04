import os
import tkinter as tk
from tkinter import filedialog, ttk, simpledialog

import cartopy.crs as ccrs
import cartopy.feature as cf
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter
from matplotlib import rcParams
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 全局变量，用于存储选择的文件夹路径
selected_folder = ""


def select_folder():
    global selected_folder
    selected_folder = filedialog.askdirectory()
    if selected_folder:
        folder_label.config(text=f"已选择文件夹: {selected_folder}")
        results_text.delete(1.0, tk.END)  # 清空之前的结果


def track_statistics():
    global selected_folder
    if not selected_folder:
        results_text.delete(1.0, tk.END)
        results_text.insert(tk.END, "请先选择数据文件夹！")
        return

    total_files = 0
    total_size = 0
    all_dates = []
    all_lats = []
    all_lons = []
    column_ranges = {}

    for filename in os.listdir(selected_folder):
        if filename.endswith('.csv'):
            total_files += 1
            file_path = os.path.join(selected_folder, filename)
            total_size += os.path.getsize(file_path)

            # 读取 CSV 文件
            try:
                df = pd.read_csv(file_path)
                if 'date' in df.columns and 'lat' in df.columns and 'lon' in df.columns:
                    all_dates.extend(pd.to_datetime(df['date'], errors='coerce',dayfirst=True).dropna().tolist())
                    all_lats.extend(df['lat'].dropna().tolist())
                    all_lons.extend(df['lon'].dropna().tolist())

                    # 统计每列的范围
                    for column in df.columns:
                        if column not in column_ranges:
                            column_ranges[column] = {
                                'min': df[column].min() if not df[column].isnull().all() else None,
                                'max': df[column].max() if not df[column].isnull().all() else None
                            }
                        else:
                            column_ranges[column]['min'] = min(column_ranges[column]['min'], df[column].min())
                            column_ranges[column]['max'] = max(column_ranges[column]['max'], df[column].max())
                else:
                    results_text.insert(tk.END, f"文件 {filename} 缺少必要列！\n")
            except Exception as e:
                results_text.insert(tk.END, f"读取文件 {filename} 时发生错误: {e}\n")

    # 统计结果
    if total_files == 0:
        results_text.insert(tk.END, "该文件夹下没有 CSV 文件。\n")
        return

    date_range = (min(all_dates).date(), max(all_dates).date()) if all_dates else (None, None)
    lat_range = (min(all_lats), max(all_lats)) if all_lats else (None, None)
    lon_range = (min(all_lons), max(all_lons)) if all_lons else (None, None)

    result = (f"CSV 文件个数: {total_files}\n"
              f"总文件大小: {total_size / (1024 * 1024):.2f} MB\n"
              # f"时间范围: {date_range[0]} 到 {date_range[1]}\n"
              f"纬度范围: {lat_range[0]} 到 {lat_range[1]}\n"
              f"经度范围: {lon_range[0]} 到 {lon_range[1]}\n"
              f"列名及数据范围:\n")

    for column, ranges in column_ranges.items():
        result += f" - {column} : {ranges['min']} 到 {ranges['max']}\n"

    results_text.insert(tk.END, result)


def plot_tracks():
    if not selected_folder:
        results_text.delete(1.0, tk.END)
        results_text.insert(tk.END, "请先选择数据文件夹！")
        return

    # 弹出输入框获取经纬度范围
    try:
        lon1 = float(simpledialog.askstring("输入经度范围", "请输入起始经度 (lon1):"))
        lon2 = float(simpledialog.askstring("输入经度范围", "请输入结束经度 (lon2):"))
        lat1 = float(simpledialog.askstring("输入纬度范围", "请输入起始纬度 (lat1):"))
        lat2 = float(simpledialog.askstring("输入纬度范围", "请输入结束纬度 (lat2):"))
    except ValueError:
        results_text.delete(1.0, tk.END)
        results_text.insert(tk.END, "输入无效，请确保输入的是数字！\n")
        return

    # 清除之前的图像
    for widget in plot_frame.winfo_children():
        widget.destroy()

    # 设置字体
    rcParams['font.family'] = rcParams['font.sans-serif'] = 'SimHei'

    # 创建一个新的图形
    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'projection': ccrs.PlateCarree()})
    ax.set_extent([lon1, lon2, lat1, lat2], crs=ccrs.PlateCarree())
    ax.add_feature(cf.COASTLINE, lw=0.3)
    ax.add_feature(cf.LAND)
    ax.add_feature(cf.OCEAN)
    ax.add_feature(cf.RIVERS)

    # 生成颜色映射
    num_files = len([f for f in os.listdir(selected_folder) if f.endswith('.csv')])
    colors = plt.colormaps['tab10'].colors

    # 遍历文件夹中的每个 CSV 文件
    for idx, filename in enumerate(os.listdir(selected_folder)):
        if filename.endswith('.csv'):
            file_path = os.path.join(selected_folder, filename)
            try:
                df = pd.read_csv(file_path)
                sns.scatterplot(data=df, x='lon', y='lat', s=10, color=colors[idx % len(colors)], ax=ax, label=filename)
            except Exception as e:
                results_text.insert(tk.END, f"读取文件 {filename} 时发生错误: {e}\n")

    # 设置坐标轴
    ax.set_xticks(np.arange(lon1, lon2, 2))
    ax.set_yticks(np.arange(lat1, lat2, 2))
    lon_formatter = LongitudeFormatter(zero_direction_label=False)
    lat_formatter = LatitudeFormatter()
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)

    plt.title('轨迹可视化')
    plt.xlabel("经度")
    plt.ylabel('纬度')

    # 显示图例
    plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
    plt.tight_layout()

    # 保存图形到本地文件夹
    save_path = os.path.join(selected_folder, "track_visualization.png")
    plt.savefig(save_path, bbox_inches='tight')
    results_text.insert(tk.END, f"图像已保存到: {save_path}\n")

    # 将图形嵌入到 Tkinter 界面
    canvas = FigureCanvasTkAgg(fig, master=plot_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


# 创建主窗口
root = tk.Tk()
root.title("航迹绘制工具")
root.geometry("800x600")
root.configure(bg="#f0f0f0")

# 设置样式
style = ttk.Style()
style.configure('TButton', font=('Arial', 15), padding=5, background="#222222")
style.configure('TLabel', font=('Arial', 15), background="#333333", foreground="#ffffff")
style.configure('TText', font=('Arial', 12), padding=5, background="#333333", foreground="#ffffff")

# 选择文件夹部分
folder_frame = ttk.Frame(root, padding="10")
folder_frame.pack(pady=10)

folder_label = ttk.Label(folder_frame, text="请先选择文件夹")
folder_label.pack(side=tk.LEFT, padx=5)

select_button = ttk.Button(folder_frame, text="选择文件夹", command=select_folder)
select_button.pack(side=tk.LEFT)

# 功能按钮部分
button_frame = ttk.Frame(root, padding="10")
button_frame.pack(pady=10)

stat_button = ttk.Button(button_frame, text="航迹统计", command=track_statistics)
stat_button.pack(pady=5)

plot_button = ttk.Button(button_frame, text="航迹绘制", command=plot_tracks)
plot_button.pack(pady=5)

# 结果显示框
results_frame = ttk.Frame(root, padding="10")
results_frame.pack(pady=10)

results_text = tk.Text(results_frame, width=80, height=10, font=('Arial', 12))
results_text.pack()

# 绘图显示框
plot_frame = ttk.Frame(root, padding="10")
plot_frame.pack(pady=10, fill=tk.BOTH, expand=True)
fig, ax = plt.subplots(figsize=(12, 10), subplot_kw={'projection': ccrs.PlateCarree()})  # 增
# 运行主循环
root.mainloop()