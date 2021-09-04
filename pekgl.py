"""
pdfextractkitのため幾何計算
"""
from abc import abstractproperty
from re import search
from typing import List, Tuple,Union,NewType
import os,sys

#%%

import math
from abc import ABC,abstractmethod

Pointable=Tuple[float,float]
class Point(ABC):
    PARSABLE=Union["Point",Pointable]
    def __str__(self) -> str:
        return str(self.xy)

    @staticmethod
    def parse(v:PARSABLE):        
        t=type(v)
        if isinstance(v,Point):
            return v
        elif (isinstance(v,list) or isinstance(v,tuple)) and len(v)==2:
            return ConstPoint(v[0],v[1])
        raise RuntimeError()    
    @property
    def xy(self)->Tuple[float,float]:
        return (self.x,self.y)
    @property
    @abstractmethod
    def x(self):
        pass
    @property
    @abstractmethod
    def y(self):
        pass
class ConstPoint(Point):
    def __init__(self,x:float,y:float):
        self._x=x
        self._y=y
    @property
    def x(self):
        return self._x
    @property
    def y(self):
        return self._y




#%%



class Rect(ABC):
    PARSABLE=Union["Rect",Tuple[Point.PARSABLE,Point.PARSABLE]]
    @staticmethod
    def parse(v:PARSABLE):
        if isinstance(v,Rect):
            return v
        elif (isinstance(v,list) or isinstance(v,tuple)) and len(v)==2:
            return ConstRect(v[0],v[1])
        raise RuntimeError()    
    def __str__(self)->str:
        return str((self.leftTop.xy,self.rightBottom.xy))
    @property
    @abstractmethod
    def top(self):
        pass
    @property
    @abstractmethod
    def left(self):
        pass    
    @property
    @abstractmethod
    def right(self):
        pass
    @property
    @abstractmethod
    def bottom(self):
        pass    
    @property
    def leftTop(self)->Point:
        return ConstPoint(self.left,self.top)
    @property
    def rightBottom(self)->Point:
        return ConstPoint(self.right,self.bottom)
    @property
    def width(self):
        return self.right-self.left
    @property
    def height(self):
        return self.top-self.bottom
    def toSegmentList(self,mindist=1)->Tuple["Segment"]:
        """矩形を直線の集合に分解します"""
        l=self.left
        t=self.top
        r=self.right
        b=self.bottom
        dy=abs(t-b)
        dx=abs(r-l)
        if dy<=mindist:
            c=(t+b)/2
            return (ConstSegment((l,c),(r,c)),)
        if dx<=mindist:
            c=(l+r)/2
            return (ConstSegment((c,t),(c,b)),)
        #４本の線にする
        return (
            ConstSegment((l,t),(l,b)),
            ConstSegment((l,b),(r,b)),
            ConstSegment((r,b),(r,t)),
            ConstSegment((r,t),(l,t)))



class ConstRect(Rect):
    """矩形を格納するクラスです。
    """
    def __init__(self,left_top:Point.PARSABLE,right_bottom:Point.PARSABLE):
        self.left_top=Point.parse(left_top)
        self.right_bottom=Point.parse(right_bottom)
        assert(self.left<=self.right)
        assert(self.top>=self.bottom)
    @property
    def top(self):
        return self.left_top.y
    @property
    def left(self):
        return self.left_top.x
    @property
    def right(self):
        return self.right_bottom.x
    @property
    def bottom(self):
        return self.right_bottom.y

class Segment(ABC):
    PARSABLE=Union["Segment",Tuple[Point.PARSABLE,Point.PARSABLE]]
    def __str__(self)->str:
        return str((self.topEdge.xy,self.bottomEdge.xy)) 
    @staticmethod
    def parse(v:PARSABLE):
        if isinstance(v,Segment):
            return v
        elif (isinstance(v,list) or isinstance(v,tuple)) and len(v)==2:
            return ConstSegment(v[0],v[1])
        raise RuntimeError("Invalid type %s"%(type(v)))    

    @property
    @abstractmethod    
    def p0(self):
        pass
    @property
    @abstractmethod    
    def p1(self):
        pass
    @property
    def length(self):
        """線分の長さ
        """
        x=(self.p0.x-self.p1.x)
        y=(self.p0.y-self.p1.y)
        return math.sqrt(x*x+y*y) 
    @property
    def topEdge(self)->Point:
        """上にある点を返します。"""
        return self.p0 if self.p0.y>self.p1.y else self.p1
    @property
    def bottomEdge(self)->Point:
        """下にある点を返します。"""
        return self.p0 if self.p0.y<self.p1.y else self.p1
    @property
    def leftEdge(self)->Point:
        """左にある点を返します。"""
        return self.p0 if self.p0.x<self.p1.x else self.p1
    @property
    def rightEdge(self)->Point:
        """右にある点を返します。"""
        return self.p0 if self.p0.x>self.p1.x else self.p1
    @property
    def center(self)->Point:
        """線分の中心点を返です。"""
        return ConstPoint(0.5*(self.p0.x+self.p1.x),0.5*(self.p0.y+self.p1.y))
    @property
    def degrees(self):
        """線分の角度を計算します。"""
        r=math.atan2(self.p0.y-self.p1.y,self.p0.x-self.p1.x)
        return math.degrees((r if r>=0 else math.pi+r))%180 # 0から180度に直す
    def segmentLineDist(self,xy:Point.PARSABLE)->float:
        """この線分と点(x,y)の距離を計算します。
        """
        def cross2(p:Point, q:Point):
            return p.x*q.y - p.y*q.x
        def dot2(p:Point, q:Point):
            return p.x*q.x + p.y*q.y
        def dist2(p:Point):
            return p.x**2 + p.y**2
        # Shortest distance between a line segment (p0-p1) and a point x
        xy=Point.parse(xy)
        p0=self.p0
        p1=self.p1
        z0 = ConstPoint(p1.x - p0.x, p1.y - p0.y)
        z1 = ConstPoint(xy.x - p0.x, xy.y - p0.y)
        if 0 <= dot2(z0, z1) <= dist2(z0):
            return abs(cross2(z0, z1)) / dist2(z0)**.5
        z2 = (xy.x - p1.x, xy.y - p1.y)
        return min(dist2(z1), dist2(z2))**.5
    @classmethod
    def margeSegment(cls,segment1:"Segment.PARSABLE",segment2:"Segment.PARSABLE",separategap=1,sidegap:float=1):
        """2つの線分が結合可能結合して新しい線分を返します。
        2つの線分の並行度が閾値以下で端点同士が範囲内にある時に、合成した線分を計算するおことができます。
        Args:
            segment1    1つめの線分
            segment2    2つめの線分
        """
        #4点の最遠点の組み合わせを求める
        segment1=Segment.parse(segment1)
        segment2=Segment.parse(segment2)
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
        far_segment=ConstSegment(points[far_point_idx[0]],points[far_point_idx[1]])
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
        return ConstSegment(far_segment.p0,far_segment.p1)


class ConstSegment(Segment):
    """線分を格納するクラス
    """
    def __init__(self,p0:Point.PARSABLE,p1:Point.PARSABLE):
        self._p0=Point.parse(p0)
        self._p1=Point.parse(p1)
    @property
    def p0(self):
        return self._p0
    @property
    def p1(self):
        return self._p1

#%%

class RectArray(ABC):
    PARSABLE=Union["RectArray",List[Union[Rect.PARSABLE,"RectArray"]]]
    @staticmethod
    def parse(v:PARSABLE):
        if isinstance(v,RectArray):
            return v
        elif (isinstance(v,list) or isinstance(v,tuple)):
            t:List[Rect]=[]
            for i in v:
                if isinstance(i,RectArray):
                    for j in i:
                        t.append(Rect.parse(j))
                    continue
                t.append(Rect.parse(i))
            return ConstRectArray(t)
        raise RuntimeError()
    def __iter__(self):
        self._itr_n=0
        return self
    def __next__(self)->Rect:
        n=self._itr_n
        if n >= len(self):
            raise StopIteration
        n=n+1
        self._itr_n=n
        return self[n-1]
    @abstractmethod
    def __len__(self)->int:
        pass
    @abstractmethod
    def __getitem__(self,key:int)->Segment:
        pass    
    def toSegmentArray(self,minwidth=1)->"SegmentArray":
        l=[]
        for i in self:
            for j in i.toSegmentList(minwidth):
                l.append(j)
        return ConstSegmentArray(l)        

class ConstRectArray(RectArray):
    def __init__(self,src:List[Rect]):
        self._items=src
    def __len__(self):
        return len(self._items)
    def __getitem__(self,key:int):
        return self._items[key]



class SegmentArray(ABC):
    PARSABLE=Union["SegmentArray",List[Union[Segment.PARSABLE,"SegmentArray"]]]
    @staticmethod
    def parse(v:PARSABLE):
        if isinstance(v,SegmentArray):
            return v
        elif (isinstance(v,list) or isinstance(v,tuple)):
            t:List[Segment]=[]
            for i in v:
                if isinstance(i,SegmentArray):
                    for j in i:
                        t.append(Segment.parse(j))
                    continue
                t.append(Segment.parse(i))
            return ConstSegmentArray(t)
        raise RuntimeError()    
    def __str__(self):
        return str([str(i) for i in self])
    def __iter__(self):
        self._itr_n=0
        return self
    def __next__(self)->Segment:
        n=self._itr_n
        if n >= len(self):
            raise StopIteration
        n=n+1
        self._itr_n=n
        return self[n-1]
    @abstractmethod
    def __len__(self)->int:
        pass
    @abstractmethod
    def __getitem__(self,key:int)->Segment:
        pass

    def margedStraightLines(self,separategap=2,sidegap=3)->"SegmentArray":
        """近似線分を結合したリストを返します。
        """
        lines=[i for i in self]
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
        return ConstSegmentArray(lines)        
    def select(self,where)->"SegmentArray":
         return ConstSegmentArray([i for i in self if where(i)]) 
    def selectLinesByDegree(self,degrees,gap)->"SegmentArray":
        """ある角度の直線と平行な線を選択します。
        degree=10,gap=3の場合、7から13度の線分を選択します。
        Args:
            degree  [0,180),並行を検査する線分の角度
            gap 角度誤差の許容値
        """
        def test(d1:Segment):
            t=abs(d1.degrees-degrees)
            return (t if t<90 else 180-t)<gap
        return self.select(test)
    def selectHorizontalLine(self,gap=0.01)->"SegmentArray":
        """水平線だけのLinesを生成します
        """
        return self.selectLinesByDegree(0,gap)
    def selectVerticalLine(self,gap=0.01)->"SegmentArray":
        """垂直線だけのLinesを生成します
        """
        return self.selectLinesByDegree(90,gap)

class ConstSegmentArray(SegmentArray):
    def __init__(self,src:List[Segment]):
        self._items=src
    def __len__(self):
        return len(self._items)
    def __getitem__(self,key:int):
        return self._items[key]


#%%