import { chromium } from 'playwright';
const browser = await chromium.launch({ args: ['--no-sandbox'] });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto('http://localhost:5183/login', { waitUntil: 'load' });
await page.waitForTimeout(1500);

await page.mouse.move(400, 600, { steps: 10 });
await page.waitForTimeout(300);
const vars = await page.evaluate(() => {
  const el = document.querySelector('.graphic-spotlight');
  const cs = getComputedStyle(el);
  return { x: cs.getPropertyValue('--spot-x'), y: cs.getPropertyValue('--spot-y') };
});
console.log('spotlight vars:', JSON.stringify(vars));

// dark mode visual check
await page.click('button[aria-label="Switch to dark theme"]');
await page.waitForTimeout(400);
await page.mouse.move(300, 300, { steps: 10 });
await page.waitForTimeout(300);
await page.screenshot({ path: '/private/tmp/claude-501/-Users-nijathatamli-Documents-team-noclip-website/60704944-10b5-4588-a49b-b8a2238ba09f/scratchpad/login-spotlight-dark.png' });

// reduced motion check: spotlight should be display:none
await page.close();
const page2 = await browser.newPage({ viewport: { width: 1440, height: 900 }, reducedMotion: 'reduce' });
await page2.goto('http://localhost:5183/login', { waitUntil: 'load' });
await page2.waitForTimeout(800);
const display = await page2.evaluate(() => getComputedStyle(document.querySelector('.graphic-spotlight')).display);
console.log('spotlight display under reduced motion:', display);

await browser.close();
