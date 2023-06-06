import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import wordcloud
import matplotlib.pyplot as plt
import re
import numpy as np

def drop_unnamed_column(data):
    unnamed_list = []
    for i in data.columns:
        if "Unnamed" in i:
            unnamed_list.append(i)
    for i in unnamed_list:
        data.drop(i,axis = 1,inplace = True)


def replace_無(data):
    data["正向情緒"] = [int(0) if i == "無" else int(i) for i in data["正向情緒"]]
    data["負向情緒"] = [int(0) if i == "無" else int(i) for i in data["負向情緒"]]
    data["中性情緒"] = [int(0) if i == "無" else int(i) for i in data["中性情緒"]]
    data.rename(columns = {"正向情緒":"正向", "負向情緒":"負向", "中性情緒":"中性"},inplace = True)
    data["正向"] = pd.to_numeric(data["正向"])
    data["負向"] = pd.to_numeric(data["負向"])
    data["中性"] = pd.to_numeric(data["中性"])
    data["看板數量"] = 1
    return data

def change_column_type(data,column):
    data[column] = pd.to_datetime(data[column], format="%Y-%m-%d")
    data[column] = data[column].dt.date

def find_品牌(data,品牌,管道):
    data_品牌 = data[data["品牌"] == 品牌]["文章情緒"].value_counts().to_frame()
    data_品牌 = data_品牌.rename(columns = {"文章情緒":"數量"})
    data_品牌["文章情緒"] = data_品牌.index
    data_品牌.reset_index(drop = True,inplace = True)
    data_品牌["管道"] = 管道
    total = data_品牌["數量"].sum()
    data_品牌["比例"] = 0
    for i in range(len(data_品牌)):
        data_品牌["比例"][i] = round(int(data_品牌["數量"][i])/total,2)*100
    return data_品牌


def find_gmap品牌(df_gmap,品牌):
    df_gmap_品牌 = df_gmap[df_gmap["品牌"] == 品牌]["Preds"].value_counts().to_frame()
    df_gmap_品牌 = df_gmap_品牌.rename(columns = {"Preds":"數量"})
    if "衝突" in df_gmap_品牌.index:
        df_gmap_品牌.loc["正向"] += df_gmap_品牌.loc["衝突"]
        df_gmap_品牌.loc["負向"] += df_gmap_品牌.loc["衝突"]
    df_gmap_品牌["文章情緒"] = df_gmap_品牌.index
    if "衝突" in df_gmap_品牌.index:
        df_gmap_品牌 = df_gmap_品牌.drop("衝突",axis = 0)
    df_gmap_品牌.reset_index(drop = True,inplace = True)
    df_gmap_品牌["管道"] = "gmap"
    total = df_gmap_品牌["數量"].sum()
    df_gmap_品牌["比例"] = 0
    for i in range(len(df_gmap_品牌)):
        df_gmap_品牌["比例"][i] = round(int(df_gmap_品牌["數量"][i])/total,2)*100
    return df_gmap_品牌


def find_品牌情緒(df_ptt,df_dcard,df_gmap,品牌):
    # 篩選出特定品牌
    df_dcard_品牌 = find_品牌(df_dcard,品牌,"Dcard")
    df_ptt_品牌 = find_品牌(df_ptt,品牌,"PTT")
    df_gmap_品牌 = find_gmap品牌(df_gmap,品牌)
    
    df_品牌_情緒 = pd.concat([df_dcard_品牌,df_ptt_品牌], axis = 0)
    df_品牌_情緒 = pd.concat([df_品牌_情緒,df_gmap_品牌], axis = 0)
    df_品牌_情緒.reset_index(drop = True,inplace = True)
    df_品牌_情緒.drop_duplicates()
    return df_品牌_情緒

def create_date(start_now,end_now):
    start_now = str(start_now)
    end_now = str(end_now)
    start_date = datetime(int(float(start_now.split("-")[0])), int(float(start_now.split("-")[1]))
                          , int(float(start_now.split("-")[2])))   # 起始日期
    end_date = datetime(int(float(end_now.split("-")[0])), int(float(end_now.split("-")[1]))
                        , int(float(end_now.split("-")[2])))   # 結束日期
    delta = timedelta(days=1)          # 每次增加一天

    current_date = start_date          # 設定當前日期為起始日期
    date_list = []
    while current_date <= end_date:
        date_list.append(current_date.strftime('%Y-%m-%d'))
        current_date += delta
    data = pd.DataFrame(date_list,columns = ["日期"])
    data["聲量"] = 0
    return data

def match_聲量(df,data):
    for i in range(len(df)):
        for j in range(len(data)):
            if str(df["created_at_日期"][i]).split(" ")[0] == str(data["日期"][j]):
                data["聲量"][j] = df["聲量"][i]
    return data

def date_range(start_now,end_now,start_choose,end_choose):
    start_now = str(start_now)
    end_now = str(end_now)
    start_choose = str(start_choose)
    end_choose = str(end_choose)

    datetime1 = datetime(int(float(start_now.split("-")[0])), int(float(start_now.split("-")[1])), int(float(start_now.split("-")[2])))
    datetime2 = datetime(int(float(end_now.split("-")[0])), int(float(end_now.split("-")[1])), int(float(end_now.split("-")[2])))
    delta1 = datetime2 - datetime1
    datetime3 = datetime(int(float(start_choose.split("-")[0])), int(float(start_choose.split("-")[1])), int(float(start_choose.split("-")[2])))
    datetime4 = datetime(int(float(end_choose.split("-")[0])), int(float(end_choose.split("-")[1])), int(float(end_choose.split("-")[2])))
    delta2 = datetime4 - datetime3
    return delta1,delta2


def create_chart_dataframe(voice,filter_data,df):
    if len(voice) == 0:
        filter_data["聲量"] = 0
    else:
        voice = df.groupby("created_at_日期").sum().reset_index()[["created_at_日期","聲量"]]
        filter_data = match_聲量(voice,filter_data)


def selectbox(brand,title,title1,title2):
    if brand == "大碩":
        col1, col2 = st.columns(2)
        with col1:
            option_競品1 = st.selectbox(f"{title}:**{brand}**，{title1}:",("偉文",'偉文', '高點',"不選擇"))
        with col2:
            option_競品2 = st.selectbox(f"{title}:**{brand}**，{title2}:",("高點",'偉文', '高點',"不選擇"))
    elif brand == "洋碩":
        col1, col2 = st.columns(2)
        with col1:
            option_競品1 = st.selectbox(f"{title}:**{brand}**，{title1}:",("巨匠",'巨匠',"菁英","字神帝國","不選擇"))
        with col2:
            option_競品2 = st.selectbox(f"{title}:**{brand}**，{title2}:",("菁英",'巨匠',"菁英","字神帝國","不選擇"))
    elif brand == "百官":
        col1, col2 = st.columns(2)
        with col1:
            option_競品1 = st.selectbox(f"{title}:**{brand}**，{title1}:",("三民",'志光',"三民","公職王","不選擇"))
        with col2:
            option_競品2 = st.selectbox(f"{title}:**{brand}**，{title2}:",("志光",'志光',"三民","公職王","不選擇"))
    elif brand == "放洋":
        col1, col2 = st.columns(2)
        with col1:
            option_競品1 = st.selectbox(f"{title}:**{brand}**，{title1}:",("留學家",'留學家',"不選擇"))
        with col2:
            option_競品2 = st.selectbox(f"{title}:**{brand}**，{title2}:",("不選擇",'留學家',"不選擇"))
    elif brand == "甄戰":
        col1, col2 = st.columns(2)
        with col1:
            option_競品1 = st.selectbox(f"{title}:**{brand}**，{title1}:",("樂學網",'樂學網',"不選擇"))
        with col2:
            option_競品2 = st.selectbox(f"{title}:**{brand}**，{title2}:",("不選擇",'樂學網',"不選擇"))
    elif brand == "龍門":
        col1, col2 = st.columns(2)
        with col1:
            option_競品1 = st.selectbox(f"{title}:**{brand}**，{title1}:",("偉文","偉文","不選擇"))
        with col2:
            option_競品2 = st.selectbox(f"{title}:**{brand}**，{title2}:",("不選擇","偉文","不選擇"))
    elif brand == '學堂':
        col1, col2 = st.columns(2)
        with col1:
            option_競品1 = st.selectbox(f"{title}:**{brand}**，{title1}:",("志光",'志光',"不選擇"))
        with col2:
            option_競品2 = st.selectbox(f"{title}:**{brand}**，{title2}:",("不選擇","志光","不選擇"))

    return option_競品1,option_競品2


def replace(data):
    data = re.sub(r"http\S+", "", data)
    data = re.sub(r'[^\w\s]', '', data)
    data = re.sub(r'[\r\n]+|(\r\n)+', '', data)
    data = re.sub(r'\d+', '', data)
    return data

def 文章斷詞(data):
    n = 0
    斷詞結果_list = []
    if data is None:
        return []
    else:
        for i in data.index:
            if n == 0:
                斷詞結果_list = replace(data["斷詞結果"][i]).split(" ")
                n+=1
            else:
                new_list = replace(data["斷詞結果"][i]).split(" ")
                for j in new_list:
                    斷詞結果_list.append(j)
                n+=1
        return 斷詞結果_list

def read_stopwords():
    stopwords = []
    f = open('cn_stopwords.txt')
    for line in f.readlines():
        line = line.replace("\n","")
        stopwords.append(line)
    return stopwords

stopwords = read_stopwords()

def words_counts(斷詞_list,data):
    斷詞_list = 文章斷詞(data)
    斷詞_newlist = []
    for i in 斷詞_list:
        if (i not in stopwords) & (len(i) > 1):
            斷詞_newlist.append(i)
            
    words = 斷詞_newlist
    counts = {}
    for word in words:  
        counts[word] = counts.get(word,0) + 1  
    items = list(counts.items())  
    items.sort(key=lambda x:x[1], reverse=True)   
    return counts

def wordcloud_chart(counts):
    fig = plt.subplots()
    wc = wordcloud.WordCloud(
      background_color='white',        
      max_words=60,                   
      mask=None,                      
      max_font_size=None,               
      font_path= "SimHei.ttf",             
      stopwords = stopwords,
      random_state=None,               
      scale = 3,
      width = 400,
      height = 240)           
    wc.generate_from_frequencies(counts)  
    fig, ax = plt.subplots()
    ax.imshow(wc, interpolation = 'bilinear')
    plt.axis('off')
    st.pyplot(fig)

def rating(brand,n,data):
    name_list = data["name"].unique()
    df = pd.DataFrame(data.groupby("name").get_group(name_list[n]).value_counts("rating"))
    df = df.rename(columns = {0:"數量"})
    df["星等數"] = df.index
    df.reset_index(inplace = True,drop = True)
    df["name"] = name_list[n]
    df["品牌"] = brand
    return df


def rating_data(data,brand):
    for i in range(len(data["name"].unique())):
        if i == 0:
            data1 = rating(brand,i,data)
        else:
            data2 = rating(brand,i,data)
            data1 = pd.concat([data1,data2],axis = 0)
    df = data1
    df["星等數"] = df["星等數"].astype(str)
    return df

def gmap_文字雲_2(data_品牌,店點_list,i,j):
    col1,col2 = st.columns(2)
    with col1:
        st.write(f"**{店點_list[i]}**")
        data_品牌_店點 = data_品牌[data_品牌["name"] == 店點_list[i]]
        斷詞_品牌 = 文章斷詞(data_品牌_店點)
        counts_品牌 = words_counts(斷詞_品牌,data_品牌_店點)
        wordcloud_chart(counts_品牌)
    with col2:
        st.write(f"**{店點_list[j]}**")
        data_品牌_店點 = data_品牌[data_品牌["name"] == 店點_list[j]]
        斷詞_品牌 = 文章斷詞(data_品牌_店點)
        counts_品牌 = words_counts(斷詞_品牌,data_品牌_店點)
        wordcloud_chart(counts_品牌)

def gmap_文字雲_1(data_品牌,店點_list,i):
    col1,col2 = st.columns(2)
    with col1:
        st.write(f"**{店點_list[i]}**")
        data_品牌_店點 = data_品牌[data_品牌["name"] == 店點_list[i]]
        斷詞_品牌 = 文章斷詞(data_品牌_店點)
        counts_品牌 = words_counts(斷詞_品牌,data_品牌_店點)
        wordcloud_chart(counts_品牌)
    with col2:
        st.write(" ")

def find_品牌_評論(data,brand,時間):
    data = data[data["品牌"] == brand]
    data = data.groupby("name").sum()[["評論數"]]
    data["name"] = data.index
    data = data.reset_index(drop = True)
    data["時間"] = 時間
    return data

def remove_衝突(data_品牌):
    data1 = data_品牌[data_品牌["Preds"] == "衝突"]
    data_品牌["Preds"] = ["正向" if i == "衝突" else i for i in data_品牌["Preds"]]
    data1["Preds"] = ["正向" if i == "衝突" else i for i in data1["Preds"]]
    data_品牌 = pd.concat([data_品牌,data1],axis = 0)
    data_品牌.reset_index(drop = True,inplace = True)
    return data_品牌

def find_article(text,data):
    if (text == '') or (text == ' ') or (text == '  ') or (text == '   '):
        data1 = None
    else:
        content_list = []
        for i in range(len(data)):
            if (text in str(data["content"][i])) or (text in str(data["title"][i])):
                content_list.append(i)
        data1 = data.iloc[content_list].reset_index(drop = True)
        data1["聲量"] = 1
        data1["關鍵字"] = text
    return data1

def remove(data,品牌):
    remove_中性 = [ ]
    for i in range(len(data)):
        if data["文章情緒"][i] == '中性':
            continue
        else:
            remove_中性.append(i)
    data["品牌"] = str(品牌)
    return data.iloc[remove_中性].reset_index(drop = True)

def replace_nan(data,column):
    for i in range(len(data)):
        if np.isnan(data[column][i]):
            data[column][i] = 0