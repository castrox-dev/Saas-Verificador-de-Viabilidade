document.addEventListener('DOMContentLoaded', function(){
  const form = document.getElementById('loginForm');
  if(!form) return;

  const rowPwd = document.getElementById('rowPassword');
  const rowEmail = document.getElementById('rowEmail');
  const btn = document.getElementById('actionBtn');
  const emailInput = document.getElementById('id_username');
  const pwdInput = document.getElementById('id_password');
  const remember = document.getElementById('rememberEmail');

  // Prefill pelo localStorage
  try{
    const savedEmail = localStorage.getItem('rememberedEmail');
    if (savedEmail) { emailInput.value = savedEmail; if(remember) remember.checked = true; }
  }catch(_){/* ignore */}

  form.addEventListener('submit', (e) => {
    const step = form.getAttribute('data-step');
    if (step === '1') {
      e.preventDefault();
      // Avança para etapa 2
      if(rowPwd) rowPwd.style.display = '';
      if(btn) btn.textContent = 'Entrar';
      form.setAttribute('data-step', '2');
      if(pwdInput) pwdInput.focus();
    } else {
      // Persistência do e-mail no localStorage
      try {
        if (remember && remember.checked && emailInput && emailInput.value.trim()) {
          localStorage.setItem('rememberedEmail', emailInput.value.trim());
        } else {
          localStorage.removeItem('rememberedEmail');
        }
      } catch(_) {}
      // Submete normalmente
    }
  });
});