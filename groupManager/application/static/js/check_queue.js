function init_check_queue(mode) {
    //if (mode == 0) {
        function handler() {
            fetch('/queue/check')
                .then(response => response.json())
                .then(data => {
                    if (data.redirect) {
                        url = data.url + "?queue_id=" + data.queue_id + "&back=" + encodeURIComponent(window.location.href) + "&token=" + data.token;
                        window.location.href = url;
                    }
                })
                .catch(error => console.error('Error:', error));
        };
    //}
    setInterval(handler, 5000);
    handler();
}