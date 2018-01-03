autosize($('textarea'));

// $.validator.setDefaults({ ignore: ":hidden:not(select)" });

// console.log($.validator)

$.validator.setDefaults({ ignore: ":hidden:not(select)" });

// validation of chosen on change
// if ($("select.custom-select").length > 0) {
//     $("select.custom-select").each(function() {
//         if ($(this).attr('required') !== undefined) {
//             $(this).change(function() {
//                 $(this).valid();
//             });
//         }
//     });
// }

// $("select.custom-select").change(function() {
//     $(this).valid();
// });

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


    // console.log($.validator) 
    // $.validator.setDefaults({ ignore: ":hidden:not(.chosen-select)" })
    // $.fn.validator.Constructor.INPUT_SELECTOR = ':input:not([type="hidden"], [type="submit"], [type="reset"], button)'
    // $("#thread-form").validate();
    // // $("#thread-form").validator('update');

    // $.validator.setDefaults({ ignore: ":hidden:not(.chosen-select)" });
    // $("#thread-form").validate({
    //     rules: {chosen:"required"},
    //     message: {chosen:"Select a Country"}
    // });


