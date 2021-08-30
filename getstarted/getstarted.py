#%%
import os,sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from pdfextractkit import PdfExtractKit
#データはここから　https://cio.go.jp/policy-opendata
path=os.path.join(os.path.dirname(__file__),"data_shishingaiyou.pdf")
with PdfExtractKit.load(path) as p:
    #ページ数
    print("Pages %d"%(len(p)))
    #文字列のダンプ
    n=0
    for i in p:
        n=n+1
        print("Lookup page %d"%(n))
        print(i.lookup())
    # #文字のダンプ
    n=0
    for i in p:
        n=n+1
        print("Extract page %d"%(n))
        print(i.extract())
    #1ページ目の文字列を検索(文字列、空白はトリミングする)
    p1texts=p[0].lookup().trim(True)
    print(p1texts.textOf("経済活性化"))
    #1ページ目の文字列を直線状にトレースしてテキストにまとめる
    p1chars=p[0].extract().trim(True)
    print(p1chars.traceX(16.4,112.26,(136.59+120.63)*0.5).text)
#%%
