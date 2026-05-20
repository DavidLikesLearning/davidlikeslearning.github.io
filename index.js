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

});
