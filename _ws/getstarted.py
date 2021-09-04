# -*- coding: utf-8 -*-
"""
https://www.mhlw.go.jp/stf/shingi2/0000208910_00029.html

"""

# def margeLine(rect_list):
#     rect_list/
#%%
from typing import List, Tuple,Union
import os,sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from pdfextractkit import PdfExtractKit,Target,PreviewCanvas,BoxLayout




from pekgl import SegmentArray,Segment,Rect,Point,ConstSegment

        

        







def findTableCells(segments:SegmentArray):

    #横/縦罫線を検出
    hsegments:SegmentArray=segments.selectHorizontalLine().margedStraightLines()
    vsegments:SegmentArray=segments.selectVerticalLine().margedStraightLines()

    #横罫線の左右エッジから補完のための縦線を生成
    le:List[Point]=[i.leftEdge for i in hsegments]
    le.sort(key=lambda k: k.y)
    re:List[Point]=[i.rightEdge for i in hsegments]
    re.sort(key=lambda k: k.y)
    #縦罫線の上下エッジから補完のための横線を生成
    te:List[Point]=[i.topEdge for i in vsegments]
    te.sort(key=lambda k: k.x)
    be:List[Point]=[i.bottomEdge for i in vsegments]
    be.sort(key=lambda k: k.x)
    #補完線と本線を結合
    print(isinstance(hsegments,SegmentArray))
    h=SegmentArray.parse([
    hsegments,
    SegmentArray.parse([ConstSegment(te[i],te[i+1]) for i in range(0,len(te)-1)]).margedStraightLines(0.1).selectHorizontalLine(),
    SegmentArray.parse([ConstSegment(be[i],be[i+1]) for i in range(0,len(be)-1)]).margedStraightLines(0.1).selectHorizontalLine()
    ]).margedStraightLines(0.3)
    v=SegmentArray.parse([
    vsegments,
    SegmentArray.parse([ConstSegment(le[i],le[i+1]) for i in range(0,len(le)-1)]).margedStraightLines(0.1).selectVerticalLine(),
    SegmentArray.parse([ConstSegment(re[i],re[i+1]) for i in range(0,len(re)-1)]).margedStraightLines(0.1).selectVerticalLine()
    ]).margedStraightLines(0.3)
    #矩形グリッドの集合と仮定して、セルの矩形集合を計算する。
    rowline=[i.center.y for i in h]
    colline=[i.center.x for i in v]
    tableboxes=[[((colline[y],rowline[x]),(colline[y+1],rowline[x+1])) for y in range(0,len(colline)-1)] for x in range(0,len(rowline)-1)]



    return tableboxes



#データはここから　https://cio.go.jp/policy-opendata
path=os.path.join(os.path.dirname(__file__),"tmp/000823359.pdf")
with PdfExtractKit.load(path) as p2:
    #ページ数
    print("Pages %d"%(len(p2)))
    p=p2[2:3]
    n=0
    for i in p:
        all=i.extract(target=Target.RECT).toSegmentArray()
        bx=findTableCells(all)
        pvc=PreviewCanvas(i)
        c=0
        # ll=lines[2]
        # print(len(ll))
        # for j in ll:
        #     c=c+1
        #     f=["red","green","blue"][c%3]
        #     pvc.rect(j.p0.xy,j.p1.xy,fill=f,outline=None)     
        for i in bx:
            for j in i:
                c=c+1
                f=["red","green","blue"][c%3]
                pvc.rect(j[0],j[1],fill=f,outline=None)     

        pvc.show()
# print(p1chars.traceX(16.4,112.26,(136.59+120.63)*0.5).text)
#%%