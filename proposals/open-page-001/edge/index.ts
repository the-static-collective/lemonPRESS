import {SITE} from './site.ts';
import {PUBLIC_CALLS} from './calls.ts';
const h={'cache-control':'public,max-age=300','x-content-type-options':'nosniff','referrer-policy':'no-referrer'};
Deno.serve(req=>{
if(req.method!=='GET'&&req.method!=='HEAD')return new Response('Read only',{status:405,headers:{allow:'GET, HEAD'}});
const calls=new URL(req.url).searchParams.get('format')==='calls';
return new Response(req.method==='HEAD'?null:calls?JSON.stringify(PUBLIC_CALLS):SITE,{headers:{...h,'content-type':calls?'application/json; charset=utf-8':'text/html; charset=utf-8','content-security-policy':"default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; connect-src 'none'"}});
});
