$('div.thread-body').click(function () {
   window.location.href = $(this).data('thread-url');
});

$('form#forum-post').submit(function () {
    $('#post-submit').prop('disabled', true);
});

$('form#thread-form').submit(function () {
    $('#thread-submit').prop('disabled', true);
});
