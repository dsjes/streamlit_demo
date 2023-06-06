import streamlit as st
import datetime
import pandas as pd
import streamlit.components.v1 as components
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']
import app_functions
import plotly.express as px
from datetime import timedelta
import plotly.graph_objects as go
import pymysql
import time
from dateutil.relativedelta import relativedelta
# import openai

# read data
@st.cache_data
def read_data(path):
    data = pd.read_csv(path)
    return data
df_dcard = read_data("dcard_demo_data.csv")
df_gmap = read_data("gmap_demo_data.csv")
df_ptt = read_data("ptt_demo_data.csv")
df_經緯度 = pd.read_csv("gmap店點經緯度.csv")
df_gmap = pd.merge(df_gmap,df_經緯度,on = 'name')
df_gmap["lon"] = [i.split('@')[1].split(",")[1] for i in df_gmap['url']]
df_gmap["lat"] = [i.split('@')[1].split(",")[0] for i in df_gmap['url']]

# dataframe 資料處理
df_gmap["name"] = ["菁英" if "Elite" in i else i for i in df_gmap["name"]]
df_gmap["Preds"] = [i.replace("面","向") for i in df_gmap["Preds"]]
df_gmap["評論數"] = 1

app_functions.drop_unnamed_column(df_dcard) ; app_functions.drop_unnamed_column(df_gmap) ; app_functions.drop_unnamed_column(df_ptt)
df_dcard = app_functions.replace_無(df_dcard) ; df_ptt = app_functions.replace_無(df_ptt)
app_functions.change_column_type(df_dcard,"created_at_日期") ; app_functions.change_column_type(df_ptt,"created_at_日期") ; app_functions.change_column_type(df_gmap,"review_time_日期")
df_dcard["聲量"] = 1 ; df_gmap["聲量"] = 1 ;df_ptt["聲量"] = 1

品牌_list = ['大碩','偉文','高點','學堂','志光','百官','洋碩','巨匠','放洋','甄戰','樂學網','龍門','留學家',
           "菁英","戴爾","三民","公職王","字神帝國","金榜函授",'駿寶','繁田塾','永漢', 'JPTIP', '地球村', '旭文', '何必', 'Jella', '東橋', '王可樂', '出口仁', 'HIROSHI']
df_gmap["品牌"] = "無"

for i in range(len(df_gmap)):
    for j in 品牌_list:
        if j in df_gmap["name"][i]:
            pd.options.mode.chained_assignment = None  # default='warn'
            df_gmap["品牌"][i] = j

df_ptt = df_ptt.fillna(0) ; df_dcard= df_dcard.fillna(0)
df_ptt["文章情緒"] = list(df_ptt[df_ptt.columns[9:12]].astype(float).idxmax(axis = 1)) ; df_dcard["文章情緒"] = list(df_dcard[df_dcard.columns[8:11]].astype(float).idxmax(axis = 1))

st.title("輿情系統")
tab1, tab2,tab3,tab4 = st.tabs(["**品牌**", "**自選關鍵字**","**熱門文章**",'**詞組管理**'])
with tab1:
    with st.form("brand"):
        brand = st.selectbox("**品牌**",options = ["大碩", "龍門", "甄戰","百官","洋碩","學堂"])
        submitted1 = st.form_submit_button('品牌選擇完畢')
    with st.form("my_form"):
        left_col, right_col = st.columns(2)
        max_date = df_ptt['created_at_日期'].max()
        
        with left_col:
            start_now = max_date  - relativedelta(months = 1)
            start_now = str(start_now).split("-")
            start_now = st.date_input("**當期開始日期**",datetime.date(int(start_now[0]), int(start_now[1]), int(start_now[2])))

        with right_col:
            end_now = max_date  - relativedelta(days = 1)
            end_now = str(end_now).split("-")
            end_now = st.date_input("**當期結束日期**",datetime.date(int(end_now[0]), int(end_now[1]), int(end_now[2])))

        left_col, right_col = st.columns(2)
        with left_col:
            start_choose = st.date_input("**自選開始日期**",datetime.date(2023, 1, 1))
        with right_col:
            end_choose = st.date_input("**自選結束日期**",datetime.date(2023, 1, 31))

        option_競品1,option_競品2 = app_functions.selectbox(brand,"目前品牌","請選擇**競品1**","請選擇**競品2**")
        options = st.selectbox("社群來源",options = ['PTT', "Dcard", "Google Map"])

        submitted = st.form_submit_button('送出')
    
    if submitted:
        brand = brand
        start_now = start_now
        end_now = end_now
        start_choose = start_choose
        end_choose = end_choose
        option_競品1 = option_競品1
        option_競品2 = option_競品2
        options = options
        st.success('送出成功', icon="✅")
    else:
        st.write("條件尚未篩選完畢")

    start_year = int(str(start_now).split("-")[0]) ; start_month = int(str(start_now).split("-")[1]) ; start_date = int(str(start_now).split("-")[2])
    end_year = int(str(end_now).split("-")[0]) ; end_month = int(str(end_now).split("-")[1]) ; end_date = int(str(end_now).split("-")[2])

    time_range = relativedelta(end_now,start_now)
    
    end_lastmonth = end_now  - relativedelta(months = time_range.months+1)
    start_lastmonth = end_lastmonth - relativedelta(days = time_range.days) -  relativedelta(months = time_range.months)

    start_lastyear = start_now - relativedelta(years = 1)
    end_lastyear = end_now - relativedelta(years = 1)

    if start_now > end_now:
        st.caption("開始日期不可大於結束日期，請重新選擇")
    else:    
        components.html(
            f"""
            <style>
                p{{
                    line-height: 0.2;
                    font-size: 10pt;
                    color:gray;
                }}
            </style>
            <p>當期區間 : {start_now} ~ {end_now}</p>
            <p>前期區間 : {start_lastmonth} ~ {end_lastmonth}</p>
            <p>去年同期 : {start_lastyear} ~ {end_lastyear}</p>
            """,
            height = 60
        )

    if start_choose > end_choose:
        st.caption("開始日期不可大於結束日期，請重新選擇")

    # 輿情總覽
    st.subheader("輿情總覽")

    df_品牌_情緒_brand = app_functions.find_品牌情緒(df_ptt,df_dcard,df_gmap,brand)
    df_品牌_情緒_競品1 = app_functions.find_品牌情緒(df_ptt,df_dcard,df_gmap,option_競品1)
    df_品牌_情緒_競品2 = app_functions.find_品牌情緒(df_ptt,df_dcard,df_gmap,option_競品2)
    df_數量 = pd.concat([df_品牌_情緒_brand.groupby('管道',as_index=False).sum('數量')["數量"],df_品牌_情緒_競品1.groupby('管道',as_index=False).sum('數量')["數量"]],axis = 0)
    df_數量 = pd.concat([df_數量,df_品牌_情緒_競品2.groupby('管道',as_index=False).sum('數量')["數量"]],axis = 0)
    df_數量 = df_數量.reset_index(drop = True)
    df_品牌_情緒 = pd.concat([app_functions.remove(df_品牌_情緒_brand,brand),app_functions.remove(df_品牌_情緒_競品1,option_競品1)],axis = 0)
    df_品牌_情緒 = pd.concat([df_品牌_情緒,app_functions.remove(df_品牌_情緒_競品2,option_競品2)],axis = 0)

    df_品牌_情緒_正向 = df_品牌_情緒[df_品牌_情緒["文章情緒"] == '正向'].rename(columns = {"比例":"正向比例"})
    df_品牌_情緒_正向.reset_index(inplace = True, drop = True)
    df_品牌_情緒_正向 = df_品牌_情緒_正向.drop_duplicates()
    df_品牌_情緒_負向 = df_品牌_情緒[df_品牌_情緒["文章情緒"] == '負向'].rename(columns = {"比例":"負向比例"})
    df_品牌_情緒_負向.reset_index(inplace = True, drop = True)
    df_品牌_情緒_負向 = df_品牌_情緒_負向.drop_duplicates()
    df_品牌_情緒 = pd.merge(df_品牌_情緒_正向,df_品牌_情緒_負向[["管道","負向比例","品牌"]],on = ['管道','品牌'],how = 'outer')
    df_品牌_情緒["聲量"] = df_數量
    app_functions.replace_nan(df_品牌_情緒,"正向比例")
    app_functions.replace_nan(df_品牌_情緒,"負向比例")
    app_functions.replace_nan(df_品牌_情緒,"數量")
    app_functions.replace_nan(df_品牌_情緒,"聲量")
    df_品牌_情緒 = df_品牌_情緒.drop_duplicates()

    fig = px.scatter(df_品牌_情緒[df_品牌_情緒['管道'] != 'gmap'], x = "正向比例",y = "負向比例",size = "聲量",color = '管道',
                text = '品牌',color_discrete_map = {"PTT":"#087294","Dcard":"#FEB62A"}
                 )
    fig.update_layout(xaxis_title = "正向比例",
                        yaxis_title = "負向比例",
                        yaxis = dict(tickfont = dict(size=20)),
                        xaxis = dict(tickfont = dict(size=20)),
                        bargap = 0.5,
                    font=dict(
                        size=20)
                    )
    # fig.update_xaxes(visible=False)
    fig.update_traces(textposition = 'top center',textfont_size=14)

    fig1 = px.scatter(df_品牌_情緒[df_品牌_情緒['管道'] == 'gmap'], x = "正向比例",y = "負向比例",size = "聲量",color = '管道',
                text = '品牌',color_discrete_map = {"PTT":"#087294","Dcard":"#FEB62A"}
                 )
    fig1.update_layout(xaxis_title = "正向比例",
                        yaxis_title = "負向比例",
                        yaxis = dict(tickfont = dict(size=20)),
                        xaxis = dict(tickfont = dict(size=20)),
                        bargap = 0.5,
                    font=dict(
                        size=20)
                    )
    fig1.update_traces(textposition = 'top center',textfont_size=14)
    

    if options == "PTT":
        data = df_ptt
    elif options == "Dcard":
        data = df_dcard
    else:
        data = df_gmap

    if (options == "PTT") or (options == "Dcard"):
        col1, padding, col2 = st.columns((22.5,0.5,6))
        with col1:
            st.plotly_chart(fig,use_container_width=True)
        with col2:
            st.write("")
        with st.expander("說明"):
            st.caption('PTT、Dcard 的情緒是使用文章內容所計算，Google Map 的情緒是使用評論所計算。')
        st.write(" ")
        data_特定品牌 = data[data["品牌"] == brand]
        data_特定品牌.reset_index(inplace = True,drop = True)
        # 篩選特定區間的資料
        data_now = data_特定品牌[(data_特定品牌["created_at_日期"] >= start_now) & (data_特定品牌["created_at_日期"] <= end_now)]
        data_lastmonth = data_特定品牌[(data_特定品牌["created_at_日期"] >= start_lastmonth) & (data_特定品牌["created_at_日期"] <= end_lastmonth)]
        data_lastyear = data_特定品牌[(data_特定品牌["created_at_日期"] >= start_lastyear) & (data_特定品牌["created_at_日期"] <= end_lastyear)]
        
        # create 符合特定日期區間的空的 dataframe
        filter_now = app_functions.create_date(start_now,end_now)
        filter_lastmonth = app_functions.create_date(start_lastmonth,end_lastmonth)
        filter_lastyear = app_functions.create_date(start_lastyear,end_lastyear)

        # 篩選出有聲量的日期
        voice_now = data_now.groupby("created_at_日期").sum().reset_index()[["created_at_日期","聲量"]]
        voice_lastmonth = data_lastmonth.groupby("created_at_日期").sum().reset_index()[["created_at_日期","聲量"]]
        voice_lastyear = data_lastyear.groupby("created_at_日期").sum().reset_index()[["created_at_日期","聲量"]]
        
        filter_now = app_functions.match_聲量(voice_now,filter_now)
        filter_lastmonth = app_functions.match_聲量(voice_lastmonth,filter_lastmonth)
        filter_lastyear = app_functions.match_聲量(voice_lastyear,filter_lastyear)

        filter_lastmonth["當期日期"] = filter_now["日期"]
        filter_lastyear["當期日期"] = filter_now["日期"]

        col1, col2 = st.columns(2)

        st.subheader("品牌聲量")
        genre = st.radio(
        "選擇一項:",
        ('當期與前期、去年同期比較', '當期與自選區間比較'))
        if genre == "當期與前期、去年同期比較":

            trace1 = go.Scatter(x = filter_now["日期"], y = filter_now["聲量"], mode='lines', 
                                name='當期',text = filter_now["日期"],line_color = '#F8B93E')
            trace2 = go.Scatter(x = filter_lastmonth["當期日期"], y = filter_lastmonth["聲量"], mode='lines', 
                                name="前期",text = filter_lastmonth["日期"],line_color = '#74C1DB')
            trace3 = go.Scatter(x = filter_lastyear["當期日期"], y = filter_lastyear["聲量"], mode='lines', 
                                name='去年同期',text = filter_lastyear["日期"],line_color = '#A9B0AB')

            fig = go.Figure(data=[trace1, trace2, trace3])

            fig.update_traces(mode="markers+lines", hovertemplate=None)
            fig.update_layout(
                title = f"「{brand}」當期聲量與前期、去年同期比較",
                xaxis_title="當期日期",
                yaxis_title="聲量",
                legend_title="時間區間",
                font=dict(size=14,),
                hovermode="x unified",
                yaxis=dict(tickmode='linear', tick0=0, dtick=1)
            )
            st.plotly_chart(fig, use_container_width=True)

        data_now = data_特定品牌[(data_特定品牌["created_at_日期"] >= start_now) & (data_特定品牌["created_at_日期"] <= end_now)]
        data_choose = data_特定品牌[(data_特定品牌["created_at_日期"] >= start_choose) & (data_特定品牌["created_at_日期"] <= end_choose)]
        app_functions.change_column_type(data_choose,"created_at_日期")
    
        filter_now = app_functions.create_date(start_now,end_now)
        filter_choose = app_functions.create_date(start_choose,end_choose)

        voice_now = data_now.groupby("created_at_日期").sum().reset_index()[["created_at_日期","聲量"]]
        app_functions.create_chart_dataframe(voice_now,filter_now,data_now)

        voice_choose = data_choose.groupby("created_at_日期").sum().reset_index()[["created_at_日期","聲量"]]
        app_functions.create_chart_dataframe(voice_choose,filter_choose,data_choose)
        filter_choose["當期日期"] = filter_now["日期"]

        if genre == "當期與自選區間比較":
            delta1,delta2 = app_functions.date_range(start_now,end_now,start_choose,end_choose)
            if delta1 == delta2:
                trace1 = go.Scatter(x = filter_now["日期"], y = filter_now["聲量"], mode='lines', 
                            name='當期',text = filter_now["日期"],line_color = '#F8B93E')
                trace2 = go.Scatter(x = filter_choose["當期日期"], y = filter_choose["聲量"], mode='lines', 
                                    name="自選",text = filter_choose["日期"],line_color = '#8ED0E6')
                fig = go.Figure(data=[trace1, trace2])
                fig.update_traces(mode="markers+lines", hovertemplate=None)
                fig.update_layout(
                    title = f"「{brand}」當期聲量與自選期間比較",
                    xaxis_title="當期日期",
                    yaxis_title="聲量",
                    legend_title="時間區間",
                    font=dict(size=14,),
                    hovermode="x unified",yaxis=dict(tickmode='linear',tick0=0,dtick=1))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("間隔天數不相符，請重新選擇")
        with st.expander("圖表說明"):
            st.caption('''
            1.圖表右上方的功能列具有下載、放大、縮小、拖曳、回到預設大小的功能。\n
            2.可將滑鼠移到圖表上擷取部分畫面，再快速點擊圖表兩下能夠回到圖表預設大小。\n
            3.點擊圖例選項能夠選擇顯示何種類別的資料。
                       ''')
            st.write(" ")

        genre1 = st.radio("選擇一項:",('與競品比較', '自選時間區間比較'))

        #與競品比較
        data_自選品牌1 = data[data["品牌"] == option_競品1]
        data_自選品牌2 = data[data["品牌"] == option_競品2]
       
        data_brand1_now = data_自選品牌1[(data_自選品牌1["created_at_日期"] >= start_now) & (data_自選品牌1["created_at_日期"] <= end_now)]
        data_brand2_now = data_自選品牌2[(data_自選品牌2["created_at_日期"] >= start_now) & (data_自選品牌1["created_at_日期"] <= end_now)]

        filter_brand1_now = app_functions.create_date(start_now,end_now)
        filter_brand2_now = app_functions.create_date(start_now,end_now)

        voice_brand1_now= data_brand1_now.groupby("created_at_日期").sum().reset_index()[["created_at_日期","聲量"]]
        voice_brand2_now= data_brand2_now.groupby("created_at_日期").sum().reset_index()[["created_at_日期","聲量"]]

        voice_brand1_now = data_brand1_now.groupby("created_at_日期").sum().reset_index()[["created_at_日期","聲量"]]
        app_functions.create_chart_dataframe(voice_brand1_now,filter_brand1_now,data_brand1_now)
        filter_brand1_now["當期日期"] = filter_now["日期"]

        voice_brand2_now = data_brand2_now.groupby("created_at_日期").sum().reset_index()[["created_at_日期","聲量"]]
        app_functions.create_chart_dataframe(voice_brand2_now,filter_brand2_now,data_brand2_now)
        filter_brand2_now["當期日期"] = filter_now["日期"]

        if genre1 == "與競品比較":

            trace1 = go.Scatter(x = filter_now["日期"], y = filter_now["聲量"], mode='lines', 
                        name = brand,text = filter_now["日期"],line_color = '#F8B93E')
            trace2 = go.Scatter(x = filter_brand1_now["當期日期"], y = filter_brand1_now["聲量"], mode='lines', 
                                name = option_競品1,text = filter_brand1_now["日期"],line_color = '#74C1DB')
            trace3 = go.Scatter(x = filter_brand2_now["當期日期"], y = filter_brand2_now["聲量"], mode='lines', 
                                name = option_競品2,text = filter_brand1_now["日期"],line_color = '#A9B0AB')
            
            if option_競品2 == "不選擇":
                fig = go.Figure(data=[trace1, trace2])
            else:
                fig = go.Figure(data=[trace1, trace2,trace3])

            fig.update_traces(mode="markers+lines", hovertemplate=None)
            fig.update_layout(
                title = f"「{brand}」與競品聲量比較",
                xaxis_title="當期日期",
                yaxis_title="聲量",
                legend_title="時間區間",
                font=dict(size=14,),
                hovermode="x unified",
                yaxis=dict(tickmode='linear',tick0=0,dtick=1))
            st.plotly_chart(fig, use_container_width=True)

        data_自選品牌1 = data[data["品牌"] == option_競品1]
        data_brand1_自選 = data_自選品牌1[(data_自選品牌1["created_at_日期"] >= start_choose) & (data_自選品牌1["created_at_日期"] <= end_choose)]
        filter_brand1_自選 = app_functions.create_date(start_choose,end_choose)
        voice_brand1_自選 = data_brand1_自選.groupby("created_at_日期").sum().reset_index()[["created_at_日期","聲量"]]
        voice_brand1_自選 = data_brand1_自選.groupby("created_at_日期").sum().reset_index()[["created_at_日期","聲量"]]
        app_functions.create_chart_dataframe(voice_brand1_自選,filter_brand1_自選,data_brand1_自選)
        filter_brand1_自選["當期日期"] = filter_now["日期"]

        if genre1 == "自選時間區間比較":
            
            trace1 = go.Scatter(x = filter_now["日期"], y = filter_now["聲量"], mode='lines', 
                        name = f"{brand}(當期)",text = filter_now["日期"],line_color = '#EB9F0C')

            trace2 = go.Scatter(x = filter_choose["當期日期"], y = filter_choose["聲量"], mode='lines', 
                                name = f"{brand}(自選)",text = filter_choose["日期"],line_color = '#FFCF73')

            trace3 = go.Scatter(x = filter_brand1_now["當期日期"], y = filter_brand1_now["聲量"], mode='lines', 
                                name = f"{option_競品1}(當期)",text = filter_brand1_now["日期"],line_color = '#0D86AD')

            trace4 = go.Scatter(x = filter_brand1_自選["當期日期"], y = filter_brand1_自選["聲量"], mode='lines', 
                                name = f"{option_競品1}(自選)",text = filter_brand1_自選["日期"],line_color = '#86D7F2')

            # 將三條折線添加到同一個圖表中
            fig = go.Figure(data=[trace1, trace2,trace3,trace4])
            # 顯示圖表
            fig.update_traces(mode="markers+lines", hovertemplate=None)
            fig.update_layout(
                title = f"「{brand}」與競品聲量比較",
                xaxis_title="當期日期",
                yaxis_title="聲量",
                legend_title="時間區間",
                font=dict(size=14,),
                hovermode="x unified",
                yaxis=dict(tickmode='linear',tick0=0,dtick=1)
            )

            st.plotly_chart(fig, use_container_width=True)

        st.subheader("看板分佈") 
        
        df_board = pd.concat([data_now,data_brand1_now],axis = 0)
        df_board = pd.concat([df_board,data_brand2_now],axis = 0)
        df_board = df_board.groupby(["品牌","board"],as_index = False).sum("評論數")
        df_board = df_board.sort_values(by = '看板數量',ascending = False)
        fig1 = px.bar(df_board,x = "board",y ="看板數量",color = "品牌",barmode="group",
                      color_discrete_sequence=px.colors.qualitative.Set2,
                      text_auto=True)
        fig1.update_layout(
            title = f"「{brand}」與競品看板分佈",
            xaxis_title="看板",
            yaxis_title="聲量",
            legend_title="品牌",
            font=dict(size=14)
        )
        st.plotly_chart(fig1,use_container_width = True)

        st.subheader("文字雲") 

        斷詞_now = app_functions.文章斷詞(data_now)
        斷詞_brand1_now = app_functions.文章斷詞(data_brand1_now)
        斷詞_brand2_now = app_functions.文章斷詞(data_brand2_now)

        count_now = app_functions.words_counts(斷詞_now,data_now)
        count_brand1_now = app_functions.words_counts(斷詞_brand1_now,data_brand1_now)
        count_brand2_now = app_functions.words_counts(斷詞_brand2_now,data_brand2_now)
        

        stopwords = []
        f = open('cn_stopwords.txt','r',encoding="utf-8")
        for line in f.readlines():
            line = line.replace("\n","")
            stopwords.append(line)

        def 判斷是否有資料(data,text,count):
            if len(data) != 0:
                app_functions.wordcloud_chart(count)
            else:
                st.write(text)

        if (option_競品1 != "不選擇") & (option_競品2 != "不選擇"):
            col1,col2 = st.columns(2)
            with col1:
                st.write(f"**{brand}**:")
                判斷是否有資料(data_now,f"沒有資料",count_now)
                
            with col2:
                st.write(f"**{option_競品1}**:")
                判斷是否有資料(data_brand1_now,f"沒有資料",count_brand1_now)
                
            col1,col2 = st.columns(2)
            with col1:
                st.write(f"**{option_競品2}**:")
                判斷是否有資料(data_brand2_now,f"沒有資料",count_brand2_now)
            with col2:
                st.write("")

        elif option_競品2 == "不選擇":
            col1,col2 = st.columns(2)
            with col1:
                st.write(f"**{brand}**:")
                判斷是否有資料(data_now,f"沒有資料",count_now)
            with col2:
                st.write(f"**{option_競品1}**:")
                判斷是否有資料(data_brand1_now,f"沒有資料",count_brand1_now)
        elif option_競品1 == "不選擇":
            col1,col2 = st.columns(2)
            with col1:
                st.write(f"**{brand}**:")
                判斷是否有資料(data_now,f"沒有資料",count_now)
            with col2:
                st.write(f"**{option_競品2}**:")
                判斷是否有資料(data_brand2_now,f"沒有資料",count_brand2_now)

        elif (option_競品1 == "不選擇") & (option_競品2 == "不選擇"):
            col1,col2 = st.columns(2)
            with col1:
                st.write(f"**{brand}**:")
                判斷是否有資料(data_now,f"沒有資料",count_now)
            with col2:
                st.write("")

        st.subheader("情緒分佈")
        

        option_情緒分佈 = st.radio("選擇一個時間區間:",('當期新增文章', '累積文章',"當期 與 前期、去年同期 比較"))
        data_特定品牌 = data[data["品牌"] == brand]
        data_品牌情緒 = data_特定品牌[data_特定品牌["created_at_日期"] <= end_now]

        data_自選品牌1 = data[data["品牌"] == option_競品1]
        data_自選品牌2 = data[data["品牌"] == option_競品2]

        data_自選品牌1 = data_自選品牌1[data_自選品牌1["created_at_日期"] <= end_now]
        data_自選品牌2 = data_自選品牌2[data_自選品牌2["created_at_日期"] <= end_now]
        if option_情緒分佈 == '當期新增文章':
            
            df_board = pd.concat([data_now,data_brand1_now],axis = 0)
            df_board = pd.concat([df_board,data_brand2_now],axis = 0)
            df_board = df_board.groupby(["品牌","文章情緒"],as_index = False).sum("評論數")
            df_board = df_board.sort_values(by = '看板數量',ascending = False)
            fig = px.bar(df_board,x = "品牌",y = "看板數量",color = "文章情緒",
                        barmode="group",
                        color_discrete_map = {
                    "負向": "#FF9191",
                    "中性": "#FFE385",
                    "正向": "#A0C8AD"},
                    text = "看板數量")
            fig.update_layout(
                title = f"「{brand}」與競品情緒分佈",
                xaxis_title = "品牌",
                yaxis_title = "聲量",
                legend_title = "文章情緒",
                font=dict(size=14))
            fig.update_traces(textposition = 'auto',textfont_size=16)
            st.plotly_chart(fig)
        elif option_情緒分佈 == '當期 與 前期、去年同期 比較':
            
            data_now["時間"] = "當期"
            data_lastmonth["時間"] = "前期"
            data_lastyear["時間"] = "去年同期"

            df_board = pd.concat([data_now,data_lastmonth],axis = 0)
            df_board = pd.concat([df_board,data_lastyear],axis = 0)
            df_board = df_board.groupby(["品牌","時間","文章情緒"],as_index = False).sum("評論數")
            df_board = df_board.sort_values(by = '看板數量',ascending = False)
            fig = px.bar(df_board,x = "文章情緒",y = "看板數量",color = "時間",text_auto = True,
                        barmode="group",
                        color_discrete_map = {
                    "當期": "#C3CAC5",
                    "前期": "#94C4D4",
                    "去年同期": "#EDDA96"})
            fig.update_layout(
                title = f"「{brand}」當期情緒與前期、去年同期比較",
                xaxis_title = "情緒",
                yaxis_title = "聲量",
                legend_title = "時間",
                font=dict(size=14,))
            st.plotly_chart(fig)
        else:
            df_board = pd.concat([data_品牌情緒,data_自選品牌1],axis = 0)
            df_board = pd.concat([df_board,data_自選品牌2],axis = 0)
            df_board = df_board.groupby(["品牌","文章情緒"],as_index = False).sum("評論數")
            df_board = df_board.sort_values(by = '看板數量',ascending = False)
            fig = px.bar(df_board,x = "品牌",y = "看板數量",color = "文章情緒",text_auto = True,
                        barmode="group",
                        color_discrete_map = {
                    "負向": "#FF9191",
                    "中性": "#FFE385",
                    "正向": "#A0C8AD"})
            fig.update_layout(
                title = f"「{brand}」與競品累積情緒分佈",
                xaxis_title = "品牌",
                yaxis_title = "聲量",
                legend_title = "情緒",
                font=dict(size=14,),
                yaxis=dict(tickmode='linear',tick0=0,dtick=20))
            st.plotly_chart(fig)

        st.subheader("文章清單")

        option_情緒 = st.radio("選擇情緒:",("全部",'正向情緒', '負向情緒',"中性情緒"))
        data_品牌情緒_now = data_特定品牌[(data_特定品牌["created_at_日期"] >= start_now)&(data_特定品牌["created_at_日期"] <= end_now)]
        data_品牌情緒_now = data_品牌情緒_now.rename(columns = {"created_at_日期":"日期"})
        data_品牌情緒_now["互動數"] = data_品牌情緒_now["like_count"]+data_品牌情緒_now["comment_count"]
        data_品牌情緒_now["管道"] = "PTT"
        data_品牌情緒_now["正向情緒"] = [0 if i == "無" else int(i)  for i in data_品牌情緒_now["正向"]]
        data_品牌情緒_now["負向情緒"] = [0 if i == "無" else int(i) for i in data_品牌情緒_now["負向"]]
        data_品牌情緒_now["中性情緒"] = [0 if i == "無" else int(i) for i in data_品牌情緒_now["中性"]]
        data_品牌情緒_now["文章情緒"] = data_品牌情緒_now[["正向情緒","負向情緒","中性情緒"]].idxmax(axis = 1).to_frame()[0]
        data = data_品牌情緒_now[["品牌","管道","日期","title","board","互動數","content","文章情緒"]]

        if option_情緒 == "全部":
            data.reset_index(drop = True,inplace = True)
            st.dataframe(data)
        else:
            data = data[data["文章情緒"] == option_情緒]
            data.reset_index(drop = True,inplace = True)
            st.dataframe(data)
        with st.expander("說明"):
            st.write("1. 滑鼠點兩下可看到資料格全貌 \n 2. 滑鼠選取部分範圍可以複製貼上到 Libre Office 或是 google sheet \n 3. 可以自行調整欄寬 \n 4. 按住 Ctrl F 可以搜尋資料 \n 5. 右下角可以縮放資料表 \n 6. 點擊欄位名稱可以遞增或遞減排序")

    # google map
    elif options == "Google Map":
        col1, padding, col2 = st.columns((22.5,0.5,6))
        with col1:
            st.markdown("**社群輿情**")
            st.plotly_chart(fig1,use_container_width=True)
        with col2:
            gmap_name = df_gmap[df_gmap["品牌"] == brand].groupby("name")["rating"].mean().to_frame()
            gmap_name["店點"] = gmap_name.index
            gmap_name.reset_index(drop = True,inplace = True)
            gmap_name["rating"] = [round(i,2)for i in gmap_name["rating"]]
            gmap_name["評價"] = [df_gmap[df_gmap["品牌"] == brand].groupby("name").get_group(i).value_counts("Preds").idxmax() for i in gmap_name["店點"]]
            gmap_name = pd.merge(gmap_name,df_gmap[['lon','name']],left_on = '店點',right_on = 'name').drop("name",axis = 1).drop_duplicates()
            gmap_name.sort_values('lon',ascending = False,inplace = True)
            gmap_name.reset_index(drop = True,inplace = True)
            list1 = []
            text = ""
            for i in range(len(gmap_name)):
                店點 = gmap_name["店點"][i]
                rating = gmap_name["rating"][i]
                評價 = gmap_name["評價"][i]
                sep_line = "\n"
                list1.append(f'**{店點}** :  {sep_line} {rating:<6}   {評價} {sep_line}')
            nl = '\n'
            text = f"{nl}{nl}{nl.join(list1)}"
            
            scrollable_style = """
                <style>
                    .scrollable-element {
                        overflow-y: auto !important;
                        max-height: 400px !important;
                    }
                </style>
            """
            
            st.markdown(" ")
            st.markdown(" ")
            st.markdown(" ")
            st.markdown(" ")
            st.markdown(" ")
            st.markdown("**店點輿情**")
            
            st.markdown(scrollable_style, unsafe_allow_html=True)
            st.markdown('<div class="scrollable-element">' + text + '</div>', unsafe_allow_html=True)

        with st.expander("說明"):
            st.caption('PTT、Dcard 的情緒是使用文章內容所計算，Google Map 的情緒是使用評論所計算。')
            st.write(" ")

        data = df_gmap
        data_now = df_gmap[(df_gmap["review_time_日期"] >= start_now) & (df_gmap["review_time_日期"] <= end_now)]
        data_lastmonth = df_gmap[(df_gmap["review_time_日期"] >= start_lastmonth) & (df_gmap["review_time_日期"] <= end_lastmonth)]
        data_lastyear = df_gmap[(df_gmap["review_time_日期"] >= start_lastyear) & (df_gmap["review_time_日期"] <= end_lastyear)]
        data_end = df_gmap[df_gmap["review_time_日期"] <= end_now]

        st.subheader("評論數分佈")
        option_評論數 = st.radio("選擇一種:",('當期新增評論數', '累積評論數'))
        if option_評論數 == "當期新增評論數":
            st.markdown(f"「{brand}」當期新增評論")
            df = data_now[data_now["品牌"] == brand].groupby("name").sum()
            df["name"] = df.index
            df.reset_index(drop = True,inplace = True)
            df = df.sort_values(by = '評論數',ascending = False)
            fig = px.bar(df, x = "評論數",y = "name",
                text="評論數")
            fig.update_layout(xaxis_title = "",
                            yaxis_title = "",
                            yaxis = dict(tickfont = dict(size=20)),
                            xaxis = dict(tickfont = dict(size=20)),
                            showlegend =  False,
                            bargap = 0.5)
            
            fig.update_traces(textposition = 'auto',textfont_size=16)

            st.plotly_chart(fig,use_container_width=True)
        else:
            st.markdown(f"「{brand}」累積評論")
            df = data_end[data_end["品牌"] == brand].groupby("name").sum()
            df["name"] = df.index
            df.reset_index(drop = True,inplace = True)
            df = df.sort_values(by = '評論數',ascending = False)
            fig = px.bar(df, x = "評論數",y = "name",
                text="評論數")
            fig.update_layout(xaxis_title = "",
                            yaxis_title = "",
                            yaxis = dict(tickfont = dict(size=20)),
                            xaxis = dict(tickfont = dict(size=20)),
                            showlegend =  False,
                            bargap = 0.5)
  
            fig.update_traces(textposition = 'auto',textfont_size=16)

            st.plotly_chart(fig,use_container_width=True)\
            
        st.subheader("星等數分佈")
        option_星等數 = st.radio("選擇一種:",('當期新增星等數', '累積星等數'))

        if option_星等數 == "當期新增星等數":
            data_品牌 = data_now[data_now["品牌"] == brand]
            df = app_functions.rating_data(data_品牌,brand)
            df = df.sort_values(by = '數量',ascending = False)
            fig = px.bar(df, x = "數量",y = "name",color = "星等數",
                text="數量",
                category_orders={"星等數": ["1", "2", "3","4","5"]},
                color_discrete_map = {
                    "1": "#FF9191",
                    "2": "#FFE385",
                    "3": "#A0C8AD",
                    "4": "#20AFDC",
                    "5": "#FFA959"}
                )
            
            fig.update_layout(xaxis_title = "評論數",
                            yaxis_title = "",
                            yaxis = dict(tickfont = dict(size=20)),
                            xaxis = dict(tickfont = dict(size=20)),
                            showlegend =  True,
                            bargap = 0.5)
            
            fig.update_traces(textposition = 'auto',textfont_size=13)
            st.markdown(f"「{brand}」當期新增星等數")
            st.plotly_chart(fig,use_container_width=True)
        else:
            data_品牌 = data_end[data_end["品牌"] == brand]
            df = app_functions.rating_data(data_品牌,brand)
            df = df.sort_values(by = '數量',ascending = False)
            fig = px.bar(df, x = "數量",y = "name",color = "星等數",
                text="數量",
                category_orders={"星等數": ["1", "2", "3","4","5"]},
                color_discrete_map = {
                    "1": "#FF9191",
                    "2": "#FFE385",
                    "3": "#A0C8AD",
                    "4": "#20AFDC",
                    "5": "#FFA959"})
            
            fig.update_layout(xaxis_title = "評論數",
                            yaxis_title = "",
                            yaxis = dict(tickfont = dict(size=20)),
                            xaxis = dict(tickfont = dict(size=20)),
                            showlegend =  True,
                            bargap = 0.5)
            
            fig.update_traces(textposition = 'auto',textfont_size=13)
            st.markdown(f"「{brand}」累積星等數")
            st.plotly_chart(fig,use_container_width=True)

        st.subheader("文字雲")

        data_品牌 = data_now[data_now["品牌"]== brand]
        店點_list = st.multiselect(f"**{brand}**",data_品牌["name"].unique(),max_selections = 4)
        n_店點 = len(店點_list)
        stopwords = app_functions.read_stopwords()
        if n_店點 == 1:
            app_functions.gmap_文字雲_1(data_品牌,店點_list,0)
        elif n_店點 ==2:
            app_functions.gmap_文字雲_2(data_品牌,店點_list,0,1)
        elif n_店點 == 3:
            app_functions.gmap_文字雲_2(data_品牌,店點_list,0,1)
            app_functions.gmap_文字雲_1(data_品牌,店點_list,2)
        elif n_店點 == 4:
            app_functions.gmap_文字雲_2(data_品牌,店點_list,0,1)
            app_functions.gmap_文字雲_2(data_品牌,店點_list,2,3)

        st.subheader("評論數比較")
        df = pd.concat([app_functions.find_品牌_評論(data_now,brand,"當期"),
                        app_functions.find_品牌_評論(data_lastmonth,brand,"前期")],
                        axis = 0)
        df = pd.concat([df,app_functions.find_品牌_評論(data_lastyear,brand,"去年同期")],
                    axis = 0)
        df.reset_index(drop = True,inplace = True)
        df = df.sort_values(by = '評論數',ascending = False)
        fig = px.bar(df, x = "評論數",y = "name",color = "時間",
            text="評論數",
            category_orders={"時間": ["當期", "前期", "去年同期"]},
            barmode = "group",color_discrete_map = {
                "當期": "#F8B93E",
                "前期": "#74C1DB",
                "去年同期": "#A9B0AB"}
            )
        fig.update_layout(xaxis_title = "評論數",
                        yaxis_title = "",
                        yaxis = dict(tickfont = dict(size=10)),
                        xaxis = dict(tickfont = dict(size=10)),
                        showlegend =  True,
                        bargap = 0.2)
        fig.update_xaxes(visible=False)
        fig.update_traces(textposition = 'auto',textfont_size=16)
        st.plotly_chart(fig,use_container_width=True)

        
        st.subheader("正負評論數")
        option_評論數 = st.radio("選擇一種:",('當期新增評論數', '累積評論數',"當期、前期、去年同期評論數比較"))
        
        if option_評論數 == "當期新增評論數":
            data_品牌 = data_now[data_now["品牌"]==brand]
            data_品牌 = data_品牌.drop('rating',axis =1)
            data_品牌 = data_品牌.drop('like_count',axis =1)
            data_品牌 = data_品牌.groupby(['name','Preds'],as_index = False).sum('評論數')
        elif option_評論數 == "累積評論數":
            data_品牌 = data_end[data_end["品牌"]==brand]
            data_品牌 = data_品牌.drop('rating',axis =1)
            data_品牌 = data_品牌.drop('like_count',axis =1)
            data_品牌 = data_品牌.groupby(['name','Preds'],as_index = False).sum('評論數')
        else:
            data_品牌_now = data_now[data_now["品牌"] == brand]
            data_品牌_lastmonth = data_lastmonth[data_lastmonth["品牌"]==brand]
            data_品牌_lastyear = data_lastyear[data_lastyear["品牌"]==brand]
            data_品牌_now["時間"] = "當期"
            data_品牌_lastmonth["時間"] = "前期"
            data_品牌_lastyear["時間"] = "去年同期"
            df_board = pd.concat([data_品牌_now,data_品牌_lastmonth],axis = 0)
            df_board = pd.concat([df_board,data_品牌_lastyear],axis = 0)
            df_board = df_board.drop('rating',axis =1)
            df_board = df_board.drop('like_count',axis =1)
            df_board = df_board.groupby(["時間",'Preds'],as_index = False).sum('評論數')

        if (option_評論數 == "當期新增評論數") or (option_評論數 == "累積評論數"):
            data_品牌 = app_functions.remove_衝突(data_品牌)
            data_品牌 = data_品牌.groupby(['name','Preds'],as_index = False).sum('評論數')
            data_品牌 = data_品牌.sort_values(by = '評論數',ascending = False)
            fig = px.bar(data_品牌,x = "name",y = "評論數",color = "Preds",barmode="group",
                        category_orders={"情緒": ["正向", "中性", "負向"]},
                        color_discrete_map = {
                            "負向": "#FF9191",
                            "中性": "#FFE385",
                            "正向": "#A0C8AD"},
                        text_auto = True)
            fig.update_layout(
                title = f"「{brand}」累積情緒分佈",
                xaxis_title = "品牌",
                yaxis_title = "數量",
                legend_title = "情緒")
            st.plotly_chart(fig,use_container_width=True)
           
        else:
            df_board = app_functions.remove_衝突(df_board)
            df_board = df_board.groupby(["時間",'Preds'],as_index = False).sum('評論數')
            df_board = df_board.sort_values(by = '評論數',ascending = False)
            fig = px.bar(df_board,x = "Preds",y = "評論數",color = "時間",barmode="group",
            category_orders={"時間": ["當期", "前期", "去年同期"]},
            color_discrete_map = {
                "當期": "#F8B93E",
                "前期": "#74C1DB",
                "去年同期": "#A9B0AB"},
                text_auto = True)
            fig.update_layout(
                title = f"「{brand}」當期、前期、去年同期 情緒比較",
                xaxis_title = "情緒",
                yaxis_title = "數量",
                legend_title = "時間"
            )
            st.plotly_chart(fig,use_container_width=True)
        st.subheader('評論地區分布')
        st.write(f'{brand}與競品評論分布')
        data_brand1_now = data[data["品牌"] == option_競品1]
        data_brand1_now = data_brand1_now[(data_brand1_now["review_time_日期"] >= start_now) & (data_brand1_now["review_time_日期"] <= end_now)]

        data_brand2_now = data[data["品牌"] == option_競品2]
        data_brand2_now = data_brand2_now[(data_brand2_now["review_time_日期"] >= start_now) & (data_brand2_now["review_time_日期"] <= end_now)]

        data_品牌 = data_now[data_now["品牌"] == brand]
        df = pd.concat([data_品牌,data_brand1_now],axis = 0)
        df = pd.concat([df,data_brand2_now],axis = 0)
        # -*- coding: utf-8 -*-
        df_經緯度 = pd.read_csv("gmap店點經緯度.csv")
   
        df["lon"] = [i.split('@')[1].split(",")[1] for i in df['url']]
        df["lat"] = [i.split('@')[1].split(",")[0] for i in df['url']]
        
        df_gmap聲量 = df.groupby('name',as_index = False).sum()[['name','聲量']]
        
        df_gmap聲量 = pd.merge(df_gmap聲量,df[['name','lon','lat','品牌']],on = 'name').drop_duplicates()
        
        df_gmap聲量.reset_index(drop = True,inplace = True)
        df_gmap聲量.rename(columns = {'聲量':'volume'})
        df_gmap聲量['lon'] = pd.to_numeric(df_gmap聲量['lon'])
        df_gmap聲量['lat'] = pd.to_numeric(df_gmap聲量['lat'])

        fig = px.scatter_mapbox(df_gmap聲量, size = '聲量',lat="lat", lon="lon", zoom = 6.15,width = 350,height = 500,color = '品牌',
                                center = dict(lon = 120.9876,lat = 23.83876 ),
                                color_discrete_map = {
                            f"{brand}": "#55B576",
                            f"{option_競品1}": "#FF5E5E",
                            f"{option_競品2}": "#20AFDC"},category_orders = {'品牌':[brand,option_競品1,option_競品2]})
        fig.update_layout(mapbox_style = 'carto-positron',margin = {'r':0,'t':0,'l':0,'b':0})
        st.plotly_chart(fig)
        
        st.subheader("評論清單")
        option_情緒 = st.radio("選擇一種情緒:",('全部', '正向','負向',"中性"))
        if option_情緒 == "全部":
            data_品牌_now = data_now[data_now["品牌"] == brand]
            data = data_品牌_now[["品牌","name","review_time_日期","content","Preds"]]
            data.columns = ["品牌","Google Map 名稱","日期","評論內容","情緒"]
            data.reset_index(drop = True,inplace = True)
            st.dataframe(data)

        else:
            data_品牌_now = data_now[data_now["品牌"] == brand]
            data = data_品牌_now[["品牌","name","review_time_日期","content","Preds"]]
            data = data[data["Preds"] == option_情緒]
            data.columns = ["品牌","Google Map 名稱","日期","評論內容","情緒"]
            data.reset_index(inplace = True,drop = True)
            st.dataframe(data)


with tab2:
    with st.form('my_form2'):
        left_col, right_col = st.columns(2)
        st.write("**時間區間:**")
        with left_col:
            start_now = st.date_input("**開始時間**",datetime.date(2023, 4, 1))

        with right_col:
            end_now = st.date_input("**結束時間**",datetime.date(2023, 4, 30))
        
        option_社群 = st.selectbox("選擇社群來源",["PTT","Dcard"])
        st.write(" ")
        st.write("**輸入自選關鍵字:**")
        col1,col2,col3,col4 = st.columns(4)
        with col1:
            text1 = st.text_input("關鍵字1","研究所")
            text1 = str(text1)
        with col2:
            text2 = st.text_input("關鍵字2","")
            text2 = str(text2)
        with col3:
            text3 = st.text_input("關鍵字3","")
            text3 = str(text3)
        with col4:
            text4 = st.text_input("關鍵字4","")
        text4 = str(text4)
        submitted = st.form_submit_button("提交")
    if submitted:
        start_now = start_now
        end_now = end_now
        option_社群 = option_社群
        text1 = text1
        text2 = text2
        text3 = text3
        text4 = text4

    if option_社群 == "PTT":
        data = df_ptt
        data = data[(data["created_at_日期"] >= start_now) \
                    & (data["created_at_日期"] <= end_now)]
        data.reset_index(inplace = True,drop = True)
    else:
        data = df_dcard
        data = data[(data["created_at_日期"] >= start_now) \
                    & (data["created_at_日期"] <= end_now)]
        data.reset_index(inplace = True,drop = True)

    
    data1 = app_functions.find_article(text1,data)
    data2 = app_functions.find_article(text2,data)
    data3 = app_functions.find_article(text3,data)
    data4 = app_functions.find_article(text4,data)

    df = pd.concat([data1,data2],axis = 0)
    df = pd.concat([df,data3],axis = 0)
    df = pd.concat([df,data4],axis = 0)
    

    df = df.groupby(["created_at_日期","關鍵字",'board'],as_index = False).sum("聲量")

    st.subheader("聲量")
    fig = px.line(df, x="created_at_日期", y="聲量",color = "關鍵字",
                  color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(
                    xaxis_title = "日期",
                    yaxis_title = "聲量"
                    )
    
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("文字雲")

    stopwords = []
    f = open('cn_stopwords.txt','r',encoding="utf-8")
    for line in f.readlines():
        line = line.replace("\n","")
        stopwords.append(line)

    def 判斷是否有資料(data,text,count):
            if len(data) != 0:
                app_functions.wordcloud_chart(count)
            else:
                st.write(text)
   
    def 斷詞_文字雲(data,text):
        df = app_functions.find_article(text,data)
        斷詞_data = app_functions.文章斷詞(df)
        count = app_functions.words_counts(斷詞_data,df)
        st.write(f"**{text}**")
        判斷是否有資料(斷詞_data,"",count)
        
    text_list = [text1,text2,text3,text4]
    text_list = list(filter(lambda x: x != '',text_list))
    for i in text_list:
        if (i == "") or (i =='  ') or (i == '   ') or (i == '    '):
            text_list.remove(i)
            

    n_text_list = len(text_list)

    if n_text_list == 4:
        col1, col2 = st.columns(2)
        with col1:
            斷詞_文字雲(data,text_list[0])
        with col2:
            斷詞_文字雲(data,text_list[1])

        col1, col2 = st.columns(2)
        with col1:
            斷詞_文字雲(data,text_list[2])
        with col2:
            斷詞_文字雲(data,text_list[3])
    elif n_text_list == 3:
        col1, col2 = st.columns(2)
        with col1:
            斷詞_文字雲(data,text_list[0])
        with col2:
            斷詞_文字雲(data,text_list[1])

        col1, col2 = st.columns(2)
        with col1:
            斷詞_文字雲(data,text_list[2])
        with col2:
            st.write("")
    elif n_text_list == 2:
        col1, col2 = st.columns(2)
        with col1:
            斷詞_文字雲(data,text_list[0])
        with col2:
            斷詞_文字雲(data,text_list[1])
    else:
        col1, col2 = st.columns(2)
        with col1:
            斷詞_文字雲(data,text_list[0])
        with col2:
            st.write("")
        
    st.subheader("看板分佈")
    
    dff = df.groupby(["board","關鍵字"],as_index = False).sum("聲量")
    dff = dff.sort_values(by = '聲量',ascending = False)
    fig = px.bar(dff,x = "board",y ="聲量",color = "關鍵字",barmode="group",
                      color_discrete_sequence=px.colors.qualitative.Set2,
                      text_auto=True)
    fig.update_layout(
            title = f"關鍵字看板分佈",
            xaxis_title="看板",
            yaxis_title="聲量",
            legend_title="關鍵字",
            font=dict(size=14)
        )
    fig.update_traces(textposition = 'auto',textfont_size=12)
    st.plotly_chart(fig,use_container_width = True)
    
    st.subheader("正負文章數")
    
    df["文章情緒"] = df[["正向","中性","負向"]].idxmax(axis = 1).to_frame()[0]
    df = df.groupby(["文章情緒","關鍵字"],as_index = False).sum("看板數量")
    df = df.sort_values(by = '看板數量',ascending = False)
    fig = px.bar(df,x = "關鍵字",y = "看板數量",color = "文章情緒",text_auto = True,
                        barmode="group",
                        color_discrete_map = {
                    "正向": "#A0C8AD",
                    "負向": "#F94D4D",
                    "中性": "#FEB62A"})
    fig.update_layout(
                xaxis_title = "關鍵字",
                yaxis_title = "聲量",
                legend_title = "情緒",
                font=dict(size=14))
    
    st.plotly_chart(fig)
    
    st.subheader("文章清單")
    col1,col2 = st.columns(2)
    with col1:
        option_關鍵字 = st.radio("選擇關鍵字:",set(text_list))
    with col2:
        option_情緒 = st.radio("選擇一個情緒:",("正向","負向","中性","全選"))

    df = pd.concat([data1,data2],axis = 0)
    df = pd.concat([df,data3],axis = 0)
    df = pd.concat([df,data4],axis = 0)

    data = df.rename(columns = {"created_at_日期":"日期"})
    data = data[data["關鍵字"] == option_關鍵字]
    if option_情緒 == '全選':
        data = data
    else:
        data = data[data["文章情緒"] == option_情緒]

    data["互動數"] = data["like_count"] + data["comment_count"]
    data["管道"] = "PTT"
    data["正向情緒"] = [0 if i == "無" else int(i)  for i in data["正向"]]
    data["負向情緒"] = [0 if i == "無" else int(i) for i in data["負向"]]
    data["中性情緒"] = [0 if i == "無" else int(i) for i in data["中性"]]
    data["文章情緒"] = data[["正向情緒","負向情緒","中性情緒"]].idxmax(axis = 1).to_frame()[0]
    data["文章情緒"] = [i.replace("情緒","") for i in data["文章情緒"]]
    data = data[["關鍵字","管道","日期","title","board","互動數","content","文章情緒"]]
    data = data[data["關鍵字"] == option_關鍵字]
    data.reset_index(drop = True,inplace = True)
    st.dataframe(data)


with tab3:
    st.subheader("熱門文章")
    today = datetime.date.today()
    delta = timedelta(days=30)   
    start = str(today-delta)
    df_ptt_db = pd.read_csv('df_ptt_db.csv')
    board_list = df_ptt_db["board"].unique()

    for i in range(len(df_ptt_db["board"].unique())):
        if i == 0:
            data = df_ptt_db.groupby("board").get_group(board_list[i]).sort_values("互動數",ascending = False)
            data.reset_index(inplace = True,drop = True)
            df = data.iloc[0].to_frame().T
        else:
            data = df_ptt_db.groupby("board").get_group(board_list[i]).sort_values("互動數",ascending = False)
            data.reset_index(inplace = True,drop = True)
            df2 = data.iloc[0].to_frame().T
            df = pd.concat([df,df2],axis = 0)
    data = df[["board","title","日期","content","互動數"]]
    data.columns = ["看板","文章標題","日期","文章內容","互動數"]
    data.reset_index(inplace = True,drop = True)
    st.dataframe(data)
    with st.expander("說明"):
            st.write("1. 滑鼠點兩下可看到資料格全貌 \n 2. 滑鼠選取部分範圍可以複製貼上到 Libre Office 或是 google sheet \n 3. 可以自行調整欄寬 \n 4. 按住 Ctrl F 可以搜尋資料 \n 5. 右下角可以縮放資料表 \n 6. 點擊欄位名稱可以遞增或遞減排序")

with tab4:

    data_詞庫 = pd.read_csv('data_詞庫.csv')
    for i in data_詞庫.columns:
        if 'Unnamed' in i:
            data_詞庫.drop(i,axis = 1,inplace = True)
    edited = st.experimental_data_editor(data_詞庫, num_rows="dynamic",use_container_width = True)

    if st.button('編輯完成'):
        try:
            edited.to_csv('new_詞庫')
            st.success("詞庫更新成功")
            time.sleep(5)
        except:
            st.warning("詞庫尚未更新成功")
        st.experimental_rerun()

