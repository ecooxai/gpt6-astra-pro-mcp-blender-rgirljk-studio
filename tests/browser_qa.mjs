import {chromium} from 'playwright';import fs from 'node:fs';
const result={testedAt:new Date().toISOString(),device:'Headless Chromium / software WebGL; not a physical-phone benchmark',cases:[]};let browser;
try{
 browser=await chromium.launch({headless:true,executablePath:'/home/dev/.local/share/chromium/chromium-1243/chrome-linux64/chrome',args:['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 for(const [name,width,height] of [['desktop',1440,1050],['mobile',390,844]]){
  const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});page.setDefaultTimeout(120000);const errors=[],failed=[],controls=[];const entry={name,width,height,errors,failed,controlsTested:controls};
  page.on('pageerror',e=>errors.push(String(e)));page.on('requestfailed',r=>failed.push({url:r.url(),type:r.resourceType(),reason:r.failure()?.errorText}));
  try{
   const started=Date.now();await page.goto(process.env.PREVIEW_URL||'http://127.0.0.1:8867',{waitUntil:'networkidle',timeout:120000});await page.waitForFunction(()=>window.__viewer?.ready,null,{timeout:120000});await page.waitForTimeout(800);
   Object.assign(entry,await page.evaluate(()=>({viewer:window.__viewer,overflow:document.documentElement.scrollWidth>innerWidth+1,canvas:{width:document.querySelector('canvas').width,height:document.querySelector('canvas').height},title:document.title})));entry.readyMs=Date.now()-started;
   // Force all evidence images to finish loading before the full-page screenshot.
   await page.evaluate(async()=>{await Promise.all([...document.images].map(im=>{im.loading='eager';return im.decode().catch(()=>{})}))});
   await page.screenshot({path:`preview/browser_${name}.png`,fullPage:true,timeout:120000});
   await page.locator('[data-view="face"]').click();controls.push('face');await page.waitForTimeout(800);await page.locator('#viewport').scrollIntoViewIfNeeded();let box=await page.locator('#viewport').boundingBox();if(box)await page.screenshot({path:`preview/browser_${name}_face.png`,clip:box,timeout:120000});
   for(const view of ['threequarter','back','side']){await page.locator(`[data-view="${view}"]`).click();controls.push(view);await page.waitForTimeout(250)}
   await page.locator('#wire').click();controls.push('wireframe-on');await page.waitForTimeout(300);await page.locator('#wire').click();controls.push('wireframe-off');
   await page.locator('#spin').click();controls.push('rotate-on');await page.waitForTimeout(350);await page.locator('#spin').click();controls.push('rotate-off');
   await page.locator('#detail').click();await page.waitForFunction(()=>window.__viewer?.quality==='full',null,{timeout:120000});controls.push('full-detail');entry.fullDetail=await page.evaluate(()=>window.__viewer);
   if(entry.fullDetail.triangles<entry.viewer.triangles)throw new Error('Full detail has fewer triangles than the lightweight model.');
   await page.locator('[data-view="face"]').click();await page.waitForTimeout(600);await page.locator('#viewport').scrollIntoViewIfNeeded();box=await page.locator('#viewport').boundingBox();if(box)await page.screenshot({path:`preview/browser_${name}_full_face.png`,clip:box,timeout:120000});
   await page.locator('#detail').click();await page.waitForFunction(()=>window.__viewer?.quality==='lightweight',null,{timeout:120000});controls.push('light-detail');
   await page.locator('#reset').click();controls.push('reset');entry.finalViewer=await page.evaluate(()=>window.__viewer);
   entry.brokenImages=await page.evaluate(()=>[...document.images].filter(im=>!im.complete||im.naturalWidth===0).map(im=>im.src));
   entry.passed=!entry.overflow&&!errors.length&&!failed.length&&!entry.brokenImages.length;
  }catch(e){entry.passed=false;entry.failure=String(e)}
  result.cases.push(entry);fs.writeFileSync('build/browser_qa.json',JSON.stringify(result,null,2));await page.close();
 }
}catch(e){result.failure=String(e)}finally{if(browser)await browser.close();result.passed=result.cases.length===2&&result.cases.every(c=>c.passed)&&!result.failure;fs.writeFileSync('build/browser_qa.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));}
if(!result.passed)process.exitCode=1;
