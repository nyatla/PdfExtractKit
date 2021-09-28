"""pdfextractkitのAPIを使った要素読み出しのヘルパークラスを定義します。
"""

from logging import addLevelName
from typing import List
import os,sys
from collections import UserList
sys.path.append(os.path.join(os.path.dirname("__file__"), '..'))
from pdfextractkit import Box,BoxType,BoxSet
from pekgl import SegmentList,Rect,Point
from PreviewCanvas import PreviewCanvas

class TableReader(UserList):
    """単純なマトリクステーブルの読み出しクラスです。RECT要素で構成された表座標系をもとに、テーブル要素のBox位置を推定し、
    セルをマルチラインのBoxSetとして読みだすためのアクセサを提供します。
    このReaderはBoxSetに１つの表だけを含むことを前提に動作します。
    このオブジェクトは読み出し専用です。
    Args:
        src 解析対象のBoxSetです。
        rowmargin 文字列解析のパラメータです。セル内で隣接するとみなす文字同士の最大値です。
        sidemargin 文字列解析のパラメータです。セル内で縦方向の行間距離の最大値です。
        lineseparategap 表解析パラメータです。Segment#margedStraightsを参照してください。
        linesidegap 表解析パラメータです。Segment#margedStraightsを参照してください。        
    """
    def __init__(self,src:BoxSet,rowmargin=1,sidemargin=3,lineseparategap=0.1,linesidegap=3):
        segments=src.selectByType(BoxType.RECT).toSegments()
        rects=TableReader._detectTableMatrix(segments,lineseparategap,linesidegap)
        #rects内の要素ごとに読み出す
        
        self.data=[[src.selectInside(c).readTextLines() for c in r] for r in rects] #Boxに変換
        self._cache={"rects":rects}
        return
    @property
    def cells(self)->List[BoxSet]:
        """セルを選択するプロパティです。
        セルは行単位に集約したBoxのBoxSetのリストです。
        """
        return self.data
    @property
    def rows(self)->List[List[BoxSet]]:
        """行配列を得ます。行配列は、横方向のセルをまとめた配列です。
            rows[r]でr行目のBoxSet配列を得ることができます。
        """
        return self.data
    @property
    def cols(self)->List[List[BoxSet]]:
        """列配列を得ます。列配列は、縦方向にセルをまとめた配列です。
            cols[r]でc列目のBoxSet配列を得ることができます。
        """
        if "cols" not in self._cache:
            lc=len(self.data[0]) #列数
            lr=len(self.data)
            if len([False for i in self.data if len(i)!=lc])!=0:
                raise RuntimeError("列数が異なる行があります。")
            self._cache["cols"]=[[self.data[r][c] for r in range(lr)] for c in range(lc)]
        return self._cache["cols"]
    def toList(self,trim:bool=False,remove_gaps:bool=False)->List[List[List[str]]]:
        """
        現在のBoxSetから表を認識してPythonのリストオブジェクトに変換します。
        Args:
            page:
        Returns:
            str型の配列です。List[row][col][line]の3次元配列です。
            lineはセル内を行単位に格納します。
        """
        if trim:
            return [[[l.trim(remove_gaps) for l in c] for c in r] for r in self.rows]
        else:
            return [[[l.text for l in c] for c in r] for r in self.rows]
    @staticmethod
    def _detectTableMatrix(segments:SegmentList,separategap=0.1,sidegap=3)->List[List[Rect]]:
        """セグメントリストから分割のない単純テーブルを再構成します。
        list[行][列]に各cellのRectを格納します。
        この関数はpekgkのユーティリティに移動したほうがいいかもね。
        """
        #横/縦罫線を検出
        hsegments:SegmentList=segments.selectHorizontals().margedStraights()
        vsegments:SegmentList=segments.selectVerticals().margedStraights()

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
        h=SegmentList([
        hsegments,
        SegmentList([(te[i],te[i+1]) for i in range(0,len(te)-1)]).margedStraights(separategap,sidegap).selectHorizontals(),
        SegmentList([(be[i],be[i+1]) for i in range(0,len(be)-1)]).margedStraights(separategap,sidegap).selectHorizontals()
        ]).margedStraights(separategap,sidegap)
        v=SegmentList([
        vsegments,
        SegmentList([(le[i],le[i+1]) for i in range(0,len(le)-1)]).margedStraights(separategap,sidegap).selectVerticals(),
        SegmentList([(re[i],re[i+1]) for i in range(0,len(re)-1)]).margedStraights(separategap,sidegap).selectVerticals()
        ]).margedStraights(separategap,sidegap)
        #矩形グリッドの集合と仮定して、セルの矩形集合を計算する。
        rowline=[i.center.y for i in h]
        colline=[i.center.x for i in v]
        rowline.sort(reverse=True)
        colline.sort()
        tableboxes=[[Rect((colline[y],rowline[x]),(colline[y+1],rowline[x+1])) for y in range(0,len(colline)-1)] for x in range(0,len(rowline)-1)]
        return tableboxes
    def _debug_drawCellsGroups(self,pvc:PreviewCanvas):
        """セル内の文字列位置を描画します。
        """
        c=0
        # a=all.readTextLines()
        for j in self:
            for k in j:
                for l in k:
                    pvc.rect(l,fill=["#ff7777","#77ff77","#7777ff"][c%3])
                c=c+1
    def _debug_drawCells(self,pvc:PreviewCanvas):
        """セルの状態を描画します。
        """
        c=0
        for j in self._cache["rects"]:
            for k in j:
                pvc.rect(k,outline="black",fill=["red","green","blue"][c%3])
                c=c+1
