#!/bin/python3
import os,sys
sys.path.append(os.path.join(os.path.dirname("__file__"), '..'))
from libPdfextractkit import *
from pdfparser import RaktenCardPdfParser


import argparse
import csv

if __name__ == "__main__":
    """
        楽天カードの明細書からデータを抽出します。
        pdfファイルを１つCSVに変換する
            # python3 meisai01.pdf -o out.csv
        pdfファイルを連続してCSVに変換する
            # python3 meisai01.pdf meisai02.pdf -o out.csv
    """
    parser = argparse.ArgumentParser(description="")
    parser.add_argument('pdf', help='pdfファイル名 ...',type=str,nargs='+')
    parser.add_argument('-o', help='出力ファイル名',type=str,default=None)
    args=parser.parse_args()
    dest=args.o if args.o is not None else (args.pdf[0]+("" if len(args.pdf)==1 else "(%dfiles)"%(len(args.pdf))))+".csv"
    with open (dest,'w') as f:
        writer=csv.writer(f,delimiter="\t")
        for i in args.pdf:
            l=RaktenCardPdfParser.parse(i).toList()
            print(l[0],l[1],l[2])
            for j in l:
                writer.writerow(j)


