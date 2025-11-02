"""File analysis service using local Ollama VLM.

Endpoints:
- POST /services/files/analyze-image: analyze a single image with optional prompt
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from typing import Optional
from pdfminer.high_level import extract_text as pdf_extract_text

from modules import llm

router = APIRouter()


class ImageAnalysisResponse(BaseModel):
    model: str
    summary: str


@router.post("/analyze-image", response_model=ImageAnalysisResponse)
async def analyze_image(
    image: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
):
    """Analyze an uploaded image using the configured VLM model via Ollama."""
    if image.content_type not in ("image/png", "image/jpeg", "image/jpg", "image/webp"):
        raise HTTPException(status_code=400, detail="Unsupported image type")

    data = await image.read()
    try:
        text = await llm.analyze_image(data, prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {e}")

    return ImageAnalysisResponse(model=llm.VLM_MODEL, summary=text or "")


class TextAnalysisRequest(BaseModel):
    text: str
    prompt: Optional[str] = None


class TextAnalysisResponse(BaseModel):
    model: str
    summary: str


@router.post("/analyze-text", response_model=TextAnalysisResponse)
async def analyze_text(req: TextAnalysisRequest):
    """Analyze raw text with the text LLM and produce a planning-focused summary."""
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    guidance = req.prompt or (
        "Summarize the planning-relevant content: key policies and references, constraints, design issues, "
        "and any potential conditions. Be concise and structured with bullet points."
    )
    full_prompt = f"{guidance}\n\nTEXT:\n{req.text[:200000]}"  # safety cap
    result = await llm.generate_text(full_prompt)
    return TextAnalysisResponse(model=llm.TEXT_MODEL, summary=result or "")


@router.post("/analyze-pdf", response_model=TextAnalysisResponse)
async def analyze_pdf(file: UploadFile = File(...), prompt: Optional[str] = Form(None)):
    """Extract text from a PDF and analyze it via the text LLM."""
    if file.content_type not in ("application/pdf",):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    data = await file.read()
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="PDF too large (25MB limit)")

    try:
        # pdfminer expects a file-like path or fp; we can write to a temp buffer
        # For simplicity, write to a temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
            tmp.write(data)
            tmp.flush()
            text = pdf_extract_text(tmp.name) or ""
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF extraction failed: {e}")

    if not text.strip():
        raise HTTPException(status_code=400, detail="No extractable text found in PDF")

    guidance = prompt or (
        "Read the document and provide a concise planning-focused summary: applicable policies/sections, "
        "constraints (heritage, flood, design), tests/standards, and any conditions implied. Use bullet points."
    )
    full_prompt = f"{guidance}\n\nEXTRACT:\n{text[:200000]}"  # safety cap
    result = await llm.generate_text(full_prompt)
    return TextAnalysisResponse(model=llm.TEXT_MODEL, summary=result or "")
