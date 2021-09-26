#%%
"""pdfextractkitのコアライブラリ。
pdfminerを隠ぺいするためのクラスなどを定義します。
"""
# import os,sys
# sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

"""
See https://blog.imind.jp/entry/2019/10/18/025658
"""
from numpy import number
from numpy.lib.arraysetops import isin
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage,PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager,PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import (
    LAParams,
    LTContainer,
    LTImage,
    LTRect,
    LTText,
    LTTextLine,LTChar,LTLine,LTTextBox
)
from enum import Enum
from typing import Callable, List,Tuple,Union,Collection
import re
from numbers import Number
from operator import itemgetter
from pekgl import Rect,Segment,RectList,isnumber


class BoxType(Enum):
    """探索するPDFオブジェクトタイプを識別するための値。
    """
    ANY  =0   #全てのオブジェクト
    CHAR =1   #テキストオブジェクト(CHAR又はTEXT)
    TEXT =2   #テキストオブジェクト(CHAR又はTEXT)
    RECT =3   #RECTオブジェクト
    LINE =4
    IMAGE=5   #画像オブジェクト
    @staticmethod
    def toEnum(v):
        return      BoxType.CHAR if isinstance(v,LTChar) \
            else    (BoxType.TEXT if isinstance(v,LTText) \
            else    (BoxType.LINE if isinstance(v,LTLine) \
            else    (BoxType.RECT if isinstance(v,LTRect) \
            else    (BoxType.IMAGE if isinstance(v,LTImage) \
            else    BoxType.ANY))))

class Box(Rect):
    def __init__(self,lt_rb:Rect.PARSABLE,boxtype,text):
        super().__init__(lt_rb)
        self.type=boxtype
        self.text:str=text
        return
    def trim(self,remove_gaps=False):
        """トリミングしたtextを返します。
        """
        if self.text is None:
            return None
        s=self.text.strip()
        if remove_gaps:
            s=re.sub("[ \u3000]","",s)
        return s
    def __str__(self) -> str:
        return str((super().__str__(),self.type,self.text))


class BoxSet(RectList):
    _CLS_WARN_FLAGS={}
    def __init__(self,boxset:List[Box]=None,order=None):
        super().__init__(boxset)
        self._cache={}
        self.kill_warning=False
    def selectByType(self,type:BoxType)->BoxType:
        """BoxTypeに合致するリストを返します。
        """
        return self.select(lambda x:x.type==type)
    @property
    def text(self):
        """ボックス内のテキストを先頭から連結して返します。テキストを持たない要素は無視します。
        """
        if "text" not in self._cache:
            self._cache["text"]="".join([i.text for i in self if i.text is not None])
        return self._cache["text"]
    def toBox(self)->Box:
        """Box集合をまとめて１つのボックスにします。
        結果はリストの順番で文字列を連結したTEXT包括ボックスです。
        @Returns
        Box、またはNoneです。
        """
        r=super().toRect()
        text=[]
        text.extend([i.text for i in self if i.text is not None])
        return Box(r.toTuple(),BoxType.TEXT,"".join(text) if len(text)>0 else None)
    def trimAll(self,remove_gaps=False)->"BoxSet":
        """全ての要素のテキストをトリミングして、有効なリストを生成します。
        """
        def operator(x:Box):
            t=x.trim(remove_gaps)
            return None if t is None or len(t)<1 else Box(x,x.type,t)
        return self.filter(operator)
    def readLine(self,key:Union[Segment.PARSABLE,Tuple[number,number,number]])->Box:
        """直線と重なる矩形を１つのBoxにまとめます。
        keyには、Segment.PARSABLE,又は(x1,x2,y)のタプルが使用できます。

        @Returns
            結果のBox、見つからなければNone。
            traceXから変更した場合、見つからない時にNoneを処理するようにしてください。
        """
        l=None
        if isinstance(key,Collection) and len(key)==3 and (False not in [isnumber(i) for i in key]):
            l=Segment((key[0],key[2]),(key[1],key[2]))
        elif Segment.isParsable(key):
            l=Segment(key)
        return self.select(lambda b: b.isOverwrap(l)).arrangeLR().toBox()
    def readBox(self,key:Union[Rect.PARSABLE])->Box:
        """矩形内の矩形を１つのBoxにまとめます。
        """
        return self.selectInside(key).arrangeLRTB().toBox()
    def readTextLines(self,rowmargin=1,sidemargin=3,)->"BoxSet":
        """boxset内のboxをテキストラインごとのBoxに取りまとめて新しいBoxSetを生成します。
        このアルゴリズムは、各Boxの縦軸中心線ごとにグループ化した後に、隣接したBox同士の距離が一定以下の
        ものだけをグループします。
        通常、TEXTタイプのBoxだけを対象にしますが、他のタイプのBoxが混じっていても動作はします。
        Args:
            rowmargin    縦軸中心線のグループ化マージンの最大値。
            sidemargin   隣接グループ化マージンの最大値。
        """
        cl=[((i.top+i.bottom)*0.5,i) for i in self]    #水平中央線ごとにソートしてまとめた(idx,Box)
        cl.sort(key=lambda x:x[1].left)                 #leftでソート
        cl.sort(key=itemgetter(0),reverse=True)                      #水平中央線でソート
        #垂直分割点の計算
        sps=([i+1 for i in range(len(cl)-1) if abs(cl[i+1][0]-cl[i][0])>rowmargin])
        sps=[0]+sps+[len(cl)]
        #水平中央線ごとにグループ化してリストに保存
        lines=[[j for j in cl[sps[i]:sps[i+1]]] for i in range(len(sps)-1)]
        texts=[]
        for line in lines:
            #水平端分割点の計算
            hps=([j+1 for j in range(len(line)-1) if abs(line[j+1][1].left-line[j][1].right)>sidemargin])
            hps=[0]+hps+[len(line)]
            #水平端で分割したテキストブロックをリストに追記
            #print(hps)
            texts.extend([[l for l in line[hps[k]:hps[k+1]]] for k in range(len(hps)-1)])
        
        #Boxに変換
        texts=[BoxSet([j[1] for j in i]).toBox() for i in texts if len(i)>0]#水平中央線ごとにソートしてまとめたBoxes
        return BoxSet(texts)


    def textOf(self,text)->Box:
        """テキストが一致するBoxを返します。
        """
        return self.select(lambda x: x.text==text) #キーの探索       


    def trim(self,remove_gaps=False):
        if "trim_warn" not in BoxSet._CLS_WARN_FLAGS:
            print("trim関数は廃止しました。trimAllを使ってください。")
            BoxSet._CLS_WARN_FLAGS["trim_warn"]=True
        return self.trimAll(remove_gaps)
    def traceX(self,x1,x2,y):
        """onHorizontalLineのエイリアス
        """
        if "traceX_warn" not in BoxSet._CLS_WARN_FLAGS:
            print("traceX関数は廃止しました。readLineを使ってください。")
            BoxSet._CLS_WARN_FLAGS["traceX_warn"]=True
        r=self.readLine((x1,x2,y))
        return Box(((0,0),(0,0)),BoxType.TEXT,"") if r is None else r

#%%
class Page:
    """Pdfの１ページに対応するクラスです。
    Pdfからレイアウト情報を生成する関数を定義します。
    """
    def __init__(self,page):
        self._rsrcmgr = PDFResourceManager()
        self._page=page
    def _internal_lookup(self,laparams:LAParams,filter:Callable):
        device = PDFPageAggregator(self._rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(self._rsrcmgr, device)
        def get_objs(layout,d):
            if not isinstance(layout, LTContainer):
                return d
            for obj in layout:
                if filter is None or filter(obj):
                    d.append(Box(
                        ((obj.bbox[0],obj.bbox[3]),(obj.bbox[2],obj.bbox[1])),
                        BoxType.toEnum(obj),
                        obj.get_text() if hasattr(obj,"get_text") else None
                        ))
                get_objs(obj,d)
            return d
        interpreter.process_page(self._page)
        layout = device.get_result()
        d=get_objs(layout,BoxSet())
        return d
    @property
    def mediaBox(self):
        """
        @Returns
        [left,top,right,height]
        """
        return self._page.mediabox
    def extract(self,filter:Union[Callable[[object],bool],BoxType,Collection[BoxType]]=None)->BoxSet:
        """Pdfの構成要素を一次減のボックスセットに変換します。
        Args:

        filter:対象にするオブジェクトを判定するフィルタ式です。
            Callable(x)の場合、Pdfオブジェクトの評価関数として動作します。xの評価値がtrueのものを対象にします。
            BoxTypeの場合、抽象化されたボックス型に合致するものを対象にします。
            List[BoxType]の場合、リストに含まれる何れかの型を対象にします。
        """
        if isinstance(filter,BoxType):
            return self._internal_lookup(None,lambda x : BoxType.toEnum(x)==filter)
        if isinstance(filter,Collection):
            return self._internal_lookup(None,lambda x : BoxType.toEnum(x) in filter)
        return self._internal_lookup(None,filter)
    def lookup(self,line_overlap=0.5, char_margin=2.0, line_margin=0.5, word_margin=0.1, boxes_flow=0.5,detect_vertical=False):
        """文字列に結合したTextBoxを生成します。
        パラメータは以下を参照。
        https://pdfminersix.readthedocs.io/en/latest/reference/composable.html#laparams
        @Args
            target NoneまたはLTChar
        """
        filter=lambda x : isinstance(x,LTTextLine) #LTTextBoxだけを得る
        return self._internal_lookup(LAParams(line_overlap=line_overlap,char_margin=char_margin,line_margin=line_margin,boxes_flow=boxes_flow,detect_vertical=detect_vertical,all_texts=True),filter)


class PdfExtractKit:
    """Pdfの展開クラスを生成します。#load関数を使って生成してください。
    ページごとにPageオブジェクトを格納します。
    ページにはインデクスを使ってアクセスできます。

    exapmle:
    with PdfExtractKit("my.pdf") as p:
        print("Pages %d"%(len(p)))
        for i in p:
            print(i.lookup().toList())
    """
    @classmethod
    def load(cls,pdf_fpath):
        """
        """
        fp=open(pdf_fpath, "rb")
        parser = PDFParser(fp)
        document = PDFDocument(parser)
        if not document.is_extractable:
            raise PDFTextExtractionNotAllowed
        # https://pdfminersix.readthedocs.io/en/latest/api/composable.html#
        pages=[Page(page) for page in PDFPage.create_pages(document)]
        return PdfExtractKit(fp,pages)
    def __init__(self,fp,pages):
        self._fp=fp
        self._pages=pages
    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        if self._fp is not None:
            self.close()
    def __len__(self):
        return len(self._pages)
    def __getitem__(self,key):
        return self._pages[key]
    def close(self):
        self._fp.close()
        self._fp=None              




