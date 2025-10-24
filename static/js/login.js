document.addEventListener('DOMContentLoaded', function(){
  const form = document.getElementById('loginForm');
  if(!form) return;

  const rowPwd = document.getElementById('rowPassword');
  const rowEmail = document.getElementById('rowEmail');
  const btn = document.getElementById('actionBtn');
  const emailInput = document.getElementById('id_username');
  const pwdInput = document.getElementById('id_password');
  const remember = document.getElementById('rememberEmail');
  const passwordToggle = document.getElementById('passwordToggle');

  // Prefill pelo localStorage
  try{
    const savedEmail = localStorage.getItem('rememberedEmail');
    if (savedEmail) { emailInput.value = savedEmail; if(remember) remember.checked = true; }
  }catch(_){/* ignore */}

  // No passo 1 não exigir senha
  if (pwdInput) {
    pwdInput.required = false;
  }

  form.addEventListener('submit', (e) => {
    const step = form.getAttribute('data-step');
    if (step === '1') {
      e.preventDefault();
      // Avança para etapa 2
      if(rowPwd) rowPwd.style.display = '';
      if (pwdInput) {
        pwdInput.required = true;
        setTimeout(() => { try { pwdInput.focus(); } catch(_){} }, 0);
      }
      if(btn) btn.textContent = 'Entrar';
      form.setAttribute('data-step', '2');
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

  // Toggle de senha
  if (passwordToggle && pwdInput) {
    passwordToggle.addEventListener('click', function() {
      const icon = passwordToggle.querySelector('i');
      if (pwdInput.type === 'password') {
        pwdInput.type = 'text';
        icon.className = 'fas fa-eye-slash';
        passwordToggle.setAttribute('aria-label', 'Ocultar senha');
      } else {
        pwdInput.type = 'password';
        icon.className = 'fas fa-eye';
        passwordToggle.setAttribute('aria-label', 'Mostrar senha');
      }
    });
  }
});