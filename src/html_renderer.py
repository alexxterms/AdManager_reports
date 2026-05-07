import asyncio
import logging
from io import BytesIO
from pathlib import Path
from typing import Optional, List, Dict, Any
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


def _build_metrics_rows(current_metrics: Dict[str, Any], previous_metrics: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
    """Build formatted metrics rows with week-over-week calculations."""
    
    if previous_metrics is None:
        previous_metrics = {}
    
    metrics_order = [
        ("AD SPEND", "ad_spend", "$", 2),
        ("CLICKTHROUGH RATE", "ctr", "%", 2),
        ("COST PER CLICK", "cpc", "$", 2),
        ("COST PER MILLE", "cpm", "$", 2),
        ("YOUR FORM FILLS", "form_fills", "#", 0),
        ("COST PER FORM FILL", "cost_per_form_fill", "$", 2),
        ("SALES", "sales", "#", 0),
        ("COST PER SALE", "cost_per_sale", "$", 2),
        ("REVENUE", "revenue", "$", 2),
        ("ROAS", "roas", "#", 2),
    ]
    
    rows = []
    
    for label, key, prefix, decimals in metrics_order:
        current_val = current_metrics.get(key, 0)
        previous_val = previous_metrics.get(key, 0)
        
        # Format current value
        if isinstance(current_val, str):
            current_str = current_val
        elif decimals == 0:
            current_str = f"{int(current_val)}"
        else:
            current_str = f"{current_val:.{decimals}f}"
        
        if prefix == "$":
            current_str = f"${current_str}"
        elif prefix == "%":
            current_str = f"{current_str}%"
        
        # Format previous value
        if isinstance(previous_val, str):
            previous_str = previous_val
        elif decimals == 0:
            previous_str = f"{int(previous_val)}"
        else:
            previous_str = f"{previous_val:.{decimals}f}"
        
        if prefix == "$":
            previous_str = f"${previous_str}"
        elif prefix == "%":
            previous_str = f"{previous_str}%"
        
        # Calculate change
        change_indicator = "—"
        change_class = "neutral"
        
        if previous_val and current_val != previous_val:
            pct_change = ((current_val - previous_val) / previous_val) * 100
            
            if pct_change > 0:
                change_indicator = f"↑ {abs(pct_change):.1f}%"
                change_class = "up"
            elif pct_change < 0:
                change_indicator = f"↓ {abs(pct_change):.1f}%"
                change_class = "down"
            else:
                change_indicator = "—"
                change_class = "neutral"
        
        rows.append({
            "label": label,
            "previous": previous_str,
            "current": current_str,
            "change": change_indicator,
            "change_class": change_class,
        })
    
    return rows


async def _render_to_pdf_async(html_content: str) -> bytes:
    """Render HTML to PDF using Playwright headless browser, return as bytes."""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        # Ensure on-screen styles and background graphics are rendered
        await page.emulate_media(media="screen")
        pdf_bytes = await page.pdf(
            format="A4",
            margin={"top": "0", "bottom": "0", "left": "0", "right": "0"},
            print_background=True,
            prefer_css_page_size=True,
        )
        await browser.close()
        return pdf_bytes


def render_report_html(
    current_metrics: Dict[str, Any],
    problems: List[str],
    solutions: List[str],
    previous_metrics: Optional[Dict[str, Any]] = None,
    report_date: str = "May 7, 2026",
    template_dir: str = ".",
    content_offset_mm: float = 0.0,
    metrics_offset_mm: float = 0.0,
    problems_offset_mm: float = 0.0,
    opportunities_offset_mm: float = 0.0,
) -> bytes:
    """
    Render HTML template with metrics data to PDF bytes.
    
    Args:
        current_metrics: Dictionary of current week metrics
        problems: List of problem/obstacle strings
        solutions: List of solution/opportunity strings
        previous_metrics: Dictionary of previous week metrics (optional)
        report_date: Report date string for the cover page
        template_dir: Directory containing Jinja2 templates
    
    Returns:
        PDF content as bytes (ready to upload)
    """
    
    # Build metrics rows with week-over-week calculations
    metrics_rows = _build_metrics_rows(current_metrics, previous_metrics)
    
    # Load Jinja2 template
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("growrev_weekly_report.html.jinja2")
    
    # Render template with data
    html_content = template.render(
        report_date=report_date,
        metrics_rows=metrics_rows,
        problems=problems,
        solutions=solutions,
        content_offset_mm=content_offset_mm,
        metrics_offset_mm=metrics_offset_mm,
        problems_offset_mm=problems_offset_mm,
        opportunities_offset_mm=opportunities_offset_mm,
    )
    
    # Convert HTML to PDF using Playwright, return bytes
    pdf_bytes = asyncio.run(_render_to_pdf_async(html_content))
    
    logger.info(f"PDF report generated ({len(pdf_bytes)} bytes)")
    return pdf_bytes
