const $ = s => document.querySelector(s);
$('#password').addEventListener('input', () => {$('#count').textContent=`${$('#password').value.length} / 64`;});
$('#toggle').addEventListener('click', () => {const show=$('#password').type==='password';$('#password').type=show?'text':'password';$('#toggle').textContent=show?'Hide':'Show';$('#toggle').setAttribute('aria-pressed',String(show));$('#toggle').setAttribute('aria-label',show?'Hide password':'Show password');});
$('#form').addEventListener('submit', async event => {
 event.preventDefault(); $('#error').hidden=true; $('#submit').disabled=true; $('#submit').textContent='Analyzing your example…'; $('#results').setAttribute('aria-busy','true'); $('#output').hidden=true; $('#empty').hidden=false;
 const controller=new AbortController(); const timeout=setTimeout(()=>controller.abort(),30000);
 try {
  const response=await fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:$('#password').value,breach_check:$('#breach').checked}),signal:controller.signal});
  const data=await response.json(); if(!response.ok) throw new Error(data.error||'Analysis is unavailable. Please try again.');
  $('#empty').hidden=true; $('#output').hidden=false; $('#score').textContent=`${data.risk_percent.toFixed(1)}%`; $('#label').textContent=`${data.label} password`; $('#results').dataset.risk=data.label.toLowerCase(); $('#meter').value=data.risk_percent;
  $('#guidance').replaceChildren(...data.guidance.map(tip=>{const li=document.createElement('li');li.textContent=tip;return li;}));
  const messages={not_requested:'Not requested. This result contains AI analysis only.',unavailable:'The breach service could not be reached. Your AI result is still available.',not_found:'Not found in the known-breach database. This does not guarantee safety.',found:`Found in known breaches ${Number(data.breach.count||0).toLocaleString()} times. Do not use this password.`};
  $('#breach-result').textContent=messages[data.breach.status];
 }catch(err){$('#error').textContent=err.name==='AbortError'?'The request timed out. Please try again.':err instanceof SyntaxError?'The server is unavailable. Please try again.':err.message;$('#error').hidden=false;}
 finally{clearTimeout(timeout);$('#submit').disabled=false;$('#submit').textContent='Analyze password ↗';$('#results').setAttribute('aria-busy','false');}
});
