import { chromium } from "playwright";
import { pathToFileURL } from "node:url";
import path from "node:path";
import assert from "node:assert/strict";

const root = process.argv[2] ? path.resolve(process.argv[2]) : process.cwd();
const appDir = process.env.APP_DIR || "appcenter";
const file = (name) => pathToFileURL(path.join(root, appDir, name)).href;
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
const passed = [];
try {
  await page.goto(file("paint-studio.html"));
  const canvas = page.locator("#canvas");
  const before = await canvas.evaluate((c) => c.toDataURL());
  const rect = await canvas.boundingBox();
  await page.mouse.move(rect.x + 45, rect.y + 45);
  await page.mouse.down();
  await page.mouse.move(rect.x + 105, rect.y + 90, { steps: 5 });
  await page.mouse.up();
  assert.notEqual(await canvas.evaluate((c) => c.toDataURL()), before, "Paint Studio should draw to canvas");
  passed.push("Paint Studio draw");

  await page.goto(file("vector-studio.html"));
  await page.locator("#tool").selectOption("rect");
  const svg = page.locator("#svg"), box = await svg.boundingBox();
  const initialRects = await svg.locator("rect").count();
  await page.mouse.move(box.x + 80, box.y + 80);
  await page.mouse.down();
  await page.mouse.move(box.x + 180, box.y + 160, { steps: 4 });
  await page.mouse.up();
  assert.ok(await svg.locator("rect").count() > initialRects, "Vector Studio should add a rectangle");
  passed.push("Vector Studio shape");

  await page.goto(file("media-deck.html"));
  const wav = Buffer.alloc(44 + 800);
  wav.write("RIFF",0); wav.writeUInt32LE(wav.length-8,4); wav.write("WAVE",8);
  wav.write("fmt ",12); wav.writeUInt32LE(16,16); wav.writeUInt16LE(1,20);
  wav.writeUInt16LE(1,22); wav.writeUInt32LE(8000,24); wav.writeUInt32LE(16000,28);
  wav.writeUInt16LE(2,32); wav.writeUInt16LE(16,34); wav.write("data",36); wav.writeUInt32LE(800,40);
  await page.locator("#files").setInputFiles({name:"smoke.wav",mimeType:"audio/wav",buffer:wav});
  assert.match(await page.locator("#status").innerText(), /Loaded: smoke\.wav/);
  passed.push("Media Deck local media load");

  await page.goto(file("document-desk.html"));
  await page.locator("#editor").fill("# smoke test\nHello");
  assert.equal(await page.locator("#editor").inputValue(), "# smoke test\nHello");
  const textDownload = page.waitForEvent("download");
  await page.locator("#saveText").click();
  assert.equal((await textDownload).suggestedFilename(), "document.txt");
  passed.push("Document Desk edit/export");

  await page.goto(file("sheet-desk.html"));
  await page.locator("#sample").click();
  await page.locator("#addRow").click();
  assert.match(await page.locator("#status").innerText(), /5 rows/);
  const csvDownload = page.waitForEvent("download");
  await page.locator("#export").click();
  assert.equal((await csvDownload).suggestedFilename(), "sheet.csv");
  passed.push("Sheet Desk grid/export");

  await page.goto(file("file-toolkit.html"));
  await page.locator("#files").setInputFiles({name:"hello.txt",mimeType:"text/plain",buffer:Buffer.from("hello toolkit")});
  await page.locator("#hash").click();
  await page.waitForFunction(() => document.querySelector("#rows").innerText.includes("hello.txt"));
  await page.waitForTimeout(150);
  assert.match(await page.locator("#rows").innerText(), /hello\.txt/);
  passed.push("File Toolkit selected-file inspection");

  await page.goto(file("code-workbench.html"));
  await page.locator("#run").click();
  const preview = page.frameLocator("#preview");
  await preview.locator("h1").waitFor();
  assert.equal(await preview.locator("h1").innerText(), "Hello, Workbench!");
  passed.push("Code Workbench sandboxed preview");

  await page.goto(file("snake-arcade.html"));
  await page.locator("#start").click();
  assert.equal(await page.locator("#status").innerText(), "Playing");
  await page.waitForTimeout(160);
  assert.ok(Number(await page.locator("#score").innerText()) >= 0);
  passed.push("Snake Arcade launch/play loop");

  console.log("Browser smoke tests passed:", passed.join(", "));
} finally {
  await browser.close();
}
