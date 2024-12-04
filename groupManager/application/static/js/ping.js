function init_ping() {
    // Отправляем пинг каждые 5 секунд
    setInterval(function() {
        fetch('/ping/')
        .then(response => response.json())
        .then(data => {
            console.log(data);
        })
        .catch(error => console.error('Error:', error));
    }, 5000);

    fetch('/ping/');

    window.addEventListener("beforeunload", function () {
        fetch("/set_offline/");
    })
}