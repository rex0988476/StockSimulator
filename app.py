from PyQt5 import QtGui, QtWidgets, QtCore
import sys
import os
import random
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.pyplot import MultipleLocator
import GLOBAL
#save txt data type
#money
#stock type num 
#stock name1, stock num1, stock price1
#stock name2, stock num2, stock price2
#...
#買: 輸入id, 會有正在賣的列表, 輸入要買的單價跟張數就可以買
#賣: 輸入要賣的id跟張數, 推到列表等待機器人(或自己)買
#關母畫面自動save+關所有子畫面
#wait
#buy_stock或許不用account
#中途換帳號/建帳號可選之前的原帳號要不要save
TOTAL_STOCK_NUM=GLOBAL.TOTAL_STOCK_NUM
ACCOUNT_INIT_MONEY=GLOBAL.ACCOUNT_INIT_MONEY
SINGLE_PAGE_STOCK_NUM=GLOBAL.SINGLE_PAGE_STOCK_NUM
ACCOUNT=GLOBAL.ACCOUNT
BUTTON_TEXT_10_SPACE=GLOBAL.BUTTON_TEXT_10_SPACE
STOCK_PRICE_UPDATE_TIME=GLOBAL.STOCK_PRICE_UPDATE_TIME
ROBOT_UPDATE_TIME=GLOBAL.ROBOT_UPDATE_TIME
ROBOT_BUY_PROBABILITY=GLOBAL.ROBOT_BUY_PROBABILITY
ROBOT_SELL_PROBABILITY=GLOBAL.ROBOT_SELL_PROBABILITY
PRINT_ROBOT_SIGNAL=GLOBAL.PRINT_ROBOT_SIGNAL
PRINT_STOCK_IMPLICIT_PARAMETER_UPDATE_NUM=GLOBAL.PRINT_STOCK_IMPLICIT_PARAMETER_UPDATE_NUM
class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Stock Simulator')
        self.width_=1600
        self.height_=900
        self.resize(self.width_, self.height_)
        self.style()
        self.start_ui()
        self.my_money=0
        self.stocks_list=[]
        f=open('STOCKS','r')
        i=0
        while i<TOTAL_STOCK_NUM:
            stock=f.readline()
            #stock_price1-stock_price2-stock_price3-stock_price4-stock_price5-stock_price6-stock_price7-stock_price8-stock_price9-stock_price10
            stock_price_history=stock.split(',')[12].split('-')
            j=0
            while j<len(stock_price_history):
                stock_price_history[j]=int(stock_price_history[j])
                j+=1
            #stock_id,stock_name,stock_price,weight,max_up_unit,max_down_unit,update_time_weight,update_time_max_up_unit,update_time_max_down_unit,cur_time_weight,cur_time_max_up_unit,cur_time_max_down_unit,status(delisting,-),cooldown_time,buy,sell,trading_volume
            self.stocks_list.append({"stock_id":stock.split(',')[0],
                                     "stock_name":stock.split(',')[1],
                                     "stock_price":int(stock.split(',')[2]),
                                     "weight":int(stock.split(',')[3]),
                                     "max_up_unit":int(stock.split(',')[4]),
                                     "max_down_unit":int(stock.split(',')[5]),
                                     "update_time_weight":int(stock.split(',')[6]),
                                     "update_time_max_up_unit":int(stock.split(',')[7]),
                                     "update_time_max_down_unit":int(stock.split(',')[8]),
                                     "cur_time_weight":int(stock.split(',')[9]),
                                     "cur_time_max_up_unit":int(stock.split(',')[10]),
                                     "cur_time_max_down_unit":int(stock.split(',')[11]),
                                     "stock_price_history":stock_price_history,
                                     "stock_status":stock.split(',')[13],
                                     "cooldown_time":int(stock.split(',')[14]),
                                     "buy":int(stock.split(',')[15]),
                                     "sell":int(stock.split(',')[16]),
                                     "trading_volume":int(stock.split(',')[17])
                                     })
            i+=1
        f.close()

        self.cur_page=1
        
        self.update_price_thread=Update_price_thread()
        self.update_price_thread.update_price_signal.connect(self.update_stocks)
        
        self.start_stock=False
        self.ui_buy=QtWidgets.QWidget()#for order problem
        self.ui_my_stock=QtWidgets.QWidget()#for order problem
        self.ui_create_new_account=QtWidgets.QWidget()#for order problem

        files=os.listdir("./data/history/")
        while len(files)>0:
            os.remove(f"./data/history/{files[0]}")
            del files[0]
        
        self.my_stocks_list=[]#{"stock_id":,"stock_name":,"num_and_price":[{"num":,"price":},...]}
        self.stock_trading_list=[]
        #{'stock_id',
        # 'buy_stock',[{'account':account1,'num':num1},{'account':account2,'num':num2},...]
        # 'sell_stock',[{'account':account1,'price':price1,'num':num1},{'account':account2,'price':price2,'num':num2},...]}
        i=0
        while i<len(self.stocks_list):
            self.stock_trading_list.append({'stock_id':self.stocks_list[i]['stock_id'],'buy_stock':[],'sell_stock':[]})
            self.my_stocks_list.append({"stock_id":self.stocks_list[i]['stock_id'],"stock_name":self.stocks_list[i]['stock_name'],"num_and_price":[]})
            i+=1

        self.robot_thread_list=[]
        i=0
        while i<1:
            robot_thread=Robot_thread()
            robot_thread.robot_signal.connect(self.robot_manager)
            self.robot_thread_list.append(robot_thread)
            i+=1
        
        #self.tsell=0
        #self.tbuy=0
        
    def robot_manager(self,buy_sell_dict):
        self.save_robot_buy_sell_dict(buy_sell_dict)
        self.process_trading(buy_sell_dict['act_stock_index'])
        self.update_stocks_list_buy_sell(buy_sell_dict['act_stock_index'])

        if buy_sell_dict['act_stock_index'] in range(SINGLE_PAGE_STOCK_NUM*(self.cur_page-1),SINGLE_PAGE_STOCK_NUM*(self.cur_page)):
            self.update_main_window_stock_ui()
        
        if self.ui_buy.isVisible():
            if self.buy_window_stock_index==buy_sell_dict['act_stock_index']:
                self.update_buy_window_sell_list_ui()
        
    def save_robot_buy_sell_dict(self,buy_sell_dict):
        #buy_sell_dict:{'act','act_stock_index','act_stock_num'}
        act_stock_price=self.stocks_list[buy_sell_dict['act_stock_index']]['stock_price']
        if PRINT_ROBOT_SIGNAL:
            print(buy_sell_dict,",current price:",act_stock_price)
        #insert_index=0
        have_same=False
        if buy_sell_dict['act']=='buy':
            #self.tbuy+=buy_sell_dict['act_stock_num']
            #i=0
            #while i<len(self.stock_trading_list[buy_sell_dict['act_stock_index']]['buy_stock']):
                #if self.stock_trading_list[buy_sell_dict['act_stock_index']]['buy_stock'][i]['price']<=act_stock_price:
                #    insert_index=i+1
                #if self.stock_trading_list[buy_sell_dict['act_stock_index']]['buy_stock'][i]['account']=='ROBOT':
                #    have_same=True
                #    self.stock_trading_list[buy_sell_dict['act_stock_index']]['buy_stock'][i]['num']+=buy_sell_dict['act_stock_num']
                #    break
            #    i+=1
            #if not have_same:
                #self.stock_trading_list[buy_sell_dict['act_stock_index']]['buy_stock'].insert(insert_index,{'price':act_stock_price,'num':buy_sell_dict['act_stock_num']})
            self.stock_trading_list[buy_sell_dict['act_stock_index']]['buy_stock'].append({'account':'ROBOT','num':buy_sell_dict['act_stock_num']})
            
        elif buy_sell_dict['act']=='sell':
            #self.tsell+=buy_sell_dict['act_stock_num']
            i=0
            while i<len(self.stock_trading_list[buy_sell_dict['act_stock_index']]['sell_stock']):
                #if self.stock_trading_list[buy_sell_dict['act_stock_index']]['sell_stock'][i]['price']<=act_stock_price:
                #    insert_index=i+1
                if self.stock_trading_list[buy_sell_dict['act_stock_index']]['sell_stock'][i]['account']=="ROBOT" and self.stock_trading_list[buy_sell_dict['act_stock_index']]['sell_stock'][i]['price']==act_stock_price:
                    have_same=True
                    self.stock_trading_list[buy_sell_dict['act_stock_index']]['sell_stock'][i]['num']+=buy_sell_dict['act_stock_num']
                    break
                i+=1
            if not have_same:
                #self.stock_trading_list[buy_sell_dict['act_stock_index']]['sell_stock'].insert(insert_index,{'price':act_stock_price,'num':buy_sell_dict['act_stock_num']})
                self.stock_trading_list[buy_sell_dict['act_stock_index']]['sell_stock'].append({'account':'ROBOT','price':act_stock_price,'num':buy_sell_dict['act_stock_num']})
        #print("tbuy:",self.tbuy,"tsell:",self.tsell,"total:",min(self.tbuy,self.tsell))

    def process_trading(self,current_acting_stock_index):
        trading_volume=0
        while len(self.stock_trading_list[current_acting_stock_index]['buy_stock'])>0 and len(self.stock_trading_list[current_acting_stock_index]['sell_stock'])>0:
            money=0
            if self.stock_trading_list[current_acting_stock_index]['buy_stock'][0]['num']>self.stock_trading_list[current_acting_stock_index]['sell_stock'][0]['num']:
                #if self.stock_trading_list[current_acting_stock_index]['buy_stock'][0]['account']==ACCOUNT:
                #    pass
                if self.stock_trading_list[current_acting_stock_index]['sell_stock'][0]['account']==ACCOUNT:
                    money=self.stock_trading_list[current_acting_stock_index]['sell_stock'][0]['price']*self.stock_trading_list[current_acting_stock_index]['sell_stock'][0]['num']*1000
                trading_volume+=self.stock_trading_list[current_acting_stock_index]['sell_stock'][0]['num']
                self.stock_trading_list[current_acting_stock_index]['buy_stock'][0]['num']-=self.stock_trading_list[current_acting_stock_index]['sell_stock'][0]['num']
                del self.stock_trading_list[current_acting_stock_index]['sell_stock'][0]
            elif self.stock_trading_list[current_acting_stock_index]['buy_stock'][0]['num']<self.stock_trading_list[current_acting_stock_index]['sell_stock'][0]['num']:
                #if self.stock_trading_list[current_acting_stock_index]['buy_stock'][0]['account']==ACCOUNT:
                #    pass
                if self.stock_trading_list[current_acting_stock_index]['sell_stock'][0]['account']==ACCOUNT:
                    money=self.stock_trading_list[current_acting_stock_index]['sell_stock'][0]['price']*self.stock_trading_list[current_acting_stock_index]['buy_stock'][0]['num']*1000
                trading_volume+=self.stock_trading_list[current_acting_stock_index]['buy_stock'][0]['num']
                self.stock_trading_list[current_acting_stock_index]['sell_stock'][0]['num']-=self.stock_trading_list[current_acting_stock_index]['buy_stock'][0]['num']
                del self.stock_trading_list[current_acting_stock_index]['buy_stock'][0]
            else:
                #if self.stock_trading_list[current_acting_stock_index]['buy_stock'][0]['account']==ACCOUNT:
                #    pass
                if self.stock_trading_list[current_acting_stock_index]['sell_stock'][0]['account']==ACCOUNT:
                    money=self.stock_trading_list[current_acting_stock_index]['sell_stock'][0]['price']*self.stock_trading_list[current_acting_stock_index]['sell_stock'][0]['num']*1000
                trading_volume+=self.stock_trading_list[current_acting_stock_index]['sell_stock'][0]['num']
                del self.stock_trading_list[current_acting_stock_index]['sell_stock'][0]
                del self.stock_trading_list[current_acting_stock_index]['buy_stock'][0]
            if money!=0:
                self.my_money+=money
                self.show_my_data_money_label.setText(f'{self.my_money}')#update
        self.stocks_list[current_acting_stock_index]['trading_volume']+=trading_volume

    def update_stocks_list_buy_sell(self,current_acting_stock_index):
        buy_stock_num=0
        sell_stock_num=0
        j=0
        while j<len(self.stock_trading_list[current_acting_stock_index]['buy_stock']):
            buy_stock_num+=self.stock_trading_list[current_acting_stock_index]['buy_stock'][j]['num']
            j+=1
        j=0
        while j<len(self.stock_trading_list[current_acting_stock_index]['sell_stock']):
            sell_stock_num+=self.stock_trading_list[current_acting_stock_index]['sell_stock'][j]['num']
            j+=1
        self.stocks_list[current_acting_stock_index]['buy']=buy_stock_num
        self.stocks_list[current_acting_stock_index]['sell']=sell_stock_num

    def update_stocks(self,update_stocks_list):
        #need_update_ui=False
        i=0
        while i<len(update_stocks_list):
            self.stocks_list[i]['stock_price']=update_stocks_list[i]['stock_price']
            self.stocks_list[i]['weight']=update_stocks_list[i]['weight']
            self.stocks_list[i]['max_up_unit']=update_stocks_list[i]['max_up_unit']
            self.stocks_list[i]['max_down_unit']=update_stocks_list[i]['max_down_unit']
            self.stocks_list[i]['update_time_weight']=update_stocks_list[i]['update_time_weight']
            self.stocks_list[i]['update_time_max_up_unit']=update_stocks_list[i]['update_time_max_up_unit']
            self.stocks_list[i]['update_time_max_down_unit']=update_stocks_list[i]['update_time_max_down_unit']
            self.stocks_list[i]['cur_time_weight']=update_stocks_list[i]['cur_time_weight']
            self.stocks_list[i]['cur_time_max_up_unit']=update_stocks_list[i]['cur_time_max_up_unit']
            self.stocks_list[i]['cur_time_max_down_unit']=update_stocks_list[i]['cur_time_max_down_unit']
            while len(self.stocks_list[i]['stock_price_history'])>0:
                del self.stocks_list[i]['stock_price_history'][0]
            j=0
            while j<10:
                self.stocks_list[i]['stock_price_history'].append(update_stocks_list[i]['stock_price_history'][j])
                j+=1
            self.stocks_list[i]['stock_status']=update_stocks_list[i]['stock_status']
            self.stocks_list[i]['cooldown_time']=update_stocks_list[i]['cooldown_time']
            #self.stocks_list[update_stocks_list[i]['index']]['stock_price']=int(update_stocks_list[i]['price'])
            #self.stocks_list[update_stocks_list[i]['index']]['weight']=int(update_stocks_list[i]['weight'])
            #self.stocks_list[update_stocks_list[i]['index']]['max_up_unit']=int(update_stocks_list[i]['max_up_unit'])
            #self.stocks_list[update_stocks_list[i]['index']]['max_down_unit']=int(update_stocks_list[i]['max_down_unit'])
            #del self.stocks_list[update_stocks_list[i]['index']]['stock_price_history'][0]
            #self.stocks_list[update_stocks_list[i]['index']]['stock_price_history'].append(update_stocks_list[i]['price'])
            #if update_stocks[i]['index'] in range(50*(self.cur_page-1),50*(self.cur_page)):
                #print('i:',update_stocks[i]['index'])
                #need_update_ui=True
            i+=1
        #if need_update_ui:
        self.update_main_window_stock_ui()

        if self.ui_my_stock.isVisible():
            self.update_my_stock_window_my_stock_list_ui()

        if self.ui_buy.isVisible():#auto update search result img
            qpixmap = self.plot_stock_history_to_img(self.buy_window_stock_id,self.stocks_list[self.buy_window_stock_index]['stock_name'],self.stocks_list[self.buy_window_stock_index]['stock_price_history'],self.stocks_list[self.buy_window_stock_index]['stock_status'])
            self.buy_img_label.setPixmap(qpixmap)#set img

    def style(self):
        self.style_box = '''
            background:#1a1a1a;
            border:1px solid #000;
            font-size:20px;
            color:white;
            font-family:Verdana;
            border-color:#1a1a1a;
            margin:1px
        '''
        self.style_btn = '''
            QPushButton{
                background:#1f538d;
                border:1px solid #000;
                border-radius:10px;
                padding:5px;
            }
            QPushButton:pressed{
                background:#a5bad1;
            }
            QPushButton:disabled{
                background:#a5bad1;
                color:#999999;
            }
        '''
        self.style_line_edit = '''
            background:#ffffff;
            border:1px solid #000;
            font-size:20px;
            color:#1a1a1a;
            font-family:Verdana;
            border-color:#1a1a1a;
            margin:1px
        '''
        self.style_red = '''
            color:#FF0000;
        '''
        self.style_green = '''
            color:#008000;
        '''
        self.style_disable = '''
            color:#696969;
        '''
        
    def start_ui(self):
        self.main_box = QtWidgets.QWidget(self)
        self.main_box.setGeometry(0,0,self.width_,self.height_)
        self.main_box.setStyleSheet(self.style_box)

        self.main_layout = QtWidgets.QFormLayout(self.main_box)

        self.account_create_btn=QtWidgets.QPushButton(self)
        self.account_create_btn.setText(f'{BUTTON_TEXT_10_SPACE*4}Create new account{BUTTON_TEXT_10_SPACE*4}')
        self.account_create_btn.setStyleSheet(self.style_btn)
        self.account_create_btn.clicked.connect(self.show_window_create_new_account)

        self.Login_btn=QtWidgets.QPushButton(self)
        self.Login_btn.setText('Login')
        self.Login_btn.setStyleSheet(self.style_btn)
        self.Login_btn.clicked.connect(self.open_account)

        self.main_layout.addRow(self.account_create_btn,self.Login_btn)

    def show_window_create_new_account(self):
        self.ui_create_new_account=QtWidgets.QWidget()
        self.ui_create_new_account.setWindowTitle("Create new account")
        self.ui_create_new_account.setStyleSheet(self.style_box)
        self.ui_create_new_account.setGeometry(self.x()+int(self.width()/2)-400,self.y()+int(self.height()/2)-75,800,150)
            
        self.create_new_account_layout = QtWidgets.QFormLayout(self.ui_create_new_account)
        #
        self.new_account_label=QtWidgets.QLabel(self.ui_create_new_account)
        self.new_account_label.setText('Account name:')

        self.new_account_name_line_edit=QtWidgets.QLineEdit(self.ui_create_new_account)
        #
        self.add_new_scores_btn=QtWidgets.QPushButton(self.ui_create_new_account)
        self.add_new_scores_btn.setText('Create')
        self.add_new_scores_btn.setStyleSheet(self.style_btn)
        self.add_new_scores_btn.clicked.connect(lambda:self.destroy_window_and_update_create_new_account('create'))

        self.add_new_account_cancel_btn=QtWidgets.QPushButton(self.ui_create_new_account)
        self.add_new_account_cancel_btn.setText('Cancel')
        self.add_new_account_cancel_btn.setStyleSheet(self.style_btn)
        self.add_new_account_cancel_btn.clicked.connect(lambda:self.destroy_window_and_update_create_new_account('cancel'))
        
        self.create_new_account_layout.addRow(self.new_account_label,self.new_account_name_line_edit)
        self.create_new_account_layout.addRow(self.add_new_account_cancel_btn,self.add_new_scores_btn)
        self.ui_create_new_account.show()

    def destroy_window_and_update_create_new_account(self,type_):
        global ACCOUNT
        if type_=='create':
            #self.save_name=self.new_account_name_line_edit.text()
            ACCOUNT=self.new_account_name_line_edit.text()
            f=open(f"{self.new_account_name_line_edit.text()}.txt",'w')
            self.my_money=ACCOUNT_INIT_MONEY
            f.write(f"{ACCOUNT_INIT_MONEY}\n")
            f.write(f"{TOTAL_STOCK_NUM}\n")
            i=0
            while i<len(self.stocks_list):
                f.write(f"{self.stocks_list[i]['stock_id']},{self.stocks_list[i]['stock_name']}\n")
                i+=1
            f.close()
            self.setWindowTitle(ACCOUNT)
            self.ui_create_new_account.close()
            self.show_stocks()
        elif type_=='cancel':
            self.ui_create_new_account.close()

    def open_account(self):
        global ACCOUNT
        self.file_dialog=QtWidgets.QFileDialog()
        QtWidgets.QFileDialog.setDirectory(self.file_dialog,'./')
        filePath , filterType = self.file_dialog.getOpenFileNames(filter='TXT (*.txt)')  # 選擇檔案對話視窗
        if len(filePath)>0:
            f=open(filePath[0],'r')
            #self.save_name=filePath[0].split('/')[-1][:-4]
            ACCOUNT=filePath[0].split('/')[-1][:-4]
            #print('saven',self.save_name)
            try:
                self.my_money=int(f.readline())
                stock_type_num=int(f.readline())
                i=0
                while i<stock_type_num:
                    stock=f.readline()[:-1]
                    stock_num_and_price_list=stock.split(',')[2:]
                    j=0
                    while j<len(stock_num_and_price_list):
                        num=int(stock_num_and_price_list[j].split('-')[0])
                        price=int(stock_num_and_price_list[j].split('-')[1])
                        self.my_stocks_list[i]['num_and_price'].append({"num":num,"price":price})
                        j+=1
                    i+=1
                f.close()
            except Exception as e:
                print('account txt syntax error000')
                print(e)
                f.close()
                os._exit(0)
            ############### init ###############
            self.setWindowTitle(ACCOUNT)
            self.show_stocks()

    def show_stocks(self):
        self.start_stock=True
        while 0<self.main_layout.rowCount()-1:
            self.main_layout.removeRow(1)
        
        #info row
        self.info_widget=QtWidgets.QWidget()
        self.info_layout=QtWidgets.QHBoxLayout(self.info_widget)
        self.info_label_stock_id=QtWidgets.QLabel(self)
        self.info_label_stock_id.setText('ID')
        self.info_label_stock=QtWidgets.QLabel(self)
        self.info_label_stock.setText('Stock')
        self.info_label_price=QtWidgets.QLabel(self)
        self.info_label_price.setText('Price')
        self.info_label_current_status=QtWidgets.QLabel(self)
        self.info_label_current_status.setText('Current status')
        self.info_label_overall_status=QtWidgets.QLabel(self)
        self.info_label_overall_status.setText('Overall status')
        self.info_label_buy=QtWidgets.QLabel(self)
        self.info_label_buy.setText('Buy')
        self.info_label_sell=QtWidgets.QLabel(self)
        self.info_label_sell.setText('Sell')
        self.info_label_trading_volume=QtWidgets.QLabel(self)
        self.info_label_trading_volume.setText('Trading Volume')
        self.info_layout.addWidget(self.info_label_stock_id)
        self.info_layout.addWidget(self.info_label_stock)
        self.info_layout.addWidget(self.info_label_price)
        self.info_layout.addWidget(self.info_label_current_status)
        self.info_layout.addWidget(self.info_label_overall_status)
        self.info_layout.addWidget(self.info_label_buy)
        self.info_layout.addWidget(self.info_label_sell)
        self.info_layout.addWidget(self.info_label_trading_volume)
        #self.info_layout.addWidget(self.info_label_high)
        
        #stocks row
        self.scroll_widget = QtWidgets.QWidget()
        self.scroll_layout = QtWidgets.QFormLayout(self.scroll_widget)
        self.scroll_area=QtWidgets.QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.scroll_widget)
        
        self.page_label=QtWidgets.QLabel(self)#for order problem
        self.update_main_window_stock_ui()
        
        #page row
        self.page_widget=QtWidgets.QWidget()
        self.page_layout=QtWidgets.QHBoxLayout(self.page_widget)
        self.page_label=QtWidgets.QLabel(self)
        if (TOTAL_STOCK_NUM/SINGLE_PAGE_STOCK_NUM)!=int(TOTAL_STOCK_NUM/SINGLE_PAGE_STOCK_NUM):
            total_page=int(TOTAL_STOCK_NUM/SINGLE_PAGE_STOCK_NUM)+1
        else:
            total_page=int(TOTAL_STOCK_NUM/SINGLE_PAGE_STOCK_NUM)
        self.page_label.setText(f'Page: {self.cur_page}/{total_page}')
        self.prev_page_btn=QtWidgets.QPushButton(self.page_widget)
        self.prev_page_btn.setText(f'{BUTTON_TEXT_10_SPACE}Prev{BUTTON_TEXT_10_SPACE}')
        self.prev_page_btn.setStyleSheet(self.style_btn)
        self.prev_page_btn.clicked.connect(lambda:self.change_page('prev'))

        self.page_line_edit=QtWidgets.QLineEdit(self.page_widget)
        self.page_line_edit.setStyleSheet(self.style_line_edit)
        self.input_page_btn=QtWidgets.QPushButton(self.page_widget)
        self.input_page_btn.setText(f'{BUTTON_TEXT_10_SPACE*3}Change{BUTTON_TEXT_10_SPACE*3}')
        self.input_page_btn.setStyleSheet(self.style_btn)
        self.input_page_btn.clicked.connect(lambda:self.change_page('input'))

        self.next_page_btn=QtWidgets.QPushButton(self.page_widget)
        self.next_page_btn.setText(f'{BUTTON_TEXT_10_SPACE}Next{BUTTON_TEXT_10_SPACE}')
        self.next_page_btn.setStyleSheet(self.style_btn)
        self.next_page_btn.clicked.connect(lambda:self.change_page('next'))
        self.page_layout.addWidget(self.page_label)
        self.page_layout.addWidget(self.prev_page_btn)
        self.page_layout.addWidget(self.page_line_edit)
        self.page_layout.addWidget(self.input_page_btn)
        self.page_layout.addWidget(self.next_page_btn)

        #search row
        #self.search_widget=QtWidgets.QWidget()
        #self.search_layout=QtWidgets.QHBoxLayout(self.search_widget)
        #self.search_label=QtWidgets.QLabel(self)
        #self.search_label.setText('Search stock:')
        #self.search_stock_id_label=QtWidgets.QLabel(self)
        #self.search_stock_id_label.setText('stock id:')
        #self.search_line_edit=QtWidgets.QLineEdit(self.search_widget)
        #self.search_line_edit.setStyleSheet(self.style_line_edit)
        #self.search_btn=QtWidgets.QPushButton(self.search_widget)
        #self.search_btn.setText(f'{BUTTON_TEXT_10_SPACE*3}Search{BUTTON_TEXT_10_SPACE*3}')
        #self.search_btn.setStyleSheet(self.style_btn)
        #self.search_btn.clicked.connect(self.show_window_search_result)
        #self.search_layout.addWidget(self.search_label)
        #self.search_layout.addWidget(self.search_stock_id_label)
        #self.search_layout.addWidget(self.search_line_edit)
        #self.search_layout.addWidget(self.search_btn)

        #buy stock row
        self.buy_stock_widget=QtWidgets.QWidget()
        self.buy_stock_layout=QtWidgets.QHBoxLayout(self.buy_stock_widget)
        self.buy_stock_label=QtWidgets.QLabel(self)
        self.buy_stock_label.setText('Buy stock:')
        self.buy_stock_id_label=QtWidgets.QLabel(self)
        self.buy_stock_id_label.setText('stock id:')
        self.stock_id_line_edit=QtWidgets.QLineEdit(self.buy_stock_widget)
        self.stock_id_line_edit.setStyleSheet(self.style_line_edit)
        #self.buy_stock_num_label=QtWidgets.QLabel(self)
        #self.buy_stock_num_label.setText('stock num:')
        #self.stock_num_line_edit=QtWidgets.QLineEdit(self.buy_stock_widget)
        #self.stock_num_line_edit.setStyleSheet(self.style_line_edit)
        self.buy_stock_ok_btn=QtWidgets.QPushButton(self.buy_stock_widget)
        self.buy_stock_ok_btn.setText(f'{BUTTON_TEXT_10_SPACE*3}Ok{BUTTON_TEXT_10_SPACE*3}')
        self.buy_stock_ok_btn.setStyleSheet(self.style_btn)
        self.buy_stock_ok_btn.clicked.connect(self.show_window_buy_stock)
        self.buy_stock_layout.addWidget(self.buy_stock_label)
        self.buy_stock_layout.addWidget(self.buy_stock_id_label)
        self.buy_stock_layout.addWidget(self.stock_id_line_edit)
        #self.buy_stock_layout.addWidget(self.buy_stock_num_label)
        #self.buy_stock_layout.addWidget(self.stock_num_line_edit)
        self.buy_stock_layout.addWidget(self.buy_stock_ok_btn)
        
        #show my data row
        self.show_my_data_widget=QtWidgets.QWidget()
        self.show_my_data_layout=QtWidgets.QHBoxLayout(self.show_my_data_widget)
        self.show_my_data_my_money_label=QtWidgets.QLabel(self)
        self.show_my_data_my_money_label.setText('My money:')
        self.show_my_data_money_label=QtWidgets.QLabel(self)
        self.show_my_data_money_label.setText(f'{self.my_money}')
        self.show_my_data_my_stock_label=QtWidgets.QLabel(self)
        self.show_my_data_my_stock_label.setText('My stock:')
        self.show_my_data_stock_btn=QtWidgets.QPushButton(self.show_my_data_widget)
        self.show_my_data_stock_btn.setText('show')
        self.show_my_data_stock_btn.setStyleSheet(self.style_btn)
        self.show_my_data_stock_btn.clicked.connect(self.show_window_my_stock)
        self.show_my_data_layout.addWidget(self.show_my_data_my_money_label)
        self.show_my_data_layout.addWidget(self.show_my_data_money_label)
        self.show_my_data_layout.addWidget(self.show_my_data_my_stock_label)
        self.show_my_data_layout.addWidget(self.show_my_data_stock_btn)

        #addRow
        self.main_layout.addRow(self.info_widget)
        self.main_layout.addRow(self.scroll_area)
        self.main_layout.addRow(self.page_widget)
        #self.main_layout.addRow(self.search_widget)
        self.main_layout.addRow(self.buy_stock_widget)
        self.main_layout.addRow(self.show_my_data_widget)

        #start update thread
        self.update_price_thread.start()

        #start robot thread
        i=0
        while i<len(self.robot_thread_list):
            self.robot_thread_list[i].start()
            i+=1
        
    def change_page(self,type_):
        is_change=False
        if type_=="prev" and self.cur_page>1:
            self.cur_page-=1
            is_change=True
        elif type_=="next" and self.cur_page<TOTAL_STOCK_NUM/SINGLE_PAGE_STOCK_NUM:
            self.cur_page+=1
            is_change=True
        elif type_=="input":
            try:
                if int(self.page_line_edit.text())>=1 and int(self.page_line_edit.text())<=TOTAL_STOCK_NUM/SINGLE_PAGE_STOCK_NUM:
                    self.cur_page=int(self.page_line_edit.text())
                    is_change=True 
            except Exception as e:
                print('change page syntax error001')
                print(e)
                #os._exit(0)
            self.page_line_edit.setText("")

        if is_change:
            self.update_main_window_stock_ui()

    def update_main_window_stock_ui(self):
        while 0<self.scroll_layout.rowCount():
            self.scroll_layout.removeRow(0)
        
        i=0
        while i<SINGLE_PAGE_STOCK_NUM and i<TOTAL_STOCK_NUM:
            widget = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout(widget)
            stock_id = QtWidgets.QLabel(self)
            stock_id.setText(f"{self.stocks_list[i+(SINGLE_PAGE_STOCK_NUM*(self.cur_page-1))]['stock_id']}")
            stock_name = QtWidgets.QLabel(self)
            stock_name.setText(f"{self.stocks_list[i+(SINGLE_PAGE_STOCK_NUM*(self.cur_page-1))]['stock_name']}")
            stock_price = QtWidgets.QLabel(self)
            stock_price.setText(f"{self.stocks_list[i+(SINGLE_PAGE_STOCK_NUM*(self.cur_page-1))]['stock_price']}")
            if self.stocks_list[i+(SINGLE_PAGE_STOCK_NUM*(self.cur_page-1))]['stock_price']==2000:
                stock_price.setStyleSheet(self.style_red)
            
            #below overall_status, just for order problem
            label_buy=QtWidgets.QLabel(self)
            label_buy.setText(f"{self.stocks_list[i+(SINGLE_PAGE_STOCK_NUM*(self.cur_page-1))]['buy']}")
            label_sell=QtWidgets.QLabel(self)
            label_sell.setText(f"{self.stocks_list[i+(SINGLE_PAGE_STOCK_NUM*(self.cur_page-1))]['sell']}")
            label_trading_volume=QtWidgets.QLabel(self)
            label_trading_volume.setText(f"{self.stocks_list[i+(SINGLE_PAGE_STOCK_NUM*(self.cur_page-1))]['trading_volume']}")

            stock_current_status = QtWidgets.QLabel(self)
            stock_overall_status = QtWidgets.QLabel(self)
            #print("stock_status:",self.stocks_list[i+(50*(self.cur_page-1))]['stock_status'])
            #print("his",self.stocks_list[i+(50*(self.cur_page-1))]['stock_price_history'])
            if self.stocks_list[i+(50*(self.cur_page-1))]['stock_status']=="-":
                #print(True)
                stock_current_status.setText("-")
                last_price=self.stocks_list[i+(SINGLE_PAGE_STOCK_NUM*(self.cur_page-1))]['stock_price_history'][-2]
                cur_price=self.stocks_list[i+(SINGLE_PAGE_STOCK_NUM*(self.cur_page-1))]['stock_price_history'][-1]
                price_diff=cur_price-last_price
                if price_diff>0:
                    stock_current_status.setText(f"+{price_diff}")
                    stock_current_status.setStyleSheet(self.style_red)
                elif price_diff<0:
                    stock_current_status.setText(f"{price_diff}")
                    stock_current_status.setStyleSheet(self.style_green)
                
                stock_overall_status.setText("-")
                oldest_price=self.stocks_list[i+(SINGLE_PAGE_STOCK_NUM*(self.cur_page-1))]['stock_price_history'][0]
                cur_price=self.stocks_list[i+(SINGLE_PAGE_STOCK_NUM*(self.cur_page-1))]['stock_price_history'][-1]
                price_diff=cur_price-oldest_price
                if price_diff>0:
                    stock_overall_status.setText(f"+{price_diff}")
                    stock_overall_status.setStyleSheet(self.style_red)
                elif price_diff<0:
                    stock_overall_status.setText(f"{price_diff}")
                    stock_overall_status.setStyleSheet(self.style_green)

            elif self.stocks_list[i+(SINGLE_PAGE_STOCK_NUM*(self.cur_page-1))]['stock_status']=="delisting":
                stock_current_status.setText("Delisting")
                stock_overall_status.setText("Delisting")
                stock_id.setStyleSheet(self.style_disable)
                stock_name.setStyleSheet(self.style_disable)
                stock_price.setStyleSheet(self.style_disable)
                stock_current_status.setStyleSheet(self.style_disable)
                stock_overall_status.setStyleSheet(self.style_disable)
                label_buy.setStyleSheet(self.style_disable)
                label_sell.setStyleSheet(self.style_disable)
                label_trading_volume.setStyleSheet(self.style_disable)

            layout.addWidget(stock_id)
            layout.addWidget(stock_name)
            layout.addWidget(stock_price)
            layout.addWidget(stock_current_status)
            layout.addWidget(stock_overall_status)
            layout.addWidget(label_buy)
            layout.addWidget(label_sell)
            layout.addWidget(label_trading_volume)

            self.scroll_layout.addRow(widget)
            i+=1

        #i=0
        #while i<50:
        #    widget = QtWidgets.QWidget()
        #    layout = QtWidgets.QHBoxLayout(widget)
        #    stock_id = QtWidgets.QLabel(self)
        #    stock_id.setText(f"{self.stocks_list[i+(50*(self.cur_page-1))]['stock_id']}")
        #    stock_name = QtWidgets.QLabel(self)
        #    stock_name.setText(f"{self.stocks_list[i+(50*(self.cur_page-1))]['stock_name']}")
        #    stock_price = QtWidgets.QLabel(self)
        #    stock_price.setText(f"{self.stocks_list[i+(50*(self.cur_page-1))]['stock_price']}")
        #    layout.addWidget(stock_id)
        #    layout.addWidget(stock_name)
        #    layout.addWidget(stock_price)
        #    self.scroll_layout.addRow(widget)
        #    i+=1
        if (TOTAL_STOCK_NUM/SINGLE_PAGE_STOCK_NUM)!=int(TOTAL_STOCK_NUM/SINGLE_PAGE_STOCK_NUM):
            total_page=int(TOTAL_STOCK_NUM/SINGLE_PAGE_STOCK_NUM)+1
        else:
            total_page=int(TOTAL_STOCK_NUM/SINGLE_PAGE_STOCK_NUM)
        self.page_label.setText(f'Page: {self.cur_page}/{total_page}')

    def show_window_my_stock(self):
        self.ui_my_stock=QtWidgets.QWidget()
        self.ui_my_stock.setWindowTitle("My stocks")
        self.ui_my_stock.setStyleSheet(self.style_box)
        self.ui_my_stock.setGeometry(self.x(),self.y()+int(self.height()/2)-300,1600,600)
            
        self.my_stock_layout = QtWidgets.QFormLayout(self.ui_my_stock)
        #info row
        self.my_stock_info_widget = QtWidgets.QWidget()
        self.my_stock_info_layout = QtWidgets.QHBoxLayout(self.my_stock_info_widget)
        self.my_stock_info_stock_id = QtWidgets.QLabel(self)
        self.my_stock_info_stock_id.setText("Stock ID")
        self.my_stock_info_stock_name = QtWidgets.QLabel(self)
        self.my_stock_info_stock_name.setText("Stock")
        self.my_stock_info_stock_num = QtWidgets.QLabel(self)
        self.my_stock_info_stock_num.setText("Num")
        self.my_stock_info_stock_buy_in_price = QtWidgets.QLabel(self)
        self.my_stock_info_stock_buy_in_price.setText("Buy in price")
        self.my_stock_info_stock_cur_price = QtWidgets.QLabel(self)
        self.my_stock_info_stock_cur_price.setText("Current price")
        self.my_stock_info_layout.addWidget(self.my_stock_info_stock_id)
        self.my_stock_info_layout.addWidget(self.my_stock_info_stock_name)
        self.my_stock_info_layout.addWidget(self.my_stock_info_stock_num)
        self.my_stock_info_layout.addWidget(self.my_stock_info_stock_buy_in_price)
        self.my_stock_info_layout.addWidget(self.my_stock_info_stock_cur_price)

        #my stock row
        self.my_stock_scroll_widget = QtWidgets.QWidget()
        self.my_stock_scroll_layout = QtWidgets.QFormLayout(self.my_stock_scroll_widget)
        self.my_stock_scroll_area=QtWidgets.QScrollArea(self)
        self.my_stock_scroll_area.setWidgetResizable(True)
        self.my_stock_scroll_area.setWidget(self.my_stock_scroll_widget) 

        self.update_my_stock_window_my_stock_list_ui()

        #sell row
        self.my_stock_sell_widget=QtWidgets.QWidget()
        self.my_stock_sell_layout=QtWidgets.QHBoxLayout(self.my_stock_sell_widget)
        self.my_stock_sell_stock_label=QtWidgets.QLabel(self.ui_my_stock)
        self.my_stock_sell_stock_label.setText('Sell stock:')
        self.my_stock_sell_stock_id_label=QtWidgets.QLabel(self.ui_my_stock)
        self.my_stock_sell_stock_id_label.setText('stock id:')
        self.my_stock_id_line_edit=QtWidgets.QLineEdit(self.ui_my_stock)
        self.my_stock_id_line_edit.setStyleSheet(self.style_line_edit)
        self.my_stock_sell_stock_num_label=QtWidgets.QLabel(self.ui_my_stock)
        self.my_stock_sell_stock_num_label.setText('sell num:')
        self.my_stock_num_line_edit=QtWidgets.QLineEdit(self.ui_my_stock)
        self.my_stock_num_line_edit.setStyleSheet(self.style_line_edit)
        self.my_stock_sell_stock_price_label=QtWidgets.QLabel(self.ui_my_stock)
        self.my_stock_sell_stock_price_label.setText('buy in price:')
        self.my_stock_price_line_edit=QtWidgets.QLineEdit(self.ui_my_stock)
        self.my_stock_price_line_edit.setStyleSheet(self.style_line_edit)
        self.my_stock_sell_layout.addWidget(self.my_stock_sell_stock_label)
        self.my_stock_sell_layout.addWidget(self.my_stock_sell_stock_id_label)
        self.my_stock_sell_layout.addWidget(self.my_stock_id_line_edit)
        self.my_stock_sell_layout.addWidget(self.my_stock_sell_stock_num_label)
        self.my_stock_sell_layout.addWidget(self.my_stock_num_line_edit)
        self.my_stock_sell_layout.addWidget(self.my_stock_sell_stock_price_label)
        self.my_stock_sell_layout.addWidget(self.my_stock_price_line_edit)
        
        #sell and close button row
        self.my_stock_sell_and_close_btn_widget=QtWidgets.QWidget()
        self.my_stock_sell_and_close_btn_layout=QtWidgets.QHBoxLayout(self.my_stock_sell_and_close_btn_widget)
        self.my_stock_close_btn=QtWidgets.QPushButton(self.ui_my_stock)
        self.my_stock_close_btn.setText('Close')
        self.my_stock_close_btn.setStyleSheet(self.style_btn)
        self.my_stock_close_btn.clicked.connect(lambda:self.destroy_window_and_update_my_stock('close'))
        self.my_stock_sell_btn=QtWidgets.QPushButton(self.ui_my_stock)
        self.my_stock_sell_btn.setText('Sell')
        self.my_stock_sell_btn.setStyleSheet(self.style_btn)
        self.my_stock_sell_btn.clicked.connect(lambda:self.destroy_window_and_update_my_stock('sell'))
        self.my_stock_sell_and_close_btn_layout.addWidget(self.my_stock_close_btn)
        self.my_stock_sell_and_close_btn_layout.addWidget(self.my_stock_sell_btn)
        
        #addRow
        self.my_stock_layout.addRow(self.my_stock_info_widget)
        self.my_stock_layout.addRow(self.my_stock_scroll_area)
        self.my_stock_layout.addRow(self.my_stock_sell_widget)
        self.my_stock_layout.addRow(self.my_stock_sell_and_close_btn_widget)
        self.ui_my_stock.show()

    def update_my_stock_window_my_stock_list_ui(self):
        while 0<self.my_stock_scroll_layout.rowCount():
            self.my_stock_scroll_layout.removeRow(0)

        i=0
        while i<len(self.my_stocks_list):
            j=0
            while j<len(self.my_stocks_list[i]['num_and_price']):
                widget = QtWidgets.QWidget()
                layout = QtWidgets.QHBoxLayout(widget)
                stock_id = QtWidgets.QLabel(self)
                stock_id.setText(f"{self.my_stocks_list[i]['stock_id']}")
                stock_name = QtWidgets.QLabel(self)
                stock_name.setText(f"{self.my_stocks_list[i]['stock_name']}")
                stock_num = QtWidgets.QLabel(self)
                stock_num.setText(f"{self.my_stocks_list[i]['num_and_price'][j]['num']}")
                stock_buy_in_price = QtWidgets.QLabel(self)
                stock_buy_in_price.setText(f"{self.my_stocks_list[i]['num_and_price'][j]['price']}")
                stock_index=self.find_stock_index_by_id(self.my_stocks_list[i]['stock_id'])
                stock_cur_price = QtWidgets.QLabel(self)
                stock_cur_price.setText(f"{self.stocks_list[stock_index]['stock_price']}")

                layout.addWidget(stock_id)
                layout.addWidget(stock_name)
                layout.addWidget(stock_num)
                layout.addWidget(stock_buy_in_price)
                layout.addWidget(stock_cur_price)

                self.my_stock_scroll_layout.addRow(widget)
                j+=1
            i+=1

    def destroy_window_and_update_my_stock(self,type_):
        try:
            if len(self.my_stock_id_line_edit.text())>0 or len(self.my_stock_num_line_edit.text())>0 or int(self.my_stock_price_line_edit.text())>0:
                int(self.my_stock_id_line_edit.text())
                int(self.my_stock_num_line_edit.text())
                int(self.my_stock_price_line_edit.text())
        except Exception as e:
            print('sell syntax error004')
            print(e)
            self.my_stock_id_line_edit.setText("")
            self.my_stock_num_line_edit.setText("")
            self.my_stock_price_line_edit.setText("")
            return
        
        if type_=="sell":
            sell_stock_id=self.my_stock_id_line_edit.text()
            sell_stock_num=int(self.my_stock_num_line_edit.text())
            buy_in_stock_price=int(self.my_stock_price_line_edit.text())
            stock_index=self.find_stock_index_by_id(sell_stock_id)
            #delete from my stock
            id_found=False
            i=0
            while i<len(self.my_stocks_list):
                if self.my_stocks_list[i]['stock_id']==sell_stock_id:
                    id_found=True
                    price_found=False
                    j=0
                    while j<len(self.my_stocks_list[i]['num_and_price']):
                        if self.my_stocks_list[i]['num_and_price'][j]['price']==buy_in_stock_price:
                            price_found=True
                            if self.my_stocks_list[i]['num_and_price'][j]['num']==sell_stock_num:
                                del self.my_stocks_list[i]['num_and_price'][j]
                            elif self.my_stocks_list[i]['num_and_price'][j]['num']>sell_stock_num:
                                self.my_stocks_list[i]['num_and_price'][j]['num']-=sell_stock_num
                            else:#sell num > have num
                                self.my_stock_id_line_edit.setText("")
                                self.my_stock_num_line_edit.setText("")
                                return
                            break
                        j+=1
                    if not price_found:#no price
                        self.my_stock_id_line_edit.setText("")
                        self.my_stock_num_line_edit.setText("")
                        return
                    break
                i+=1
            if not id_found:#no id
                self.my_stock_id_line_edit.setText("")
                self.my_stock_num_line_edit.setText("")
                return
            #add to stock_trading_list
            sell_stock_price=self.stocks_list[stock_index]['stock_price']#current price
            have_same=False
            i=0
            while i<len(self.stock_trading_list[stock_index]['sell_stock']):
                if self.stock_trading_list[stock_index]['sell_stock'][i]['account']==ACCOUNT and self.stock_trading_list[stock_index]['sell_stock'][i]['price']==sell_stock_price:
                    have_same=True
                    self.stock_trading_list[stock_index]['sell_stock'][i]['num']+=sell_stock_num
                    break
                i+=1
            if not have_same:
                self.stock_trading_list[stock_index]['sell_stock'].append({'account':ACCOUNT,'price':sell_stock_price,'num':sell_stock_num})

            #update ui
            self.update_my_stock_window_my_stock_list_ui()
            if self.ui_buy.isVisible():
                if self.buy_window_stock_index==stock_index:
                    self.update_buy_window_sell_list_ui()
            
        elif type_=="close":
            self.ui_my_stock.close()

        self.my_stock_id_line_edit.setText("")
        self.my_stock_num_line_edit.setText("")
           
    def find_stock_index_by_id(self,id):
        i=0
        while i<len(self.stocks_list):
            if str(id)==self.stocks_list[i]['stock_id']:
                return i
            i+=1
        return -1
    
    def plot_stock_history_to_img(self,stock_id,stock_name,stock_price_history,stock_status="-"):
        x = [9,8,7,6,5,4,3,2,1,0]
        x_major_locator=MultipleLocator(1)
        #let x bar unit = 1
        y_major_locator=MultipleLocator(100)
        #let y bar unit = 100
        ax=plt.gca()
        #x bar and y bar object
        ax.xaxis.set_major_locator(x_major_locator)
        #set x bar unit = 1
        ax.yaxis.set_major_locator(y_major_locator)
        #set y bar unit = 100
        #print('sph:',stock_price_history)
        plt.plot(x,stock_price_history,'o-')#draw by x,y
        for a, b in zip(x, stock_price_history):
            plt.text(a, b+50, b, ha='center', va='bottom', fontsize=10)
        if stock_status=="-":
            plt.title(f'{stock_name}          ID:{stock_id}')
        elif stock_status=="delisting":
            plt.title(f'{stock_name}   ID:{stock_id}   Delisting')
        plt.xlabel("time")
        plt.ylabel("price")
        plt.xlim([9.5,-0.5])#set min and max x bar num
        plt.ylim([0,2000])#set min and max y bar num
        plt.savefig(f'./data/history/{stock_id}.jpg')
        plt.clf()
        qpixmap = QtGui.QPixmap() 
        qpixmap.load(f'./data/history/{stock_id}.jpg')#read img
        return qpixmap

    def show_window_buy_stock(self):
        try:
            int(self.stock_id_line_edit.text())
        except Exception as e:
            print('search syntax error002')
            print(e)
            self.stock_id_line_edit.setText("")
            return
            #os._exit(0)
            
        stock_id=self.stock_id_line_edit.text()
        stock_index=self.find_stock_index_by_id(stock_id)
        self.buy_window_stock_id=stock_id #for auto update and destroy_window_and_update_buy func
        self.buy_window_stock_index=stock_index #for auto update, update_buy_window_sell_list_ui and destroy_window_and_update_buy func
        self.stock_id_line_edit.setText("")
        if stock_index!=-1:
            self.ui_buy=QtWidgets.QWidget()
            self.ui_buy.setWindowTitle(f"{self.stocks_list[stock_index]['stock_name']}")
            self.ui_buy.setStyleSheet(self.style_box)
            self.ui_buy.setGeometry(self.x()+int(self.width()/2)-int(self.ui_buy.width()/2),self.y()+30,self.ui_buy.width(),self.height_)
            self.buy_layout = QtWidgets.QFormLayout(self.ui_buy)
            #img row
            qpixmap = self.plot_stock_history_to_img(stock_id,self.stocks_list[stock_index]['stock_name'],self.stocks_list[stock_index]['stock_price_history'],self.stocks_list[stock_index]['stock_status'])
            self.buy_img_label=QtWidgets.QLabel(self.ui_buy)
            self.buy_img_label.setPixmap(qpixmap)#set img
            #sell list title row
            self.buy_sell_list_title_label=QtWidgets.QLabel(self)
            self.buy_sell_list_title_label.setText('Sell list')
            self.buy_sell_list_title_label.setAlignment(QtCore.Qt.AlignCenter)
            #sell list info row
            self.buy_sell_list_info_widget=QtWidgets.QWidget()
            self.buy_sell_list_info_layout=QtWidgets.QHBoxLayout(self.buy_sell_list_info_widget)
            self.buy_sell_list_info_label_account=QtWidgets.QLabel(self)
            self.buy_sell_list_info_label_account.setText('Account')
            self.buy_sell_list_info_label_num=QtWidgets.QLabel(self)
            self.buy_sell_list_info_label_num.setText('Num')
            self.buy_sell_list_info_label_price=QtWidgets.QLabel(self)
            self.buy_sell_list_info_label_price.setText('Price')
            self.buy_sell_list_info_layout.addWidget(self.buy_sell_list_info_label_account)
            self.buy_sell_list_info_layout.addWidget(self.buy_sell_list_info_label_num)
            self.buy_sell_list_info_layout.addWidget(self.buy_sell_list_info_label_price)
            #sell list row
            self.buy_scroll_widget = QtWidgets.QWidget()
            self.buy_scroll_layout = QtWidgets.QFormLayout(self.buy_scroll_widget)
            self.buy_scroll_area=QtWidgets.QScrollArea(self)
            self.buy_scroll_area.setWidgetResizable(True)
            self.buy_scroll_area.setWidget(self.buy_scroll_widget)
            self.update_buy_window_sell_list_ui()
            #num and price line edit row
            self.buy_num_price_widget=QtWidgets.QWidget()
            self.buy_num_price_layout=QtWidgets.QHBoxLayout(self.buy_num_price_widget)
            self.buy_num_label=QtWidgets.QLabel(self.ui_buy)
            self.buy_num_label.setText('Buy num:')
            self.buy_num_line_edit=QtWidgets.QLineEdit(self.ui_buy)
            self.buy_num_line_edit.setStyleSheet(self.style_line_edit)
            self.buy_price_label=QtWidgets.QLabel(self.ui_buy)
            self.buy_price_label.setText('price:')
            self.buy_price_line_edit=QtWidgets.QLineEdit(self.ui_buy)
            self.buy_price_line_edit.setStyleSheet(self.style_line_edit)
            self.buy_num_price_layout.addWidget(self.buy_num_label)
            self.buy_num_price_layout.addWidget(self.buy_num_line_edit)
            self.buy_num_price_layout.addWidget(self.buy_price_label)
            self.buy_num_price_layout.addWidget(self.buy_price_line_edit)
            #buy and close button row
            self.buy_buy_and_close_btn_widget=QtWidgets.QWidget()
            self.buy_buy_and_close_btn_layout=QtWidgets.QHBoxLayout(self.buy_buy_and_close_btn_widget)
            self.buy_close_btn=QtWidgets.QPushButton(self.ui_buy)
            self.buy_close_btn.setText('Close')
            self.buy_close_btn.setStyleSheet(self.style_btn)
            self.buy_close_btn.clicked.connect(lambda:self.destroy_window_and_update_buy('close'))
            self.buy_buy_btn=QtWidgets.QPushButton(self.ui_buy)
            self.buy_buy_btn.setText('Buy')
            self.buy_buy_btn.setStyleSheet(self.style_btn)
            self.buy_buy_btn.clicked.connect(lambda:self.destroy_window_and_update_buy('buy'))
            self.buy_buy_and_close_btn_layout.addWidget(self.buy_close_btn)
            self.buy_buy_and_close_btn_layout.addWidget(self.buy_buy_btn)
            #addRow
            self.buy_layout.addRow(self.buy_img_label)
            self.buy_layout.addRow(self.buy_sell_list_title_label)
            self.buy_layout.addRow(self.buy_sell_list_info_widget)
            self.buy_layout.addRow(self.buy_scroll_area)
            self.buy_layout.addRow(self.buy_num_price_widget)
            self.buy_layout.addRow(self.buy_buy_and_close_btn_widget)
            self.ui_buy.show()

    def update_buy_window_sell_list_ui(self):
        while 0<self.buy_scroll_layout.rowCount():
            self.buy_scroll_layout.removeRow(0)
        
        i=0
        while i<len(self.stock_trading_list[self.buy_window_stock_index]['sell_stock']):
            widget=QtWidgets.QWidget()
            layout=QtWidgets.QHBoxLayout(widget)
            label_account=QtWidgets.QLabel(self)
            label_account.setText(f"{self.stock_trading_list[self.buy_window_stock_index]['sell_stock'][i]['account']}")
            label_num=QtWidgets.QLabel(self)
            label_num.setText(f"{self.stock_trading_list[self.buy_window_stock_index]['sell_stock'][i]['num']}")
            label_price=QtWidgets.QLabel(self)
            label_price.setText(f"{self.stock_trading_list[self.buy_window_stock_index]['sell_stock'][i]['price']}")
            layout.addWidget(label_account)
            layout.addWidget(label_num)
            layout.addWidget(label_price)

            self.buy_scroll_layout.addRow(widget)
            i+=1

    def destroy_window_and_update_buy(self,type_):
        try:
            if len(self.buy_num_line_edit.text())>0 or len(self.buy_price_line_edit.text())>0:
                int(self.buy_num_line_edit.text())
                int(self.buy_price_line_edit.text())
        except Exception as e:
            print('sell syntax error003')
            print(e)
            self.buy_num_line_edit.setText("")
            self.buy_price_line_edit.setText("")
            return
        
        if type_=='buy':
            buy_num=int(self.buy_num_line_edit.text())
            buy_price=int(self.buy_price_line_edit.text())
            if buy_num>0 and buy_price>0:
                i=0
                while i<len(self.stock_trading_list[self.buy_window_stock_index]['sell_stock']):
                    if buy_num<=self.stock_trading_list[self.buy_window_stock_index]['sell_stock'][i]['num'] and buy_price==self.stock_trading_list[self.buy_window_stock_index]['sell_stock'][i]['price'] and self.my_money >= buy_num*buy_price*1000:
                        #delete from stock_trading_list
                        if self.stock_trading_list[self.buy_window_stock_index]['sell_stock'][i]['num']==buy_num:
                            del self.stock_trading_list[self.buy_window_stock_index]['sell_stock'][i]
                        else:
                            self.stock_trading_list[self.buy_window_stock_index]['sell_stock'][i]['num']-=buy_num
                        #delete my money
                        self.my_money -= buy_num*buy_price*1000
                        #save to my stock list
                        insert_index=0
                        have_same=False
                        j=0
                        while j<len(self.my_stocks_list[self.buy_window_stock_index]["num_and_price"]):
                            if self.my_stocks_list[self.buy_window_stock_index]["num_and_price"][j]['price']<buy_price:
                                insert_index+=1
                            if self.my_stocks_list[self.buy_window_stock_index]["num_and_price"][j]['price']==buy_price:
                                self.my_stocks_list[self.buy_window_stock_index]["num_and_price"][j]['num']+=buy_num
                                have_same=True
                                break
                            j+=1
                        if not have_same:
                            self.my_stocks_list[self.buy_window_stock_index]["num_and_price"].insert(insert_index,{"num":buy_num,"price":buy_price})   
                        #self.my_stocks_list=[]#{"stock_id":,"stock_name":"num_and_price":[{"num":,"price"},...]}
                        #print(f'get:{self.buy_window_stock_index}({buy_price})*{buy_num},total:[{buy_num*buy_price*1000}]')
                        #update sell and trading_volume
                        self.stocks_list[self.buy_window_stock_index]['sell']-=buy_num
                        self.stocks_list[self.buy_window_stock_index]['trading_volume']+=buy_num
                        #wait
                        self.update_main_window_stock_ui()
                        self.show_my_data_money_label.setText(f'{self.my_money}')#update my money label
                        if self.ui_my_stock.isVisible():
                            self.update_my_stock_window_my_stock_list_ui()
                        self.update_buy_window_sell_list_ui()
                        break
                    i+=1

        elif type_=='close':
            self.ui_buy.close()
        
        self.buy_num_line_edit.setText("")
        self.buy_price_line_edit.setText("")
    
    def save_to_STOCKS(self):
        f=open('STOCKS','w')
        i=0
        while i<len(self.stocks_list):
            #stock_id,stock_name,stock_price,
            f.write(str(self.stocks_list[i]['stock_id'])+','+str(self.stocks_list[i]['stock_name'])+','+str(self.stocks_list[i]['stock_price'])+',')
            #weight,max_up_unit,max_down_unit,
            f.write(str(self.stocks_list[i]['weight'])+','+str(self.stocks_list[i]['max_up_unit'])+','+str(self.stocks_list[i]['max_down_unit'])+',')
            #update_time_weight,update_time_max_up_unit,update_time_max_down_unit,
            f.write(str(self.stocks_list[i]['update_time_weight'])+','+str(self.stocks_list[i]['update_time_max_up_unit'])+','+str(self.stocks_list[i]['update_time_max_down_unit'])+',')
            #cur_time_weight,cur_time_max_up_unit,cur_time_max_down_unit,
            f.write(str(self.stocks_list[i]['cur_time_weight'])+','+str(self.stocks_list[i]['cur_time_max_up_unit'])+','+str(self.stocks_list[i]['cur_time_max_down_unit'])+',')
            #stock_price_history,
            j=0
            while j<len(self.stocks_list[i]['stock_price_history'])-1:
                f.write(str(self.stocks_list[i]['stock_price_history'][j])+'-')
                j+=1
            f.write(str(self.stocks_list[i]['stock_price_history'][j])+',')
            #stock_status,cooldown_time,
            f.write(str(self.stocks_list[i]['stock_status'])+','+str(self.stocks_list[i]['cooldown_time'])+',')
            #buy,sell,trading_volume
            f.write(str(self.stocks_list[i]['buy'])+','+str(self.stocks_list[i]['sell'])+','+str(self.stocks_list[i]['trading_volume'])+'\n')
            i+=1
        f.close()

    def save_to_ACCOUNT(self):
        f=open(f"{ACCOUNT}.txt",'w')
        #my money
        f.write(f"{self.my_money}\n")
        #stock type num
        f.write(f"{len(self.my_stocks_list)}\n")
        i=0
        while i<len(self.my_stocks_list):
            #stock_id,stock_name,
            f.write(f"{self.my_stocks_list[i]['stock_id']},{self.my_stocks_list[i]['stock_name']}")
            if len(self.my_stocks_list[i]['num_and_price'])>0:
                f.write(",")
                #num-price
                j=0
                while j<len(self.my_stocks_list[i]['num_and_price'])-1:
                    f.write(f"{self.my_stocks_list[i]['num_and_price'][j]['num']}-{self.my_stocks_list[i]['num_and_price'][j]['price']},")
                    j+=1
                f.write(f"{self.my_stocks_list[i]['num_and_price'][j]['num']}-{self.my_stocks_list[i]['num_and_price'][j]['price']}\n")
            else:
                f.write("\n")
            i+=1
        f.close()

    def resizeEvent(self,event):
        width, height = event.size().width(), event.size().height()
        self.main_box.setGeometry(0,0,width,height)

    def closeEvent(self,event):
        if self.start_stock:
            self.save_to_STOCKS()
            self.save_to_ACCOUNT()
        self.ui_create_new_account.close()
        self.ui_buy.close()
        self.ui_my_stock.close()

class Update_price_thread(QtCore.QThread):
    def __init__(self,parent=None):
        super(Update_price_thread, self).__init__(parent)
        self.stocks_list=[]
        f=open('STOCKS','r')
        i=0
        while i<TOTAL_STOCK_NUM:
            stock=f.readline()
            #stock_price1-stock_price2-stock_price3-stock_price4-stock_price5-stock_price6-stock_price7-stock_price8-stock_price9-stock_price10
            stock_price_history=stock.split(',')[12].split('-')
            j=0
            while j<len(stock_price_history):
                stock_price_history[j]=int(stock_price_history[j])
                j+=1
            #stock_id,stock_name,stock_price,weight,max_up_unit,max_down_unit,update_time_weight,update_time_max_up_unit,update_time_max_down_unit,cur_time_weight,cur_time_max_up_unit,cur_time_max_down_unit,status(delisting,-),cooldown_time
            self.stocks_list.append({"stock_id":stock.split(',')[0],
                                     "stock_name":stock.split(',')[1],
                                     "stock_price":int(stock.split(',')[2]),
                                     "weight":int(stock.split(',')[3]),
                                     "max_up_unit":int(stock.split(',')[4]),
                                     "max_down_unit":int(stock.split(',')[5]),
                                     "update_time_weight":int(stock.split(',')[6]),
                                     "update_time_max_up_unit":int(stock.split(',')[7]),
                                     "update_time_max_down_unit":int(stock.split(',')[8]),
                                     "cur_time_weight":int(stock.split(',')[9]),
                                     "cur_time_max_up_unit":int(stock.split(',')[10]),
                                     "cur_time_max_down_unit":int(stock.split(',')[11]),
                                     "stock_price_history":stock_price_history,
                                     "stock_status":stock.split(',')[13],
                                     "cooldown_time":int(stock.split(',')[14])
                                     })#no:buy, sell, trading_volume
            i+=1
        f.close()
    
    update_price_signal = QtCore.pyqtSignal(list)

    def run(self):
        while True:
            #index_price_weight_up_down_history=[]
            time.sleep(STOCK_PRICE_UPDATE_TIME)
            update_num=0
            j=0
            while j<len(self.stocks_list):#update price
                if self.stocks_list[j]['stock_status']=="-":
                    is_update=False
                    self.stocks_list[j]['cur_time_weight']-=1
                    self.stocks_list[j]['cur_time_max_up_unit']-=1
                    self.stocks_list[j]['cur_time_max_down_unit']-=1
                    del self.stocks_list[j]['stock_price_history'][0]
                    if self.stocks_list[j]['cur_time_weight']==0:
                        is_update=True
                        self.stocks_list[j]['cur_time_weight']=self.stocks_list[j]['update_time_weight']
                        self.stocks_list[j]['weight']=random.randint(1,10)

                    if self.stocks_list[j]['cur_time_max_up_unit']==0:
                        is_update=True
                        self.stocks_list[j]['cur_time_max_up_unit']=self.stocks_list[j]['update_time_max_up_unit']
                        self.stocks_list[j]['max_up_unit']=random.randint(1,5)

                    if self.stocks_list[j]['cur_time_max_down_unit']==0:
                        is_update=True
                        self.stocks_list[j]['cur_time_max_down_unit']=self.stocks_list[j]['update_time_max_down_unit']
                        self.stocks_list[j]['max_down_unit']=random.randint(-5,-1)

                    self.stocks_list[j]['stock_price']+=self.stocks_list[j]['weight'] * random.randint(self.stocks_list[j]['max_down_unit'],self.stocks_list[j]['max_up_unit'])
                    
                    if self.stocks_list[j]['stock_price']<0:
                        self.stocks_list[j]['stock_price']=0
                        self.stocks_list[j]['stock_status']="delisting"
                    
                    if self.stocks_list[j]['stock_price']>2000:
                        self.stocks_list[j]['stock_price']=2000
                        #too good, reroll
                        self.stocks_list[j]['weight']=random.randint(1,10)
                        self.stocks_list[j]['max_up_unit']=random.randint(1,5)
                        self.stocks_list[j]['max_down_unit']=random.randint(-5,-1)
                        self.stocks_list[j]['update_time_weight']=random.randint(1,30)
                        self.stocks_list[j]['update_time_max_up_unit']=random.randint(1,30)
                        self.stocks_list[j]['update_time_max_down_unit']=random.randint(1,30)
                        self.stocks_list[j]['cur_time_weight']=self.stocks_list[j]['update_time_weight']
                        self.stocks_list[j]['cur_time_max_up_unit']=self.stocks_list[j]['update_time_max_up_unit']
                        self.stocks_list[j]['cur_time_max_down_unit']=self.stocks_list[j]['update_time_max_down_unit']


                    self.stocks_list[j]['stock_price_history'].append(self.stocks_list[j]['stock_price'])
                    #index_price_weight_up_down_history.append({"index":j,"price":self.stocks_list[j]['stock_price'],"weight":self.stocks_list[j]['weight'],"max_up_unit":self.stocks_list[j]['max_up_unit'],"max_down_unit":self.stocks_list[j]['max_down_unit'],"stock_price_history":self.stocks_list[j]['stock_price_history']})

                    if is_update:
                        update_num+=1
                    #print(self.stocks_list[j]['stock_name'])
                #else:
                #    self.stocks_list[j]['stock_price_history'].append(self.stocks_list[j]['stock_price'])
                elif self.stocks_list[j]['stock_status']=="delisting":
                    self.stocks_list[j]['cooldown_time']-=1
                    if self.stocks_list[j]['cooldown_time']==0:
                        self.stocks_list[j]['stock_status']="-"
                        self.stocks_list[j]['cooldown_time']=10
                        self.stocks_list[j]['stock_price']=random.randint(500,1500)
                        self.stocks_list[j]['weight']=random.randint(1,10)
                        self.stocks_list[j]['max_up_unit']=random.randint(1,5)
                        self.stocks_list[j]['max_down_unit']=random.randint(-5,-1)
                        self.stocks_list[j]['update_time_weight']=random.randint(1,30)
                        self.stocks_list[j]['update_time_max_up_unit']=random.randint(1,30)
                        self.stocks_list[j]['update_time_max_down_unit']=random.randint(1,30)
                        self.stocks_list[j]['cur_time_weight']=self.stocks_list[j]['update_time_weight']
                        self.stocks_list[j]['cur_time_max_up_unit']=self.stocks_list[j]['update_time_max_up_unit']
                        self.stocks_list[j]['cur_time_max_down_unit']=self.stocks_list[j]['update_time_max_down_unit']
                        while len(self.stocks_list[j]['stock_price_history'])>0:
                            del self.stocks_list[j]['stock_price_history'][0]
                        while len(self.stocks_list[j]['stock_price_history'])<10:
                            self.stocks_list[j]['stock_price_history'].append(self.stocks_list[j]['stock_price'])

                        #index_price_weight_up_down_history.append({"index":j,"price":self.stocks_list[j]['stock_price'],"weight":self.stocks_list[j]['weight'],"max_up_unit":self.stocks_list[j]['max_up_unit'],"max_down_unit":self.stocks_list[j]['max_down_unit'],"stock_price_history":self.stocks_list[j]['stock_price_history']})

                j+=1
            if PRINT_STOCK_IMPLICIT_PARAMETER_UPDATE_NUM:
                print(f"=============update num:{update_num}=============")
            self.update_price_signal.emit(self.stocks_list)

class Robot_thread(QtCore.QThread):
    def __init__(self,parent=None):
        super(Robot_thread, self).__init__(parent)
        #self.robot_id=robot_id

    robot_signal = QtCore.pyqtSignal(dict)

    def run(self):
        while True:
            time.sleep(ROBOT_UPDATE_TIME)
            act_choice=random.random()#0.0~1.0
            #act=random.choice(['buy','sell'])
            act_stock_index=-1
            act_stock_num=0
            act=""
            if act_choice<=ROBOT_BUY_PROBABILITY:#buy
                act='buy'
                buy_stock_index=random.randint(0,TOTAL_STOCK_NUM-1)
                buy_stock_num=random.randint(1,10)
                act_stock_index=buy_stock_index
                act_stock_num=buy_stock_num

            else:#sell
                act='sell'
                sell_stock_index=random.randint(0,TOTAL_STOCK_NUM-1)
                sell_stock_num=random.randint(1,10)
                act_stock_index=sell_stock_index
                act_stock_num=sell_stock_num

            #self.robot_signal.emit({'robot_id':self.robot_id,'act':act,'act_stock_index':act_stock_index,'act_stock_num':act_stock_num})
            self.robot_signal.emit({'act':act,'act_stock_index':act_stock_index,'act_stock_num':act_stock_num})

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Form = MyWidget()
    Form.show()
    sys.exit(app.exec_())