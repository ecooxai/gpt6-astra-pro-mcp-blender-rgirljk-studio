import {chromium} from 'playwright';import fs from 'node:fs';
const browser=await chromium.launch({headless:true,executablePath:'/home/dev/.local/share/chromium/chromium-1243/chrome-linux64/chrome',args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const result={testedAt:new Date().toISOString(),device:'Headless Chromium / software WebGL; not a physical-phone benchmark',cases:[]};
for(const [name,width,height] of [['desktop',1440,1050],['mobile',390,844]]){
 const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});const errors=[];const failed=[];
 page.on('pageerror',e=>errors.push(String(e)));page.on('requestfailed',r=>failed.push(r.url()));
 await page.goto('http://127.0.0.1:8867',{waitUntil:'networkidle',timeout:60000});await page.waitForFunction(()=>window.__viewer?.ready,{timeout:90000});await page.waitForTimeout(1200);
 const data=await page.evaluate(()=>({viewer:window.__viewer,overflow:document.documentElement.scrollWidth>innerWidth+1,canvas:{width:document.querySelector('canvas').width,height:document.querySelector('canvas').height},title:document.title}));
 await page.screenshot({path:`preview/browser_${name}.png`,fullPage:true});
 await page.locator('[data-view="face"]').click();await page.waitForTimeout(350);await page.screenshot({path:`preview/browser_${name}_face.png`,fullPage:true,timeout:90000});
 await page.locator('[data-view="back"]').click();await page.locator('#wire').click();await page.locator('#wire').click();await page.locator('#reset').click();
 result.cases.push({name,width,height,...data,errors,failed,controlsTested:['face','back','wireframe-on','wireframe-off','reset']});fs.writeFileSync('build/browser_qa.json',JSON.stringify(result,null,2));await page.close();
}
await browser.close();fs.writeFileSync('build/browser_qa.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
