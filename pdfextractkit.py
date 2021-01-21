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
    LTTextLine,LTChar
)
"""
https://blog.imind.jp/entry/2019/10/18/025658
"""
from enum import Enum
from typing import List,Tuple
import pandas
import re
class TextLayout(Enum):
    LEFT_TO_RIGHT=1
    TOP_TO_BOTTOM_LEFT_TO_RIGHT=2

class TextBoxTable:
    def __init__(self,df,order=None):
        self.df=df if order is None else {
            TextLayout.LEFT_TO_RIGHT:lambda df:df.sort_values(['left'], ascending=[True]),
            TextLayout.TOP_TO_BOTTOM_LEFT_TO_RIGHT:lambda df:df.sort_values(['top','left'], ascending=[False, True]),
        }[order](df)        
    def trim(self,remove_gaps=False):
        '''
        テキストをトリミングする。空トリミングの結果、空になった要素は除外する。
        Args:
            remove_gapsがTrueなら、文字列間の空白を除去する。
        '''
        df=self.df
        df['text'] = df['text'].map(lambda x:x.strip())
        df=pandas.DataFrame(df[[len(i)>0  for i in df["text"]]])
        if remove_gaps:
            df.loc[:,"text"]=[re.sub("[ \u3000]","",i) for i in df["text"]]
        return TextBoxTable(df)
    def __len__(self):
        return len(self.df)        
    # def __iter__(self):
    #     return self.df.itertuples()
    def __getitem__(self,key):
        return TextBoxTable(self.df[key])
    def __str__(self):
        o=pandas.set_option('display.max_rows',99999)
        try:
            return str(self.df)
        finally:
            pandas.set_option('display.max_rows',o)
    @property
    def text(self):
        return "".join(self.df["text"])
    @property
    def bottom(self):
        return self.df["bottom"].min()
    @property
    def top(self):
        return self.df["top"].max()

    def select(self,where,order=None):
        """
        要素ごとにwhereに指定した関数で評価し、trueのものを新しいL
        """
        df=self.df[[where(i) for i in self.df.itertuples()]]
        return TextBoxTable(df,order)
    def textOf(self,text):
        """テキストの一致する項目のリストを返します。
        """
        return self.select(lambda x: x.text==text) #キーの探索       
    def traceX(self,x1,x2,y,order=TextLayout.LEFT_TO_RIGHT):
        """onHorizontalLineのエイリアス
        """
        return self.onHorizontalLine(x1,x2,y,order)
    def onHorizontalLine(self,x1,x2,y,order=TextLayout.LEFT_TO_RIGHT):
        """x1,yとx,2,yを結ぶ直線上の座標にある集合を生成する。
        """
        return self.inBox(x1,y,x2,y,order)
    def inBox(self,x1,y1,x2,y2,order=TextLayout.TOP_TO_BOTTOM_LEFT_TO_RIGHT):
        """x1,y1とx2,y2で定義した矩形内と重なる集合を生成する。
        """
        l=min(x1,x2)
        r=max(x1,x2)
        t=max(y1,y2)
        b=min(y1,y2)
        df=self.df
        df=df[(l<=df["right"]) & (df["left"]<=r)& (b<=df["top"]) & (df["bottom"]<=t)]
        return TextBoxTable(df,order)

class Page:
    def __init__(self,page):
        self._rsrcmgr = PDFResourceManager()
        self._page=page
        device = PDFPageAggregator(self._rsrcmgr)
        interpreter = PDFPageInterpreter(self._rsrcmgr, device)

    def _internal_lookup(self,laparams:LAParams,target=LTTextLine,order=TextLayout.TOP_TO_BOTTOM_LEFT_TO_RIGHT):
        device = PDFPageAggregator(self._rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(self._rsrcmgr, device)
        def get_objs(layout,d):
            if not isinstance(layout, LTContainer):
                return d
            for obj in layout:
                if isinstance(obj, target):
                    d.append([obj.bbox[0],obj.bbox[3],obj.bbox[2],obj.bbox[1],obj.get_text()])
                get_objs(obj,d)
            return d
        interpreter.process_page(self._page)
        layout = device.get_result()
        d=get_objs(layout,list())
        df=pandas.DataFrame(
            columns=["left","top","right","bottom","text"],
            # dtype=[("page",int),("left",float),("top",float),("right",float),("bottom",float),("text",object)],
            data=d)
        return TextBoxTable(df,order)
    def extract(self):
        return self._internal_lookup(None,LTChar)
    def lookup(self,line_overlap=0.5, char_margin=2.0, line_margin=0.5, word_margin=0.1, boxes_flow=0.5,detect_vertical=False):
        return self._internal_lookup(LAParams(line_overlap=line_overlap,char_margin=char_margin,line_margin=line_margin,boxes_flow=boxes_flow,detect_vertical=detect_vertical,all_texts=True))


class PdfExtractKit:
    @classmethod
    def load(cls,pdf_fpath):
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
