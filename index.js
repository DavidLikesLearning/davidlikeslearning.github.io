$(document).ready(function () {

  // Hide loading screen after brief pause
  setTimeout(function () {
    $('#loading').addClass('hidden');
  }, 1100);

  // Smooth scroll for nav anchors
  $(document).on('click', 'a[href^="#"]', function (e) {
    const target = $(this.attr('href'));
    if (!target.length) return;
    e.preventDefault();
    $('html, body').animate({ scrollTop: target.offset().top - 72 }, 480);
  });

  // Fade-up cards as they scroll into view
  const observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        $(entry.target)
          .addClass('animate__animated animate__fadeInUp')
          .css({ 'animation-duration': '0.5s', 'animation-fill-mode': 'both' });
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });

  document.querySelectorAll('.card').forEach(function (card) {
    observer.observe(card);
  });

  // Tab switching (research sections)
  function activateTab(target) {
    const btn = $('.tab-btn[data-tab="' + target + '"]');
    if (!btn.length) return;
    $('.tab-btn').removeClass('active');
    btn.addClass('active');
    $('.tab-panel').removeClass('active');
    $('#' + target).addClass('active');
  }

  $('.tab-btn').on('click', function () {
    activateTab($(this).data('tab'));
  });

  // Deep-link straight to a tab via a URL hash, e.g. research.html#tab-solar
  if (window.location.hash) {
    activateTab(window.location.hash.slice(1));
  }

});
