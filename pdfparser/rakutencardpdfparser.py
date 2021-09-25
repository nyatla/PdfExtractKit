import os,sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from libPdfextractkit import PdfExtractKit
class RaktenCardPdfParser:
    class Data:
        def __init__(self,data):
            self.data=data
        def toList(self):
            d=self.data
            r=[]
            r.append(("ご利用カード",d["ご利用カード"]))
            r.append(("今回ご請求金額",d["今回ご請求金額"]))
            r.append(("お支払日",d["お支払日"]))
            r.append(("ご利用明細",))
            r.extend(d["ご利用明細"])
            return r    
    @classmethod
    def parse(cls,path,validationcheck=True)->Data:
        d={}
        with PdfExtractKit.load(path) as a:
            if len(a)>=3:
                raise Exception("明細の二枚目以降のレイアウトが分からないので実装してません。")
            cls._readPage1(a[0],d)
            # for i in range(1,len(a)):
            #     cls._readPage2(a[i],d)
        if validationcheck:
            if sum([i[-1] for i in d["ご利用明細"]])!=d["今回ご請求金額"]:
                raise Exception("明細の合計と明細の請求金額が一致しません。")
        return cls.Data(d)
    @classmethod
    def _readPage1(cls,page1,d):
        tbl=page1.lookup(word_margin=0.3).trim(True)
        table_key=tbl.textOf("利用者") #キーの探索
        t=page1.extract().trim(True)
        tbl=page1.extract().trim(True)
        d["ご利用カード"]=t.traceX(221,400,715).text
        d["今回ご請求金額"]=int(t.traceX(28,100,712).text.replace(",","").replace("円",""))
        d["お支払日"]=t.traceX(20,127,728).text
        details=[]
        l=table_key.bottom-(6.1+2)
        while l>100:
            ymd=t.traceX(31,60,l).text
            if len("".join(ymd))==0:
                l=l-14.04
                continue
            paid=t.traceX(65,210. ,l).text
            destination=t.traceX(215,241,l).text
            method=t.traceX(260,300.1,l).text
            amount=int(t.traceX(474,515,l).text.replace(",",""))
            l=l-14.04
            details.append([ymd,paid,destination,method,amount])
        d["ご利用明細"]=details
        return
    # @classmethod
    # def readPage2(self,page1,d):
    #     tbl=page1.lookup(word_margin=0.05).trim(True)
    #     table_key=tbl.textOf("ご利用先") #キーの探索

    #     t=page1.extract().trim(True)
    #     tbl=page1.extract().trim(True)
    #     details=[]
    #     l=table_key.bottom-8
    #     while l>57:
    #         ymd=[t.traceX(    0,29. ,l).text,t.traceX( 29.8,43. ,l).text,t.traceX( 43.9,56. ,l).text]
    #         if len("".join(ymd))==0:
    #             l=l-11.7
    #             continue
    #         ymd="%02d/%02d/%02d"%(int(ymd[0]),int(ymd[1]),int(ymd[2]))
    #         paid=t.traceX( 56.3,77. ,l).text
    #         destination=t.traceX( 77.9,294 ,l).text
    #         method=t.traceX(294.1,308.1,l).text
    #         amount=int(t.traceX(309.0,361.6,l).text)
    #         l=l-11.7
    #         details.append([ymd,paid,destination,method,amount])
    #     d["ご利用明細"]=d["ご利用明細"]+details
    #     return

