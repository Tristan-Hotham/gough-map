// QA: open index.html at desktop and phone widths, log console errors, take screenshots to qa/.
// Run from the study root with a static server (python3 -m http.server PORT; set PORT). MapLibre comes from a local npm
// copy (MAPLIBRE_DIST); web fonts and tile services are blocked in the build container, so screenshots show the offline look.
const { chromium } = require("playwright");
const fs = require("fs");
const ML = process.env.MAPLIBRE_DIST || "/tmp/ml/node_modules/maplibre-gl/dist";
(async () => {
  fs.mkdirSync("qa", { recursive: true });
  const b = await chromium.launch({ args: ["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"] });
  const errs = [];
  for (const [nm, vw, vh] of [["desktop", 1280, 900], ["phone", 390, 844]]) {
    const p = await b.newPage({ viewport: { width: vw, height: vh }, deviceScaleFactor: nm === "phone" ? 2 : 1 });
    await p.route(/arcgisonline|googleapis|gstatic|cartocdn/, r => r.abort());
    await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.js/, r => r.fulfill({ path: ML + "/maplibre-gl.js", contentType: "application/javascript" }));
    await p.route(/maplibre-gl@[\d.]+\/dist\/maplibre-gl\.css/, r => r.fulfill({ path: ML + "/maplibre-gl.css", contentType: "text/css" }));
    p.on("console", m => { if (m.type() === "error" && !/ERR_FAILED|net::|Failed to load resource|AJAXError|arcgis|carto/i.test(m.text())) errs.push(nm + ": " + m.text()); });
    p.on("pageerror", e => errs.push(nm + " pageerror: " + e.message));
    await p.goto("http://localhost:" + process.env.PORT + "/index.html", { waitUntil: "load" });
    await p.waitForTimeout(6000);
    await p.screenshot({ path: `qa/${nm}_top.png` });
    const shot = async (sel, f) => { await p.locator(sel).scrollIntoViewIfNeeded(); await p.waitForTimeout(1500); await p.locator(sel).screenshot({ path: `qa/${nm}_${f}.png` }); };
    await shot("#atlas", "atlas");
    await p.fill("#q", "York"); await p.waitForTimeout(400); await p.keyboard.press("Enter"); await p.waitForTimeout(3500); await shot("#atlas", "york");
    await p.locator("#fmap .lyrBtn").click(); await p.waitForTimeout(300);
    await p.locator('#fmap input[data-l="grid"]').check(); await p.locator('#fmap input[data-l="coast"]').check(); await p.locator("#fmap .lyrBtn").click();
    await p.click('#focusRow .btn:nth-child(2)'); await p.waitForTimeout(3000); await shot("#atlas", "grid");
    await p.locator('#fmap .lyrBtn').click(); await p.locator('#fmap input[data-l="grid"]').uncheck(); await p.locator('#fmap input[data-l="coast"]').uncheck(); await p.locator("#fmap .lyrBtn").click();
    await p.locator("#morph").fill("100"); await p.locator("#morph").dispatchEvent("input"); await p.waitForTimeout(1500);
    await p.click('#focusRow .btn:nth-child(10)'); await p.waitForTimeout(3000); await shot("#atlas", "morph");
    await p.locator("#morph").fill("0"); await p.locator("#morph").dispatchEvent("input");
    await p.locator("#mmap .lyrBtn").click(); await p.locator('#mmap input[data-l="arrows"]').check(); await p.locator("#mmap .lyrBtn").click();
    await p.click('#focusRow .btn:nth-child(7)'); await p.waitForTimeout(3000); await shot("#atlas", "wales");
    await p.click("#northUp"); await p.waitForTimeout(1500); await shot("#fmap", "northup");
    for (const c of ["regChart", "mileChart", "drawChart", "jChart", "perChart"]) await shot("#" + c, c);
    if (nm === "phone") { await p.click("#theme"); await p.waitForTimeout(1200); await shot("#mileChart", "dark_mile");
      await p.locator("#fmap").scrollIntoViewIfNeeded(); await p.locator("#fmap .mfs-btn").click(); await p.waitForTimeout(1500); await p.screenshot({ path: `qa/${nm}_fullscreen.png` }); }
    const ov = await p.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    console.log(nm, "horizontal overflow px:", ov);
    await p.close();
  }
  console.log("errors:", errs.length ? errs : "none");
  await b.close();
})();
