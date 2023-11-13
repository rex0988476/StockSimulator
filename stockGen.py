import random
import nltk
nltk.download('words')
from nltk.corpus import words

GENERATE_STOCK_NUM=100

#Implicit parameter of stock:
#1.weight :stock每次漲跌單位價錢 range(1,10)
#2.max_up_unit :stock每次漲最大單位 range(1,5)
#3.max_down_unit :stock每次跌最大單位 range(-5,-1)
#公式:new stock price = cur_price + weight * random.randint(max_down_unit,max_up_unit)
#4.update_time_weight: 更新一次weight的時間 range(1,30)
#5.update_time_max_up_unit: 更新一次max_up_unit的時間 range(1,30)
#6.update_time_max_down_unit: 更新一次max_down_unit的時間 range(1,30)
#7.cur_time_weight: weight剩餘更新時間
#8.cur_time_max_up_unit: max_up_unit剩餘更新時間
#9.cur_time_max_down_unit: max_down_unit剩餘更新時間

#status: 股票狀態(-,下市)
#cooldown_time: 重新上市剩餘冷卻時間


# 下載英文單詞列表
english_words = words.words()

# 隨機生成不重複的10000個英文名詞
#random.seed(42)  # 設定種子以確保結果可複製
unique_nouns = set()

while len(unique_nouns) < 10000:
    word = random.choice(english_words)
    if word.isalpha() and len(word)<=15:
        unique_nouns.add(word.lower())

# 將不重複的名詞轉換為列表
unique_nouns_list = list(unique_nouns)

f=open('STOCKS','w')
i=0
while i<GENERATE_STOCK_NUM:
    id=""
    if len(str(i))==1:
        id="000"+str(i)
    elif len(str(i))==2:
        id="00"+str(i)
    elif len(str(i))==3:
        id="0"+str(i)
    else:
        id=str(i)
    price=random.randint(500,1500)
    weight=random.randint(1,10)
    max_up_unit=random.randint(1,5)
    max_down_unit=random.randint(-5,-1)
    update_time_weight=random.randint(1,30)
    update_time_max_up_unit=random.randint(1,30)
    update_time_max_down_unit=random.randint(1,30)
    cur_time_weight=update_time_weight
    cur_time_max_up_unit=update_time_max_up_unit
    cur_time_max_down_unit=update_time_max_down_unit
    #stock_id,stock_name,stock_price,weight,max_up_unit,max_down_unit,update_time_weight,update_time_max_up_unit,update_time_max_down_unit,stock_price1-stock_price2-stock_price3-stock_price4-stock_price5-stock_price6-stock_price7-stock_price8-stock_price9-stock_price10,status(delisting,-),cooldown_time,buy,sell,trading_volume
    f.write(f"{id},{unique_nouns_list[i]},{price},{weight},{max_up_unit},{max_down_unit},{update_time_weight},{update_time_max_up_unit},{update_time_max_down_unit},{cur_time_weight},{cur_time_max_up_unit},{cur_time_max_down_unit},{price}-{price}-{price}-{price}-{price}-{price}-{price}-{price}-{price}-{price},-,10,0,0,0\n")
    i+=1
f.close()
