// Relay subscribe form. Credentials live only in the Cloudflare Worker.
const signalForm=document.getElementById('signal-signup');
const signalButton=document.getElementById('signal-submit');
const signalStatus=document.getElementById('signup-status');
if(signalForm){
  fetch('/api/signup-status',{headers:{accept:'application/json'}})
    .then(r=>r.ok?r.json():Promise.reject(Error('Setup pending')))
    .then(data=>{
      if(data.ready){signalButton.disabled=false;signalStatus.textContent='Subscribe by email. Confirmation is required.';}
      else{signalStatus.textContent='Signups are opening soon. Please check back.';}
    }).catch(()=>{signalStatus.textContent='Signup service is temporarily unavailable.';});
  signalForm.addEventListener('submit',async event=>{
    event.preventDefault();
    if(signalButton.disabled)return;
    const email=document.getElementById('signal-email');
    const consent=document.getElementById('signal-consent');
    if(!email.checkValidity()){email.reportValidity();return;}
    if(!consent.checked){consent.reportValidity();return;}
    signalButton.disabled=true;
    signalStatus.textContent='Requesting your confirmation email…';
    try{
      const response=await fetch('/api/subscribe',{
        method:'POST',headers:{'content-type':'application/json'},
        body:JSON.stringify({email:email.value,consent:consent.checked,website:document.getElementById('signal-website').value})
      });
      const data=await response.json();
      signalStatus.textContent=data.message||'Could not process your request.';
      if(data.ok)signalForm.reset();
    }catch(error){signalStatus.textContent='Connection trouble. Please try again shortly.';}
    finally{signalButton.disabled=false;}
  });
}
