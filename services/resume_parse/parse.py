from PyPDF2 import PdfReader
from io import BytesIO
from docx import Document


def parse_pdf(file):
    cls = False
    if isinstance(file, str):
        file = open(file, 'rb')
        cls = True

    pdf_reader = PdfReader(file)
    text = ""
    
    for page in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page].extract_text()
    
    if cls:
        file.close()    
    
    return text


def parse_docx(docx):
    docx.seek(0)
    content = docx.read()
        
    doc = Document(BytesIO(content))
    text = ""

    for para in doc.paragraphs:
        text += '\n' + para.text

    return text