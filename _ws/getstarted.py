# -*- coding: utf-8 -*-
"""
https://www.mhlw.go.jp/stf/shingi2/0000208910_00029.html

"""

# def margeLine(rect_list):
#     rect_list/
#%%
from typing import List, Tuple
import os,sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from pdfextractkit import PdfExtractKit,Target,PreviewCanvas,BoxLayout


import math

class Point:
    def __init__(self,x,y):
        self.x=x
        self.y=y
    @property
    def xy(self)->Tuple[float,float]:
        return (self.x,self.y)

class Segment:
    @staticmethod
    def fromValue(xy0:Tuple[float,float],xy1:Tuple[float,float]):
        return Segment(Point(xy0[0],xy0[1]),Point(xy1[0],xy1[1]))
    def fromPoint(p0:Point,p1:Point):
        return Segment(p0,p1)
    def __init__(self,p0:Point,p1:Point):
        self.p0=p0
        self.p1=p1
    @property
    def length(self):
        """線分の長さ
        """
        x=(self.p0.x-self.p1.x)
        y=(self.p0.y-self.p1.y)
        return math.sqrt(x*x+y*y)
    def segmentLineDist(self,xy:Point)->float:
        """この線分と点(x,y)の距離を計算します。
        """
        def cross2(p:Point, q:Point):
            return p.x*q.y - p.y*q.x
        def dot2(p:Point, q:Point):
            return p.x*q.x + p.y*q.y
        def dist2(p:Point):
            return p.x**2 + p.y**2
        # Shortest distance between a line segment (p0-p1) and a point x
        p0=self.p0
        p1=self.p1
        z0 = Point(p1.x - p0.x, p1.y - p0.y)
        z1 = Point(xy.x - p0.x, xy.y - p0.y)
        if 0 <= dot2(z0, z1) <= dist2(z0):
            return abs(cross2(z0, z1)) / dist2(z0)**.5
        z2 = (xy.x - p1.x, xy.y - p1.y)
        return min(dist2(z1), dist2(z2))**.5
    # def topEdge(self):
    #     return self.p0 if self.p0.y>self.p1.y
    # def bottomEdge(self):
    # def leftEdge(self):
    # def rightEdge(self):
        

    @classmethod
    def margeSegment(cls,segment1,segment2,separategap=1,sidegap:float=1):
        """2つの線分が結合可能結合して新しい線分を返します。
        2つの線分の並行度が閾値以下で端点同士が範囲内にある時に、合成した線分を計算するおことができます。
        Args:
            segment1    1つめの線分
            segment2    2つめの線分
        """
        #4点の最遠点の組み合わせを求める
        points:List[Point]=[segment1.p0,segment1.p1,segment2.p0,segment2.p1]
        far_point_idx=[0,0] #再遠点のインデクス
        max_f2=0
        for i in range(0,3):
            for j in range(i+1,4):
                w=(points[i].x-points[j].x)**2+(points[i].y-points[j].y)**2
                if max_f2<w:
                    max_f2=w
                    far_point_idx=[i,j]
        #最近点のセット
        near_point_idx=[i for i in range(0,4) if i not in far_point_idx]

        #最遠点セグメントを作る。
        far_segment=Segment.fromPoint(points[far_point_idx[0]],points[far_point_idx[1]])
        #再遠点距離が2本の直線の合計値＋マージンより大きければエラー
        if segment1.length+segment2.length+separategap<far_segment.length:
            return None
        #最近点と再遠点セグメントの距離を計算
        nf1=far_segment.segmentLineDist(points[near_point_idx[0]])
        nf2=far_segment.segmentLineDist(points[near_point_idx[1]])
        #print(nf1+nf2,l1.length+l2.length+0.0-far_segment.length)
        #最近点と再遠点セグメントの距離合計が閾値より大きければエラー
        if nf1+nf2>sidegap:
            return None
        return Segment.fromPoint(far_segment.p0,far_segment.p1)




class Segments:
    @classmethod
    def fromRects(cls,rects,minwidth=1)->List["Segment"]:
        def fromRect(l,t,r,b,minwidth):
            #RECTから線分クラスを生成する。
            dy=abs(t-b)
            dx=abs(r-l)
            if dy<=minwidth:
                c=(t+b)/2
                return (Segment.fromValue((l,c),(r,c)),)
            if dx<=minwidth:
                c=(l+r)/2
                return (Segment.fromValue((c,t),(c,b)),)
            #４本の線にする
            return (
                Segment.fromValue((l,t),(l,b)),
                Segment.fromValue((l,b),(r,b)),
                Segment.fromValue((r,b),(r,t)),
                Segment.fromValue((r,t),(l,t)))
        l=[]
        for i in rects:
            for j in fromRect(i.left,i.top,i.right,i.bottom,minwidth):
                l.append(j)
        return Segments(l)
    def __init__(self,segments:List[Segment]):
        """
        Args:
            lines   [[(x1,y1),(x2,y2)],...]
        """        
        self.items=segments
        
    def __iter__(self):
        self._itr_n=0
        return self
    def __next__(self):
        n=self._itr_n
        if n >= len(self.items):
            raise StopIteration
        n=n+1
        self._itr_n=n
        return self.items[n-1]
    def __len__(self):
        """格納しているBox要素の数です。
        """
        return len(self.items)
    def __getitem__(self,key:int):
        """n番目のレイアウトを返します。
        """
        return self.lines[key]
    def margedStraightLines(self,separategap=2,sidegap=3):
        """近似線分を結合したリストを返します。
        """
        lines=[i for i in self.items]

        c=True
        while c:
            c=False
            i=0
            while i<len(lines):
                l1=lines[i]
                j=i+1
                while j<len(lines):
                    l2=lines[j]
                    ml=Segment.margeSegment(l1,l2,separategap,sidegap)
                    if ml is not None:
                        lines[i]=ml
                        del lines[j]
                        c=True
                    else:
                        j=j+1
                i=i+1
        return Segments(lines)
    def selectLinesByDegree(self,degree,gap):
        """ある角度の直線と平行な線を選択します。
        Args:
            degree  0～90,線分同士の角度のうち狭いほう
            gap
        """
        def deg(l):
            #線分の角度を計算
            return math.degrees(math.atan2(abs(l.p0.y-l.p1.y),abs(l.p0.x-l.p1.x))) #点0を基準にした角度(0,90)
        return Segments([i for i in self.items if abs(deg(i)-degree)<gap])
    def selectHorizontalLine(self,gap=0.01):
        """水平線だけのLinesを生成します
        """
        return self.selectLinesByDegree(0,gap)
    def selectVerticalLine(self,gap=0.01):
        """垂直線だけのLinesを生成します
        """
        return self.selectLinesByDegree(90,gap)




        

        







def find(boxes):

    all=Segments.fromRects(boxes)
    #罫線を検出
    # h=all.selectHorizontalLine().margedStraightLines()
    v=all.selectVerticalLine().margedStraightLines()
    #表の横幅と立幅を計算
    
    return (all,v)

#データはここから　https://cio.go.jp/policy-opendata
path=os.path.join(os.path.dirname(__file__),"tmp/000823359.pdf")
with PdfExtractKit.load(path) as p2:
    #ページ数
    print("Pages %d"%(len(p2)))
    p=p2[2:3]
    n=0
    for i in p:
        boxes=i.extract(target=Target.RECT)
        lines=find(boxes)
        pvc=PreviewCanvas(i)
        c=0
        ll=lines[1]
        print(len(ll))
        for j in ll:
            c=c+1
            f=["red","green","blue"][c%3]
            pvc.rect(j.p0.xy,j.p1.xy,fill=f,outline=None)     
        # for j in lines[1]:
        #     print(j.height)
        #     pvc.rect((j.left,j.top),(j.right,j.bottom),fill="red",outline=None)     
        pvc.show()
# print(p1chars.traceX(16.4,112.26,(136.59+120.63)*0.5).text)
#%%