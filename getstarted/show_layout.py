# -*- coding: utf-8 -*-
"""
Pdfのオブジェクトのレイアウトを画像として表示します。

"""
#%%
from typing import List
import os,sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from libPdfextractkit import PdfExtractKit,PreviewCanvas

print("Current directory -> "+os.getcwd())
path=os.path.join(os.path.dirname(__file__),"data/data_shishingaiyou.pdf")
with PdfExtractKit.load(path) as p2:
    #ページ数
    print("Pages %d"%(len(p2)))
    p=p2[0:1]
    n=0
    for i in p:
        box=i.extract()
        pil=PreviewCanvas(i)
        for j in box:
            pil.rect(((j.left,j.top),(j.right,j.bottom)))     
            pass
        pil.show()
#%%