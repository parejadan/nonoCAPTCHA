// string format replace <target_site_recaptcha_anchor>
() => {
    widget = JQuery("<div id=recaptcha-widget>").appendTo("body");
    parent.window.recapReady = function() {
        grecaptcha.render(document.getElementById('recaptcha-widget'), {
            sitekey: '<target_site_recaptcha_anchor>',
            callback: function() {
                console.log('recaptcha callback')
            }
        });
    };
}