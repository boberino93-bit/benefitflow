from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .models import BookingApprovalRequest, BookingProposalRequest, PlanRequest, VerificationRequest
from .optimizer import build_plan
from .parser import extract_pdf_text, parse_benefits_text
from .providers import list_providers
from .workflow import approve_proposal, create_proposal, verify_provider

BASE = Path(__file__).resolve().parent.parent
app = FastAPI(title="BenefitFlow Beta", version="0.3.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.3.0", "project": "benefitflow", "rnd_status": "BLOCKED_PENDING_USER_START"}


@app.post("/api/parse-text")
def parse_text(text: str = Form(...)):
    return parse_benefits_text(text)


@app.post("/api/parse-file")
async def parse_file(file: UploadFile = File(...)):
    data = await file.read()
    name = (file.filename or "").lower()
    try:
        text = extract_pdf_text(data) if name.endswith(".pdf") else data.decode("utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read file: {exc}") from exc
    return parse_benefits_text(text)


@app.post("/api/plan")
def plan(req: PlanRequest):
    return build_plan(req)


@app.get("/api/providers")
def providers(category: str | None = None):
    return {"providers": list_providers(category), "synthetic": True}


@app.post("/api/providers/verify")
def provider_verify(req: VerificationRequest):
    try:
        return verify_provider(req.provider_id, req.insurer_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/booking/propose")
def booking_propose(req: BookingProposalRequest):
    try:
        return create_proposal(req)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/booking/approve")
def booking_approve(req: BookingApprovalRequest):
    try:
        return approve_proposal(req.proposal_id, req.approved)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
