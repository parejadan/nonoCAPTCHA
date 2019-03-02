(function() {
    checkbox_frame = parent.window.jQuery(
        "iframe[src*='api2/anchor']").contents();
    image_frame = parent.window.jQuery(
        "iframe[src*='api2/bframe']").contents();

    var bot_header = jQuery(".rc-doscaptcha-header-text", image_frame)
    if(bot_header.length) {
        if(bot_header.text().indexOf("Try again later") > -1){
            parent.window.wasdetected = true;
            return true;
        }
    }

    var try_again_header = jQuery(
        ".rc-audiochallenge-error-message", image_frame)
    if(try_again_header.length) {
        if(try_again_header.text().indexOf("please solve more") > -1){
            try_again_header.text('Trying again...')
            parent.window.tryagain = true;
            return true;
        }
    }

    var checkbox_anchor = jQuery("#recaptcha-anchor", checkbox_frame);
    if(checkbox_anchor.attr("aria-checked") === "true") {
        parent.window.success = true;
        return true;
    }

})()