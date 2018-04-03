$('div.thread-body').click(function () {
   window.location.href = $(this).data('thread-url');
});
$('form#forum-post').submit(function (e) {
    $('#post-submit').prop('disabled', true);
});
