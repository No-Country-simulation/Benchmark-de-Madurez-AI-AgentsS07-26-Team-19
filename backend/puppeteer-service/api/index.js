const express = require("express");
const chromium = require("@sparticuz/chromium");
const puppeteer = require("puppeteer-core");

const app = express();
app.use(express.json({ limit: "10mb" }));

let browserPromise = null;

async function getBrowser() {
  if (!browserPromise) {
    browserPromise = puppeteer.launch({
      args: chromium.args,
      defaultViewport: { width: 1280, height: 720 },
      executablePath: await chromium.executablePath(),
      headless: "new",
    });
  }
  return browserPromise;
}

app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "puppeteer-pdf" });
});

app.post("/generate", async (req, res) => {
  const { html, filename = "report.pdf" } = req.body;

  if (!html) {
    return res.status(400).json({ error: "Missing 'html' field" });
  }

  let page;
  try {
    const browser = await getBrowser();
    page = await browser.newPage();
    await page.setContent(html, { waitUntil: "networkidle0", timeout: 45000 });

    const pdfBuffer = await page.pdf({
      format: "A4",
      printBackground: true,
      margin: { top: "20mm", bottom: "20mm", left: "15mm", right: "15mm" },
    });

    const pdfBase64 = Buffer.from(pdfBuffer).toString("base64");
    res.json({ pdf_base64: pdfBase64, filename });
  } catch (err) {
    console.error("PDF generation error:", err);
    res.status(500).json({ error: "PDF generation failed", detail: err.message });
  } finally {
    if (page) await page.close();
  }
});

module.exports = app;