import os,sys
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))
from pdfextractkit import Box,BoxSet,BoxType,PdfExtractKit,Page
from PreviewCanvas import PreviewCanvas
from readers import TableReader