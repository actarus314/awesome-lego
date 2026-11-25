(()=>{
const L=document.documentElement.lang,D=JSON.parse(document.getElementById('data').textContent);
const S={{STRINGS}};
const t=k=>(S[k]||{})[L]||k,tn=(k,n)=>t(n===1?k+'1':k).replace('{n}',n),COLON=L==='fr'?' : ':': ';  // French puts a space before the colon, English does not
document.querySelectorAll('[data-t]').forEach(e=>e.textContent=t(e.dataset.t));document.querySelectorAll('[data-t-label]').forEach(e=>e.setAttribute('aria-label',t(e.dataset.tLabel)));
const R=D.resources,C=D.categories,catName=id=>(C.find(c=>c.id===id)||{})[L]||id,shortCat=id=>catName(id).split(/[,(]/)[0].replace(/ (et|and) .*/,'');
const ci=id=>`<img class="ci" src="${L==='fr'?'../':''}media/icons/${id}.svg" alt="">`;  // category icon: headings of the directory and tiles of "Where to start" only
const host=u=>{try{return new URL(u).hostname.replace(/^www\./,'')}catch(e){return u}};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const MONTHS=t('months').split(',');  // the month in letters, never abbreviated: 3 July 2027, 3 juillet 2027, 1er avril
const fmt=d=>{if(!d)return'';const[y,m,j]=String(d).split('-').map(Number);return m?(j?(L==='fr'&&j===1?'1er':j)+' ':'')+MONTHS[m-1]+' '+y:String(y)};
const dt=d=>d?`<time datetime="${esc(d)}">${esc(fmt(d))}</time>`:'';  // every date shown, machine-readable and never broken over two lines
const TITLE0=document.title;
// colours of the theme as numbers, to choose readable text (WCAG contrast)
const RGB=v=>{const d=document.createElement('i');d.style.color=`var(${v})`;document.body.appendChild(d);const m=getComputedStyle(d).color.match(/[\d.]+/g).map(Number);d.remove();return m.slice(0,3)};
const LUM=c=>{const f=x=>(x/=255)<=.03928?x/12.92:((x+.055)/1.055)**2.4;return .2126*f(c[0])+.7152*f(c[1])+.0722*f(c[2])},CR=(a,b)=>{const x=LUM(a),y=LUM(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
const SMOOTH=()=>matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth';  // no animated scroll for those who asked for less motion
const fold=s=>String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'');
const world=r=>{const o=(r.covers||[]).includes('official'),a=(r.covers||[]).includes('alternative');return o&&a?'both':o?'official':a?'alternative':''};
const cname=(()=>{try{const n=new Intl.DisplayNames([L],{type:'region'});return c=>c==='international'?t('intl'):(n.of(c)||c)}catch(e){return c=>c}})();
document.getElementById('fresh').innerHTML=`${t('reviewed')} ${dt(R.reduce((a,r)=>r.checked>a?r.checked:a,''))} · ${t('built')} ${dt(D.built)}`;
const tb=document.getElementById('theme'),root=document.documentElement,ic=p=>`<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">${p}</svg>`;
const lab={auto:ic('<circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 0 0 18z" fill="currentColor"/>'),light:ic('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>'),dark:ic('<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>')};
const tname={auto:{en:'Theme: auto',fr:'Thème : auto'},light:{en:'Theme: light',fr:'Thème : clair'},dark:{en:'Theme: dark',fr:'Thème : sombre'}};
const getT=()=>{try{return localStorage.getItem('theme')||'auto'}catch(e){return 'auto'}};
const setT=v=>{if(v==='auto')delete root.dataset.theme;else root.dataset.theme=v;if(drawn)vBrands();tb.innerHTML=lab[v];tb.setAttribute('aria-label',tname[v][L]);try{localStorage.setItem('theme',v)}catch(e){}};
document.getElementById('langbtn').onclick=()=>{try{localStorage.setItem('lang',L==='fr'?'en':'fr')}catch(e){}};
setT(getT());tb.onclick=()=>{const o=['auto','light','dark'];setT(o[(o.indexOf(getT())+1)%3])};
const hdr=()=>{const h=document.querySelector('header.top').offsetHeight;root.style.setProperty('--hdr',h+'px');return h};hdr();
const tip=document.getElementById('tip');
const hideTip=()=>tip.style.opacity=0;addEventListener('scroll',hideTip,{passive:true});addEventListener('resize',hideTip);
document.addEventListener('focusin',e=>{const el=e.target.closest&&e.target.closest('[data-tip]');if(!el||!el.matches(':focus-visible'))return;tip.textContent=el.dataset.tip;tip.style.opacity=1;const r=el.getBoundingClientRect(),w=tip.offsetWidth;tip.style.left=Math.min(innerWidth-w-8,Math.max(8,r.left))+'px';tip.style.top=(r.bottom+8)+'px'});document.addEventListener('focusout',hideTip);addEventListener('keydown',e=>{if(e.key==='Escape')hideTip()});
document.addEventListener('mousemove',e=>{const el=e.target.closest('[data-tip]');if(!el){hideTip();return}tip.textContent=el.dataset.tip;tip.style.opacity=1;const w=tip.offsetWidth,h=tip.offsetHeight;let x=e.clientX+12,y=e.clientY+14;if(x+w>innerWidth-8)x=e.clientX-w-12;if(y+h>innerHeight-8)y=e.clientY-h-14;tip.style.left=x+'px';tip.style.top=y+'px'});
const active=R.filter(r=>r.status==='active').length,langs=new Set(R.flatMap(r=>r.languages||[]));
document.getElementById('kpis').innerHTML=[[R.length,t('resources')],[C.length,t('categories')],[Math.round(100*active/R.length)+' %',t('active')],[langs.size,t('languages')]].map(([v,l])=>`<div class="kpi"><b>${v}</b><span>${l}</span></div>`).join('');
// search index: MiniSearch, fuzzy and prefix matching, results ranked by relevance
const LEGO=R.find(r=>r.cat==='brands'&&(r.covers||[]).includes('official'));  // the LEGO brand: its brand mode shows where official LEGO is
const BRANDS=[...D.brands,...(LEGO?[{id:LEGO.id,name:LEGO.name,aka:[],lego:true}]:[])];
const brandName=id=>(BRANDS.find(x=>x.id===id)||{}).name||'';
const linked=(r,b)=>b===(LEGO||{}).id?!!r.operator&&r.id!==b:(r.brands||[]).includes(b);  // sites and places of the LEGO Group and under the LEGO brand; for another brand, the entries that sell, track, review or admit it
let ms=null;
// strengths and weaknesses: details.json, read when the browser is idle, or as soon as a card is unfolded or the search used
R.forEach(r=>{r[L].strengths=[];r[L].weaknesses=[]});let detP=null,DET=false;
const det=()=>detP||(detP=fetch('details.json').then(x=>{if(!x.ok)throw x.status;return x.json()}).then(d=>{R.forEach(r=>{const v=d[r.id];if(v){r[L].strengths=v[0];r[L].weaknesses=v[1]}});DET=true;if(ms){ms=null;if(st.q.trim()){setQuery(st.q);update(false)}}else if(BM)update(false)}).catch(()=>{detP=null}));  // built when first needed (focus of the search field, or a search)
const index=()=>{if(ms)return ms;ms=new MiniSearch({fields:['name','summary','strengths','weaknesses','group','covers','countries','city','size','brands'],storeFields:[],
 processTerm:w=>fold(w),searchOptions:{boost:{name:4,brands:3,group:2},prefix:true,fuzzy:0.2,combineWith:'AND'}});
 ms.addAll(R.map(r=>({id:r.id,name:r.name,summary:r[L].summary,strengths:r[L].strengths.join(' '),weaknesses:r[L].weaknesses.join(' '),group:r[L].group,
 covers:(r.covers||[]).map(t).join(' '),countries:(r.countries||[]).map(cname).join(' '),city:[r.city,r.city_fr,r.city_local].filter(Boolean).join(' '),size:sizeOf(r),brands:(r.brands||[]).map(brandName).join(' ')})));return ms};
const st={cat:new Set(),cov:new Set(),langs:new Set(),active:false,featured:false,country:'',q:'',view:'cards',sort:null};
let BM='';  // brand mode: the query is exactly a brand's name or other name
const BNAME=new Map(BRANDS.flatMap(b=>[b.name,...b.aka].map(n=>[fold(n),b.id])));
const BN=Object.fromEntries(BRANDS.map(b=>[b.id,R.filter(r=>linked(r,b.id)).length]));
const CTRY=Object.entries(R.flatMap(r=>(r.countries||[]).filter(c=>c!=='international')).reduce((a,c)=>(a[c]=(a[c]||0)+1,a),{})).sort((a,b)=>b[1]-a[1]||cname(a[0]).localeCompare(cname(b[0])));
// the visitor's language (browser), then English, then the others: everyone finds what they can read first, nothing is hidden
const VL=(((navigator.languages||[navigator.language])[0]||L).slice(0,2).toLowerCase());
const LANGS=[...new Set([VL,L,'en'])];
const lname=(()=>{try{const n=new Intl.DisplayNames([L],{type:'language'});return c=>{const x=n.of(c)||c;return L==='fr'?x.toLowerCase():x}}catch(e){return c=>c}})();
const lrank=r=>{const l=r.languages||[];return l.includes(VL)?0:l.includes('en')?1:2};
const FU=['affiliation','ads','sponsorship','subscription','donations','shop','none'];
const toggle=(set,v)=>set.has(v)?set.delete(v):set.add(v);
let hits=null;
const covers=['official','alternative','second-hand','parts','custom-builds','instructions','news','data'];
function match(r,skip){
 if(BM&&r.id===BM)return false;  // the brand itself is the banner above its entries
 if(skip!=='cat'&&st.cat.size&&!st.cat.has(r.cat))return false;
 if(skip!=='cov'&&st.cov.size&&!(r.covers||[]).some(c=>st.cov.has(c)))return false;
 if(st.active&&r.status!=='active')return false;
 if(st.langs.size&&!(r.languages||[]).some(l=>st.langs.has(l)))return false;
 if(st.featured&&!r.featured)return false;

 if(skip!=='country'&&st.country&&!(r.countries||[]).includes(st.country))return false;
 if(BM){if(!linked(r,BM))return false}else if(hits&&!hits.has(r.id))return false;
 return true}
const fc=document.getElementById('f-cat'),fv=document.getElementById('f-cov'),fm=document.getElementById('f-misc'),q=document.getElementById('q');q.placeholder=t('search');q.setAttribute('aria-label',t('search'));
function drawFilters(){
 fc.innerHTML=C.map(c=>`<button class="chip${st.cat.has(c.id)?' on':''}" data-cat="${c.id}" aria-pressed="${st.cat.has(c.id)}">${esc(c[L])}<span class="c">${R.filter(r=>r.cat===c.id&&match(r,'cat')).length}</span></button>`).join('');
 fv.innerHTML=covers.map(c=>`<button class="chip${st.cov.has(c)?' on':''}" data-cov="${c}" aria-pressed="${st.cov.has(c)}">${t(c)}<span class="c">${R.filter(r=>(r.covers||[]).includes(c)&&match(r,'cov')).length}</span></button>`).join('');
 fm.innerHTML=[['featured',t('featured')],['active',t('only_active')]].map(([k,l,tip])=>`<button class="chip${st[k]?' on':''}" data-m="${k}" aria-pressed="${st[k]}"${tip?` title="${esc(tip)}"`:''}>${l}</button>`).join('')+LANGS.map(l=>`<button class="chip${st.langs.has(l)?' on':''}" data-lang="${l}" aria-pressed="${st.langs.has(l)}">${esc(t('in_lang').replace('{x}',lname(l)))}</button>`).join('')+`<select id="f-country" class="${st.country?'on':''}" aria-label="${t('country_all')}"><option value="">${t('country_all')}</option>${CTRY.map(([c])=>`<option value="${c}"${st.country===c?' selected':''}>${esc(cname(c))} (${R.filter(r=>(r.countries||[]).includes(c)&&match(r,'country')).length})</option>`).join('')}</select>`}
fc.onclick=e=>{const b=e.target.closest('[data-cat]');if(b){toggle(st.cat,b.dataset.cat);update()}};
fv.onclick=e=>{const b=e.target.closest('[data-cov]');if(b){const c=b.dataset.cov;st.cov.has(c)?st.cov.delete(c):st.cov.add(c);update()}};
fm.onchange=e=>{if(e.target.id==='f-country'){st.country=e.target.value;update()}};
fm.onclick=e=>{const lb=e.target.closest('[data-lang]');if(lb){toggle(st.langs,lb.dataset.lang);update();return}const b=e.target.closest('[data-m]');if(b){st[b.dataset.m]=!st[b.dataset.m];update()}};
function setQuery(v){st.q=v;q.value=v;const s=v.trim();BM=BNAME.get(fold(s))||'';hits=s?new Map(index().search(s).map(h=>[h.id,h.score])):null}
let qt;q.oninput=()=>{clearTimeout(qt);qt=setTimeout(()=>{setQuery(q.value);update(false)},120)};
function resetAll(){st.cat.clear();st.cov.clear();st.active=st.featured=false;st.langs.clear();st.country='';setQuery('')}
document.getElementById('reset').onclick=document.getElementById('reset2').onclick=()=>{resetAll();update()};
// contact: one line per item (address, phone, email), each with its icon; a phone or an email never breaks
const ICO={adr:'<path d="M8 1.5a4.5 4.5 0 0 0-4.5 4.5c0 3.4 4.5 8.5 4.5 8.5s4.5-5.1 4.5-8.5A4.5 4.5 0 0 0 8 1.5zm0 6.3a1.8 1.8 0 1 1 0-3.6 1.8 1.8 0 0 1 0 3.6z"/>',
 tel:'<path d="M4.2 1.8l2 2.6c.4.5.3 1.1-.1 1.5l-.9.8c.6 1.4 2.4 3.2 3.8 3.8l.8-.9c.4-.4 1-.5 1.5-.1l2.6 2c.5.4.5 1 .1 1.5l-1.1 1.2c-.6.6-1.5.8-2.3.5C6.9 13.4 2.6 9.1 1.3 5.4c-.3-.8-.1-1.7.5-2.3L3 2c.4-.5.9-.6 1.2-.2z"/>',
 mail:'<path d="M2 3.5h12c.6 0 1 .4 1 1v7c0 .6-.4 1-1 1H2c-.6 0-1-.4-1-1v-7c0-.6.4-1 1-1zm.4 1.5L8 9l5.6-4H2.4z"/>'};
function contact(r){const c=r.contact||{};const li=(k,cls,html)=>`<li class="${cls}"><svg viewBox="0 0 16 16" aria-hidden="true">${ICO[k]}</svg>${html}</li>`,a=[];
 if(c.address)c.address.split(' ; ').forEach(ad=>a.push(li('adr','adr',`<a href="https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(ad+', '+(r.countries||[]).filter(x=>x!=='international').map(cname).join(' '))}" target="_blank" rel="noopener" title="${t('addr_map')}">${ad.split(', ').map(x=>x.length>28?esc(x):`<span class="nw">${esc(x)}</span>`).join(', ')}</a>`)));  // a line breaks between the parts of an address, never inside a short part (a town, a postal code)
 if(c.phone)a.push(li('tel','tel',`<a href="tel:${esc(c.phone.replace(/\s/g,''))}">${esc(c.phone)}</a>`));if(c.email)a.push(li('mail','mail',`<a href="mailto:${esc(c.email)}">${esc(c.email)}</a>`));
 return a.length?`<ul class="ct">${a.join('')}</ul>`:''}
const stLabel=r=>t(r.status==='archived'&&r.regime==='operating'?'st_closed':r.status==='active'&&r.regime==='operating'?'st_open':'st_'+r.status);  // the status said for what the entry is: open or closed, updated or not
const cityOf=r=>L==='fr'&&r.city_fr?r.city_fr:r.city||'';
const sizeOf=r=>r.size?r.size.map(z=>{const v=tn('u_'+z.unit,z.n);return z.approx?t('sz_'+z.approx).replace('{x}',v):v}).join(', '):'';
const one=r=>{const c=(r.countries||[]).filter(x=>x!=='international');return c.length===1?cname(c[0]):''};
function sameSite(r){const o=(r.same||[]).filter(id=>id!==r.id).map(id=>R.find(x=>x.id===id)).filter(Boolean);if(!o.length)return'';
 if(o.length>6&&r.operator&&LEGO)return r===LEGO||BM===LEGO.id?`<div class="same">${t('same_site')}${COLON}${esc(tn('n_entries',o.length))}</div>`:`<div class="same">${t('same_site')}${COLON}${esc(tn('n_entries',o.length))}, <button type="button" class="lk" data-brand="${LEGO.id}">${esc(tn('all_about',BN[LEGO.id]).replace('{b}',LEGO.name))}</button></div>`;  // lego.com: a dozen entries, all in the brand mode of LEGO
 return `<div class="same">${t('same_site')}${COLON}${o.map(x=>`<a href="#entry=${x.id}" data-go="${x.id}">${esc(x.name)}</a>`).join(', ')}</div>`}
function card(r,showCat){const x=r[L];const tags=[...(r.covers||[]).filter(c=>c!==r.cat).map(c=>`<span class="tag ${c}">${t(c)}</span>`),(r.status!=='active'?`<span class="tag st-${r.status}">${stLabel(r)}</span>`:''),(r.regime==='work'&&r.last?`<span class="tag">${t('dated').replace('{y}',dt(r.last.slice(0,4)))}</span>`:''),(r.languages||[]).length?`<span class="tag langs">${esc(r.languages.join(' · ').toUpperCase())}</span>`:'',r.access?`<span class="tag">${t('acc_'+r.access)}</span>`:''].join('');
 const m=r.metrics||{};const fu=r.funding&&r.funding[0]!=='unknown'?FU.filter(f=>r.funding.includes(f)).map(f=>t('fu_'+f)).join(', '):'';  // funding read at the source replaces the free business model text
 const extra=[[cityOf(r),one(r)].filter(Boolean).map(esc).join(', '),esc(sizeOf(r)),m.stars!=null?'★ '+m.stars:'',r.next?esc(t('next'))+' '+dt(r.next):'',fu?esc(fu[0].toUpperCase()+fu.slice(1)):''].filter(Boolean).join(' · ');
 const wb=BN[r.id]!=null&&BM!==r.id?`<button type="button" class="btn all" data-brand="${r.id}">${esc(tn('all_about',BN[r.id]).replace('{b}',brandName(r.id)))}</button>`:'';
 return `<article class="card" id="r-${r.id}"><div class="h"><a href="${esc(r.url)}" rel="noopener">${r.featured?'<span class="star" aria-hidden="true">★ </span>':''}${esc(r.name)}</a><span class="g">${esc(showCat?shortCat(r.cat):x.group)}</span></div><p class="s"${x.tl?' lang="en"':''}>${esc(x.summary)}</p>${contact(r)}${extra?`<div class="src">${extra}</div>`:''}<div class="tags">${tags}</div>${sameSite(r)}`+
 (x.d?`<details data-d="${r.id}"><summary>${t('strengths')} · ${t('weaknesses')}</summary></details>`:'')+wb+`</article>`}
// strengths, weaknesses and sources: built when a card is unfolded, not for every card at once
function details(r){const x=r[L],tl=x.tl?' lang="en"':'';return `${x.strengths.length?`<ul class="plus"${tl}>${x.strengths.map(s=>`<li>${esc(s)}</li>`).join('')}</ul>`:''}${x.weaknesses.length?`<ul class="minus"${tl}>${x.weaknesses.map(s=>`<li>${esc(s)}</li>`).join('')}</ul>`:''}<div class="src">${t('sources')}${COLON}${r.sources.map((s,i,a)=>{const h=host(s.url),dup=a.filter(x=>host(x.url)===h).length>1,seg=(()=>{try{return new URL(s.url).pathname.split('/').filter(Boolean)[0]||''}catch(e){return ''}})();return `<a href="${esc(s.url)}" rel="noopener">${dup&&seg?esc(h)+'/<wbr>'+esc(seg):esc(h)}</a>`}).join(' · ')}</div>`}
document.getElementById('list').addEventListener('toggle',e=>{const d=e.target;if(d.tagName==='DETAILS'&&d.open&&d.dataset.d&&!d.dataset.f)det().then(()=>{if(!DET||d.dataset.f)return;d.dataset.f=1;d.insertAdjacentHTML('beforeend',details(R.find(r=>r.id===d.dataset.d)))})},true);  // a failed reading is tried again at the next unfolding
const COLS=[['name',t('c_name'),r=>r.name],['cat',t('c_cat'),r=>catName(r.cat)],['scope',t('c_scope'),r=>(r.covers||[]).filter(c=>c==='official'||c==='alternative').map(t).join(', ')],['lang',t('c_lang'),r=>(r.languages||[]).join(' ').toUpperCase(),'opt'],['status',t('c_status'),stLabel,'opt'],['last',t('c_last'),r=>r.last||'','n'],['stars',t('c_stars'),r=>(r.metrics||{}).stars??-1,'n opt']];
function drawTable(rs){if(st.sort){const c=COLS.find(c=>c[0]===st.sort.k),d=st.sort.d;rs.sort((a,b)=>{const x=c[2](a),y=c[2](b);return (typeof x==='number'?x-y:String(x).localeCompare(String(y)))*d})}
 return `<div class="tscroll" role="region" tabindex="0" aria-label="${esc(t('nav_dir'))}"><table class="dt"><caption class="vh">${esc(t('nav_dir'))}</caption><thead><tr>${COLS.map(c=>`<th scope="col" class="${(c[3]||'').includes('opt')?'opt':''}"${st.sort&&st.sort.k===c[0]?` aria-sort="${st.sort.d>0?'ascending':'descending'}"`:''}><button type="button" class="sortb" data-k="${c[0]}">${c[1]}</button></th>`).join('')}</tr></thead><tbody>${rs.map(r=>`<tr data-go="${r.id}"><td><a href="${esc(r.url)}" rel="noopener">${r.featured?'★ ':''}${esc(r.name)}</a></td><td>${esc(catName(r.cat))}</td><td>${esc(COLS[2][2](r))}</td><td class="opt">${esc(COLS[3][2](r))}</td><td class="opt">${esc(COLS[4][2](r))}</td><td class="n">${dt(r.last)}</td><td class="n opt">${(r.metrics||{}).stars??''}</td></tr>`).join('')}</tbody></table></div>`}
document.getElementById('list').addEventListener('click',e=>{const go=e.target.closest('a[data-go]');if(go){e.preventDefault();openEntry(go.dataset.go);return}const sc=e.target.closest('[data-scope]');if(sc){resetAll();st.cov.add(sc.dataset.scope);update();document.getElementById('directory').scrollIntoView({behavior:SMOOTH()});return}const wb=e.target.closest('[data-brand]');if(wb){resetAll();setQuery(brandName(wb.dataset.brand));update();const h=document.getElementById('bn-h');document.getElementById('directory').scrollIntoView({behavior:SMOOTH()});if(h)h.focus({preventScroll:true});return}const h=e.target.closest('button[data-k]');if(h){const k=h.dataset.k;st.sort=!st.sort||st.sort.k!==k?{k,d:1}:st.sort.d>0?{k,d:-1}:null;keepFocus(drawList);return}const row=e.target.closest('tr[data-go]');if(row&&!e.target.closest('a')){st.view='cards';openEntry(row.dataset.go)}});
document.getElementById('viewsw').onclick=e=>{const b=e.target.closest('[data-v]');if(b){st.view=b.dataset.v;update(false)}};
function drawList(){const rs=R.filter(r=>match(r));document.getElementById('count').innerHTML=rs.length+' / '+R.length+'<span class="cw"> '+t('shown')+'</span>';const list=document.getElementById('list');
 document.querySelectorAll('#viewsw [data-v]').forEach(b=>b.setAttribute('aria-pressed',b.dataset.v===st.view));
 if(!rs.length){list.innerHTML=(BM?banner(R.find(r=>r.id===BM),BRANDS.find(x=>x.id===BM),rs):'')+`<div class="empty">${t('none')}</div>`;return}
 if(st.view==='table'){root.style.setProperty('--bar-h',(document.querySelector('.bar').offsetHeight+hdr())+'px');if(hits&&!st.sort)rs.sort((a,b)=>hits.get(b.id)-hits.get(a.id));list.innerHTML=(BM?banner(R.find(r=>r.id===BM),BRANDS.find(x=>x.id===BM),rs):'')+drawTable(rs);return}
 if(BM){const nm=brandName(BM),b=BRANDS.find(x=>x.id===BM),re=new RegExp('(^|[^a-z0-9])('+[b.name,...b.aka].map(n=>fold(n).replace(/[.*+?^${}()|[\]\\]/g,'\\$&')).join('|')+')([^a-z0-9]|$)'),
   others=b.lego?[]:R.filter(r=>r.id!==BM&&!linked(r,BM)&&re.test(fold([r.name,r[L].summary,...r[L].strengths,...r[L].weaknesses,sizeOf(r)].join(' '))));  // for LEGO, every entry would
  list.innerHTML=banner(R.find(r=>r.id===BM),b,rs)+byCat(rs,crank)+(others.length?`<details class="more"><summary>${esc(tn('bm_more',others.length).replace('{b}',nm))}</summary><div class="grid" style="margin-top:10px">${others.map(r=>card(r,true)).join('')}</div></details>`:'');return}
 if(hits){rs.sort((a,b)=>hits.get(b.id)-hits.get(a.id));list.innerHTML=`<section class="cat"><h3>${t('ranked')} <span class="count">${rs.length}</span></h3><div class="grid">${rs.map(r=>card(r,true)).join('')}</div></section>`;return}
 list.innerHTML=byCat(rs)}
function byCat(rs,first){return C.map(c=>{const cr=rs.filter(r=>r.cat===c.id);if(!cr.length)return'';
  cr.sort((a,b)=>(first?first(a)-first(b):0)||(c.groups.findIndex(g=>g.id===a.group)-c.groups.findIndex(g=>g.id===b.group))||(lrank(a)-lrank(b))||a.name.localeCompare(b.name));
  return `<section class="cat"><h3>${ci(c.id)}${esc(c[L])} <span class="count">${cr.length}</span></h3><div class="grid">${cr.map(r=>card(r,false)).join('')}</div></section>`}).join('')}
function toDir(){if(cur!=='dir')history.pushState(null,'',location.pathname+location.search);show('dir')}
function openEntry(id){toDir();resetAll();st.view='cards';update();const el=document.getElementById('r-'+id);if(!el)return;const d=el.querySelector('details');if(d)d.open=true;document.querySelectorAll('.card.focus').forEach(c=>c.classList.remove('focus'));el.classList.add('focus');root.style.setProperty('--bar-h',(document.querySelector('.bar').offsetHeight+hdr())+'px');settle(el)}
function settle(el,n=0){el.scrollIntoView({block:'start'});if(n<10)requestAnimationFrame(()=>settle(el,n+1));else setTimeout(()=>el.scrollIntoView({block:'start'}),250)}  // the cards above get their real height as they near the screen
const mg=document.getElementById('mapgrid');
const spans=(()=>{const n=C.map(c=>R.filter(r=>r.cat===c.id).length),tot=n.reduce((a,b)=>a+b,0),raw=n.map(v=>Math.max(2,Math.round(24*v/tot)));const rows=[];let acc=[];for(const s of raw){if(acc.reduce((a,b)=>a+b,0)+s>12&&acc.length){rows.push(acc);acc=[]}acc.push(s)}if(acc.length)rows.push(acc);
 return rows.flatMap(r=>{const s=r.reduce((a,b)=>a+b,0),k=r.map(x=>Math.max(2,Math.round(x*12/s)));k[k.length-1]+=12-k.reduce((a,b)=>a+b,0);return k})})();
function drawMap(){mg.innerHTML=C.map((c,i)=>{const rs=R.filter(r=>r.cat===c.id);return `<div class="tile${st.cat.has(c.id)?' on':''}" style="--span:${spans[i]}" data-cat="${c.id}"><h3><button type="button" class="tt" data-cat="${c.id}" aria-pressed="${st.cat.has(c.id)}">${esc(c[L])}</button></h3><span class="n">${rs.length}</span><span class="studs">${rs.map(r=>`<button type="button" tabindex="-1" class="stud ${world(r)}${r.status==='active'?'':' dim'}" data-go="${r.id}" data-tip="${esc(r.name)}" aria-label="${esc(r.name)}"></button>`).join('')}</span></div>`}).join('')}
mg.onclick=e=>{const s=e.target.closest('[data-go]');if(s){openEntry(s.dataset.go);return}const b=e.target.closest('[data-cat]');if(!b)return;toggle(st.cat,b.dataset.cat);update();document.getElementById('directory').scrollIntoView({behavior:SMOOTH()})};

document.getElementById('mapkey').innerHTML=[['official',t('official')],['both',t('both')],['alternative',t('alternative')],['',t('otherw')],['official dim',t('dim')]].map(([c,n])=>`<span><i class="stud ${c}"></i>${n}</span>`).join('');
// makers of the bricks (brands.toml `makers`, read at the source): own production, made elsewhere, not established
const mkName=x=>L==='fr'&&x.name_fr?x.name_fr:x.name,mkSrc=(xs,dated)=>xs.map(x=>`<a href="${esc(x.url)}" rel="noopener" title="${esc(fmt(x.date))}">${esc(host(x.url))}</a>${dated?' '+dt(x.date):''}`).join(', ');
const mkOf=b=>{const r=R.find(x=>x.id===b.id)||{},m=r.makers||[];return{r,own:m.filter(x=>x.id===b.id),ext:m.filter(x=>x.id!==b.id)}};
function mkLine(r){if(BN[r.id]==null||r===LEGO)return'';const{own,ext}=mkOf(r);const by={};[...own.map(x=>[t('own_make'),x]),...ext.map(x=>[mkName(x),x])].forEach(([k,x])=>(by[k]=by[k]||[]).push(x));
 const parts=Object.entries(by).map(([k,xs])=>`${esc(k)} · ${mkSrc(xs)}`);
 return `<div class="mkline">${t('bricks')}${COLON}${parts.length?parts.join(' ; '):esc(t('no_maker'))}</div>`}
// brand mode: the brand as a banner above its entries (decision of 24/11/2026, 11:58 to 12:05)
const PRE=L==='fr'?'../':'';
function banner(r,b,rs){if(!r)return'';const cats=C.map(c=>[c.id,rs.filter(x=>x.cat===c.id).length]).filter(x=>x[1]);
 const grp=((C.find(c=>c.id===r.cat)||{groups:[]}).groups.find(g=>g.id===r.group)||{})[L]||r[L].group;
 const meta=[one(r),grp].filter(Boolean).map(esc).join(' · ')+` · <a href="${esc(r.url)}" rel="noopener">${esc(host(r.url))}</a>`;
 return `<section class="banner ${b.lego?'official':'alternative'}" aria-labelledby="bn-h">${r.logo?`<img class="logo" src="${PRE}${esc(r.logo)}" alt="${esc(t('logo_of').replace('{b}',b.name))}">`:''}<div class="bt"><h3 id="bn-h" tabindex="-1">${esc(b.name)}</h3><p class="meta">${meta}</p><p class="s"${r[L].tl?' lang="en"':''}>${esc(r[L].summary)}</p>${mkLine(r)}`+
  (cats.length?`<p class="counts">${b.lego?esc(t('lego_where'))+COLON:esc(tn('n_linked',rs.length))+COLON}${cats.map(([c,n])=>`${esc(shortCat(c))} ${n}`).join(' · ')}</p>`:'')+
  (b.lego?`<button type="button" class="btn all" data-scope="official">${esc(t('lego_scope').replace('{n}',R.filter(x=>(x.covers||[]).includes('official')).length))}</button>`:'')+`</div></section>`}
function vMakers(){const el=document.getElementById('v-makers');const all=D.brands.map(b=>({...b,...mkOf(b)}));
 const own=all.filter(b=>b.own.length&&!b.ext.length),ext=all.filter(b=>b.ext.length),none=all.filter(b=>!b.own.length&&!b.ext.length);
 const via={};ext.forEach(b=>{const g={};b.ext.forEach(x=>{const k=x.name_fr||/\(/.test(x.name)||!x.id?mkName(x):brandName(x.id)||mkName(x);(g[k]=g[k]||[]).push(x)});Object.entries(g).forEach(([k,xs])=>(via[k]=via[k]||[]).push({b,xs}))});
 const btn=(id,label)=>`<button type="button" data-brand="${id}">${esc(label)}</button>`;
 el.innerHTML=`<h3>${t('mk_title')}</h3><div class="mk">`+
  `<div><h4>${t('mk_own')} (${own.length})</h4><ul>${own.map(b=>`<li>${btn(b.id,b.name)} <span class="via">${mkSrc(b.own,true)}</span></li>`).join('')}</ul></div>`+
  `<div><h4>${t('mk_ext')} (${ext.length})</h4><ul>${Object.entries(via).sort((a,b)=>b[1].length-a[1].length).map(([k,v])=>`<li><span class="via">${esc(k)} →</span> ${v.map(({b,xs})=>`${btn(b.id,b.name)} <span class="via">(${mkSrc(xs,true)})</span>`).join(' · ')}</li>`).join('')}</ul></div>`+
  `<div><h4>${t('mk_none')} (${none.length})</h4><ul>${none.map(b=>`<li>${btn(b.id,b.name)}</li>`).join('')}</ul></div></div><p class="note">${t('mk_note')}</p>`;
 el.onclick=e=>{const b=e.target.closest('button[data-brand]');if(b)brandMode(b.dataset.brand)}}
function brandMode(id){toDir();resetAll();setQuery(brandName(id));update();document.getElementById('directory').scrollIntoView({behavior:SMOOTH()});const h=document.getElementById('bn-h');if(h)h.focus({preventScroll:true})}
// insight 1: which listed resources name each alternative brand, by category
const IC=['shops','comparators','second-hand','community','video'];
function vBrands(){const el=document.getElementById('v-brands');
 const rows=D.brands.map(b=>{const v=IC.map(c=>R.filter(r=>r.cat===c&&(r.brands||[]).includes(b.id)).length);return{...b,v,tot:v.reduce((a,x)=>a+x,0)}}).sort((a,b)=>b.tot-a.tot||a.name.localeCompare(b.name));
 const seen=rows.filter(r=>r.tot),none=rows.filter(r=>!r.tot),max=Math.max(...seen.flatMap(r=>r.v),1);
 const noVoice=seen.filter(r=>r.v[0]>0&&r.v[3]===0&&r.v[4]===0);
 const nn=none.length,nv=noVoice.length,names=noVoice.map(r=>r.name).join(', ');  // singular and plural in both languages
 const take=L==='fr'?(nn?`${nn} ${nn===1?'marque':'marques'} sur ${rows.length} ${nn===1?"n'est liée":'ne sont liées'} à aucune autre fiche. `:'')+(nv?`${nv===1?'Une marque se vend':nv+' marques se vendent'} dans les boutiques recensées sans qu'aucune communauté ni chaîne vidéo n'en parle : ${names}.`:'')
  :(nn?`${nn} ${nn===1?'brand':'brands'} out of ${rows.length} ${nn===1?'is':'are'} linked to no other entry. `:'')+(nv?`${nv===1?'One brand is':nv+' brands are'} sold in the listed shops with no community or video channel talking about ${nv===1?'it':'them'}: ${names}.`:'');
 const FG=RGB('--fg'),CD=RGB('--card'),SQ=RGB('--seq'),mix=p=>SQ.map((v,i)=>v*p/100+CD[i]*(1-p/100));
 const ink=pct=>{const mx=mix(pct);return CR(mx,FG)>=CR(mx,CD)?'var(--fg)':'var(--card)'};  // the darker or lighter text, whichever reads best on this cell
 const fit=pct=>{for(let p=pct;p<=100;p++){const mx=mix(p);if(Math.max(CR(mx,FG),CR(mx,CD))>=4.5)return p}return pct};  // a shade where neither text reads is darkened a little
 const cell=(r,i)=>{const pct=fit(Math.round(14+66*r.v[i]/max));return r.v[i]?`<button type="button" class="c" style="background:color-mix(in srgb,var(--seq) ${pct}%,var(--card));color:${ink(pct)}" data-f="${IC[i]}|${r.id}" aria-label="${esc(r.name)}, ${esc(catName(IC[i]))}${COLON}${r.v[i]}" data-tip="${esc(r.name)} · ${esc(catName(IC[i]))}${COLON}${r.v[i]}">${r.v[i]}</button>`:`<span class="c z" aria-hidden="true">·</span>`};
 el.innerHTML=`<h3>${t('b_title')}</h3><p class="take">${esc(take)}</p><div class="heatbox" role="region" tabindex="0" aria-label="${esc(t('b_title'))}"><div class="heat" style="grid-template-columns:minmax(92px,1.3fr) repeat(${IC.length},minmax(34px,1fr))"><span></span>${IC.map(c=>`<span class="h">${esc(shortCat(c))}</span>`).join('')}${seen.map(r=>`<span class="rn">${esc(r.name)}</span>${IC.map((_,i)=>cell(r,i)).join('')}`).join('')}${none.length?`<span class="sep">${t('b_none')}</span><span class="rn" style="grid-column:1/-1;white-space:normal;color:var(--muted)">${esc(none.map(r=>r.name).join(' · '))}</span>`:''}</div></div><p class="note">${t('b_note')}</p>`;
 el.onclick=e=>{const b=e.target.closest('[data-f]');if(!b)return;const[c,id]=b.dataset.f.split('|');toDir();resetAll();setQuery(brandName(id));st.cat.add(c);update();document.getElementById('directory').scrollIntoView({behavior:SMOOTH()})}}
// insight 2: pulse. Dormant resources (no activity for 6 months) one by one; the active ones counted per category
function vPulse(){const RA=R.filter(r=>r.regime==='activity');  // finished works and places open or closed are not measured by their posts
const el=document.getElementById('v-pulse');const cats=C.map(c=>c.id),today=new Date(D.built),from=new Date(today);from.setMonth(from.getMonth()-24);
 const six=new Date(today);six.setMonth(six.getMonth()-6);
 const W=Math.max(300,el.clientWidth-40),lw=Math.min(170,W*.36),cut=v=>v.length*7.6>lw?v.slice(0,Math.max(4,Math.floor(lw/7.6)-1))+'…':v,x0=lw+14,x1=W-90,xs=Math.min(x0+(W-x0-90)*0.82,x1-70),rh=34,H=cats.length*rh+30,X=d=>x0+(xs-x0)*Math.max(0,Math.min(1,(d-from)/(six-from)));
 const old=RA.filter(r=>r.last&&new Date(r.last)<six),nolast=RA.filter(r=>!r.last).length;
 const top=Object.entries(old.reduce((a,r)=>(a[r.cat]=(a[r.cat]||0)+1,a),{})).sort((a,b)=>b[1]-a[1])[0];
 const take=L==='fr'?`Parmi les sites, chaînes, forums et logiciels, ${old.length} n'ont montré aucun signe de vie depuis 6 mois${top?`, surtout dans « ${catName(top[0])} » (${top[1]})`:''} ; ${nolast} n'ont pas de date observable. Œuvres, lieux, boutiques et marques n'y figurent pas : leurs publications ne les mesurent pas.`
  :`Among sites, channels, forums and software, ${old.length} have shown no sign of life for 6 months${top?`, mostly in "${catName(top[0])}" (${top[1]})`:''}; ${nolast} have no observable date. Works, places, shops and brands are left out: their posts do not measure them.`;
 let s=`<svg class="pulse" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(t('p_title'))}">`;
 s+=`<rect x="${xs}" y="2" width="${x1-xs}" height="${H-26}" fill="var(--sunk)" rx="4"/><text class="ax" x="${(xs+x1)/2}" y="${H-6}" text-anchor="middle">${t('p_recent')}</text>`;
 const mm=d=>String(d.getMonth()+1).padStart(2,'0')+'/'+d.getFullYear();  // the axis in figures, month and year (decision of 25/11/2026: no day, no ambiguity)
 // marks at fixed places, chosen by the room the scale leaves (figures have one width: about 7 px each): every 6 months, every 12, the first one only, or none on the narrowest screens
 const step=(xs-x0)/3,first=9*7,half=4*7,room=(xs+x1)/2-t('p_recent').length*3.6-8-x0,ks=step>=first+half+8?[0,6,12]:2*step>=first+half+8?[0,12]:room>=first?[0]:[];
 for(const k of ks){const d=new Date(from);d.setMonth(d.getMonth()+k);s+=`<text class="ax" x="${X(d)}" y="${H-6}" text-anchor="${k?'middle':'start'}">${k?'':'≤ '}${mm(d)}</text>`}
 cats.forEach((c,i)=>{const y=14+i*rh,rs=RA.filter(r=>r.cat===c&&r.last);s+=`<text x="${lw}" y="${y+5}" text-anchor="end">${esc(cut(shortCat(c)))}</text><line x1="${x0}" x2="${xs}" y1="${y}" y2="${y}" stroke="var(--line)"/>`;
  const placed=[],old2=rs.filter(r=>new Date(r.last)<from);
  if(old2.length){s+=`<circle cx="${x0}" cy="${y}" r="${old2.length>1?9:5.5}" fill="var(--card)" stroke="var(--warn)" stroke-width="2.5" data-go="${old2[0].id}" data-tip="${esc(old2.map(r=>r.name+' · '+fmt(r.last)).join(' ; '))}" style="cursor:pointer"/>`+(old2.length>1?`<text x="${x0}" y="${y+4}" text-anchor="middle" style="font-size:10px;font-weight:700;fill:var(--warn);pointer-events:none">${old2.length}</text>`:'');placed.push({x:x0,dy:0})}
  rs.filter(r=>new Date(r.last)<six&&new Date(r.last)>=from).sort((a,b)=>a.last<b.last?-1:1).forEach(r=>{const x=X(new Date(r.last));let dy=0;for(const k of [0,-9,9,-18,18]){if(!placed.some(p=>Math.abs(p.x-x)<10&&p.dy===k)){dy=k;break}}placed.push({x,dy});
   s+=`<circle cx="${x}" cy="${y+dy}" r="5.5" fill="var(--card)" stroke="var(--warn)" stroke-width="2.5" data-go="${r.id}" data-tip="${esc(r.name)} · ${fmt(r.last)}" style="cursor:pointer"/>`});
  const n=rs.filter(r=>new Date(r.last)>=six).length,bw=(x1-xs-30)*n/Math.max(1,...cats.map(cc=>RA.filter(r=>r.cat===cc&&r.last&&new Date(r.last)>=six).length));
  s+=`<rect x="${xs+6}" y="${y-6}" width="${bw}" height="12" rx="3" fill="var(--other)" data-tip="${esc(shortCat(c))} · ${n}"/><text class="ax" x="${xs+10+bw}" y="${y+4}">${n}</text>`});
 el.innerHTML=`<h3>${t('p_title')}</h3><p class="take">${esc(take)}</p>${s}</svg><p class="note">${t('p_note')}</p>`;

 el.onclick=e=>{const p=e.target.closest('[data-go]');if(p)openEntry(p.dataset.go)}}
// insight 3: recognised fan communities against population, by country (backend data)
function vPassion(){const el=document.getElementById('v-passion'),P=D.passion;if(!el)return;if(!P){el.remove();return}
 const rows=P.rows.filter(r=>r.pop),nopop=P.rows.filter(r=>!r.pop),avg=rows.reduce((a,r)=>a+r.n,0)/rows.reduce((a,r)=>a+r.pop,0);
 const has=new Set(CTRY.map(c=>c[0])),f=x=>x.toFixed(1),lg=Math.log10;
 const rated=rows.map(r=>({...r,k:r.n/r.pop/avg}));
 const top=rated.filter(r=>r.n>=3).sort((a,b)=>b.k-a.k).slice(0,3),low=rated.filter(r=>r.pop>=4e7&&r.k<1).sort((a,b)=>a.k-b.k);
 const list=a=>a.map(r=>`${cname(r.c)} (×${f(r.k)})`).join(', ');
 const take=L==='fr'?`Rapportés à leur population, ${list(top)} comptent le plus de communautés de fans reconnues. ${low.length} grands pays restent sous la moyenne : ${low.map(r=>cname(r.c)).join(', ')}.`
  :`Relative to population, ${list(top)} have the most recognised fan communities. ${low.length} large countries stay below the average: ${low.map(r=>cname(r.c)).join(', ')}.`;
 const W=Math.max(320,el.clientWidth-40),H=Math.min(420,Math.max(280,W*.42)),ml=44,mr=16,mt=10,mb=40;
 const X=v=>ml+(W-ml-mr)*(lg(v)-lg(3e5))/(lg(5e8)-lg(3e5)),Y=v=>mt+(H-mt-mb)*(1-(Math.log2(v)-Math.log2(.8))/(Math.log2(80)-Math.log2(.8)));
 let s=`<svg class="passion" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(t('pa_title'))}"><defs><clipPath id="pc"><rect x="${ml}" y="${mt}" width="${W-ml-mr}" height="${H-mt-mb}"/></clipPath></defs>`;
 for(const v of [1e6,1e7,1e8])s+=`<line x1="${X(v)}" x2="${X(v)}" y1="${mt}" y2="${H-mb}" stroke="var(--line)"/><text class="ax" x="${X(v)}" y="${H-mb+16}" text-anchor="middle">${v/1e6} M</text>`;
 for(const v of [1,2,5,10,20,50])s+=`<line x1="${ml}" x2="${W-mr}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--line)"/><text class="ax" x="${ml-6}" y="${Y(v)+4}" text-anchor="end">${v}</text>`;
 s+=`<text class="ax" x="${W-mr}" y="${H-4}" text-anchor="end">${t('pa_pop')} →</text><text class="ax" x="${ml}" y="${mt+12}" dx="6">↑ ${t('pa_n')}</text>`;
 s+=`<line clip-path="url(#pc)" x1="${X(3e5)}" y1="${Y(avg*3e5)}" x2="${X(5e8)}" y2="${Y(avg*5e8)}" stroke="var(--muted)" stroke-width="1.5" stroke-dasharray="5 4"/>`;
 const placed=[],boxes=[],lab=[];
 rated.sort((a,b)=>b.n-a.n||b.pop-a.pop).forEach(r=>{const x=X(r.pop);let y=Y(r.n);for(const k of [0,-7,7,-14,14]){if(!placed.some(p=>Math.abs(p.x-x)<9&&Math.abs(p.y-(y+k))<9)){y+=k;break}}placed.push({x,y});
  const go=has.has(r.c);s+=`<circle cx="${x}" cy="${y}" r="5.5" fill="${r.k>=1?'var(--accent)':'var(--other)'}" stroke="var(--card)" stroke-width="2"${go?` data-c="${r.c}" style="cursor:pointer"`:''} data-tip="${esc(cname(r.c))} · ${r.n} · ×${f(r.k)}"/>`;
  if(r.n>=(W<600?10:3))lab.push({r,x,y})});
 const hit=(bx,by,w)=>boxes.some(b=>bx<b.x+b.w&&bx+w>b.x&&by<b.y+13&&by+13>b.y)||placed.some(p=>p.x+6>bx&&p.x-6<bx+w&&p.y+6>by&&p.y-6<by+13);
 lab.forEach(({r,x,y})=>{const w=cname(r.c).length*6.8;for(const [dx,dy,a] of [[9,4,'start'],[-9,4,'end'],[0,-10,'middle'],[0,19,'middle'],[9,-9,'start'],[-9,-9,'end'],[9,17,'start'],[-9,17,'end']]){const bx=a==='start'?x+dx:a==='end'?x+dx-w:x-w/2,by=y+dy-11;if(bx<ml||bx+w>W-mr||by<mt)continue;if(!hit(bx,by,w)){boxes.push({x:bx,y:by,w});s+=`<text class="lb" x="${x+dx}" y="${y+dy}" text-anchor="${a}">${esc(cname(r.c))}</text>`;break}}});
 const xn=nopop.length?t('pa_nopop')+nopop.map(r=>`${cname(r.c)} (${r.n})`).join(', ')+'.':'';
 el.innerHTML=`<h3>${t('pa_title')}</h3><p class="take">${esc(take)}</p>${s}</svg><p class="note">${esc(t('pa_note').replace('{y}',P.pop_year).replace('{x}',xn)).replace('{d}',dt(P.date))}</p>`;
 const kept=[];el.querySelectorAll('svg text').forEach(x=>{const b=x.getBBox(),hit=kept.some(k=>b.x<k.x+k.width-1&&k.x<b.x+b.width-1&&b.y<k.y+k.height-1&&k.y<b.y+b.height-1);if(hit&&x.classList.contains('lb'))x.remove();else kept.push(b)});  // a country name that the estimate placed over another text is left out (its point keeps its tooltip)
 el.onclick=e=>{const p=e.target.closest('[data-c]');if(!p)return;toDir();resetAll();st.country=p.dataset.c;update();document.getElementById('directory').scrollIntoView({behavior:SMOOTH()})}}
var drawn=false;matchMedia('(prefers-color-scheme: dark)').addEventListener('change',()=>{if(drawn)vBrands()});  // colours chosen by contrast are chosen again
function drawInsights(){vPassion();vMakers();vBrands();vPulse();drawn=true}
let rz;addEventListener('resize',()=>{clearTimeout(rz);rz=setTimeout(()=>{hdr();if(cur==='obs'){vPulse();vPassion()}},150)});
// two views: directory, observatory; the address keeps the view
const VIEWS={dir:document.getElementById('view-dir'),obs:document.getElementById('view-obs')};let cur='dir';
const viewOf=h=>(h==='#observatory'||h==='#findings')?'obs':'dir';  // #findings: address of the former "Findings" view
const OUT=/^#(out|agenda|near-me)$/;  // addresses of the former "Out and about" view: "Where to start" now points to the calendars, clubs and places
function show(view,first){const was=cur;cur=view;document.title=view==='dir'?TITLE0:t('nav_'+view)+' · '+TITLE0;Object.entries(VIEWS).forEach(([k,el])=>el.hidden=k!==view);document.querySelectorAll('nav.tabs a').forEach(a=>{if(a.dataset.view===view)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current')});
 if(view==='obs'){if(!drawn)drawInsights();else{vPulse();vPassion()}}const sec=view==='dir'&&(first?OUT0:OUT.test(location.hash))?document.getElementById('start'):null;if(sec)sec.scrollIntoView();else if(!first&&was!==view)scrollTo({top:0})}  // no forced layout on the first display
document.getElementById('skip').onclick=e=>{e.preventDefault();toDir();const q=document.getElementById('q');q.scrollIntoView({block:'center'});q.focus()};
document.querySelector('nav.tabs a[data-view=dir]').onclick=e=>{e.preventDefault();toDir();writeHash();document.getElementById('map').scrollIntoView({behavior:SMOOTH()})};
addEventListener('hashchange',()=>{const v=viewOf(location.hash);if(v!=='dir'||cur!=='dir'||OUT.test(location.hash))show(v)});
function writeHash(){if(cur!=='dir')return;const p=new URLSearchParams();if(st.q.trim())p.set('q',st.q.trim());if(st.cat.size)p.set('cat',[...st.cat].join(','));if(st.cov.size)p.set('scope',[...st.cov].join(','));const cr=['featured','active'].filter(k=>st[k]);if(cr.length)p.set('crit',cr.join(','));if(st.langs.size)p.set('lang',[...st.langs].join(','));if(st.country)p.set('country',st.country);if(st.view!=='cards')p.set('view',st.view);const h=p.toString();history.replaceState(null,'',h?'#'+h:location.pathname+location.search)}
function readHash(){const h=location.hash.slice(1);if(!h||viewOf(location.hash)!=='dir')return;const p=new URLSearchParams(h);(p.get('cat')||'').split(',').filter(Boolean).forEach(c=>st.cat.add(c));(p.get('scope')||'').split(',').filter(Boolean).forEach(c=>st.cov.add(c));(p.get('crit')||'').split(',').forEach(k=>{if(k==='fr')st.langs.add('fr');else if(k in st&&typeof st[k]==='boolean')st[k]=true});(p.get('lang')||'').split(',').filter(Boolean).forEach(l=>st.langs.add(l));if(p.get('country'))st.country=p.get('country');if(p.get('view')==='table')st.view='table';if(p.get('q'))setQuery(p.get('q'))}
const ft=document.getElementById('ftoggle'),bar=document.querySelector('.bar');
ft.onclick=()=>{const o=bar.classList.toggle('open');ft.setAttribute('aria-expanded',o)};
function nActive(){return st.cat.size+st.cov.size+['featured','active'].filter(k=>st[k]).length+st.langs.size+(st.country?1:0)}
const FKEYS=['cat','cov','m','lang','k','v','brand'];  // a control redrawn by innerHTML gets the focus back
function keepFocus(draw){const a=document.activeElement,k=a&&a.dataset?FKEYS.find(x=>a.dataset[x]!==undefined):null,v=k&&a.dataset[k],box=k&&a.closest('[id]'),cls=a&&a.className;draw();
 if(k&&box&&!document.body.contains(a)){const b=document.getElementById(box.id);if(!b)return;const n=[...b.querySelectorAll(`[data-${k}]`)].find(x=>x.dataset[k]===v&&x.className.split(' ')[0]===String(cls).split(' ')[0])||[...b.querySelectorAll(`[data-${k}]`)].find(x=>x.dataset[k]===v);if(n)n.focus({preventScroll:true})}}
function update(all=true){keepFocus(()=>update0(all))}
function update0(all){const n=nActive();ft.textContent=t('filters')+(n?` (${n})`:'');drawFilters();drawList();if(all)drawMap();writeHash()}
const VC=(()=>{const tags=navigator.languages||[navigator.language];for(const t of tags){const m=/^[a-z]{2,3}-([A-Z]{2})$/i.exec(t||'');if(m)return m[1].toUpperCase()}
 return {fr:'FR',de:'DE',it:'IT',es:'ES',nl:'NL',pl:'PL',pt:'PT',da:'DK',sv:'SE',nb:'NO',no:'NO',fi:'FI',cs:'CZ'}[VL]||''})();
const crank=r=>{const c=r.countries||[];return (VC&&c.includes(VC))||(VC==='FR'&&r.ships_to_france)?0:c.includes('international')?1:2};
// search suggestions, built from the data: brands (with their other names), entries, categories, countries and cities
const SG=(()=>{const out=[],add=(g,label,names,w,go,d)=>out.push({g,label,keys:names.map(fold),w,go,d});
 BRANDS.forEach(b=>add('brand',b.name,[b.name,...b.aka],BN[b.id],{q:b.name},tn('n_linked',BN[b.id])+(b.aka.length?' · '+b.aka.join(', '):'')));
 R.filter(r=>BN[r.id]==null).forEach(r=>add('entry',r.name,[r.name],(r.featured?100:0)+(r.status==='active'?10:0),{entry:r.id},catName(r.cat)));
 C.forEach(c=>{const n=R.filter(r=>r.cat===c.id).length;add('cat',c[L],[c[L],c.en,c.fr],n,{cat:c.id},tn('n_entries',n))});
 CTRY.forEach(([c,n])=>add('place',cname(c),[cname(c),c],n,{country:c},tn('n_entries',n)));
 add('entry',L==='fr'?'Un mur qui cache autre chose':'A wall that hides something',['konami','secret','vault','cheat','easter egg','hidden','coffre','triche'],-1,{vault:true},'↑ ↑ ↓ ↓ ← → ← → B A');  // a hint towards the Brick Vault
 Object.values(R.reduce((a,r)=>{if(r.city)(a[r.city]=a[r.city]||{r0:r,rs:[]}).rs.push(r);return a},{})).forEach(({r0,rs})=>add('place',cityOf(r0),[r0.city,r0.city_fr,r0.city_local].filter(Boolean),rs.length,{q:cityOf(r0)},rs.map(r=>catName(r.cat)).filter((v,i,a)=>a.indexOf(v)===i).join(', ')));  // a city is found by its English, French or local name
 return out})();
const sugg=document.getElementById('sugg');let sgItems=[],sgAt=-1;
function suggest(v){const f=fold(v.trim());sgItems=[];sgAt=-1;
 if(f.length>=2){const rank=x=>{let best=9;for(const k of x.keys){if(k.startsWith(f))best=Math.min(best,0);else if(k.split(/[^a-z0-9]+/).some(w=>w.startsWith(f)))best=Math.min(best,1)}return best};  // the start of the name, or of one of its words
  for(const g of ['brand','entry','cat','place']){sgItems.push(...SG.filter(x=>x.g===g).map(x=>({...x,r:rank(x)})).filter(x=>x.r<9&&(!x.go.vault||f.length>=5)).sort((a,b)=>a.r-b.r||b.w-a.w||a.label.localeCompare(b.label)).slice(0,3))}
  sgItems=sgItems.slice(0,8)}
 const hl=l=>{const i=fold(l).indexOf(f);return i<0?esc(l):esc(l.slice(0,i))+'<mark>'+esc(l.slice(i,i+f.length))+'</mark>'+esc(l.slice(i+f.length))};
 sugg.innerHTML=['brand','entry','cat','place'].map(g=>{const xs=sgItems.map((x,i)=>[x,i]).filter(([x])=>x.g===g);return xs.length?`<div role="group" aria-label="${esc(t('sg_'+g))}"><div class="sg" aria-hidden="true">${t('sg_'+g)}</div>${xs.map(([x,i])=>`<div role="option" id="sg-${i}" data-i="${i}" aria-selected="false"><span>${hl(x.label)}</span><span class="d">${esc(x.d||'')}</span></div>`).join('')}</div>`:''}).join('');
 sugg.hidden=!sgItems.length;q.setAttribute('aria-expanded',!sugg.hidden);q.removeAttribute('aria-activedescendant')}
function sgMove(d){if(!sgItems.length)return;sgAt=(sgAt+d+sgItems.length)%sgItems.length;sugg.querySelectorAll('[role=option]').forEach(o=>o.setAttribute('aria-selected',+o.dataset.i===sgAt));q.setAttribute('aria-activedescendant','sg-'+sgAt);const o=document.getElementById('sg-'+sgAt);if(o)o.scrollIntoView({block:'nearest'})}
function sgClose(){sugg.hidden=true;sgItems=[];sgAt=-1;q.setAttribute('aria-expanded','false');q.removeAttribute('aria-activedescendant')}
function sgPick(x){sgClose();const go=x.go;if(go.vault){location.href=(L==='fr'?'../':'')+'vault/';return}if(go.entry){openEntry(go.entry);return}
 resetAll();if(go.q)setQuery(go.q);if(go.cat)st.cat.add(go.cat);if(go.country)st.country=go.country;update();document.getElementById('directory').scrollIntoView({behavior:SMOOTH()})}
q.addEventListener('input',()=>suggest(q.value));
q.addEventListener('keydown',e=>{if(e.key==='ArrowDown'){e.preventDefault();if(sugg.hidden)suggest(q.value);sgMove(1)}else if(e.key==='ArrowUp'){e.preventDefault();sgMove(-1)}
 else if(e.key==='Enter'){if(sgAt>=0){e.preventDefault();sgPick(sgItems[sgAt])}else{sgClose();clearTimeout(qt);setQuery(q.value);update(false)}}else if(e.key==='Escape'&&!sugg.hidden){e.preventDefault();sgClose()}});
sugg.addEventListener('mousedown',e=>e.preventDefault());  // keep the focus in the field
sugg.addEventListener('click',e=>{const o=e.target.closest('[data-i]');if(o)sgPick(sgItems[+o.dataset.i])});
q.addEventListener('blur',()=>setTimeout(sgClose,100));
// "Where to start" (data/journeys.toml): per need, the reference of the visitor's country or language, then entries of its groups ranked
// for the visitor (their rank in the visitor's country or language first, then worldwide), then the whole category; 4 lines at most
const byId=id=>R.find(r=>r.id===id);
function needEntries(j,skip,n){const key=j.scope==='country'?VC:j.scope==='language'?VL:'',inG=r=>j.groups.includes(r.cat+'/'+r.group)&&r.id!==skip&&r.status!=='dead';
 if(j.mode==='brand')return R.filter(r=>inG(r)&&BN[r.id]!=null&&r.rank&&r.rank.intl).sort((a,b)=>a.rank.intl-b.rank.intl).slice(0,n);
 const rk=r=>{const x=r.rank||{};return key&&x[key]?[0,x[key]]:x.intl?[1,x.intl]:null};
 return R.filter(r=>inG(r)&&rk(r)).sort((a,b)=>{const x=rk(a),y=rk(b);return x[0]-y[0]||x[1]-y[1]||lrank(a)-lrank(b)}).slice(0,n)}
function drawNeeds(){document.getElementById('journeys').innerHTML=(D.journeys||[]).map(j=>{const key=j.scope==='country'?VC:j.scope==='language'?VL:'',rf=j.reference||{},ref=byId(rf[key]||rf.default),es=needEntries(j,ref&&ref.id,ref?2:3),n=R.filter(r=>r.cat===j.category).length;
 const li=(r,cls)=>`<li${cls?` class="${cls}"`:''}><a href="#entry=${r.id}" ${j.mode==='brand'?`data-brand="${r.id}"`:`data-go="${r.id}"`}>${esc(r.name)}</a></li>`;
 return `<div class="jr"><h3>${ci(j.category)}${esc(j['title_'+L])}</h3><ul>${ref?li(ref,'ref'):''}${es.map(r=>li(r)).join('')}<li class="all"><a href="#cat=${j.category}" data-cat="${j.category}">${esc(catName(j.category))} <span class="nw">· ${n} →</span></a></li></ul></div>`}).join('')}
drawNeeds();
document.getElementById('journeys').onclick=e=>{const a=e.target.closest('a');if(!a)return;e.preventDefault();if(a.dataset.go)openEntry(a.dataset.go);else if(a.dataset.brand)brandMode(a.dataset.brand);else if(a.dataset.cat){resetAll();st.cat.add(a.dataset.cat);update();document.getElementById('directory').scrollIntoView({behavior:SMOOTH()})}};
const landing=new URLSearchParams(location.hash.slice(1)).get('entry');  // #entry=<id>: a link to one entry (feed, outside pages)
const v0=viewOf(location.hash),OUT0=OUT.test(location.hash);cur=v0;readHash();update();show(v0,true);if(landing)openEntry(landing);document.documentElement.classList.add('ready');
q.addEventListener('focus',()=>{det();index()},{once:true});
(window.requestIdleCallback||(f=>setTimeout(f,1500)))(()=>det());  // the search index is built when the search field is first used
})();
