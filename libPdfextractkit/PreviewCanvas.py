from typing import Callable, List,Tuple,Union,Collection
import re
from pdfextractkit import Page
from pekgl import Rect,Segment
from PIL import Image, ImageDraw
from numbers import Number
import math
class PreviewCanvas:
    """PillowライブラリでPdfのページプレビューを表示するためのクラスです。
    """
    def __init__(self,layout:Union[Page,Tuple[Number,Number]],size:Number=None):
        
        def parseLayout(p):
            if isinstance(p,Page):
                box=p.mediaBox
                return (box[2]-box[0],box[3]-box[1])#R-L,T-B
            elif isinstance(p,Collection):
                return p
        pw,ph=parseLayout(layout)
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
    def line(self,xy:Segment.PARSABLE,color="black",width=1):
        xy=xy if isinstance(xy,Segment) else Segment(xy)
        h=self._im.height
        self._draw.line([(xy.p0.x,h-xy.p0.y),(xy.p1.x,h-xy.p1.y)],fill=color, width=width)
    def rect(self,rect:Rect.PARSABLE,fill=None,outline="black",width=1):
        rect=rect if isinstance(rect,Rect) else Rect(rect)
        h=self._im.height
        self._draw.rectangle([(rect.left,h-rect.top),(rect.right,h-rect.bottom)], fill=fill, outline=outline,  width=width)
    def show(self):
        self._im.show()
    @property
    def image(self)->Image:
        return self._im