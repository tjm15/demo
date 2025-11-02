"""
Extract paragraphs from PDF policy documents.
Outputs JSONL with: {doc_id, para_ref, text, page}
"""
import sys
import json
from pathlib import Path

def extract_paras(pdf_path: Path) -> list:
    """
    Extract paragraphs from PDF.
    In production, use pdfminer.six or surya-ocr.
    """
    doc_id = pdf_path.stem
    
    # Mock extraction
    return [
        {
            "doc_id": doc_id,
            "para_ref": f"{doc_id.upper()}-1",
            "text": "Sample policy paragraph extracted from PDF. Development should support sustainable growth patterns.",
            "page": 1
        },
        {
            "doc_id": doc_id,
            "para_ref": f"{doc_id.upper()}-2", 
            "text": "All development must demonstrate high quality design that respects local character.",
            "page": 2
        }
    ]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_paras.py <pdf_files...>")
        sys.exit(1)
    
    output_file = Path("fixtures/lpa_demo/policy_paras.jsonl")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        for pdf_file in sys.argv[1:]:
            pdf_path = Path(pdf_file)
            if not pdf_path.exists():
                print(f"Warning: {pdf_file} not found, skipping")
                continue
            
            print(f"Extracting {pdf_path.name}...")
            paras = extract_paras(pdf_path)
            
            for para in paras:
                f.write(json.dumps(para) + '\n')
    
    print(f"✓ Extracted to {output_file}")
