import pandas as pd
import pymysql

# def read_data(path):
#     data = pd.read_csv(path)
#     return data
# df_dcard = read_data("data/dcard_data_update.csv")
# df_gmap = read_data("data/gmap_data_update.csv")
# df_ptt = read_data("data/ptt_data_update.csv")
# print(len(df_ptt))
# df_dcard = df_dcard[(df_dcard['created_at_日期'] <= '2022-09-31') & (df_dcard['created_at_日期'] >= '2022-09-01')]
# df_gmap = df_gmap[(df_gmap['review_time_日期'] >= '2023-04-01') & (df_gmap['review_time_日期'] <= '2023-04-30')]
# df_ptt = df_ptt[(df_ptt['created_at_日期'] >= '2023-04-01') & (df_ptt['created_at_日期'] <= '2023-04-30')]

# df_dcard.to_csv('demo_data/dcard_demo_data.csv')
# df_ptt.to_csv('demo_data/ptt_demo_data.csv')
# df_gmap.to_csv('demo_data/gmap_demo_data.csv')


conn = pymysql.connect(host = "122.147.5.184",user = "tkb0004308",password = "eeoFU1DdmvmTxwu",port = 33062,database = "network_g")
df_ptt_board = pd.read_sql("SELECT * FROM ptt_board;",conn)
df_ptt_db = pd.read_sql(f"SELECT * FROM network_g.ptt_article  WHERE DATE(created_at) > '2023-04-29' AND DATE(created_at) <= '2023-04-30';",con = conn)

df_ptt_db["互動數"] = df_ptt_db["dislike_count"] + df_ptt_db["neutral_count"] +\
df_ptt_db["like_count"]+ df_ptt_db["comment_count"]
df_ptt_db["日期"] = [str(i).split(" ")[0] for i in df_ptt_db["created_at"]]
df_ptt_db.to_csv('df_ptt_db.csv')
print(df_ptt_db)