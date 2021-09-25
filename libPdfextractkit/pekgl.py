#%%
"""
pdfextractkitのため幾何計算クラス類を定義します。
"""
from re import search
from typing import Callable, Collection, Any, List, Tuple,Union
from collections import UserList
from collections import namedtuple





#%%

import copy
import math
from abc import ABC,abstractmethod

def isnumber(n):
    return isinstance(n,(float,int))

def isArrayable(o:object,l:int=None):
    if l is None:
        return isinstance(o,Collection)
        # return isinstance(o,tuple) or isinstance(o,list) or isinstance(o,UserList)
    else:
        return isinstance(o,Collection) and len(o)==l
        # return (isinstance(o,tuple) or isinstance(o,list) or isinstance(o,UserList)) and len(o)==l

def isNumerics(l:Union[List[Union[int,float]],Collection[Union[int,float]]],num=None):
    if not isArrayable(l):
        return False
    for i in l:
        if not isnumber(i):
            return False
    if num is not None and num!=len(l):
        return False            
    return True




class BaseClass(ABC):
    @abstractmethod
    def isParsable(v):
        pass

from operator import attrgetter
class BaseList(UserList):
    """幾何ライブラリのリストクラスのベースクラスです。
    このクラスは、要素にイミュータブルなクラスを期待します。
    派生クラスは状態変数を持つべきではありません。これはコピー時に問題になります。
    """
    def select(self,operator:Callable[[Any],bool]):
        """要素全てにoperator関数を適応して、結果がtrueだけのものを新しいリストにして返します。
        """
        r=self.__new__(type(self))
        r.data=[i for i in self if operator(i)]
        return r
    def filter(self,operator:Callable[[Any],Any]):
        """要素全てにoperator関数を適応して、結果がNoneでないものを新しいリストにして返します。
        この関数は要素を抽出し、内容を交換するときに使います。引数をそのまま返すと新しい要素にコピーされます。
        引数と同じ型のオブジェクトを生成して返すと、リストの要素がその値に置き換わります。
        """
        r=self.__new__(type(self))
        d=[]
        for i in self:
            b=operator(i)
            if b is None:
                continue
            d.append(b)
        r.data=d
        return r
    def arrange(self,key:Callable,reverse=False):
        """keyでソートした結果を返します。
        """
        d=self[:]
        d.sort(key=key,reverse=reverse)
        return d
    def arrangeLR(self):
        """左端を基準に、左から右に並べます。
        """
        return self.arrange(attrgetter("left"))
    def arrangeTB(self):
        """上端を基準に、上から下に並べます。
        """
        return self.arrange(attrgetter("top"),True)
    def arrangeLRTB(self):
        """左から右に並べた後に、右から左に並べ他結果を返します。
        """
        return self.arrangeLR().arrangeTB()



class Point(BaseClass):
    PARSABLE=Union["Point",Tuple[float,float]]
    def __init__(self,x:Union[float,PARSABLE],y:float=None):
        if y is None:
            if isinstance(x,Point):
                #Point,None
                self._d=x._d
            elif isNumerics(x,2):
                #Tuple[float,float],None
                self._d=x
            else:
                raise RuntimeError("Invalid type a1:%s"%(type(x)))     
        elif isnumber(x) and isnumber(y):
            #float,float
            self._d=(x,y)
        else:
            raise RuntimeError("Invalid type a1:%s a2:%s"%(type(x),type(y)))     
    def __str__(self) -> str:
        return str(self._d)
    @staticmethod
    def isParsable(v):
        return isinstance(v,Point) or isNumerics(v,2)   
    @property
    def xy(self)->Tuple[float,float]:
        return self._d
    @property
    def x(self)->float:
        return self._d[0]
    @property
    def y(self)->float:
        return self._d[1]
    def toTuple(self):
        return self._d



#%%
class Segment:
    PARSABLE=Union["Segment",Tuple[Point.PARSABLE,Point.PARSABLE]]
    def __init__(self,p0:Union[Point.PARSABLE,PARSABLE],p1:Point.PARSABLE=None):
        if p1 is None:
            if isinstance(p0,Segment):
                #Segment,None
                self._d=p0._d
            elif isArrayable(p0,2) and Point.isParsable(p0[0]) and Point.isParsable(p0[1]):
                #Tuple[Point.PARSABLE,Point.PARSABLE],None
                self._d=(
                    p0[0] if isinstance(p0[0],Point) else Point(p0[0]),
                    p0[1] if isinstance(p0[1],Point) else Point(p0[1]),
                )
            else:
                raise RuntimeError("Invalid type a1:%s"%(type(p0)))     
        elif Point.isParsable(p0) and Point.isParsable(p1):
            self._d=(
                p0 if isinstance(p0,Point) else Point(p0),
                p1 if isinstance(p1,Point) else Point(p1),
            )
        else:
            raise RuntimeError("Invalid type a1:%s a2:%s"%(type(p0),type(p1)))   
    @classmethod
    def createHorizontal(cls,x1,x2,y):
        """水平線を返します
        """
        return Segment((x1,y),(x2,y))
    @staticmethod
    def isParsable(v):
        return isinstance(v,Segment) or isArrayable(v,2) and Point.isParsable(v[0]) and Point.isParsable(v[1])              
    def __str__(self)->str:
        return str((self.topEdge.xy,self.bottomEdge.xy)) 
    @property
    def p0(self)->Point:
        return self._d[0]
    @property
    def p1(self)->Point:
        return self._d[1]
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
        return Point(0.5*(self.p0.x+self.p1.x),0.5*(self.p0.y+self.p1.y))
    @property
    def degrees(self):
        """線分の角度を計算します。"""
        r=math.atan2(self.p0.y-self.p1.y,self.p0.x-self.p1.x)
        return math.degrees((r if r>=0 else math.pi+r))%180 # 0から180度に直す
    def toTuple(self):
        return (self.p0.toTuple(),self.p1.toTuple())
    def distanceToPoint(self,xy:Point.PARSABLE)->float:
        """この線分と点(x,y)の距離を計算します。
        """
        def cross2(p:Point, q:Point):
            return p.x*q.y - p.y*q.x
        def dot2(p:Point, q:Point):
            return p.x*q.x + p.y*q.y
        def dist2(p:Point):
            return p.x**2 + p.y**2
        # Shortest distance between a line segment (p0-p1) and a point x
        xy=xy if isinstance(xy,Point) else Point(xy)
        p0=self.p0
        p1=self.p1
        z0 = Point(p1.x - p0.x, p1.y - p0.y)
        z1 = Point(xy.x - p0.x, xy.y - p0.y)
        if 0 <= dot2(z0, z1) <= dist2(z0):
            return abs(cross2(z0, z1)) / dist2(z0)**.5
        z2 = (xy.x - p1.x, xy.y - p1.y)
        return min(dist2(z1), dist2(z2))**.5
    def isIntersects(self,cd:"Segment.PARSABLE")->bool:
        """線分同士の交差を判定します。"""
        ab=self
        cd=cd if isinstance(cd,Segment) else Segment(cd)
        a=ab.p0
        b=ab.p1
        c=cd.p0
        d=cd.p1
        s = (a.x - b.x) * (c.y - a.y) - (a.y - b.y) * (c.x - a.x)
        t = (a.x - b.x) * (d.y - a.y) - (a.y - b.y) * (d.x - a.x)
        if s * t > 0:
            return False
        s = (c.x - d.x) * (a.y - c.y) - (c.y - d.y) * (a.x - c.x)
        t = (c.x - d.x) * (b.y - c.y) - (c.y - d.y) * (b.x - c.x)
        if s * t > 0:
            return False
        return True



    @classmethod
    def margeSegment(cls,segment1:"Segment.PARSABLE",segment2:"Segment.PARSABLE",separategap=1,sidegap:float=1)->"Segment":
        """2つの線分が結合可能結合して新しい線分を返します。
        2つの線分の並行度が閾値以下で端点同士が範囲内にある時に、合成した線分を計算することができます。
        Args:
            segment1    1つめの線分
            segment2    2つめの線分
            separategap 再遠点の距離-２本の直線の長さ和の上限。線の分離の許容値です。
            sidegap それぞれの線について、最近点と直線の距離の和の上限。線の並行度の許容値です。
        """
        #4点の最遠点の組み合わせを求める
        segment1=segment1 if isinstance(segment1,Segment) else Segment(segment1)
        segment2=segment2 if isinstance(segment2,Segment) else Segment(segment2)
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
        far_segment=Segment(points[far_point_idx[0]],points[far_point_idx[1]])
        #再遠点距離が2本の直線の合計値＋マージンより大きければエラー
        if segment1.length+segment2.length+separategap<far_segment.length:
            return None
        #最近点と再遠点セグメントの距離を計算
        nf1=far_segment.distanceToPoint(points[near_point_idx[0]])
        nf2=far_segment.distanceToPoint(points[near_point_idx[1]])
        #print(nf1+nf2,l1.length+l2.length+0.0-far_segment.length)
        #最近点と再遠点セグメントの距離合計が閾値より大きければエラー
        if nf1+nf2>sidegap:
            return None
        return Segment(far_segment.p0,far_segment.p1)
    def move(self,dx=0,dy=0)->"Segment":
        """矩形を平行移動します。
        """
        return Segment((self.p0.x+dx,self.p0.y+dy),(self.p1.x+dx,self.p0.y+dy))



class Rect(BaseClass):
    PARSABLE=Union["Rect",Tuple[Point.PARSABLE,Point.PARSABLE]]
    def __init__(self,p0:Union[Point.PARSABLE,PARSABLE],p1:Point.PARSABLE=None):
        """コンストラクタです。
        初期化パラメータの指定にはいくつかの方法があります。
        Args:
            p0のみ:Rect,Rect.PARSABLE,dict
            p0,p1:Point.PARSABLE,Point.PARSABLE            
        """
        try:
            if p1 is None:
                if isinstance(p0,Rect):
                    #RECT,None
                    self._d=p0._d
                elif isArrayable(p0,2) and Point.isParsable(p0[0]) and Point.isParsable(p0[1]):
                    #Tuple[Point.PARSABLE,Point.PARSABLE],None
                    self._d=(
                        p0[0] if isinstance(p0[0],Point) else Point(p0[0]),
                        p0[1] if isinstance(p0[1],Point) else Point(p0[1]),
                    )
                elif isinstance(p0,dict) and len(p0)==1:
                    #dict拡張構文
                    if "ltwh" in p0:
                        self._d=((p0[0],p0[1]),(p0[0]+p0[2],p0[1]+p0[3]))
                    elif "ltw" in p0:
                        self._d=((p0[0],p0[1]),(p0[0]+p0[2],p0[1]))
                    else:
                        raise RuntimeError("Invalid type a1:%s"%(type(p0)))     
                else:
                    raise RuntimeError("Invalid type a1:%s"%(type(p0)))     
            elif Point.isParsable(p0) and Point.isParsable(p1):
                self._d=(
                    p0 if isinstance(p0,Point) else Point(p0),
                    p1 if isinstance(p1,Point) else Point(p1),
                )
            else:
                raise RuntimeError("Invalid type a1:%s a2:%s"%(type(p0),type(p1)))     
            assert(self.left<=self.right)
            assert(self.top>=self.bottom)
        except:
            raise
    def __str__(self) -> str:
        return str((self.p0,self.p1))
    @staticmethod
    def isParsable(v):
        return isinstance(v,Rect) or isArrayable(v,2) and Point.isParsable(v[0]) and Point.isParsable(v[1])              
    def __str__(self)->str:
        return str((self.leftTop.xy,self.rightBottom.xy))
    @property
    def top(self)->float:
        return self._d[0].y
    @property
    def left(self)->float:
        return self._d[0].x
    @property
    def right(self)->float:
        return self._d[1].x
    @property
    def bottom(self)->float:
        return self._d[1].y
    @property
    def leftTop(self)->Point:
        return self._d[0]
    @property
    def rightBottom(self)->Point:
        return self._d[1]
    @property
    def width(self):
        return self.right-self.left
    @property
    def height(self):
        return self.top-self.bottom
    def toSegments(self,mindist=1)->Tuple[Segment]:
        """矩形を直線の集合に分解します"""
        l=self.left
        t=self.top
        r=self.right
        b=self.bottom
        dy=abs(t-b)
        dx=abs(r-l)
        if dy<=mindist:
            c=(t+b)/2
            return (Segment((l,c),(r,c)),)
        if dx<=mindist:
            c=(l+r)/2
            return (Segment((c,t),(c,b)),)
        #４本の線にする
        return (
            Segment((l,t),(l,b)),
            Segment((l,b),(r,b)),
            Segment((r,b),(r,t)),
            Segment((r,t),(l,t)))
    def toPoints(self)->Tuple[Point]:
        """LT,LB,RB,RTの順で４頂点を返します。
        """
        return (self._d[0],Point(self.left,self.bottom),self._d[1],Point(self.right,self.top))

    def toTuple(self):
        return (self._d[0].toTuple(),self._d[1].toTuple())

    def isInside(self,target:Union[Point.PARSABLE,Segment,"Rect.PARSABLE",List[Point.PARSABLE]])->bool:
        """対象がRECTの内側にあるかを返します。

        targetの型毎の判定基準
            Point 矩形内に座標がある場合true
            Segment 矩形内に両方の端点がある場合true
            Rect 矩形内に４点がある場合true
            List[Point.PARSABLE] 全ての点が矩形の中にある場合true
        """
        if isinstance(target,Point):
            return self.left<=target.x and target.x<=self.right and self.top>=target.y and target.y>=self.bottom
        if isinstance(target,Segment):
            return self.left<=target.leftEdge.x and target.rightEdge.x<=self.right and self.top>=target.topEdge.y and target.bottomEdge.y>=self.bottom
        if isinstance(target,Rect):
            return self.left<=target.left and target.right<=self.right and self.top>=target.top and target.bottom>=self.bottom
        if isArrayable(target):
            for i in target:
                if not self.isInside(i if isinstance(i,Point) else Point(i)):
                    return False
            return True
        if Point.isParsable(target):
            return self.isInside(Point(target))
        if Segment.isParsable(target):
            return self.isInside(Segment(target))
        if Rect.isParsable(target):
            return self.isInside(Rect(target))
        else:
            raise RuntimeError("Invalid type %s"%(type(target)))   
    def isOverwrap(self,target:Union[Point.PARSABLE,Segment.PARSABLE,"Rect.PARSABLE"])->bool:
        """対象と矩形の重なりを返します。
        targetの型毎の結果は以下の通りです。
            Point 矩形内に座標がある場合true(isInsideの結果と同じ)
            Segment 矩形の４辺の何れかと交わる場合、または矩形内にある場合true
            Rect 矩形内に対象の頂点がある場合、または対象の中に矩形の頂点がある場合true
            List[Point.PARSABLE] 何れかの頂点がRECTの内側にある場合
        """
        if isinstance(target,Point):
            return self.isInside(target)
        if isinstance(target,Segment):
            for s in self.toSegments(0):
                if target.isIntersects(s):
                    return True
            return self.isInside(target)
        if isinstance(target,Rect):
            return self.isOverwrap(target.toPoints()) or target.isOverwrap(self.toPoints())
        if isArrayable(target):
            for i in target:
                if self.isInside(i if isinstance(i,Point) else Point(i)):
                    return True
            return False
        if Point.isParsable(target):
            return self.isOverwrap(Point(target))
        if Segment.isParsable(target):
            return self.isOverwrap(Segment(target))
        if Rect.isParsable(target):
            return self.isOverwrap(Rect(target))
        else:
            raise RuntimeError("Invalid type %s"%(type(target)))   



    def move(self,dx=0,dy=0)->"Rect":
        """矩形を平行移動します。
        """
        return Rect((self.left+dx,self.top+dy),(self.right+dx,self.bottom+dy))

# r=Rect(((0,10),(10,0)))
# print(r.isOverwrap(Rect((1,6),(1,6))))

#%%



#%%
class RectList(BaseList):
    PARSABLE=Union[Collection[Union[Rect.PARSABLE,"PARSABLE"]]]
    def __init__(self,v:Union[Rect.PARSABLE,PARSABLE]=None):
        super().__init__(v.data if isinstance(v,RectList) else RectList._parse(v))
    def __str__(self) -> str:
        return "".join([str(i)+"\n" for i in self])
    @staticmethod
    def _parse(v:PARSABLE)->List[Rect]:
        r=list()
        if v is None:
            return r
        def appendfunc(l,t):
            if isinstance(t,Rect):
                l.append(t)
            elif Rect.isParsable(t):
                l.append(Rect(t))
            elif isArrayable(t):
                for i in t:
                    appendfunc(l,i)
            else:
                raise RuntimeError("Invalid type %s %s"%(type(v),str(v)))
        appendfunc(r,v)
        return r

    def toSegments(self,minwidth=1)->"SegmentList":
        self=self if isinstance(self,RectList) else RectList(self)
        l=SegmentList()
        for i in self:
            for j in i.toSegments(minwidth):
                l.append(j)
        return l
    def toRect(self,rect_constructor=None)->Rect:
        """包括するボックスを返します。
        """
        assert(len(self)>0)
        l=self[0].left
        r=self[0].right
        t=self[0].top
        b=self[0].bottom
        for i in self[1:]:
           l=min(l,i.left)
           r=max(r,i.right)
           t=max(t,i.top)
           b=min(b,i.bottom)
        return Rect(((l,t),(r,b)))
    @property
    def top(self):
        return max([i.top for i in self])
    @property
    def bottom(self):
        return min([i.bottom for i in self])
    @property
    def left(self):
        return min([i.left for i in self])
    @property
    def right(self):
        return max([i.right for i in self])
    def selectInside(self,key:Union["Rect.PARSABLE"]):
        """矩形内にある子要素を選択します。
        戻り値はこのリストの格納しているRect継承クラスです。
        """
        key=key if isinstance(key,Rect) else Rect(key)
        return self.select(lambda b:key.isInside(b))


#%%


class SegmentList(BaseList):
    """list互換のオブジェクト。
    """
    PARSABLE=Union[Collection[Union[Segment.PARSABLE,"PARSABLE"]]]
    def __init__(self,v:Union[Segment.PARSABLE,PARSABLE]=None):
        super().__init__(v.data if isinstance(v,SegmentList) else SegmentList._parse(v))
    @staticmethod
    def _parse(v:PARSABLE):
        r=list()
        if v is None:
            return r
        def appendfunc(l,t):
            if isinstance(t,Segment):
                l.append(t)
            elif Segment.isParsable(t):
                l.append(Segment(t))
            elif isArrayable(t):
                for i in t:
                    appendfunc(l,i)
            else:
                raise RuntimeError("Invalid type %s %s"%(type(v),str(v)))
        appendfunc(r,v)
        return r
    def margedStraights(self,separategap=2,sidegap=3)->"SegmentList":
        """近似線分を結合したリストを返します。
        """
        lines=SegmentList(self)
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
        return lines        
    def select(self,where)->"SegmentList":
         return SegmentList([i for i in self if where(i)]) 
    def selectByDegree(self,degrees,gap)->"SegmentList":
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
    def selectHorizontals(self,gap=0.01)->"SegmentList":
        """水平線だけのLinesを生成します
        """
        return self.selectByDegree(0,gap)
    def selectVerticals(self,gap=0.01)->"SegmentList":
        """垂直線だけのLinesを生成します
        """
        return self.selectByDegree(90,gap)





#%%




#%%