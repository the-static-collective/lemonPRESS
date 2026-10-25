// lemonPRESS Issue 000 / public proof reader, read-only, distinct from admitted house publication.
import {SITE} from './site.ts';
Deno.serve(req=>{
  if(req.method!=='GET'&&req.method!=='HEAD')return new Response(JSON.stringify({error:'READ_ONLY_PRESS_PROOF'}),{status:405,headers:{'content-type':'application/json; charset=utf-8','allow':'GET, HEAD'}});
  return new Response(req.method==='HEAD'?null:SITE,{status:200,headers:{
    'content-type':'text/html; charset=utf-8','x-content-type-options':'nosniff',
    'referrer-policy':'no-referrer','cache-control':'public,max-age=180',
    'permissions-policy':'camera=(),microphone=(),geolocation=()',
    'content-security-policy':"default-src 'none'; base-uri 'none'; frame-ancestors 'none'; object-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; form-action 'none'"
  }});
});
