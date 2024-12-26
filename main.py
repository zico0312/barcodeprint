import time
from sbpl import SG412R_Status5, LabelGenerator
import tkinter as tk
import sqlite3
import tkinter.simpledialog as ts
import tkinter.messagebox as tm


class MainPage(tk.Tk):
    def __init__(self):
        super().__init__()
        self.connection=None
        self.loading=True
        self.screen_width =self.winfo_screenwidth()
        self.screen_height=self.winfo_screenheight()
        app_width=int(self.screen_width*1/5)
        app_height=int(self.screen_height*1/5)
        self.geometry(f"{app_width}x{app_height}+{int(self.screen_width*4/10)}+{int(self.screen_height*4/10)}")
        self.title("バーコード作成プログラム")
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        config_menu = tk.Menu(menubar, tearoff=0)
        config_menu.add_command(label="プリンタ接続設定",command=self.printer_config)
        config_menu.add_separator()
        config_menu.add_command(label="終了", command=self.quit)
        menubar.add_cascade(label="設定", menu=config_menu)
        self.conn=sqlite3.connect("data.db")
        self.cursor=self.conn.cursor()
        self.database_init()
        self.ipaddress=None
        self.port=None
        self.dpi=None
        data=self.cursor.execute('''
            select ipaddress,port,dpi from Config
        ''').fetchall()
        
        print(data)
        
        if (data):
            self.ipaddress:str=data[-1][0]
            self.port:int=data[-1][1]
            self.dpi:int=data[-1][2]
        
        frame=tk.Frame(self)
        frame.pack(side=tk.TOP,padx=4,pady=12,fill=tk.X)
        tk.Label(frame,text="開始番号",font=("",12,"")).pack(side=tk.LEFT)
        self.startnumberinput=tk.Entry(frame,font=("",12,""),justify=tk.CENTER)
        self.startnumberinput.pack(side=tk.LEFT)
        self.startnumberinput.bind("<Return>",self.focus_next_widget)
        
        
        frame=tk.Frame(self)
        frame.pack(side=tk.TOP,padx=4,pady=12,fill=tk.X)
        tk.Label(frame,text="終了番号",font=("",12,"")).pack(side=tk.LEFT)
        self.endnumberinput=tk.Entry(frame,font=("",12,""),justify=tk.CENTER)
        self.endnumberinput.pack(side=tk.LEFT)
        
        frame=tk.Frame(self)
        frame.pack(side=tk.TOP,padx=4,pady=12,fill=tk.X)
        tk.Button(frame,text="印字",font=("",12,""),command=self.print_label).pack(side=tk.TOP,anchor=tk.S)

        self.comm= SG412R_Status5()
        self.connection=self.comm.open(self.ipaddress, self.port)

        self.loading=False
    
    def database_init(self):
        self.cursor.execute('''
                            create table if not exists config(
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                ipaddress text,
                                port integer,
                                dpi integer,
                                created_at DATETIME DEFAULT (datetime('now', '+9 hours'))
                            )
                            
                            ''')
        self.conn.commit()
        
    def printer_config(self):
        ipaddress=ts.askstring("プリンタのIP入力画面","プリンタのIPアドレスを入力して下さい。",initialvalue=self.ipaddress,parent=self)
        if not(ipaddress):
            return
        port=ts.askinteger("プリンタのPORT入力画面","プリンタのPORTを入力して下さい。",initialvalue=self.port if self.port else 9100,parent=self)
        try:
            port=int(port)
        except Exception as e:
            print(e)
            tm.showerror("エラー","PORTの指定に誤りがあります。")
            return
        
        dpi=ts.askinteger("プリンタのdpi入力画面","プリンタのdpiを入力して下さい。",initialvalue=self.dpi if self.dpi else 203,parent=self)
        try:
            dpi=int(dpi)
        except Exception as e:
            print(e)
            tm.showerror("エラー","dpiの指定に誤りがあります。")
            return
        
        
        self.cursor.execute('''
            insert into config(ipaddress,port,dpi) values(?,?,?)                    
        '''
        ,(ipaddress,port,dpi))
        self.conn.commit()
        self.ipaddress=ipaddress
        self.port=port
        self.dpi=dpi
    
    def focus_next_widget(self,event):
        event.widget.tk_focusNext().focus()
        return "break"
    
    

    def print_label(self):
        if self.loading:
            print("sajoksoa")
            return
        startnum=self.startnumberinput.get()
        if not startnum or not startnum.isnumeric():
            tm.showerror("エラー","開始番号が不正な値です",parent=self)
            return
        endnum=self.endnumberinput.get()
        if not endnum or not endnum.isnumeric():
            tm.showerror("エラー","終了番号が不正な値です",parent=self)
            return
        
        if not self.ipaddress or not self.port or not self.dpi:
            tm.showerror("エラー","プリンタが未設定です")
            return
        label_width=int(90*self.dpi/25.4)
        
        if not self.connection:
            print("接続なし")
            return
        
        try:
            # ソケットをオープン
            
            time.sleep(1)
            # ラベル生成
            gen = LabelGenerator()
            
            with gen.packet_for_with():
                for num in range(int(startnum),int(endnum)+1):
                    time.sleep(1)
                    num_str=f"{num:03}"
                    print(num_str)
                    with gen.page_for_with():
                        gen.expansion((2, 2))
                        gen.pos((10,10))
                        gen.code_39(text=num_str,pitch=2,height=100)
                        gen.pos((10,130))
                        gen.write_text(num_str)
                        gen.print()
                        self.comm.send(gen.to_bytes())
                        cut_command = b'^XA^MMC^XZ'  # カットコマンド
                        self.comm.send(cut_command)
                    
    
            # 最終化パケットの送信
            print("処理完了")


        except Exception as e:
            print("エラー:", e)

    print("完了")
        
        
        
if __name__=="__main__":
    mainpage=MainPage()
    mainpage.mainloop()




