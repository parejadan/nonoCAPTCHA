() => {
        frame = jQuery("iframe[src*='api2/bframe']")
        jQuery(frame).load( function() {
            window.ready_eddy = true;
        });
        if(window.ready_eddy) {
            return true;
        }
    }