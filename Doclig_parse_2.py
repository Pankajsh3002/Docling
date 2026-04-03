import os
# Bypasses the 'cl.exe' compiler error on Windows
os.environ["TORCH_COMPILE_DISABLE"] = "1"

import pytesseract
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.types.doc import PictureItem, TableItem, TextItem
from PIL import Image

# 1. Setup Tesseract Path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 2. Setup Docling with local models
local_models_path = r"D:\Python_AI\NLP\Docling\docling_models"

pipeline_options = PdfPipelineOptions()
pipeline_options.artifacts_path = local_models_path
pipeline_options.do_ocr = False 
pipeline_options.do_table_structure = True
pipeline_options.images_scale = 2.0 
pipeline_options.generate_page_images = True
pipeline_options.generate_picture_images = True
pipeline_options.do_picture_classification = True 

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

# 3. Convert
pdf_path = "Hindi_English PDF_3.pdf"
result = converter.convert(pdf_path)
doc = result.document

# 4. Iterate and Replace
# 4. Extract OCR text and store with order
ocr_texts = []  # Use list to maintain order

for node, level in doc.iterate_items():
    if isinstance(node, PictureItem):
        print("Image Found")
        pil_image = node.get_image(doc)
        
        if pil_image:
            print("get True - Starting Pytesseract OCR")
            ocr_text = pytesseract.image_to_string(pil_image, lang="hin+eng").strip()
            
            if ocr_text:
                ocr_texts.append(ocr_text)
                print(f"OCR Text {len(ocr_texts)}: {ocr_text[:50]}...")

# 5. Export to Markdown
markdown_output = doc.export_to_markdown()

# Debug: Check what the markdown looks like
print("\n=== MARKDOWN PREVIEW (first 1000 chars) ===")
print(markdown_output[:1000])
print("=== END PREVIEW ===\n")

# Try multiple image patterns that Docling might use
import re

# Pattern 1: Standard markdown images ![alt](path)
pattern1 = r'!\[.*?\]\(.*?\)'
matches1 = re.findall(pattern1, markdown_output)

# Pattern 2: HTML img tags
pattern2 = r'<img[^>]*>'
matches2 = re.findall(pattern2, markdown_output)

# Pattern 3: Docling might use <!-- image --> comments
pattern3 = r'<!--.*?image.*?-->'
matches3 = re.findall(pattern3, markdown_output, re.IGNORECASE)

# Pattern 4: Figure references
pattern4 = r'\[Figure \d+\]|\(Figure \d+\)'
matches4 = re.findall(pattern4, markdown_output)

print(f"Found {len(matches1)} standard markdown images")
print(f"Found {len(matches2)} HTML img tags")
print(f"Found {len(matches3)} image comments")
print(f"Found {len(matches4)} figure references")

# Use whichever pattern found matches
if matches1:
    image_pattern = pattern1
    print("Using standard markdown pattern")
elif matches2:
    image_pattern = pattern2
    print("Using HTML img pattern")
elif matches3:
    image_pattern = pattern3
    print("Using comment pattern")
elif matches4:
    image_pattern = pattern4
    print("Using figure reference pattern")
else:
    print("No image markers found - writing sample to check manually")
    with open("debug_markdown.md", "w", encoding="utf-8") as f:
        f.write(markdown_output)
    print("Check debug_markdown.md to see the format")
    image_pattern = None

# Insert OCR text if we found a pattern
if image_pattern:
    parts = re.split(f'({image_pattern})', markdown_output)
    
    enhanced_markdown = ""
    ocr_index = 0
    
    for part in parts:
        enhanced_markdown += part
        
        if re.match(image_pattern, part):
            if ocr_index < len(ocr_texts):
                enhanced_markdown += f"\n\n{ocr_texts[ocr_index]}\n\n"
                ocr_index += 1
    
    with open("hybrid_output.md", "w", encoding="utf-8") as f:
        f.write(enhanced_markdown)
    
    print(f"Process complete. Inserted {ocr_index} OCR texts. Check hybrid_output.md")
else:
    # Fallback: append at end
    enhanced_markdown = markdown_output
    for idx, ocr_text in enumerate(ocr_texts, 1):
        enhanced_markdown += f"\n\n### Image {idx} OCR Text\n\n{ocr_text}\n"
    
    with open("hybrid_output.md", "w", encoding="utf-8") as f:
        f.write(enhanced_markdown)
    
    print(f"Could not find image markers. Appended {len(ocr_texts)} OCR texts at end.")


# 5. Export to Markdown
# This maintains your tables (County, State, Field) and lists (Phase One, etc.)
# markdown_output = doc.export_to_markdown()

# with open("hybrid_output.md", "w", encoding="utf-8") as f:
#     f.write(markdown_output)

# print("Process complete. Check hybrid_output.md")