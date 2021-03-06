# PdfExtractKit
幾何学的なセレクタでpdfから文字列を読み出すためのツールキットです。
クレジットカードの電子明細PDFを読みだしてCSVにしたりできます。

## セットアップ
```
pip install pdfminer pandas
```

## アプリケーション

### イオンカード電子明細をCSVに変換

```
$ python3 ./app/extractAeoncardPdf.py /mnt/d/tmp.wsl/meisai202009.pdf
('ご利用カード', 'イオンカード') ('今回ご請求金額', 99999) ('お支払日', '2020年9月2日（水）')
:
```

出力
```
ご利用カード	イオンカード
今回ご請求金額	99999
お支払日	2020年9月2日（水）
ご利用明細
20/06/30	本人	ＡＭＡＺＯＮ．ＣＯ．ＪＰ	１回	3333
20/07/11	本人	ＡＭＡＺＯＮ．ＣＯ．ＪＰ	１回	4444
：
20/07/20	本人	ＡＬＩＥＸＰＲＥＳＳ．ＣＯＭ	１回	5555
```

### 楽天カード電子明細をCSVに変換

```
$ python3 ./app/extractRaktenCardPdf.py /mnt/d/tmp.wsl/statement_202101.pdf
('ご利用カード', '楽天カード(VISA)') ('今回ご請求金額', 99999) ('お支払日', '2021年01月ご請求金額')
:
```

明細が複数ページにまたがるpdfは手元にないので対応していません。

## ライブラリ

pdfextractkit.pyがpdf読み出し用のライブラリです。
getstarted/getstarted.pyに一通りの昨日を実行するサンプルがあります。
```
$ python3 ./getstarted/getstarted.py
```

pdfparserにはそれぞれのpdfレイアウトに対応した読み出しクラスがあります。
pdfから読みだした情報をpythonオブジェクトに加工します。

