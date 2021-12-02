#!/bin/python3
"""
    pdf内の単純表をjsonに変換します。
        # python3 table.pdf -o out.json

    出力するjsonの形式は以下の通りです。
    [
        {page:int,data:[parsed tables]},...
    ]
    テーブルはテーブルの行毎に1列づつ、セル内の行毎に配列で格納します。
"""

#%%
from datetime import date
from tqdm import tqdm
from logging import addLevelName
import os,sys
sys.path.append(os.path.join(os.path.dirname("__file__"), '..'))

from typing import Collection,List, Tuple
sys.path.append(os.path.join(os.path.dirname("__file__"), '..'))
from libPdfextractkit import Box, PdfExtractKit,PreviewCanvas,BoxType,BoxSet,TableReader,Page
import argparse
from typing import Collection,Dict,Union
import json




from app.extlibs.libNyatlanPython.syntaxparser import *
from app.extlibs.libNyatlanPython.jsontemplates import DataJson

#%%




if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('pdf', help='pdfファイル名',type=str)
    parser.add_argument('--filter', help='文字列のトリミングモード',choices=["none","trim","nogap"],type=str,default="none")
    parser.add_argument('--rowmargin', help='表認識の結合マージン',type=float,default=1)
    parser.add_argument('--sidemargin', help='表認識の結合マージン',type=float,default=3)
    parser.add_argument('--lineseparategap', help='表認識の結合マージン',type=float,default=0.1)
    parser.add_argument('--linesidegap', help='表認識の結合マージン',type=float,default=3.)
    parser.add_argument('--pages', help='ページ識別子 all|1,2..|1-2|1-|1:2',type=str,default="all")
    parser.add_argument('--description', help='descriptionフィールドの値',type=str,default="")
    parser.add_argument('-o', help='出力ファイル名',type=str,default=None)
    args=parser.parse_args()
    dest=args.o if args.o is not None else args.pdf+".json"
    ftrim=args.filter=="trim" or args.filter=="nogap"
    fnogap=args.filter=="nogap"



    params=args.__dict__
    version="PdfExtractKit.app.tableScraper/0.1"
    ret=None
    with PdfExtractKit.load(args.pdf) as doc:
        print("%s has %d pages."%(args.pdf,len(doc)))
        pl=SyntaxParser.toIntList(args.pages,minimum=1,maximum=len(doc))
        print("pages: %s"%(str(pl)))
        pbar = tqdm(total=len(pl))
        data=[]
        for p in pl:
            #ページ全体をパース
            tr=TableReader(doc[p-1].extract(),rowmargin=args.rowmargin,sidemargin=args.sidemargin,lineseparategap=args.lineseparategap,linesidegap=args.linesidegap)
            data.append({"page":p,"table":tr.toList(ftrim,fnogap)})
            pbar.update(1)
        pbar.close()
        dj=DataJson.create(version,data,description=args.description,params=params)
        dj.save(args.pdf+".json" if args.o is None else args.o)
