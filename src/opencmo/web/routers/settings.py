"""Settings API router."""

from __future__ import annotations

import os

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from opencmo import storage

router = APIRouter(prefix="/api/v1")


def _mask_key(key: str) -> str:
    if len(key) > 8:
        return f"{key[:3]}...{key[-4:]}"
    return "***" if key else ""


async def _get_setting(name: str) -> str:
    from opencmo import llm
    return (await llm.get_key_async(name)) or ""


@router.get("/settings")
async def api_v1_settings_get():
    api_key = await _get_setting("OPENAI_API_KEY")
    base_url = await _get_setting("OPENAI_BASE_URL")
    model = await _get_setting("OPENCMO_MODEL_DEFAULT")
    # Reddit
    reddit_cid = await _get_setting("REDDIT_CLIENT_ID")
    reddit_secret = await _get_setting("REDDIT_CLIENT_SECRET")
    reddit_user = await _get_setting("REDDIT_USERNAME")
    reddit_pass = await _get_setting("REDDIT_PASSWORD")
    auto_publish = await _get_setting("OPENCMO_AUTO_PUBLISH")
    # Twitter
    twitter_api_key = await _get_setting("TWITTER_API_KEY")
    twitter_api_secret = await _get_setting("TWITTER_API_SECRET")
    twitter_access_token = await _get_setting("TWITTER_ACCESS_TOKEN")
    twitter_access_secret = await _get_setting("TWITTER_ACCESS_SECRET")
    # GEO platforms
    anthropic_key = await _get_setting("ANTHROPIC_API_KEY")
    google_ai_key = await _get_setting("GOOGLE_AI_API_KEY")
    geo_chatgpt = await _get_setting("OPENCMO_GEO_CHATGPT")
    # SEO
    pagespeed_key = await _get_setting("PAGESPEED_API_KEY")
    # Search (Tavily)
    tavily_key = await _get_setting("TAVILY_API_KEY")
    # SERP
    dataforseo_login = await _get_setting("DATAFORSEO_LOGIN")
    dataforseo_pass = await _get_setting("DATAFORSEO_PASSWORD")
    # Email
    smtp_host = await _get_setting("OPENCMO_SMTP_HOST")
    smtp_port = await _get_setting("OPENCMO_SMTP_PORT")
    smtp_user = await _get_setting("OPENCMO_SMTP_USER")
    smtp_pass = await _get_setting("OPENCMO_SMTP_PASS")
    report_email = await _get_setting("OPENCMO_REPORT_EMAIL")
    return JSONResponse({
        "api_key_set": bool(api_key),
        "api_key_masked": _mask_key(api_key),
        "base_url": base_url,
        "model": model,
        # Reddit
        "reddit_configured": bool(reddit_cid and reddit_secret and reddit_user and reddit_pass),
        "reddit_username": reddit_user,
        "auto_publish": auto_publish == "1",
        # Twitter
        "twitter_configured": bool(twitter_api_key and twitter_api_secret and twitter_access_token and twitter_access_secret),
        "twitter_api_key_masked": _mask_key(twitter_api_key),
        # GEO
        "anthropic_key_set": bool(anthropic_key),
        "anthropic_key_masked": _mask_key(anthropic_key),
        "google_ai_key_set": bool(google_ai_key),
        "google_ai_key_masked": _mask_key(google_ai_key),
        "geo_chatgpt_enabled": geo_chatgpt == "1",
        # SEO
        "pagespeed_key_set": bool(pagespeed_key),
        "pagespeed_key_masked": _mask_key(pagespeed_key),
        # Search (Tavily)
        "tavily_key_set": bool(tavily_key),
        "tavily_key_masked": _mask_key(tavily_key),
        # SERP
        "dataforseo_configured": bool(dataforseo_login and dataforseo_pass),
        "dataforseo_login": dataforseo_login,
        # Email
        "email_configured": bool(smtp_host and smtp_user and smtp_pass),
        "smtp_host": smtp_host,
        "smtp_port": smtp_port,
        "smtp_user": smtp_user,
        "report_email": report_email,
    })


_ALL_SETTING_KEYS = (
    "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENCMO_MODEL_DEFAULT",
    # Reddit
    "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USERNAME", "REDDIT_PASSWORD",
    "OPENCMO_AUTO_PUBLISH",
    # Twitter
    "TWITTER_API_KEY", "TWITTER_API_SECRET", "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_SECRET",
    # GEO
    "ANTHROPIC_API_KEY", "GOOGLE_AI_API_KEY", "OPENCMO_GEO_CHATGPT",
    # SEO
    "PAGESPEED_API_KEY",
    # Search (Tavily)
    "TAVILY_API_KEY",
    # SERP
    "DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD",
    # Email
    "OPENCMO_SMTP_HOST", "OPENCMO_SMTP_PORT", "OPENCMO_SMTP_USER", "OPENCMO_SMTP_PASS",
    "OPENCMO_REPORT_EMAIL",
)


@router.post("/settings")
async def api_v1_settings_save(request: Request):
    body = await request.json()
    for key in _ALL_SETTING_KEYS:
        val = body.get(key)
        if val is not None:
            val = val.strip() if isinstance(val, str) else str(val)
            if val:
                await storage.set_setting(key, val)
                os.environ[key] = val
            else:
                await storage.delete_setting(key)
                os.environ.pop(key, None)
    return JSONResponse({"ok": True})
