from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .models import BookingApprovalRequest, BookingProposalRequest, PlanRequest, VerificationRequest
from .optimizer import build_plan
from .parser import extract_pdf_text, parse_benefits_text
from .providers import get_provider_evidence, list_providers
from .simulation import get_audit, get_transaction, simulate_transaction
from .workflow import approve_proposal, create_proposal, verify_provider

BASE = Path(__file__).resolve().parent.parent
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
MAX_TEXT_CHARS = 100_000

app = FastAPI(title="BenefitFlow Alpha", version="0.4.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")


class DemoTransactionRequest(BaseModel):
    proposal_id: str
    scenario: Literal["confirmed", "waitlisted", "retryable_failure", "ambiguous_after_send", "rejected"] = "confirmed"


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "0.4.0",
        "project": "benefitflow",
        "rnd_status": "ROUND1_CLOSED_P0_HARDENING_ACTIVE",
        "demo_mode": True,
        "live_integrations_allowed": False,
    }


@app.post("/api/parse-text")
def parse_text(text: str = Form(...)):
    if len(text) > MAX_TEXT_CHARS:
        raise HTTPException(status_code=413, detail=f"Demo text limit is {MAX_TEXT_CHARS} characters")
    return parse_benefits_text(text)


@app.post("/api/parse-file")
async def parse_file(file: UploadFile = File(...)):
    data = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"Demo upload limit is {MAX_UPLOAD_BYTES // (1024 * 1024)} MB")
    name = (file.filename or "").lower()
    try:
        text = extract_pdf_text(data) if name.endswith(".pdf") else data.decode("utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not read file: {exc}") from exc
    if len(text) > MAX_TEXT_CHARS:
        raise HTTPException(status_code=413, detail=f"Extracted text exceeds {MAX_TEXT_CHARS} characters")
    return parse_benefits_text(text)


@app.post("/api/plan")
def plan(req: PlanRequest):
    return build_plan(req)


@app.get("/api/providers")
def providers(category: str | None = None):
    return {"providers": list_providers(category), "synthetic": True}


@app.get("/api/providers/{provider_id}/evidence")
def provider_evidence(provider_id: str):
    try:
        return get_provider_evidence(provider_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


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
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/demo/transaction")
def demo_transaction(req: DemoTransactionRequest):
    try:
        return simulate_transaction(req.proposal_id, req.scenario)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/demo/transaction/{proposal_id}")
def demo_transaction_get(proposal_id: str):
    try:
        return get_transaction(proposal_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/demo/audit/{proposal_id}")
def demo_audit(proposal_id: str):
    try:
        return get_audit(proposal_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
