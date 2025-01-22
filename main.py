import socket
import time
from sbpl import SG412R_Status5, LabelGenerator
import tkinter as tk
import sqlite3
import tkinter.simpledialog as ts
import tkinter.messagebox as tm




class MainPage(tk.Tk):
    def __init__(self):
        super().__init__()
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
        frame.pack(side=tk.TOP,padx=4,fill=tk.X)
        small_frame=tk.Frame(frame)
        small_frame.pack(side=tk.TOP,anchor=tk.W)
        tk.Label(small_frame,text="IPアドレス:").pack(side=tk.LEFT)
        self.ipaddresslabel=tk.Label(small_frame,text=self.ipaddress)
        self.ipaddresslabel.pack(side=tk.LEFT)
        small_frame=tk.Frame(frame)
        small_frame.pack(side=tk.TOP,anchor=tk.W)
        tk.Label(small_frame,text="PORT:").pack(side=tk.LEFT,padx=4)
        self.portlabel=tk.Label(small_frame,text=self.port)
        self.portlabel.pack(side=tk.LEFT)
        small_frame=tk.Frame(frame)
        small_frame.pack(side=tk.TOP,anchor=tk.W)
        tk.Label(small_frame,text="dpi:").pack(side=tk.LEFT,padx=4)
        self.dpilabel=tk.Label(small_frame,text=self.dpi)
        self.dpilabel.pack(side=tk.LEFT)
        frame=tk.Frame(self)
        frame.pack(side=tk.TOP,padx=4,pady=4,fill=tk.X)
        min_frame=tk.Frame(frame)
        min_frame.pack(side=tk.TOP,padx=4,pady=4)
        tk.Label(min_frame,text="番号",font=("",12,"")).pack(side=tk.TOP)
        self.startnumberinput=tk.Entry(min_frame,font=("",12,""),justify=tk.CENTER)
        self.startnumberinput.pack(side=tk.TOP)
        self.startnumberinput.bind("<Return>",self.focus_next_widget)
        
        self.startnumberinput.focus_force()
        
        frame=tk.Frame(self)
        frame.pack(side=tk.TOP,padx=4,pady=12,fill=tk.X)
        tk.Button(frame,text="印字",font=("",12,""),command=self.print_label).pack(side=tk.TOP,anchor=tk.S)

        
    
    
    
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
        self.ipaddresslabel.config(text=self.ipaddress)
        self.portlabel.config(self.port)
        self.dpilabel.config(text=self.dpi)
        
    
    def focus_next_widget(self,event):
        event.widget.tk_focusNext().focus()
        return "break"
    
    

    def print_label(self):
        startnum=self.startnumberinput.get()
        if not startnum or not startnum.isnumeric():
            tm.showerror("エラー","番号が不正な値です",parent=self)
            return
        
        
        if not self.ipaddress or not self.port or not self.dpi:
            tm.showerror("エラー","プリンタが未設定です",parent=self)
            return
    

        commandlist=[]
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.ipaddress,self.port))
                

                s.send(b'\x12\x50\x47')
                # プリンターからの応答を受け取る（最大1024バイト）
                response = s.recv(1024)

                # 受け取ったデータを表示
                data = response[1:-1]
                parts = data.decode('utf-8').split(',')
                for i in parts:
                    print(i)
                status=parts[1]
                print("status",status)
                
                if status!="PS0":
                    tm.showerror("エラー","プリンタとの接続が確立できません。")
                    return




                #開始コマンド
                escape_code = 0x1B
                ascii_code = ord('佐')
                print(ascii_code)
                
                commandlist.append(b'\x1B\x41')

                command=b''

                #横指定
                command+=b'\x1B\x48'+str(50).encode()

                

                #縦指定
                command+=b'\x1B\x56'+str(10).encode()

                #文字
                # command+=(b'\x1B\x4C0202\x1B\x5001'+b'\x1B\x42\x44003120001')

                

                commandlist.append(command)

                sen=b''

                text = "(株式会社"
                for i in text:
                    if ord(i)<=256:
                        sen+=bytes([ord(i)])
                    else:
                        sen+=bytes(i.encode("shift-jis").hex().upper(),"shift-jis")


                print(sen)

                #sen=b'81698A94816A83548367815B'

                commandlist.append((b'\x1B\x4B\x32H'+sen))
                
                #終了コマンド
                commandlist.append(b'\x1B\x5A')

                new_command=b'\n'.join(commandlist)

                print(commandlist)
                print(new_command)

                


                s.send(new_command)

                
                
                # command=b'''
                #     \x1B\x41\n
                #     \x1B\x4850\x1B\x5650\x1B\x4C0202\x1B\x58\x53AAAA\n
                #     \x1B\x5A
                # '''
                

                # command=b'''
                # \x1B\x41\n
                # \x1B\x4850\x1B\x5650\x1B\x4C\x01\x01\x1B\x58\x4DABCDEFG\n
                # \x1B\x5A
                # '''

                # print(command)

                # s.send(command)

               
        
            # 最終化パケットの送信
            print("処理完了")


        except Exception as e:
            print("エラー:", e)

        finally:
            print("完了")

        
        
        
if __name__=="__main__":
    mainpage=MainPage()
    mainpage.mainloop()




