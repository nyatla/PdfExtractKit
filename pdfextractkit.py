"""
See https://blog.imind.jp/entry/2019/10/18/025658
"""
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfpage import PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
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
from typing import List,Tuple,Union
import pandas
import re



class BoxLayout(Enum):
    """レイアウトのソートルール。
    """
    LEFT_TO_RIGHT=1
    TOP_TO_BOTTOM_LEFT_TO_RIGHT=2
    TOP_TO_BOTTOM=3
    LEFT_TO_RIGHT_TOP_TO_BOTTOM=4

class BoxSet:
    class Box:
        def __init__(self,row):
            self.r=row
        def __str__(self):
            o=(
                pandas.set_option('display.max_rows',99999),
                pandas.set_option('display.max_columns',99999))
            try:
                return str(self.r)
            finally:
                pandas.set_option('display.max_rows',o[0])
                pandas.set_option('display.max_columns',o[1])
        @property
        def bottom(self):
            return self.r["bottom"]
        @property
        def top(self):
            return self.r["top"]
        @property
        def left(self):
            return self.r["left"]
        @property
        def right(self):
            return self.r["right"]
        @property
        def width(self):
            return self.right-self.left
        @property
        def height(self):
            return self.top-self.bottom

    def __init__(self,df,order=None):
        self._df=df if order is None else {
            BoxLayout.LEFT_TO_RIGHT:lambda df:df.sort_values(['left'], ascending=[True]),
            BoxLayout.TOP_TO_BOTTOM:lambda df:df.sort_values(['top'], ascending=[False]),
            BoxLayout.LEFT_TO_RIGHT_TOP_TO_BOTTOM:lambda df:df.sort_values(['left','top'], ascending=[True,False]),
            BoxLayout.TOP_TO_BOTTOM_LEFT_TO_RIGHT:lambda df:df.sort_values(['top','left'], ascending=[False, True]),
        }[order](df)
    def __iter__(self):
        self._itr_n=0
        return self
    def __next__(self):
        n=self._itr_n
        if n >= len(self._df):
            raise StopIteration
        n=n+1
        self._itr_n=n
        return BoxSet.Box(self._df.iloc[n-1])
    def __len__(self):
        """格納しているBox要素の数です。
        """
        return len(self._df)        
    def __getitem__(self,key:int):
        """n番目のレイアウトを返します。
        """
        return BoxSet.Box(self._df.loc[key])
    def __str__(self):
        o=(
            pandas.set_option('display.max_rows',99999),
            pandas.set_option('display.max_columns',99999))
        try:
            return str(self._df)
        finally:
            pandas.set_option('display.max_rows',o[0])
            pandas.set_option('display.max_columns',o[1])
    @property
    def text(self):
        """ボックス内のテキストを先頭から連結して返します。
        """
        return "".join(self._df["text"])
    @property
    def bottom(self):
        """ボックスの下端を返します。
        """
        return self._df["bottom"].min()
    @property
    def top(self):
        """ボックスの上端を返します。
        """
        return self._df["top"].max()
    @property
    def left(self):
        """ボックスの左端を返します。
        """
        return self._df["left"].min()
    @property
    def right(self):
        """ボックスの右端を返します。
        """
        return self._df["right"].max()
    def trim(self,remove_gaps=False):
        '''
        テキストをトリミングして、空文字列の要素をリストから除去したリストを返します。
        Args:
            remove_gapsがTrueなら、文字列間の空白を除去します。
        '''
        df=self._df
        df['text'] = df['text'].map(lambda x:x.strip())
        df=pandas.DataFrame(df[[len(i)>0  for i in df["text"]]])
        if remove_gaps:
            df.loc[:,"text"]=[re.sub("[ \u3000]","",i) for i in df["text"]]
        return BoxSet(df)
    def select(self,where,order:BoxLayout=None):
        """
        要素ごとにwhereに指定した関数で評価し、trueになったリストを返します。
        Args:
            where   def(df)->boolの関数式
            order   要素のソート方法
        """
        df=self._df[[where(i) for i in self._df.itertuples()]]
        return BoxSet(df,order)
    def textOf(self,text):
        """テキストの一致する要素のリストを返します。
        """
        return self.select(lambda x: x.text==text) #キーの探索       
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

class Target(Enum):
    """探索するPDFオブジェクトタイプを識別するための値。
    """
    CHAR =0   #テキストオブジェクト(CHAR又はTEXT)
    TEXT =1   #テキストオブジェクト(CHAR又はTEXT)
    RECT =2   #RECTオブジェクト
    LINE =3
    IMAGE=4   #画像オブジェクト
    ANY  =5   #全てのオブジェクト

class Page:
    """Pdfの１ページに対応するクラスです。
    Pdfからレイアウト情報を生成する関数を定義します。
    """
    def __init__(self,page):
        self._rsrcmgr = PDFResourceManager()
        self._page=page
        device = PDFPageAggregator(self._rsrcmgr)
        interpreter = PDFPageInterpreter(self._rsrcmgr, device)

    def _internal_lookup(self,laparams:LAParams,target,order=BoxLayout.TOP_TO_BOTTOM_LEFT_TO_RIGHT):
        device = PDFPageAggregator(self._rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(self._rsrcmgr, device)
        def type2Target(v):
            return      Target.CHAR if isinstance(v,LTChar) \
                else    (Target.TEXT if isinstance(v,LTText) \
                else    (Target.LINE if isinstance(v,LTLine) \
                else    (Target.RECT if isinstance(v,LTRect) \
                else    (Target.IMAGE if isinstance(v,LTImage) \
                else    type(v)))))
        def get_objs(layout,d):
            if not isinstance(layout, LTContainer):
                return d
            for obj in layout:
                if isinstance(obj, target):
                    d.append([obj.bbox[0],obj.bbox[3],obj.bbox[2],obj.bbox[1],obj.get_text() if hasattr(obj,"get_text") else None,type2Target(obj)])
                get_objs(obj,d)
            return d
        interpreter.process_page(self._page)
        layout = device.get_result()
        d=get_objs(layout,list())
        df=pandas.DataFrame(
            columns=["left","top","right","bottom","text","type"],
            # dtype=[("page",int),("left",float),("top",float),("right",float),("bottom",float),("text",object)],
            data=d)
        return BoxSet(df,order)
    @property
    def mediaBox(self):
        """
        @Returns
        [left,top,right,height]
        """
        return self._page.mediabox
    def extract(self,target:Target=None):
        """1文字単位に分解したTextBoxを生成します。
        """
        targetclass=LTChar if target is None else [LTChar,LTText,LTRect,LTLine,LTImage,LTItem][target.value]
        return self._internal_lookup(None,targetclass)
    def lookup(self,line_overlap=0.5, char_margin=2.0, line_margin=0.5, word_margin=0.1, boxes_flow=0.5,detect_vertical=False):
        """文字列に結合したTextBoxを生成します。
        パラメータは以下を参照。
        https://pdfminersix.readthedocs.io/en/latest/reference/composable.html#laparams
        @Args
            target NoneまたはLTChar
        """
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