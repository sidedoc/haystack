from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
import os
from haystack.nodes import TextConverter, PDFToTextConverter, DocxToTextConverter
from haystack.nodes import PreProcessor
import uuid

app = FastAPI()

UPLOAD_FOLDER = "uploaded_files"

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'pdf', 'txt', 'doc', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.post("/upload/")
async def upload_file(clean_empty_lines: bool=Form(...),
                      clean_whitespace: bool=Form(...),
                      clean_header_footer: bool =Form(...),
                      split_length: int = Form(...),
                      split_overlap: int = Form(...),
                      file: UploadFile = File(...)):

    if not allowed_file(file.filename):
        return JSONResponse(content={"error": "Invalid file format"}, status_code=400)
    
    ext = file.filename.split('.')[1]
    new_filename = str(uuid.uuid4().hex)
    file_path = os.path.join(UPLOAD_FOLDER, new_filename+'.'+ext)
    # file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    
    text = ""
    if file.filename.lower().endswith('.txt'):
        converter = TextConverter(remove_numeric_tables=True, valid_languages=["en"])
        text = converter.convert(file_path=file_path, meta=None)[0]
    elif file.filename.lower().endswith('.pdf'):
        converter = PDFToTextConverter(remove_numeric_tables=True, valid_languages=["en"])
        text = converter.convert(file_path=file_path, meta=None)[0]
    elif file.filename.lower().endswith('.doc') or file.filename.lower().endswith('.docx'):
        converter = DocxToTextConverter(remove_numeric_tables=False, valid_languages=["en"])
        text = converter.convert(file_path=file_path, meta=None)[0]
    
    print(text)
    
    preprocessor = PreProcessor(
        clean_empty_lines=clean_empty_lines,
        clean_whitespace=clean_whitespace,
        clean_header_footer=clean_header_footer,
        split_length=split_length,
        split_overlap=split_overlap,
        add_page_number=True
    )
    
    docs_default = preprocessor.process([text])
    
    print(f"n_docs_input: 1\nn_docs_output: {len(docs_default)}")
    
    return {"message": "File uploaded and converted successfully", "text": docs_default}