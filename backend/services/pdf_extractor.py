import pdfplumber

class PDFTextExtractor:
    def __init__(self):
        pass
    
    def extract_text_from_pdf(self, file_path):
        """
        Extract text from PDF file
        """
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise Exception(f"PDF extraction error: {str(e)}")
        
        return text
