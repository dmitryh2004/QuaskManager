let __password_input_id__ = undefined;

function checkPassword(password) {
    //minimal requirements
    if (password.length < 8) return 0;
    if (!/[A-Za-zА-Яа-я]/.test(password)) return 0;
    if (!/[0-9]/.test(password)) return 0;

    //recommended requirements
    if (password.length < 16) return 1;
    if (!/[A-ZА-Я]/.test(password)) return 1;
    if (!/[!@#\$%\^\&*\)\(+=._-]/.test(password)) return 1;

    return 2;
}

function changeColor() {
    var password = document.getElementById(__password_input_id__);
    var strength = checkPassword(password.value);
    console.log(password.value);
    console.log(strength);

    if (strength == 0) {
        password.style.background = "#F00";
    }
    else if (strength == 1) {
        password.style.background = "#FF0";
    }
    else {
        password.style.background = "#0F0";
    }
}

function init(password_input_id, form_id) {
    var password_input = document.getElementById(password_input_id);
    __password_input_id__ = password_input_id;
    password_input.addEventListener('change', changeColor);

    document.getElementById(form_id).addEventListener("submit", function(e) {
        var password = document.getElementById(password_input_id);
        var strength = checkPassword(password.value);

        if (strength == 0)
        {
            alert("Ваш пароль слишком слабый! Измените пароль согласно минимальным требованиям.");
            e.preventDefault();
        }
    });
}