/* Session navigation: use the existing save-before-navigation flow. */
let navigationEntries=[location.hash||'#/home'],navigationIndex=0;
function navigationObserve(){
 const current=location.hash||'#/home';
 if(navigationEntries[navigationIndex]===current)return;
 navigationEntries=navigationEntries.slice(0,navigationIndex+1);
 navigationEntries.push(current);navigationIndex=navigationEntries.length-1;
}
function navigationParent(){
 const r=(location.hash||'#/home').replace(/^#\//,'').split('/');
 try{
  if(r[0]==='a'){const {s}=ctx('act',r[1]);if(s)return '#/s/'+s.id+'/acts';}
  if(r[0]==='s'){const {p}=ctx('sys',r[1]);if(p)return '#/p/'+p.id;}
  if(r[0]==='build')return '#/p/'+r[1];
  if(r.length>2)return '#/'+r.slice(0,-1).join('/');
  if(r[0]==='lib'&&r.length>1)return '#/lib';
 }catch(error){/* A deleted parent falls back to the object list. */}
 return '#/home';
}
A.navigationBack=()=>{
 const target=navigationIndex>0?navigationEntries[navigationIndex-1]:navigationParent();
 if(target===(location.hash||'#/home'))return;
 return manualDecision(()=>{
  if(navigationIndex>0)navigationIndex--;else navigationEntries=[target];
  go(target);
 });
};
const navigationRender=render;
render=()=>{
 navigationObserve();navigationRender();
 const page=document.querySelector('#content .page');
 if(!page||page.querySelector('[data-a="navigationBack"]'))return;
 const disabled=navigationIndex===0&&(location.hash||'#/home')==='#/home';
 page.insertAdjacentHTML('afterbegin',`<div class="row mb" data-navigation><button class="btn" data-a="navigationBack" aria-label="Назад" ${disabled?'disabled':''}>← Назад</button></div>`);
};
