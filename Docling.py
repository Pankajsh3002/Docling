from pathlib import Path
import pytesseract
from PIL import Image
# from surya.ocr import run_ocr
# from surya.model.detection.model import load_model as load_det_model
# from surya.model.detection.processor import load_processor as load_det_processor
# from surya.model.recognition.model import load_model as load_rec_model
# from surya.model.recognition.processor import load_processor as load_rec_processor
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat, DocItemLabel
from docling.datamodel.pipeline_options import PdfPipelineOptions
import os

os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

# --- Load Surya Models Once ---
# print("Loading Surya OCR models...")
# det_model     = load_det_model()
# det_processor = load_det_processor()
# rec_model     = load_rec_model()
# rec_processor = load_rec_processor()
# print("Surya models loaded.")


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def custom_tesseract_ocr(pil_image: Image.Image) -> str:
    try:
        # Convert properly
        pil_image = pil_image.convert("RGB")

        # Optional preprocessing (BOOST accuracy 🔥)
        import cv2
        import numpy as np

        img = np.array(pil_image)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

        return pytesseract.image_to_string(thresh, lang='eng')

    except Exception as e:
        return f"OCR Error: {e}"


# --- Surya OCR Function ---
def custom_surya_ocr_prediction(pil_image: Image.Image) -> str:
    predictions = run_ocr(
        [pil_image],
        [["en"]],
        det_model,
        det_processor,
        rec_model,
        rec_processor,
    )
    lines = [line.text for line in predictions[0].text_lines]
    return "\n".join(lines).strip()

# --- 1. Setup Paths ---
models_path = r"D:\Python_AI\NLP\Docling\docling_models"
source_pdf = r"D:\Python_AI\NLP\Docling\doc3.pdf"
output_md_path = "final_output.md"

# --- 2. Configure Pipeline ---
pipeline_options = PdfPipelineOptions(artifacts_path=models_path)
pipeline_options.do_ocr = False  
pipeline_options.do_table_structure = True
pipeline_options.generate_page_images = True       # Required for get_image() to work
pipeline_options.generate_picture_images = True    # Required for get_image() to work
pipeline_options.do_picture_classification = False
pipeline_options.images_scale = 2.0  # Increases resolution for better detection
# pipeline_options.pdf_backend_options.force_ocr = True
# pipeline_options.picture_classification_options.picture_area_threshold = 0  # Process ALL images

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# --- 3. Convert Document ---
print("Extracting document structure...")
result = converter.convert(source_pdf)
# print(result)


# --- 4. Initialize List ---
md_elements = []

# --- 5. Loop and Append ---
print("Processing elements...")
for element, level in result.document.iterate_items():
    
    # 1. Catch ALL heading types
    if element.label in [DocItemLabel.TITLE, DocItemLabel.SECTION_HEADER, DocItemLabel.PAGE_HEADER]:
        md_elements.append(f"# {element.text}")
        
    # 2. Catch standard text and list items
    elif element.label in [DocItemLabel.TEXT, DocItemLabel.LIST_ITEM]:
        md_elements.append(element.text)
        
    # 3. Catch Tables (With fallback for Image Screenshots)
    elif element.label == DocItemLabel.TABLE:
        table_md = element.export_to_markdown()
        
        if len(table_md.strip()) < 10: 
            print("Found an empty table screenshot. Sending to Surya OCR...")
            page_no = element.prov[0].page_no
            page = result.pages[page_no - 1]
            image_crop = element.get_image(page)
            ocr_text = custom_surya_ocr_prediction(image_crop)
            md_elements.append(f"> **Image Table Content:**\n> {ocr_text}")
        else:
            md_elements.append(table_md)
            
    # 4. Catch ALL image types (Pictures and Figures) ← ONLY THIS BLOCK CHANGED
    # elif element.label in [DocItemLabel.PICTURE, DocItemLabel.FIGURE, DocItemLabel.FORM, DocItemLabel.KEY_VALUE_REGION]:
    elif element.label in DocItemLabel.PICTURE:
        print("image")
        page_no = element.prov[0].page_no
        page = result.pages[page_no - 1]
        image_crop = element.get_image(page)

        if image_crop:
            print(f"Sending image crop from page {page_no} to Surya OCR...")
            ocr_text = custom_tesseract_ocr(image_crop)
            md_elements.append(f"> **Image Content:**\n> {ocr_text}")
        else:
            md_elements.append(f"> **Image on page {page_no} — could not crop]**")

# --- 6. Join and Save ---
print(f"Loop finished. Saving to {output_md_path}...")



final_markdown_string = "\n\n".join(md_elements)

with open(output_md_path, 'w', encoding='utf-8') as f:
    f.write(final_markdown_string)

print("Process completed successfully!")