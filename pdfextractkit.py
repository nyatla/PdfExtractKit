"""
See https://blog.imind.jp/entry/2019/10/18/025658
"""
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage,PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager,PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import (
    LAParams,
    LTContainer,
    LTImage,
    LTItem,
    LTRect,
    LTText,
    LTTextLine,LTChar,LTLine
)
from enum import Enum
from typing import Callable, List,Tuple,Union
import pandas
import re

from pekgl import Rect,Segment,RectList

class BoxLayout(Enum):
    """レイアウトのソートルール。
    """
    LEFT_TO_RIGHT=1
    TOP_TO_BOTTOM_LEFT_TO_RIGHT=2
    TOP_TO_BOTTOM=3
    LEFT_TO_RIGHT_TOP_TO_BOTTOM=4
class BoxType(Enum):
    """探索するPDFオブジェクトタイプを識別するための値。
    """
    CHAR =0   #テキストオブジェクト(CHAR又はTEXT)
    TEXT =1   #テキストオブジェクト(CHAR又はTEXT)
    RECT =2   #RECTオブジェクト
    LINE =3
    IMAGE=4   #画像オブジェクト
    ANY  =5   #全てのオブジェクト
    @staticmethod
    def toEnum(v):
        return      BoxType.CHAR if isinstance(v,LTChar) \
            else    (BoxType.TEXT if isinstance(v,LTText) \
            else    (BoxType.LINE if isinstance(v,LTLine) \
            else    (BoxType.RECT if isinstance(v,LTRect) \
            else    (BoxType.IMAGE if isinstance(v,LTImage) \
            else    type(v)))))

class Box(Rect):
    def __init__(self,lt_rb,boxtype,text):
        super().__init__(lt_rb)
        self.text:str=text
        self.type=type
        return
    def trim(self,remove_gaps=False):
        """トリミングしたtextを返します。
        """
        if self.text is None:
            return None
        s=self.text.split()
        if remove_gaps:
            s=re.sub("[ \u3000]","",s)
        return s



class BoxSet(RectList):
    def __init__(self,boxset:List[Box],order=None):
        super().__init__(boxset)
        self._cache={}
    @property
    def text(self):
        """ボックス内のテキストを先頭から連結して返します。
        """
        if "text" not in self._cache:
            self._cache["text"]="".join([i.text for i in self if i.text is not None])
        return self._cache["text"]

    def toTextBox(self):
        """ボックスを取りまとめます。
        結果はリストの順番で文字列を連結したTEXT包括ボックスです。
        """
        r=super().toRect()
        text=[self[0].text] if  self[0] is not None else []
        for i in self[1:]:
           if i.text is not None:
               text.append(i.text)
        return Box(r.toTuple(),BoxType.TEXT,"".join(text) if len(text)>0 else None)

    def selectInHorizontalSegment():
        pass
    def selectOnHorizontalSegment():
        pass
    def sortLtoR():
        """左から右にソートします。
        """
        pass
    def sortTtoB():
        """上から下にソートします。
        """
        pass
    def sortLtoRandTtoB():
        pass
    def sortTtoBLtoR():
        pass

   


        
    # def trim(self,remove_gaps=False):
    #     '''
    #     ボックス内のテキストをトリミングして、空文字列の要素をリストから除去したリストを返します。
    #     Args:
    #         remove_gapsがTrueなら、文字列間の空白を除去します。
    #     '''

    #     r=BoxSet()
    #     for i:Box in self:
    #         ti.text
    #         pass
    #     df=self._df
    #     df['text'] = df['text'].map(lambda x:x.strip())
    #     df=pandas.DataFrame(df[[len(i)>0  for i in df["text"]]])
    #     if remove_gaps:
    #         df.loc[:,"text"]=[re.sub("[ \u3000]","",i) for i in df["text"]]
    #     return BoxSet(df)
    def textOf(self,text):
        """テキストが一致するBoxSetを返します。
        """
        return self.select(lambda x: x.text==text) #キーの探索       
    def select(self,where,order:BoxLayout=None):
        """
        要素ごとにwhereに指定した関数で評価し、trueになったリストを返します。
        Args:
            where   def(df)->boolの関数式
            order   要素のソート方法
        """
        df=self._df[[where(i) for i in self._df.itertuples()]]
        return BoxSet(df,order)
    def onHorizontalLine(self,x1,x2,y,order:BoxLayout=BoxLayout.LEFT_TO_RIGHT):
        """x1,yとx,2,yを結ぶ直線と重なるオブジェクトの集合を生成します。
        """
        return self.onBox(x1,y,x2,y,order)
    def onBox(self,x1,y1,x2,y2,order=BoxLayout.TOP_TO_BOTTOM_LEFT_TO_RIGHT):
        """x1,y1とx2,y2で定義した矩形と重なる集合を生成します。
        """
        l=min(x1,x2)
        r=max(x1,x2)
        t=max(y1,y2)
        b=min(y1,y2)
        df=self._df
        df=df[(l<=df["right"]) & (df["left"]<=r)& (b<=df["top"]) & (df["bottom"]<=t)]
        return BoxSet(df,order)
    def innerBox(self,x1,y1,x2,y2,order=BoxLayout.TOP_TO_BOTTOM_LEFT_TO_RIGHT):
        """x1,y1とx2,y2で定義した矩形内にある集合を生成します。
        """
        l=min(x1,x2)
        r=max(x1,x2)
        t=max(y1,y2)
        b=min(y1,y2)
        df=self._df
        df=df[(l>=df["left"]) & (df["right"]<=r)& (t>=df["top"]) & (df["bottom"]>=b)]
        return BoxSet(df,order)
    
    def traceX(self,x1,x2,y,order:BoxLayout=BoxLayout.LEFT_TO_RIGHT):
        """onHorizontalLineのエイリアス
        """
        print("このAPIは廃止しました。onHorizontalLineを使ってください。")
        return self.onHorizontalLine(x1,x2,y,order)
    def inBox(self,x1,y1,x2,y2,order=BoxLayout.TOP_TO_BOTTOM_LEFT_TO_RIGHT):
        print("このAPIは廃止しました。onBoxを使ってください。")
        return self.onBox(x1,y1,x2,y2,order)


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
        def getbox(layout,d):
            """矩形をフラット化
            """
            if not isinstance(layout, LTContainer):
                return d
            for obj in layout:
                if filter is None or not filter(obj):
                    continue
                d.append(Box(
                    ((obj.bbox[0],obj.bbox[3]),(obj.bbox[2],obj.bbox[1])),
                    BoxType.toEnum(obj),
                    obj.get_text() if hasattr(obj,"get_text") else None
                    ))
                getbox(obj,d)
            return d
        interpreter.process_page(self._page)
        layout = device.get_result()
        boxes=getbox(layout,list())
        return BoxSet(boxes)
    @property
    def mediaBox(self):
        """
        @Returns
        [left,top,right,height]
        """
        return self._page.mediabox
    def extract(self,filter:Union[Callable[[object],bool],BoxType]=None):
        """Pdfの構成要素を一次減のボックスセットに変換します。
        Args:

        filter:対象にするオブジェクトを判定するフィルタ式です。
            Callable(x)の場合、Pdfオブジェクトの評価関数として動作します。xの評価値がtrueのものを対象にします。
            BoxTypeの場合、抽象化されたボックス型に合致するものを対象にします。
            (NP)List[BoxType]の場合、リストに含まれる何れかの型を対象にします。
        """
        if isinstance(filter,BoxType):
            return self._internal_lookup(None,lambda x : BoxType.toEnum(x)==filter)
        return self._internal_lookup(None,filter)
    def lookup(self,line_overlap=0.5, char_margin=2.0, line_margin=0.5, word_margin=0.1, boxes_flow=0.5,detect_vertical=False):
        """文字列に結合したTextBoxを生成します。
        パラメータは以下を参照。
        https://pdfminersix.readthedocs.io/en/latest/reference/composable.html#laparams
        @Args
            target NoneまたはLTChar
        """
        filter=lambda x : isinstance(x,LTTextLine) #LTTextLineだけを得る
        return self._internal_lookup(LAParams(line_overlap=line_overlap,char_margin=char_margin,line_margin=line_margin,boxes_flow=boxes_flow,detect_vertical=detect_vertical,all_texts=True),LTTextLine)


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



from pekgl import Point,Rect
from PIL import Image, ImageDraw
import math
class PreviewCanvas:
    """PillowライブラリでPdfのページプレビューを表示するためのクラスです。
    """
    def __init__(self,page:Page,size:Union[float,int]=None):
        box=page.mediaBox
        pw=box[2]-box[0] #R-L
        ph=box[3]-box[1] #T-B
        if size is not None:
            r=size/math.sqrt(pw*pw+ph*ph)
            pw=r*pw
            ph=r*ph
        pw=round(pw)
        ph=round(ph)
        self._im = Image.new('RGB', (pw,ph),color="white")
        self._draw = ImageDraw.Draw(self._im)
    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        if self._im is not None:
            self._im.close()
    def line(self,xy:List[List[int]],color="black",width=1):
        h=self._im.height
        self._draw.line([(i[0],h-i[1]) for i in xy],fill=color, width=width)
    def rect(self,xy1,xy2,fill=None,outline="black",width=1):
        h=self._im.height
        self._draw.rectangle([(xy1[0],h-xy1[1]),(xy2[0],h-xy2[1])], fill=fill, outline=outline,  width=width)
    def show(self):
        self._im.show()
    @property
    def image(self)->Image:
        return self._im