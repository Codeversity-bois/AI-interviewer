from PyPDF2 import PdfReader
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import sys, os
# Add the project root to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# extract normal text 
def text_extraction(file_name):
    reader = PdfReader(file_name)
    page = reader.pages[0]
    text = page.extract_text()
    return text


# # OCR extraction
# def ocr_extraction(file_name):
#     reader = PdfReader(file_name)
#     number_of_pages = len(reader.pages)
#     images = convert_from_path(file_name, dpi = 3000, first_page=0, last_page=number_of_pages-1)
#     content = ""
#     for page_image in images:
#         extracted_text = pytesseract.image_to_string(page_image)
#         content+=" "+extracted_text
#     return content





# #output
# con = text_extraction("resume.pdf")
# # con = ocr_extraction("resume_ocr.pdf")
# print(con)
