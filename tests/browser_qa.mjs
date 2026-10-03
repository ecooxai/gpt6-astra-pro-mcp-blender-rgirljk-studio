import {chromium} from 'playwright';import fs from 'node:fs';
const result={testedAt:new Date().toISOString(),device:'Headless Chromium / software WebGL; not a physical-phone benchmark',cases:[]};let browser;
try{
 browser=await chromium.launch({headless:true,executablePath:'/home/dev/.local/share/chromium/chromium-1243/chrome-linux64/chrome',args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 for(const [name,width,height] of [['desktop',1440,1050],['mobile',390,844]]){
  const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});page.setDefaultTimeout(120000);const errors=[],failed=[],controls=[];const entry={name,width,height,errors,failed,controlsTested:controls};
  page.on('pageerror',e=>errors.push(String(e)));page.on('requestfailed',r=>failed.push({url:r.url(),type:r.resourceType(),reason:r.failure()?.errorText}));
  try{
   const started=Date.now();await page.goto(process.env.PREVIEW_URL||'http://127.0.0.1:8867',{waitUntil:'networkidle',timeout:120000});await page.waitForFunction(()=>window.__viewer?.ready,null,{timeout:120000});await page.waitForTimeout(1200);
   Object.assign(entry,await page.evaluate(()=>({viewer:window.__viewer,overflow:document.documentElement.scrollWidth>innerWidth+1,canvas:{width:document.querySelector('canvas').width,height:document.querySelector('canvas').height},title:document.title})));entry.readyMs=Date.now()-started;
   await page.screenshot({path:`preview/browser_${name}.png`,fullPage:true,timeout:120000});
   await page.locator('[data-view="face"]').click();controls.push('face');await page.waitForTimeout(600);await page.locator('#viewport').scrollIntoViewIfNeeded();const box=await page.locator('#viewport').boundingBox();if(box)await page.screenshot({path:`preview/browser_${name}_face.png`,clip:box,timeout:120000});
   await page.locator('[data-view="back"]').click();controls.push('back');await page.locator('#wire').click();controls.push('wireframe-on');await page.waitForTimeout(300);await page.locator('#wire').click();controls.push('wireframe-off');await page.locator('#reset').click();controls.push('reset');
   entry.passed=!entry.overflow&&!errors.length&&!failed.length;
  }catch(e){entry.passed=false;entry.failure=String(e)}
  result.cases.push(entry);fs.writeFileSync('build/browser_qa.json',JSON.stringify(result,null,2));await page.close();
 }
}catch(e){result.failure=String(e)}finally{if(browser)await browser.close();result.passed=result.cases.length===2&&result.cases.every(c=>c.passed)&&!result.failure;fs.writeFileSync('build/browser_qa.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));}
if(!result.passed)process.exitCode=1;
