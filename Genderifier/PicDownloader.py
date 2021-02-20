import pandas as pd
from sqlalchemy import create_engine

from Instagram import Instagram
import matplotlib.pyplot as plt
import os


db = create_engine('postgresql://postgres:kzu7@localhost/Lineless')

def request_sql(query, db):
    return pd.read_sql(query, db)

sql_command = """
    SELECT 
        *
    FROM
        pixelline.follows
"""
follower_df = request_sql(sql_command, db)

print(follower_df.head())

username = 'underfcuk'
pwd = 'atleastitried'
API = Instagram(username, pwd)
API.login()

x = API.getUserInfo(1044434874)
print(x)








