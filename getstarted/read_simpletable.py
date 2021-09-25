# -*- coding: utf-8 -*-
"""
単純な表形式のデータを展開するサンプルです。
掲載場所 https://www.data.go.jp/data/dataset/mof_20170208_0033/resource/23ec2641-a47d-4bb2-a5c0-f91368955855
データ https://www.houjin-bangou.nta.go.jp/setsumei/images/cities.pdf

"""

#%%
from logging import addLevelName
import os,sys
sys.path.append(os.path.join(os.path.dirname("__file__"), '..'))
from libPdfextractkit import Box, PdfExtractKit,PreviewCanvas,BoxType,BoxSet,TableReader




if __name__ == '__main__':
    print("Current directory -> "+os.getcwd())
    path=os.path.join(os.path.dirname("__file__"),"data/cities.pdf")
    with PdfExtractKit.load(path) as p:
        #ページ数
        print("Pages %d"%(len(p)))
        n=0
        p2=p[2]
        all=p2.extract()
        sr=TableReader(all)#ページ全体をソースにしてテーブルの読み出しインスタンスを生成する
        pvc=PreviewCanvas(p2)
        c=0
        sr._debug_drawCells(pvc) #セルを描画
        sr._debug_drawCellsGroups(pvc) #セルごとにグループ化した行を描画
        pvc.show()
        #行単位で文字列を表示
        for i in sr:
            print(",".join([j.text for j in i]))
#%%