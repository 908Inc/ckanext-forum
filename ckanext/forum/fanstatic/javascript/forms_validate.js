autosize($('textarea'));

$.validator.setDefaults({ ignore: ":hidden:not(select)" });

$('#thread-form').validate({
    errorPlacement: function (error, element) {
        console.log("placement");
        if (element.is("select.custom-select")) {
            console.log("placement for chosen");
            // placement for chosen
            $("div.select-section").append(error);
        } else {
            // standard placement
            error.insertAfter(element);
        }
    },
    
});


