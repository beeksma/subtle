jQuery(document).ready(function($) {
    $(".clickable-dir").click(function() {
        window.location = $(this).data("url");
    });
    
    $(".clickable-file").click(function () {
        $('#browser').fadeOut('quick', function(){
            $('#load_screen').fadeIn('quick');
        });
        window.location = $(this).data("url");                        
    });
});