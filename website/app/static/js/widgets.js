// Copy buttons for the embed snippets on /widgets.
(function () {
    function fallbackCopy(text) {
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); } catch (e) {}
        document.body.removeChild(ta);
    }

    document.querySelectorAll('.code-copy-btn').forEach(function (btn) {
        var label = btn.textContent;
        btn.addEventListener('click', function () {
            var text = btn.parentNode.querySelector('code').textContent;
            var done = function () {
                btn.textContent = btn.dataset.copied;
                btn.classList.add('copied');
                setTimeout(function () {
                    btn.textContent = label;
                    btn.classList.remove('copied');
                }, 1500);
            };
            if (navigator.clipboard && window.isSecureContext) {
                navigator.clipboard.writeText(text).then(done, function () {
                    fallbackCopy(text);
                    done();
                });
            } else {
                fallbackCopy(text);
                done();
            }
        });
    });
})();
