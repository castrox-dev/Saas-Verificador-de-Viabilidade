// Script para registrar e gerenciar o Service Worker PWA
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    // Registrar service worker no escopo raiz para ter acesso a todo o site
    // O header Service-Worker-Allowed: / deve estar configurado no servidor
    navigator.serviceWorker.register('/static/js/sw.js', { scope: '/' })
      .then((registration) => {
        console.log('Service Worker registrado com sucesso:', registration.scope);

        // Verificar atualizações periodicamente
        registration.addEventListener('updatefound', () => {
          const newWorker = registration.installing;
          
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              // Novo service worker disponível
              console.log('Nova versão do Service Worker disponível');
              // Opcional: mostrar notificação para o usuário atualizar
            }
          });
        });
      })
      .catch((error) => {
        console.log('Falha ao registrar Service Worker:', error);
      });

    // Ouvir mensagens do service worker
    navigator.serviceWorker.addEventListener('message', (event) => {
      console.log('Mensagem do Service Worker:', event.data);
    });

    // Pedir permissão para notificações (opcional)
    if ('Notification' in window && Notification.permission === 'default') {
      // Não pedir automaticamente - apenas quando necessário
      // Notification.requestPermission();
    }
  });

  // Atualizar service worker quando a página ganhar foco
  window.addEventListener('focus', () => {
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({
        type: 'SKIP_WAITING'
      });
    }
  });
} else {
  console.log('Service Worker não suportado neste navegador');
}

// Detectar se está instalado como PWA
window.addEventListener('beforeinstallprompt', (e) => {
  // Prevenir a prompt padrão
  e.preventDefault();
  
  // Guardar o evento para mostrar depois
  window.deferredPrompt = e;
  
  // Opcional: mostrar botão de instalação personalizado
  console.log('PWA pode ser instalado');
});

// Detectar se foi instalado
window.addEventListener('appinstalled', () => {
  console.log('PWA instalado com sucesso');
  // Limpar o prompt adiado
  window.deferredPrompt = null;
});

// Função auxiliar para mostrar prompt de instalação (opcional)
function installPWA() {
  if (window.deferredPrompt) {
    window.deferredPrompt.prompt();
    
    window.deferredPrompt.userChoice.then((choiceResult) => {
      if (choiceResult.outcome === 'accepted') {
        console.log('Usuário aceitou instalar o PWA');
      } else {
        console.log('Usuário rejeitou instalar o PWA');
      }
      window.deferredPrompt = null;
    });
  }
}

// Expor função globalmente (opcional)
window.installPWA = installPWA;

